# marketplace/admin.py
"""
Django Admin configuration for the marketplace application.

This module defines how models are displayed and managed in the Django admin interface.
It includes custom list views, search fields, and filters for improved usability.
"""

from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductCategory,
    Bucket,
    BucketProduct,
    Sale,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Category model.
    """

    list_display = ("name", "parent", "created_at", "modified_at")
    search_fields = ("name",)
    list_filter = ("created_at", "modified_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Product model.

    Includes a custom method to display associated categories.
    """

    list_display = (
        "name",
        "price",
        "display_categories",
        "created_at",
        "modified_at",
    )
    search_fields = ("name", "description")
    list_filter = ("categories", "created_at", "modified_at")

    def display_categories(self, obj):
        """
        Custom method to display the categories of a product in the list view.
        """
        return ", ".join([category.name for category in obj.categories.all()])

    display_categories.short_description = "Categories"


@admin.register(Bucket)
class BucketAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Bucket model.
    """

    list_display = ("user", "created_at")


@admin.register(BucketProduct)
class BucketProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for the BucketProduct model.
    """

    list_display = ("product", "bucket", "number")


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for the ProductCategory model.
    """

    list_display = ("product", "category")


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Sale model.

    Includes horizontal filters for many-to-many relationships.
    """

    list_display = (
        "name",
        "announcement_date",
        "start_date",
        "end_date",
        "was_announced",
        "discount",
    )
    list_filter = (
        "announcement_date",
        "start_date",
        "end_date",
        "was_announced",
    )
    search_fields = ("name",)
    filter_horizontal = ("products", "categories")
