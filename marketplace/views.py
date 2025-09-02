# marketplace/views.py

from decimal import Decimal
import logging
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, generics, permissions, viewsets
from django.db import transaction
from django.http import Http404
from .models import Order, OrderItem, Product, Bucket, BucketProduct
from .serializers import (
    OrderSerializer,
    ProductSerializer,
    BucketSerializer,
    V2ProductSerializer,
    BucketProductSerializer,
)
from django.db.models import F
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

UNEXPECTED_SERVER_ERROR_MSG = "An unexpected server error occurred."
NUMBER_MUST_BE_POSITIVE_ERROR_MSG = "Number must be a positive integer."
PRODUCT_NOT_FOUND_IN_BUCKET_ERROR_MSG = "Product not found in bucket."


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
            logger.warning(
                f"Invalid category ID format received: {category_param}"
            )
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
    List all products with optional filtering, sorting, and sale discounts.
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

        # Apply discounts
        serialized_data = []
        for product in products:
            serializer = ProductSerializer(product)
            product_data = serializer.data
            discount = product.get_best_discount(request.user)
            if discount > 0:
                discounted_price = product.price * (Decimal("1.00") - discount)
                product_data["price"] = f"{discounted_price:.2f}"
                product_data["discount"] = f"{discount:.2f}"
            else:
                product_data["price"] = f"{product.price:.2f}"
            serialized_data.append(product_data)

        logger.info("Successfully processed product list request.")
        return Response({"results": serialized_data}, status=status.HTTP_200_OK)
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
        logger.info(
            f"Successfully retrieved bucket for user {request.user.id}."
        )
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
                {"error": NUMBER_MUST_BE_POSITIVE_ERROR_MSG},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid number format received: {number}. Error: {e}")
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
            {"error": PRODUCT_NOT_FOUND_IN_BUCKET_ERROR_MSG},
            status=status.HTTP_404_NOT_FOUND,
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
                        {"error": NUMBER_MUST_BE_POSITIVE_ERROR_MSG},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                bucket_product.number = number
                bucket_product.save()
            except (ValueError, TypeError) as e:
                logger.warning(
                    (
                        f"Invalid number format received for product {product_id}: "
                        f"{request.data.get('number')}. Error: {e}"
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


class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class for consistent API responses.
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ProductListV2(generics.ListAPIView):
    """
    A class-based view for the V2 product list endpoint, with filtering,
    sorting, and pagination.
    """

    queryset = Product.objects.all()
    serializer_class = V2ProductSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = _get_filtered_products(self.request, queryset)
        if isinstance(queryset, Response):
            return queryset
        queryset = _get_sorted_products(self.request, queryset)
        if isinstance(queryset, Response):
            return queryset
        return queryset


class BucketProductViewSet(viewsets.ModelViewSet):
    """
    A viewset for handling all CRUD operations on a user's bucket products.

    This replaces the old function-based views for the V1 API.
    """

    queryset = BucketProduct.objects.all()
    serializer_class = BucketProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_bucket, _ = Bucket.objects.get_or_create(user=self.request.user)
        return user_bucket.bucketproduct_set.all()

    def create(self, request, *args, **kwargs):
        product_id = request.data.get("id")
        number = request.data.get("number", 1)

        try:
            number = int(number)
            if number <= 0:
                return Response(
                    {"error": NUMBER_MUST_BE_POSITIVE_ERROR_MSG},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid number format: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = get_object_or_404(Product, id=product_id)
        except Http404:
            return Response(
                {"error": "Product not found."},
                status=status.HTTP_404_NOT_FOUND,
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
            return Response(
                {"total": f"{total:.2f}"}, status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected server error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def update(self, request, *args, **kwargs):
        product_id = self.kwargs.get("pk")
        try:
            number = int(request.data.get("number"))
            if number <= 0:
                return Response(
                    {"error": NUMBER_MUST_BE_POSITIVE_ERROR_MSG},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except (ValueError, TypeError) as e:
            return Response(
                {"error": f"Invalid number format: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                user_bucket, _ = Bucket.objects.get_or_create(user=request.user)
                bucket_product = get_object_or_404(
                    BucketProduct, bucket=user_bucket, product__id=product_id
                )
                product = bucket_product.product

                if number > product.available_items:
                    return Response(
                        {
                            "error": (
                                f"Only {product.available_items} items available "
                                "for this product."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                bucket_product.number = number
                bucket_product.save()

            total = sum(
                item.product.price * item.number
                for item in user_bucket.bucketproduct_set.all()
            )
            return Response(
                {"total": f"{total:.2f}"}, status=status.HTTP_200_OK
            )
        except Http404:
            return Response(
                {"error": PRODUCT_NOT_FOUND_IN_BUCKET_ERROR_MSG},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected server error occurred: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        product_id = self.kwargs.get("pk")
        try:
            user_bucket, _ = Bucket.objects.get_or_create(user=request.user)
            bucket_product = get_object_or_404(
                BucketProduct, bucket=user_bucket, product__id=product_id
            )
            bucket_product.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Http404:
            return Response(
                {"error": PRODUCT_NOT_FOUND_IN_BUCKET_ERROR_MSG},
                status=status.HTTP_404_NOT_FOUND,
            )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_order(request):
    """
    Creates an order from the user's bucket, empties the bucket,
    and updates product availability.
    """
    try:
        user_bucket = Bucket.objects.select_for_update().get(user=request.user)
    except Bucket.DoesNotExist:
        return Response(
            {"error": "User does not have a bucket."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    bucket_products = BucketProduct.objects.filter(
        bucket=user_bucket
    ).select_related("product")
    if not bucket_products.exists():
        return Response(
            {"error": "Bucket is empty."}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            # Check for sufficient inventory
            for item in bucket_products:
                product = item.product
                if item.number > product.available_items:
                    return Response(
                        {
                            "error": (
                                f"Not enough stock for product '{product.name}'. "
                                f"Only {product.available_items} available."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Create the order
            order = Order.objects.create(user=request.user)
            order_total = Decimal("0.00")
            order_items = []

            for item in bucket_products:
                product = item.product
                discount = product.get_best_discount(request.user)
                final_price = product.price * (Decimal("1.00") - discount)

                order_item = OrderItem(
                    order=order,
                    product=product,
                    name=product.name,
                    price=final_price,
                    discount=discount,
                    number=item.number,
                )
                order_items.append(order_item)
                order_total += final_price * item.number

                # Decrease available items
                product.available_items = F("available_items") - item.number
                product.save()

            OrderItem.objects.bulk_create(order_items)
            order.total = order_total
            order.save()

            # Clear the bucket
            bucket_products.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during order creation: {e}",
            exc_info=True,
        )
        return Response(
            {"error": UNEXPECTED_SERVER_ERROR_MSG},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
