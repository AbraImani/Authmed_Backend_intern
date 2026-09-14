from dataclasses import dataclass, field

from inspections.models import Evidence, OCRTask, InspectionProcessingRun
from inspections.services.comparison import InspectionComparisonService
from inspections.services.scoring import InspectionScoringService


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
    enrichment_summary: dict = field(default_factory=dict)
    active_steps: dict[str, bool] = field(default_factory=dict)


class BaseProcessingStep:
    name = "base"
    stage = "ocr"

    def enabled(self, context: InspectionProcessingContext):
        return context.active_steps.get(self.name, True)

    def execute(self, context: InspectionProcessingContext):
        raise NotImplementedError


class OCRProcessingStep(BaseProcessingStep):
    name = "ocr"
    stage = "ocr"

    def __init__(self, ocr_executor):
        self.ocr_executor = ocr_executor

    def execute(self, context: InspectionProcessingContext):
        for evidence in context.evidence_items:
            task = evidence.ocr_tasks.order_by("-created_at").first() or OCRTask.objects.create(evidence=evidence)
            if task.status not in {"completed", "cancelled"}:
                self.ocr_executor.queue(task, provider_name=getattr(task, "provider_name", ""), processor_version=task.processor_version or "ocr-v1")
                self.ocr_executor.execute(task)
            context.ocr_tasks.append(task)

        if context.ocr_tasks:
            latest_task = context.ocr_tasks[-1]
            context.normalized_fields = latest_task.normalized_output or {}
            context.ocr_provider_name = latest_task.provider_name or ""
            context.extracted_text = latest_task.evidence.extracted_text or ""
            context.confidence = latest_task.evidence.extraction_confidence


class ComparisonProcessingStep(BaseProcessingStep):
    name = "comparison"
    stage = "comparison"

    def __init__(self, comparison_service: InspectionComparisonService):
        self.comparison_service = comparison_service

    def execute(self, context: InspectionProcessingContext):
        context.comparison_result = self.comparison_service.compare(
            context.inspection,
            context.normalized_fields,
            context.evidence_items,
        )


class ScoringProcessingStep(BaseProcessingStep):
    name = "scoring"
    stage = "scoring"

    def __init__(self, scoring_service: InspectionScoringService):
        self.scoring_service = scoring_service

    def execute(self, context: InspectionProcessingContext):
        context.scoring_result = self.scoring_service.score(
            context.comparison_result,
            evidence_items=context.evidence_items,
            supplier_confidence=100,
        )


class AIEnrichmentProcessingStep(BaseProcessingStep):
    name = "ai_enrichment"
    stage = "scoring"

    def __init__(self, inference_provider):
        self.inference_provider = inference_provider

    def execute(self, context: InspectionProcessingContext):
        context.enrichment_summary = self.inference_provider.infer(context)
