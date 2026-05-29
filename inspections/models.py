import hashlib

from django.db import models
from django.utils import timezone
from organizations.models import Site, Organization
from products.models import ProductReference
from suppliers.models import Supplier
from users.models import User
from .upload_paths import inspection_evidence_upload_to
from .validators import validate_inspection_file_extension, validate_inspection_file_size


class BatchInspection(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    site = models.ForeignKey(Site, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    product = models.ForeignKey(ProductReference, on_delete=models.SET_NULL, null=True, blank=True)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    batch_number = models.CharField(max_length=128, blank=True)
    received_at = models.DateTimeField()
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
    )

    # `status` tracks the inspection lifecycle while `outcome` stores the final business decision.
    status = models.CharField(
        max_length=32,
        choices=STATUS_CHOICES,
        default="pending",
        help_text="Inspection workflow status (pending -> in_progress -> completed).\nDo not use for final business outcome; see `outcome`.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    OUTCOME_CHOICES = (
        ("accepted", "Accepted"),
        ("isolated", "Isolated"),
        ("escalated", "Escalated"),
    )

    # Final decision is written by the review workflow, not by mobile capture.
    outcome = models.CharField(
        max_length=32,
        choices=OUTCOME_CHOICES,
        null=True,
        blank=True,
        help_text="Final business decision for the inspection (accepted, isolated, escalated). Set by review/decision workflow.",
    )

    def __str__(self):
        prod = self.product or "Unknown"
        return f"BatchInspection {self.id} - {prod} ({self.status})"


class Evidence(models.Model):
    EVIDENCE_TYPE_CHOICES = (
        ("photo", "Photo"),
        ("document", "Document"),
        ("other", "Other"),
        ("package_photo", "Package photo"),
        ("shelf_photo", "Shelf photo"),
        ("invoice", "Invoice"),
        ("barcode", "Barcode"),
        ("batch_label", "Batch label"),
        ("storage_environment", "Storage environment"),
        ("pharmacist_note", "Pharmacist note"),
    )

    EVIDENCE_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("reviewed", "Reviewed"),
        ("flagged", "Flagged"),
    )

    EXTRACTION_STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    inspection = models.ForeignKey(BatchInspection, on_delete=models.CASCADE, related_name="evidences")
    image = models.FileField(
        upload_to=inspection_evidence_upload_to,
        validators=[validate_inspection_file_extension, validate_inspection_file_size],
    )
    evidence_type = models.CharField(max_length=32, choices=EVIDENCE_TYPE_CHOICES, default="photo")
    evidence_status = models.CharField(max_length=32, choices=EVIDENCE_STATUS_CHOICES, default="pending")
    display_order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)
    extracted_text = models.TextField(blank=True)
    extraction_status = models.CharField(max_length=32, choices=EXTRACTION_STATUS_CHOICES, default="pending")
    extraction_confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    file_size_bytes = models.PositiveIntegerField(null=True, blank=True)
    checksum = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Captures who uploaded the evidence so the mobile client can show attribution.
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["display_order", "created_at"]
        indexes = [
            models.Index(fields=["inspection", "evidence_type"]),
            models.Index(fields=["inspection", "evidence_status"]),
            models.Index(fields=["inspection", "display_order"]),
        ]

    def __str__(self):
        return f"Evidence {self.id} for inspection {self.inspection_id} by {self.created_by or 'unknown'}"

    def clean(self):
        if self.notes:
            self.notes = self.notes.strip()
        if self.extracted_text:
            self.extracted_text = self.extracted_text.strip()

    def _update_file_metadata(self):
        if not self.image:
            self.file_size_bytes = None
            self.checksum = ""
            return
        self.file_size_bytes = getattr(self.image, "size", None)
        hasher = hashlib.sha256()
        self.image.seek(0)
        for chunk in self.image.chunks():
            hasher.update(chunk)
        self.checksum = hasher.hexdigest()
        self.image.seek(0)

    def save(self, *args, **kwargs):
        self.full_clean()
        self._update_file_metadata()
        super().save(*args, **kwargs)


class OCRTask(models.Model):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    )

    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name="ocr_tasks")
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default="pending")
    retry_count = models.PositiveIntegerField(default=0)
    processing_time = models.DurationField(null=True, blank=True)
    processor_version = models.CharField(max_length=64, blank=True)
    raw_output = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["evidence", "status"]),
        ]

    def __str__(self):
        return f"OCRTask {self.id} for evidence {self.evidence_id} ({self.status})"


class RiskResult(models.Model):
    inspection = models.OneToOneField(BatchInspection, on_delete=models.CASCADE, related_name="risk_result")
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    # Suspicion is derived from the score unless an explicit value is supplied by the workflow.
    SUSPICION_LEVEL_CHOICES = (
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    )
    suspicion_level = models.CharField(max_length=16, choices=SUSPICION_LEVEL_CHOICES, default="low")
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    flags = models.JSONField(default=list, blank=True)
    reason = models.TextField(blank=True)
    # Separate calculation time from `created_at` so the app can distinguish scoring time from persistence time.
    calculated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RiskResult {self.risk_score} for {self.inspection_id}"


class ReviewDecision(models.Model):
    inspection = models.ForeignKey(BatchInspection, on_delete=models.CASCADE, related_name="decisions")
    # Reviewer is optional at the model layer but the API defaults it to the authenticated user.
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    DECISION_CHOICES = (
        ("accepted", "Accepted"),
        ("isolated", "Isolated"),
        ("escalated", "Escalated"),
    )
    decision = models.CharField(max_length=32, choices=DECISION_CHOICES)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Decision {self.id} - {self.decision}"
