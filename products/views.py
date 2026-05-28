from rest_framework import viewsets, permissions
from .models import ProductReference
from .serializers import ProductSerializer
from authmed_intern.permissions import IsOrgMember


class ProductViewSet(viewsets.ModelViewSet):
    """Provide org-scoped CRUD for ProductReference objects.

    The list/retrieve/update/partial update behavior is all driven through the
    same queryset so object-level access stays consistent across the API.
    """

    queryset = ProductReference.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]

    def get_queryset(self):
        user = self.request.user
        qs = ProductReference.objects.select_related("organization", "supplier")
        # Admin users can see all references or narrow to a specific organization.
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            org_id = self.request.query_params.get("organization")
            if org_id:
                return qs.filter(organization_id=org_id)
            return qs

        organization = getattr(user, "organization", None)
        if organization is None:
            return ProductReference.objects.none()

        # Regular users see only active references for their own organization by default.
        show_inactive = self.request.query_params.get("show_inactive") in {"1", "true", "True"}
        if show_inactive:
            return qs.filter(organization=organization)
        return qs.filter(organization=organization, is_active=True)

    def perform_create(self, serializer):
        user = self.request.user
        organization = getattr(user, "organization", None)
        # The authenticated user's organization is authoritative for new references.
        serializer.save(organization=organization)
