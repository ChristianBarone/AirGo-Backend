from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers import GoogleAuthSerializer


GOOGLE_CLIENT_ID = "500956123135-fidfq8ecmd60e6pak1e4ds5r1ai9sojp.apps.googleusercontent.com"


class GoogleLoginView(APIView):

    ## Verificación de la request con Google
    # Generación del usuario si no existe, login si ya existe (avisar si no quereis que el default sea "name")
    # Gestión de errores con el token
    def post(self, request):

        serializer = GoogleAuthSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        if not idinfo.get("email_verified", False):
            return Response(
                {"error": "Email not verified"},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = serializer.validated_data["token"]

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                GOOGLE_CLIENT_ID
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

            refresh = RefreshToken.for_user(user)

            return Response({
                "user": email,
                "picture": picture,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            })

        except ValueError:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_400_BAD_REQUEST
            )