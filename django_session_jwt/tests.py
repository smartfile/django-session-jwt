import time
from unittest import mock

from os.path import dirname, normpath
from os.path import join as pathjoin

from datetime import datetime

from django.conf import settings
from django.test import override_settings
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.test.client import Client as BaseClient

from django_session_jwt.middleware import session
from django_session_jwt.test import Client

from freezegun import freeze_time

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
        self.assertFalse('i' in fields)       # short form
        self.assertFalse('invalid' in fields) # long form
        self.assertTrue('foo' in fields)      # from callable

    def test_session(self):
        "Test persisting session data"
        r = self.client.post('/login/', {'username': 'john', 'password': 'password'})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/set/', { 'a': '12345', 'b': 'abcde' })
        self.assertEqual(r.status_code, 200)
        r = self.client.get('/get/')
        self.assertEqual(r.status_code, 200)
        json = r.json()
        self.assertEqual(json['a'], '12345')
        self.assertEqual(json['b'], 'abcde')

    def test_expiration(self):
        "Test JWT exp field handling"
        r = self.client.post('/login/', {'username': 'john', 'password': 'password'})
        self.assertEqual(r.status_code, 200)
        r = self.client.post('/set/', { 'a': '12345', 'b': 'abcde' })
        self.assertEqual(r.status_code, 200)
        fields = session.verify_jwt(r.cookies[settings.SESSION_COOKIE_NAME].value)
        # JWT expiration should exceed cookie expiration.
        expires = r.cookies[settings.SESSION_COOKIE_NAME]['expires']
        # Normalize date format (different Django versions use - or <space>)
        expires = expires.replace('-', ' ')
        # format: "Fri, 14 Aug 2020 19:27:28 GMT"
        expires = int(time.mktime(datetime.strptime(expires, '%a, %d %b %Y %H:%M:%S %Z').timetuple()))
        self.assertGreater(expires, fields['exp'])

    def test_anonymous_session(self):
        "Test anonymous session"
        client = BaseClient()
        r = client.get('/get/')
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.cookies.get(settings.SESSION_COOKIE_NAME))

    @override_settings(SESSION_SAVE_EVERY_REQUEST=True)
    def test_unauthenicated_view(self):
        "Test valid JWT with unauthenticated view"
        client = BaseClient()
        with freeze_time('2020-01-01T09:00:00'):
            client.cookies[settings.SESSION_COOKIE_NAME] = session.create_jwt(
                self.user,
                self.client.session.session_key,
            )
            jwt1 = session.verify_jwt(
                client.cookies[settings.SESSION_COOKIE_NAME].value)

        with freeze_time('2020-01-01T09:05:00'):
            r = client.get('/get/')

            self.assertEqual(r.status_code, 200)
            jwt2 = session.verify_jwt(
                r.cookies.get(settings.SESSION_COOKIE_NAME).value)
        self.assertNotEqual(jwt1['iat'], jwt2['iat'])


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
        self.assertTrue('foo' in fields)      # from callable
