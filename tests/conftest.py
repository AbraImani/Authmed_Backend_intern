"""Business tests traverse Firebase DRF authentication with a test-only verifier."""
import pytest
from rest_framework.exceptions import AuthenticationFailed

BUSINESS_TEST_MODULES = {
    "test_workflow", "test_products_api", "test_product_reference_images",
    "test_inspections_mobile", "test_evidence_mobile", "test_decisions_mobile",
    "test_risk_results_mobile", "test_ocr_task_pipeline",
}

@pytest.fixture(autouse=True)
def business_identity_verifier(request, monkeypatch):
    if request.module.__name__.split(".")[-1] not in BUSINESS_TEST_MODULES:
        return
    def verify(token):
        if not token.startswith("test-firebase:"):
            raise AuthenticationFailed("Invalid test identity.")
        return {"uid": token.removeprefix("test-firebase:")}
    monkeypatch.setattr("users.authentication.verify_firebase_token", verify)
