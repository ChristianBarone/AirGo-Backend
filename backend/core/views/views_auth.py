from google.oauth2 import id_token
from google.auth.transport import requests

from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from ..serializers import GoogleAuthSerializer

GOOGLE_CLIENT_ID = "278712094443-2fl5uln8283bmf5ca83ou3eke9r2bu1t.apps.googleusercontent.com"


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

            # ✅ Ahora idinfo ya existe cuando hacemos el check
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