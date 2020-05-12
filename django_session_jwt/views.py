from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout


def login(request):
    user = authenticate(username=request.POST['username'],
                        password=request.POST['password'])
    if user is None:
        return HttpResponseNotFound('Failed')

    auth_login(request, user)
    request.session['test'] = 'This value should be present'

    return HttpResponse('OK')


def logout(request):
    auth_logout(request)
    return HttpResponse('OK')


def set(request):
    for key, value in request.POST.items():
        request.session[key] = value
    return HttpResponse('OK')


def get(request):
    data = dict(request.session.items())
    return JsonResponse(data)
