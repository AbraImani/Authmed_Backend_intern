import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from organizations.models import Organization, Site
from suppliers.models import Supplier
from products.models import ProductReference
from inspections.models import BatchInspection, Evidence, RiskResult, ReviewDecision
from audits.models import AuditLog

User = get_user_model()


@pytest.mark.django_db
class TestJWTAuth:
    def test_jwt_token_obtain(self):
        """Test JWT token obtain endpoint."""
        user = User.objects.create_user(username="testuser", password="testpass123", email="test@example.com")
        client = Client()
        response = client.post("/api/auth/token/", {"username": "testuser", "password": "testpass123"}, content_type="application/json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()
        assert "refresh" in response.json()

    def test_jwt_token_refresh(self):
        """Test JWT token refresh endpoint."""
        user = User.objects.create_user(username="testuser", password="testpass123")
        refresh = RefreshToken.for_user(user)
        client = Client()
        response = client.post("/api/auth/token/refresh/", {"refresh": str(refresh)}, content_type="application/json")
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.json()


@pytest.mark.django_db
class TestOrganizationAndSite:
    def test_create_organization(self):
        """Test organization creation."""
        org = Organization.objects.create(name="Test Org", address="123 Test St")
        assert org.name == "Test Org"
        assert Organization.objects.count() == 1

    def test_create_site(self):
        """Test site creation."""
        org = Organization.objects.create(name="Test Org")
        site = Site.objects.create(organization=org, name="Test Site", address="456 Site Blvd")
        assert site.name == "Test Site"
        assert site.organization == org


@pytest.mark.django_db
class TestBatchInspectionWorkflow:
    def setup_method(self):
        """Set up test data."""
        self.org = Organization.objects.create(name="Test Hospital")
        self.site = Site.objects.create(organization=self.org, name="Test Pharmacy")
        self.supplier = Supplier.objects.create(name="Test Supplier")
        self.product = ProductReference.objects.create(organization=self.org, name="Test Product", sku="TST001")
        self.inspector = User.objects.create_user(username="inspector", password="pass", role="inspector", organization=self.org, site=self.site)
        self.reviewer = User.objects.create_user(username="reviewer", password="pass", role="reviewer", organization=self.org, site=self.site)

    def test_create_batch_inspection(self):
        """Test batch inspection creation."""
        insp = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            supplier=self.supplier,
            product=self.product,
            inspector=self.inspector,
            batch_number="BATCH-001",
            received_at=timezone.now(),
        )
        assert insp.batch_number == "BATCH-001"
        assert insp.outcome is None  # Not set initially
        assert insp.inspector == self.inspector

    def test_batch_inspection_outcome_choices(self):
        """Test that BatchInspection outcome supports accepted, isolated, escalated."""
        outcomes = ["accepted", "isolated", "escalated"]
        for outcome in outcomes:
            insp = BatchInspection.objects.create(
                organization=self.org,
                site=self.site,
                outcome=outcome,
                batch_number=f"BATCH-{outcome}",
                received_at=timezone.now(),
            )
            assert insp.outcome == outcome


@pytest.mark.django_db
class TestEvidenceCapture:
    def setup_method(self):
        """Set up test data."""
        self.org = Organization.objects.create(name="Test Hospital")
        self.site = Site.objects.create(organization=self.org, name="Test Pharmacy")
        self.inspector = User.objects.create_user(username="inspector", password="pass", role="inspector", organization=self.org, site=self.site)
        self.insp = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            inspector=self.inspector,
            batch_number="BATCH-001",
            received_at=timezone.now(),
        )

    def test_create_evidence(self):
        """Test evidence creation (attachment to batch inspection)."""
        evidence = Evidence.objects.create(inspection=self.insp, notes="Damage on label")
        assert evidence.inspection == self.insp
        assert evidence.notes == "Damage on label"
        assert self.insp.evidences.count() == 1

    def test_multiple_evidences_per_inspection(self):
        """Test that multiple evidence items can be attached."""
        for i in range(3):
            Evidence.objects.create(inspection=self.insp, notes=f"Evidence {i}")
        assert self.insp.evidences.count() == 3


