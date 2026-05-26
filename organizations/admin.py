from django.contrib import admin
from .models import Organization, Site


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "address")
    date_hierarchy = "created_at"


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "created_at")
    list_filter = ("organization",)
    search_fields = ("name", "address")
    date_hierarchy = "created_at"
