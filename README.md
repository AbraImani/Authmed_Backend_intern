# AuthMed Backend V1 - canonical Django repository

This independent repository (`Authmed_Backend_intern`) is the canonical
inspection backend. Its Git history remains independent of the parent
`authmed-core` repository. The parent's `backend/` and Dockerfile are legacy
and do not deploy this application.

Phase 0 stabilized processing; Phase 1 adds Firebase identity, organization
memberships, contextual roles and tenant isolation. See the [Phase 1 report](docs/phase1/report.md),
[identity setup](docs/phase1/identity.md) and [authorization matrix](docs/phase1/tenancy.md).
SQLite and local media remain temporary. Private storage, managed AI and
deployment belong to later phases. Tests require no Google Cloud credentials.
The whole application is not yet a pilot release.

Use a virtual environment inside this repository. Python 3.11 is the Phase 0
validation environment. Do not reuse or repair the parent's environment.


This is a Django and DRF backend implementing the AuthMed medicine intake inspection and risk-control workflow.

Core features
- Organizations and Sites multi-tenancy
- Local `User` linked by Firebase UID; roles belong to `OrganizationMembership`
- Suppliers, Product references
- BatchInspection workflow: receive batch -> capture Evidence -> RiskResult -> ReviewDecision
- AuditLog for traceability (create/update/delete recorded)
- Firebase ID tokens by default; explicit legacy JWT development mode only
- Admin UI and API docs (Swagger)

Quick start (local)

1. Create virtualenv and install dependencies

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements-phase1.lock
```

2. Create `.env` from `.env.example` and adjust secrets

3. Run migrations

```powershell
python manage.py migrate
```

4. Create superuser

```powershell
python manage.py createsuperuser
```

5. Optional development-only demo data (requires explicit legacy JWT mode and DEBUG=True)

```powershell
python manage.py seed_demo
```

6. Run server

```powershell
python manage.py runserver
```

API docs
- Open `http://127.0.0.1:8000/api/docs/` for Swagger UI
- Open `http://127.0.0.1:8000/api/schema/` for OpenAPI JSON

Authentication
- Firebase clients send `Authorization: Bearer <Firebase ID token>`.
- `GET /api/me/` returns the local profile, memberships and active capabilities.
- Use `X-Organization-ID` to select one of multiple active memberships.
- Active membership is required on all tenant APIs, including for superusers.
- Django Admin retains internal session/password login.
- Legacy token endpoints are available only in explicit development mode;
  see [identity setup](docs/phase1/identity.md). Demo accounts are local-only.

Testing

```powershell
pytest -q
```

Project structure (essential files)

- `authmed_intern/` - Django project settings and URLs
- `users/` - Custom User model, serializers, API
- `organizations/` - Organization and Site models
- `suppliers/` - Supplier model
- `products/` - ProductReference model
 - `products/` - ProductReference model

Product Reference
-----------------
`ProductReference` is the canonical, organization-scoped reference for medicines used to align inspections with known products. It stores a human name, optional SKU, supplier linkage, simple dosage/form/strength attributes, packaging notes and a representative image. Inspections reference `ProductReference` to enable consistent comparison and future dataset building.
- `inspections/` - `BatchInspection`, `Evidence`, `RiskResult`, `ReviewDecision` and seed command
- `audits/` - `AuditLog` model and automatic signals

How this supports the workflow
1. A `BatchInspection` is created when a shipment/batch is received (fields: product, supplier, inspector, batch_number, received_at).
2. `Evidence` objects (images, notes) are attached to the inspection via the `batch-inspections/{id}/add_evidence/` action or `evidences/` endpoint.
3. A `RiskResult` is stored (one-to-one) describing risk score and reason from automated or manual evaluation.
4. A `ReviewDecision` is recorded when a reviewer approves or rejects; the `BatchInspection` also stores an `outcome` (`accepted`, `isolated`, `escalated`).
5. All create/update/delete events are recorded into `AuditLog` for internal traceability.

Status vs Outcome
- **status**: represents workflow progression used by mobile and UI to track the inspection lifecycle (values: `pending`, `in_progress`, `completed`). This is a transient workflow state.
- **outcome**: represents the final business decision resulting from review/decision workflows (values: `accepted`, `isolated`, `escalated`). This is set by reviewers and should be considered the authoritative final disposition.

Phase 3 mobile handoff
- `risk_result_summary` is a small stable summary object for Flutter.
- `decision_summary` is the final decision object Flutter can render directly.
- When a decision is submitted, the inspection is marked `completed` and the `outcome` is updated to match the decision.

Phase 4 operational foundation
- `ProductReferenceImage` stores multiple reference views per medicine reference with deterministic upload paths and lightweight metadata.
- `Evidence` now carries evidence categories, ordering, file metadata, and OCR placeholder fields for later extraction work.
- `OCRTask` tracks processing state without connecting an external OCR provider yet.
- `DatasetGroup` organizes reference images for labeling readiness, review, and future dataset preparation.
- CSV import preview helpers exist for product reference ingestion planning and duplicate detection.


Phase 0 validation and processing behavior
-----------------------------------------

See [the Phase 0 validation guide](docs/phase0/validation.md). The lock file
records the tested environment; `requirements.txt` remains the dependency
intent. Tests use isolated settings, real migrations and in-memory file
storage. No local business database or uploaded files are required.

No real OCR/AI provider is configured in Phase 0. Analysis reports a failed
run with `provider_unavailable`, not a successful fake result. Empty or
incomparable extraction reports `insufficient_data` and `requires_review`.
Incomplete stage sets cannot publish a final risk. Existing historical risk
records are retained on failure; inspect the latest processing status before
using an old risk result. Versioned risk/run associations belong to Phase 5.

Processing runs are created through `process-intelligence` and are read-only
through `/api/processing-runs/`. Phase 1 enforces tenant and role boundaries
around existing CRUD; final risk/review workflow guarantees remain Phase 5.
The current API and generated OpenAPI are not yet the frozen Flutter contract.
