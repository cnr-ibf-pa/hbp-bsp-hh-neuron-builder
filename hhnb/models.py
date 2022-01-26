from django.db import models


class User(models.Model):
    sub = models.UUIDField('sub', primary_key=True)
    last_login = models.DateTimeField('last login', auto_now=True, blank=True, null=True)

    USERNAME_FIELD = 'sub'
    REQUIRED_FIELDS = []

    is_active = True

    @property
    def is_anonymous(self):
        """
        Always return False. This is a way of comparing User objects to
        anonymous users.
        """
        return False

    @property
    def is_authenticated(self):
        """
        Always return True. This is a way to tell if the user has been
        authenticated in templates.
        """
        return True