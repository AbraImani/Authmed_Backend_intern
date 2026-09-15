from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductReferenceImageViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"product-reference-images", ProductReferenceImageViewSet, basename="product-reference-image")

urlpatterns = [path("", include(router.urls))]
