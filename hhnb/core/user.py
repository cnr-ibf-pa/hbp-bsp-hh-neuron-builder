# User class

from multipledispatch.core import dispatch
from requests.sessions import Request
from hhnb.tools.hpc_job_manager import Nsg

import requests


AVATAR_URL = 'https://wiki.ebrains.eu/bin/download/XWiki/{}/avatar.png?width=36&height=36&keepAspectRatio=true'


class AvatarNotFound(Exception):
    pass


class EbrainsUser:

    def __init__(self, username, token=None):
        self._username = username
        self._avatar_url = AVATAR_URL.format(username)
        if token:
            self._token = token

    def set_token(self, token):
        self._token = token

    def get_username(self):
        return self._username

    def get_user_avatar(self):
        r = requests.get(url=self._avatar_url, verify=False)
        if r.status_code == 200:
            return r.content
        raise AvatarNotFound('Avatar not found')

    def get_token(self):
        return self._token;

    def get_bearer_token(self):
        return 'Bearer ' + self._token


class NsgUser:

    def __init__(self, username, password):
        self._username = username
        self._password = password

    def get_username(self):
        return self._usename

    def get_password(self):
        return self._password

    def validate_credentials(self):
        r = Nsg.check_nsg_login(self._username, self._password)
        print('NSG Credentials validation', r)
        if r['response'] == 'OK':
            return True
        return False


class HhnbUser:

    def __init__(self, ebrains_user=None, nsg_user=None):
        if ebrains_user:
            self.set_ebrains_user(ebrains_user)
        if nsg_user:
            self.set_nsg_user(nsg_user)

    def set_ebrains_user(self, ebrains_user):
        if type(ebrains_user) != EbrainsUser:
            raise TypeError()
        self._ebrains_user = ebrains_user
    
    def set_nsg_user(self, nsg_user):
        if type(nsg_user) != NsgUser:
            raise TypeError()
        self._nsg_user = nsg_user

    def get_ebrains_user(self):
        return self._ebrains_user

    def get_nsg_user(self):
        return self._nsg_user

    def get_user_avatar(self):
        return self._ebrains_user.get_user_avatar()

    def validate_nsg_login(self):
        return self._nsg_user.validate_credentials()

    def get_token(self):
        return self._ebrains_user.get_token()

    def get_username(self):
        return self._ebrains_user.get_username()
    


    @classmethod
    def get_user_from_request(cls, request):
        hhnb_user = cls()
        ebrains_user = EbrainsUser(username=request.user.username 
                                   if request.user.is_authenticated 
                                   else 'anonymous')
        
        if 'oidc_access_token' in request.session.keys():
            ebrains_user.set_token(request.session['oidc_access_token'])
        hhnb_user.set_ebrains_user(ebrains_user)
        return hhnb_user