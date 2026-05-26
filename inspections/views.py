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
            return BatchInspection.objects.all()
        organization = getattr(user, "organization", None)
        if organization is None:
            return BatchInspection.objects.none()
        return BatchInspection.objects.filter(organization=organization)

    def perform_create(self, serializer):
        user = self.request.user
        organization = getattr(user, "organization", None)
        serializer.save(organization=organization, inspector=user)

    @action(detail=True, methods=["post"])
    def add_evidence(self, request, pk=None):
        insp = self.get_object()
        serializer = EvidenceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(inspection=insp)
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
        return Evidence.objects.filter(inspection__organization=organization)

    def perform_create(self, serializer):
        serializer.save()


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
