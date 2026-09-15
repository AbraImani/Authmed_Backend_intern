from organizations.tenancy import TenantQuerysetMixin, get_request_organization
from rest_framework import viewsets, permissions, filters
from organizations.filters import TenantFilterBackend
from .models import ProductReference, ProductReferenceImage
from .serializers import ProductSerializer, ProductReferenceImageSerializer
from authmed_intern.permissions import TenantPermission


class ProductViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'manage'
    tenant_filters = {}
    """Provide org-scoped CRUD for ProductReference objects.

    The list/retrieve/update/partial update behavior is all driven through the
    same queryset so object-level access stays consistent across the API.
    """

    queryset = ProductReference.objects.select_related("organization", "supplier")
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    filter_backends = [TenantFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["supplier", "form", "is_active"]
    search_fields = ["name", "sku", "description", "packaging_notes", "supplier__name"]
    ordering_fields = ["name", "sku", "created_at", "updated_at"]


    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.query_params.get("show_inactive") not in {"1", "true", "True"}:
            qs = qs.filter(is_active=True)
        return qs

    def perform_create(self, serializer):
        user = self.request.user
        organization = get_request_organization(self.request)
        # The authenticated user's organization is authoritative for new references.
        serializer.save(organization=organization)


class ProductReferenceImageViewSet(TenantQuerysetMixin, viewsets.ModelViewSet):
    write_capability = 'manage'
    tenant_filters = {}
    """Org-scoped CRUD for reference image assets."""

    queryset = ProductReferenceImage.objects.select_related("product_reference", "product_reference__organization", "uploaded_by").order_by("display_order", "created_at")
    serializer_class = ProductReferenceImageSerializer
    permission_classes = [permissions.IsAuthenticated, TenantPermission]
    filter_backends = [TenantFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["product_reference", "image_type"]
    search_fields = ["notes", "source", "checksum", "product_reference__name"]
    ordering_fields = ["display_order", "created_at"]


    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
