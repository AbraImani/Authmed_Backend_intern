# Current runtime after Phase 1.5

FirebaseAuthentication is the only DRF authentication class. Firebase Admin
uses ADC and an explicit FIREBASE_PROJECT_ID; Django Admin retains sessions.
SimpleJWT, token URLs, mode switches and the fixed-password demo command are
removed. `/me` and tenant permissions remain as implemented in Phase 1.

OrganizationMembership exclusively owns role, organization and site context.
User.organization, User.role and User.site are removed by a new migration.
The migration runs after Phase 1 membership migration and refuses to drop
fields when an organization has no matching membership, a legacy role is
unknown, or a site context was not transferred consistently. It reports
numeric user IDs for trusted operators to reconcile before retrying. It never
creates or activates memberships implicitly. A profile with no organization
and no site has no tenant context to transfer. Existing membership revocations
remain authoritative.

DatasetGroup/ DatasetGroupImage were annotation and labeling-preparation
prototypes, not inspection/reference prerequisites. Their routes, serializers,
admin classes and runtime models are removed. Before table retirement, the
migration copies every row and column into:

- `products_datasetgroup_archive_phase1_5`
- `products_datasetgroupimage_archive_phase1_5`

Archives have no live foreign-key constraints, ORM model or public API. They
retain original IDs/annotations without blocking deletion of business images
or users. This data-preserving retirement is intentionally not automatically
reversible; a future restore requires an explicit migration. Historical
migrations are unchanged. Current local database and media files are retained.

The only OCR runtime code is the provider interface, extraction lifecycle,
normalization, comparison, scoring and processing pipeline. The deterministic
adapter lives in tests. EasyOCR/PaddleOCR stubs and the abandoned inference
package are deleted. CSV import-preview utilities had no runtime entry point;
they and their feature-specific tests are removed. Product CRUD and image
reference workflows remain covered.

The contextual permission matrix remains in `organizations/roles.py` and the
existing Phase 1 guide; dataset-management entries in that historical guide
are now retired. Stored risk/review semantics remain unchanged for Phase 5.
There are no training/notebook/YOLO pipelines in the canonical runtime.

Use requirements.lock for runtime and requirements-dev.lock for tests.
Historical locks moved under docs/phase0 and docs/phase1 for reproducibility.
PyJWT remains a required Firebase Admin dependency; it is not a second login
mechanism. Google Cloud client packages pulled by Firebase Admin remain SDK
requirements, not implemented Cloud Storage/Firestore integrations.

The documentation under product, workflows, architecture, data-model,
deployment and sequences is design material, not a deployed API contract.
The generated OpenAPI and current models define supported behavior. Obsolete
standalone JWT/login, global-admin RBAC and invented API contracts were deleted.
