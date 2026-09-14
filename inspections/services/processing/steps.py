from dataclasses import dataclass, field

from inspections.models import Evidence, OCRTask, InspectionProcessingRun
from inspections.services.errors import InsufficientData, ProviderUnavailable
from inspections.services.ocr.base import OCRProviderError


@dataclass
class InspectionProcessingContext:
    run: InspectionProcessingRun
    inspection: object
    evidence_items: list[Evidence] = field(default_factory=list)
    ocr_tasks: list[OCRTask] = field(default_factory=list)
    normalized_fields: dict = field(default_factory=dict)
    ocr_provider_name: str = ""
    extracted_text: str = ""
    confidence: float | None = None
    comparison_result: object | None = None
    scoring_result: object | None = None
    active_steps: dict[str, bool] = field(default_factory=dict)


class BaseProcessingStep:
    name = "base"
    stage = "ocr"

    def enabled(self, context):
        return context.active_steps.get(self.name, False)

    def execute(self, context):
        raise NotImplementedError


class OCRProcessingStep(BaseProcessingStep):
    name = "ocr"
    stage = "ocr"

    def __init__(self, ocr_executor):
        self.ocr_executor = ocr_executor

    def execute(self, context):
        if not context.evidence_items:
            raise InsufficientData("No evidence is available; human review required.")
        if not self.ocr_executor.pipeline.adapters:
            raise ProviderUnavailable("No OCR provider is configured.")
        confidences = []
        providers = set()
        texts = []
        for evidence in context.evidence_items:
            # Each run processes the current file, never a stale/client-edited task.
            task = OCRTask.objects.create(evidence=evidence)
            context.ocr_tasks.append(task)
            self.ocr_executor.queue(task, processor_version="ocr-v1")
            self.ocr_executor.execute(task)
            if task.status != "completed":
                raise OCRProviderError(f"OCR failed for evidence {evidence.id}.")
            providers.add(task.provider_name)
            context.ocr_provider_name = ",".join(sorted(providers))[:64]
            texts.append(task.evidence.extracted_text or "")
            context.extracted_text = "\n".join(texts)
            confidences.append(task.evidence.extraction_confidence)
            for key, value in (task.normalized_output or {}).items():
                if not value:
                    continue
                previous = context.normalized_fields.get(key)
                if previous and previous != value:
                    raise InsufficientData("Conflicting extracted fields; human review required.")
                context.normalized_fields[key] = value
        if confidences and all(value is not None for value in confidences):
            context.confidence = min(confidences)


class ComparisonProcessingStep(BaseProcessingStep):
    name = "comparison"
    stage = "comparison"

    def __init__(self, comparison_service):
        self.comparison_service = comparison_service

    def execute(self, context):
        context.comparison_result = self.comparison_service.compare(
            context.inspection, context.normalized_fields, context.evidence_items,
        )


class ScoringProcessingStep(BaseProcessingStep):
    name = "scoring"
    stage = "scoring"

    def __init__(self, scoring_service):
        self.scoring_service = scoring_service

    def execute(self, context):
        context.scoring_result = self.scoring_service.score(
            context.comparison_result,
            evidence_items=context.evidence_items,
            extraction_confidence=context.confidence,
        )
