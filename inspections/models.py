from django.db import models
from organizations.models import Site, Organization
from products.models import ProductReference
from suppliers.models import Supplier
from users.models import User


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
    inspection = models.ForeignKey(BatchInspection, on_delete=models.CASCADE, related_name="evidences")
    image = models.ImageField(upload_to="evidences/")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    EVIDENCE_TYPE_CHOICES = (
        ("photo", "Photo"),
        ("document", "Document"),
        ("other", "Other"),
    )
    evidence_type = models.CharField(max_length=32, choices=EVIDENCE_TYPE_CHOICES, default="photo")

    def __str__(self):
        return f"Evidence {self.id} for inspection {self.inspection_id} by {self.created_by or 'unknown'}"


class RiskResult(models.Model):
    inspection = models.OneToOneField(BatchInspection, on_delete=models.CASCADE, related_name="risk_result")
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"RiskResult {self.risk_score} for {self.inspection_id}"


class ReviewDecision(models.Model):
    inspection = models.ForeignKey(BatchInspection, on_delete=models.CASCADE, related_name="decisions")
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
