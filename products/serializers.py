from rest_framework import serializers
from .models import ProductReference


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
