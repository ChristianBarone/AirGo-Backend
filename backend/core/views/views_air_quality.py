from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, inline_serializer
from drf_spectacular.types import OpenApiTypes

from ..services.air_quality import get_air_quality_near


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
                    "zone": serializers.CharField(help_text="Nombre de la zona / estación"),
                    "aqi": serializers.FloatField(help_text="Índice de calidad del aire (AQI)"),
                    "geoPoint": inline_serializer(
                        name="GeoPoint",
                        fields={
                            "lat": serializers.FloatField(),
                            "lon": serializers.FloatField(),
                        },
                    ),
                },
            ),
            400: OpenApiResponse(description="Parámetros lat, lon o radio no numéricos"),
            500: OpenApiResponse(description="Error interno al consultar la fuente de datos"),
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
