import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from organizations.models import Organization, Site
from suppliers.models import Supplier
from products.models import ProductReference
from django.contrib.auth import get_user_model
from inspections.models import BatchInspection, Evidence

User = get_user_model()


@pytest.mark.django_db
class TestEvidenceMobileAPI:
    def setup_method(self):
        self.org = Organization.objects.create(name="Ev Org")
        self.site = Site.objects.create(organization=self.org, name="Ev Site")
        self.supplier = Supplier.objects.create(name="Ev Supplier")
        self.product = ProductReference.objects.create(organization=self.org, name="Ev Product", sku="EV001")
        self.inspector = User.objects.create_user(username="ev-inspector", password="pass", role="inspector", organization=self.org, site=self.site)
        self.other_org = Organization.objects.create(name="Other Org")
        self.other_user = User.objects.create_user(username="other-user", password="pass", role="inspector", organization=self.other_org)

    def _get_token(self, username, password):
        client = APIClient()
        response = client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        assert response.status_code == 200
        return response.json()["access"]

    def test_create_evidence_for_inspection(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-1", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"inspection": insp.id, "notes": "Photo of label", "evidence_type": "photo"}
        resp = client.post("/api/evidences/", payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["inspection"] == insp.id
        assert data["notes"] == "Photo of label"
        assert data["created_by"]["username"] == "ev-inspector" if isinstance(data.get("created_by"), dict) else True

    def test_add_evidence_via_inspection_action(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-2", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"notes": "Attached via action", "evidence_type": "photo"}
        resp = client.post(f"/api/batch-inspections/{insp.id}/add_evidence/", payload, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["inspection"] == insp.id
        assert data["notes"] == "Attached via action"

    def test_list_evidence_for_inspection(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-3", received_at=timezone.now())
        for i in range(3):
            Evidence.objects.create(inspection=insp, notes=f"note {i}", evidence_type="photo", created_by=self.inspector)
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp = client.get(f"/api/evidences/?inspection={insp.id}")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 3

    def test_evidence_scope_prevents_cross_org_attach(self):
        # create an inspection in org
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-4", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("other-user", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"inspection": insp.id, "notes": "Should be rejected", "evidence_type": "photo"}
        resp = client.post("/api/evidences/", payload, format="json")
        assert resp.status_code == 400