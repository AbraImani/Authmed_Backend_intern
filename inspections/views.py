from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision
from .serializers import (
    InspectionSerializer,
    EvidenceSerializer,
    RiskResultSerializer,
    ReviewDecisionSerializer,
)
from authmed_intern.permissions import IsOrgMember


class InspectionViewSet(viewsets.ModelViewSet):
    queryset = BatchInspection.objects.all()
    serializer_class = InspectionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            qs = BatchInspection.objects.all()
        else:
            organization = getattr(user, "organization", None)
            if organization is None:
                return BatchInspection.objects.none()
            # Non-admin users only see inspections from their own organization.
            qs = BatchInspection.objects.filter(organization=organization)

        # Mobile list screens filter locally by site, supplier, product, and workflow status.
        site_id = self.request.query_params.get("site")
        supplier_id = self.request.query_params.get("supplier")
        product_id = self.request.query_params.get("product")
        status = self.request.query_params.get("status")

        if site_id:
            qs = qs.filter(site_id=site_id)
        if supplier_id:
            qs = qs.filter(supplier_id=supplier_id)
        if product_id:
            qs = qs.filter(product_id=product_id)
        if status:
            qs = qs.filter(status=status)

        return qs.order_by("-received_at")

    def perform_create(self, serializer):
        user = self.request.user
        organization = getattr(user, "organization", None)
        # Default organization and inspector from the authenticated user so mobile clients send less data.
        if organization is not None:
            serializer.save(organization=organization, inspector=user)
        else:
            serializer.save(inspector=user)

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


class EvidenceViewSet(viewsets.ModelViewSet):
    queryset = Evidence.objects.all()
    serializer_class = EvidenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            return Evidence.objects.all()
        organization = getattr(user, "organization", None)
        if organization is None:
            return Evidence.objects.none()
        qs = Evidence.objects.filter(inspection__organization=organization)
        inspection_id = self.request.query_params.get("inspection")
        if inspection_id:
            qs = qs.filter(inspection_id=inspection_id)
        return qs.order_by("-created_at")

    def perform_create(self, serializer):
        # Ensure created_by is set and validate inspection scoping via serializer
        user = self.request.user
        serializer.save(created_by=user)


class RiskResultViewSet(viewsets.ModelViewSet):
    queryset = RiskResult.objects.all()
    serializer_class = RiskResultSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            qs = RiskResult.objects.all()
        else:
            organization = getattr(user, "organization", None)
            if organization is None:
                return RiskResult.objects.none()
            # Risk results are visible only inside the caller's organization.
            qs = RiskResult.objects.filter(inspection__organization=organization)

        inspection_id = self.request.query_params.get("inspection")
        if inspection_id:
            qs = qs.filter(inspection_id=inspection_id)
        return qs.order_by("-created_at")

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


class ReviewDecisionViewSet(viewsets.ModelViewSet):
    queryset = ReviewDecision.objects.all()
    serializer_class = ReviewDecisionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            qs = ReviewDecision.objects.all()
        else:
            organization = getattr(user, "organization", None)
            if organization is None:
                return ReviewDecision.objects.none()
            # Decisions are filtered by organization so a reviewer cannot read cross-org final states.
            qs = ReviewDecision.objects.filter(inspection__organization=organization)

        inspection_id = self.request.query_params.get("inspection")
        if inspection_id:
            qs = qs.filter(inspection_id=inspection_id)
        return qs.order_by("-created_at")

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
