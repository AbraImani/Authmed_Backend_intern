import csv
from io import StringIO

from products.import_validators import validate_product_reference_csv_headers
from .duplicates import find_product_reference_duplicates
from .schemas import ProductReferenceImportPreview, ProductReferenceImportRow

FIELD_ALIASES = {
    "name": ("name", "product_name", "brand_name"),
    "sku": ("sku", "product_code"),
    "supplier": ("supplier", "manufacturer"),
    "form": ("form", "dosage_form"),
    "strength": ("strength",),
    "pack_size": ("pack_size", "presentation"),
    "description": ("description",),
    "packaging_notes": ("packaging_notes", "notes"),
    "is_active": ("is_active", "active"),
    "gtin": ("gtin",),
    "manufacturer": ("manufacturer",),
    "brand_name": ("brand_name",),
    "product_code": ("product_code",),
    "dosage_form": ("dosage_form",),
}
def _clean_value(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _normalize_boolean(value):
    text = _clean_value(value)
    if text is None:
        return None
    return text.lower() in {"1", "true", "yes", "y", "active"}


def normalize_import_row(source_row):
    normalized = {}
    for canonical_field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            if alias in source_row:
                value = _clean_value(source_row.get(alias))
                if canonical_field == "is_active":
                    normalized[canonical_field] = _normalize_boolean(value)
                elif value is not None:
                    normalized[canonical_field] = value
                break
    return normalized


def validate_import_headers(fieldnames):
    return validate_product_reference_csv_headers(fieldnames)


def preview_product_reference_import(csv_text, organization):
    reader = csv.DictReader(StringIO(csv_text))
    header_errors = validate_import_headers(reader.fieldnames)
    rows = []
    valid_rows = 0
    invalid_rows = 0

    if header_errors:
        preview_row = ProductReferenceImportRow(row_number=0, source={}, normalized={}, errors=header_errors)
        return ProductReferenceImportPreview(total_rows=0, valid_rows=0, invalid_rows=1, rows=[preview_row])

    for index, source_row in enumerate(reader, start=1):
        normalized = normalize_import_row(source_row)
        errors = []
        if not normalized.get("name"):
            errors.append("Missing product name.")
        duplicate_matches = find_product_reference_duplicates(organization, normalized)
        if errors:
            invalid_rows += 1
        else:
            valid_rows += 1
        rows.append(
            ProductReferenceImportRow(
                row_number=index,
                source=source_row,
                normalized=normalized,
                duplicate_matches=duplicate_matches,
                errors=errors,
            )
        )

    return ProductReferenceImportPreview(
        total_rows=len(rows),
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        rows=rows,
    )
