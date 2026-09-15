# Phase 1.5 ? Repository cleanup report

## A. Cleanup summary

Verdict: **PHASE 1.5 COMPLETE**. Scope: the independent `Authmed core backend` repository only, from Phase 1 commit `a611d6f`, on `feature/backend-v1-phase1-5`. Phase 2 has not started.

Physical cleanup removed **271 files**, including **20 tracked source/test/documentation files**, **247 cache files** and **4 temporary validation artifacts**. **32 directories** disappeared. Three file moves are recorded separately and are not counted as deletions. Existing business SQLite/media data and Git history were preserved. The parent repository's 44 tracked files remained unchanged.

The measured source/data/documentation tree changed from **570 files / 79 directories** to **328 files / 48 directories**. These tree counts omit `.git` and `.venv` internals; three explicitly removed old `.venv` validation artifacts and the transient deletion-batch manifest are included in the deletion ledger. New migrations, tests, lock files and audit documents explain why net file reduction differs from gross removals.

- [Tree BEFORE cleanup](tree-before.txt), [machine-readable BEFORE](before.json)
- [Tree AFTER cleanup](tree-after.txt), [machine-readable AFTER](after.json)
- [Every directory classified](directory-classification.md)
- [Every deleted directory](deleted-directories.json)
- [Preservation checks](preservation.json)

## B. Files deleted

[deleted-files.json](deleted-files.json) is the exhaustive ledger: every removed path, reason, reference-search result and risk assessment. All 271 paths were checked physically absent. The 20 Git-tracked deletions are:

1. `authmed_intern/urls_auth.py`
2. `inspections/management/commands/seed_demo.py`
3. `inspections/services/inference/__init__.py`
4. `inspections/services/inference/base.py`
5. `inspections/services/inference/fake.py`
6. `inspections/services/ocr/easyocr_adapter.py`
7. `inspections/services/ocr/paddleocr_adapter.py`
8. `inspections/services/ocr/normalization.py`
9. `products/import_validators.py`
10. `products/services/__init__.py`
11. `products/services/imports/__init__.py`
12. `products/services/imports/duplicates.py`
13. `products/services/imports/preview.py`
14. `products/services/imports/schemas.py`
15. `tests/test_basic.py`
16. `tests/test_dataset_groups.py`
17. `tests/test_product_import_preview.py`
18. `docs/architecture/api-endpoints.md`
19. `docs/architecture/rbac-matrix.md`
20. `docs/sequences/sequence-login.md`

Retired imports, URL registrations, settings and dependencies were removed with their implementations. Runtime reference searches found no references to deleted modules. Historical documentation and migrations may name retired features as history. Empty source directories and source caches were physically removed. `.git` and installed dependency trees were not traversed for cache deletion.

## C. Files moved / isolated

[moved-files.json](moved-files.json) records three moves: the deterministic OCR adapter now lives in `tests/ocr_adapter.py`; previous Phase 0/1 locks now live under their historical documentation directories. They are excluded from runtime installation and container context.

## D. Legacy code retained

No abandoned executable inference, training, YOLO, CSV-preview or demo package remains. The exhaustive directory table explains every retained directory.

Historical migrations remain necessary for existing databases and must not be deleted in a future phase. Phase 0/1 reports and lock snapshots remain required audit evidence. Product, architecture, data-model, deployment, sequence and workflow documents contain design material; they are explicitly distinguished from the deployed contract and excluded from runtime. Reconcile each document in its implementing future phase; no unsupported phase number is assigned. The three misleading duplicate API/auth/RBAC documents were deleted.

Stored inspection risk and review semantics remain unchanged for Phase 5. Existing media is business data, not an unused local research dataset, and must not be deleted as source cleanup. The local `.venv` is a development environment excluded from runtime context. The provider-neutral OCR interface and active normalization/comparison/processing/scoring services are live code, not legacy retention.

## E. User legacy fields

`User.organization`, `User.role` and `User.site` are removed from models/admin by new guarded migration `users.0003_remove_user_organization_remove_user_role_and_more`. `OrganizationMembership` is authoritative. The migration follows the Phase 1 membership transfer and refuses to drop unresolved tenant/site context or an unknown legacy role. Numeric unresolved user IDs are reported for reconciliation. It does not grant or reactivate memberships. A populated-data regression verifies refusal preserves fields, followed by successful migration after reconciliation.

No cleanup migration was applied to the retained local business database. Operators must reconcile reported legacy context before applying this migration to existing deployments.

## F. SimpleJWT status

SimpleJWT package, token URLs, fallback authentication, auth-mode setting and token configuration were removed. Firebase is the sole DRF authentication mechanism; Django Admin retains session authentication. Both retired token paths resolve to 404. PyJWT stays because Firebase Admin depends on it, not as a second login mechanism.

