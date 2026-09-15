import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient
from organizations.models import Organization, Site, OrganizationMembership
from organizations.roles import Role
from suppliers.models import Supplier
from products.models import ProductReference, ProductReferenceImage
from inspections.models import BatchInspection, Evidence, OCRTask, InspectionProcessingRun, RiskResult, ReviewDecision
from audits.models import AuditLog

User = get_user_model()
pytestmark = pytest.mark.django_db

@pytest.fixture
def tenants():
    result = []
    for suffix in ("A", "B"):
        org = Organization.objects.create(name="Org " + suffix)
        site = Site.objects.create(organization=org, name="Site " + suffix)
        supplier = Supplier.objects.create(organization=org, name="Supplier " + suffix)
        product = ProductReference.objects.create(organization=org, supplier=supplier, name="Product " + suffix)
        inspection = BatchInspection.objects.create(organization=org, site=site, supplier=supplier, product=product, received_at=timezone.now())
        evidence = Evidence.objects.create(inspection=inspection, image=SimpleUploadedFile(suffix + ".pdf", b"%PDF-1.4 test", content_type="application/pdf"))
        task = OCRTask.objects.create(evidence=evidence)
        run = InspectionProcessingRun.objects.create(inspection=inspection)
        risk = RiskResult.objects.create(inspection=inspection, risk_score=50)
        decision = ReviewDecision.objects.create(inspection=inspection, decision="isolated")
        audit = AuditLog.objects.create(organization=org, action="test", object_type="BatchInspection", object_id=str(inspection.pk))
        image = ProductReferenceImage.objects.create(product_reference=product, image=SimpleUploadedFile("reference.gif", bytes.fromhex("47494638376101000100800000000000ffffff21f90401000000002c00000000010001000002024c01003b"), content_type="image/gif"))
        users = {}
        for role in Role.values:
            user = User.objects.create_user(username=suffix + role)
            OrganizationMembership.objects.create(user=user, organization=org, role=role, primary_site=site)
            users[role] = user
        result.append(dict(org=org, site=site, supplier=supplier, product=product, inspection=inspection, evidence=evidence,
                           task=task, run=run, risk=risk, decision=decision, audit=audit, image=image, users=users))
    return result

def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client

RESOURCES = [("organizations", "org"), ("sites", "site"), ("suppliers", "supplier"), ("products", "product"),
             ("batch-inspections", "inspection"), ("evidences", "evidence"), ("ocr-tasks", "task"),
             ("processing-runs", "run"), ("risk-results", "risk"), ("decisions", "decision"),
             ("audit-logs", "audit"), ("product-reference-images", "image")]

@pytest.mark.parametrize("route,key", RESOURCES)
def test_outbound_lists_and_foreign_details_are_scoped(tenants, route, key):
    own, foreign = tenants
    client = client_for(own["users"][Role.ADMIN])
    response = client.get(f"/api/{route}/")
    assert response.status_code == 200
    ids = {item["id"] for item in response.data}
    assert own[key].pk in ids and foreign[key].pk not in ids
    assert client.get(f"/api/{route}/{own[key].pk}/").status_code == 200
    assert client.get(f"/api/{route}/{foreign[key].pk}/").status_code == 404

@pytest.mark.parametrize("route,key", [entry for entry in RESOURCES if entry[0] not in {"organizations", "processing-runs", "audit-logs"}])
@pytest.mark.parametrize("method", ["patch", "put", "delete"])
def test_cross_tenant_mutations_are_hidden(tenants, route, key, method):
    own, foreign = tenants
    response = getattr(client_for(own["users"][Role.ADMIN]), method)(f"/api/{route}/{foreign[key].pk}/", {}, format="json")
    assert response.status_code == 404
    assert type(foreign[key]).objects.filter(pk=foreign[key].pk).exists()

@pytest.mark.parametrize("relation", ["site", "product", "supplier", "organization"])
@pytest.mark.parametrize("method", ["post", "patch"])
def test_foreign_inspection_relations_rejected_without_explicit_organization(tenants, relation, method):
    own, foreign = tenants
    client = client_for(own["users"][Role.INSPECTOR])
    payload = {"site": own["site"].pk, "received_at": timezone.now().isoformat()}
    payload[relation] = foreign["org" if relation == "organization" else relation].pk
    url = "/api/batch-inspections/" if method == "post" else f'/api/batch-inspections/{own["inspection"].pk}/'
    response = getattr(client, method)(url, payload, format="json")
    assert response.status_code == 400

@pytest.mark.parametrize("route,field,target,role", [
    ("evidences", "inspection", "inspection", Role.INSPECTOR),
    ("ocr-tasks", "evidence", "evidence", Role.INSPECTOR),
    ("risk-results", "inspection", "inspection", Role.QUALITY),
    ("decisions", "inspection", "inspection", Role.REVIEWER),
    ("products", "supplier", "supplier", Role.MANAGER),
    ("sites", "organization", "org", Role.MANAGER),
    ("product-reference-images", "product_reference", "product", Role.MANAGER),
])
def test_inbound_nested_relations_scoped(tenants, route, field, target, role):
    own, foreign = tenants
    payload = {field: [foreign[target].pk] if field == "reference_images" else foreign[target].pk, "name": "attempt", "risk_score": 5, "decision": "accepted"}
    response = client_for(own["users"][role]).post(f"/api/{route}/", payload, format="json")
    assert response.status_code == 400 and field in response.data

