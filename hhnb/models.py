from django.contrib.auth.models import AbstractUser
from django.db import models


class MyUser(AbstractUser):
    name = models.CharField(max_length=64, blank=True)


class Workflow():
    workflow_id = models.CharField(editable=False, max_length=16)
    username = models.CharField(editable=False, max_length=32)
    model_id = models.CharField(editable=False, max_length=64)
