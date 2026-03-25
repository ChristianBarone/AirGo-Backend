from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.air_quality import get_air_quality_near
from ..services.navigation import get_eco_route


class EcoRouteView(APIView):
    def post(self, request):
        # Esperamos lat_start, lon_start, lat_end, lon_end
        data = request.data

        try:
            start = {"lat": float(data["lat_start"]), "lon": float(data["lon_start"])}
            end = {"lat": float(data["lat_end"]), "lon": float(data["lon_end"])}
        except (KeyError, ValueError):
            return Response({"error": "Faltan coordenadas de inicio o fin"}, status=400)

        # 1. Obtener contaminación actual en la zona (radio 20km para pillar sensores)
        stations = get_air_quality_near(start["lat"], start["lon"], radio_km=20)

        # 2. Pedir a GraphHopper la ruta esquivando esas estaciones
        route_data = get_eco_route(start, end, stations)

        return Response({
            "status": "success",
            "aqi_stations_used": len(stations),
            "route": route_data
        })