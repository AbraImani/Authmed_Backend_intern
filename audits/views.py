from rest_framework import viewsets, permissions
from .models import AuditLog
from .serializers import AuditLogSerializer
from authmed_intern.permissions import IsAdminOrReviewer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReviewer]
