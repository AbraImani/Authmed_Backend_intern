import hashlib

from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from organizations.models import Organization
from suppliers.models import Supplier
from .upload_paths import product_reference_cover_upload_to, product_reference_image_upload_to
from .validators import validate_reference_image_file_size, validate_reference_image_extension

User = get_user_model()


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
    reference_image = models.ImageField(
        upload_to=product_reference_cover_upload_to,
        null=True,
        blank=True,
        validators=[validate_reference_image_extension, validate_reference_image_file_size],
    )

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


class ProductReferenceImage(models.Model):
    """Additional reference imagery for inspection alignment.

    Each image stores lightweight metadata so future comparison and dataset
    workflows can distinguish packaging views without requiring ML logic now.
    """

    IMAGE_TYPE_CHOICES = (
        ("front_packaging", "Front packaging"),
        ("back_packaging", "Back packaging"),
        ("blister", "Blister"),
        ("label", "Label"),
        ("barcode", "Barcode"),
        ("leaflet", "Leaflet"),
        ("carton", "Carton"),
        ("seal", "Seal"),
    )

    product_reference = models.ForeignKey(ProductReference, on_delete=models.CASCADE, related_name="reference_images")
    image = models.ImageField(
        upload_to=product_reference_image_upload_to,
        validators=[validate_reference_image_extension, validate_reference_image_file_size],
    )
    image_type = models.CharField(max_length=32, choices=IMAGE_TYPE_CHOICES, default="front_packaging")
    angle = models.CharField(max_length=64, blank=True)
    lighting_condition = models.CharField(max_length=64, blank=True)
    source = models.CharField(max_length=128, blank=True, help_text="Source of the reference image (manual, import, partner, etc.).")
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)
    notes = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["display_order", "created_at"]
        indexes = [
            models.Index(fields=["product_reference", "image_type"]),
            models.Index(fields=["product_reference", "display_order"]),
        ]

    def __str__(self):
        return f"{self.product_reference.name} - {self.image_type}"

    @property
    def organization(self):
        return getattr(self.product_reference, "organization", None)

    def clean(self):
        if self.angle:
            self.angle = self.angle.strip()
        if self.lighting_condition:
            self.lighting_condition = self.lighting_condition.strip()
        if self.source:
            self.source = self.source.strip()
        if self.notes:
            self.notes = self.notes.strip()

    def _update_checksum(self):
        if not self.image:
            self.checksum = ""
            return
        hasher = hashlib.sha256()
        self.image.seek(0)
        for chunk in self.image.chunks():
            hasher.update(chunk)
        self.checksum = hasher.hexdigest()
        self.image.seek(0)

    def save(self, *args, **kwargs):
        self.full_clean()
        self._update_checksum()
        super().save(*args, **kwargs)


class DatasetGroup(models.Model):
    """Organize reference images for future labeling and ML dataset readiness."""

    ANNOTATION_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In progress"),
        ("completed", "Completed"),
        ("needs_review", "Needs review"),
    )

    QUALITY_FLAG_CHOICES = (
        ("good", "Good"),
        ("needs_review", "Needs review"),
        ("duplicate", "Duplicate"),
        ("blurry", "Blurry"),
        ("corrupt", "Corrupt"),
    )

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    labeling_ready = models.BooleanField(default=False)
    annotation_status = models.CharField(max_length=32, choices=ANNOTATION_STATUS_CHOICES, default="pending")
    quality_flag = models.CharField(max_length=32, choices=QUALITY_FLAG_CHOICES, default="needs_review")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reference_images = models.ManyToManyField(
        ProductReferenceImage,
        related_name="dataset_groups",
        blank=True,
        through="DatasetGroupImage",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["organization", "name"]
        unique_together = ("organization", "name")
        indexes = [
            models.Index(fields=["organization", "annotation_status"]),
            models.Index(fields=["organization", "quality_flag"]),
            models.Index(fields=["organization", "labeling_ready"]),
        ]

    def __str__(self):
        return f"{self.organization.name} - {self.name}"

    def clean(self):
        if self.name:
            self.name = self.name.strip()
        if self.description:
            self.description = self.description.strip()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DatasetGroupImage(models.Model):
    """Through table that stores per-image annotation preparation metadata."""

    ANNOTATION_STATUS_CHOICES = DatasetGroup.ANNOTATION_STATUS_CHOICES
    QUALITY_FLAG_CHOICES = DatasetGroup.QUALITY_FLAG_CHOICES

    dataset_group = models.ForeignKey(DatasetGroup, on_delete=models.CASCADE)
    reference_image = models.ForeignKey(ProductReferenceImage, on_delete=models.CASCADE)
    annotation_status = models.CharField(max_length=32, choices=ANNOTATION_STATUS_CHOICES, default="pending")
    quality_flag = models.CharField(max_length=32, choices=QUALITY_FLAG_CHOICES, default="needs_review")
    annotation_notes = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "created_at"]
        unique_together = ("dataset_group", "reference_image")
        indexes = [
            models.Index(fields=["dataset_group", "annotation_status"]),
            models.Index(fields=["dataset_group", "quality_flag"]),
        ]

    def __str__(self):
        return f"{self.dataset_group.name} - {self.reference_image_id}"
