# marketplace/admin.py
from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "created_at", "modified_at")
    search_fields = ("name",)
    list_filter = ("created_at", "modified_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "category", "created_at", "modified_at")
    search_fields = ("name", "description")
    list_filter = ("category", "created_at", "modified_at")
