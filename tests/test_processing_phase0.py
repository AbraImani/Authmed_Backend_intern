from tests.helpers import create_member_user
from unittest.mock import Mock

import pytest
from celery.exceptions import Retry
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from django.utils import timezone

from organizations.models import Organization, Site
from users.models import User
from inspections.models import BatchInspection, Evidence, InspectionProcessingRun, RiskResult
from inspections.serializers import InspectionProcessingRunSerializer
from inspections.services.comparison import InspectionComparisonService
from inspections.services.scoring import InspectionScoringService
from inspections.services.errors import InsufficientData, ProviderUnavailable, IncompleteAnalysis
from inspections.services.ocr import OCRExtractionPipeline, OCRExtractionResult
from tests.ocr_adapter import StaticOCRAdapter
from inspections.services.processing import InspectionIntelligencePipeline, InspectionProcessingService
from inspections.tasks import build_default_intelligence_pipeline, process_inspection_run

pytestmark = pytest.mark.django_db


@pytest.fixture
def inspection():
    organization = Organization.objects.create(name="Phase0")
    site = Site.objects.create(organization=organization, name="Site")
    user = create_member_user(username="phase0", organization=organization, site=site)
    obj = BatchInspection.objects.create(
        organization=organization, site=site, inspector=user,
        batch_number="B-01", received_at=timezone.now(),
    )
    Evidence.objects.create(
        inspection=obj, image=SimpleUploadedFile("label.pdf", b"%PDF-test"),
        evidence_type="batch_label", created_by=user,
    )
    return obj


@pytest.fixture
def run(inspection):
    return InspectionProcessingRun.objects.create(inspection=inspection, created_by=inspection.inspector)


def pipeline(fields=None, confidence=87, enabled_steps=None):
    result = OCRExtractionResult(
        provider_name="test-only", text="B-01", confidence=confidence,
        normalized_fields={"batch_number": "B-01"} if fields is None else fields,
    )
    return InspectionIntelligencePipeline(
        OCRExtractionPipeline([StaticOCRAdapter(result)]), enabled_steps=enabled_steps,
    )


def test_lifecycle_success_has_one_completion_and_persisted_timestamps(run):
    run.mark_queued(stage="ocr")
    queued = run.queued_at
    run.mark_processing(stage="comparison")
    run.mark_completed()
    run.refresh_from_db()
    assert run.status == "completed"
    assert queued <= run.execution_started_at <= run.execution_completed_at
    assert run.processing_duration == run.execution_completed_at - run.execution_started_at
    assert run.failed_at is None and run.cancelled_at is None
    with pytest.raises(ValueError):
        run.mark_completed()
    with pytest.raises(ValueError):
        run.mark_queued()


def test_failure_and_retry_reset_attempt_but_preserve_log(run):
    run.mark_queued()
    run.mark_processing()
    run.mark_failed("provider_unavailable", stage="ocr")
    run.refresh_from_db()
    assert run.failed_at >= run.execution_started_at
    assert run.execution_completed_at is None
    assert run.processing_duration is not None
    run.increment_retry()
    run.mark_queued()
    run.refresh_from_db()
    assert run.retry_count == 1 and run.status == "queued"
    assert run.failed_at is None and run.execution_started_at is None
    assert run.execution_completed_at is None and run.processing_duration is None
    assert any(entry["message"] == "Run failed." for entry in run.processing_log)


def test_cancelled_run_is_terminal_and_not_completed(run):
    run.mark_queued()
    run.mark_processing()
    run.mark_cancelled("No longer needed")
    run.refresh_from_db()
    assert run.cancelled_at >= run.execution_started_at
    assert run.execution_completed_at is None
    with pytest.raises(ValueError):
        run.mark_completed()
    with pytest.raises(ValueError):
        run.mark_queued()
    assert process_inspection_run.run(run.id) == run.id
    run.refresh_from_db()
    assert run.status == "cancelled"


def test_pending_run_cannot_complete_or_start_without_queue(run):
    with pytest.raises(ValueError):
        run.mark_completed()
    with pytest.raises(ValueError):
        run.mark_processing()


