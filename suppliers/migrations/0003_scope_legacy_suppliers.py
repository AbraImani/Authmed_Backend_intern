from django.db import migrations

def scope_suppliers(apps, schema_editor):
    Supplier = apps.get_model("suppliers", "Supplier")
    Product = apps.get_model("products", "ProductReference")
    Inspection = apps.get_model("inspections", "BatchInspection")
    alias = schema_editor.connection.alias
    for supplier in Supplier.objects.using(alias).filter(organization_id=None).iterator():
        organizations = set(Product.objects.using(alias).filter(supplier_id=supplier.pk).values_list("organization_id", flat=True))
        organizations.update(Inspection.objects.using(alias).filter(supplier_id=supplier.pk).values_list("organization_id", flat=True))
        organizations.discard(None)
        if len(organizations) == 1:
            Supplier.objects.using(alias).filter(pk=supplier.pk).update(organization_id=organizations.pop())
        elif len(organizations) > 1:
            # Preserve original unassigned record; each tenant gets an independent copy.
            for org_id in sorted(organizations):
                clone = Supplier.objects.using(alias).create(organization_id=org_id, name=supplier.name, contact=supplier.contact, address=supplier.address)
                Product.objects.using(alias).filter(supplier_id=supplier.pk, organization_id=org_id).update(supplier_id=clone.pk)
                Inspection.objects.using(alias).filter(supplier_id=supplier.pk, organization_id=org_id).update(supplier_id=clone.pk)

class Migration(migrations.Migration):
    dependencies = [("suppliers", "0002_supplier_organization"), ("products", "0006_datasetgroup_datasetgroupimage_and_more"), ("inspections", "0010_processing_run_lifecycle")]
    operations = [migrations.RunPython(scope_suppliers, migrations.RunPython.noop)]
