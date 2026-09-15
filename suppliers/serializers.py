from organizations.serializer_scope import TenantSerializerMixin
from organizations.tenancy import get_request_organization
from rest_framework import serializers
from .models import Supplier


class SupplierSerializer(TenantSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "organization", "name", "contact", "address", "created_at"]

        read_only_fields = ["organization", "created_at"]
