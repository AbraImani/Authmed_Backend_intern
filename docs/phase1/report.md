# AuthMed Backend V1 - Phase 1 implementation report

## A. Phase 1 executive summary

Firebase identity, local user resolution, organization memberships, contextual
roles and tenant isolation are implemented. Authentication proves identity;
active local membership and capabilities authorize business requests. The
Phase 0 processing foundation is preserved. Phase 2 has not started.

The implementation and automated security foundation are complete for this
phase. This is not a claim that the entire application is ready for pilot
release, nor a claim of live Firebase/cloud deployment verification.

## B. Initial Git state

Canonical repository: `D:/FAITH/Faith/administratif/openSource/authmed-core/Authmed core backend`.
Initial branch: `feature/backend-v1-phase1`, already present and clean.
Initial HEAD: `b932f8c`. Modified/untracked files: none.
Phase 0 commits confirmed: `ecf5aa1`, `f6c871b`, `b932f8c`.
See [initial-state.json](initial-state.json).

Nested Git history remains intact. Hash comparison confirms all 44 tracked
parent files unchanged against the preserved baseline. No parent edits,
history rewriting, destructive Git operations, pushes, merges or deployment.

## C. Firebase authentication implementation

`users/firebase.py` lazily initializes a named Firebase Admin app with an
explicit project and Application Default Credentials. It calls
`auth.verify_id_token(..., check_revoked=True)` and checks the expected UID,
subject, issuer and audience. Invalid/expired/revoked/disabled tokens return
safe 401 errors. Configuration/provider failures return generic 503 errors.
Firebase Auth emulator configuration fails closed in this verifier.

`FirebaseAuthentication` returns `(local User, safe auth context)` to DRF;
request.user is never a dictionary. Unknown verified UIDs create only a local
identity shell with an unusable password, no staff/superuser rights and no
membership. Existing users are resolved by UID, never by email. Business role
claims from Firebase are ignored. Tokens/claims are not serialized by /me.

Configuration: `FIREBASE_PROJECT_ID`, ADC, optionally an untracked local
`GOOGLE_APPLICATION_CREDENTIALS` file. No credentials requested or committed.
See [identity setup](identity.md), including links to the official Firebase
verification, Admin SDK and ADC documentation used for implementation.

## D. User model changes

Added nullable, unique, indexed-by-uniqueness, noneditable `firebase_uid`.
Legacy organization/site/role fields remain stored but are not API authorization
sources. Public user APIs are read-only scoped directory views; no client can
change identity links, memberships, staff flags or roles. Django UserAdmin
replaces generic ModelAdmin for proper password handling; admin login remains
Django session/password authentication. Membership provisioning is internal.

## E. Organization membership model

`OrganizationMembership`: user, organization, role, is_active, optional
primary_site, created_at and updated_at. Database uniqueness covers
(user, organization), including inactive rows. Primary site must belong to the
same organization. Multiple organizations per user are supported without a
site-permission M2M or invitation framework.

Legacy data migration creates memberships only for explicit organizations and
known prior roles. Inactive users receive inactive membership. Invalid old site
assignments are not transferred; unknown-role/unassigned users receive none.
Original user fields and rows are retained.

## F. Role model

Authoritative membership roles/capabilities are in `organizations/roles.py`:
admin, organization_manager, inspector, reviewer and quality_officer.
Tenant admin is distinct from platform administration. Even a Django
superuser requires active membership on tenant APIs; global access remains
inside Django Admin. See the [exact endpoint capability matrix](tenancy.md).

Managers/admins manage references, suppliers, sites and datasets; inspectors
can use inspection/evidence/OCR operations; reviewers/quality officers can use
existing decision writes; quality officers/admins can write existing risk
records. Audit and user-directory reads have explicit capabilities. Final
business transition semantics remain later-phase work.

## G. Active tenant context

A single active membership is selected automatically. Multiple memberships
require `X-Organization-ID` on business requests, validated against active
local membership. /me can return memberships without selecting one.
Unassigned, inactive, ambiguous or unauthorized contexts return 403.
Membership is rechecked each request; request-local caching is not a persistent
authorization cache. Query parameter organization only narrows the active
context and never switches into a foreign organization.

## H. /me endpoint

