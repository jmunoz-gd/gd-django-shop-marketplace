# marketplace/serializers.py

from rest_framework import serializers
from .models import Category, Product, Bucket, BucketProduct


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

    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "categories"]


class BucketProductSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="product.name", read_only=True)
    id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = BucketProduct
        fields = ["id", "name", "number"]


class BucketSerializer(serializers.ModelSerializer):
    products = BucketProductSerializer(source="bucketproduct_set", many=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Bucket
        fields = ["total", "products"]

    def get_total(self, obj):
        total = sum(
            item.product.price * item.number for item in obj.bucketproduct_set.all()
        )
        return f"{total:.2f}"