@pytest.mark.django_db
class TestRiskResult:
    def setup_method(self):
        """Set up test data."""
        self.org = Organization.objects.create(name="Test Hospital")
        self.site = Site.objects.create(organization=self.org, name="Test Pharmacy")
        self.inspector = User.objects.create_user(username="inspector", password="pass", role="inspector", organization=self.org, site=self.site)
        self.insp = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            inspector=self.inspector,
            batch_number="BATCH-001",
            received_at=timezone.now(),
        )

    def test_create_risk_result(self):
        """Test risk result creation."""
        risk = RiskResult.objects.create(inspection=self.insp, risk_score=45.5, reason="Label damage detected")
        assert risk.inspection == self.insp
        assert risk.risk_score == 45.5
        assert risk.reason == "Label damage detected"

    def test_one_to_one_risk_result_relationship(self):
        """Test that each inspection has at most one risk result."""
        RiskResult.objects.create(inspection=self.insp, risk_score=10)
        # Verify the one-to-one relationship via reverse access
        assert self.insp.risk_result.risk_score == 10


@pytest.mark.django_db
class TestReviewDecision:
    def setup_method(self):
        """Set up test data."""
        self.org = Organization.objects.create(name="Test Hospital")
        self.site = Site.objects.create(organization=self.org, name="Test Pharmacy")
        self.reviewer = User.objects.create_user(username="reviewer", password="pass", role="reviewer", organization=self.org, site=self.site)
        self.inspector = User.objects.create_user(username="inspector", password="pass", role="inspector", organization=self.org, site=self.site)
        self.insp = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            inspector=self.inspector,
            batch_number="BATCH-001",
            received_at=timezone.now(),
        )

    def test_create_review_decision(self):
        """Test review decision creation with explicit decision choice."""
        decision = ReviewDecision.objects.create(
            inspection=self.insp, reviewer=self.reviewer, decision="accepted", notes="Approved for release"
        )
        assert decision.inspection == self.insp
        assert decision.reviewer == self.reviewer
        assert decision.decision == "accepted"
        assert decision.notes == "Approved for release"

    def test_review_decision_choices(self):
        """Test that decision field supports accepted, isolated, escalated."""
        decisions = ["accepted", "isolated", "escalated"]
        for i, decision_choice in enumerate(decisions):
            insp = BatchInspection.objects.create(
                organization=self.org,
                site=self.site,
                batch_number=f"BATCH-{i}",
                received_at=timezone.now(),
            )
            decision = ReviewDecision.objects.create(inspection=insp, reviewer=self.reviewer, decision=decision_choice)
            assert decision.decision == decision_choice


@pytest.mark.django_db
class TestAuditLog:
    def setup_method(self):
        """Set up test data."""
        AuditLog.objects.all().delete()
        self.org = Organization.objects.create(name="Test Hospital")
        AuditLog.objects.all().delete()

    def test_audit_log_creation(self):
        """Test that audit logs are created."""
        log = AuditLog.objects.create(
            actor="test_user", action="created", object_type="BatchInspection", object_id="123", details={"key": "value"}
        )
        assert log.action == "created"
        assert log.object_type == "BatchInspection"
        assert AuditLog.objects.filter(
            actor="test_user",
            action="created",
            object_type="BatchInspection",
            object_id="123",
            details={"key": "value"},
        ).count() == 1

    def test_audit_log_query(self):
        """Test that audit logs can be queried."""
        created_log = AuditLog.objects.create(actor="user1", action="created", object_type="Organization", object_id="1")
        updated_log = AuditLog.objects.create(actor="user2", action="updated", object_type="Organization", object_id="1")
        deleted_log = AuditLog.objects.create(actor="user1", action="deleted", object_type="Organization", object_id="2")

        created_logs = AuditLog.objects.filter(actor="user1", action="created", object_type="Organization", object_id="1")
        assert created_logs.count() == 1
        assert created_logs.first() == created_log

        user1_logs = AuditLog.objects.filter(actor="user1", object_type="Organization")
        assert user1_logs.count() == 2
        assert set(user1_logs.values_list("object_id", flat=True)) == {"1", "2"}
