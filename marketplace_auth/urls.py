"""
URL patterns for the marketplace_auth application.

This module defines the API endpoints for user registration.
"""

from django.urls import path
from .views import registration_view

urlpatterns = [
    path("registration/", registration_view, name="registration"),
]
