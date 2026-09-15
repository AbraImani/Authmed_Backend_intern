from unittest.mock import patch
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from firebase_admin import auth
from rest_framework.test import APIClient, APIRequestFactory
from users.authentication import FirebaseAuthentication
from organizations.models import Organization, OrganizationMembership
from organizations.roles import Role

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def firebase(settings):
    settings.AUTHMED_API_AUTH_MODE = "firebase"
    settings.FIREBASE_PROJECT_ID = "authmed-test-project"
    claims = {"uid": "uid-123", "sub": "uid-123", "aud": settings.FIREBASE_PROJECT_ID,
              "iss": "https://securetoken.google.com/" + settings.FIREBASE_PROJECT_ID,
              "email": "person@example.test", "admin": True, "role": "admin"}
    with patch("users.firebase.get_firebase_app", return_value=object()), patch("firebase_admin.auth.verify_id_token", return_value=claims) as verifier:
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer signed-test-token")
        yield client, claims, verifier

def test_valid_token_provisions_identity_shell_only(firebase):
    client, claims, verifier = firebase
    response = client.get("/api/me/")
    assert response.status_code == 200
    user = User.objects.get(firebase_uid=claims["uid"])
    assert not user.is_staff and not user.is_superuser and not user.has_usable_password()
    assert user.organization_id is None and user.site_id is None
    assert not user.memberships.exists()
    assert response.data["active_context"] is None and response.data["capabilities"] == []
    assert set(response.data) == {"id", "firebase_uid", "email", "first_name", "last_name", "memberships", "active_context", "capabilities"}
    assert verifier.call_args.kwargs["check_revoked"] is True
    assert client.get("/api/batch-inspections/").status_code == 403

def test_authentication_returns_local_user_not_claims_dict(firebase):
    request = APIRequestFactory().get("/api/me/", HTTP_AUTHORIZATION="Bearer signed-test-token")
    user, context = FirebaseAuthentication().authenticate(request)
    assert isinstance(user, User) and user.is_authenticated
    assert context == {"provider": "firebase"}

def test_existing_uid_resolved_and_email_never_links(firebase):
    client, claims, verifier = firebase
    unrelated = User.objects.create_user(username="legacy", email=claims["email"])
    existing = User.objects.create_user(username="linked", firebase_uid=claims["uid"], email="old@example.test")
    assert client.get("/api/me/").data["id"] == existing.pk
    assert User.objects.count() == 2
    unrelated.refresh_from_db()
    assert unrelated.firebase_uid is None

@pytest.mark.parametrize("error", [auth.InvalidIdTokenError, auth.ExpiredIdTokenError, auth.RevokedIdTokenError, auth.UserDisabledError])
def test_sdk_authentication_failures_are_safe_401(firebase, error):
    client, claims, verifier = firebase
    verifier.side_effect = error("sensitive Firebase diagnostic", None) if error is auth.ExpiredIdTokenError else error("sensitive Firebase diagnostic")
    response = client.get("/api/me/")
    assert response.status_code == 401
    assert "sensitive" not in str(response.data)
    assert response["WWW-Authenticate"] == "Bearer"
    assert not User.objects.exists()

@pytest.mark.parametrize("field,value", [("aud", "foreign-project"), ("iss", "https://foreign"), ("sub", "other"), ("uid", ""), ("uid", "x" * 129)])
def test_wrong_project_issuer_or_identity_is_rejected(firebase, field, value):
    client, claims, verifier = firebase
    claims[field] = value
    assert client.get("/api/me/").status_code == 401
    assert not User.objects.exists()

@pytest.mark.parametrize("header", [None, "Bearer", "Bearer one two", "Basic abc"])
def test_missing_and_malformed_authentication(firebase, header):
    client, claims, verifier = firebase
    client.credentials(**({"HTTP_AUTHORIZATION": header} if header else {}))
    assert client.get("/api/me/").status_code == 401
    verifier.assert_not_called()

def test_verifier_outage_is_controlled_503(firebase):
    client, claims, verifier = firebase
    verifier.side_effect = RuntimeError("private credential path")
    response = client.get("/api/me/")
    assert response.status_code == 503 and "private" not in str(response.data)

def test_disabled_local_user_rejected(firebase):
    client, claims, verifier = firebase
    User.objects.create_user(username="disabled", firebase_uid=claims["uid"], is_active=False)
    assert client.get("/api/me/").status_code == 401

def test_duplicate_uid_database_constraint_and_nullable_legacy_ids():
    User.objects.create_user(username="first", firebase_uid="unique")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(username="second", firebase_uid="unique")
    User.objects.create_user(username="legacy-a")
    User.objects.create_user(username="legacy-b")

@pytest.mark.parametrize("active", [True, False])
def test_me_membership_and_business_authorization(firebase, active):
    client, claims, verifier = firebase
    user = User.objects.create_user(username="member", firebase_uid=claims["uid"])
    org = Organization.objects.create(name="Organization")
    OrganizationMembership.objects.create(user=user, organization=org, role=Role.INSPECTOR, is_active=active)
    response = client.get("/api/me/")
    assert response.status_code == 200 and response.data["memberships"][0]["is_active"] is active
    assert bool(response.data["active_context"]) is active
    assert client.get("/api/products/").status_code == (200 if active else 403)

def test_no_simplejwt_fallback_in_firebase_mode(firebase):
    client, claims, verifier = firebase
    verifier.side_effect = auth.InvalidIdTokenError("bad signature")
    assert client.post("/api/auth/token/", {}).status_code == 404
    assert client.post("/api/auth/token/refresh/", {}).status_code == 404
    assert client.get("/api/me/").status_code == 401

def test_admin_session_is_separate_from_business_api(firebase):
    client, claims, verifier = firebase
    user = User.objects.create_superuser(username="platform", password="test-password")
    client.credentials()
    client.force_login(user)
    assert client.get("/admin/").status_code == 200
    assert client.get("/api/me/").status_code == 401


def test_non_staff_member_cannot_use_django_admin(firebase):
    client, claims, verifier = firebase
    user = User.objects.create_user(username="ordinary", password="test-password")
    client.credentials()
    client.force_login(user)
    assert client.get("/admin/").status_code == 302

def test_missing_project_and_emulator_configuration_fail_closed(settings, monkeypatch):
    from users.firebase import get_firebase_app, IdentityUnavailable
    get_firebase_app.cache_clear()
    settings.FIREBASE_PROJECT_ID = ""
    with pytest.raises(IdentityUnavailable):
        get_firebase_app()
    settings.FIREBASE_PROJECT_ID = "project"
    monkeypatch.setenv("FIREBASE_AUTH_EMULATOR_HOST", "127.0.0.1:9099")
    with pytest.raises(IdentityUnavailable):
        get_firebase_app()
    get_firebase_app.cache_clear()
