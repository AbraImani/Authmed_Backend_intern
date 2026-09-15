# Phase 1 validation

Run from `Authmed core backend` with the repository's Python 3.11 virtualenv.
Install dependencies using `requirements-phase1.lock`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=authmed_intern.test_settings
.\.venv\Scripts\python.exe manage.py spectacular --file .venv/phase1-schema.yaml --validate --settings=authmed_intern.test_settings
.\.venv\Scripts\python.exe -m pip check
```

Final full suite: **284 passed in 183.81s**, 0 failures, 0 skipped,
0 collection errors. This includes:

| Coverage | Tests |
| --- | ---: |
| Preserved Phase 0 scenarios, with explicit membership/role fixtures | 110 |
| Firebase, local identity, /me, admin separation and auth configuration | 25 |
| Tenant isolation, RBAC, relation validation, filters and active context | 148 |
| Populated Phase 0 data upgrade in a fresh process | 1 |

Django system check: no issues (0 silenced).
Model/migration drift: no changes detected.
OpenAPI: 0 errors, 72 warnings (48 unique), unchanged warning count from
Phase 0. Remaining serializer typing and enum naming warnings belong to
Phase 6. Dependency check: no broken requirements.

Clean migrations run inside the preserved structural suite using an isolated
subprocess. The populated upgrade test uses MigrationExecutor to create the
actual pre-phase1 schema, inserts legacy data, applies all new migrations and
checks preservation and tenant ownership. Real migrations are never disabled.

Additional commands used during implementation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_firebase_phase1.py -q --tb=short
.\.venv\Scripts\python.exe -m pytest tests/test_tenancy_phase1.py -q --tb=short -x
.\.venv\Scripts\python.exe -m pytest tests/test_migrations_phase1.py -q --tb=short
.\.venv\Scripts\python.exe -m pytest tests/test_tenancy_phase1.py -q --tb=short -k "browsable or filter_foreign"
```

Intermediate runs identified an audit signal attempting an insert before its
new column existed, an invalid image fixture, a Firebase exception constructor
requiring a cause, and old tests expecting global tenant-admin access. These
were corrected; no failing case was removed to obtain the final result.

Tests use SQLite in memory, in-memory uploaded files, real Django/DRF requests
and mocked Firebase SDK verification. They require no cloud credentials,
live Firebase, Redis or network services. Existing local business DB/media
were not migrated. Live Firebase project/IAM behavior, PostgreSQL concurrency,
cloud deployment and Flutter integration remain future integration checks.
