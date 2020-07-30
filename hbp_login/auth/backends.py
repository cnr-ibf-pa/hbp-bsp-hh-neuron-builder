from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

import requests


class SocialAuth(object):

    _token = None

    def __init__(self, token):
        self._token = token
        super(SocialAuth, self).__init__()

    def get(self):
        return self._token

    def set(self, token):
        self._token = token


class MyHbpBackend(BaseBackend):
    HBP_USER_URL = 'https://services.humanbrainproject.eu/idm/v1/api/user/me'

    def authenticate(self, request, token=None, user_id=None):
        print('[MyHbpBackend] authenticate() called.')
        headers = {'Authorization': token}
        r = requests.get(self.HBP_USER_URL, headers=headers)
        if r.status_code == 200:
            try:
                user = User.objects.get(pk=r.json()['id'])
            except User.DoesNotExist:
                user = User(pk=r.json()['id'], username=r.json()['username'])
                user.save()
            user.social_auth = SocialAuth(token=token)
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
