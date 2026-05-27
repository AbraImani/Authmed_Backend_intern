import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from organizations.models import Organization, Site
from django.contrib.auth import get_user_model
from inspections.models import BatchInspection, ReviewDecision, RiskResult

User = get_user_model()


@pytest.mark.django_db
class TestDecisionWorkflowMobileAPI:
    def setup_method(self):
        self.org = Organization.objects.create(name="Decision Org")
        self.site = Site.objects.create(organization=self.org, name="Decision Site")
        self.inspector = User.objects.create_user(username="decision-inspector", password="pass", role="inspector", organization=self.org, site=self.site)
        self.reviewer = User.objects.create_user(username="decision-reviewer", password="pass", role="reviewer", organization=self.org, site=self.site)

        self.other_org = Organization.objects.create(name="Other Decision Org")
        self.other_site = Site.objects.create(organization=self.other_org, name="Other Decision Site")
        self.other_user = User.objects.create_user(username="decision-other", password="pass", role="reviewer", organization=self.other_org, site=self.other_site)

        self.inspection = BatchInspection.objects.create(
            organization=self.org,
            site=self.site,
            inspector=self.inspector,
            batch_number="DEC-001",
            received_at=timezone.now(),
            status="pending",
        )
        RiskResult.objects.create(
            inspection=self.inspection,
            risk_score="82.00",
            suspicion_level="high",
            reason="Multiple suspicious indicators.",
            confidence="91.00",
            flags=["packaging_mismatch"],
        )

    def _auth_client(self, username, password):
        client = APIClient()
        response = client.post("/api/auth/token/", {"username": username, "password": password}, format="json")
        assert response.status_code == 200
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
        return client

    def test_submit_review_decision_updates_final_state(self):
        client = self._auth_client("decision-reviewer", "pass")
        payload = {
            "inspection": self.inspection.id,
            "decision": "isolated",
            "notes": "Isolate pending review due to risk profile.",
        }
        response = client.post("/api/decisions/", payload, format="json")
        assert response.status_code == 201
        data = response.json()
        assert data["decision"] == "isolated"
        assert data["decision_display"] == "Isolated"
        assert data["reviewer_display"]["username"] == "decision-reviewer"

        self.inspection.refresh_from_db()
        assert self.inspection.outcome == "isolated"
        assert self.inspection.status == "completed"

    def test_get_decision_by_inspection(self):
        decision = ReviewDecision.objects.create(
            inspection=self.inspection,
            reviewer=self.reviewer,
            decision="accepted",
            notes="Approved for release.",
        )
        client = self._auth_client("decision-reviewer", "pass")
        response = client.get(f"/api/decisions/by-inspection/?inspection={self.inspection.id}")
        assert response.status_code == 200
        assert response.json()["id"] == decision.id

    def test_inspection_detail_contains_decision_summary(self):
        ReviewDecision.objects.create(
            inspection=self.inspection,
            reviewer=self.reviewer,
            decision="escalated",
            notes="Escalate due to unresolved anomalies.",
        )
        client = self._auth_client("decision-reviewer", "pass")
        response = client.get(f"/api/batch-inspections/{self.inspection.id}/")
        assert response.status_code == 200
        summary = response.json()["decision_summary"]
        assert summary["exists"] is True
        assert summary["decision"] == "escalated"
        assert summary["reviewer_display"]["username"] == "decision-reviewer"

    def test_prevent_duplicate_decision_submission(self):
        ReviewDecision.objects.create(
            inspection=self.inspection,
            reviewer=self.reviewer,
            decision="accepted",
            notes="Initial final decision.",
        )
        client = self._auth_client("decision-reviewer", "pass")
        payload = {
            "inspection": self.inspection.id,
            "decision": "isolated",
            "notes": "Second decision should be rejected.",
        }
        response = client.post("/api/decisions/", payload, format="json")
        assert response.status_code == 400
        assert "inspection" in response.json()

    def test_enforce_org_scoping_on_decision_submission(self):
        client = self._auth_client("decision-other", "pass")
        payload = {
            "inspection": self.inspection.id,
            "decision": "accepted",
            "notes": "Cross-org attempt.",
        }
        response = client.post("/api/decisions/", payload, format="json")
        assert response.status_code == 400
