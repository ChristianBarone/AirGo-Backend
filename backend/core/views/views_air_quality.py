from datetime import datetime # <--- IMPORTANTE añadir este
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny

from core.models import AirQualityHistoric
from ..services.air_quality import get_air_quality_near, haversine_km

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

class AirQualityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Air Quality"],
        summary="Calidad del aire cercana",
        description=(
            "Devuelve las estaciones de calidad del aire dentro del radio indicado alrededor "
            "de las coordenadas dadas. No requiere autenticación."
        ),
        parameters=[
            OpenApiParameter(name="lat", type=OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="lon", type=OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY, required=True),
            OpenApiParameter(name="radio", type=OpenApiTypes.FLOAT, location=OpenApiParameter.QUERY, required=False),
        ],
        responses={
            200: inline_serializer(
                name="AirQualityStation",
                many=True,
                fields={
                    "zone": serializers.CharField(),
                    "aqi": serializers.FloatField(),
                    "geoPoint": inline_serializer(
                        name="GeoPoint",
                        fields={"lat": serializers.FloatField(), "lon": serializers.FloatField()},
                    ),
                },
            ),
        },
    )
    def get(self, request):
        try:
            lat = float(request.GET.get("lat"))
            lon = float(request.GET.get("lon"))
            radio = float(request.GET.get("radio", 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "Los parámetros lat, lon y radio deben ser numéricos"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. INTENTAR API EN VIVO (PLAN A)
        try:
            pollution_points = get_air_quality_near(lat, lon, radio)
        except Exception:
            pollution_points = []

        # 2. SI LA API FALLÓ O NO HAY DATOS, USAR BD (PLAN B)
        if not pollution_points:
            now = datetime.now()
            historics = AirQualityHistoric.objects.filter(
                day_of_week=now.weekday(),
                hora=now.hour
            )

            for h in historics:
                dist = haversine_km(lat, lon, h.lat, h.lon)
                if dist <= radio:
                    pollution_points.append({
                        "zone": f"Estación Histórica (Aprox)",
                        "aqi": h.aqi,
                        "geoPoint": {"lat": h.lat, "lon": h.lon}
                    })

        if not pollution_points:
            return Response(
                {"error": "No hay datos disponibles."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(pollution_points, status=status.HTTP_200_OK)

class ExternalAirQualityView(APIView):
    def get(self, request):
        lat_param = request.query_params.get("lat")
        lon_param = request.query_params.get("lon")
        radius_param = request.query_params.get("radius")

        if not lat_param or not lon_param:
            return Response({"error": "Falten els paràmetres 'lat' i 'lon'."}, status=400)

        try:
            lat = float(lat_param)
            lon = float(lon_param)
            search_radius = float(radius_param) if radius_param else 10.0
        except ValueError:
            return Response({"error": "Formats numèrics incorrectes."}, status=400)

        # 1. PLAN A: API EXTERNA
        try:
            stations = get_air_quality_near(lat, lon, radio_km=search_radius)
        except Exception:
            stations = []

        # 2. PLAN B: BD
        source = "live"
        if not stations:
            source = "historic"
            now = datetime.now()
            historics = AirQualityHistoric.objects.filter(
                day_of_week=now.weekday(),
                hora=now.hour
            )
            for h in historics:
                dist = haversine_km(lat, lon, h.lat, h.lon)
                if dist <= search_radius:
                    stations.append({
                        "zone": "Dato Histórico Guardado",
                        "geoPoint": {"lat": h.lat, "lon": h.lon},
                        "aqi": h.aqi,
                        "distance": dist
                    })

        if not stations:
            return Response({"message": "No hi ha dades disponibles."}, status=404)

        for s in stations:
            if "distance" not in s:
                s["distance"] = haversine_km(lat, lon, s["geoPoint"]["lat"], s["geoPoint"]["lon"])

        nearest_station = min(stations, key=lambda x: x["distance"])

        response_data = {
            "point_quality": {
                "aqi": nearest_station["aqi"],
                "station": nearest_station["zone"],
                "distance_km": round(nearest_station["distance"], 2),
                "source": source
            }
        }

        if radius_param is not None:
            best_areas = sorted(stations, key=lambda x: x["aqi"])[:3]
            response_data["recommendations"] = [
                {
                    "zone": area["zone"],
                    "lat": area["geoPoint"]["lat"],
                    "lon": area["geoPoint"]["lon"],
                    "aqi": area["aqi"],
                }
                for area in best_areas if area["aqi"] < 100
            ]

        return Response(response_data, status=status.HTTP_200_OK)