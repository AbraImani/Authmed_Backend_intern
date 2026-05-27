from rest_framework import serializers
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision
from organizations.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()


class EvidenceSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    created_by_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Evidence
        fields = ["id", "inspection", "image", "image_url", "evidence_type", "notes", "created_by", "created_by_display", "created_at"]
        read_only_fields = ["id", "created_at", "created_by"]

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        request = self.context.get("request")
        # require image on creation
        img = attrs.get("image") or getattr(self.instance, "image", None)
        if img is None:
            raise serializers.ValidationError({"image": "Image is required for evidence."})
        if not inspection:
            raise serializers.ValidationError({"inspection": "Inspection is required for evidence."})
        if request and request.user.is_authenticated and inspection is not None:
            organization = getattr(request.user, "organization", None)
            if organization is not None and inspection.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Evidence must belong to the authenticated user's organization.")
        return attrs

    def get_image_url(self, obj):
        try:
            if obj.image and hasattr(obj.image, 'url'):
                return obj.image.url
        except Exception:
            return None
        return None

    def get_created_by_display(self, obj):
        if obj.created_by:
            return {"id": obj.created_by.id, "username": getattr(obj.created_by, "username", None)}
        return None

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["created_by"] = user
        return super().create(validated_data)


class RiskResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskResult
        fields = ["id", "inspection", "risk_score", "reason", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        request = self.context.get("request")
        if request and request.user.is_authenticated and inspection is not None:
            organization = getattr(request.user, "organization", None)
            if organization is not None and inspection.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Risk results must belong to the authenticated user's organization.")
        return attrs


class ReviewDecisionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewDecision
        fields = ["id", "inspection", "reviewer", "decision", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        reviewer = attrs.get("reviewer") or getattr(self.instance, "reviewer", None)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            organization = getattr(request.user, "organization", None)
            if organization is not None and inspection is not None and inspection.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Review decisions must belong to the authenticated user's organization.")
            if reviewer is not None and reviewer.organization is not None and organization is not None and reviewer.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Reviewer must belong to the same organization as the inspection.")
        return attrs


class InspectionSerializer(serializers.ModelSerializer):
    evidences = EvidenceSerializer(many=True, read_only=True)
    risk_result = RiskResultSerializer(read_only=True)
    decisions = ReviewDecisionSerializer(many=True, read_only=True)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), required=False, allow_null=True)
    inspector = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True)
    organization_display = serializers.SerializerMethodField(read_only=True)
    site_display = serializers.SerializerMethodField(read_only=True)
    supplier_display = serializers.SerializerMethodField(read_only=True)
    product_display = serializers.SerializerMethodField(read_only=True)
    inspector_display = serializers.SerializerMethodField(read_only=True)
    outcome = serializers.CharField(read_only=True)
    outcome_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BatchInspection
        fields = [
            "id",
            "organization",
            "site",
            "supplier",
            "product",
            "inspector",
            "organization_display",
            "site_display",
            "supplier_display",
            "product_display",
            "inspector_display",
            "batch_number",
            "expiry_date",
            "notes",
            "status",
            "outcome",
            "outcome_display",
            "received_at",
            "created_at",
            "evidences",
            "risk_result",
            "decisions",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            organization = attrs.get("organization") or getattr(self.instance, "organization", None)
            site = attrs.get("site") or getattr(self.instance, "site", None)
            supplier = attrs.get("supplier") or getattr(self.instance, "supplier", None)
            product = attrs.get("product") or getattr(self.instance, "product", None)
            inspector = attrs.get("inspector") or getattr(self.instance, "inspector", None)

            if organization is not None and getattr(user, "role", None) != "admin":
                if user.organization != organization:
                    raise serializers.ValidationError("Inspection organization must match the authenticated user's organization.")

            if site is not None and organization is not None and site.organization != organization:
                raise serializers.ValidationError("Site must belong to the selected organization.")

            if product is not None and organization is not None and product.organization != organization:
                raise serializers.ValidationError("Product reference must belong to the selected organization.")

            if inspector is not None and inspector.organization is not None and organization is not None and inspector.organization != organization:
                raise serializers.ValidationError("Inspector must belong to the selected organization.")

            # Validate expiry_date does not precede received_at
            expiry = attrs.get("expiry_date") or getattr(self.instance, "expiry_date", None)
            received = attrs.get("received_at") or getattr(self.instance, "received_at", None)
            if expiry is not None and received is not None:
                try:
                    rec_date = received.date()
                except Exception:
                    rec_date = None
                if rec_date is not None and expiry < rec_date:
                    raise serializers.ValidationError("Expiry date cannot be before the received date.")

        return attrs

    def get_organization_display(self, obj):
        return getattr(obj.organization, "name", None)

    def get_site_display(self, obj):
        return getattr(obj.site, "name", None)

    def get_supplier_display(self, obj):
        return getattr(obj.supplier, "name", None) if obj.supplier else None

    def get_product_display(self, obj):
        return getattr(obj.product, "name", None) if obj.product else None

    def get_inspector_display(self, obj):
        if obj.inspector:
            return {"id": obj.inspector.id, "username": getattr(obj.inspector, "username", None)}
        return None

    def get_outcome_display(self, obj):
        try:
            return obj.get_outcome_display()
        except Exception:
            return getattr(obj, "outcome", None)

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        # Ensure organization and inspector default to request user when available
        if user and user.is_authenticated:
            if "organization" not in validated_data:
                validated_data["organization"] = getattr(user, "organization", None)
            if "inspector" not in validated_data:
                validated_data["inspector"] = user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # Allow partial updates from mobile; do not overwrite organization unintentionally
        if "organization" in validated_data and getattr(instance, "organization", None) is not None:
            # prevent changing organization through update
            validated_data.pop("organization", None)
        return super().update(instance, validated_data)
