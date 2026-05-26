import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from organizations.models import Organization, Site
from suppliers.models import Supplier
from products.models import ProductReference
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestInspectionsMobileAPI:
    def setup_method(self):
        self.org = Organization.objects.create(name="Mobile Org")
        self.site = Site.objects.create(organization=self.org, name="Mobile Site")
        self.supplier = Supplier.objects.create(name="Mobile Supplier")
        self.product = ProductReference.objects.create(organization=self.org, name="Mobile Product", sku="MOB001")
        self.inspector = User.objects.create_user(username="mobile-inspector", password="pass", role="inspector", organization=self.org, site=self.site)

    def _get_token(self, username, password):
        client = APIClient()
        response = client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        assert response.status_code == 200
        return response.json()["access"]

    def test_create_inspection_mobile(self):
        client = APIClient()
        token = self._get_token("mobile-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "site": self.site.id,
            "supplier": self.supplier.id,
            "product": self.product.id,
            "batch_number": "MOB-BATCH-001",
            "received_at": timezone.now().isoformat(),
            "expiry_date": "2030-01-01",
            "notes": "Sample notes from mobile",
            "status": "in_progress",
        }
        response = client.post("/api/batch-inspections/", payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["batch_number"] == "MOB-BATCH-001"
        assert data["status"] == "in_progress"
        assert "inspector_display" in data

    def test_list_and_filter_inspections_mobile(self):
        # create two inspections with different status
        from inspections.models import BatchInspection
        BatchInspection.objects.create(organization=self.org, site=self.site, supplier=self.supplier, product=self.product, inspector=self.inspector, batch_number="A", received_at=timezone.now(), status="pending")
        BatchInspection.objects.create(organization=self.org, site=self.site, supplier=self.supplier, product=self.product, inspector=self.inspector, batch_number="B", received_at=timezone.now(), status="completed")

        client = APIClient()
        token = self._get_token("mobile-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        resp_all = client.get("/api/batch-inspections/")
        assert resp_all.status_code == 200
        assert len(resp_all.json()) >= 2

        resp_filtered = client.get(f"/api/batch-inspections/?status=pending")
        assert resp_filtered.status_code == 200
        items = resp_filtered.json()
        assert all(item["status"] == "pending" for item in items)

    def test_detail_and_patch_inspection_mobile(self):
        from inspections.models import BatchInspection
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, supplier=self.supplier, product=self.product, inspector=self.inspector, batch_number="PATCH-1", received_at=timezone.now(), status="pending")
        client = APIClient()
        token = self._get_token("mobile-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        detail = client.get(f"/api/batch-inspections/{insp.id}/")
        assert detail.status_code == 200
        assert detail.json()["batch_number"] == "PATCH-1"

        patch_resp = client.patch(f"/api/batch-inspections/{insp.id}/", {"notes": "Updated from mobile", "status": "in_progress"}, format="json")
        assert patch_resp.status_code == 200
        updated = patch_resp.json()
        assert updated["notes"] == "Updated from mobile"
        assert updated["status"] == "in_progress"
