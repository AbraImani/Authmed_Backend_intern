import pytest

from organizations.models import Organization
from products.models import ProductReference
from products.services.imports import preview_product_reference_import
from products.import_validators import validate_product_reference_csv_headers
from suppliers.models import Supplier


@pytest.mark.django_db
class TestProductReferenceImportPreview:
    def setup_method(self):
        self.org = Organization.objects.create(name="Import Org")
        self.supplier = Supplier.objects.create(name="Import Supplier")
        self.existing = ProductReference.objects.create(
            organization=self.org,
            name="Existing Brand",
            sku="EX-001",
            supplier=self.supplier,
            form="tablet",
            strength="500 mg",
            pack_size="10 tablets",
        )

    def test_validate_headers_requires_product_name(self):
        errors = validate_product_reference_csv_headers(["sku", "manufacturer"])
        assert errors
        assert "product name column" in errors[0]

    def test_preview_normalizes_aliases_and_finds_duplicates(self):
        csv_text = """product_name,product_code,manufacturer,dosage_form,strength,pack_size,notes
Existing Brand,EX-001,Import Supplier,tablet,500 mg,10 tablets,Sample note
New Brand,NB-002,Other Supplier,syrup,5 mg/ml,1 bottle,Another note
"""
        preview = preview_product_reference_import(csv_text, self.org)
        assert preview.total_rows == 2
        assert preview.valid_rows == 2
        assert preview.invalid_rows == 0
        first_row = preview.rows[0]
        assert first_row.normalized["name"] == "Existing Brand"
        assert first_row.normalized["sku"] == "EX-001"
        assert first_row.normalized["supplier"] == "Import Supplier"
        assert first_row.duplicate_matches
        second_row = preview.rows[1]
        assert second_row.normalized["name"] == "New Brand"
        assert second_row.normalized["form"] == "syrup"
        assert second_row.duplicate_matches == []

    def test_preview_reports_missing_names(self):
        csv_text = """sku,manufacturer
,Import Supplier
"""
        preview = preview_product_reference_import(csv_text, self.org)
        assert preview.total_rows == 0
        assert preview.invalid_rows == 1
        assert preview.rows[0].errors
