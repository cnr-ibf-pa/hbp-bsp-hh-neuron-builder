from django.contrib.auth.models import AbstractBaseUser
from django.db import models


class User(AbstractBaseUser):
    sub = models.UUIDField('sub', primary_key=True)

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

    def save(self, *args, **kwargs):
        self.set_unusable_password()
        super().save(*args, **kwargs)
