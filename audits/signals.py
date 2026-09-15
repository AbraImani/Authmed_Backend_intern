from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.db import connection, transaction
from organizations.tenancy import object_organization_id


AuditLog = apps.get_model("audits", "AuditLog")


def _audit_table_exists():
    try:
        # During migrations or test setup the audit table may not exist yet, so skip safely.
        with connection.cursor() as cursor:
            if AuditLog._meta.db_table not in connection.introspection.table_names(cursor):
                return False
            columns = {column.name for column in connection.introspection.get_table_description(cursor, AuditLog._meta.db_table)}
            return {field.column for field in AuditLog._meta.fields}.issubset(columns)
    except Exception:
        return False


@receiver(post_save)
def model_saved(sender, instance, created, **kwargs):
    # Skip AuditLog itself
    if sender._meta.apps is not apps or sender._meta.app_label not in {"organizations", "suppliers", "products", "inspections", "users"}:
        return
    if not _audit_table_exists():
        return
    try:
        # Use inspector username when available so the audit trail reflects the mobile workflow actor.
        with transaction.atomic():
            AuditLog.objects.create(
                organization_id=object_organization_id(instance),
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
    if sender._meta.apps is not apps or sender._meta.app_label not in {"organizations", "suppliers", "products", "inspections", "users"}:
        return
    if not _audit_table_exists():
        return
    try:
        # Deletions are still recorded even when we cannot reliably infer the original actor.
        with transaction.atomic():
            AuditLog.objects.create(
                organization_id=object_organization_id(instance),
                actor="",
                action="deleted",
                object_type=sender.__name__,
                object_id=str(getattr(instance, "id", "")),
                details={"repr": str(instance)},
            )
    except Exception:
        pass
