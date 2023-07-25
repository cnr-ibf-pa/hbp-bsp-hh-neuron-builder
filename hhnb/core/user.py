"""
This package provides some classes to handle the end user of the web application.
"""

# User class

from hh_neuron_builder.settings import NSG_KEY, OIDC_OP_USER_ENDPOINT, TMP_DIR
import os
import requests


class AvatarNotFoundError(Exception):
    pass


class UserInfoError(Exception):
    pass


class EbrainsUser:
    """
    Ebrains user class.
    """
    _AVATAR_URL = 'https://wiki.ebrains.eu/bin/download/XWiki/{}/avatar.png?width=36&height=36&keepAspectRatio=true'
    _USER_PAGE_URL = 'https://wiki.ebrains.eu/bin/view/Identity/#/users/{}'

    def __init__(self, sub, token=None):
        """
        Initialize the user.

        Parameters
        ----------
        sub : str, uuid
            the id that identify the user in the Ebrains platform
        token : str, optional
            the user barer token , by default None
        """
        self._sub = sub
        self._cache_dir = os.path.join(TMP_DIR, self._sub)
        if token:
            self._token = token

    def __repr__(self):
        return f'EBRAINS User: {self._sub}'

    def __str__(self):
        return self._sub

    def _get_user_info(self):
        """
        Returns a json containing all the user information.
        If any error occurred an UserInfoError will be raised.
        """
        r = requests.get(url=OIDC_OP_USER_ENDPOINT,
                         headers={'Authorization': self.get_bearer_token()},
                         verify=False)
        if r.status_code == 200:
            return r.json()
        else:
            raise UserInfoError('Error while fetching user information')

    def set_token(self, token):
        """ Set the user barer token. """
        self._token = token

    def get_sub(self):
        """ Get the user sub id. """
        return self._sub

    def get_username(self):
        """ Get the user preferred username. """
        return self._get_user_info()['preferred_username']

    def get_user_avatar(self):
        """
        Returns the user image set on the Ebrains platform.
        This method uses a file cache mechanisms to speed up the request.

        If no image is found an AvatarNotFoundError will be raised.
        """
        if not os.path.exists(self._cache_dir):
            os.mkdir(self._cache_dir)

        if 'avatar.png' in os.listdir(self._cache_dir):
            with open(os.path.join(self._cache_dir, 'avatar.png'), 'rb') as fd:
                return fd.read()

        try:
            r = requests.get(url=self._AVATAR_URL.format(self.get_username()),
                            verify=False)
            if r.status_code == 200:
                with open(os.path.join(self._cache_dir, 'avatar.png'), 'wb') as fd:
                    fd.write(r.content)
                return r.content
            else:
                raise AvatarNotFoundError('Avatar not found')
        except requests.exceptions.ConnectionError:
            raise AvatarNotFoundError('Avatar not found')

    def get_user_page(self):
        """ Returns the Ebrains profile page of the current user. """
        return self._USER_PAGE_URL.format(self.get_username())

    def get_token(self):
        """ Returns the user raw token. """
        return self._token

    def get_bearer_token(self):
        """ Returns the user barer token. """
        return 'Bearer ' + self._token


class NsgUser:
    """
    NSG user class.
    """

    def __init__(self, username, password):
        """
        Initialize the NSG user providing its credentials.

        Parameters
        ----------
        username : str
            username
        password : str
            password
        """
        self._username = username
        self._password = password

    def __repr__(self):
        return f'NSG User: {self._username}'

    def __str__(self):
        return self._username

    def get_username(self):
        """ Returns the username. """
        return self._username

    def get_password(self):
        """ Returns the password. """
        return self._password

    def validate_credentials(self):
        """
        Validate the credentials.

        Returns
        -------
        bool
            True if the credentials are valid, False otherwise
        """
        r = requests.get(url='https://nsgr.sdsc.edu:8443/cipresrest/v1/job',
                         auth=(self._username, self._password),
                         headers={'cipres-appkey': NSG_KEY},
                         verify=False)
        if r.status_code == 200:
            return True
        return False


class HhnbUser:
    """
    Handle the internal user for the HHNB application
    """

    def __init__(self, ebrains_user=None, nsg_user=None):
        """
        Initialize the HHNB user

        Parameters
        ----------
        ebrains_user : hhnb.core.user.EbrainsUser, optional
            Set an already instantiate Ebrains user
        nsg_user : hhnb.core.user.NsgUser, optional
            Set an already instantiate NSG user
        """
        self._ebrains_user = None
        self._nsg_user = None
        if ebrains_user:
            self.set_ebrains_user(ebrains_user)
        if nsg_user:
            self.set_nsg_user(nsg_user)

    def __repr__(self):
        return self.__class__

    def __str__(self):
        return f'<User: "{self._ebrains_user}">'

    def set_ebrains_user(self, ebrains_user):
        """
        Set the Ebrains user.

        Parameters
        ----------
        ebrains_user : hhnb.core.user.EbrainsUser
            the Ebrains user

        Raises
        ------
        TypeError
            if the parameter is not of EbrainsUser type
        """
        if type(ebrains_user) != EbrainsUser:
            raise TypeError()
        self._ebrains_user = ebrains_user

    def set_nsg_user(self, nsg_user):
        """
        Set the NSG user.

        Parameters
        ----------
        nsg_user : hhnb.core.user.NsgUser
            the NSG user

        Raises
        ------
        TypeError
            if the parameter in not of NsgUser type
        """
        if type(nsg_user) != NsgUser:
            raise TypeError()
        self._nsg_user = nsg_user

    def get_ebrains_user(self):
        """ Returns the Ebrains user. """
        return self._ebrains_user

    def get_nsg_user(self):
        """ Returns the NSG user. """
        return self._nsg_user

    def get_user_avatar(self):
        """ Returns the Ebrains user avatar. """
        return self._ebrains_user.get_user_avatar()

    def validate_nsg_login(self):
        """ Validate the NSG credials. """
        return self._nsg_user.validate_credentials()

    def get_token(self):
        """ Returns the Ebrains user token. """
        return self._ebrains_user.get_token()

    def get_username(self):
        """ Returns the preferred username. """
        return self._ebrains_user.get_username()

    def get_sub(self):
        """ Returns the user id. """
        return self._ebrains_user.get_sub()


    @classmethod
    def get_user_from_request(cls, request):
        """
        This class method returns an HhnbUser instance by processing the request object
        and automatically authenticated with the Ebrains platform and NSG if
        every data is present in the request object.

        Parameters
        ----------
        request : HttpRequest
            the request from the frontend

        Returns
        -------
        hhnb.core.user.HhnbUser
            the user instance
        """
        hhnb_user = cls()

        ebrains_user = EbrainsUser(sub=str(request.user.sub)
                                   if request.user.is_authenticated
                                   else 'anonymous')
        if 'oidc_access_token' in request.session.keys():
            ebrains_user.set_token(request.session['oidc_access_token'])

        hhnb_user.set_ebrains_user(ebrains_user)

        if request.session.get('nsg_username')\
            and request.session.get('nsg_password'):
            nsg_user = NsgUser(request.session.get('nsg_username'),
                               request.session.get('nsg_password'))

            hhnb_user.set_nsg_user(nsg_user)

        return hhnb_user