from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


class Category(models.Model):
    """
    Represents a product category, which can be part of a hierarchical structure.
    """

    name = models.CharField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="children",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Represents a single product available in the marketplace.
    """

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    categories = models.ManyToManyField(
        Category, through="ProductCategory", related_name="products"
    )

    available_items = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def get_best_discount(self, user):
        """Calculates the single best discount for the product based on active sales."""
        now = timezone.now()
        applicable_sales = self.sales.filter(
            start_date__lte=now,
            end_date__gte=now,
        )

        if user and user.is_authenticated:
            user_groups = user.groups.all()
            applicable_sales = applicable_sales.filter(
                models.Q(allowed_users=user)
                | models.Q(allowed_groups__in=user_groups)
                | models.Q(
                    allowed_users__isnull=True, allowed_groups__isnull=True
                )
            )
        else:
            # For anonymous users, only consider public sales
            applicable_sales = applicable_sales.filter(
                allowed_users__isnull=True, allowed_groups__isnull=True
            )

        if applicable_sales.exists():
            return max(sale.discount for sale in applicable_sales)
        return Decimal("0.00")

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    """
    Intermediate model to manage the many-to-many relationship between products
    and categories.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("product", "category")


class Bucket(models.Model):
    """
    Represents a user's shopping bucket, storing products they intend to purchase.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(
        Product, through="BucketProduct", related_name="buckets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bucket for {self.user.username}"


class BucketProduct(models.Model):
    """
    Represents a specific product within a user's bucket, including the quantity.
    """

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    bucket = models.ForeignKey(Bucket, on_delete=models.CASCADE)
    number = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "bucket")

    def __str__(self):
        return (
            f"{self.number} of {self.product.name} in "
            f"{self.bucket.user.username}'s bucket"
        )


class Sale(models.Model):
    """
    Represents a sale event with a discount.

    The discount can be applied to specific products or categories.
    """

    name = models.CharField(max_length=255)
    announcement_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    was_announced = models.BooleanField(default=False)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    products = models.ManyToManyField(Product, related_name="sales", blank=True)
    categories = models.ManyToManyField(
        Category, related_name="sales", blank=True
    )
    allowed_users = models.ManyToManyField(
        User, related_name="closed_sales", blank=True
    )
    allowed_groups = models.ManyToManyField(
        Group, related_name="closed_sales", blank=True
    )

    def is_closed_sale(self):
        """Checks if the sale is a closed sale (only for specific users/groups)."""
        return self.allowed_users.exists() or self.allowed_groups.exists()

    def __str__(self):
        return self.name


class Order(models.Model):
    """
    Represents a finalized order created from a user's bucket.
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0.00")
    )

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"


class OrderItem(models.Model):
    """
    Represents a single product within an Order,
    capturing its state at the time of purchase.
    """

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items"
    )
    product = models.ForeignKey(Product, on_delete=models.DO_NOTHING)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("0.00")
    )
    number = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.number} of {self.name} for Order {self.order.id}"
