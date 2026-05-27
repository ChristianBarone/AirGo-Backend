from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

from ..services.bicing import get_bicing_near
from ..models import BicingEstacio


class BicingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Bicing"],
        summary="Estaciones de Bicing cercanas",
        description=(
            "Devuelve las estaciones de Bicing dentro del radio indicado. "
            "Si la API externa no está disponible, se sirven los datos cacheados en base de datos. "
            "Requiere autenticación JWT."
        ),
        parameters=[
            OpenApiParameter(
                name="lat",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Latitud del punto de referencia (por defecto: 41.385)",
            ),
            OpenApiParameter(
                name="lon",
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Longitud del punto de referencia (por defecto: 2.173)",
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
                name="BicingEstacioResponse",
                many=True,
                fields={
                    "station_id": serializers.IntegerField(
                        help_text="ID de la estación Bicing"
                    ),
                    "name": serializers.CharField(help_text="Nombre de la estación"),
                    "lat": serializers.FloatField(),
                    "lon": serializers.FloatField(),
                    "capacity": serializers.IntegerField(
                        help_text="Capacidad total de la estación"
                    ),
                    "bikes_available": serializers.IntegerField(
                        help_text="Bicicletas disponibles ahora"
                    ),
                    "docks_available": serializers.IntegerField(
                        help_text="Anclajes libres ahora"
                    ),
                    "updated_at": serializers.DateTimeField(
                        help_text="Última actualización del dato"
                    ),
                },
            ),
            400: OpenApiResponse(description="lat, lon o radio no son números válidos"),
            401: OpenApiResponse(description="No autenticado"),
        },
    )
    def get(self, request):
        try:
            lat = float(request.query_params.get("lat", 41.385))
            lon = float(request.query_params.get("lon", 2.173))
            radio = float(request.query_params.get("radio", 5))
        except ValueError:
            return Response(
                {"error": "lat, lon y radio deben ser números"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = get_bicing_near(lat, lon, radio_km=radio)

        if not data:  # API caída o sin resultados → fallback a BD
            data = list(BicingEstacio.objects.values())

        return Response(data)
