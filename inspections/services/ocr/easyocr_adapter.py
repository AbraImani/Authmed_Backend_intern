from .base import BaseOCRAdapter, OCRProviderError, OCRExtractionResult


class EasyOCRAdapter(BaseOCRAdapter):
    provider_name = "easyocr"

    def extract(self, file_obj) -> OCRExtractionResult:
        raise OCRProviderError("EasyOCR provider is not configured yet.")
