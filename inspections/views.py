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


class RiskResultViewSet(viewsets.ModelViewSet):
    queryset = RiskResult.objects.all()
    serializer_class = RiskResultSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]


class ReviewDecisionViewSet(viewsets.ModelViewSet):
    queryset = ReviewDecision.objects.all()
    serializer_class = ReviewDecisionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