`GET /api/me/` exposes id, firebase_uid, email, first_name, last_name,
memberships, active_context and capabilities. It requires valid identity,
while allowing profiles with no active membership to understand their access
state. Password hashes, tokens, security claims and internal flags are absent.
The endpoint and optional organization header appear in generated OpenAPI.

## I. Tenant isolation implementation

Shared TenantQuerysetMixin, TenantPermission, TenantSerializerMixin and
TenantFilterBackend enforce outbound rows, object/action access, incoming FK
and many-to-many relations, object ownership and browsable-API filter choices.
Foreign object lookup returns 404; invalid relations return 400; unauthorized
roles/membership return 403; absent/invalid identity returns 401.

Coverage includes organizations, sites, user directory, products, reference
images, datasets, suppliers, inspections, evidence, OCR tasks/actions,
processing runs/actions, risks, decisions and audits. Actor assignment is
server-controlled. Historical inconsistent foreign relation IDs/displays are
redacted from serialization while underlying data remains preserved.

## J. Supplier / product scoping changes

Supplier now has nullable organization ownership. Null means unassigned
historical data, hidden from tenant APIs. New suppliers receive active tenant
ownership. Migration infers single-owner suppliers and copies shared suppliers
per tenant, repointing products/inspections while retaining original records.
Product organization scoping is preserved. Foreign suppliers/references cannot
be attached. Filter choices and HTML controls are scoped as well as JSON rows.

## K. Audit access isolation

AuditLog has nullable organization ownership captured from actual objects,
including nested evidence, OCR tasks, processing runs, risks and decisions.
Existing recoverable events are assigned to their tenant; ambiguous/deleted/
global events remain hidden. Reviewer A cannot list or retrieve audit B.
Signals ignore migration-state models, verify schema readiness and isolate
best-effort inserts in savepoints. Final audit immutability/reliability is
Phase 5; the existing audit design was not replaced.

## L. SimpleJWT transition status

Firebase is the sole default end-user mechanism. Explicit legacy development
mode selects SimpleJWT for the entire API; it requires DEBUG=True through
normal settings. There is no fallback from invalid Firebase tokens to JWT.
Token obtain/refresh return 404 in Firebase mode. Existing JWT tests retain
explicit legacy settings. Django Admin remains separate. Demo seeding is
restricted to the explicit legacy development mode. Flutter targets Firebase.

## M. Migrations created

- `users/0002_user_firebase_uid`.
- `organizations/0002_organizationmembership`.
- `organizations/0003_migrate_legacy_memberships`.
- `suppliers/0002_supplier_organization`.
- `suppliers/0003_scope_legacy_suppliers`.
- `audits/0002_auditlog_organization`.
- `audits/0003_scope_existing_audits`.

No historical migrations rewritten. Empty database migrations and populated
Phase 0 upgrade both pass. No migration was applied to the local business DB.
Data reversal does not attempt destructive supplier merging or membership
removal; future deployed rollback needs separate review.

## N. Security test matrix results

25 Firebase/identity/admin/configuration tests pass. 148 tenant/RBAC tests
pass. Coverage includes A reads A, A cannot read/write/delete/action B,
foreign site/product/supplier references, nested evidence/run/risk/decision
access, audit isolation, absent/inactive membership, explicit platform policy,
multiple memberships, membership revocation on the next request, safe /me,
UID uniqueness, issuer/audience/token failures and HTML filter leakage.
The populated migration preservation test also passes.

Old tests now create memberships explicitly. Reference management fixtures use
manager roles; manual risk-write fixtures use quality roles. Two old tests
expecting global organization-admin visibility now assert tenant isolation.
The no-membership product-create expectation changes from 400 to 403.
All 110 previous scenarios remain in the suite; no tests were deleted.

## O. Full test results

**284 passed in 183.81s; 0 failed; 0 skipped; 0 collection errors.**
Django system check: no issues. Model/migration drift: none. Dependency check:
no broken requirements. Exact commands and execution details are in
[validation.md](validation.md). Tests use real migrations and isolated storage,
not live cloud credentials or the business database.

## P. OpenAPI result

Generation and structural validation pass: **0 errors**, 72 warnings
(48 unique). Warning count is unchanged from Phase 0. Remaining method typing
and enum naming warnings belong to Phase 6. Firebase Bearer authentication and
/me are represented; the final Flutter API contract is not frozen.

