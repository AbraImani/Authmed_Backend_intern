from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


from inspections.services.errors import ProcessingError


class OCRProviderError(ProcessingError):
    code = "ocr_failed"


@dataclass
class OCRExtractionResult:
    provider_name: str
    text: str = ""
    confidence: float | None = None
    normalized_fields: dict[str, Any] = field(default_factory=dict)
    raw_output: dict[str, Any] = field(default_factory=dict)
    logs: list[dict[str, Any]] = field(default_factory=list)


class BaseOCRAdapter(ABC):
    provider_name = "base"

    @abstractmethod
    def extract(self, file_obj) -> OCRExtractionResult:
        raise NotImplementedError
