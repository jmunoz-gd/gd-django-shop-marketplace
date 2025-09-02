"""
API views for user authentication and registration.
"""

import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import UserRegistrationSerializer

logger = logging.getLogger(__name__)


@api_view(["POST"])
def registration_view(request):
    """
    Handles user registration and returns an authentication token.

    A new User is created with the provided details, and an authentication
    token is generated for the new user.
    """
    logger.info("POST request received for user registration.")
    serializer = UserRegistrationSerializer(data=request.data)

    try:
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            logger.info(f"New user registered with email: {user.email}.")
            return Response(
                {"token": token.key}, status=status.HTTP_201_CREATED
            )

        logger.warning(
            f"Invalid registration data received: {serializer.errors}."
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during registration: {e}",
            exc_info=True,
        )
        return Response(
            {"error": "An unexpected server error occurred."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
