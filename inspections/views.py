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
            qs = BatchInspection.objects.filter(organization=organization)

        # apply optional filters for mobile convenience
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
        # rely on serializer.create defaults but ensure organization/inspector set when available
        if organization is not None:
            serializer.save(organization=organization, inspector=user)
        else:
            serializer.save(inspector=user)

    @action(detail=True, methods=["post"])
    def add_evidence(self, request, pk=None):
        insp = self.get_object()
        data = dict(request.data) if isinstance(request.data, dict) else {**request.data}
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
            return RiskResult.objects.all()
        organization = getattr(user, "organization", None)
        if organization is None:
            return RiskResult.objects.none()
        return RiskResult.objects.filter(inspection__organization=organization)

    def perform_create(self, serializer):
        serializer.save()


class ReviewDecisionViewSet(viewsets.ModelViewSet):
    queryset = ReviewDecision.objects.all()
    serializer_class = ReviewDecisionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            return ReviewDecision.objects.all()
        organization = getattr(user, "organization", None)
        if organization is None:
            return ReviewDecision.objects.none()
        return ReviewDecision.objects.filter(inspection__organization=organization)

    def perform_create(self, serializer):
        serializer.save()
