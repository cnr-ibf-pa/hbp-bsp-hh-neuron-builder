from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    name = models.CharField(max_length=64, blank=True)