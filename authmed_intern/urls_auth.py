from django.conf import settings
from rest_framework.exceptions import NotFound
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

class DevelopmentOnlyMixin:
    def initial(self, request, *args, **kwargs):
        if settings.AUTHMED_API_AUTH_MODE != "legacy_jwt":
            raise NotFound()
        return super().initial(request, *args, **kwargs)

class LegacyTokenView(DevelopmentOnlyMixin, TokenObtainPairView):
    pass

class LegacyRefreshView(DevelopmentOnlyMixin, TokenRefreshView):
    pass

urlpatterns = [
    # JWT token endpoints
    path("token/", LegacyTokenView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", LegacyRefreshView.as_view(), name="token_refresh"),
]
