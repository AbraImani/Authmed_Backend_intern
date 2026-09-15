from django.contrib import admin
from .models import ProductReference, ProductReferenceImage


class ProductReferenceImageInline(admin.TabularInline):
    model = ProductReferenceImage
    extra = 0
    readonly_fields = ("checksum", "created_at")
    fields = ("image", "image_type", "display_order", "angle", "lighting_condition", "source", "notes", "checksum", "created_at")


@admin.register(ProductReference)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "supplier", "sku", "form", "strength", "is_active", "created_at")
    list_filter = ("organization", "supplier", "form", "is_active")
    search_fields = ("name", "sku", "description", "packaging_notes", "supplier__name")
    date_hierarchy = "created_at"
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("organization", "supplier")
    autocomplete_fields = ("supplier",)
    inlines = [ProductReferenceImageInline]


@admin.register(ProductReferenceImage)
class ProductReferenceImageAdmin(admin.ModelAdmin):
    list_display = ("product_reference", "image_type", "display_order", "uploaded_by", "checksum", "created_at")
    list_filter = ("image_type", "product_reference__organization")
    search_fields = ("product_reference__name", "notes", "source", "uploaded_by__username")
    readonly_fields = ("checksum", "created_at")
    list_select_related = ("product_reference", "uploaded_by", "product_reference__organization")
