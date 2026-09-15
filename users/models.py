from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    firebase_uid = models.CharField(max_length=128, unique=True, null=True, blank=True, editable=False)
