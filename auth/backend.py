from mozilla_django_oidc.auth import OIDCAuthenticationBackend, SuspiciousOperation, LOGGER
from hhnb.models import MyUser as User


class MyOIDCBackend(OIDCAuthenticationBackend):

    def get_or_create_user(self, access_token, id_token, payload):
        print('[MyOIDCBackend] get_or_create_user() called.')

        user_info = self.get_userinfo(access_token, id_token, payload)

        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = 'Claims verification failed'
            raise SuspiciousOperation(msg)

        return User(
            username=user_info.get('preferred_username'),
            email=user_info.get('email'),
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', ''),
            name=user_info.get('name', ''),
            sub=user_info.get('sub', '')
        )
