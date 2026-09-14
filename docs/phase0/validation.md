# Phase 0 validation

Run from the canonical `Authmed core backend` repository using Python 3.11.
Install `requirements-phase0.lock` into its own `.venv`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run --settings=authmed_intern.test_settings
.\.venv\Scripts\python.exe manage.py migrate --noinput --settings=authmed_intern.test_settings
.\.venv\Scripts\python.exe manage.py spectacular --file .venv/phase0-schema.yaml --validate --settings=authmed_intern.test_settings
.\.venv\Scripts\python.exe -m pip check
```

Final verification on 2026-09-15: **110 passed in 24.43s**, zero failed,
zero skipped and zero collection errors. The suite includes 65 preserved
existing tests, 37 processing regressions and 8 structural checks.

Django check: no issues. Migration drift: no changes detected. Clean database
migration: succeeds in a fresh subprocess as part of the structural suite.
Tests apply real migrations; migration execution is never bypassed.
Dependency check: no broken requirements.

OpenAPI generation and validation succeeded: **0 errors**, 72 warnings
(48 unique). Remaining warnings concern missing serializer method type hints
and conflicting enum names. Structural validity does not freeze the Flutter
contract; warning cleanup and contract stabilization belong to Phase 6.
The generated schema is local at `.venv/phase0-schema.yaml`.

Test settings use SQLite in memory, in-memory file storage and a memory
Celery broker/backend. No running Redis, provider, cloud credentials, existing
business database or uploaded media is needed. Adapter doubles are confined
to tests. This verifies local behavior, not live provider integration,
PostgreSQL concurrency, production deployment or full tenant security.

During environment setup an early test attempt ran before installation
finished and had 11 collection errors. After installation completed, normal
collection and the entire suite passed without import or migration bypasses.

See [the implementation report](report.md) for scope and remaining phases.
