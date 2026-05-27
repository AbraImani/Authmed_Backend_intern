from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.db import connection


AuditLog = apps.get_model("audits", "AuditLog")


def _audit_table_exists():
    try:
        # During migrations or test setup the audit table may not exist yet, so skip safely.
        return AuditLog._meta.db_table in connection.introspection.table_names()
    except Exception:
        return False


@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    # Skip AuditLog itself
    if sender._meta.app_label == "audits":
        return
    if not _audit_table_exists():
        return
    try:
        # Use inspector username when available so the audit trail reflects the mobile workflow actor.
        AuditLog.objects.create(
            actor=getattr(instance, "inspector", None) and getattr(instance.inspector, "username", "") or "",
            action=("created" if created else "updated"),
            object_type=sender.__name__,
            object_id=str(getattr(instance, "id", "")),
            details={"repr": str(instance)},
        )
    except Exception:
        # Avoid breaking saves if audit fails
        pass


@receiver(post_delete)
def model_deleted(sender, instance, **kwargs):
    if sender._meta.app_label == "audits":
        return
    if not _audit_table_exists():
        return
    try:
        # Deletions are still recorded even when we cannot reliably infer the original actor.
        AuditLog.objects.create(
            actor="",
            action="deleted",
            object_type=sender.__name__,
            object_id=str(getattr(instance, "id", "")),
            details={"repr": str(instance)},
        )
    except Exception:
        pass
