from django.contrib import admin
from .models import ProductReference


@admin.register(ProductReference)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "supplier", "sku", "form", "strength", "is_active", "created_at")
    list_filter = ("organization", "supplier", "form", "is_active")
    search_fields = ("name", "sku", "description", "packaging_notes", "supplier__name")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("organization", "supplier")
    autocomplete_fields = ("supplier",)
