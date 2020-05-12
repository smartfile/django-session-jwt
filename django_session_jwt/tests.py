from django.conf import settings
from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from .middleware.session import verify_jwt, create_jwt


User = get_user_model()


class BaseTestCase(TestCase):
    """
    Make a user and test client available.
    """

    def setUp(self):
        self.user = User.objects.create_user('john', 'john@domain.com', 'password')
        self.client = Client()


class JWTTestCase(BaseTestCase):
    """
    Test low-level JWT handling.
    """

    def test_create(self):
        "Test JWT creation / verification"
        session_key = '1234abcdef'
        jwt = create_jwt(self.user, session_key)
        fields = verify_jwt(jwt)
        self.assertEqual(fields['sk'], session_key)


class ViewTestCase(BaseTestCase):
    """
    Test django sessions / views.
    """

    def test_login(self):
        "Test logging in a user"
        r = self.client.post('/login/', {'username': 'john', 'password': 'password'})
        self.assertEqual(r.status_code, 200)
        fields = verify_jwt(r.cookies[settings.SESSION_COOKIE_NAME].value)
        self.assertTrue('id' in fields)
        self.assertTrue('username' in fields)
        self.assertTrue('email' in fields)

    def test_session(self):
        "Test persisting session data"
        r = self.client.post('/set/', { 'a': 12345, 'b': 'abcde' })
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/get/')
        self.assertEqual(r.status_code, 200)
