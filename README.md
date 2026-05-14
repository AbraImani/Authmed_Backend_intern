# AuthMed Intern Backend

This is a Django an DRF backend implementing the AuthMed medicine intake inspection and risk-control workflow.

Core features
- Organizations and Sites multi-tenancy
- Custom `User` model with roles: `admin`, `inspector`, `reviewer`
- Suppliers, Product references
- BatchInspection workflow: receive batch -> capture Evidence -> RiskResult -> ReviewDecision
- AuditLog for traceability (create/update/delete recorded)
- JWT authentication (SimpleJWT)
- Admin UI and API docs (Swagger)

Quick start (local)

1. Create virtualenv and install dependencies

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Create `.env` from `.env.example` and adjust secrets

3. Run migrations

```powershell
python manage.py makemigrations
python manage.py migrate
```

4. Create superuser

```powershell
python manage.py createsuperuser
```

5. Seed demo data (creates demo org, site, users, supplier, product, a sample batch inspection)

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
- JWT token endpoints: `POST /api/auth/token/` (obtain), `POST /api/auth/token/refresh/`

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
- `inspections/` - `BatchInspection`, `Evidence`, `RiskResult`, `ReviewDecision` and seed command
- `audits/` - `AuditLog` model and automatic signals

How this supports the workflow
1. A `BatchInspection` is created when a shipment/batch is received (fields: product, supplier, inspector, batch_number, received_at).
2. `Evidence` objects (images, notes) are attached to the inspection via the `batch-inspections/{id}/add_evidence/` action or `evidences/` endpoint.
3. A `RiskResult` is stored (one-to-one) describing risk score and reason from automated or manual evaluation.
4. A `ReviewDecision` is recorded when a reviewer approves or rejects; the `BatchInspection` also stores an `outcome` (`accepted`, `isolated`, `escalated`).
5. All create/update/delete events are recorded into `AuditLog` for internal traceability.
