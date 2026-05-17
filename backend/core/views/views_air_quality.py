from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

from ..services.air_quality import get_air_quality_near, haversine_km


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
            OpenApiParameter(
                name="lat",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Latitud del punto de referencia (ej: 41.385)",
            ),
            OpenApiParameter(
                name="lon",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Longitud del punto de referencia (ej: 2.173)",
            ),
            OpenApiParameter(
                name="radio",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Radio de búsqueda en kilómetros (por defecto: 5)",
            ),
        ],
        responses={
            200: inline_serializer(
                name="AirQualityStation",
                many=True,
                fields={
                    "zone": serializers.CharField(
                        help_text="Nombre de la zona / estación"
                    ),
                    "aqi": serializers.FloatField(
                        help_text="Índice de calidad del aire (AQI)"
                    ),
                    "geoPoint": inline_serializer(
                        name="GeoPoint",
                        fields={
                            "lat": serializers.FloatField(),
                            "lon": serializers.FloatField(),
                        },
                    ),
                },
            ),
            400: OpenApiResponse(
                description="Parámetros lat, lon o radio no numéricos"
            ),
            500: OpenApiResponse(
                description="Error interno al consultar la fuente de datos"
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

        try:
            pollution_points = get_air_quality_near(lat, lon, radio)
            return Response(pollution_points, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error obteniendo calidad del aire: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExternalAirQualityView(APIView):

    def get(self, request):
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        radius = request.query_params.get("radius")  # Radi per defecte 5km

        if not lat or not lon:
            return Response(
                {"error": "Falten els paràmetres 'lat' i 'lon'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat, lon = float(lat), float(lon)
        except ValueError:
            return Response({"error": "Formats numèrics incorrectes."}, status=400)

        # Obtenim totes les estacions properes
        search_radius = float(radius) if radius else 10.0
        stations = get_air_quality_near(lat, lon, radio_km=search_radius)

        if not stations:
            return Response(
                {"message": "No hi ha dades disponibles per aquesta zona."}, status=404
            )

        # Calculem quina estació és la més propera de les que hem trobat
        for s in stations:
            s["distance"] = haversine_km(
                lat, lon, s["geoPoint"]["lat"], s["geoPoint"]["lon"]
            )

        nearest_station = min(stations, key=lambda x: x["distance"])

        response_data = {
            "point_quality": {
                "aqi": nearest_station["aqi"],
                "station": nearest_station["zone"],
                "distance_km": round(nearest_station["distance"], 2),
            }
        }

        # 4. NOMÉS si han passat el paràmetre 'radius', afegim les recomanacions
        if radius is not None:
            # Ordenem per millor AQI i agafem les 3 millors zones
            best_areas = sorted(stations, key=lambda x: x["aqi"])[:3]
            response_data["recommendations"] = [
                {
                    "zone": area["zone"],
                    "lat": area["geoPoint"]["lat"],
                    "lon": area["geoPoint"]["lon"],
                    "aqi": area["aqi"],
                }
                for area in best_areas
                if area["aqi"] < 100
            ]

        return Response(response_data, status=status.HTTP_200_OK)