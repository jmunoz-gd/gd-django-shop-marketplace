"""
URL configuration for shop project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from marketplace.views import BucketProductViewSet, ProductListV2, create_order


# DRF router for the new ViewSet
router_v2 = routers.DefaultRouter()
router_v2.register(r"bucket", BucketProductViewSet, basename="bucket")


urlpatterns = [
    path("admin/", admin.site.urls),
    # V1 API Endpoints
    path("v1/marketplace/", include("marketplace.urls")),
    path("v1/marketplace_auth/", include("marketplace_auth.urls")),
    # V2 API Endpoints
    path("v2/marketplace/", include(router_v2.urls)),
    path(
        "v2/marketplace/products/",
        ProductListV2.as_view(),
        name="product-list-v2",
    ),
    path("v2/marketplace/create-order/", create_order, name="create-order"),
]
