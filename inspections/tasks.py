from celery import shared_task

from inspections.models import OCRTask
from inspections.services.ocr import OCRExtractionPipeline, OCRTaskExecutionService
from inspections.services.ocr.easyocr_adapter import EasyOCRAdapter
from inspections.services.ocr.paddleocr_adapter import PaddleOCRAdapter


def build_default_ocr_pipeline():
    """Build the default OCR pipeline from configured providers.

    The default setup only prepares the execution path; provider adapters still
    need to be configured before OCR can succeed in production.
    """
    return OCRExtractionPipeline([EasyOCRAdapter(), PaddleOCRAdapter()])


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_ocr_task(self, ocr_task_id):
    task = OCRTask.objects.select_related("evidence", "evidence__inspection").get(pk=ocr_task_id)
    service = OCRTaskExecutionService(build_default_ocr_pipeline())
    service.queue(task, provider_name="configured-providers", processor_version="ocr-task-v1")
    return service.execute(task)
