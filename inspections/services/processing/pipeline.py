from dataclasses import dataclass, field
import logging

from django.db import transaction

from inspections.models import InspectionProcessingRun, RiskResult
from inspections.services.comparison import InspectionComparisonService
from inspections.services.errors import (
    IncompleteAnalysis, ProcessingCancelled, ProcessingError, ProviderUnavailable,
)
from inspections.services.ocr import OCRExtractionPipeline, OCRTaskExecutionService
from inspections.services.scoring import InspectionScoringService
from .config import resolve_enabled_steps
from .steps import (
    ComparisonProcessingStep, InspectionProcessingContext,
    OCRProcessingStep, ScoringProcessingStep,
)

logger = logging.getLogger(__name__)


def _number(value):
    return float(value) if value is not None else None


@dataclass
class InspectionIntelligenceSummary:
    run_id: int
    comparison_summary: dict = field(default_factory=dict)
    scoring_summary: dict = field(default_factory=dict)
    ocr_summary: dict = field(default_factory=dict)
    risk_result_id: int | None = None


class InspectionIntelligencePipeline:
    """Execute all requested stages; publish a risk only after complete success."""

    def __init__(self, ocr_pipeline: OCRExtractionPipeline, enabled_steps=None):
        self.ocr_pipeline = ocr_pipeline
        self.comparison_service = InspectionComparisonService()
        self.scoring_service = InspectionScoringService()
        self.ocr_executor = OCRTaskExecutionService(ocr_pipeline)
        self.enabled_steps = resolve_enabled_steps(enabled_steps)

    def build_steps(self):
        return [
            OCRProcessingStep(self.ocr_executor),
            ComparisonProcessingStep(self.comparison_service),
            ScoringProcessingStep(self.scoring_service),
        ]

    def _persist_summaries(self, context):
        with transaction.atomic():
            current = InspectionProcessingRun.objects.select_for_update().get(pk=context.run.pk)
            if current.status == "cancelled":
                raise ProcessingCancelled("Run was cancelled.")
            if current.status not in {"pending", "queued", "processing"}:
                raise IncompleteAnalysis("Run is no longer processing.")
            self._save_summaries(context)

    def _save_summaries(self, context):
        run = context.run
        run.ocr_summary = {
            "task_count": len(context.ocr_tasks),
            "task_ids": [task.id for task in context.ocr_tasks],
            "provider_name": context.ocr_provider_name,
            "normalized_fields": context.normalized_fields,
            "extracted_text": context.extracted_text,
            "confidence": _number(context.confidence),
        }
        run.provider_name = context.ocr_provider_name
        comparison = context.comparison_result
        if comparison is not None:
            run.comparison_summary = {
                "mismatch_categories": comparison.mismatch_categories,
                "weighted_score": _number(comparison.weighted_score),
                "confidence": _number(comparison.confidence),
                "sufficient_data": comparison.sufficient_data,
                "compared_fields": comparison.compared_fields,
                "summary": comparison.summary,
                "details": comparison.details,
            }
        scoring = context.scoring_result
        if scoring is not None:
            run.scoring_summary = {
                "status": "calculated",
                "risk_score": _number(scoring.risk_score),
                "confidence": _number(scoring.confidence),
                "risk_level": scoring.risk_level,
                "explanation": scoring.explanation,
                "triggered_rules": scoring.triggered_rules,
            }
        run.save(update_fields=[
            "ocr_summary", "comparison_summary", "scoring_summary", "provider_name",
            "processing_log", "updated_at",
        ])

    def run(self, run: InspectionProcessingRun):
        if run.status == "pending":
            run.mark_queued()
        if run.status == "queued":
            run.mark_processing()
        if run.status != "processing":
            raise ValueError(f"Cannot execute a run in state {run.status}.")
        context = InspectionProcessingContext(
            run=run, inspection=run.inspection,
            evidence_items=list(run.inspection.evidences.order_by("display_order", "created_at")),
            active_steps=self.enabled_steps,
        )
        try:
            if self.enabled_steps["ai_enrichment"]:
                raise ProviderUnavailable("AI enrichment is not configured in Phase 0.")
            executed = set()
            for step in self.build_steps():
                with transaction.atomic():
                    current = InspectionProcessingRun.objects.select_for_update().get(pk=run.pk)
                    if current.status == "cancelled":
                        raise ProcessingCancelled("Run was cancelled.")
                    if current.status != "processing":
                        raise IncompleteAnalysis("Run is no longer processing.")
                    if not step.enabled(context):
                        run.append_log(f"Step skipped: {step.name}.")
                        run.save(update_fields=["processing_log", "updated_at"])
                        continue
                    run.current_stage = step.stage
                    run.save(update_fields=["current_stage", "updated_at"])
                step.execute(context)
                executed.add(step.name)
                run.append_log(f"Step completed: {step.name}.", payload={"step": step.name})
                self._persist_summaries(context)

            if not {"ocr", "comparison", "scoring"}.issubset(executed) or context.scoring_result is None:
                raise IncompleteAnalysis("Required analysis stages did not finish; human review required.")
            # Completion and risk publication either both commit or neither does.
            with transaction.atomic():
                current = InspectionProcessingRun.objects.select_for_update().get(pk=run.pk)
                if current.status == "cancelled":
                    raise ProcessingCancelled("Run was cancelled.")
                if current.status != "processing":
                    raise IncompleteAnalysis("Run is no longer processing.")
                scoring = context.scoring_result
                run.triggered_rules = scoring.triggered_rules
                run.risk_level = scoring.risk_level
                run.risk_score = scoring.risk_score
                run.confidence = scoring.confidence
                run.explanation = scoring.explanation
                run.scoring_summary["status"] = "assessed"
                run.save(update_fields=["triggered_rules", "risk_level", "risk_score", "confidence", "explanation", "scoring_summary", "updated_at"])
                run.mark_completed()
                risk, _ = RiskResult.objects.update_or_create(
                    inspection=run.inspection,
                    defaults={
                        "risk_score": scoring.risk_score,
                        "suspicion_level": scoring.risk_level.lower(),
                        "confidence": scoring.confidence,
                        "flags": scoring.triggered_rules,
                        "reason": scoring.explanation,
                        "calculated_at": run.execution_completed_at,
                    },
                )
            return InspectionIntelligenceSummary(
                run_id=run.id, comparison_summary=run.comparison_summary,
                scoring_summary=run.scoring_summary, ocr_summary=run.ocr_summary,
                risk_result_id=risk.id,
            )
        except ProcessingCancelled:
            run.refresh_from_db()
            raise
        except Exception as exc:
            code = exc.code if isinstance(exc, ProcessingError) else "processing_failed"
            message = str(exc) if isinstance(exc, ProcessingError) else "Analysis failed; human review required."
            if not isinstance(exc, ProcessingError):
                logger.exception("Inspection processing failed for run %s", run.pk)
            with transaction.atomic():
                current = InspectionProcessingRun.objects.select_for_update().get(pk=run.pk)
                if current.status in {"pending", "queued", "processing"}:
                    # Publish no score from an interrupted or insufficient analysis.
                    context.run = current
                    context.scoring_result = None
                    self._persist_summaries(context)
                    current.risk_score = None
                    current.confidence = None
                    current.risk_level = ""
                    current.triggered_rules = []
                    current.explanation = message
                    current.scoring_summary = {
                        "status": code, "requires_review": True,
                        "risk_score": None, "confidence": None, "risk_level": None,
                    }
                    current.save(update_fields=["risk_score", "confidence", "risk_level", "triggered_rules", "explanation", "scoring_summary", "updated_at"])
                    current.mark_failed(code, stage=current.current_stage)
            run.refresh_from_db()
            raise
