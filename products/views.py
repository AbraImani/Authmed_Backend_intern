from rest_framework import viewsets, permissions
from .models import ProductReference
from .serializers import ProductSerializer
from authmed_intern.permissions import IsOrgMember


class ProductViewSet(viewsets.ModelViewSet):
    queryset = ProductReference.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            return ProductReference.objects.all()
        organization = getattr(user, "organization", None)
        if organization is None:
            return ProductReference.objects.none()
        return ProductReference.objects.filter(organization=organization)

    def perform_create(self, serializer):
        user = self.request.user
        organization = getattr(user, "organization", None)
        serializer.save(organization=organization)
