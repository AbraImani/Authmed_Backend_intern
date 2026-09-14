from dataclasses import dataclass, field

from django.conf import settings

from inspections.models import InspectionProcessingRun, RiskResult
from inspections.services.comparison import InspectionComparisonService
from inspections.services.inference import FakeInferenceProvider
from inspections.services.ocr import OCRExtractionPipeline, OCRTaskExecutionService
from inspections.services.scoring import InspectionScoringService
from .steps import (
    AIEnrichmentProcessingStep,
    ComparisonProcessingStep,
    InspectionProcessingContext,
    OCRProcessingStep,
    ScoringProcessingStep,
)


@dataclass
class InspectionIntelligenceSummary:
    run_id: int
    comparison_summary: dict = field(default_factory=dict)
    scoring_summary: dict = field(default_factory=dict)
    ocr_summary: dict = field(default_factory=dict)
    risk_result_id: int | None = None


class InspectionIntelligencePipeline:
    """Orchestrate OCR, comparison, and scoring for one inspection."""

    def __init__(self, ocr_pipeline: OCRExtractionPipeline, inference_provider=None, enabled_steps=None):
        self.ocr_pipeline = ocr_pipeline
        self.comparison_service = InspectionComparisonService()
        self.scoring_service = InspectionScoringService()
        self.ocr_executor = OCRTaskExecutionService(ocr_pipeline)
        self.inference_provider = inference_provider or FakeInferenceProvider()
        self.enabled_steps = enabled_steps or getattr(settings, "INSPECTION_INTELLIGENCE_STEPS", {})

    def build_steps(self):
        return [
            OCRProcessingStep(self.ocr_executor),
            ComparisonProcessingStep(self.comparison_service),
            ScoringProcessingStep(self.scoring_service),
            AIEnrichmentProcessingStep(self.inference_provider),
        ]

    def run(self, run: InspectionProcessingRun):
        inspection = run.inspection
        run.append_log("Processing pipeline started.")
        context = InspectionProcessingContext(
            run=run,
            inspection=inspection,
            evidence_items=list(inspection.evidences.order_by("display_order", "created_at")),
            active_steps=self.enabled_steps,
        )

        for step in self.build_steps():
            if not step.enabled(context):
                run.append_log(f"Step skipped: {step.name}.", payload={"step": step.name})
                continue
            run.current_stage = step.stage
            run.save(update_fields=["current_stage", "updated_at"])
            step.execute(context)
            run.append_log(f"Step completed: {step.name}.", payload={"step": step.name})

            run.ocr_summary = {
                "task_count": len(context.ocr_tasks),
                "provider_name": context.ocr_provider_name,
                "normalized_fields": context.normalized_fields,
                "extracted_text": context.extracted_text,
                "confidence": float(context.confidence) if context.confidence is not None else None,
            }
            if context.comparison_result is not None:
                run.comparison_summary = {
                    "mismatch_categories": context.comparison_result.mismatch_categories,
                    "weighted_score": float(context.comparison_result.weighted_score),
                    "confidence": float(context.comparison_result.confidence),
                    "summary": context.comparison_result.summary,
                    "details": context.comparison_result.details,
                }
            if context.scoring_result is not None:
                run.scoring_summary = {
                    "risk_score": float(context.scoring_result.risk_score),
                    "confidence": float(context.scoring_result.confidence),
                    "risk_level": context.scoring_result.risk_level,
                    "explanation": context.scoring_result.explanation,
                    "triggered_rules": context.scoring_result.triggered_rules,
                }
                run.triggered_rules = context.scoring_result.triggered_rules
                run.risk_level = context.scoring_result.risk_level
                run.risk_score = context.scoring_result.risk_score
                run.confidence = context.scoring_result.confidence
                run.explanation = context.scoring_result.explanation
                risk_result, _ = RiskResult.objects.update_or_create(
                    inspection=inspection,
                    defaults={
                        "risk_score": context.scoring_result.risk_score,
                        "suspicion_level": context.scoring_result.risk_level.lower(),
                        "confidence": context.scoring_result.confidence,
                        "flags": context.scoring_result.triggered_rules,
                        "reason": context.scoring_result.explanation,
                        "calculated_at": run.execution_completed_at,
                    },
                )
            else:
                risk_result = None

            run.enrichment_summary = context.enrichment_summary
            run.provider_name = context.ocr_provider_name
            run.mark_completed()

            return InspectionIntelligenceSummary(
                run_id=run.id,
                comparison_summary=run.comparison_summary,
                scoring_summary=run.scoring_summary,
                ocr_summary=run.ocr_summary,
                risk_result_id=risk_result.id if risk_result is not None else None,
            )
