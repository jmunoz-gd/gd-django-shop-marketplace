# marketplace/views.py

import logging

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Product
from .serializers import ProductSerializer

logger = logging.getLogger(__name__)


def _get_filtered_products(request, products):
    """
    Handles the 'category' GET parameter for filtering products.
    Returns the filtered queryset or a bad request response.
    """
    category_param = request.query_params.get("category")
    if not category_param:
        return products

    exclude_categories = category_param.startswith("-")
    if exclude_categories:
        category_param = category_param[1:]

    category_ids = []
    for cid_str in category_param.split(","):
        try:
            cid = int(cid_str.strip())
            category_ids.append(cid)
        except (ValueError, TypeError):
            logger.warning(f"Invalid category ID format received: {category_param}")
            return Response(
                {"error": "Invalid category ID format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    if category_ids:
        if exclude_categories:
            products = products.exclude(category__id__in=category_ids)
        else:
            products = products.filter(category__id__in=category_ids)

    return products


def _get_sorted_products(request, products):
    sort_param = request.query_params.get("sort")
    if not sort_param:
        return products

    sort_field = sort_param
    if sort_field.startswith("-"):
        sort_field = sort_field[1:]

    if not hasattr(Product, sort_field):
        logger.warning(f"Invalid sort field received: {sort_param}")
        return Response(
            {"error": f"Invalid sort field: {sort_param}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    products = products.order_by(sort_param)
    return products


@api_view(["GET"])
def product_list(request):
    """
    List all products with optional filtering and sorting.
    """
    logger.info("GET request received for product list.")

    try:
        products = Product.objects.all()

        products = _get_filtered_products(request, products)
        if isinstance(products, Response):
            return products

        products = _get_sorted_products(request, products)
        if isinstance(products, Response):
            return products

        serializer = ProductSerializer(products, many=True)
        logger.info("Successfully processed product list request.")
        return Response({"results": serializer.data}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        return Response(
            {"error": "An unexpected server error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
