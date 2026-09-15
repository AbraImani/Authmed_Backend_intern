"""Shared tenant boundary for API queries, relations and object permissions."""
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import OrganizationMembership

# Unknown objects fail closed. Users are multi-tenant and handled separately.
TENANT_PATHS = {
    "organizations.organization": "pk",
    "organizations.site": "organization_id",
    "organizations.organizationmembership": "organization_id",
    "suppliers.supplier": "organization_id",
    "products.productreference": "organization_id",
    "products.productreferenceimage": "product_reference__organization_id",
    "inspections.batchinspection": "organization_id",
    "inspections.evidence": "inspection__organization_id",
    "inspections.ocrtask": "evidence__inspection__organization_id",
    "inspections.inspectionprocessingrun": "inspection__organization_id",
    "inspections.riskresult": "inspection__organization_id",
    "inspections.reviewdecision": "inspection__organization_id",
    "audits.auditlog": "organization_id",
}

def get_active_membership(request, required=True):
    if hasattr(request, "_authmed_membership"):
        membership = request._authmed_membership
    else:
        user = request.user
        membership = None
        if user and user.is_authenticated and user.is_active:
            qs = OrganizationMembership.objects.select_related("organization", "primary_site").filter(user=user, is_active=True)
            selection = request.headers.get("X-Organization-ID")
            if selection is not None:
                if not selection.isascii() or not selection.isdigit() or len(selection) > 18:
                    raise PermissionDenied("Invalid organization context.")
                membership = qs.filter(organization_id=int(selection)).first()
                if membership is None:
                    raise PermissionDenied("Organization context is not authorized.")
            else:
                choices = list(qs.order_by("pk")[:2])
                if len(choices) == 1:
                    membership = choices[0]
                elif len(choices) > 1 and required:
                    raise PermissionDenied("Select an authorized organization using X-Organization-ID.")
        request._authmed_membership = membership
    if membership is None and required:
        raise PermissionDenied("An active organization membership is required.")
    return membership

def get_request_organization(request):
    return get_active_membership(request).organization

def scope_queryset(queryset, organization):
    label = queryset.model._meta.label_lower
    if label == "users.user":
        return queryset.filter(memberships__organization=organization, memberships__is_active=True).distinct()
    path = TENANT_PATHS.get(label)
    return queryset.filter(**{path: organization.pk}) if path else queryset.none()

def object_organization_id(obj):
    path = TENANT_PATHS.get(obj._meta.label_lower)
    if not path:
        return None
    value = obj
    for part in path.split("__"):
        value = getattr(value, part, None)
        if value is None:
            return None
    return value

class TenantQuerysetMixin:
    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.queryset.none()
        qs = scope_queryset(super().get_queryset(), get_request_organization(self.request))
        org_filter = self.request.query_params.get("organization")
        if org_filter is not None:
            if not org_filter.isascii() or not org_filter.isdigit() or len(org_filter) > 18:
                raise ValidationError({"organization": "Expected an organization identifier."})
            path = TENANT_PATHS.get(qs.model._meta.label_lower)
            qs = qs.filter(**{path: int(org_filter)}) if path else qs.none()
        # Preserve existing mobile list filters without global role exceptions.
        for parameter, field in getattr(self, "tenant_filters", {}).items():
            value = self.request.query_params.get(parameter)
            if value:
                if field.endswith("_id") and (not value.isascii() or not value.isdigit() or len(value) > 18):
                    raise ValidationError({parameter: "Expected an identifier."})
                qs = qs.filter(**{field: value})
        return qs
