from rest_framework import serializers
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision


class EvidenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evidence
        fields = ["id", "inspection", "image", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        request = self.context.get("request")
        if request and request.user.is_authenticated and inspection is not None:
            organization = getattr(request.user, "organization", None)
            if organization is not None and inspection.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Evidence must belong to the authenticated user's organization.")
        return attrs


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

    class Meta:
        model = BatchInspection
        fields = [
            "id",
            "organization",
            "site",
            "supplier",
            "product",
            "inspector",
            "batch_number",
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

        return attrs
