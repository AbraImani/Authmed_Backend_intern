"""Firebase verification boundary; no credentials or network work at import time."""
import os
from functools import lru_cache
from threading import Lock
from django.conf import settings
from rest_framework.exceptions import APIException, AuthenticationFailed

_lock = Lock()

class IdentityUnavailable(APIException):
    status_code = 503
    default_detail = "Identity verification is temporarily unavailable."

@lru_cache(maxsize=1)
def get_firebase_app():
    import firebase_admin
    from firebase_admin import credentials
    project = settings.FIREBASE_PROJECT_ID
    if not project or os.getenv("FIREBASE_AUTH_EMULATOR_HOST"):
        raise IdentityUnavailable()
    with _lock:
        try:
            return firebase_admin.get_app("authmed-identity")
        except ValueError:
            return firebase_admin.initialize_app(
                credentials.ApplicationDefault(), {"projectId": project}, name="authmed-identity"
            )

def verify_firebase_token(token):
    from firebase_admin import auth
    try:
        claims = auth.verify_id_token(token, app=get_firebase_app(), check_revoked=True)
    except (auth.InvalidIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError, ValueError):
        raise AuthenticationFailed("Invalid or expired authentication token.") from None
    except Exception:
        raise IdentityUnavailable() from None
    uid = claims.get("uid")
    project = settings.FIREBASE_PROJECT_ID
    if (not isinstance(uid, str) or not 0 < len(uid) <= 128
            or claims.get("sub") != uid or claims.get("aud") != project
            or claims.get("iss") != f"https://securetoken.google.com/{project}"):
        raise AuthenticationFailed("Invalid or expired authentication token.")
    return claims
