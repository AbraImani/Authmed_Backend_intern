from django.db import models

class Role(models.TextChoices):
    ADMIN = "admin", "Organization admin"
    MANAGER = "organization_manager", "Organization manager"
    INSPECTOR = "inspector", "Inspector"
    REVIEWER = "reviewer", "Reviewer"
    QUALITY = "quality_officer", "Quality officer"

CAPABILITIES = {
    Role.ADMIN: frozenset({"read", "manage", "inspect", "review", "quality", "audit", "members"}),
    Role.MANAGER: frozenset({"read", "manage", "inspect", "audit", "members"}),
    Role.INSPECTOR: frozenset({"read", "inspect"}),
    Role.REVIEWER: frozenset({"read", "review", "audit"}),
    Role.QUALITY: frozenset({"read", "review", "quality", "audit"}),
}
