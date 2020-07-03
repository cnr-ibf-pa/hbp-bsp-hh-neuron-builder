from django.contrib.auth import authenticate
from django.shortcuts import render
from hbp_login.config.hbp_login import HBP_LOGIN
from django.urls import resolve

from urllib.parse import urlparse

import json


class SingletonLoginClass(object):
    __instance__ = None
    _callback_url = None

    def __init__(self):
        if SingletonLoginClass.__instance__ is None:
            SingletonLoginClass.__instance__ = self
        else:
            raise Exception('Cannot create another instace for SingletonLoginClass')

    @staticmethod
    def get_instance():
        if not SingletonLoginClass.__instance__:
            return SingletonLoginClass()
        else:
            return SingletonLoginClass.__instance__

    def set_callback_url(self, url):
        self._callback_url = url
        print('[SingletonLoginClass] set callback url to: "%s".' % self._callback_url)

    def get_callback_url(self):
        print('[SingletonLoginClass] get callback url: %s' % self._callback_url)
        return self._callback_url


def login(request):
    url_parsed = urlparse(request.build_absolute_uri())
    if url_parsed[4]:
        SingletonLoginClass.get_instance().set_callback_url(url_parsed[4].split('next=')[1])
    try:
        token = request.POST['token']
        user = authenticate(request, token=token)
        if user.is_authenticated:
            request.user = user
            view, args, kwargs = resolve(SingletonLoginClass.get_instance().get_callback_url())
            kwargs['request'] = request
            return view(*args, **kwargs)
    except KeyError:
        config = HBP_LOGIN
        return render(request, 'hbp-login.html', {"login_config": json.dumps(config)})
