from argparse import _VersionAction
from django.db import models
# from django.contrib.auth.models import Use
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class CustomUser(AbstractUser):
    username = models.CharField(max_length=50, blank=False, null=False, primary_key=True, unique=True)
    first_name = models.CharField(max_length=50,blank=True, null=True)
    last_name = models.CharField(max_length=50,blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png',blank=True, null=True)
    phone_number = models.CharField(null=True, blank=True, max_length=30)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.email