@pytest.mark.parametrize("action", ["process-intelligence", "add_evidence"])
def test_foreign_inspection_actions_hidden(tenants, action):
    own, foreign = tenants
    response = client_for(own["users"][Role.INSPECTOR]).post(f'/api/batch-inspections/{foreign["inspection"].pk}/{action}/', {}, format="json")
    assert response.status_code == 404

@pytest.mark.parametrize("action", ["retry", "cancel"])
def test_foreign_ocr_actions_hidden(tenants, action):
    own, foreign = tenants
    assert client_for(own["users"][Role.INSPECTOR]).post(f'/api/ocr-tasks/{foreign["task"].pk}/{action}/').status_code == 404

@pytest.mark.parametrize("state", ["missing", "inactive", "legacy_admin", "platform"])
@pytest.mark.parametrize("route", [entry[0] for entry in RESOURCES] + ["users"])
def test_no_active_membership_denies_all_business_apis(tenants, state, route):
    own, foreign = tenants
    user = User.objects.create_user(username="unauthorized", is_superuser=state == "platform", is_staff=state == "platform")
    if state == "legacy_admin":
        user.role = "admin"  # A transient legacy attribute cannot grant access.
        user.organization = own["org"]
    if state == "inactive":
        OrganizationMembership.objects.create(user=user, organization=own["org"], role=Role.ADMIN, is_active=False)
    client = client_for(user)
    assert client.get(f"/api/{route}/").status_code == 403
    assert client.post(f"/api/{route}/", {}, format="json").status_code == 403

@pytest.mark.parametrize("role,allowed", [(Role.ADMIN, {"manage", "inspect", "review", "quality", "audit", "members"}),
    (Role.MANAGER, {"manage", "inspect", "audit", "members"}), (Role.INSPECTOR, {"inspect"}),
    (Role.REVIEWER, {"review", "audit"}), (Role.QUALITY, {"review", "quality", "audit"})])
def test_role_matrix_on_real_endpoints(tenants, role, allowed):
    own, foreign = tenants
    client = client_for(own["users"][role])
    for capability, route in [("manage", "suppliers"), ("inspect", "batch-inspections"), ("review", "decisions"), ("quality", "risk-results")]:
        response = client.post(f"/api/{route}/", {}, format="json")
        assert response.status_code == (400 if capability in allowed else 403), (role, capability, response.data)
    for capability, route in [("audit", "audit-logs"), ("members", "users")]:
        assert client.get(f"/api/{route}/").status_code == (200 if capability in allowed else 403)

def test_multiple_memberships_require_explicit_context(tenants):
    own, foreign = tenants
    user = own["users"][Role.INSPECTOR]
    OrganizationMembership.objects.create(user=user, organization=foreign["org"], role=Role.REVIEWER)
    client = client_for(user)
    assert client.get("/api/products/").status_code == 403
    me = client.get("/api/me/")
    assert len(me.data["memberships"]) == 2 and me.data["active_context"] is None
    response = client.get("/api/products/", HTTP_X_ORGANIZATION_ID=str(foreign["org"].pk))
    assert {item["id"] for item in response.data} == {foreign["product"].pk}
    assert client.post("/api/batch-inspections/", {}, HTTP_X_ORGANIZATION_ID=str(foreign["org"].pk)).status_code == 403

@pytest.mark.parametrize("header", ["999999", "abc", "-1", "1,2", "9" * 50, ""])
def test_invalid_or_foreign_context_is_denied(tenants, header):
    own, foreign = tenants
    assert client_for(own["users"][Role.ADMIN]).get("/api/me/", HTTP_X_ORGANIZATION_ID=header).status_code == 403

def test_foreign_context_header_never_grants_membership(tenants):
    own, foreign = tenants
    assert client_for(own["users"][Role.ADMIN]).get("/api/products/", HTTP_X_ORGANIZATION_ID=str(foreign["org"].pk)).status_code == 403

def test_membership_uniqueness_and_site_consistency(tenants):
    own, foreign = tenants
    user = own["users"][Role.ADMIN]
    with pytest.raises(IntegrityError), transaction.atomic():
        OrganizationMembership.objects.create(user=user, organization=own["org"], role=Role.INSPECTOR)
    with pytest.raises(ValidationError):
        OrganizationMembership.objects.create(user=user, organization=foreign["org"], role=Role.REVIEWER, primary_site=own["site"])

def test_identity_fields_and_memberships_cannot_be_self_granted(tenants):
    own, foreign = tenants
    user = own["users"][Role.ADMIN]
    response = client_for(user).patch(f"/api/users/{user.pk}/", {"firebase_uid": "attacker", "is_superuser": True, "organization": foreign["org"].pk}, format="json")
    assert response.status_code == 405
    user.refresh_from_db()
    assert user.firebase_uid is None and not user.is_superuser

