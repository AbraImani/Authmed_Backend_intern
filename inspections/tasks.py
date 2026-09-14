from celery import shared_task
from django.db import transaction

from inspections.models import OCRTask, InspectionProcessingRun
from inspections.services.errors import ProcessingError
from inspections.services.ocr import OCRExtractionPipeline, OCRTaskExecutionService
from inspections.services.processing import InspectionIntelligencePipeline


def build_default_ocr_pipeline():
    """Phase 0 has no configured real provider; never use a fake fallback."""
    return OCRExtractionPipeline([])


def build_default_intelligence_pipeline():
    return InspectionIntelligencePipeline(build_default_ocr_pipeline())


@shared_task
def process_ocr_task(ocr_task_id):
    task = OCRTask.objects.select_related("evidence", "evidence__inspection").get(pk=ocr_task_id)
    if task.status in {"completed", "cancelled"}:
        return task.id
    service = OCRTaskExecutionService(build_default_ocr_pipeline())
    service.queue(task, processor_version="ocr-task-v1")
    service.execute(task)
    return task.id


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_inspection_run(self, run_id, enabled_steps=None):
    with transaction.atomic():
        run = InspectionProcessingRun.objects.select_for_update().select_related("inspection").get(pk=run_id)
        # Duplicate delivery must not resurrect terminal runs or execute twice.
        if run.status not in {"pending", "queued"}:
            return run.id
        if run.status == "pending":
            run.mark_queued()
        run.mark_processing()
    try:
        pipeline = InspectionIntelligencePipeline(build_default_ocr_pipeline(), enabled_steps=enabled_steps)
        return pipeline.run(run).run_id
    except ProcessingError:
        # Controlled unavailable/insufficient/cancelled outcomes are persisted by
        # the pipeline. Retrying without new data/provider would be misleading.
        return run.id
    except Exception as exc:
        retry = False
        with transaction.atomic():
            run = InspectionProcessingRun.objects.select_for_update().get(pk=run_id)
            if run.status == "processing":
                run.mark_failed("processing_failed", stage=run.current_stage)
            if run.status == "failed" and self.request.retries < self.max_retries:
                run.increment_retry()
                run.mark_queued()
                run.append_log("Celery retry scheduled.", level="warning")
                run.save(update_fields=["processing_log", "updated_at"])
                retry = True
        # Celery raises Retry: it must happen AFTER the state transaction commits.
        if retry:
            raise self.retry(exc=exc)
        raise
