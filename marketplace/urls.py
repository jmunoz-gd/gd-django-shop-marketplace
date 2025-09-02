"""
URL patterns for the marketplace application.
These patterns define the V1 API endpoints for product and bucket management.
"""

from django.urls import path
from . import views

urlpatterns = [
    # V1 API endpoints for products, bucket, and bucket management.
    path("products/", views.product_list, name="product-list"),
    path("bucket/", views.bucket_view, name="bucket-view"),
    path("bucket/add/", views.add_to_bucket, name="bucket-add"),
    path(
        "bucket/<int:product_id>/update/",
        views.bucket_product_detail,
        name="bucket-update",
    ),
    path(
        "bucket/<int:product_id>/",
        views.bucket_product_detail,
        name="bucket-delete",
    ),
]
