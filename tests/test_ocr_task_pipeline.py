import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from organizations.models import Organization, Site
from products.models import ProductReference
from suppliers.models import Supplier
from inspections.models import BatchInspection, Evidence, OCRTask
from inspections.services.ocr import OCRExtractionPipeline, OCRTaskExecutionService, OCRExtractionResult
from inspections.services.normalization import normalize_ocr_payload
from inspections.tasks import process_ocr_task

User = get_user_model()


class DummyOCRAdapter:
    provider_name = "dummy"

    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def extract(self, file_obj):
        if self.error is not None:
            raise self.error
        return self.result


@pytest.mark.django_db
class TestOCRTaskPipeline:
    def setup_method(self):
        self.org = Organization.objects.create(name="OCR Org")
        self.site = Site.objects.create(organization=self.org, name="OCR Site")
        self.supplier = Supplier.objects.create(name="OCR Supplier")
        self.product = ProductReference.objects.create(organization=self.org, name="OCR Product", sku="OCR-1", supplier=self.supplier)
        self.user = User.objects.create_user(username="ocr-user", password="pass", organization=self.org, site=self.site, role="inspector")
        self.inspection = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            supplier=self.supplier,
            product=self.product,
            inspector=self.user,
            batch_number="OCR-BATCH-1",
            received_at=timezone.now(),
        )
        self.evidence = Evidence.objects.create(
            inspection=self.inspection,
            image=self._sample_image(),
            evidence_type="batch_label",
            notes="OCR candidate",
            created_by=self.user,
        )

    def _sample_image(self, name="ocr.gif"):
        tiny_gif = (
            b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff"
            b"!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;"
        )
        return SimpleUploadedFile(name, tiny_gif, content_type="image/gif")

    def test_text_normalization_normalizes_core_fields(self):
        normalized = normalize_ocr_payload(
            {
                "text": "  batch 123  ",
                "medicine_name": " acme med ",
                "batch_number": " bn-001 ",
                "expiry_date": "2030-01-02",
                "manufacturer": "acme pharma",
                "dosage": "500 mg",
                "barcode_data": " ab c123 ",
                "regulatory_code": " rc-9 ",
                "confidence": "87.2",
            }
        )
        assert normalized["text"] == "batch 123"
        assert normalized["normalized_fields"]["medicine_name"] == "acme med"
        assert normalized["normalized_fields"]["manufacturer"] == "ACME PHARMA"
        assert normalized["normalized_fields"]["barcode_data"] == "ABC123"
        assert normalized["normalized_fields"]["expiry_date"] == "2030-01-02"
        assert normalized["confidence"] == 87.2

    def test_execute_task_marks_completion_and_updates_evidence(self):
        result = OCRExtractionResult(
            provider_name="dummy",
            text="ACME MED 500 MG",
            confidence=91.5,
            normalized_fields={
                "medicine_name": "ACME MED",
                "batch_number": "BATCH-001",
                "expiry_date": "2030-01-02",
                "manufacturer": "ACME PHARMA",
                "dosage": "500 MG",
                "barcode_data": "ABC123",
                "regulatory_code": "RC-9",
            },
            raw_output={"text": "raw"},
            logs=[{"message": "provider completed", "level": "info", "payload": {"frames": 1}}],
        )
        pipeline = OCRExtractionPipeline([DummyOCRAdapter(result=result)])
        service = OCRTaskExecutionService(pipeline)
        task = OCRTask.objects.create(evidence=self.evidence)

        service.queue(task, provider_name="dummy", processor_version="ocr-test")
        service.execute(task)

        task.refresh_from_db()
        self.evidence.refresh_from_db()
        assert task.status == "completed"
        assert task.provider_name == "dummy"
        assert task.normalized_output["medicine_name"] == "ACME MED"
        assert task.raw_output == {"text": "raw"}
        assert task.processing_time is not None
        assert self.evidence.extraction_status == "completed"
        assert self.evidence.extracted_text == "ACME MED 500 MG"
        assert self.evidence.extraction_confidence == 91.5
        assert self.evidence.metadata["ocr_provider"] == "dummy"

    def test_retry_and_failure_path_updates_task_and_evidence(self):
        pipeline = OCRExtractionPipeline([DummyOCRAdapter(error=RuntimeError("provider offline"))])
        service = OCRTaskExecutionService(pipeline)
        task = OCRTask.objects.create(evidence=self.evidence)

        service.execute(task)
        task.refresh_from_db()
        self.evidence.refresh_from_db()
        assert task.status == "failed"
        assert task.error_message
        assert self.evidence.extraction_status == "failed"
        assert self.evidence.metadata["ocr_error"] == "All OCR providers failed."

        service.retry(task)
        task.refresh_from_db()
        assert task.status == "queued"
        assert task.retry_count == 1

    def test_celery_task_wrapper_executes_with_monkeypatched_pipeline(self, monkeypatch):
        result = OCRExtractionResult(
            provider_name="dummy",
            text="ACME MED 500 MG",
            confidence=88.0,
            normalized_fields={"medicine_name": "ACME MED", "batch_number": "BATCH-001"},
            raw_output={"text": "raw"},
            logs=[],
        )
        pipeline = OCRExtractionPipeline([DummyOCRAdapter(result=result)])
        monkeypatch.setattr("inspections.tasks.build_default_ocr_pipeline", lambda: pipeline)
        task = OCRTask.objects.create(evidence=self.evidence)

        result_wrapper = process_ocr_task.apply(args=[task.id])
        assert result_wrapper.successful()
        task.refresh_from_db()
        assert task.status == "completed"

    def test_ocr_task_api_exposes_lifecycle_and_actions(self):
        result = OCRExtractionResult(
            provider_name="dummy",
            text="ACME MED 500 MG",
            confidence=90.0,
            normalized_fields={"medicine_name": "ACME MED"},
            raw_output={"text": "raw"},
            logs=[],
        )
        pipeline = OCRExtractionPipeline([DummyOCRAdapter(result=result)])
        service = OCRTaskExecutionService(pipeline)
        task = OCRTask.objects.create(evidence=self.evidence)
        service.queue(task, provider_name="dummy", processor_version="ocr-test")

        client = APIClient()
        response = client.post("/api/auth/token/", {"username": "ocr-user", "password": "pass"}, format="json")
        token = response.json()["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        detail = client.get(f"/api/ocr-tasks/{task.id}/")
        assert detail.status_code == 200
        body = detail.json()
        assert body["inspection_display"]["batch_number"] == "OCR-BATCH-1"
        assert body["lifecycle_summary"]["status"] == "queued"

        retry = client.post(f"/api/ocr-tasks/{task.id}/retry/", {}, format="json")
        assert retry.status_code == 200
        assert retry.json()["retry_count"] == 1

        cancel = client.post(f"/api/ocr-tasks/{task.id}/cancel/", {"reason": "no longer needed"}, format="json")
        assert cancel.status_code == 200
        assert cancel.json()["status"] == "cancelled"

    def test_inspection_detail_exposes_processing_summary(self):
        result = OCRExtractionResult(
            provider_name="dummy",
            text="ACME MED 500 MG",
            confidence=90.0,
            normalized_fields={"medicine_name": "ACME MED"},
            raw_output={"text": "raw"},
            logs=[],
        )
        pipeline = OCRExtractionPipeline([DummyOCRAdapter(result=result)])
        service = OCRTaskExecutionService(pipeline)
        task = OCRTask.objects.create(evidence=self.evidence)
        service.execute(task)

        client = APIClient()
        response = client.post("/api/auth/token/", {"username": "ocr-user", "password": "pass"}, format="json")
        token = response.json()["access"]
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        detail = client.get(f"/api/batch-inspections/{self.inspection.id}/")
        assert detail.status_code == 200
        summary = detail.json()["processing_summary"]
        assert summary["exists"] is True
        assert summary["latest_status"] == "completed"
