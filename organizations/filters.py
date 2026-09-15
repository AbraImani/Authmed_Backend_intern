from django_filters.rest_framework import DjangoFilterBackend
from .tenancy import get_request_organization, scope_queryset

class TenantFilterBackend(DjangoFilterBackend):
    """Also scope filter choices and browsable-API HTML, not just result rows."""
    def get_filterset(self, request, queryset, view):
        filterset = super().get_filterset(request, queryset, view)
        if filterset is not None and not getattr(view, "swagger_fake_view", False):
            organization = get_request_organization(request)
            for item in filterset.filters.values():
                field = item.field
                if getattr(field, "queryset", None) is not None:
                    field.queryset = scope_queryset(field.queryset, organization)
        return filterset
