from django.contrib import admin
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision, OCRTask


@admin.register(BatchInspection)
class BatchInspectionAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "supplier", "inspector", "outcome", "received_at")
    list_filter = ("outcome", "organization", "site", "supplier")
    search_fields = ("batch_number", "product__name", "supplier__name", "inspector__username")
    date_hierarchy = "received_at"


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "inspection", "evidence_type", "evidence_status", "display_order", "created_at")
    list_filter = ("evidence_type", "evidence_status")
    search_fields = ("inspection__batch_number", "notes", "extracted_text")
    date_hierarchy = "created_at"


@admin.register(RiskResult)
class RiskResultAdmin(admin.ModelAdmin):
    list_display = ("inspection", "risk_score", "created_at")
    search_fields = ("inspection__batch_number", "reason")
    date_hierarchy = "created_at"


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("inspection", "reviewer", "decision", "created_at")
    list_filter = ("decision",)
    search_fields = ("inspection__batch_number", "reviewer__username", "notes")
    date_hierarchy = "created_at"


@admin.register(OCRTask)
class OCRTaskAdmin(admin.ModelAdmin):
    list_display = ("evidence", "status", "retry_count", "processor_version", "created_at")
    list_filter = ("status",)
    search_fields = ("evidence__inspection__batch_number", "processor_version", "error_message")
    date_hierarchy = "created_at"
