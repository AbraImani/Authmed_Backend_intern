from rest_framework import viewsets, permissions
from .models import Organization, Site
from .serializers import OrganizationSerializer, SiteSerializer
from authmed_intern.permissions import IsAdminRole


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]


class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]
