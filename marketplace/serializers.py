# marketplace/serializers.py

from decimal import Decimal
from rest_framework import serializers
from .models import Category, Order, OrderItem, Product, Bucket, BucketProduct


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
        fields = ["id", "name", "description", "categories", "available_items"]


class V2ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for the Product model in the v2 API, including price and discount.

    This serializer calculates and displays the final discounted price and
    the discount percentage.
    """

    categories = CategorySerializer(many=True, read_only=True)
    discounted_price = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "price",
            "categories",
            "discounted_price",
            "discount",
            "available_items",
        ]

    def get_discount(self, obj):
        request = self.context.get("request")
        if request:
            discount = obj.get_best_discount(request.user)
            return f"{discount:.2f}"
        return "0.00"

    def get_discounted_price(self, obj):
        request = self.context.get("request")
        if request:
            discount = obj.get_best_discount(request.user)
            discounted_price = obj.price * (Decimal("1.00") - discount)
            return f"{discounted_price:.2f}"
        return f"{obj.price:.2f}"


class BucketProductSerializer(serializers.ModelSerializer):
    """
    Serializer for a product item within a user's shopping bucket.
    """

    name = serializers.CharField(source="product.name", read_only=True)
    id = serializers.IntegerField(source="product.id", read_only=True)

    class Meta:
        model = BucketProduct
        fields = ["id", "name", "number"]


class BucketSerializer(serializers.ModelSerializer):
    """
    Serializer for a user's shopping bucket.

    It includes a nested representation of all products in the bucket and
    calculates the total price.
    """

    products = BucketProductSerializer(source="bucketproduct_set", many=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Bucket
        fields = ["total", "products"]

    def get_total(self, obj):
        total = sum(
            item.product.price * item.number
            for item in obj.bucketproduct_set.all()
        )
        return f"{total:.2f}"


class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for a product item within an Order.

    This serializer captures the state of a product at the time of purchase,
    including its price and discount.
    """

    class Meta:
        model = OrderItem
        fields = ["product", "name", "price", "discount", "number"]


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for a finalized Order.

    It includes a nested representation of all OrderItems and the order total.
    """

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ["id", "user", "created_at", "total", "items"]
