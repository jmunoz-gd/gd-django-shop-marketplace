# marketplace/serializers.py

from rest_framework import serializers
from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for the Category model to be nested within Product.
    """

    class Meta:
        model = Category
        fields = ["id", "name"]


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model, including a nested Category representation.
    """

    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "category"]
