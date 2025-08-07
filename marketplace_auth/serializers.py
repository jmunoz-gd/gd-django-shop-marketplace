# marketplace_auth/serializers.py

from django.contrib.auth.models import User
from rest_framework import serializers


class UserRegistrationSerializer(serializers.ModelSerializer):
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
        user = User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["second_name"],
        )
        return user
