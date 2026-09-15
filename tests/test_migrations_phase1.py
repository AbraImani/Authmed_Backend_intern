"""Upgrade actual pre-phase1 data in an isolated process and in-memory database."""
import os
from pathlib import Path
import subprocess
import sys


def test_phase0_database_upgrades_without_losing_legacy_data():
    code = r"""
import django
django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone
executor = MigrationExecutor(connection)
old = [("users", "0001_initial"), ("organizations", "0001_initial"), ("suppliers", "0001_initial"),
       ("products", "0006_datasetgroup_datasetgroupimage_and_more"), ("inspections", "0010_processing_run_lifecycle"), ("audits", "0001_initial")]
executor.migrate(old)
apps = executor.loader.project_state(old).apps
Org = apps.get_model("organizations", "Organization")
Site = apps.get_model("organizations", "Site")
User = apps.get_model("users", "User")
Supplier = apps.get_model("suppliers", "Supplier")
Product = apps.get_model("products", "ProductReference")
Inspection = apps.get_model("inspections", "BatchInspection")
Audit = apps.get_model("audits", "AuditLog")
a = Org.objects.create(name="A")
b = Org.objects.create(name="B")
site_a = Site.objects.create(organization=a, name="A")
site_b = Site.objects.create(organization=b, name="B")
user = User.objects.create(username="legacy-admin", role="admin", organization=a, site=site_a)
inactive = User.objects.create(username="inactive", role="reviewer", organization=b, is_active=False)
inconsistent = User.objects.create(username="wrong-site", role="inspector", organization=a, site=site_b)
orphan = User.objects.create(username="unassigned", role="admin")
unknown = User.objects.create(username="unknown-role", role="unknown", organization=a)
shared = Supplier.objects.create(name="Shared", contact="kept")
unassigned = Supplier.objects.create(name="Unassigned")
single = Supplier.objects.create(name="Single")
pa = Product.objects.create(organization=a, name="PA", supplier=shared)
pb = Product.objects.create(organization=b, name="PB", supplier=shared)
pc = Product.objects.create(organization=a, name="PC", supplier=single)
inspection = Inspection.objects.create(organization=b, site=site_b, supplier=shared, received_at=timezone.now())
event = Audit.objects.create(action="created", object_type="BatchInspection", object_id=str(inspection.pk), details={"preserved": True})
unknown_event = Audit.objects.create(action="unknown", object_type="User", object_id=str(user.pk))
executor = MigrationExecutor(connection)
phase1 = [("users", "0002_user_firebase_uid"), ("organizations", "0003_migrate_legacy_memberships"), ("suppliers", "0003_scope_legacy_suppliers"), ("audits", "0003_scope_existing_audits")]
executor.migrate(phase1)
apps = executor.loader.project_state(phase1).apps
User = apps.get_model("users", "User")
Member = apps.get_model("organizations", "OrganizationMembership")
Supplier = apps.get_model("suppliers", "Supplier")
Product = apps.get_model("products", "ProductReference")
Inspection = apps.get_model("inspections", "BatchInspection")
Audit = apps.get_model("audits", "AuditLog")
assert User.objects.count() == 5
assert User.objects.get(pk=user.pk).firebase_uid is None
assert Member.objects.get(user_id=user.pk).role == "admin"
assert Member.objects.get(user_id=user.pk).primary_site_id == site_a.pk
assert not Member.objects.get(user_id=inactive.pk).is_active
assert Member.objects.get(user_id=inconsistent.pk).primary_site_id is None
assert not Member.objects.filter(user_id__in=[orphan.pk, unknown.pk]).exists()
assert Supplier.objects.get(pk=shared.pk).organization_id is None
assert Supplier.objects.get(pk=unassigned.pk).organization_id is None
assert Supplier.objects.get(pk=single.pk).organization_id == a.pk
assert Product.objects.get(pk=pa.pk).supplier.organization_id == a.pk
assert Product.objects.get(pk=pb.pk).supplier.organization_id == b.pk
assert Product.objects.get(pk=pa.pk).supplier_id != Product.objects.get(pk=pb.pk).supplier_id
assert Inspection.objects.get(pk=inspection.pk).supplier_id == Product.objects.get(pk=pb.pk).supplier_id
assert Audit.objects.get(pk=event.pk).organization_id == b.pk
assert Audit.objects.get(pk=event.pk).details == {"preserved": True}
assert Audit.objects.get(pk=unknown_event.pk).organization_id is None
print("Phase 0 data upgrade passed")
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "authmed_intern.test_settings"}, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
