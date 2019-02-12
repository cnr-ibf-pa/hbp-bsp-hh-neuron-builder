import os

class Token:

    @classmethod
    def renewToken(cls, request):                                           
        # authorization token renewal
        social_auth = request.user.social_auth.get()
        backend = social_auth.get_backend_instance()
        refresh_token = social_auth.extra_data['refresh_token']
        new_token_response = backend.refresh_token(token=refresh_token)
        new_access_token = new_token_response['access_token']
        social_auth.extra_data['access_token'] = new_access_token
        social_auth.save()

