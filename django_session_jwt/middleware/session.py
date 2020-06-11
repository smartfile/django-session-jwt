import logging
from datetime import datetime

from os.path import exists as pathexists

import jwt
from jwt.exceptions import DecodeError

from importlib import import_module

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
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


SESSION_FIELD = getattr(settings, 'DJANGO_SESSION_JWT', {}).get('SESSION_FIELD', 'sk')
KEY, PUBKEY, ALGO = _parse_key(getattr(settings, 'DJANGO_SESSION_JWT', {}).get('KEY', settings.SECRET_KEY))
FIELDS = _parse_fields(getattr(settings, 'DJANGO_SESSION_JWT', {}).get('FIELDS', []))
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

    except DecodeError:
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
        # Thu, 28 May 2020 19:17:13 GMT
        # Django 2.0, 1.11 have - chars in date...
        expires = expires.replace('-', ' ')
        fields['exp'] = datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z')

    for attrname, sname, _ in FIELDS:
        try:
            fields[sname] = rgetattr(user, attrname)

        except AttributeError:
            # Omit missing fields:
            LOGGER.warning('Could not get missing field %s from user', attrname)
            continue

    return jwt.encode(fields, KEY, algorithm=ALGO).decode('utf8')


def convert_cookie(cookies, user):
    cookie = cookies[settings.SESSION_COOKIE_NAME]
    cookies[settings.SESSION_COOKIE_NAME] = create_jwt(
        user, cookie.value, cookie.get('expires'))


class SessionMiddleware(BaseSessionMiddleware):
    """
    Extend django.contrib.sessions middleware to use JWT as session cookie.
    """

    def process_request(self, request):
        session_jwt = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        fields = verify_jwt(session_jwt)
        session_key = fields.pop(SESSION_FIELD, None)
        request.session = self.SessionStore(session_key)
        request.session['jwt'] = fields

    def process_response(self, request, response):
        # Rather than duplicating the session logic here, just allow super()
        # to do it's thing, then convert the session cookie (if any) when it's
        # done.
        super(SessionMiddleware, self).process_response(request, response)

        # Behave the same as contrib.sessions, only recreate the JWT if the session
        # was modified or SESSION_SAVE_EVERY_REQUEST is enabled.
        if not request.session.modified and not settings.SESSION_SAVE_EVERY_REQUEST:
            return response

        try:
            convert_cookie(response.cookies, request.user)

        except (KeyError, AttributeError):
            # No cookie, no problem...
            pass

        return response
