# marketplace/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path("products/", views.product_list, name="product-list"),
    path("bucket/", views.bucket_view, name="bucket-view"),
    path("bucket/add/", views.add_to_bucket, name="bucket-add"),
    path(
        "bucket/<int:product_id>/update/",
        views.bucket_product_detail,
        name="bucket-update",
    ),
    path("bucket/<int:product_id>/", views.bucket_product_detail, name="bucket-delete"),
]
