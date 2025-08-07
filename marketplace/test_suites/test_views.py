# marketplace/test_suites/test_views.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from marketplace.models import Category, Product


class ProductListViewTest(APITestCase):
    """
    Test suite for the product_list API view.
    """

    def setUp(self):
        """
        Set up the necessary data for all tests.
        """
        # Create categories for testing filtering
        self.category_electronics = Category.objects.create(name="Electronics")
        self.category_clothing = Category.objects.create(name="Clothing")
        self.category_books = Category.objects.create(name="Books")

        # Create products linked to different categories for testing
        self.product_a = Product.objects.create(
            name="Laptop",
            price="1200.00",
            description="Powerful laptop for professionals.",
        )
        self.product_a.categories.set([self.category_electronics])

        self.product_b = Product.objects.create(
            name="Smartphone", price="800.00", description="Latest smartphone model."
        )
        self.product_b.categories.set([self.category_electronics])

        self.product_c = Product.objects.create(
            name="T-Shirt", price="20.00", description="Comfortable cotton t-shirt."
        )
        self.product_c.categories.set([self.category_clothing])

        self.product_d = Product.objects.create(
            name="Fiction Book", price="30.00", description="An exciting fiction novel."
        )
        self.product_d.categories.set([self.category_books])

        self.url = reverse("product-list")

    # --- Test API Contract ---

    def test_api_contract_returns_expected_format(self):
        """
        Ensure the view returns data in the expected JSON format.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIsInstance(response.data["results"], list)

        if len(response.data["results"]) > 0:
            product_data = response.data["results"][0]
            self.assertIn("id", product_data)
            self.assertIn("name", product_data)
            self.assertIn("description", product_data)
            self.assertIn("categories", product_data)  # <-- Check for 'categories'
            self.assertIsInstance(product_data["categories"], list)
            self.assertIsInstance(product_data["categories"][0], dict)
            self.assertIn("id", product_data["categories"][0])
            self.assertIn("name", product_data["categories"][0])

    # --- Test Filtering ---

    def test_filter_by_single_category(self):
        """
        Test that filtering by a single category ID returns only relevant products.
        """
        response = self.client.get(self.url, {"category": self.category_electronics.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        product_names = [p["name"] for p in response.data["results"]]
        self.assertIn("Laptop", product_names)
        self.assertIn("Smartphone", product_names)
        self.assertNotIn("T-Shirt", product_names)

    def test_filter_by_multiple_categories(self):
        """
        Test that filtering by multiple category IDs returns products from all
        specified categories.
        """
        category_ids = f"{self.category_electronics.id},{self.category_clothing.id}"
        response = self.client.get(self.url, {"category": category_ids})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_exclude_category_with_minus_prefix(self):
        """
        Test that using a '-' prefix excludes a specified category.
        """
        response = self.client.get(
            self.url, {"category": f"-{self.category_electronics.id}"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        product_names = [p["name"] for p in response.data["results"]]
        self.assertIn("T-Shirt", product_names)
        self.assertIn("Fiction Book", product_names)

    def test_invalid_category_id_returns_bad_request(self):
        """
        Test that an invalid category ID format returns a 400 Bad Request.
        """
        response = self.client.get(self.url, {"category": "invalid-id"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- Test Sorting ---

    def test_sort_by_name_ascending(self):
        """
        Test that sorting by a field in ascending order works correctly.
        """
        response = self.client.get(self.url, {"sort": "name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product_names = [p["name"] for p in response.data["results"]]
        self.assertEqual(
            product_names, ["Fiction Book", "Laptop", "Smartphone", "T-Shirt"]
        )

    def test_sort_by_name_descending(self):
        """
        Test that sorting by a field with a '-' prefix sorts in descending order.
        """
        response = self.client.get(self.url, {"sort": "-name"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        product_names = [p["name"] for p in response.data["results"]]
        self.assertEqual(
            product_names, ["T-Shirt", "Smartphone", "Laptop", "Fiction Book"]
        )

    def test_invalid_sort_field_returns_bad_request(self):
        """
        Test that sorting by a field that does not exist returns a 400 Bad Request.
        """
        response = self.client.get(self.url, {"sort": "invalid-field"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid sort field", response.data["error"])
