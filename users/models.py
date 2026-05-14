from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("inspector", "Inspector"),
        ("reviewer", "Reviewer"),
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default="inspector")
    organization = models.ForeignKey(
        "organizations.Organization",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )
    site = models.ForeignKey(
        "organizations.Site",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