def test_all_stages_execute_and_results_survive_reload(run):
    summary = pipeline().run(run)
    run.refresh_from_db()
    risk = RiskResult.objects.get(pk=summary.risk_result_id)
    messages = [entry["message"] for entry in run.processing_log]
    assert [m for m in messages if m.startswith("Step completed:")] == [
        "Step completed: ocr.", "Step completed: comparison.", "Step completed: scoring.",
    ]
    assert messages.count("Run completed.") == 1
    assert run.status == "completed" and run.current_stage == "completed"
    assert run.ocr_summary["task_count"] == 1
    assert run.ocr_summary["normalized_fields"]["batch_number"] == "B-01"
    assert run.comparison_summary["sufficient_data"] is True
    assert run.scoring_summary["status"] == "assessed"
    assert run.provider_name == "test-only"
    assert run.risk_score == risk.risk_score == 0
    assert run.confidence == risk.confidence == 87
    assert risk.calculated_at == run.execution_completed_at
    assert run.inspection.evidences.get().ocr_tasks.count() == 1


@pytest.mark.parametrize("fields", [{}, {"medicine_name": "Only a name"}, {"batch_number": ""}])
def test_empty_or_non_comparable_extraction_is_unresolved(run, fields):
    with pytest.raises(InsufficientData):
        pipeline(fields=fields, confidence=100).run(run)
    run.refresh_from_db()
    assert run.status == "failed" and run.failure_reason == "insufficient_data"
    assert run.failed_at is not None and run.execution_completed_at is None
    assert run.risk_score is None and run.confidence is None and run.risk_level == ""
    assert run.scoring_summary["requires_review"] is True
    assert run.scoring_summary["risk_score"] is None
    assert not RiskResult.objects.filter(inspection=run.inspection).exists()


def test_missing_expected_field_is_not_falsely_reassuring(run):
    run.inspection.expiry_date = timezone.now().date()
    run.inspection.save(update_fields=["expiry_date"])
    with pytest.raises(InsufficientData):
        pipeline().run(run)
    run.refresh_from_db()
    assert "expiry_date" in run.comparison_summary["details"]["missing_comparison_fields"]


def test_direct_scoring_rejects_empty_extraction(inspection):
    evidence = list(inspection.evidences.all())
    comparison = InspectionComparisonService().compare(inspection, {}, evidence)
    assert comparison.confidence is None and not comparison.sufficient_data
    with pytest.raises(InsufficientData):
        InspectionScoringService().score(comparison, evidence_items=evidence, extraction_confidence=100)


def test_no_provider_is_explicit_and_never_creates_risk(run):
    with pytest.raises(ProviderUnavailable):
        build_default_intelligence_pipeline().run(run)
    run.refresh_from_db()
    assert run.status == "failed" and run.failure_reason == "provider_unavailable"
    assert run.execution_completed_at is None and run.risk_score is None
    assert not RiskResult.objects.filter(inspection=run.inspection).exists()


def test_worker_preserves_controlled_provider_failure(run):
    process_inspection_run.run(run.id)
    run.refresh_from_db()
    assert run.status == "failed" and run.failure_reason == "provider_unavailable"
    assert run.retry_count == 0
    process_inspection_run.run(run.id)
    run.refresh_from_db()
    assert run.status == "failed" and run.retry_count == 0


def test_no_evidence_requires_review(inspection):
    inspection.evidences.all().delete()
    run = InspectionProcessingRun.objects.create(inspection=inspection)
    with pytest.raises(InsufficientData):
        pipeline().run(run)
    run.refresh_from_db()
    assert run.failure_reason == "insufficient_data"


def test_enrichment_flag_cannot_activate_fake_success(run):
    with pytest.raises(ProviderUnavailable):
        pipeline(enabled_steps={"ai_enrichment": True}).run(run)
    run.refresh_from_db()
    assert run.status == "failed" and not run.risk_level
    assert not RiskResult.objects.filter(inspection=run.inspection).exists()


@pytest.mark.parametrize("flags", [
    {"scoring": False}, {"ocr": False, "comparison": False, "scoring": False},
])
def test_partial_stages_cannot_publish_final_analysis(run, flags):
    with pytest.raises(IncompleteAnalysis):
        pipeline(enabled_steps=flags).run(run)
    run.refresh_from_db()
    assert run.status == "failed" and run.failure_reason == "incomplete_analysis"
    assert run.execution_completed_at is None
    assert not RiskResult.objects.filter(inspection=run.inspection).exists()


