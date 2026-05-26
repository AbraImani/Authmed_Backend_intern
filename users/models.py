from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser with role-based access control.
    
    This model adds organization and site scoping to support multi-tenancy,
    allowing users to be assigned to specific organizations and locations.
    Each user has a role that determines their permissions and capabilities
    in the inspection workflow (admin, inspector, or reviewer).
    """
    
    # Role options available to users
    ROLE_CHOICES = (
        ("admin", "Admin"),  # Full system access, organization management
        ("inspector", "Inspector"),  # Inspects batches, captures evidence
        ("reviewer", "Reviewer"),  # Reviews inspection results, makes final decisions
    )
    
    # User role - determines access level and permissions (default: inspector)
    role = models.CharField(
        max_length=32,
        choices=ROLE_CHOICES,
        default="inspector",
        help_text="User role defining access permissions and capabilities"
    )
    
    # Organization assignment - user belongs to this organization (optional)
    organization = models.ForeignKey(
        "organizations.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        help_text="Organization this user belongs to; null for superusers/admins"
    )
    
    # Site assignment - user works at this specific site within the organization (optional)
    site = models.ForeignKey(
        "organizations.Site",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        help_text="Specific site/location where user operates; optional if user covers multiple sites"
    )

    def __str__(self):
        """Return user representation as username and role."""
        return f"{self.username} ({self.role})"
