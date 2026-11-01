# Owner: Person A
"""
Custom JWT Authentication and Password Hashing for tatkal_core.
Directly maps to the unmanaged MySQL `app_user` table.
"""

import hashlib
import os
import secrets
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework import exceptions
from .models import AppUser

def hash_password(password: str, salt: str = None) -> str:
    if not salt:
        salt = secrets.token_hex(8)
    iterations = 100000
    h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations)
    return f"pbkdf2_sha256${iterations}${salt}${h.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    try:
        parts = stored_hash.split("$")
        if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
            iterations = int(parts[1])
            salt = parts[2]
            expected_hex = parts[3]
            h = hashlib.pbkdf2_hmac("sha256", plain_password.encode(), salt.encode(), iterations)
            return secrets.compare_digest(h.hex(), expected_hex)
        elif len(parts) == 1:
            # Fallback for plain sha256 if needed
            return secrets.compare_digest(hashlib.sha256(plain_password.encode()).hexdigest(), stored_hash)
        return False
    except Exception:
        return False

class CustomUserWrapper:
    """Wrapper to make AppUser behave like Django's AbstractBaseUser for DRF."""
    def __init__(self, app_user: AppUser):
        self.app_user = app_user
        self.user_id = app_user.user_id
        self.id = app_user.user_id
        self.pk = app_user.user_id
        self.email = app_user.email
        self.first_name = app_user.first_name
        self.last_name = app_user.last_name
        self.role = app_user.role
        self.is_active = app_user.is_active
        self.is_authenticated = True
        self.is_anonymous = False

    @property
    def is_staff(self):
        return self.role == "ADMIN"

    @property
    def is_superuser(self):
        return self.role == "ADMIN"

    def __str__(self):
        return f"{self.email} ({self.role})"

class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if not user_id:
            raise InvalidToken("Token contained no recognizable user identification")

        try:
            user = AppUser.objects.using("readonly").get(user_id=user_id)
        except AppUser.DoesNotExist:
            raise AuthenticationFailed("User not found", code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed("User account is disabled", code="user_inactive")

        return CustomUserWrapper(user)
