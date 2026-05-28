from django.db import models
from django.core.exceptions import ValidationError
from organizations.models import Organization
from suppliers.models import Supplier


class ProductReference(models.Model):
    """A canonical product reference used for inspection alignment and future
    dataset preparation.

    Minimal, inspection-focused fields only: organization-scoped, human name,
    optional SKU, supplier/manufacturer link, simple dosage/form/strength fields,
    packaging notes, and an active flag. Keep extensible but not opinionated.
    """

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=128, blank=True)
    # Link to the supplier/manufacturer source used for reference provenance.
    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Supplier or manufacturer source for this reference.",
    )
    # Simple inspection-relevant attributes
    form = models.CharField(
        max_length=64,
        blank=True,
        help_text="Dosage form (e.g. tablet, capsule, syrup, vial).",
    )
    strength = models.CharField(max_length=64, blank=True, help_text="Strength (e.g. 500 mg, 5 mg/ml)")
    pack_size = models.CharField(max_length=64, blank=True, help_text="Pack size or presentation (e.g. 10 tablets)")
    packaging_notes = models.TextField(blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text="If false, this reference is archived/inactive")
    # Lightweight optional image to associate a single representative reference image.
    reference_image = models.ImageField(upload_to="product_references/", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Prevent simple duplicates within an organization by name.
        unique_together = ("organization", "name")
        ordering = ["organization", "name"]
        indexes = [
            models.Index(fields=["organization", "sku"]),
            models.Index(fields=["organization", "name"]),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def clean(self):
        # Basic normalization and validation for inspection-focused lookups.
        if self.name:
            self.name = self.name.strip()
        if self.sku:
            self.sku = self.sku.strip()

        if not self.name:
            raise ValidationError({"name": "Name is required for a product reference."})

    def save(self, *args, **kwargs):
        # Ensure model-level validation runs on save to keep DB consistent when created
        # outside serializers (admin, shell, migrations).
        self.full_clean()
        super().save(*args, **kwargs)
