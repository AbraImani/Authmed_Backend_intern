from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class InspectionComparisonResult:
    mismatch_categories: list[str] = field(default_factory=list)
    weighted_score: Decimal | None = None
    confidence: Decimal | None = None
    sufficient_data: bool = False
    compared_fields: list[str] = field(default_factory=list)
    summary: str = ""
    details: dict = field(default_factory=dict)

    @property
    def has_mismatches(self):
        return bool(self.mismatch_categories)


class InspectionComparisonService:
    """Explainable rule-based comparison for inspection intelligence."""

    WEIGHTS = {
        "batch_mismatch": 30,
        "expiry_mismatch": 25,
        "manufacturer_mismatch": 20,
        "barcode_mismatch": 20,
        "packaging_inconsistency": 15,
        "missing_evidence": 20,
    }

    def compare(self, inspection, normalized_ocr_fields, evidence_items):
        normalized_ocr_fields = normalized_ocr_fields or {}
        evidence_items = list(evidence_items or [])
        mismatches = []
        details = {}

        batch_number = normalized_ocr_fields.get("batch_number")
        if batch_number and inspection.batch_number and batch_number != inspection.batch_number:
            mismatches.append("batch_mismatch")
            details["batch_mismatch"] = {
                "expected": inspection.batch_number,
                "observed": batch_number,
            }

        expiry_date = normalized_ocr_fields.get("expiry_date")
        if expiry_date and inspection.expiry_date and expiry_date != inspection.expiry_date.isoformat():
            mismatches.append("expiry_mismatch")
            details["expiry_mismatch"] = {
                "expected": inspection.expiry_date.isoformat(),
                "observed": expiry_date,
            }

        manufacturer = (normalized_ocr_fields.get("manufacturer") or "").upper()
        supplier_name = getattr(inspection.supplier, "name", "").upper()
        product_supplier_name = getattr(getattr(inspection.product, "supplier", None), "name", "").upper()
        if manufacturer and manufacturer not in {supplier_name, product_supplier_name}:
            mismatches.append("manufacturer_mismatch")
            details["manufacturer_mismatch"] = {
                "expected": inspection.supplier.name if inspection.supplier else getattr(getattr(inspection.product, "supplier", None), "name", None),
                "observed": normalized_ocr_fields.get("manufacturer"),
            }

        barcode_data = normalized_ocr_fields.get("barcode_data")
        product_sku = getattr(inspection.product, "sku", "")
        if barcode_data and product_sku and barcode_data != product_sku.upper():
            mismatches.append("barcode_mismatch")
            details["barcode_mismatch"] = {
                "expected": product_sku,
                "observed": barcode_data,
            }

        evidence_types = {getattr(item, "evidence_type", None) for item in evidence_items}
        if not evidence_items:
            mismatches.append("missing_evidence")
            details["missing_evidence"] = {"expected": "at least one evidence item", "observed": 0}
        elif "package_photo" not in evidence_types and "batch_label" not in evidence_types:
            mismatches.append("packaging_inconsistency")
            details["packaging_inconsistency"] = {
                "expected": ["package_photo", "batch_label"],
                "observed": sorted(evidence_types),
            }

        expected = {
            "batch_number": inspection.batch_number,
            "expiry_date": inspection.expiry_date,
            "manufacturer": supplier_name or product_supplier_name,
            "barcode_data": product_sku,
        }
        required = {key for key, value in expected.items() if value}
        observed = {key for key in required if normalized_ocr_fields.get(key)}
        missing = sorted(required - observed)
        sufficient_data = bool(evidence_items and observed) and not missing
        details["missing_comparison_fields"] = missing
        if not required:
            details["missing_reference_data"] = True

        total_penalty = sum(self.WEIGHTS.get(category, 10) for category in mismatches)
        weighted_score = max(0, 100 - total_penalty)
        confidence = max(0, 100 - (len(mismatches) * 10))
        summary = "No mismatch detected." if not mismatches else f"Detected {len(mismatches)} mismatch category(s)."

        return InspectionComparisonResult(
            mismatch_categories=mismatches,
            weighted_score=Decimal(str(weighted_score)).quantize(Decimal("1.00")) if sufficient_data else None,
            confidence=Decimal(str(confidence)).quantize(Decimal("1.00")) if sufficient_data else None,
            sufficient_data=sufficient_data,
            compared_fields=sorted(observed),
            summary=summary if sufficient_data else "Insufficient comparable data; human review required.",
            details=details,
        )
