from django.contrib import admin
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision


@admin.register(BatchInspection)
class BatchInspectionAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "supplier", "inspector", "outcome", "received_at")
    list_filter = ("outcome", "organization", "site", "supplier")
    search_fields = ("batch_number", "product__name", "supplier__name", "inspector__username")
    date_hierarchy = "received_at"


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "inspection", "created_at")
    search_fields = ("inspection__batch_number", "notes")
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
