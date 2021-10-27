.. image:: https://coveralls.io/repos/github/smartfile/django-session-jwt/badge.svg?branch=master
    :target: https://coveralls.io/github/smartfile/django-session-jwt?branch=master

.. image:: https://github.com/smartfile/django-session-jwt/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/smartfile/django-session-jwt/actions

.. image:: https://badge.fury.io/py/django-session-jwt.svg
    :target: https://badge.fury.io/py/django-session-jwt

django-session-jwt
==================

This is a session middleware that extends the ``django.contrib.sessions`` system. It is compatible with Django sessions insofar as it utilizes a session key stored in a cookie. The difference is in the format of the coookie.

``django.contrib.sessions`` stores a cookie named ``settings.SESSION_COOKIE_NAME`` which contains a value such as: ``"5a6aybftilfw60wl9ehwrg4ybzawr9b4"``. The session key is a key used server-side to fetch additional data associated with a session. This data is stored in a backend such as a database or memcache.

``django_session_jwt.sessions`` enhances this behavior by modifying the format of the session cookie. Instead of writing the session key as the value of the cookie, it writes a JWT which contains the session key. In addition to the session key, the JWT can contain other desirable fields.

The reason for this extension is to allow one to utilize django server-side sessions without modification while also providing a JWT for use by other federated services. While this could be accomplished by using multiple cookies, the JWT is both a client-side store as well as containing the key to a server-side store.

Installation
------------

This module respects the settings for ``django.contrib.sessions`` and provides additional options for controlling the JWT.

``pip install django-session-jwt``

Then modify settings.py:

.. code-block:: python

    # Replace Django's SessionMiddleware
    MIDDLEWARE = [
        ...
        # "django.contrib.sessions.middleware.SessionMiddleware",
        "django_session_jwt.middleware.SessionMiddleware",
        ...
    ]

    SESSION_COOKIE_NAME='sessionid'

    DJANGO_SESSION_JWT = {
        # Fields allow you to specify which attributes of the user object will be stored
        # in the JWT (and copied to the session).
        'FIELDS': [
            # You can provide all three options:
            ('attribute_name', 'short form', 'long form'),

            # Short and long forms can be the same by omitting one.
            ('attribute_name', 'both forms'),

            # The attribute_name can reference nested attributes by using period(s). also
            # the field can be a string, in which case the attribute name is used as both
            # the long and short forms.
            'related_object.attribute_name',
            ...
        ],

        # You can also populate the JWT fields by configuring your own callable. The
        # callable should return a dictionary. The function should optionally accept user.
        'CALLABLE': 'some.module.with.a.function',

        # KEY can also be a tuple in order to specify private and public keys.
        'KEY': 'string value or path to PEM key file',
        # 'KEY': (private_key_or_path, public_key_or_path),

        # The session field is used to store the session key within the JWT. The default
        # is 'sk' but it can be overridden.
        'SESSION_FIELD': 'sk',
        ...
    }

As an optimization, the ``FIELDS`` list can contain tuples ``('attribute_name', 'short form', 'long form')`` providing a short name for the field. The JWT key will use the short form, but it will be converted to the long form when decoded. This can help reduce the size of the jWT.

Using the JWT
-------------

By default, the JWT will contain a single value ``"sk"`` and will be slightly larger than the default session cookie. The whole point of this application is to allow you to add additional fields to the JWT that can be used by other services running along side your Django application.

Once installed and configured, the browser will send the session cookie with each request. This cookie is verified and the sk / session key is utilized to set up Django sessions within the Django application. External applications can utilize the JWT directly, so you should define any "global" fields in the ``DJANGO_SESSION_JWT['FIELDS']`` list / tuple. This way, legacy data stored within Django's session does not pollute the JWT and vice/versa.

You can use a symmetric key or asymmetric key pair. In the simplest case, you can set ``DJANGO_SESSION_JWT['KEY'] = SECRET_KEY``. You will then need to distribute the `SECRET_KEY` to all federated services. Another option is to use an asymmetric key pair such as an RSA key pair. This way the Django application alone holds the private key for signing JWTs while federated services hold only the public key for verifying the signature. A hybrid configuration might share the private key with a number of federated services for the purpose of issuing or extending JWTs while limiting other services to just the public key.

No library is provided for consuming the JWT, federated services should use available JWT libraries for verifying and extracting fields from the JWT.

Django Tests
------------

When using Django's test client in unit tests, the login() method bypasses middleware and sets the session cookie directly. If you are using ``django-session-jwt`` this may cause tests to fail. In this case, you can use an alternative test client ``django_session_jwt.test.Client`` that overrides the ``login()`` method to convert the sessoin cookie to a JWT.

Here is an `example <django_session_jwt/tests.py#L85>`_ of using this test client.

Development
-----------

To deploy to PyPI:

::

    git tag <version>
    git push --tags

Travis CI will do the rest.

Tests and linting:

::

    make test
    make lint
