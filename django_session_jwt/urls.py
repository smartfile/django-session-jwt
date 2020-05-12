from __future__ import unicode_literals

try:
    from django.conf.urls import url

    def patterns(*args):
        return args

except ImportError:
    from django.conf.urls.defaults import patterns, url

from django_session_jwt.views import login, logout, set, get


urlpatterns = patterns(
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^set/$', set, name='set'),
    url(r'^get/$', get, name='get'),
)

