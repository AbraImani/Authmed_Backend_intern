from django.contrib import admin
from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "actor", "action", "object_type", "object_id")
    list_filter = ("action", "object_type", "timestamp")
    search_fields = ("actor", "action", "object_type", "object_id")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp", "actor", "action", "object_type", "object_id", "details")
