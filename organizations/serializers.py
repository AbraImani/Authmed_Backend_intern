from organizations.serializer_scope import TenantSerializerMixin
from organizations.tenancy import get_request_organization
from rest_framework import serializers
from .models import Organization, Site


class OrganizationSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "address", "created_at"]
        read_only_fields = ["id", "created_at"]


class SiteSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ["id", "organization", "name", "address", "created_at"]
        read_only_fields = ["id", "created_at"]
