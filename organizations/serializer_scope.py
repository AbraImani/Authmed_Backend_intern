from rest_framework import serializers
from .tenancy import get_request_organization, scope_queryset, object_organization_id

class TenantSerializerMixin:
    """Scope incoming IDs before validation, including many-to-many relations."""
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return fields
        organization = get_request_organization(request)
        for field in fields.values():
            relation = getattr(field, "child_relation", field)
            if not relation.read_only and getattr(relation, "queryset", None) is not None:
                relation.queryset = scope_queryset(relation.queryset, organization)
        return fields

    def to_internal_value(self, data):
        request = self.context.get("request")
        organization = get_request_organization(request) if request else None
        # Even read-only organization input must never silently select a foreign tenant.
        if organization and "organization" in data and str(data["organization"]) != str(organization.pk):
            raise serializers.ValidationError({"organization": "Invalid organization context."})
        return super().to_internal_value(data)

    def validate(self, attrs):
        request = self.context.get("request")
        if request:
            organization = get_request_organization(request)
            for field in self.Meta.model._meta.fields:
                if not field.is_relation or field.name in {"created_by", "uploaded_by", "reviewer", "inspector", "user"}:
                    continue
                value = attrs.get(field.name, getattr(self.instance, field.name, None))
                if value is not None and object_organization_id(value) != organization.pk:
                    raise serializers.ValidationError({field.name: "Relation is outside the active organization."})
        return super().validate(attrs)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        request = self.context.get("request")
        if not request:
            return result
        organization = get_request_organization(request)
        for field in instance._meta.fields:
            if not field.is_relation or field.name not in result:
                continue
            value = getattr(instance, field.name, None)
            if value is None:
                continue
            if value._meta.label_lower == "users.user":
                allowed = value.memberships.filter(organization=organization).exists()
            else:
                allowed = object_organization_id(value) == organization.pk
            if not allowed:
                result[field.name] = None
                display = field.name + "_display"
                if display in result:
                    result[display] = None
        return result
