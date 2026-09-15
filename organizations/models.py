from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Site(models.Model):
    organization = models.ForeignKey(Organization, related_name="sites", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.organization.name})"


class OrganizationMembership(models.Model):
    from .roles import Role
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="memberships")
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=32, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    primary_site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.SET_NULL, related_name="memberships")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "organization"], name="unique_user_organization_membership")]

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.primary_site_id and self.primary_site.organization_id != self.organization_id:
            raise ValidationError({"primary_site": "Site must belong to the membership organization."})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
