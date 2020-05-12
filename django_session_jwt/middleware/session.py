import logging
import jwt
from jwt.exceptions import DecodeError

from importlib import import_module

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.sessions.middleware import SessionMiddleware as BaseSessionMiddleware


KEY = getattr(settings, 'DJANGO_SESSION_JWT', {}).get('KEY', settings.SECRET_KEY)
FIELDS = getattr(settings, 'DJANGO_SESSION_JWT', {}).get('FIELDS', [])
LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.NullHandler())


def verify_jwt(blob):
    """
    Verify a JWT and return the session_key attribute from it.
    """
    try:
        fields = jwt.decode(blob, KEY, algorithms=['HS256'])

    except DecodeError:
        return {}

    # Convert short names to long names.
    for lname, sname in [(i[0], i[1]) for i in FIELDS if type(i) is tuple]:
        try:
            fields[lname] = fields.pop(sname)

        except KeyError:
            continue
    
    return fields


def create_jwt(user, session_key):
    """
    Create a JWT for the given user containing the configured fields.
    """
    fields = {
        'sk': session_key,
    }
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

    return jwt.encode(fields, KEY, algorithm='HS256').decode('utf8')


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
        super().process_response(request, response)
        try:
            session_key = response.cookies[settings.SESSION_COOKIE_NAME].value
            response.cookies[settings.SESSION_COOKIE_NAME] = \
                create_jwt(request.user, session_key)

        except (KeyError, AttributeError):
            # No cookie, no problem...
            pass

        return response