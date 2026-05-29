from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ProductReference, ProductReferenceImage

User = get_user_model()


class ProductSerializer(serializers.ModelSerializer):
    """Serialize product references as a compact, inspection-ready payload.

    The API keeps the reference structure intentionally simple so Flutter and
    backend workflows can rely on stable product, supplier, and organization
    fields without extra mapping.
    """

    organization_display = serializers.SerializerMethodField(read_only=True)
    supplier_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductReference
        fields = [
            "id",
            "organization",
            "organization_display",
            "name",
            "sku",
            "supplier",
            "supplier_display",
            "form",
            "strength",
            "pack_size",
            "packaging_notes",
            "description",
            "is_active",
            "reference_image",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at", "organization", "organization_display", "supplier_display"]

    def get_organization_display(self, obj):
        return getattr(obj.organization, "name", None)

    def get_supplier_display(self, obj):
        return getattr(obj.supplier, "name", None)

    def validate(self, data):
        """Enforce organization scoping and prevent duplicate names within an organization."""
        request = self.context.get("request")
        user = getattr(request, "user", None)
        org = getattr(user, "organization", None)
        # This serializer intentionally blocks cross-organization writes; the
        # ProductReference library is always managed inside one organization boundary.
        if request and request.method in ("POST", "PUT", "PATCH"):
            if org is None:
                raise serializers.ValidationError("Authenticated user must belong to an organization to create product references.")
            # Avoid duplicate human-readable reference names within the same organization.
            name = data.get("name")
            qs = ProductReference.objects.filter(organization=org, name__iexact=name)
            # When updating, exclude the current instance so PATCH/PUT stays idempotent.
            instance = getattr(self, "instance", None)
            if instance:
                qs = qs.exclude(pk=instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"name": "A product reference with this name already exists in your organization."})
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        org = getattr(user, "organization", None)
        if org:
            # The authenticated user's organization is the source of truth for new references.
            validated_data["organization"] = org
        return super().create(validated_data)


class ProductReferenceImageSerializer(serializers.ModelSerializer):
    """Serialize reference images as a lightweight upload-ready payload."""

    product_reference_display = serializers.SerializerMethodField(read_only=True)
    organization_display = serializers.SerializerMethodField(read_only=True)
    uploaded_by_display = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    image_type_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ProductReferenceImage
        fields = [
            "id",
            "product_reference",
            "product_reference_display",
            "organization_display",
            "image",
            "image_url",
            "image_type",
            "image_type_display",
            "angle",
            "lighting_condition",
            "source",
            "uploaded_by",
            "uploaded_by_display",
            "checksum",
            "notes",
            "display_order",
            "created_at",
        ]
        read_only_fields = ["id", "checksum", "created_at", "uploaded_by"]

    def get_product_reference_display(self, obj):
        return getattr(obj.product_reference, "name", None)

    def get_organization_display(self, obj):
        return getattr(obj.organization, "name", None)

    def get_uploaded_by_display(self, obj):
        if obj.uploaded_by:
            return {"id": obj.uploaded_by.id, "username": getattr(obj.uploaded_by, "username", None)}
        return None

    def get_image_url(self, obj):
        try:
            if obj.image and hasattr(obj.image, "url"):
                return obj.image.url
        except Exception:
            return None
        return None

    def get_image_type_display(self, obj):
        try:
            return obj.get_image_type_display()
        except Exception:
            return obj.image_type

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        product_reference = attrs.get("product_reference") or getattr(self.instance, "product_reference", None)
        if product_reference is None:
            raise serializers.ValidationError({"product_reference": "Product reference is required."})

        if request and user and user.is_authenticated:
            organization = getattr(user, "organization", None)
            if organization is not None and product_reference.organization != organization and getattr(user, "role", None) != "admin":
                raise serializers.ValidationError("Reference images must belong to the authenticated user's organization.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["uploaded_by"] = user
        return super().create(validated_data)
