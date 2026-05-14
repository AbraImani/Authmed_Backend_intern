from django.contrib import admin
from .models import ProductReference


@admin.register(ProductReference)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "sku", "created_at")
    list_filter = ("organization",)
