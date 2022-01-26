from hh_neuron_builder.settings import FERNET_KEY, SECRET_KEY

from cryptography.fernet import Fernet
from hashlib import blake2b


class InvalidSign(Exception):
    pass


class Cypher:

    @staticmethod
    def encrypt(plain_text, at_time=None):
        print(plain_text)
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
        if type(cipher_text) == str:
            token = bytes(cipher_text, 'utf-8')
        f = Fernet(FERNET_KEY)
        if at_time:
            plaint_text = f.decrypt_at_time(token, 10, int(at_time))
        else:
            plaint_text = f.decrypt(token, 10).decode('utf-8')
        return plaint_text


class Sign:
    
    def __init__(self):
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
        s = cls()
        return s._get_hash(data)

    @classmethod
    def verify_data_sign(cls, sign, data):
        s = cls()
        if s._get_hash(data) == sign:
            return True
        raise InvalidSign('Invalid signature.')
