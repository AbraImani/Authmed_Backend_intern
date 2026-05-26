from django.db import models


class Supplier(models.Model):
    """Supplier of medicine batches and products."""

    name = models.CharField(max_length=255, blank=False)  # Supplier company name (required)
    contact = models.CharField(max_length=255, blank=True)  # Contact person or email (optional)
    address = models.TextField(blank=True)  # Physical address (optional)
    created_at = models.DateTimeField(auto_now_add=True)  # When supplier was added

    def __str__(self):
        return self.name
