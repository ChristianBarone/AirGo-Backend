from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..services.bicing import get_bicing_near

class BicingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat", 41.385))
            lon = float(request.query_params.get("lon", 2.173))
            radio = float(request.query_params.get("radio", 5))
        except ValueError:
            return Response({"error": "lat, lon y radio deben ser números"}, status=400)

        data = get_bicing_near(lat, lon, radio_km=radio)
        return Response(data)