from rest_framework import serializers
from .models import User
from organizations.models import OrganizationMembership
from organizations.roles import CAPABILITIES

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = fields

class MeMembershipSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    primary_site = serializers.SerializerMethodField()

    class Meta:
        model = OrganizationMembership
        fields = ["id", "organization", "role", "is_active", "primary_site"]

    def get_organization(self, obj) -> dict:
        return {"id": obj.organization_id, "name": obj.organization.name}

    def get_primary_site(self, obj) -> dict | None:
        if obj.primary_site_id and obj.primary_site.organization_id == obj.organization_id:
            return {"id": obj.primary_site_id, "name": obj.primary_site.name}
        return None

class MeSerializer(serializers.ModelSerializer):
    memberships = MeMembershipSerializer(many=True, read_only=True)
    active_context = serializers.SerializerMethodField()
    capabilities = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "firebase_uid", "email", "first_name", "last_name", "memberships", "active_context", "capabilities"]
        read_only_fields = fields

    def get_active_context(self, obj) -> dict | None:
        member = self.context.get("membership")
        return MeMembershipSerializer(member).data if member else None

    def get_capabilities(self, obj) -> list[str]:
        member = self.context.get("membership")
        return sorted(CAPABILITIES.get(member.role, ())) if member else []
