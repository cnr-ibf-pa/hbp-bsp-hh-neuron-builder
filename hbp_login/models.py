from django.contrib.auth.models import User
from django.db import models

# Create your models here.

# class SocialAuth(object):
#     _auth_token = None
#
#     def __init__(self, token):
#         self._auth_token = token
#         super(SocialAuth, self).__init__(self)
#
#     def set(self, token):
#         self._auth_token = token
#
#     def get(self):
#         return self._auth_token


class SocialAuth(models.Field):

    description = "Social Auth example for HbpUser models"

    def __init__(self, token, *args, **kwargs):
        self.token = token
        super().__init__(*args, **kwargs)

    def get(self):
        return self.token


class HbpUser(User):
    social_auth = SocialAuth(token='')