## G. Dataset / research status

DatasetGroup and DatasetGroupImage models, API, serializers, admin and tenancy special cases are removed. New migration `products.0007_remove_datasetgroupimage_dataset_group_and_more` first copies every original column and row into `products_datasetgroup_archive_phase1_5` and `products_datasetgroupimage_archive_phase1_5`, then drops live prototype tables. Archives have no API, ORM model or live foreign-key dependency. Populated migration tests confirm annotation preservation and independence from live image deletion. The retirement is intentionally not automatically reversible: restoration requires an explicit migration.

No training/dataset/YOLO pipeline exists in the canonical runtime. The parent workspace and business uploads remain untouched.

## H. OCR legacy status

Deleted EasyOCR/PaddleOCR stubs, abandoned inference package and redundant normalization re-export. Retained the active provider-neutral OCR lifecycle and downstream services. The deterministic mock moved to tests and is excluded from production context. No new OCR provider was implemented.

## I. Dependencies

Removed `djangorestframework-simplejwt` from active dependencies and uninstalled it locally. Moved `pytest`, `pytest-django` and their test-only dependency closure out of runtime requirements. Runtime lock contains **68 distributions**; development lock adds **6 test-only distributions**. [Dependency inventory and reasons](dependencies.json).

The isolated runtime environment boots before test dependencies are installed and asserts pytest and SimpleJWT are absent. Firebase-required PyJWT and Google Cloud clients remain transitive SDK dependencies. `pip check` passes. Historical locks are preserved only under docs.

## J. Dockerignore / runtime context

`.dockerignore` excludes Git, virtual environments, secrets, local database/media, caches, tests, reports, design documentation, research/training locations and development requirements/settings. It preserves migration source. [Audited runtime context](runtime-context.txt): **107 files**. [Reference/context check](reference-check.json).

The repository is prepared for future container deployment. This phase audited context exclusions; it did not build a Docker image or deploy a service. The unused hardcoded SECRET_KEY fallback was removed and dotenv loading is anchored to the canonical repository, preventing parent `.env` discovery.

## K. Independent-copy result

[Full reproducibility evidence](independence.json). Git-visible source was copied outside the parent workspace into a fresh temporary directory, without parent files, `.git`, `.env`, media or an existing virtualenv. This was an isolated source-copy test, not a remote clone. A new Python 3.11 environment installed the runtime lock, booted WSGI, returned 401 for unauthenticated `/api/me/`, and confirmed application modules load from the copy. Fresh migrations, Django checks, migration drift and runtime dependency checks passed. Test dependencies were then installed and the complete suite passed. All final Python source/tests match that tested copy byte-for-byte. No real Firebase credentials or live authentication service were used by tests.

## L. Migrations

Two new migrations described in E/G; all historical migration files remain unchanged. Fresh installation and populated Phase 1 upgrade are tested, including guard failure and data preservation. `makemigrations --check --dry-run` reports no changes. The retained local SQLite database has not been upgraded by this cleanup.

## M. Tests

Independent full suite: **271 passed in 120.69 seconds**. Before adding the seven cleanup regressions, all 264 retained tests also passed locally. Twenty cases exclusively covering retired demo/JWT/dataset/import features were removed or replaced with the retired-route assertions. Business workflow authentication now exercises FirebaseAuthentication through a restricted test verifier; dedicated Firebase security tests retain their own verification coverage. The suite includes Firebase rejection behavior, membership authorization, role matrix, cross-tenant isolation, business workflows and populated migration safeguards.

Django system check: zero issues. Runtime `pip check`: no broken requirements. No pytest/source bytecode caches remain in the canonical tree; pytest cache generation is disabled.

## N. OpenAPI

Validation succeeds: **35 paths, zero errors**. **62 warnings (43 unique)** remain and are disclosed rather than described as warning-free. The schema asserts FirebaseBearer, `/me`, and absence of retired token/dataset endpoints. Warning cleanup is outside this repository-retirement change.

## O. Commits

1. `4d2936a` ? `refactor(repo): remove verified legacy and dead backend code`
2. `60b6956` ? `chore(runtime): minimize dependencies and deployment context`
3. The commit containing this report ? `test(cleanup): verify independent backend and regression coverage`

The final commit hash is reported in the completion message; a report cannot embed its own final hash.

## P. Final Git status

All cleanup and evidence changes are committed on `feature/backend-v1-phase1-5`; the final porcelain status is checked empty after the report commit. The independent nested Git history and prior phase refs remain preserved. Nothing was pushed or deployed.

## Q. Phase verdict

**PHASE 1.5 COMPLETE**. Physical cleanup, runtime separation, data safeguards, independence checks and regression validation are complete. Phase 2 has not started.