def test_late_failure_publishes_no_risk(run, monkeypatch):
    runner = pipeline()
    monkeypatch.setattr(runner.scoring_service, "score", Mock(side_effect=RuntimeError("test failure")))
    with pytest.raises(RuntimeError):
        runner.run(run)
    run.refresh_from_db()
    assert run.status == "failed" and run.failure_reason == "processing_failed"
    assert run.ocr_summary["task_count"] == 1
    assert run.comparison_summary["sufficient_data"]
    assert not RiskResult.objects.filter(inspection=run.inspection).exists()


def test_risk_write_failure_rolls_back_completion(run, monkeypatch):
    monkeypatch.setattr(RiskResult.objects, "update_or_create", Mock(side_effect=RuntimeError("test db failure")))
    with pytest.raises(RuntimeError):
        pipeline().run(run)
    run.refresh_from_db()
    assert run.status == "failed" and run.execution_completed_at is None
    assert run.risk_score is None


def test_unknown_confidence_stays_unknown(run):
    pipeline(confidence=None).run(run)
    run.refresh_from_db()
    assert run.status == "completed" and run.confidence is None
    assert RiskResult.objects.get(inspection=run.inspection).confidence is None


def test_conflicting_documents_require_review(run):
    Evidence.objects.create(
        inspection=run.inspection, image=SimpleUploadedFile("second.pdf", b"%PDF-test"),
        evidence_type="batch_label",
    )
    adapter = Mock(provider_name="test-only")
    adapter.extract.side_effect = [
        OCRExtractionResult(provider_name="test-only", normalized_fields={"batch_number": "B-01"}),
        OCRExtractionResult(provider_name="test-only", normalized_fields={"batch_number": "OTHER"}),
    ]
    runner = InspectionIntelligencePipeline(OCRExtractionPipeline([adapter]))
    with pytest.raises(InsufficientData):
        runner.run(run)
    run.refresh_from_db()
    assert run.failure_reason == "insufficient_data" and run.risk_score is None


def test_scheduler_idempotency_and_post_commit_dispatch(inspection, django_capture_on_commit_callbacks):
    enqueue = Mock()
    service = InspectionProcessingService(enqueue)
    with django_capture_on_commit_callbacks(execute=True):
        run, created = service.schedule(inspection, triggered_by=inspection.inspector)
        duplicate, created_again = service.schedule(inspection)
        enqueue.assert_not_called()
    assert created and not created_again and run.id == duplicate.id
    enqueue.assert_called_once()
    run.refresh_from_db()
    assert run.created_by_id == inspection.inspector_id
    assert any(entry["message"].startswith("Duplicate") for entry in run.processing_log)


def test_dispatch_failure_persists_failed_run(inspection, django_capture_on_commit_callbacks):
    service = InspectionProcessingService(Mock(side_effect=ConnectionError("test broker offline")))
    with django_capture_on_commit_callbacks(execute=True):
        run, _ = service.schedule(inspection)
    run.refresh_from_db()
    assert run.status == "failed" and run.failure_reason == "dispatch_unavailable"
    assert run.execution_started_at is None and run.execution_completed_at is None


def test_retry_state_commits_before_celery_retry(run, monkeypatch):
    monkeypatch.setattr("inspections.tasks.build_default_ocr_pipeline", lambda: pipeline().ocr_pipeline)
    monkeypatch.setattr(InspectionIntelligencePipeline, "run", Mock(side_effect=RuntimeError("test transient error")))
    monkeypatch.setattr(process_inspection_run, "retry", Mock(side_effect=Retry("test retry")))
    with pytest.raises(Retry):
        process_inspection_run.run(run.id)
    run.refresh_from_db()
    assert run.status == "queued" and run.retry_count == 1
    assert run.execution_started_at is None
    assert any(entry["message"] == "Run failed." for entry in run.processing_log)


