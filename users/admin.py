from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (("Legacy business fields", {"fields": ("role", "organization", "site", "firebase_uid")}),)
    readonly_fields = ("firebase_uid",)
