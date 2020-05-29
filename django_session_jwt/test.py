from django.test.client import Client as BaseClient
from django.contrib.auth import SESSION_KEY, get_user_model

from django_session_jwt.middleware import convert_cookie


User = get_user_model()


class Client(BaseClient):
    def login(self, **credentials):
        ret = super(Client, self).login(**credentials)
        if ret:
            user = User.objects.get(id=int(self.session[SESSION_KEY]))
            convert_cookie(self.cookies, user)
        return ret
