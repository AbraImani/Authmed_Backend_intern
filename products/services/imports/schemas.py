from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProductReferenceImportRow:
    row_number: int
    source: dict[str, Any]
    normalized: dict[str, Any]
    duplicate_matches: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


@dataclass
class ProductReferenceImportPreview:
    total_rows: int
    valid_rows: int
    invalid_rows: int
    rows: list[ProductReferenceImportRow]
