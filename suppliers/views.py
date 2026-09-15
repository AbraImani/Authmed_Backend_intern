from organizations.tenancy import TenantQuerysetMixin, get_request_organization
from rest_framework import viewsets, permissions
from .models import Supplier
from .serializers import SupplierSerializer
from authmed_intern.permissions import TenantPermission


class SupplierViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'manage'
    tenant_filters = {}
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]

    def perform_create(self, serializer):
        serializer.save(organization=get_request_organization(self.request))
