import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from organizations.models import Organization, Site
from django.contrib.auth import get_user_model
from inspections.models import BatchInspection, RiskResult

User = get_user_model()


@pytest.mark.django_db
class TestRiskResultsMobileAPI:
    def setup_method(self):
        self.org = Organization.objects.create(name="Risk Org")
        self.site = Site.objects.create(organization=self.org, name="Risk Site")
        self.inspector = User.objects.create_user(
            username="risk-inspector",
            password="pass",
            role="inspector",
            organization=self.org,
            site=self.site,
        )

        self.other_org = Organization.objects.create(name="Other Risk Org")
        self.other_site = Site.objects.create(organization=self.other_org, name="Other Risk Site")
        self.other_user = User.objects.create_user(
            username="risk-other",
            password="pass",
            role="inspector",
            organization=self.other_org,
            site=self.other_site,
        )

        self.inspection = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            inspector=self.inspector,
            batch_number="RISK-001",
            received_at=timezone.now(),
        )

    def _auth_client(self, username, password):
        client = APIClient()
        response = client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        assert response.status_code == 200
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
        return client

    def test_create_risk_result_for_inspection(self):
        client = self._auth_client("risk-inspector", "pass")
        payload = {
            "inspection": self.inspection.id,
            "risk_score": "72.50",
            "reason": "Damaged seal and inconsistent batch print.",
            "confidence": "88.30",
            "flags": ["seal_damage", "print_mismatch"],
        }
        response = client.post("/api/risk-results/", payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["inspection"] == self.inspection.id
        assert data["risk_score"] == "72.50"
        assert data["suspicion_level"] == "high"
        assert data["is_high_risk"] is True
        assert data["inspection_display"]["batch_number"] == "RISK-001"

    def test_get_risk_result_detail(self):
        risk = RiskResult.objects.create(
            inspection=self.inspection,
            risk_score="35.00",
            suspicion_level="medium",
            reason="Temperature excursion reported.",
            confidence="77.10",
            flags=["temperature_excursion"],
        )
        client = self._auth_client("risk-inspector", "pass")
        response = client.get(f"/api/risk-results/{risk.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == risk.id
        assert data["suspicion_level_display"] == "Medium"

    def test_get_risk_result_by_inspection(self):
        RiskResult.objects.create(
            inspection=self.inspection,
            risk_score="45.00",
            suspicion_level="medium",
            reason="Label formatting inconsistency.",
        )
        client = self._auth_client("risk-inspector", "pass")
        response = client.get(f"/api/risk-results/by-inspection/?inspection={self.inspection.id}")
        assert response.status_code == 200
        assert response.json()["inspection"] == self.inspection.id

    def test_prevent_duplicate_risk_result_per_inspection(self):
        RiskResult.objects.create(
            inspection=self.inspection,
            risk_score="15.00",
            suspicion_level="low",
            reason="Initial scoring.",
        )
        client = self._auth_client("risk-inspector", "pass")
        payload = {
            "inspection": self.inspection.id,
            "risk_score": "92.00",
            "reason": "Second result should fail.",
        }
        response = client.post("/api/risk-results/", payload, format="json")
        assert response.status_code == 400
        assert "inspection" in response.json()

    def test_enforce_org_scoping_on_risk_result(self):
        client = self._auth_client("risk-other", "pass")
        payload = {
            "inspection": self.inspection.id,
            "risk_score": "90.00",
            "reason": "Cross-org access attempt.",
        }
        response = client.post("/api/risk-results/", payload, format="json")
        assert response.status_code == 400

    def test_inspection_detail_contains_risk_result_summary(self):
        RiskResult.objects.create(
            inspection=self.inspection,
            risk_score="85.00",
            suspicion_level="critical",
            reason="Multiple counterfeiting indicators.",
            confidence="90.00",
            flags=["counterfeit_packaging", "barcode_mismatch"],
        )
        client = self._auth_client("risk-inspector", "pass")
        response = client.get(f"/api/batch-inspections/{self.inspection.id}/")
        assert response.status_code == 200
        summary = response.json()["risk_result_summary"]
        assert summary["exists"] is True
        assert summary["suspicion_level"] == "critical"
        assert summary["risk_score"] == "85.00"