def test_duplicate_worker_delivery_does_not_restart_running_run(run, monkeypatch):
    run.mark_queued()
    run.mark_processing()
    build = Mock()
    monkeypatch.setattr("inspections.tasks.build_default_ocr_pipeline", build)
    assert process_inspection_run.run(run.id) == run.id
    build.assert_not_called()


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_processing_runs_cannot_be_written_through_generic_crud(run, method):
    client = APIClient()
    client.force_authenticate(run.inspection.inspector)
    path = "/api/processing-runs/" if method == "post" else f"/api/processing-runs/{run.id}/"
    response = getattr(client, method)(path, {"inspection": run.inspection_id, "status": "completed"}, format="json")
    assert response.status_code == 405
    run.refresh_from_db()
    assert run.status == "pending"


def test_run_serializer_has_no_phantom_or_writable_fields(run):
    serializer = InspectionProcessingRunSerializer(run)
    assert "enrichment_summary" not in serializer.fields
    assert all(field.read_only for field in serializer.fields.values())
    assert serializer.data["id"] == run.id


@pytest.mark.parametrize("flags", [[], {"unknown": True}, {"ocr": "not a boolean"}])
def test_invalid_processing_options_are_rejected_before_run_creation(inspection, flags):
    client = APIClient()
    client.force_authenticate(inspection.inspector)
    response = client.post(
        f"/api/batch-inspections/{inspection.id}/process-intelligence/",
        {"enabled_steps": flags}, format="json",
    )
    assert response.status_code == 400
    assert not inspection.processing_runs.exists()


def test_failed_processing_summary_exposes_review_required(run):
    with pytest.raises(InsufficientData):
        pipeline(fields={}).run(run)
    client = APIClient()
    client.force_authenticate(run.inspection.inspector)
    response = client.get(f"/api/batch-inspections/{run.inspection_id}/processing-status/")
    assert response.status_code == 200
    assert response.data["requires_review"] is True
    assert response.data["failure_reason"] == "insufficient_data"


def test_new_attempt_does_not_reuse_old_extraction_confidence(run):
    pipeline().run(run)
    second = InspectionProcessingRun.objects.create(inspection=run.inspection)
    pipeline(confidence=None).run(second)
    second.refresh_from_db()
    assert second.status == "completed" and second.confidence is None
    assert second.ocr_summary["confidence"] is None


def test_cancellation_during_stage_is_preserved(run, monkeypatch):
    from inspections.services.errors import ProcessingCancelled

    runner = pipeline()
    original_compare = runner.comparison_service.compare

    def cancel_then_compare(*args, **kwargs):
        other = InspectionProcessingRun.objects.get(pk=run.pk)
        other.mark_cancelled("Cancelled while comparison was running")
        return original_compare(*args, **kwargs)

    monkeypatch.setattr(runner.comparison_service, "compare", cancel_then_compare)
    with pytest.raises(ProcessingCancelled):
        runner.run(run)
    run.refresh_from_db()
    assert run.status == "cancelled" and run.cancelled_at is not None
    assert run.execution_completed_at is None
    assert any(entry["message"] == "Run cancelled." for entry in run.processing_log)
    assert not RiskResult.objects.filter(inspection=run.inspection).exists()


def test_failed_attempt_keeps_historical_risk_but_marks_latest_run_unresolved(run):
    pipeline().run(run)
    historical = RiskResult.objects.get(inspection=run.inspection)
    second = InspectionProcessingRun.objects.create(inspection=run.inspection)
    with pytest.raises(InsufficientData):
        pipeline(fields={}).run(second)
    historical.refresh_from_db()
    second.refresh_from_db()
    assert historical.calculated_at == run.execution_completed_at
    assert second.status == "failed" and second.scoring_summary["requires_review"]
    assert second.risk_score is None


def test_exhausted_retry_is_failed_with_no_completion(run, monkeypatch):
    monkeypatch.setattr(InspectionIntelligencePipeline, "run", Mock(side_effect=RuntimeError("test permanent error")))
    monkeypatch.setattr(process_inspection_run, "max_retries", 0)
    with pytest.raises(RuntimeError):
        process_inspection_run.run(run.id)
    run.refresh_from_db()
    assert run.status == "failed" and run.failed_at is not None
    assert run.execution_completed_at is None and run.retry_count == 0
