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
    inspection_display = serializers.SerializerMethodField(read_only=True)
    suspicion_level_display = serializers.SerializerMethodField(read_only=True)
    is_high_risk = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = RiskResult
        fields = [
            "id",
            "inspection",
            "inspection_display",
            "risk_score",
            "suspicion_level",
            "suspicion_level_display",
            "confidence",
            "flags",
            "reason",
            "is_high_risk",
            "calculated_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def _infer_suspicion_level(self, risk_score):
        score = float(risk_score)
        if score >= 85:
            return "critical"
        if score >= 60:
            return "high"
        if score >= 30:
            return "medium"
        return "low"

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        request = self.context.get("request")
        if inspection is None:
            raise serializers.ValidationError({"inspection": "Inspection is required for risk results."})

        risk_score = attrs.get("risk_score")
        if risk_score is not None:
            score = float(risk_score)
            if score < 0 or score > 100:
                raise serializers.ValidationError({"risk_score": "Risk score must be between 0 and 100."})

        confidence = attrs.get("confidence")
        if confidence is not None:
            confidence_value = float(confidence)
            if confidence_value < 0 or confidence_value > 100:
                raise serializers.ValidationError({"confidence": "Confidence must be between 0 and 100."})

        existing = RiskResult.objects.filter(inspection=inspection)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"inspection": "This inspection already has a risk result."})

        if request and request.user.is_authenticated and inspection is not None:
            organization = getattr(request.user, "organization", None)
            if organization is not None and inspection.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Risk results must belong to the authenticated user's organization.")
        return attrs

    def get_inspection_display(self, obj):
        if obj.inspection:
            return {
                "id": obj.inspection.id,
                "batch_number": getattr(obj.inspection, "batch_number", None),
                "status": getattr(obj.inspection, "status", None),
            }
        return None

    def get_suspicion_level_display(self, obj):
        try:
            return obj.get_suspicion_level_display()
        except Exception:
            return obj.suspicion_level

    def get_is_high_risk(self, obj):
        return obj.suspicion_level in {"high", "critical"}

    def create(self, validated_data):
        if "suspicion_level" not in validated_data and "risk_score" in validated_data:
            validated_data["suspicion_level"] = self._infer_suspicion_level(validated_data["risk_score"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "suspicion_level" not in validated_data and "risk_score" in validated_data:
            validated_data["suspicion_level"] = self._infer_suspicion_level(validated_data["risk_score"])
        return super().update(instance, validated_data)


class ReviewDecisionSerializer(serializers.ModelSerializer):
    reviewer_display = serializers.SerializerMethodField(read_only=True)
    decision_display = serializers.SerializerMethodField(read_only=True)
    reviewed_at = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = ReviewDecision
        fields = [
            "id",
            "inspection",
            "reviewer",
            "reviewer_display",
            "decision",
            "decision_display",
            "notes",
            "reviewed_at",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        reviewer = attrs.get("reviewer") or getattr(self.instance, "reviewer", None)
        request = self.context.get("request")
        if inspection is None:
            raise serializers.ValidationError({"inspection": "Inspection is required for decisions."})

        existing = ReviewDecision.objects.filter(inspection=inspection)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"inspection": "This inspection already has a submitted decision."})

        if request and request.user.is_authenticated:
            organization = getattr(request.user, "organization", None)
            if organization is not None and inspection is not None and inspection.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Review decisions must belong to the authenticated user's organization.")
            if reviewer is not None and reviewer.organization is not None and organization is not None and reviewer.organization != organization and getattr(request.user, "role", None) != "admin":
                raise serializers.ValidationError("Reviewer must belong to the same organization as the inspection.")
        return attrs

    def get_reviewer_display(self, obj):
        if obj.reviewer:
            return {"id": obj.reviewer.id, "username": getattr(obj.reviewer, "username", None)}
        return None

    def get_decision_display(self, obj):
        try:
            return obj.get_decision_display()
        except Exception:
            return obj.decision

    def get_reviewed_at(self, obj):
        return obj.created_at

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated and "reviewer" not in validated_data:
            validated_data["reviewer"] = user
        return super().create(validated_data)


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
    risk_result_summary = serializers.SerializerMethodField(read_only=True)
    decision_summary = serializers.SerializerMethodField(read_only=True)

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
            "risk_result_summary",
            "decision_summary",
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

    def get_risk_result_summary(self, obj):
        risk = getattr(obj, "risk_result", None)
        if not risk:
            return {"exists": False}
        return {
            "exists": True,
            "id": risk.id,
            "risk_score": str(risk.risk_score),
            "suspicion_level": risk.suspicion_level,
            "reason": risk.reason,
            "confidence": str(risk.confidence) if risk.confidence is not None else None,
            "calculated_at": risk.calculated_at,
        }

    def get_decision_summary(self, obj):
        latest_decision = obj.decisions.order_by("-created_at").first()
        if not latest_decision:
            return {"exists": False}
        return {
            "exists": True,
            "id": latest_decision.id,
            "decision": latest_decision.decision,
            "decision_display": latest_decision.get_decision_display(),
            "notes": latest_decision.notes,
            "reviewer_display": {
                "id": latest_decision.reviewer.id,
                "username": getattr(latest_decision.reviewer, "username", None),
            }
            if latest_decision.reviewer
            else None,
            "reviewed_at": latest_decision.created_at,
        }

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
