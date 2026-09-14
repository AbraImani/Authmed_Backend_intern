from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class InspectionScoringResult:
    risk_score: Decimal
    confidence: Decimal
    risk_level: str
    explanation: str
    triggered_rules: list[dict] = field(default_factory=list)


class InspectionScoringService:
    """Convert comparison signals into a transparent risk score."""

    def score(self, comparison_result, evidence_items=None, supplier_confidence=100):
        evidence_items = list(evidence_items or [])
        evidence_completeness_penalty = 0 if evidence_items else 20
        mismatch_penalty = sum(
            {
                "batch_mismatch": 30,
                "expiry_mismatch": 25,
                "manufacturer_mismatch": 20,
                "barcode_mismatch": 20,
                "packaging_inconsistency": 15,
                "missing_evidence": 20,
            }.get(category, 10)
            for category in comparison_result.mismatch_categories
        )
        base_risk = min(100, mismatch_penalty + evidence_completeness_penalty)
        supplier_penalty = max(0, 100 - int(supplier_confidence)) // 5
        risk_score = min(100, base_risk + supplier_penalty)

        if risk_score >= 85:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        confidence = max(0, min(100, int(comparison_result.confidence) - evidence_completeness_penalty))
        explanation = comparison_result.summary
        triggered_rules = [
            {"rule": category, "penalty": score}
            for category, score in {
                "batch_mismatch": 30,
                "expiry_mismatch": 25,
                "manufacturer_mismatch": 20,
                "barcode_mismatch": 20,
                "packaging_inconsistency": 15,
                "missing_evidence": 20,
            }.items()
            if category in comparison_result.mismatch_categories
        ]

        return InspectionScoringResult(
            risk_score=Decimal(str(risk_score)).quantize(Decimal("1.00")),
            confidence=Decimal(str(confidence)).quantize(Decimal("1.00")),
            risk_level=risk_level,
            explanation=explanation,
            triggered_rules=triggered_rules,
        )
