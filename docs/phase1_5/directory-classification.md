# Directory classification

Every directory outside opaque Git/environment internals is classified below. File-level isolation is recorded in moved-files.json. No retained directory contains abandoned executable research code.

| Directory | Classification | Reason / future disposition |
|---|---|---|
| `.git/` | KEEP BUT EXCLUDE FROM RUNTIME | Independent repository history; permanent source-control metadata. |
| `.pytest_cache/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `.pytest_cache/v/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `.pytest_cache/v/cache/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `.venv/` | KEEP BUT EXCLUDE FROM RUNTIME | Local installed environment, not canonical source; recreated from locks for deployment. |
| `audits/` | KEEP | Active Django application or processing service. |
| `audits/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `audits/migrations/` | KEEP | Historical migration chain and new data-preserving cleanup migrations; retain permanently. |
| `audits/migrations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `authmed_intern/` | KEEP | Active Django application or processing service. |
| `authmed_intern/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `docs/` | KEEP BUT EXCLUDE FROM RUNTIME | Documentation index and evidence, excluded from container context. |
| `docs/architecture/` | KEEP BUT EXCLUDE FROM RUNTIME | Product/domain design reference, explicitly non-authoritative for runtime. Reconcile with the future phase implementing each domain; no speculative deletion date. |
| `docs/data-model/` | KEEP BUT EXCLUDE FROM RUNTIME | Product/domain design reference, explicitly non-authoritative for runtime. Reconcile with the future phase implementing each domain; no speculative deletion date. |
| `docs/deployment/` | KEEP BUT EXCLUDE FROM RUNTIME | Product/domain design reference, explicitly non-authoritative for runtime. Reconcile with the future phase implementing each domain; no speculative deletion date. |
| `docs/phase0/` | KEEP BUT EXCLUDE FROM RUNTIME | Required phase evidence and historical dependency snapshots; preserve for audit, no future deletion phase. |
| `docs/phase1/` | KEEP BUT EXCLUDE FROM RUNTIME | Required phase evidence and historical dependency snapshots; preserve for audit, no future deletion phase. |
| `docs/phase1_5/` | KEEP BUT EXCLUDE FROM RUNTIME | Required phase evidence and historical dependency snapshots; preserve for audit, no future deletion phase. |
| `docs/product/` | KEEP BUT EXCLUDE FROM RUNTIME | Product/domain design reference, explicitly non-authoritative for runtime. Reconcile with the future phase implementing each domain; no speculative deletion date. |
| `docs/sequences/` | KEEP BUT EXCLUDE FROM RUNTIME | Product/domain design reference, explicitly non-authoritative for runtime. Reconcile with the future phase implementing each domain; no speculative deletion date. |
| `docs/workflows/` | KEEP BUT EXCLUDE FROM RUNTIME | Product/domain design reference, explicitly non-authoritative for runtime. Reconcile with the future phase implementing each domain; no speculative deletion date. |
| `inspections/` | KEEP | Active Django application or processing service. |
| `inspections/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/management/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/management/commands/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/management/commands/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/migrations/` | KEEP | Historical migration chain and new data-preserving cleanup migrations; retain permanently. |
| `inspections/migrations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/` | KEEP | Active Django application or processing service. |
| `inspections/services/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/comparison/` | KEEP | Active Django application or processing service. |
| `inspections/services/comparison/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/inference/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/inference/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/normalization/` | KEEP | Active Django application or processing service. |
| `inspections/services/normalization/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/ocr/` | KEEP | Active Django application or processing service. |
| `inspections/services/ocr/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/processing/` | KEEP | Active Django application or processing service. |
| `inspections/services/processing/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `inspections/services/scoring/` | KEEP | Active Django application or processing service. |
| `inspections/services/scoring/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `media/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/evidences/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/inspections/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/inspections/1/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/inspections/1/evidence/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/inspections/1/evidence/batch_label/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/inspections/1/evidence/invoice/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/inspections/1/evidence/photo/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/references/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/references/1/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/references/1/front_packaging/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/1/references/1/label/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/2/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/2/references/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/2/references/2/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `media/organizations/2/references/2/barcode/` | KEEP BUT EXCLUDE FROM RUNTIME | Existing business uploads; not training datasets. Preserve data; storage lifecycle is a later implementation decision. |
| `organizations/` | KEEP | Active Django application or processing service. |
| `organizations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `organizations/migrations/` | KEEP | Historical migration chain and new data-preserving cleanup migrations; retain permanently. |
| `organizations/migrations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `products/` | KEEP | Active Django application or processing service. |
| `products/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `products/migrations/` | KEEP | Historical migration chain and new data-preserving cleanup migrations; retain permanently. |
| `products/migrations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `products/services/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `products/services/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `products/services/imports/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `products/services/imports/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `suppliers/` | KEEP | Active Django application or processing service. |
| `suppliers/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `suppliers/migrations/` | KEEP | Historical migration chain and new data-preserving cleanup migrations; retain permanently. |
| `suppliers/migrations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `tests/` | KEEP BUT EXCLUDE FROM RUNTIME | Firebase, RBAC, tenant and regression verification; isolated OCR fixture retained here. |
| `tests/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `users/` | KEEP | Active Django application or processing service. |
| `users/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
| `users/migrations/` | KEEP | Historical migration chain and new data-preserving cleanup migrations; retain permanently. |
| `users/migrations/__pycache__/` | DELETE | Physically removed: generated cache or unused inference/demo/import subtree; see deleted-files.json. |
