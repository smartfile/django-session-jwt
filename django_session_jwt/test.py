from importlib import import_module

from django.conf import settings
from django.test.client import Client as BaseClient
from django.contrib.auth import SESSION_KEY, get_user_model

from django_session_jwt.middleware import convert_cookie, verify_jwt


User = get_user_model()


class Client(BaseClient):
    def login(self, **credentials):
        ret = super(Client, self).login(**credentials)
        if ret:
            user = User.objects.get(id=int(self.session[SESSION_KEY]))
            convert_cookie(self.cookies, user)
        return ret

    @property
    def session(self):
        """
        Obtains the current session variables.
        """
        engine = import_module(settings.SESSION_ENGINE)
        cookie = self.cookies.get(settings.SESSION_COOKIE_NAME)
        if cookie:
            sk = verify_jwt(cookie.value).get('sk', cookie.value)
            return engine.SessionStore(sk)

        session = engine.SessionStore()
        session.save()
        self.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        return session
