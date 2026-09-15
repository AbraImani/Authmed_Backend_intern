from django.db import migrations

# Ambiguous, deleted and global objects stay unassigned, hidden from tenant APIs.
PATHS = {
    "Organization": ("organizations", "Organization", "pk"),
    "Site": ("organizations", "Site", "organization_id"),
    "Supplier": ("suppliers", "Supplier", "organization_id"),
    "ProductReference": ("products", "ProductReference", "organization_id"),
    "ProductReferenceImage": ("products", "ProductReferenceImage", "product_reference__organization_id"),
    "DatasetGroup": ("products", "DatasetGroup", "organization_id"),
    "BatchInspection": ("inspections", "BatchInspection", "organization_id"),
    "Evidence": ("inspections", "Evidence", "inspection__organization_id"),
    "OCRTask": ("inspections", "OCRTask", "evidence__inspection__organization_id"),
    "InspectionProcessingRun": ("inspections", "InspectionProcessingRun", "inspection__organization_id"),
    "RiskResult": ("inspections", "RiskResult", "inspection__organization_id"),
    "ReviewDecision": ("inspections", "ReviewDecision", "inspection__organization_id"),
}

def scope_audits(apps, schema_editor):
    Audit = apps.get_model("audits", "AuditLog")
    alias = schema_editor.connection.alias
    for event in Audit.objects.using(alias).filter(organization_id=None).iterator():
        mapping = PATHS.get(event.object_type)
        if not mapping or not event.object_id.isascii() or not event.object_id.isdigit() or len(event.object_id) > 18:
            continue
        app, model, path = mapping
        org_id = apps.get_model(app, model).objects.using(alias).filter(pk=int(event.object_id)).values_list(path, flat=True).first()
        if org_id:
            Audit.objects.using(alias).filter(pk=event.pk).update(organization_id=org_id)

class Migration(migrations.Migration):
    dependencies = [("audits", "0002_auditlog_organization"), ("suppliers", "0003_scope_legacy_suppliers")]
    operations = [migrations.RunPython(scope_audits, migrations.RunPython.noop)]
