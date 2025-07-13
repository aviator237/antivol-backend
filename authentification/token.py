from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from six import text_type
import random



class TokenGenerator:
    @staticmethod
    def make_token():
        return ''.join(random.choices('0123456789', k=5))
    