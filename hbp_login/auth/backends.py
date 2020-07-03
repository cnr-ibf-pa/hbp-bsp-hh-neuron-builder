from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from hbp_login.models import HbpUser


import requests


class MyHbpBackend(BaseBackend):
    HBP_USER_URL = 'https://services.humanbrainproject.eu/idm/v1/api/user/me'

    def authenticate(self, request, token=None):
        print('[MyHbpBackend] authenticate() called.')
        headers = {'Authorization': token}
        r = requests.get(self.HBP_USER_URL, headers=headers)
        if r.status_code == 200:
            try:
                user = HbpUser.objects.get(pk=r.json()['id'])
            except HbpUser.DoesNotExist:
                user = User(pk=r.json()['id'], username=r.json()['username'], token=token)
                user.save()
            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
