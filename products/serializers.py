from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ProductReference, ProductReferenceImage, DatasetGroup, DatasetGroupImage

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


class DatasetGroupSerializer(serializers.ModelSerializer):
    """Serialize dataset groups used for labeling and review preparation."""

    organization_display = serializers.SerializerMethodField(read_only=True)
    created_by_display = serializers.SerializerMethodField(read_only=True)
    annotation_status_display = serializers.SerializerMethodField(read_only=True)
    quality_flag_display = serializers.SerializerMethodField(read_only=True)
    reference_images_display = serializers.SerializerMethodField(read_only=True)
    reference_images = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ProductReferenceImage.objects.select_related("product_reference", "product_reference__organization"),
        required=False,
    )

    class Meta:
        model = DatasetGroup
        fields = [
            "id",
            "organization",
            "organization_display",
            "name",
            "description",
            "labeling_ready",
            "annotation_status",
            "annotation_status_display",
            "quality_flag",
            "quality_flag_display",
            "reference_images",
            "reference_images_display",
            "created_by",
            "created_by_display",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_by", "created_at", "updated_at"]

    def get_organization_display(self, obj):
        return getattr(obj.organization, "name", None)

    def get_created_by_display(self, obj):
        if obj.created_by:
            return {"id": obj.created_by.id, "username": getattr(obj.created_by, "username", None)}
        return None

    def get_annotation_status_display(self, obj):
        try:
            return obj.get_annotation_status_display()
        except Exception:
            return obj.annotation_status

    def get_quality_flag_display(self, obj):
        try:
            return obj.get_quality_flag_display()
        except Exception:
            return obj.quality_flag

    def get_reference_images_display(self, obj):
        images = []
        for image in obj.reference_images.select_related("product_reference", "product_reference__organization", "uploaded_by"):
            images.append(
                {
                    "id": image.id,
                    "product_reference": image.product_reference_id,
                    "product_reference_display": getattr(image.product_reference, "name", None),
                    "image_type": image.image_type,
                    "image_type_display": image.get_image_type_display() if hasattr(image, "get_image_type_display") else image.image_type,
                    "checksum": image.checksum,
                }
            )
        return images

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        reference_images = attrs.get("reference_images") or []
        organization = attrs.get("organization") or getattr(self.instance, "organization", None) or getattr(user, "organization", None)

        if request and user and user.is_authenticated:
            if organization is not None and getattr(user, "role", None) != "admin" and user.organization != organization:
                raise serializers.ValidationError("Dataset groups must belong to the authenticated user's organization.")

        for image in reference_images:
            if organization is not None and image.product_reference.organization != organization and getattr(user, "role", None) != "admin":
                raise serializers.ValidationError("Dataset images must belong to the same organization as the dataset group.")
        return attrs

    def create(self, validated_data):
        reference_images = validated_data.pop("reference_images", [])
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["created_by"] = user
            validated_data["organization"] = getattr(user, "organization", None)
        dataset_group = super().create(validated_data)
        self._sync_reference_images(dataset_group, reference_images)
        return dataset_group

    def update(self, instance, validated_data):
        reference_images = validated_data.pop("reference_images", None)
        dataset_group = super().update(instance, validated_data)
        if reference_images is not None:
            self._sync_reference_images(dataset_group, reference_images)
        return dataset_group

    def _sync_reference_images(self, dataset_group, reference_images):
        DatasetGroupImage.objects.filter(dataset_group=dataset_group).delete()
        for index, image in enumerate(reference_images):
            DatasetGroupImage.objects.create(dataset_group=dataset_group, reference_image=image, sort_order=index)
