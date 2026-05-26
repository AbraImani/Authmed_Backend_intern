from django.db import models


class Organization(models.Model):
    """Top-level tenant organization representing a company or entity."""

    name = models.CharField(max_length=255)  # Organization name
    address = models.TextField(blank=True)  # Physical address
    created_at = models.DateTimeField(auto_now_add=True)  # When organization was created

    def __str__(self):
        return self.name


class Site(models.Model):
    """Physical site or location within an organization."""

    organization = models.ForeignKey(Organization, related_name="sites", on_delete=models.CASCADE)  # Parent organization
    name = models.CharField(max_length=255)  # Site name/location
    address = models.TextField(blank=True)  # Physical address of site
    created_at = models.DateTimeField(auto_now_add=True)  # When site was created

    def __str__(self):
        return f"{self.name} ({self.organization.name})"
