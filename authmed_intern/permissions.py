from rest_framework import permissions
from organizations.roles import CAPABILITIES
from organizations.tenancy import get_active_membership, object_organization_id

class TenantPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated or not request.user.is_active:
            return False
        membership = get_active_membership(request)
        if hasattr(view, "action_map") and getattr(view, "action", None) is None:
            return True  # Let DRF return 405 for unsupported methods after membership validation.
        capability = getattr(view, "read_capability", "read") if request.method in permissions.SAFE_METHODS else getattr(view, "write_capability", None)
        return capability in CAPABILITIES.get(membership.role, ())

    def has_object_permission(self, request, view, obj):
        membership = get_active_membership(request)
        if obj._meta.label_lower == "users.user":
            return obj.memberships.filter(organization_id=membership.organization_id, is_active=True).exists()
        return object_organization_id(obj) == membership.organization_id

# Kept as compatibility imports, now contextual and fail-closed.
IsOrgMember = TenantPermission
IsAdminRole = TenantPermission
IsAdminOrReviewer = TenantPermission
