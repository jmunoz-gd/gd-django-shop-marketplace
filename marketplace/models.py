# marketplace/models.py
from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
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
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)

    categories = models.ManyToManyField(
        Category, through="ProductCategory", related_name="products"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("product", "category")


class Bucket(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(
        Product, through="BucketProduct", related_name="buckets"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Bucket for {self.user.username}"


class BucketProduct(models.Model):
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
    name = models.CharField(max_length=255)
    announcement_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    was_announced = models.BooleanField(default=False)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    products = models.ManyToManyField(Product, related_name="sales", blank=True)
    categories = models.ManyToManyField(Category, related_name="sales", blank=True)

    def __str__(self):
        return self.name
