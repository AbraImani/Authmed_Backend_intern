# Phase 1 identity contract

Default: `AUTHMED_API_AUTH_MODE=firebase`. Flutter sends a Firebase ID token
as `Authorization: Bearer <token>`. Firebase Admin validates its signature,
expiry, issuer, audience, revocation and disabled-user state. Configure
`FIREBASE_PROJECT_ID`. Credentials use Application Default Credentials;
locally `GOOGLE_APPLICATION_CREDENTIALS` can reference an untracked service
account file outside the repository. No credential file is required for tests.
The Firebase Auth emulator is intentionally rejected by this production verifier.

A verified UID resolves exactly one local User. Unknown UIDs create only an
identity shell with an unusable password. Email never links existing accounts;
custom role/admin claims never grant privileges. API responses contain no token.
Provision active membership separately through trusted internal administration.
Legacy users retain their old identifiers and fields; do not merge accounts by
email or copy memberships onto a new identity without an administrator's
explicit verification of the account linkage.

Django Admin remains Django session/password authentication. Ordinary users
are not granted staff access. Firebase UID is not editable through public API
or the generic admin form. Existing password admin uses Django's UserAdmin.

Temporary local compatibility: `AUTHMED_API_AUTH_MODE=legacy_jwt` together
with `DEBUG=True` selects SimpleJWT for the entire API. The development
`/api/auth/token/` and `/api/auth/token/refresh/` endpoints are available only
in that mode; they return 404 in Firebase mode. There is no mixed Bearer
fallback and no session authentication on business APIs. Tests select legacy
mode for old scenarios and override to Firebase for real DRF/verifier tests.
SimpleJWT is retained for explicit development compatibility, not Flutter.

Status semantics: missing/invalid/expired/revoked/disabled identity returns
401; verified but unauthorized membership/role returns 403; foreign tenant
object lookup returns 404; invalid relations return 400 without disclosing
foreign object contents. Verifier/configuration outages return generic 503.

References: [Firebase token verification](https://firebase.google.com/docs/auth/admin/verify-id-tokens),
[Python verify_id_token](https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth),
[Application Default Credentials](https://firebase.google.com/docs/admin/setup).
Live Firebase integration requires the deployment's credentials and project;
the automated tests mock the SDK verification boundary and do not contact cloud services.
