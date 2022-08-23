from hh_neuron_builder.settings import FERNET_KEY, SECRET_KEY

from cryptography.fernet import Fernet
from hashlib import blake2b


class InvalidSign(Exception):
    pass


class Cypher:
    """
    This class is used to encrypt and decrypt data through
    two static simple methods.
    The encryption and decryption use the same key.
    """

    @staticmethod
    def encrypt(plain_text, at_time=None):
        """
        Encrypt a message using the Fernet method. 

        Parameters
        ----------
        plain_text : str
            the plain message to encrypt
        at_time : int, optional

        Returns
        -------
        str
            the encrypted message
        """
        if type(plain_text) == str:
            data = bytes(plain_text, 'utf-8')
        f = Fernet(FERNET_KEY)
        if at_time:
            token = f.encrypt_at_time(data, int(at_time))
        else:
            token = f.encrypt(data)
        cipher_text = token.decode('utf-8')
        return cipher_text

    @staticmethod
    def decrypt(cipher_text, at_time=None):
        """
        Decrypt a cipher message previously encrypted using the encrypt method.

        Parameters
        ----------
        cipher_text : str
            the cipher message
        at_time : int, optional

        Returns
        -------
        str
            the plain message
        """
        if type(cipher_text) == str:
            token = bytes(cipher_text, 'utf-8')
        f = Fernet(FERNET_KEY)
        if at_time:
            plaint_text = f.decrypt_at_time(token, 10, int(at_time))
        else:
            plaint_text = f.decrypt(token, 10).decode('utf-8')
        return plaint_text


class Sign:
    """
    This class is used to sign a file and to verify the integrity of the file
    by verifing its sign. 
    """
    
    def __init__(self):
        """
        Initialize the hash function to create/verify the sign.
        """
        if type(SECRET_KEY) != bytes:
            key = bytes(SECRET_KEY, 'utf-8')
        else:
            key = SECRET_KEY
        self._h = blake2b(key=key)

    def _get_hash(self, data):
        if type(data) != bytes:
            data = bytes(data)
        self._h.update(data)
        return bytes(self._h.hexdigest(), 'utf-8')

    @classmethod
    def get_data_sign(cls, data):
        """
        Create the hash sign for the data.

        Parameters
        ----------
        data : any
            data to sign

        Returns
        -------
        bytes
            the sign
        """
        s = cls()
        return s._get_hash(data)

    @classmethod
    def verify_data_sign(cls, sign, data):
        """
        Verify if the sign is valide for the data.

        Parameters
        ----------
        sign : bytes
            the sign 
        data : any
            the data to verify

        Returns
        -------
        bool
            True if the sign is verified for the data, 
            otherwise an InvalidSignError will be raised

        Raises
        ------
        InvalidSign
            This error is raised if the sign is not valid for the data
        """
        s = cls()
        if s._get_hash(data) == sign:
            return True
        raise InvalidSign('Invalid signature.')
