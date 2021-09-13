from __future__ import unicode_literals

from django.conf.urls import url

from django_session_jwt.views import login, logout, set, get


urlpatterns = [
    url(r'^login/$', login, name='login'),
    url(r'^logout/$', logout, name='logout'),
    url(r'^set/$', set, name='set'),
    url(r'^get/$', get, name='get'),
]

