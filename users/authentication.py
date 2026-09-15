import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed
from .firebase import verify_firebase_token

class FirebaseAuthentication(BaseAuthentication):
    def authenticate_header(self, request):
        return "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != b"bearer":
            raise AuthenticationFailed("Expected a Bearer authentication token.")
        try:
            token = header[1].decode("ascii")
        except UnicodeDecodeError:
            raise AuthenticationFailed("Invalid authentication token.") from None
        claims = verify_firebase_token(token)
        uid = claims.get("uid")
        if not isinstance(uid, str) or not 0 < len(uid) <= 128:
            raise AuthenticationFailed("Invalid authentication token.")
        User = get_user_model()
        # No email linking, role assignment or membership creation.
        user, created = User.objects.get_or_create(
            firebase_uid=uid,
            defaults={"username": "firebase_" + uuid.uuid4().hex, "password": "!",
                      "email": str(claims.get("email", ""))[:254]},
        )
        if not user.is_active:
            raise AuthenticationFailed("Account is inactive.")
        return user, {"provider": "firebase"}

class AuthMedAuthentication(FirebaseAuthentication):
    """One explicitly configured mechanism, never a Firebase-to-JWT fallback."""
    def authenticate(self, request):
        if settings.AUTHMED_API_AUTH_MODE == "legacy_jwt":
            from rest_framework_simplejwt.authentication import JWTAuthentication
            return JWTAuthentication().authenticate(request)
        return super().authenticate(request)
