from django.db import models
from organizations.models import Organization


class ProductReference(models.Model):
    """Reference catalog of products managed by an organization."""

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # Organization that manages this product
    name = models.CharField(max_length=255)  # Product name
    sku = models.CharField(max_length=128, blank=True)  # Stock keeping unit/product code
    description = models.TextField(blank=True)  # Product description
    created_at = models.DateTimeField(auto_now_add=True)  # When product was added to catalog

    def __str__(self):
        return f"{self.organization.name} - {self.name}"
