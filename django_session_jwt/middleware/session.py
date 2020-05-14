import logging
from datetime import datetime

from os.path import exists as pathexists

import jwt
from jwt.exceptions import DecodeError

from importlib import import_module

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.middleware import SessionMiddleware as BaseSessionMiddleware


def _parse_key(key):
    def _load_key(k):
        if pathexists(k):
            k = open(k, 'rb').read()
        return k

    if type(key) is tuple:
        # Key pair.
        return _load_key(key[0]), _load_key(key[1]), 'RS256'

    key = _load_key(key)
    return key, key, 'HS256'


KEY, PUBKEY, ALGO = _parse_key(getattr(settings, 'DJANGO_SESSION_JWT', {}).get('KEY', settings.SECRET_KEY))
FIELDS = getattr(settings, 'DJANGO_SESSION_JWT', {}).get('FIELDS', [])
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def verify_jwt(blob):
    """
    Verify a JWT and return the session_key attribute from it.
    """
    try:
        fields = jwt.decode(blob, PUBKEY, algorithms=[ALGO])

    except DecodeError:
        return {}

    # Convert short names to long names.
    for lname, sname in [(i[0], i[1]) for i in FIELDS if type(i) is tuple]:
        try:
            fields[lname] = fields.pop(sname)

        except KeyError:
            continue
    
    return fields


def create_jwt(user, session_key, expires=None):
    """
    Create a JWT for the given user containing the configured fields.
    """
    fields = {
        'sk': session_key,
        'iat': datetime.utcnow(),
    }
    if expires:
        # Thu, 28 May 2020 19:17:13 GMT
        # Django 2.0, 1.11 have - chars in date...
        expires = expires.replace('-', ' ')
        fields['exp'] = datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z')
    for field_name in FIELDS:
        if type(field_name) is tuple:
            lname, sname = field_name
        
        else:
            lname = sname = field_name

        try:
            fields[sname] = getattr(user, lname)

        except AttributeError:
            # Omit missing fields:
            LOGGER.warning('Could not get missing field %s from user', field_name)
            continue

    return jwt.encode(fields, KEY, algorithm=ALGO).decode('utf8')


class SessionMiddleware(BaseSessionMiddleware):
    """
    Extend django.contrib.sessions middleware to use JWT as session cookie.
    """

    def process_request(self, request):
        session_jwt = request.COOKIES.get(settings.SESSION_COOKIE_NAME)
        session_key = verify_jwt(session_jwt).get('sk')
        request.session = self.SessionStore(session_key)

    def process_response(self, request, response):
        # Rather than duplicating the session logic here, just allow super()
        # to do it's thing, then convert the session cookie (if any) when it's
        # done.
        super(SessionMiddleware, self).process_response(request, response)
        try:
            cookie = response.cookies[settings.SESSION_COOKIE_NAME]
            response.cookies[settings.SESSION_COOKIE_NAME] = \
                create_jwt(request.user, cookie.value, cookie.get('expires'))

        except (KeyError, AttributeError):
            # No cookie, no problem...
            pass

        return response
