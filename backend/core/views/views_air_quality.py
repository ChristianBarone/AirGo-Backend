from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..services.air_quality import get_air_quality_near
from ..models import AirQualityHistoric
from datetime import datetime

class AirQualityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat", 41.385))
            lon = float(request.query_params.get("lon", 2.173))
        except ValueError:
            return Response({"error": "lat y lon deben ser números"}, status=400)

        try:
            data = get_air_quality_near(lat, lon)
        except Exception:
            now = datetime.now()
            historic = AirQualityHistoric.objects.filter(
                day_of_week=now.weekday(),
                hora=now.hour
            ).first()
            data = {"aqi": historic.aqi} if historic else {"error": "Sin datos disponibles"}

        return Response(data)