from rest_framework import permissions


class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and getattr(request.user, "role", None) == "admin")


class IsAdminOrReviewer(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, "role", None) in {"admin", "reviewer"}
        )


class IsOrgMember(permissions.BasePermission):
    """Allow access only to users belonging to the same organization or staff."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Admin users are allowed to inspect any object regardless of organization.
        if user.is_superuser or user.role == "admin":
            return True
        # If object has organization attribute, compare
        org = getattr(obj, "organization", None)
        if org is None:
            return True
        # For org-scoped resources, the object's organization must match the caller's organization.
        return getattr(user, "organization", None) == org

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
