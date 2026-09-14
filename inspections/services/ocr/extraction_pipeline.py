from dataclasses import dataclass, field
from typing import Iterable

from inspections.models import OCRTask
from inspections.services.normalization import normalize_ocr_payload
from .base import OCRProviderError
from inspections.services.errors import ProviderUnavailable


@dataclass
class OCRPipelineOutcome:
    provider_name: str
    text: str
    confidence: float | None
    normalized_fields: dict
    raw_output: dict
    logs: list[dict] = field(default_factory=list)


class OCRExtractionPipeline:
    """Try OCR providers in order and normalize their outputs.

    The pipeline stays provider-agnostic so a future production adapter can be
    plugged in without changing task execution or downstream processing.
    """

    def __init__(self, adapters: Iterable):
        self.adapters = list(adapters)

    def run(self, file_obj):
        if not self.adapters:
            raise ProviderUnavailable("No OCR provider is configured.")
        errors = []
        for adapter in self.adapters:
            try:
                file_obj.seek(0)
                result = adapter.extract(file_obj)
                normalized = normalize_ocr_payload(
                    {
                        "provider_name": result.provider_name,
                        "text": result.text,
                        "confidence": result.confidence,
                        "raw_output": result.raw_output or {},
                        "logs": result.logs or [],
                        **(result.normalized_fields or {}),
                    }
                )
                return OCRPipelineOutcome(
                    provider_name=normalized["provider_name"],
                    text=normalized["text"],
                    confidence=normalized["confidence"],
                    normalized_fields=normalized["normalized_fields"],
                    raw_output=normalized["raw_output"],
                    logs=normalized["logs"],
                )
            except Exception as exc:
                errors.append({"provider": getattr(adapter, "provider_name", "unknown"), "error": str(exc)})
        raise OCRProviderError("All OCR providers failed.")


class OCRTaskExecutionService:
    """Execute OCR tasks and persist lifecycle state transitions."""

    def __init__(self, pipeline: OCRExtractionPipeline):
        self.pipeline = pipeline

    def execute(self, task: OCRTask):
        if task.status in {"completed", "cancelled"}:
            task.append_log("Task skipped because it is already terminal.", level="warning")
            task.save(update_fields=["processing_log", "updated_at"])
            return task

        task.mark_processing()
        try:
            outcome = self.pipeline.run(task.evidence.image)
            task.mark_completed(
                normalized_output=outcome.normalized_fields,
                raw_output=outcome.raw_output,
                provider_name=outcome.provider_name,
                extracted_text=outcome.text,
                confidence=outcome.confidence,
            )
            for log_entry in outcome.logs:
                task.append_log(log_entry.get("message", "OCR provider log."), level=log_entry.get("level", "info"), payload=log_entry.get("payload", {}))
            task.save(update_fields=["processing_log", "updated_at"])
            return task
        except Exception as exc:
            task.mark_failed(str(exc), provider_name=getattr(task, "provider_name", ""), processor_version=task.processor_version)
            return task

    def queue(self, task: OCRTask, provider_name="", processor_version=""):
        task.mark_queued(provider_name=provider_name, processor_version=processor_version)
        return task

    def retry(self, task: OCRTask):
        task.increment_retry()
        task.status = "queued"
        task.error_message = ""
        task.append_log("Task queued for retry.")
        task.save(update_fields=["status", "error_message", "processing_log", "updated_at", "retry_count"])
        return task
