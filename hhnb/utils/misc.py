from cryptography.fernet import Fernet

from hh_neuron_builder.settings import FERNET_KEY


class Cypher:

    @staticmethod
    def encrypt(plain_text, at_time=None):
        if type(plain_text) == str:
            data = bytes(plain_text, 'utf-8')
        f = Fernet(FERNET_KEY)
        if at_time:
            token = f.encrypt_at_time(data, at_time)
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
            plaint_text = f.decrypt_at_time(token, at_time)
        else:
            plaint_text = f.decrypt(token)
        return plaint_text

