from __future__ import unicode_literals

# Django settings for django_session_jwt project.

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': ':memory:',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '8ij$(7l2!w0f8kggntbv=+$bd=^2xs$cl+3v^_##qjw@2py9_3'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    # 'django.template.loaders.eggs.Loader',
)

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django_session_jwt.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

# For older Django versions
MIDDLEWARE_CLASSES = MIDDLEWARE

ROOT_URLCONF = 'django_session_jwt.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'django_session_jwt.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django_session_jwt',
)

DJANGO_SESSION_JWT = {
    # FIELDS should consist of tuples of (attrname, sname, lname) where:
    # - attrname is the name of a user object attribute. This can reference a
    #   nested object by using periods: related_object.attribute_name.
    # - sname is the short form of this name, ideally a single char (unique).
    #   this form is used within the JWT itself and should be short to reduce
    #   storage.
    # - lname is the long form of the name. This is the name that can be used
    #   to access this value after the JWT is verified.
    'FIELDS': [
        ('id', 'id', 'user_id'),
        ('username', 'u', 'username'),
        ('email', 'e', 'email'),
        ('invalid', 'i', 'invalid'),
    ],
    'CALLABLE': 'django_session_jwt.get_fields',
    'KEY': SECRET_KEY,
    # The default, uncomment to override:
    # 'SESSION_FIELD': 'sk',
    'EXPIRES': 60 * 60 * 8,
}

