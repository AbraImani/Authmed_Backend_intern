# AuthMed Backend

This repository is the independent Django/DRF medicine intake inspection
backend. It has no runtime dependency on the parent workspace. Its current
local nesting is a workspace layout, not a deployment requirement.

Firebase ID tokens identify local users. OrganizationMembership owns tenant
roles and optional site context. Django Admin uses Django sessions. There are
no SimpleJWT endpoints, demo passwords, training providers or dataset APIs.
The processing pipeline reports unavailable providers explicitly; real managed
OCR/AI, private storage and deployment remain later phases.

## Local setup

Use Python 3.11 and a virtual environment inside a fresh clone:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
```

Runtime-only installation uses `requirements.lock`; `requirements.txt` records
runtime dependency intent and `requirements-dev.txt` adds only test tooling.
Copy `.env.example` to `.env`, set your own SECRET_KEY and Firebase project ID.
Use Application Default Credentials; never commit a service-account file.
Settings load only this repository's `.env` and do not search parent folders.

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Existing databases must satisfy the guarded legacy-context migration described
in [runtime and migration notes](docs/phase1_5/runtime.md). The cleanup process
does not apply migrations to your existing local business database.

## API and validation

Send `Authorization: Bearer <Firebase ID token>` and use `GET /api/me/` for
profile, memberships and capabilities. Select `X-Organization-ID` when more
than one active membership exists. All tenant APIs require active membership,
including for platform superusers. Provision membership through Django Admin.

Supported collections: organizations, sites, users (read-only), suppliers,
products, product-reference-images, batch-inspections, evidences, ocr-tasks,
processing-runs (read-only), risk-results, decisions and audit-logs (read-only).
Schema: `/api/schema/`; Swagger: `/api/docs/`. Final Flutter contracts and
business state transitions remain later phases.

```powershell
.\.venv\Scripts\python.exe -B -m pytest -q
.\.venv\Scripts\python.exe -B manage.py check
.\.venv\Scripts\python.exe -B manage.py makemigrations --check --dry-run --settings=authmed_intern.test_settings
```

Tests use real migrations, isolated storage and simulated Firebase verification;
no live cloud credentials or Redis are required. See the [documentation index](docs/README.md)
and [physical cleanup report](docs/phase1_5/report.md). `.dockerignore` excludes
local data, credentials, tests and documentation while preserving migrations.
No deployment or Phase 2 work has been performed.