def test_audit_signal_records_nested_tenant_and_unknown_events_stay_hidden(tenants):
    own, foreign = tenants
    own["evidence"].notes = "updated"
    own["evidence"].save()
    event = AuditLog.objects.filter(object_type="Evidence", object_id=str(own["evidence"].pk), action="updated").latest("pk")
    assert event.organization_id == own["org"].pk
    unknown = AuditLog.objects.create(action="legacy unassigned")
    ids = {item["id"] for item in client_for(own["users"][Role.REVIEWER]).get("/api/audit-logs/").data}
    assert event.pk in ids and unknown.pk not in ids

def test_unassigned_supplier_is_not_global(tenants):
    own, foreign = tenants
    supplier = Supplier.objects.create(name="Unassigned legacy")
    client = client_for(own["users"][Role.MANAGER])
    assert client.get(f"/api/suppliers/{supplier.pk}/").status_code == 404
    assert client.post("/api/products/", {"name": "test", "supplier": supplier.pk}).status_code == 400

def test_platform_superuser_with_membership_still_cannot_cross_tenant(tenants):
    own, foreign = tenants
    user = own["users"][Role.ADMIN]
    user.is_staff = user.is_superuser = True
    user.save()
    assert client_for(user).get(f'/api/products/{foreign["product"].pk}/').status_code == 404


def test_corrupt_legacy_relations_do_not_expose_foreign_details(tenants):
    own, foreign = tenants
    ProductReference.objects.filter(pk=own["product"].pk).update(supplier=foreign["supplier"])
    response = client_for(own["users"][Role.MANAGER]).get(f'/api/products/{own["product"].pk}/')
    assert response.status_code == 200
    assert response.data["supplier"] is None and response.data["supplier_display"] is None
    own["product"].refresh_from_db()
    assert own["product"].supplier_id == foreign["supplier"].pk  # Data preserved for repair.

@pytest.mark.parametrize("route", ["risk-results", "decisions"])
def test_by_inspection_action_cannot_read_foreign_result(tenants, route):
    own, foreign = tenants
    client = client_for(own["users"][Role.REVIEWER])
    assert client.get(f'/api/{route}/by-inspection/?inspection={foreign["inspection"].pk}').status_code == 404

def test_processing_status_action_is_tenant_scoped(tenants):
    own, foreign = tenants
    assert client_for(own["users"][Role.INSPECTOR]).get(f'/api/batch-inspections/{foreign["inspection"].pk}/processing-status/').status_code == 404

def test_supplier_creation_uses_active_context(tenants):
    own, foreign = tenants
    client = client_for(own["users"][Role.MANAGER])
    response = client.post("/api/suppliers/", {"name": "New supplier"}, format="json")
    assert response.status_code == 201 and response.data["organization"] == own["org"].pk
    assert client.post("/api/suppliers/", {"name": "Foreign", "organization": foreign["org"].pk}, format="json").status_code == 400

def test_membership_changes_take_effect_on_next_request(tenants):
    own, foreign = tenants
    user = own["users"][Role.INSPECTOR]
    client = client_for(user)
    assert client.get("/api/products/").status_code == 200
    user.memberships.update(is_active=False)
    assert client.get("/api/products/").status_code == 403

def test_inspector_is_assigned_server_side(tenants):
    own, foreign = tenants
    user = own["users"][Role.INSPECTOR]
    response = client_for(user).post("/api/batch-inspections/", {
        "site": own["site"].pk, "inspector": foreign["users"][Role.INSPECTOR].pk,
        "received_at": timezone.now().isoformat(),
    }, format="json")
    assert response.status_code == 201 and response.data["inspector"] == user.pk

def test_reviewer_cannot_read_foreign_audits(tenants):
    own, foreign = tenants
    client = client_for(own["users"][Role.REVIEWER])
    response = client.get("/api/audit-logs/")
    assert foreign["audit"].pk not in {item["id"] for item in response.data}
    assert client.get(f'/api/audit-logs/{foreign["audit"].pk}/').status_code == 404


def test_browsable_api_filter_choices_do_not_leak_foreign_suppliers(tenants):
    own, foreign = tenants
    response = client_for(own["users"][Role.MANAGER]).get("/api/products/", HTTP_ACCEPT="text/html")
    assert response.status_code == 200
    body = response.content.decode()
    assert own["supplier"].name in body
    assert foreign["supplier"].name not in body

def test_filter_foreign_key_choices_are_scoped(tenants):
    own, foreign = tenants
    client = client_for(own["users"][Role.MANAGER])
    assert client.get(f'/api/products/?supplier={foreign["supplier"].pk}').status_code == 400
    assert client.get(f'/api/products/?supplier={own["supplier"].pk}').status_code == 200


def test_reusable_permission_fails_closed_for_unconfigured_write_view(tenants):
    from types import SimpleNamespace
    from authmed_intern.permissions import TenantPermission
    own, foreign = tenants
    request = SimpleNamespace(user=own["users"][Role.INSPECTOR], method="POST", headers={})
    assert not TenantPermission().has_permission(request, SimpleNamespace())
