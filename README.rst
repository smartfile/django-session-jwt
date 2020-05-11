django-session-jwt
==================

This is a session middleware that extends the ``django.contrib.sessions`` system. It is compatible with Django sessions insofar as it utilizes a sessionid stored in a cookie. The difference is in the format of the coookie.

``django.contrib.sessions`` stores a cookie named ``sessionid`` which contains a value such as: ``"5a6aybftilfw60wl9ehwrg4ybzawr9b4"``. The sessionid is a key used server-side to fetch additional data associated with an authenticated user. This data is stored in a backend such as a database or memcache.

``django_session_jwt.sessions`` enhances this behavior by modifying the format of the sessionid cookie. Instead of writing the session key as the value of the cookie, it writes a JWT which contains the sessionid. In addition to the sessionid, the JWT can contain other desirable fields.

The reason for this extension is to allow one to utilize django server-side sessions without modification while also providing a JWT for use by other federated services. By modifying the cookie format the need to utilize two session cookies is removed, as the JWT is both a client-side store as well as containing the key to a server-side store.

Installation
------------

This module respects the settings for ``django.contrib.sessions`` and provides additional options for controlling the JWT.

``pip install django-session-jwt``

Then modify settings.py:

::

    SESSION_ENGINE='django_session_jwt.engine'
    SESSION_COOKIE_NAME='sessionid'

    DJANGO_SESSION_JWT = {
        'fields': (
            'a list',
            'of attributes',
            'of the user',
            'object to place',
            'in the jwt',
        ),
        'key': 'string value or path to PEM key file',
        ,
        ...
    }

Using the JWT
-------------

By default, the JWT will contain a single value ``"sessionid"`` and will be only slightly larger than the default session cookie. The whole point of this application is to allow you to add additional fields to the JWT that can be used by other services running along side your Django application.

Once installed and in use, the browser will send the sessionid cookie with each request. This cookie is verified and the sessionid is utilized to set up Django sessions within the Django application. External applications can utilize the JWT directly, so you should define any "global" fields in the ``DJANGO_SESSION_JWT['fields']`` list / tuple. This way, legacy data stored within Django's session does not pollute the JWT and vice/versa.

You can use a symmetric key or asymmetric key pair. In the simplest case, you can set ``DJANGO_SESSION_JWT['key'] = SECRET_KEY``. You will then need to distribute the `SECRET_KEY` to all federated services. Another option is to use an asymmetric key pair such as an RSA key pair. This way the Django application alone holds the private key for signing JWTs while federated services hold only the public key for verifying the signature. A hybrid configuration might share the private key with a number of federated services for the purpose of issuing or extending JWTs while limiting other services to just the public key.

No library is provided for consuming the JWT, federated services should use available JWT libraries for verifying and extracting fields from the JWT.