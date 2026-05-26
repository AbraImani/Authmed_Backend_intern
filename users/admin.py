from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "role", "organization", "site", "is_staff")
    list_filter = ("role", "organization", "site", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
