# marketplace/test_suites/test_auth.py

from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User


class UserRegistrationTest(APITestCase):
    def setUp(self):
        self.url = reverse("registration")
        self.valid_payload = {
            "first_name": "John",
            "second_name": "Doe",
            "email": "john.doe@example.com",
            "password": "strongpassword123",
        }
        self.invalid_payload_missing_field = {
            "first_name": "Jane",
            "second_name": "Doe",
            "email": "jane.doe@example.com",
        }

    def test_post_registration_api_contract_success(self):
        """
        Ensure the registration view correctly creates a user and returns a token.
        """
        response = self.client.post(self.url, self.valid_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertEqual(User.objects.count(), 1)
        self.assertTrue(User.objects.filter(email="john.doe@example.com").exists())

    def test_post_registration_api_contract_failure_invalid_data(self):
        """
        Ensure the registration view returns a 400 for invalid data.
        """
        response = self.client.post(
            self.url, self.invalid_payload_missing_field, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertEqual(User.objects.count(), 0)
