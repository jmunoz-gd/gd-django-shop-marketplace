# marketplace/views.py

import logging
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.http import Http404  # Ensure Http404 is imported
from .models import Product, Bucket, BucketProduct
from .serializers import ProductSerializer, BucketSerializer

logger = logging.getLogger(__name__)

UNEXPECTED_SERVER_ERROR_MSG = "An unexpected server error occurred."


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
            products = products.exclude(categories__id__in=category_ids)
        else:
            products = products.filter(categories__id__in=category_ids)

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
        logger.error(
            f"An unexpected error occurred while processing product list: {e}",
            exc_info=True,
        )
        return Response(
            {"error": UNEXPECTED_SERVER_ERROR_MSG},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def bucket_view(request):
    """
    Shows the current user's bucket state.
    """
    logger.info(f"GET request for bucket received from user {request.user.id}.")
    try:
        user_bucket, _ = Bucket.objects.get_or_create(user=request.user)
        serializer = BucketSerializer(user_bucket)
        logger.info(f"Successfully retrieved bucket for user {request.user.id}.")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(
            (
                f"An unexpected error occurred while fetching bucket for user "
                f"{request.user.id}: {e}"
            ),
            exc_info=True,
        )
        return Response(
            {"error": UNEXPECTED_SERVER_ERROR_MSG},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def add_to_bucket(request):
    product_id = request.data.get("id")
    number = request.data.get("number", 1)

    logger.info(
        (
            f"POST request to add product {product_id} to bucket from user "
            f"{request.user.id}."
        )
    )

    try:
        number = int(number)
        if number <= 0:
            logger.warning(f"Invalid number {number} for adding to bucket.")
            return Response(
                {"error": "Number must be a positive integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except (ValueError, TypeError):
        logger.warning(f"Invalid number format received: {number}.")
        return Response(
            {"error": "Invalid number format."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        product = get_object_or_404(Product, id=product_id)
    except Http404:
        logger.warning(f"Product with ID {product_id} not found.")
        return Response(
            {"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND
        )

    try:
        with transaction.atomic():
            user_bucket, _ = Bucket.objects.get_or_create(user=request.user)
            bucket_product, created = BucketProduct.objects.get_or_create(
                bucket=user_bucket, product=product
            )

            if not created:
                bucket_product.number += number
                bucket_product.save()

        total = sum(
            item.product.price * item.number
            for item in user_bucket.bucketproduct_set.all()
        )
        logger.info(
            f"Product {product_id} added/updated in bucket for user {request.user.id}."
        )
        return Response({"total": f"{total:.2f}"}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while adding to bucket for user "
            f"{request.user.id}: {e}",
            exc_info=True,
        )
        return Response(
            {"error": UNEXPECTED_SERVER_ERROR_MSG},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def bucket_product_detail(request, product_id):
    logger.info(
        f"{request.method} request for product {product_id} in bucket from user "
        f"{request.user.id}."
    )

    # --- FIX: Simplify error handling ---
    try:
        user_bucket, _ = Bucket.objects.get_or_create(user=request.user)
        bucket_product = get_object_or_404(
            BucketProduct, bucket=user_bucket, product__id=product_id
        )
    except Http404:
        logger.warning(
            f"Product {product_id} not found in bucket for user {request.user.id}."
        )
        return Response(
            {"error": "Product not found in bucket."}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(
            (
                f"An unexpected error occurred during initial fetch for product "
                f"{product_id}: {e}"
            ),
            exc_info=True,
        )
        return Response(
            {"error": UNEXPECTED_SERVER_ERROR_MSG},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # All the logic below this point assumes bucket_product exists
    try:
        if request.method == "POST":
            number = request.data.get("number")
            try:
                number = int(number)
                if number <= 0:
                    logger.warning(
                        (
                            f"Invalid number {number} for updating bucket product "
                            f"{product_id}."
                        )
                    )
                    return Response(
                        {"error": "Number must be a positive integer."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                bucket_product.number = number
                bucket_product.save()
            except (ValueError, TypeError):
                logger.warning(
                    (
                        f"Invalid number format received for product {product_id}: "
                        f"{request.data.get('number')}."
                    )
                )
                return Response(
                    {"error": "Invalid number format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif request.method == "DELETE":
            bucket_product.delete()
            logger.info(
                f"Product {product_id} removed from bucket for user {request.user.id}."
            )
            return Response(status=status.HTTP_204_NO_CONTENT)

        total = sum(
            item.product.price * item.number
            for item in user_bucket.bucketproduct_set.all()
        )
        logger.info(
            f"Successfully processed {request.method} request for product {product_id}."
        )
        return Response({"total": f"{total:.2f}"}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(
            (
                f"An unexpected error occurred during {request.method} for product "
                f"{product_id}: {e}"
            ),
            exc_info=True,
        )
        return Response(
            {"error": UNEXPECTED_SERVER_ERROR_MSG},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
