import logging
import time

from datetime import datetime, timedelta

from os.path import exists as pathexists

import jwt
from jwt.exceptions import DecodeError, ExpiredSignatureError

from importlib import import_module

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware as BaseSessionMiddleware
from django.core.exceptions import ImproperlyConfigured


def _parse_key(key):
    def _load_key(k):
        if pathexists(k):
            k = open(k, 'rb').read()
        return k

    if isinstance(key, tuple):
        # Key pair.
        return _load_key(key[0]), _load_key(key[1]), 'RS256'

    key = _load_key(key)
    return key, key, 'HS256'


def _parse_fields(fields):
    "Parse and validate field definitions."
    snames, lnames = [], []

    for i, field in enumerate(fields):
        # Transform field in 3-tuple.
        if isinstance(field, tuple):
            if len(field) == 2:  # (attrname, sname)
                field = (field[0], field[1], field[1])

            elif len(field) == 1:  # (attrname)
                field = (field[0], field[0], field[0])

        else:  # attrname
            field = (field, field, field)

        # Collect all snames and lnames for uniqueness check.
        snames.append(field[1])
        lnames.append(field[2])

        # Validate that "sk" is not used, we use that for the session key.
        if field[1] == SESSION_FIELD:
            raise ImproperlyConfigured(
                'Short name "%s" is reserved for session field. Use '
                'DJANGO_SESSION_JWT["SESSION_FIELD"] to specify another '
                'value.' % SESSION_FIELD)

        if len(field) != 3:
            raise ImproperlyConfigured(
                'DJANGO_SESSION_JWT["FIELDS"] should be a list of 3-tuples.')

        fields[i] = field

    if len(snames) != len(set(snames)):
        raise ImproperlyConfigured(
            'DJANGO_SESSION_JWT["FIELDS"] short names are not unique')

    if len(lnames) != len(set(lnames)):
        raise ImproperlyConfigured(
            'DJANGO_SESSION_JWT["FIELDS"] long names are not unique')

    return fields


def _parse_callable(f):
    if not f:
        return

    module_name, _, f_name = f.rpartition('.')
    m = import_module(module_name)

    return getattr(m, f_name)


DJANGO_SESSION_JWT = getattr(settings, 'DJANGO_SESSION_JWT', {})
SESSION_FIELD = DJANGO_SESSION_JWT.get('SESSION_FIELD', 'sk')
KEY, PUBKEY, ALGO = _parse_key(DJANGO_SESSION_JWT.get('KEY', settings.SECRET_KEY))
FIELDS = _parse_fields(DJANGO_SESSION_JWT.get('FIELDS', []))
CALLABLE = _parse_callable(DJANGO_SESSION_JWT.get('CALLABLE'))
EXPIRES = DJANGO_SESSION_JWT.get('EXPIRES', None)
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def rgetattr(obj, name):
    "Recursive getattr()."
    names = name.split('.')
    for n in names:
        obj = getattr(obj, n)
    return obj


def verify_jwt(blob):
    """
    Verify a JWT and return the session_key attribute from it.
    """
    try:
        fields = jwt.decode(blob, PUBKEY, algorithms=[ALGO])

    except (DecodeError, ExpiredSignatureError):
        return {}

    # Convert short names to long names.
    for _, sname, lname in FIELDS:
        try:
            # Leave both short and long forms in dictionary.
            fields[lname] = fields[sname]

        except KeyError:
            continue

    return fields


def create_jwt(user, session_key, expires=None):
    """
    Create a JWT for the given user containing the configured fields.
    """
    fields = {
        SESSION_FIELD: session_key,
        'iat': datetime.utcnow(),
    }
    if expires:
        # Set a future expiration date.
        fields['exp'] = datetime.utcnow() + timedelta(seconds=expires)

    for attrname, sname, _ in FIELDS:
        try:
            fields[sname] = rgetattr(user, attrname)

        except AttributeError:
            # Omit missing fields:
            LOGGER.warning('Could not get missing field %s from user', attrname)
            continue

    if CALLABLE:
        fields.update(CALLABLE(user))

    return jwt.encode(fields, KEY, algorithm=ALGO)


def convert_cookie(cookies, user):
    cookie = cookies[settings.SESSION_COOKIE_NAME]
    cookies[settings.SESSION_COOKIE_NAME] = create_jwt(
        user, cookie.value, EXPIRES)


class SessionMiddleware(BaseSessionMiddleware):
    """
    Extend django.contrib.sessions middleware to use JWT as session cookie.
    """

    def process_request(self, request):
        session_jwt = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        fields = verify_jwt(session_jwt)

        session_key = fields.pop(SESSION_FIELD, None)
        request.session = self.SessionStore(session_key)
        if fields:
            request.session['jwt'] = fields

    def process_response(self, request, response):
        if not request.user.is_authenticated:
            # The user is unauthenticated. Try to determine the user by the
            # session JWT
            User = get_user_model()
            try:
                user_id = request.session['jwt']['user_id']
                user = User.objects.get(id=user_id)
            except (KeyError, User.DoesNotExist):
                # Unable to determine the user. ID will not be set in the JWT.
                user = None
        else:
            user = request.user

        # Rather than duplicating the session logic here, just allow super()
        # to do it's thing, then convert the session cookie (if any) when it's
        # done.
        super(SessionMiddleware, self).process_response(request, response)

        # Determine if JWT is more than halfway through it's lifetime.
        expires = getattr(request, 'session', {}).get('jwt', {}).get('exp', None)
        halftime = time.mktime((datetime.utcnow() + timedelta(seconds=EXPIRES / 2)).timetuple())
        halflife = expires and expires <= halftime

        # Behave the same as contrib.sessions, only recreate the JWT if the session
        # was modified or SESSION_SAVE_EVERY_REQUEST is enabled.
        if not halflife and not request.session.modified and \
           not settings.SESSION_SAVE_EVERY_REQUEST:
            return response

        try:
            convert_cookie(response.cookies, user)

        except (KeyError, AttributeError):
            # No cookie, no problem...
            pass

        return response
