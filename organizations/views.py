from organizations.tenancy import TenantQuerysetMixin
from rest_framework import viewsets, permissions
from .models import Organization, Site
from .serializers import OrganizationSerializer, SiteSerializer
from authmed_intern.permissions import TenantPermission


class OrganizationViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "put", "patch", "head", "options"]
    write_capability = 'manage'
    tenant_filters = {}
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]


class SiteViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'manage'
    tenant_filters = {}
    queryset = Site.objects.all()
    serializer_class = SiteSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
