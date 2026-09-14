from celery import shared_task
from django.db import transaction

from inspections.models import OCRTask, InspectionProcessingRun
from inspections.services.ocr import OCRExtractionPipeline, OCRTaskExecutionService
from inspections.services.ocr.easyocr_adapter import EasyOCRAdapter
from inspections.services.ocr.paddleocr_adapter import PaddleOCRAdapter
from inspections.services.processing import InspectionIntelligencePipeline


def build_default_ocr_pipeline():
    """Build the default OCR pipeline from configured providers.

    The default setup only prepares the execution path; provider adapters still
    need to be configured before OCR can succeed in production.
    """
    return OCRExtractionPipeline([EasyOCRAdapter(), PaddleOCRAdapter()])


def build_default_intelligence_pipeline():
    return InspectionIntelligencePipeline(build_default_ocr_pipeline())


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_ocr_task(self, ocr_task_id):
    task = OCRTask.objects.select_related("evidence", "evidence__inspection").get(pk=ocr_task_id)
    service = OCRTaskExecutionService(build_default_ocr_pipeline())
    service.queue(task, provider_name="configured-providers", processor_version="ocr-task-v1")
    return service.execute(task)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_inspection_run(self, run_id, enabled_steps=None):
    enabled_steps = enabled_steps or {}
    with transaction.atomic():
        run = InspectionProcessingRun.objects.select_for_update().select_related("inspection").get(pk=run_id)
        if run.status == "completed":
            return run.id
        if run.status in {"failed", "cancelled"}:
            run.mark_queued(stage=run.current_stage or "ocr")
        run.mark_processing(stage=run.current_stage or "ocr")

    pipeline = InspectionIntelligencePipeline(build_default_ocr_pipeline(), enabled_steps=enabled_steps)
    try:
        summary = pipeline.run(run)
        return summary.run_id
    except Exception as exc:
        with transaction.atomic():
            run = InspectionProcessingRun.objects.select_for_update().get(pk=run_id)
            run.increment_retry()
            run.append_log("Celery retry scheduled.", level="warning", payload={"error": str(exc)})
            if self.request.retries < self.max_retries:
                run.mark_queued(stage=run.current_stage or "ocr")
                raise self.retry(exc=exc)
            run.mark_failed(str(exc), stage=run.current_stage or "failed")
        raise
