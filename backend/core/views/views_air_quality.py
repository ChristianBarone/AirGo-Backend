from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ..services.air_quality import get_air_quality_near


class AirQualityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            lat = float(request.GET.get("lat"))
            lon = float(request.GET.get("lon"))
            radio = float(request.GET.get("radio", 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "Los parámetros lat, lon y radio deben ser numéricos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pollution_points = get_air_quality_near(lat, lon, radio)
            return Response(pollution_points, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error obteniendo calidad del aire: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )