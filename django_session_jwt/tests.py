try:
    from unittest import mock

except ImportError:
    import mock

from os.path import dirname, normpath
from os.path import join as pathjoin

from django.conf import settings
from django.test import TestCase
from django.contrib.auth import get_user_model

from django_session_jwt.middleware import session
from django_session_jwt.test import Client


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
        jwt = session.create_jwt(self.user, session_key)
        fields = session.verify_jwt(jwt)
        self.assertEqual(fields['sk'], session_key)

    def test_asymmetrical(self):
        "Test using RSA key"
        key, pubkey, algo = session._parse_key((
            normpath(pathjoin(dirname(__file__), '../keys/rsa')),
            normpath(pathjoin(dirname(__file__), '../keys/rsa.pub'))
        ))

        with mock.patch('django_session_jwt.middleware.session.ALGO', algo), \
             mock.patch('django_session_jwt.middleware.session.KEY', key):
            session_key = '1234abcdef'
            jwt = session.create_jwt(self.user, session_key)
        with mock.patch('django_session_jwt.middleware.session.ALGO', algo), \
             mock.patch('django_session_jwt.middleware.session.PUBKEY', pubkey):
            fields = session.verify_jwt(jwt)
            self.assertEqual(fields['sk'], session_key)


class ViewTestCase(BaseTestCase):
    """
    Test django sessions / views.
    """

    def test_login(self):
        "Test logging in a user via POST"
        r = self.client.post('/login/', {'username': 'john', 'password': 'password'})
        self.assertEqual(r.status_code, 200)
        fields = session.verify_jwt(r.cookies[settings.SESSION_COOKIE_NAME].value)
        self.assertTrue('id' in fields)       # short form
        self.assertTrue('user_id' in fields)  # long form
        self.assertTrue('u' in fields)        # short form
        self.assertTrue('username' in fields) # long form
        self.assertTrue('e' in fields)        # short form
        self.assertTrue('email' in fields)    # long form

    def test_session(self):
        "Test persisting session data"
        r = self.client.post('/set/', { 'a': '12345', 'b': 'abcde' })
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/get/')
        self.assertEqual(r.status_code, 200)
        json = r.json()
        self.assertEqual(json['a'], '12345')
        self.assertEqual(json['b'], 'abcde')


class TestClientTestCase(BaseTestCase):
    def test_login(self):
        "Test logging in a user using Client.login()"
        ret = self.client.login(username='john', password='password')
        self.assertTrue(ret)
        fields = session.verify_jwt(self.client.cookies[settings.SESSION_COOKIE_NAME].value)
        self.assertTrue('id' in fields)       # short form
        self.assertTrue('user_id' in fields)  # long form
        self.assertTrue('u' in fields)        # short form
        self.assertTrue('username' in fields) # long form
        self.assertTrue('e' in fields)        # short form
        self.assertTrue('email' in fields)    # long form
