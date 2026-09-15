from organizations.tenancy import TenantQuerysetMixin, get_request_organization
from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer
from authmed_intern.permissions import TenantPermission


class AuditLogViewSet(TenantQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    write_capability = None
    tenant_filters = {}
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]

    read_capability = "audit"
