from rest_framework import serializers
from .models import ProductReference


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductReference
        fields = ["id", "organization", "name", "sku", "description", "created_at"]
