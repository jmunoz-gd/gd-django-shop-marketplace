"""
Serializers for user authentication and registration.
"""

from django.contrib.auth.models import User
from rest_framework import serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for handling user registration.

    It creates a new User instance and automatically generates a username from the
    email. The password and second_name fields are write-only to prevent them from
    being exposed in the API response.
    """

    password = serializers.CharField(write_only=True)
    second_name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["first_name", "second_name", "email", "password"]
        extra_kwargs = {
            "first_name": {"required": True},
            "email": {"required": True},
            "password": {"required": True},
        }

    def create(self, validated_data):
        """
        Create and return a new `User` instance, given the validated data.
        """
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["second_name"],
        )
        return user
