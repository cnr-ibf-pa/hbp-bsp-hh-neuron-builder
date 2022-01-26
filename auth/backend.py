from mozilla_django_oidc.auth import OIDCAuthenticationBackend, SuspiciousOperation
from hhnb.models import User


class MyOIDCBackend(OIDCAuthenticationBackend):

    def filter_users_by_claims(self, claims):
        sub_id = claims.get('sub')
        if not sub_id:
            return self.UserModel.objects.none()
        try:
            user = User.objects.get(sub=sub_id)
            return user
        except User.DoesNotExist:
            return self.UserModel.objects.none()

    def get_or_create_user(self, access_token, id_token, payload):

        user_info = self.get_userinfo(access_token, id_token, payload)
        sub = user_info.get('sub')
        claims_verified = self.verify_claims(user_info)
        if not claims_verified:
            msg = 'Claims verification failed'
            raise SuspiciousOperation(msg)

        try:
            return User.objects.get(sub=sub)
        except User.DoesNotExist:
            user = User(sub=sub)
            user.save()
            return user