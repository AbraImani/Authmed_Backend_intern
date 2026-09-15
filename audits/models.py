from django.db import models


class AuditLog(models.Model):
    organization = models.ForeignKey("organizations.Organization", null=True, blank=True, on_delete=models.SET_NULL, related_name="auditlog_records")
    timestamp = models.DateTimeField(auto_now_add=True)
    actor = models.CharField(max_length=255, blank=True)
    action = models.CharField(max_length=255)
    object_type = models.CharField(max_length=128, blank=True)
    object_id = models.CharField(max_length=128, blank=True)
    details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.timestamp.isoformat()} {self.actor} {self.action}"
