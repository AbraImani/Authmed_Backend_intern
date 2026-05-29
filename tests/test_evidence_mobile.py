import pytest
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from organizations.models import Organization, Site
from suppliers.models import Supplier
from products.models import ProductReference
from django.contrib.auth import get_user_model
from inspections.models import BatchInspection, Evidence, OCRTask

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

    def _sample_image(self, name="evidence.jpg"):
        tiny_gif = (
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
            b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
        )
        return SimpleUploadedFile(name, tiny_gif, content_type="image/gif")

    def test_create_evidence_for_inspection(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-1", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "inspection": insp.id,
            "notes": "Photo of label",
            "evidence_type": "photo",
            "image": self._sample_image(),
        }
        resp = client.post("/api/evidences/", payload, format="multipart")
        assert resp.status_code == 201
        data = resp.json()
        assert data["inspection"] == insp.id
        assert data["notes"] == "Photo of label"
        assert data["evidence_type"] == "photo"
        assert data["evidence_status"] == "pending"
        assert data["display_order"] == 0
        assert data["created_by_display"]["username"] == "ev-inspector"
        assert data["image_url"] is not None
        assert data["checksum"]

    def test_create_structured_evidence_and_filter(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-1B", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "inspection": insp.id,
            "notes": "Batch label evidence",
            "evidence_type": "batch_label",
            "evidence_status": "reviewed",
            "display_order": 4,
            "image": self._sample_image(name="batch-label.gif"),
        }
        resp = client.post("/api/evidences/", payload, format="multipart")
        assert resp.status_code == 201
        data = resp.json()
        assert data["evidence_type"] == "batch_label"
        assert data["evidence_status"] == "reviewed"

        filtered = client.get(f"/api/evidences/?inspection={insp.id}&evidence_type=batch_label&evidence_status=reviewed")
        assert filtered.status_code == 200
        assert len(filtered.json()) == 1

    def test_add_evidence_via_inspection_action(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-2", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {
            "notes": "Attached via action",
            "evidence_type": "photo",
            "image": self._sample_image(name="action.jpg"),
        }
        resp = client.post(f"/api/batch-inspections/{insp.id}/add_evidence/", payload, format="multipart")
        assert resp.status_code == 201
        data = resp.json()
        assert data["inspection"] == insp.id
        assert data["notes"] == "Attached via action"

    def test_list_evidence_for_inspection(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-3", received_at=timezone.now())
        for i in range(3):
            Evidence.objects.create(
                inspection=insp,
                notes=f"note {i}",
                evidence_type="photo",
                created_by=self.inspector,
                image=self._sample_image(name=f"list-{i}.gif"),
            )
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
        payload = {
            "inspection": insp.id,
            "notes": "Should be rejected",
            "evidence_type": "photo",
            "image": self._sample_image(name="cross-org.jpg"),
        }
        resp = client.post("/api/evidences/", payload, format="multipart")
        assert resp.status_code == 400

    def test_create_evidence_requires_image(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-5", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"inspection": insp.id, "notes": "Missing image", "evidence_type": "photo"}
        resp = client.post("/api/evidences/", payload, format="json")
        assert resp.status_code == 400
        assert "image" in resp.json()

    def test_add_evidence_requires_image(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-6", received_at=timezone.now())
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        payload = {"notes": "Missing image via action", "evidence_type": "photo"}
        resp = client.post(f"/api/batch-inspections/{insp.id}/add_evidence/", payload, format="json")
        assert resp.status_code == 400
        assert "image" in resp.json()

    def test_create_ocr_task_and_filter_by_status(self):
        insp = BatchInspection.objects.create(organization=self.org, site=self.site, inspector=self.inspector, batch_number="E-7", received_at=timezone.now())
        evidence = Evidence.objects.create(
            inspection=insp,
            notes="OCR candidate",
            evidence_type="invoice",
            created_by=self.inspector,
            image=self._sample_image(name="ocr.gif"),
        )
        client = APIClient()
        token = self._get_token("ev-inspector", "pass")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        create_resp = client.post(
            "/api/ocr-tasks/",
            {"evidence": evidence.id, "status": "pending", "processor_version": "stub-v1"},
            format="json",
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["evidence_display"]["evidence_type"] == "invoice"

        list_resp = client.get("/api/ocr-tasks/?status=pending")
        assert list_resp.status_code == 200
        assert len(list_resp.json()) == 1