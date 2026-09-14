from .base import BaseOCRAdapter, OCRExtractionResult


class StaticOCRAdapter(BaseOCRAdapter):
    """Deterministic OCR adapter for tests and placeholder datasets."""

    provider_name = "static-ocr"

    def __init__(self, result=None):
        self.result = result or OCRExtractionResult(
            provider_name=self.provider_name,
            text="",
            confidence=0.0,
            normalized_fields={},
            raw_output={},
            logs=[{"level": "info", "message": "Static OCR adapter used as a placeholder.", "payload": {}}],
        )

    def extract(self, file_obj):
        if self.result.provider_name != self.provider_name:
            return OCRExtractionResult(
                provider_name=self.result.provider_name,
                text=self.result.text,
                confidence=self.result.confidence,
                normalized_fields=self.result.normalized_fields,
                raw_output=self.result.raw_output,
                logs=self.result.logs,
            )
        return self.result
