import os

from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from ..serializers import GoogleAuthSerializer
from ..models import Usuari

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Auth"],
        summary="Login con Google",
        description=(
            "Verifica un token de Google OAuth2 y devuelve un par de tokens JWT (access + refresh). "
            "Si el usuario no existe, lo crea automáticamente. "
            "Incluye el `google_id` dentro del payload del access token para su uso en endpoints protegidos."
        ),
        request=GoogleAuthSerializer,
        responses={
            200: inline_serializer(
                name="GoogleLoginResponse",
                fields={
                    "user": serializers.EmailField(help_text="Email del usuario autenticado"),
                    "usuari_id": serializers.IntegerField(help_text="ID interno del Usuari"),
                    "picture": serializers.URLField(
                        allow_null=True, help_text="URL de la foto de perfil de Google"
                    ),
                    "access": serializers.CharField(help_text="JWT access token (expira en 5 min por defecto)"),
                    "refresh": serializers.CharField(help_text="JWT refresh token"),
                },
            ),
            400: OpenApiResponse(description="Token de Google inválido o email no verificado"),
        },
    )
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
            google_id = idinfo["sub"]

            user, created = User.objects.get_or_create(
                username=email,
                defaults={"email": email, "first_name": name}
            )

            usuari, _ = Usuari.objects.get_or_create(
                google_id=google_id,
                defaults={
                    "username": email,
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
            refresh['google_id'] = usuari.google_id

            return Response({
                "user": email,
                "usuari_id": usuari.id,
                "picture": picture,
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            })

        except ValueError as e:
            return Response(
                {"error": "Invalid Google token", "detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )