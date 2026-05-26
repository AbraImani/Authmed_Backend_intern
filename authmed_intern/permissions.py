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
        if user.is_superuser or user.role == "admin":
            return True
        # If object has organization attribute, compare
        org = getattr(obj, "organization", None)
        if org is None:
            return True
        return getattr(user, "organization", None) == org

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
