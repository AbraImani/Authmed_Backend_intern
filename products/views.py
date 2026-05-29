from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ProductReference, ProductReferenceImage
from .models import DatasetGroup
from .serializers import ProductSerializer, ProductReferenceImageSerializer, DatasetGroupSerializer
from authmed_intern.permissions import IsOrgMember


class ProductViewSet(viewsets.ModelViewSet):
    """Provide org-scoped CRUD for ProductReference objects.

    The list/retrieve/update/partial update behavior is all driven through the
    same queryset so object-level access stays consistent across the API.
    """

    queryset = ProductReference.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["supplier", "form", "is_active"]
    search_fields = ["name", "sku", "description", "packaging_notes", "supplier__name"]
    ordering_fields = ["name", "sku", "created_at", "updated_at"]

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


class ProductReferenceImageViewSet(viewsets.ModelViewSet):
    """Org-scoped CRUD for reference image assets."""

    queryset = ProductReferenceImage.objects.all()
    serializer_class = ProductReferenceImageSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["product_reference", "image_type"]
    search_fields = ["notes", "source", "checksum", "product_reference__name"]
    ordering_fields = ["display_order", "created_at"]

    def get_queryset(self):
        user = self.request.user
        qs = ProductReferenceImage.objects.select_related("product_reference", "product_reference__organization", "uploaded_by")
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            organization_id = self.request.query_params.get("organization")
            product_reference_id = self.request.query_params.get("product_reference")
            image_type = self.request.query_params.get("image_type")
            if organization_id:
                qs = qs.filter(product_reference__organization_id=organization_id)
            if product_reference_id:
                qs = qs.filter(product_reference_id=product_reference_id)
            if image_type:
                qs = qs.filter(image_type=image_type)
            return qs.order_by("display_order", "created_at")

        organization = getattr(user, "organization", None)
        if organization is None:
            return ProductReferenceImage.objects.none()

        qs = qs.filter(product_reference__organization=organization)
        product_reference_id = self.request.query_params.get("product_reference")
        image_type = self.request.query_params.get("image_type")
        if product_reference_id:
            qs = qs.filter(product_reference_id=product_reference_id)
        if image_type:
            qs = qs.filter(image_type=image_type)
        return qs.order_by("display_order", "created_at")

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)


class DatasetGroupViewSet(viewsets.ModelViewSet):
    """Org-scoped CRUD for dataset readiness groups."""

    queryset = DatasetGroup.objects.all()
    serializer_class = DatasetGroupSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgMember]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["annotation_status", "quality_flag", "labeling_ready"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at", "updated_at"]

    def get_queryset(self):
        user = self.request.user
        qs = DatasetGroup.objects.prefetch_related("reference_images", "reference_images__product_reference")
        if user.is_authenticated and getattr(user, "role", None) == "admin":
            organization_id = self.request.query_params.get("organization")
            if organization_id:
                qs = qs.filter(organization_id=organization_id)
            return qs.order_by("name")

        organization = getattr(user, "organization", None)
        if organization is None:
            return DatasetGroup.objects.none()

        qs = qs.filter(organization=organization)
        return qs.order_by("name")
