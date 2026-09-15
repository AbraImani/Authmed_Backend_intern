from django.db import migrations

def migrate_memberships(apps, schema_editor):
    User = apps.get_model("users", "User")
    Membership = apps.get_model("organizations", "OrganizationMembership")
    alias = schema_editor.connection.alias
    for user in User.objects.using(alias).exclude(organization_id=None).iterator():
        if user.role not in {"admin", "inspector", "reviewer"}:
            continue
        site_id = user.site_id if user.site_id and user.site.organization_id == user.organization_id else None
        Membership.objects.using(alias).get_or_create(
            user_id=user.pk, organization_id=user.organization_id,
            defaults={"role": user.role, "is_active": user.is_active, "primary_site_id": site_id},
        )

class Migration(migrations.Migration):
    dependencies = [("organizations", "0002_organizationmembership"), ("users", "0002_user_firebase_uid")]
    # Preserve memberships on reverse rather than deleting subsequently managed business data.
    operations = [migrations.RunPython(migrate_memberships, migrations.RunPython.noop)]
