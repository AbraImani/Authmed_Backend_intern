from django.contrib import admin
from .models import BatchInspection, Evidence, RiskResult, ReviewDecision


@admin.register(BatchInspection)
class BatchInspectionAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "supplier", "inspector", "outcome", "received_at")
    list_filter = ("outcome", "organization")


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("id", "inspection", "created_at")


@admin.register(RiskResult)
class RiskResultAdmin(admin.ModelAdmin):
    list_display = ("inspection", "risk_score", "created_at")


@admin.register(ReviewDecision)
class ReviewDecisionAdmin(admin.ModelAdmin):
    list_display = ("inspection", "reviewer", "decision", "created_at")
