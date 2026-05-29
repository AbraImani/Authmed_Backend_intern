from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    InspectionViewSet,
    EvidenceViewSet,
    RiskResultViewSet,
    ReviewDecisionViewSet,
    OCRTaskViewSet,
)

router = DefaultRouter()
router.register(r"batch-inspections", InspectionViewSet)
router.register(r"evidences", EvidenceViewSet)
router.register(r"ocr-tasks", OCRTaskViewSet)
router.register(r"risk-results", RiskResultViewSet)
router.register(r"decisions", ReviewDecisionViewSet)

urlpatterns = [path("", include(router.urls))]
