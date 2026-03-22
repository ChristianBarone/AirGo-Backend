import os

from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers import GoogleAuthSerializer
from ..models import Usuari

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")


class GoogleLoginView(APIView):

    def post(self, request):

        serializer = GoogleAuthSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        token = serializer.validated_data["token"]

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                GOOGLE_CLIENT_ID
            )

            if not idinfo.get("email_verified", False):
                return Response(
                    {"error": "Email not verified"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            email = idinfo["email"]
            name = idinfo.get("name", "")
            picture = idinfo.get("picture")

            user, created = User.objects.get_or_create(
                username=email,
                defaults={
                    "email": email,
                    "first_name": name
                }
            )

            Usuari.objects.get_or_create(
                username=email,
                defaults={
                    "punts": 0,
                    "teBici": False,
                    "pes": 0.0,
                    "altura": 0.0,
                    "ratxa": 0,
                    "limitRutes": 0,
                    "titol": "",
                }
            )

            refresh = RefreshToken.for_user(user)

            return Response({
                "user": email,
                "picture": picture,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            })

        except ValueError as e:
            return Response(
                {"error": "Invalid Google token", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )