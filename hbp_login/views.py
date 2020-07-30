from django.contrib.auth import authenticate
from django.shortcuts import render
from django.urls import resolve

from hbp_login.config.hbp_login import HBP_LOGIN
from hbp_login.auth.backends import MyHbpBackend

from urllib.parse import urlparse, unquote

import json


class SingletonLoginClass(object):
    __instance__ = None
    _callback_url = None
    _ctx = None

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

    def set_ctx(self, ctx):
        self._ctx = ctx

    def get_ctx(self):
        return self._ctx


def login(request, ctx=None):
    print('[Login view]: %s' % request.build_absolute_uri())
    # if ctx:
    #     SingletonLoginClass.get_instance().set_ctx(ctx)
    # elif unquote(request.build_absolute_uri()).find('ctx') > 0:
    #     ctx =
    url_parsed = urlparse(request.build_absolute_uri())
    if url_parsed[4]:
        SingletonLoginClass.get_instance().set_callback_url(url_parsed[4].split('next=')[1])
    try:
        print('[Login view] User in session %s' % request.session['user_id'])
    except KeyError:
        print('[Login view] User not saved in session')
    try:
        token = request.POST['token']
        user = authenticate(request, token=token)
        if user.is_authenticated:
            request.user = user
            request.session['user_id'] = user.id
            request.session.save()
            view, args, kwargs = resolve(SingletonLoginClass.get_instance().get_callback_url())
            request.session['ctx'] = SingletonLoginClass.get_instance().get_ctx()
            kwargs['request'] = request
            return view(*args, **kwargs)
    except KeyError:
        print('[Login view] Getting token via js')
        config = HBP_LOGIN
        print('[Login view] Rendering login')
        print(request)
        request = None
        return render(request, 'hbp_login/hbp-login.html', {"login_config": json.dumps(config)})
