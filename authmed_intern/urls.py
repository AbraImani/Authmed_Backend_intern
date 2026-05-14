from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("users.urls")),
    path("api/", include("organizations.urls")),
    path("api/", include("suppliers.urls")),
    path("api/", include("products.urls")),
    path("api/", include("inspections.urls")),
    path("api/", include("audits.urls")),
    path("api/auth/", include("authmed_intern.urls_auth")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
