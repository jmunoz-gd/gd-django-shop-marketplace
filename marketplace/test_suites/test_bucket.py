# marketplace/test_suites/test_bucket.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from marketplace.models import Category, Product, Bucket, BucketProduct
from decimal import Decimal


class BucketApiTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser@example.com",
            email="testuser@example.com",
            password="password123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)

        self.bucket = Bucket.objects.create(user=self.user)

        self.category = Category.objects.create(name="Electronics")
        self.product1 = Product.objects.create(name="Laptop", price=Decimal("1200.00"))
        self.product1.categories.set([self.category])
        self.product2 = Product.objects.create(
            name="Smartphone", price=Decimal("800.00")
        )
        self.product2.categories.set([self.category])

        self.bucket_view_url = reverse("bucket-view")
        self.bucket_add_url = reverse("bucket-add")

    # --- GET /v1/marketplace/bucket ---

    def test_get_bucket_api_contract(self):
        """
        Ensure the GET bucket view returns the correct format and an initial total of 0.
        """
        response = self.client.get(self.bucket_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total", response.data)
        self.assertIn("products", response.data)
        self.assertEqual(response.data["total"], "0.00")
        self.assertEqual(len(response.data["products"]), 0)

    def test_get_bucket_calculates_total_correctly(self):
        """
        Ensure the total is calculated correctly after adding products.
        """
        BucketProduct.objects.create(
            bucket=self.bucket, product=self.product1, number=2
        )
        BucketProduct.objects.create(
            bucket=self.bucket, product=self.product2, number=1
        )

        response = self.client.get(self.bucket_view_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        expected_total = (2 * self.product1.price) + (1 * self.product2.price)
        self.assertEqual(Decimal(response.data["total"]), expected_total)

    # --- POST /v1/marketplace/bucket/add ---

    def test_post_add_to_bucket_creates_new_item(self):
        """
        Ensure adding a product creates a new item and returns the correct total.
        """
        payload = {"id": self.product1.id, "number": 2}
        response = self.client.post(self.bucket_add_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("total", response.data)
        self.assertEqual(BucketProduct.objects.count(), 1)

    def test_post_add_to_bucket_updates_existing_item(self):
        """
        Ensure adding the same product twice updates the quantity.
        """
        payload = {"id": self.product1.id, "number": 1}
        self.client.post(self.bucket_add_url, payload, format="json")

        payload = {"id": self.product1.id, "number": 3}
        response = self.client.post(self.bucket_add_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BucketProduct.objects.get(product=self.product1).number, 4)

    def test_post_add_to_bucket_invalid_data(self):
        """
        Ensure invalid data returns a 400 Bad Request.
        """
        payload = {"id": 999, "number": -1}  # Non-existent product and invalid number
        response = self.client.post(self.bucket_add_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- POST /v1/marketplace/bucket/{product_id}/update ---

    def test_post_update_product_in_bucket_success(self):
        """
        Ensure updating a product's number is successful.
        """
        BucketProduct.objects.create(
            bucket=self.user.bucket, product=self.product1, number=1
        )
        update_url = reverse("bucket-update", kwargs={"product_id": self.product1.id})
        response = self.client.post(update_url, {"number": 5}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BucketProduct.objects.get(product=self.product1).number, 5)

    def test_post_update_product_not_found(self):
        """
        Ensure updating a product not in the bucket returns a 404.
        """
        update_url = reverse("bucket-update", kwargs={"product_id": self.product2.id})
        response = self.client.post(update_url, {"number": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- DELETE /v1/marketplace/bucket/{product_id} ---

    def test_delete_product_from_bucket_success(self):
        """
        Ensure deleting a product returns a 204 No Content.
        """
        BucketProduct.objects.create(
            bucket=self.user.bucket, product=self.product1, number=1
        )
        delete_url = reverse("bucket-delete", kwargs={"product_id": self.product1.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(BucketProduct.objects.filter(product=self.product1).exists())

    def test_delete_product_not_found(self):
        """
        Ensure deleting a product not in the bucket returns a 404.
        """
        delete_url = reverse("bucket-delete", kwargs={"product_id": self.product2.id})
        response = self.client.delete(delete_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