## Q. Files modified

Complete repository-relative inventory follows. The identity, tenancy and
validation guides explain the implementation by responsibility. No files were
deleted. `requirements-phase0.lock` and Phase 0 report artifacts are preserved.

- `.env.example`
- `README.md`
- `audits/migrations/0002_auditlog_organization.py`
- `audits/migrations/0003_scope_existing_audits.py`
- `audits/models.py`
- `audits/signals.py`
- `audits/views.py`
- `authmed_intern/permissions.py`
- `authmed_intern/settings.py`
- `authmed_intern/test_settings.py`
- `authmed_intern/urls_auth.py`
- `docs/phase1/identity.md`
- `docs/phase1/initial-state.json`
- `docs/phase1/report.md`
- `docs/phase1/tenancy.md`
- `docs/phase1/validation.md`
- `inspections/management/commands/seed_demo.py`
- `inspections/serializers.py`
- `inspections/views.py`
- `organizations/admin.py`
- `organizations/filters.py`
- `organizations/migrations/0002_organizationmembership.py`
- `organizations/migrations/0003_migrate_legacy_memberships.py`
- `organizations/models.py`
- `organizations/roles.py`
- `organizations/serializer_scope.py`
- `organizations/serializers.py`
- `organizations/tenancy.py`
- `organizations/views.py`
- `products/serializers.py`
- `products/views.py`
- `requirements-phase1.lock`
- `requirements.txt`
- `suppliers/migrations/0002_supplier_organization.py`
- `suppliers/migrations/0003_scope_legacy_suppliers.py`
- `suppliers/models.py`
- `suppliers/serializers.py`
- `suppliers/views.py`
- `tests/__init__.py`
- `tests/helpers.py`
- `tests/test_dataset_groups.py`
- `tests/test_decisions_mobile.py`
- `tests/test_evidence_mobile.py`
- `tests/test_firebase_phase1.py`
- `tests/test_inspections_mobile.py`
- `tests/test_migrations_phase1.py`
- `tests/test_ocr_task_pipeline.py`
- `tests/test_processing_phase0.py`
- `tests/test_product_reference_images.py`
- `tests/test_products_api.py`
- `tests/test_risk_results_mobile.py`
- `tests/test_tenancy_phase1.py`
- `tests/test_workflow.py`
- `users/admin.py`
- `users/apps.py`
- `users/authentication.py`
- `users/firebase.py`
- `users/migrations/0002_user_firebase_uid.py`
- `users/models.py`
- `users/schema.py`
- `users/serializers.py`
- `users/urls.py`
- `users/views.py`

## R. Commits created

1. `c606326` - `feat(auth): integrate firebase identity with local user profiles`.
2. `700b0c4` - `feat(tenancy): add organization memberships roles and scoped authorization`.
3. `test(security): enforce role matrix and tenant isolation` - regression
   matrices, adapted historical fixtures, README and final reports. This report
   belongs to that commit; its hash is shown in git log and the completion message.

## S. Final Git status

Implementation stays on `feature/backend-v1-phase1`, with three logical local
commits. Final clean-tree verification follows the report commit and is stated
in the completion message. Phase 0 branch/history and nested Git are preserved.
No remote publish, merge or parent modification occurred.

## T. Remaining blockers

| Phase | Remaining work |
| --- | --- |
| 2 | Final inspection state machine and authorized business transitions. |
| 3 | Private evidence/file storage, file lifecycle and Cloud Storage controls. |
| 4 | Real managed OCR/AI provider integration. |
| 5 | Versioned risks, final review workflow and durable business audit guarantees. |
| 6 | Stable Flutter contract, schema warnings and final error contract. |
| 7 | Full business/security validation and live identity integration checks. |
| 8 | PostgreSQL/Cloud SQL, Google Cloud deployment and production IAM validation. |
| 9 | Flutter end-to-end authentication/workflows and pilot release. |

Before live usage, configure the existing Firebase project/ADC and explicitly
administer identity linkage/memberships; email alone must never merge accounts.
Live Firebase and cloud deployment were not exercised in these offline tests.
No Phase 2 implementation or Google Cloud deployment has started.

## U. Phase 1 verdict

PHASE 1 COMPLETE
