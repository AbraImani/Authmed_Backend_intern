from .base import BaseOCRAdapter, OCRProviderError, OCRExtractionResult


class PaddleOCRAdapter(BaseOCRAdapter):
    provider_name = "paddleocr"

    def extract(self, file_obj) -> OCRExtractionResult:
        raise OCRProviderError("PaddleOCR provider is not configured yet.")
