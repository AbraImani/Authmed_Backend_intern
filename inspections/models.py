from django.db import models
from organizations.models import Site, Organization
from products.models import ProductReference
from suppliers.models import Supplier
from users.models import User


class BatchInspection(models.Model):
    """Represents a batch of medicines received for inspection and risk assessment."""
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # Owning organization
    site = models.ForeignKey(Site, on_delete=models.CASCADE)  # Location where batch was received
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)  # Supplier of batch
    product = models.ForeignKey(ProductReference, on_delete=models.SET_NULL, null=True, blank=True)  # Product reference
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)  # Inspector conducting review
    batch_number = models.CharField(max_length=128, blank=True)  # Batch identifier
    received_at = models.DateTimeField()  # When batch was received
    created_at = models.DateTimeField(auto_now_add=True)  # Record creation timestamp

    OUTCOME_CHOICES = (
        ("accepted", "Accepted"),
        ("isolated", "Isolated"),
        ("escalated", "Escalated"),
    )

    outcome = models.CharField(max_length=32, choices=OUTCOME_CHOICES, null=True, blank=True)  # Final outcome from reviewer

    def __str__(self):
        return f"BatchInspection {self.id} - {self.product or 'Unknown'}"


class Evidence(models.Model):
    """Supporting evidence (images and notes) attached to a batch inspection."""
    
    inspection = models.ForeignKey(BatchInspection, on_delete=models.CASCADE, related_name="evidences")  # Related inspection
    image = models.ImageField(upload_to="evidences/")  # Evidence image
    notes = models.TextField(blank=True)  # Additional notes or observations
    created_at = models.DateTimeField(auto_now_add=True)  # When evidence was recorded

    def __str__(self):
        return f"Evidence {self.id} for inspection {self.inspection_id}"


class RiskResult(models.Model):
    """Risk assessment outcome for a batch inspection (one per inspection)."""
    
    inspection = models.OneToOneField(BatchInspection, on_delete=models.CASCADE, related_name="risk_result")  # Associated inspection
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)  # Numeric risk score (0-100)
    reason = models.TextField(blank=True)  # Explanation of risk assessment
    created_at = models.DateTimeField(auto_now_add=True)  # When assessment was created

    def __str__(self):
        return f"RiskResult {self.risk_score} for {self.inspection_id}"


class ReviewDecision(models.Model):
    """Final review decision made by a reviewer on a batch inspection."""

    inspection = models.ForeignKey(BatchInspection, on_delete=models.CASCADE, related_name="decisions")  # Inspected batch
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)  # Reviewer making the decision
    DECISION_CHOICES = (
        ("accepted", "Accepted"),
        ("isolated", "Isolated"),
        ("escalated", "Escalated"),
    )
    decision = models.CharField(max_length=32, choices=DECISION_CHOICES)  # Final decision
    notes = models.TextField(blank=True)  # Comments or justification
    created_at = models.DateTimeField(auto_now_add=True)  # When decision was made

    def __str__(self):
        return f"Decision {self.id} - {self.decision}"
