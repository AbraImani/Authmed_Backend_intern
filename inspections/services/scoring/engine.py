from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from inspections.services.comparison import InspectionComparisonService
from inspections.services.errors import InsufficientData


@dataclass
class InspectionScoringResult:
    risk_score: Decimal
    confidence: Decimal | None
    risk_level: str
    explanation: str
    triggered_rules: list[dict] = field(default_factory=list)


class InspectionScoringService:
    """Existing deterministic rules, gated on sufficient comparable data."""

    def score(self, comparison_result, evidence_items=None, supplier_confidence=100, extraction_confidence=None):
        if not evidence_items or comparison_result is None or not comparison_result.sufficient_data:
            raise InsufficientData("Insufficient comparable data; human review required.")
        weights = InspectionComparisonService.WEIGHTS
        mismatch_penalty = sum(weights.get(category, 10) for category in comparison_result.mismatch_categories)
        supplier_penalty = max(0, 100 - int(supplier_confidence)) // 5
        risk_score = min(100, mismatch_penalty + supplier_penalty)
        if risk_score >= 85:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Do not manufacture certainty when the provider reports none.
        confidence = None
        if extraction_confidence is not None:
            try:
                value = Decimal(str(extraction_confidence))
                if value.is_finite() and 0 <= value <= 100:
                    confidence = min(value, comparison_result.confidence).quantize(Decimal("1.00"))
            except (InvalidOperation, TypeError, ValueError):
                pass
        return InspectionScoringResult(
            risk_score=Decimal(str(risk_score)).quantize(Decimal("1.00")),
            confidence=confidence,
            risk_level=risk_level,
            explanation=comparison_result.summary,
            triggered_rules=[
                {"rule": category, "penalty": weights.get(category, 10)}
                for category in comparison_result.mismatch_categories
            ],
        )
