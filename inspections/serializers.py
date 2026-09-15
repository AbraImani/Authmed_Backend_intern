from organizations.serializer_scope import TenantSerializerMixin
from organizations.tenancy import get_request_organization
from rest_framework import serializers
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision, OCRTask, InspectionProcessingRun
from organizations.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()


class EvidenceSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    image = serializers.FileField(required=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    created_by_display = serializers.SerializerMethodField(read_only=True)
    evidence_type_display = serializers.SerializerMethodField(read_only=True)
    evidence_status_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Evidence
        fields = [
            "id",
            "inspection",
            "image",
            "image_url",
            "evidence_type",
            "evidence_type_display",
            "evidence_status",
            "evidence_status_display",
            "display_order",
            "notes",
            "extracted_text",
            "extraction_status",
            "extraction_confidence",
            "metadata",
            "file_size_bytes",
            "checksum",
            "created_by",
            "created_by_display",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "created_by", "file_size_bytes", "checksum"]

    def validate(self, attrs):
        inspection = attrs.get("inspection") or getattr(self.instance, "inspection", None)
        request = self.context.get("request")
        # The mobile workflow treats evidence as incomplete without a real image.
        img = attrs.get("image") or getattr(self.instance, "image", None)
        if img is None:
            raise serializers.ValidationError({"image": "Image is required for evidence."})
        if not inspection:
            raise serializers.ValidationError({"inspection": "Inspection is required for evidence."})
        if request and request.user.is_authenticated and inspection is not None:
            organization = get_request_organization(request)
            if organization is not None and inspection.organization != organization:
                raise serializers.ValidationError("Evidence must belong to the authenticated user's organization.")
        return super().validate(attrs)

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

    def get_evidence_type_display(self, obj):
        try:
            return obj.get_evidence_type_display()
        except Exception:
            return obj.evidence_type

    def get_evidence_status_display(self, obj):
        try:
            return obj.get_evidence_status_display()
        except Exception:
            return obj.evidence_status

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            validated_data["created_by"] = user
        return super().create(validated_data)


class OCRTaskSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    """Serialize OCR preparation tasks without invoking any OCR provider."""

    evidence_display = serializers.SerializerMethodField(read_only=True)
    inspection_display = serializers.SerializerMethodField(read_only=True)
    lifecycle_summary = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OCRTask
        fields = [
            "id",
            "evidence",
            "evidence_display",
            "inspection_display",
            "status",
            "retry_count",
            "execution_started_at",
            "execution_completed_at",
            "processing_time",
            "provider_name",
            "processor_version",
            "raw_output",
            "normalized_output",
            "processing_log",
            "error_message",
            "lifecycle_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_evidence_display(self, obj):
        evidence = obj.evidence
        return {
            "id": evidence.id,
            "inspection_id": evidence.inspection_id,
            "evidence_type": evidence.evidence_type,
            "evidence_status": evidence.evidence_status,
        }

    def get_inspection_display(self, obj):
        inspection = obj.evidence.inspection
        return {
            "id": inspection.id,
            "batch_number": inspection.batch_number,
            "status": inspection.status,
            "outcome": inspection.outcome,
        }

    def get_lifecycle_summary(self, obj):
        return {
            "status": obj.status,
            "retry_count": obj.retry_count,
            "provider_name": obj.provider_name,
            "has_error": bool(obj.error_message),
            "execution_started_at": obj.execution_started_at,
            "execution_completed_at": obj.execution_completed_at,
        }

    def validate(self, attrs):
        evidence = attrs.get("evidence") or getattr(self.instance, "evidence", None)
        request = self.context.get("request")
        if evidence is None:
            raise serializers.ValidationError({"evidence": "Evidence is required for OCR tasks."})
        if request and request.user.is_authenticated:
            organization = get_request_organization(request)
            if organization is not None and evidence.inspection.organization != organization:
                raise serializers.ValidationError("OCR tasks must belong to the authenticated user's organization.")
        return super().validate(attrs)


class RiskResultSerializer(TenantSerializerMixin, serializers.ModelSerializer):
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

        # Keep the inspection/result relationship one-to-one even if the database relation changes later.
        existing = RiskResult.objects.filter(inspection=inspection)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"inspection": "This inspection already has a risk result."})

        if request and request.user.is_authenticated and inspection is not None:
            organization = get_request_organization(request)
            if organization is not None and inspection.organization != organization:
                raise serializers.ValidationError("Risk results must belong to the authenticated user's organization.")
        return super().validate(attrs)

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
        # Flutter can omit suspicion_level; the backend derives it from the score to keep payloads stable.
        if "suspicion_level" not in validated_data and "risk_score" in validated_data:
            validated_data["suspicion_level"] = self._infer_suspicion_level(validated_data["risk_score"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "suspicion_level" not in validated_data and "risk_score" in validated_data:
            validated_data["suspicion_level"] = self._infer_suspicion_level(validated_data["risk_score"])
        return super().update(instance, validated_data)


class ReviewDecisionSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    reviewer = serializers.PrimaryKeyRelatedField(read_only=True)
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

        # Only one final decision should survive for an inspection in this workflow.
        existing = ReviewDecision.objects.filter(inspection=inspection)
        if self.instance is not None:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise serializers.ValidationError({"inspection": "This inspection already has a submitted decision."})

        if request and request.user.is_authenticated:
            organization = get_request_organization(request)
            if organization is not None and inspection is not None and inspection.organization != organization:
                raise serializers.ValidationError("Review decisions must belong to the authenticated user's organization.")
        return super().validate(attrs)

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
        # The API defaults reviewer to the authenticated user so Flutter does not have to send it.
        if user and user.is_authenticated and "reviewer" not in validated_data:
            validated_data["reviewer"] = user
        return super().create(validated_data)


class InspectionSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    evidences = EvidenceSerializer(many=True, read_only=True)
    risk_result = RiskResultSerializer(read_only=True)
    decisions = ReviewDecisionSerializer(many=True, read_only=True)
    organization = serializers.PrimaryKeyRelatedField(queryset=Organization.objects.all(), required=False, allow_null=True)
    inspector = serializers.PrimaryKeyRelatedField(read_only=True)
    organization_display = serializers.SerializerMethodField(read_only=True)
    site_display = serializers.SerializerMethodField(read_only=True)
    supplier_display = serializers.SerializerMethodField(read_only=True)
    product_display = serializers.SerializerMethodField(read_only=True)
    inspector_display = serializers.SerializerMethodField(read_only=True)
    outcome = serializers.CharField(read_only=True)
    outcome_display = serializers.SerializerMethodField(read_only=True)
    risk_result_summary = serializers.SerializerMethodField(read_only=True)
    decision_summary = serializers.SerializerMethodField(read_only=True)
    processing_summary = serializers.SerializerMethodField(read_only=True)

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
            "processing_summary",
            "decisions",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            organization = attrs.get("organization") or getattr(self.instance, "organization", None) or get_request_organization(request)
            site = attrs.get("site") or getattr(self.instance, "site", None)
            supplier = attrs.get("supplier") or getattr(self.instance, "supplier", None)
            product = attrs.get("product") or getattr(self.instance, "product", None)
            inspector = attrs.get("inspector") or getattr(self.instance, "inspector", None)

            if organization is not None:
                if get_request_organization(request) != organization:
                    raise serializers.ValidationError("Inspection organization must match the authenticated user's organization.")

            if site is not None and organization is not None and site.organization != organization:
                raise serializers.ValidationError("Site must belong to the selected organization.")

            if product is not None and organization is not None and product.organization != organization:
                raise serializers.ValidationError("Product reference must belong to the selected organization.")


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

        return super().validate(attrs)

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
        # Stable, compact summary so the mobile app does not need to remap nested risk result objects.
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
        # Always expose the latest decision because the inspection detail screen renders a single final state.
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

    def get_processing_summary(self, obj):
        ocr_tasks = OCRTask.objects.filter(evidence__inspection=obj).order_by("-created_at")
        latest_task = ocr_tasks.first()
        latest_run = InspectionProcessingRun.objects.filter(inspection=obj).order_by("-created_at").first()
        if not latest_task and not latest_run:
            return {"exists": False}
        return {
            "exists": True,
            "latest_run_id": latest_run.id if latest_run else None,
            "latest_run_status": latest_run.status if latest_run else None,
            "failure_reason": latest_run.failure_reason if latest_run else None,
            "requires_review": bool(latest_run and latest_run.status == "failed"),
            "latest_run_stage": latest_run.current_stage if latest_run else None,
            "latest_run_queued_at": latest_run.queued_at if latest_run else None,
            "latest_run_started_at": latest_run.execution_started_at if latest_run else None,
            "latest_run_completed_at": latest_run.execution_completed_at if latest_run else None,
            "latest_risk_level": latest_run.risk_level if latest_run else None,
            "latest_risk_score": float(latest_run.risk_score) if latest_run and latest_run.risk_score is not None else None,
            "latest_confidence": float(latest_run.confidence) if latest_run and latest_run.confidence is not None else None,
            "latest_task_id": latest_task.id if latest_task else None,
            "latest_status": latest_task.status if latest_task else None,
            "latest_provider": latest_task.provider_name if latest_task else None,
            "queued_count": ocr_tasks.filter(status="queued").count(),
            "processing_count": ocr_tasks.filter(status="processing").count(),
            "completed_count": ocr_tasks.filter(status="completed").count(),
            "failed_count": ocr_tasks.filter(status="failed").count(),
            "cancelled_count": ocr_tasks.filter(status="cancelled").count(),
        }


class InspectionProcessingRunSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    """Expose a compact inspection processing history payload."""

    inspection_display = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.SerializerMethodField(read_only=True)
    stage_display = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = InspectionProcessingRun
        fields = [
            "id",
            "inspection",
            "inspection_display",
            "created_by",
            "status",
            "status_display",
            "current_stage",
            "stage_display",
            "retry_count",
            "execution_started_at",
            "execution_completed_at",
            "queued_at",
            "failed_at",
            "cancelled_at",
            "processing_duration",
            "provider_name",
            "ocr_summary",
            "comparison_summary",
            "scoring_summary",
            "triggered_rules",
            "risk_level",
            "risk_score",
            "confidence",
            "explanation",
            "failure_reason",
            "processing_log",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_inspection_display(self, obj):
        return {"id": obj.inspection.id, "batch_number": obj.inspection.batch_number, "status": obj.inspection.status}

    def get_status_display(self, obj):
        try:
            return obj.get_status_display()
        except Exception:
            return obj.status

    def get_stage_display(self, obj):
        try:
            return obj.get_current_stage_display()
        except Exception:
            return obj.current_stage
