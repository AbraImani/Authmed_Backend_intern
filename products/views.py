from rest_framework import viewsets, permissions
from .models import ProductReference
from .serializers import ProductSerializer
from authmed_intern.permissions import IsOrgMember


class ProductViewSet(viewsets.ModelViewSet):
    queryset = ProductReference.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
