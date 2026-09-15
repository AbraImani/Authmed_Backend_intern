import os
from pathlib import Path
import subprocess
import sys
import pytest
from django.apps import apps
from django.contrib.auth import get_user_model
from django.urls import resolve, Resolver404
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.validation import validate_schema

@pytest.mark.parametrize("path", ["/api/auth/token/", "/api/auth/token/refresh/", "/api/dataset-groups/", "/api/dataset-groups/1/"])
def test_retired_routes_are_physically_unregistered(path):
    with pytest.raises(Resolver404):
        resolve(path)

def test_only_memberships_define_business_context():
    fields = {field.name for field in get_user_model()._meta.fields}
    assert not fields.intersection({"organization", "role", "site"})
    with pytest.raises(LookupError):
        apps.get_model("products", "DatasetGroup")

def test_supported_openapi_contains_no_retired_surfaces():
    schema = SchemaGenerator().get_schema(request=None, public=True)
    validate_schema(schema)
    assert "/api/me/" in schema["paths"]
    assert not any("dataset-group" in path or "/auth/token" in path for path in schema["paths"])
    assert "FirebaseBearer" in schema["components"]["securitySchemes"]

def test_cleanup_guards_user_data_and_archives_datasets():
    code = r"""
import django
django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
phase1 = [("users", "0002_user_firebase_uid"), ("organizations", "0003_migrate_legacy_memberships"),
          ("suppliers", "0003_scope_legacy_suppliers"), ("audits", "0003_scope_existing_audits")]
executor = MigrationExecutor(connection)
executor.migrate(phase1)
apps = executor.loader.project_state(phase1).apps
Org = apps.get_model("organizations", "Organization")
Site = apps.get_model("organizations", "Site")
User = apps.get_model("users", "User")
Member = apps.get_model("organizations", "OrganizationMembership")
Product = apps.get_model("products", "ProductReference")
Image = apps.get_model("products", "ProductReferenceImage")
Group = apps.get_model("products", "DatasetGroup")
Link = apps.get_model("products", "DatasetGroupImage")
org = Org.objects.create(name="Preserved organization")
site = Site.objects.create(organization=org, name="Preserved site")
user = User.objects.create(username="legacy", organization=org, site=site, role="inspector")
product = Product.objects.create(organization=org, name="Business reference")
image = Image.objects.create(product_reference=product, image="historical.gif")
group = Group.objects.create(organization=org, name="Historical labeling", description="Preserve this", created_by=user)
link = Link.objects.create(dataset_group=group, reference_image=image, annotation_notes="Keep annotation")
cleanup_user = [("users", "0003_remove_user_organization_remove_user_role_and_more")]
for stage in ("missing_member", "missing_site"):
    try:
        MigrationExecutor(connection).migrate(cleanup_user)
    except RuntimeError as exc:
        assert "Legacy user context is not fully migrated" in str(exc)
    else:
        raise AssertionError("Unsafe context removal was allowed")
    assert User.objects.get(pk=user.pk).site_id == site.pk
    if stage == "missing_member":
        member = Member.objects.create(user=user, organization=org, role="inspector")
member.primary_site = site
member.save()
executor = MigrationExecutor(connection)
executor.migrate(executor.loader.graph.leaf_nodes())
state = executor.loader.project_state().apps
assert not {"site", "role", "organization"}.intersection(f.name for f in state.get_model("users", "User")._meta.fields)
assert state.get_model("organizations", "OrganizationMembership").objects.get(user_id=user.pk).primary_site_id == site.pk
with connection.cursor() as cursor:
    cursor.execute('SELECT name, description, created_by_id FROM products_datasetgroup_archive_phase1_5')
    assert cursor.fetchall() == [("Historical labeling", "Preserve this", user.pk)]
    cursor.execute('SELECT dataset_group_id, reference_image_id, annotation_notes FROM products_datasetgroupimage_archive_phase1_5')
    assert cursor.fetchall() == [(group.pk, image.pk, "Keep annotation")]
assert "products_datasetgroup" not in connection.introspection.table_names()
# Archived rows do not leave live FK constraints that break business deletion.
state.get_model("products", "ProductReferenceImage").objects.get(pk=image.pk).delete()
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM products_datasetgroupimage_archive_phase1_5')
    assert cursor.fetchone()[0] == 1
print("Guarded cleanup and complete dataset archive passed")
"""
    result = subprocess.run([sys.executable, "-B", "-c", code], cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "DJANGO_SETTINGS_MODULE": "authmed_intern.test_settings", "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
