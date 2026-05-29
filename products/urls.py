from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ProductReferenceImageViewSet, DatasetGroupViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet)
router.register(r"product-reference-images", ProductReferenceImageViewSet, basename="product-reference-image")
router.register(r"dataset-groups", DatasetGroupViewSet, basename="dataset-group")

urlpatterns = [path("", include(router.urls))]
