from organizations.tenancy import TenantQuerysetMixin, get_request_organization
from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import ValidationError
from inspections.services.processing.config import resolve_enabled_steps
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision, OCRTask, InspectionProcessingRun
from .serializers import (
    InspectionSerializer,
    EvidenceSerializer,
    RiskResultSerializer,
    ReviewDecisionSerializer,
    OCRTaskSerializer,
    InspectionProcessingRunSerializer,
)
from authmed_intern.permissions import TenantPermission
from inspections.services.processing import InspectionProcessingService
from inspections.dispatch import enqueue_inspection_run


class InspectionViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'inspect'
    tenant_filters = {'site': 'site_id', 'supplier': 'supplier_id', 'product': 'product_id', 'status': 'status'}
    queryset = BatchInspection.objects.select_related("organization", "site", "supplier", "product", "inspector").order_by("-received_at")
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]


    def perform_create(self, serializer):
        user = self.request.user
        organization = get_request_organization(self.request)
        # Default organization and inspector from the authenticated user so mobile clients send less data.
        serializer.save(organization=organization, inspector=user)

    @action(detail=True, methods=["post"])
    def add_evidence(self, request, pk=None):
        insp = self.get_object()
        data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
        # The action is inspection-scoped, so the inspection id is injected server-side.
        data["inspection"] = insp.id
        serializer = EvidenceSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save(inspection=insp, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"], url_path="process-intelligence")
    def process_intelligence(self, request, pk=None):
        inspection = self.get_object()
        try:
            enabled_steps = resolve_enabled_steps(request.data.get("enabled_steps"))
        except (ValueError, AttributeError) as exc:
            raise ValidationError({"enabled_steps": str(exc)})
        run, created = InspectionProcessingService(enqueue_inspection_run).schedule(
            inspection,
            triggered_by=request.user,
            enabled_steps=enabled_steps,
        )
        payload = InspectionProcessingRunSerializer(run, context={"request": request}).data
        payload["scheduled"] = created
        return Response(payload, status=status.HTTP_202_ACCEPTED if created else status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="processing-status")
    def processing_status(self, request, pk=None):
        inspection = self.get_object()
        summary = InspectionSerializer(inspection, context={"request": request}).data.get("processing_summary")
        return Response(summary, status=status.HTTP_200_OK)


class EvidenceViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'inspect'
    tenant_filters = {'inspection': 'inspection_id', 'evidence_type': 'evidence_type', 'evidence_status': 'evidence_status'}
    queryset = Evidence.objects.select_related("inspection", "inspection__organization", "created_by").order_by("display_order", "created_at")
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]


    def perform_create(self, serializer):
        # Ensure created_by is set and validate inspection scoping via serializer
        user = self.request.user
        serializer.save(created_by=user)


class OCRTaskViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'inspect'
    tenant_filters = {'status': 'status'}
    queryset = OCRTask.objects.select_related("evidence", "evidence__inspection").order_by("-created_at")
    serializer_class = OCRTaskSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]


    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        task = self.get_object()
        task.increment_retry()
        task.status = "queued"
        task.error_message = ""
        task.append_log("Task re-queued via API.")
        task.save(update_fields=["status", "error_message", "processing_log", "updated_at", "retry_count"])
        return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        task = self.get_object()
        reason = request.data.get("reason", "Cancelled via API.")
        task.mark_cancelled(reason=reason)
        return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)


class InspectionProcessingRunViewSet(TenantQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    write_capability = None
    tenant_filters = {'inspection': 'inspection_id', 'status': 'status'}
    queryset = InspectionProcessingRun.objects.select_related("inspection", "created_by").order_by("-created_at")
    serializer_class = InspectionProcessingRunSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]



class RiskResultViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'quality'
    tenant_filters = {'inspection': 'inspection_id'}
    queryset = RiskResult.objects.select_related("inspection").order_by("-created_at")
    serializer_class = RiskResultSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]


    def perform_create(self, serializer):
        serializer.save()

    @action(detail=False, methods=["get"], url_path="by-inspection")
    def by_inspection(self, request):
        inspection_id = request.query_params.get("inspection")
        if not inspection_id:
            return Response({"inspection": "Query parameter 'inspection' is required."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(inspection_id=inspection_id)
        risk_result = queryset.first()
        if risk_result is None:
            return Response({"detail": "No risk result found for this inspection."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(risk_result)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ReviewDecisionViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'review'
    tenant_filters = {'inspection': 'inspection_id'}
    queryset = ReviewDecision.objects.select_related("inspection", "reviewer").order_by("-created_at")
    serializer_class = ReviewDecisionSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]


    def perform_create(self, serializer):
        decision = serializer.save()
        inspection = decision.inspection
        # Final decision closes the workflow: the inspection becomes completed and outcome mirrors the choice.
        inspection.outcome = decision.decision
        inspection.status = "completed"
        inspection.save(update_fields=["outcome", "status"])

    @action(detail=False, methods=["get"], url_path="by-inspection")
    def by_inspection(self, request):
        inspection_id = request.query_params.get("inspection")
        if not inspection_id:
            return Response({"inspection": "Query parameter 'inspection' is required."}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.get_queryset().filter(inspection_id=inspection_id)
        decision = queryset.first()
        if decision is None:
            return Response({"detail": "No decision found for this inspection."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(decision)
        return Response(serializer.data, status=status.HTTP_200_OK)
