from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Seed demo data for AuthMed intern backend"

    def handle(self, *args, **options):
        from organizations.models import Organization, Site
        from users.models import User
        from suppliers.models import Supplier
        from products.models import ProductReference as Product
        from inspections.models import BatchInspection, Evidence, RiskResult, ReviewDecision

        self.stdout.write("Seeding demo data...")

        org, _ = Organization.objects.get_or_create(name="Demo Hospital", defaults={"address": "123 Demo St"})
        site, _ = Site.objects.get_or_create(organization=org, name="Main Pharmacy", defaults={"address": "1 Clinic Way"})

        # Create users with proper Django password hashing
        admin_user, admin_created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "role": "admin",
                "organization": org,
                "site": site,
                "is_staff": True,
                "is_superuser": False,
            },
        )
        if admin_created:
            admin_user.set_password("adminpass")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created admin user with password: adminpass"))
        else:
            self.stdout.write("Admin user already exists")

        inspector, inspector_created = User.objects.get_or_create(
            username="inspector1",
            defaults={
                "email": "inspector@example.com",
                "role": "inspector",
                "organization": org,
                "site": site,
            },
        )
        if inspector_created:
            inspector.set_password("inspectpass")
            inspector.save()
            self.stdout.write(self.style.SUCCESS("Created inspector user with password: inspectpass"))
        else:
            self.stdout.write("Inspector user already exists")

        reviewer, reviewer_created = User.objects.get_or_create(
            username="reviewer1",
            defaults={
                "email": "reviewer@example.com",
                "role": "reviewer",
                "organization": org,
                "site": site,
            },
        )
        if reviewer_created:
            reviewer.set_password("reviewpass")
            reviewer.save()
            self.stdout.write(self.style.SUCCESS("Created reviewer user with password: reviewpass"))
        else:
            self.stdout.write("Reviewer user already exists")

        nathan_defaults = {
            "first_name": "Nathan",
            "last_name": "Cirhuza",
            "email": "nathan@authmed.africa",
            "role": "inspector",
            "organization": org,
            "site": site,
            "is_active": True,
            "is_staff": False,
            "is_superuser": False,
        }
        nathan, nathan_created = User.objects.get_or_create(username="nathan.cirhuza", defaults=nathan_defaults)
        for field, value in nathan_defaults.items():
            setattr(nathan, field, value)
        nathan.set_password("nathan@authmed.africa")
        nathan.save()
        if nathan_created:
            self.stdout.write(self.style.SUCCESS("Created onboarding user Nathan Cirhuza with password: nathan@authmed.africa"))
        else:
            self.stdout.write("Updated onboarding user nathan.cirhuza")

        supplier, _ = Supplier.objects.get_or_create(name="Acme Pharma", defaults={"contact": "+1 555", "address": "Factory Rd"})
        product, _ = Product.objects.get_or_create(organization=org, name="PainAway 100mg", defaults={"sku": "PA100"})

        # Create a sample batch inspection
        insp, insp_created = BatchInspection.objects.get_or_create(
            batch_number="BATCH-001",
            defaults={
                "organization": org,
                "site": site,
                "supplier": supplier,
                "product": product,
                "inspector": inspector,
                "received_at": timezone.now(),
                "outcome": "accepted",
            },
        )
        if insp_created:
            self.stdout.write(self.style.SUCCESS("Created batch inspection BATCH-001"))

        RiskResult.objects.get_or_create(inspection=insp, defaults={"risk_score": 12.5, "reason": "Minor packaging damage"})
        ReviewDecision.objects.get_or_create(inspection=insp, defaults={"reviewer": reviewer, "decision": "accepted", "notes": "Accept after inspection"})

        self.stdout.write(self.style.SUCCESS("Demo data seeded successfully."))
