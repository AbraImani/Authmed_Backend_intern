from rest_framework import viewsets, permissions
from .models import Supplier
from .serializers import SupplierSerializer
from authmed_intern.permissions import IsOrgMember


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
