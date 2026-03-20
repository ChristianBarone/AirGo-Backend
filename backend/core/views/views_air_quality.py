from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..services.air_quality import get_air_quality_near

class AirQualityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat", 41.385))
            lon = float(request.query_params.get("lon", 2.173))
        except ValueError:
            return Response({"error": "lat y lon deben ser números"}, status=400)

        data = get_air_quality_near(lat, lon)
        return Response(data)