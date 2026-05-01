import math

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from ..services.air_quality import get_air_quality_near
from ..services.navigation import get_eco_route
from ..models import Route



def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distancia en KM entre dos puntos de la Tierra."""
    R = 6371.0
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (
        math.sin(dLat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def generar_segments_contaminacio(punts_ruta, stations, radi_km=1.5):
    """
    Recibe la lista de coordenadas de la ruta y las estaciones,
    y devuelve los segmentos de contaminación en formato GraphHopper:
    [[inici_idx, fi_idx, valor_aqi], ...]
    """
    details = []
    if not punts_ruta:
        return details

    current_aqi = None
    start_idx = 0

    for idx, punt in enumerate(punts_ruta):
        lon, lat = punt[0], punt[1]
        punt_aqi = 20
        distancia_minima = float('inf')

        for st in stations:
            dist = haversine(lat, lon, st["geoPoint"]["lat"], st["geoPoint"]["lon"])
            if dist < distancia_minima:
                distancia_minima = dist
                temp_aqi = st["aqi"]

        if distancia_minima <= radi_km:
            punt_aqi = temp_aqi

        if current_aqi is None:
            current_aqi = punt_aqi
        elif current_aqi != punt_aqi:
            details.append([start_idx, idx, current_aqi])
            start_idx = idx
            current_aqi = punt_aqi



    details.append([start_idx, len(punts_ruta) - 1, current_aqi])

    return details


# ── View ──────────────────────────────────────────────────────────────────────

_EcoRouteRequest = inline_serializer(
    name="EcoRouteRequest",
    fields={
        "profile": serializers.ChoiceField(
            choices=[
                ("eco_bike", "Bicicleta"),
                ("eco_foot", "A peu"),
                ("running", "Running")
            ],
            default="eco_bike",
            help_text="Tria el mitjà de transport per a la ruta."
        ),
        "points": serializers.ListField(
            child=serializers.ListField(
                child=serializers.FloatField(),
                min_length=2,
                max_length=2
            ),
            help_text="Llista de punts: [[lat, lon], [lat, lon], ...]",
            min_length=2
        ),
    },
)

_EcoRouteResponse = inline_serializer(
    name="EcoRouteResponse",
    fields={
        "status": serializers.CharField(help_text="'success'"),
        "route_id": serializers.IntegerField(help_text="ID de la ruta creada en BD"),
        "summary": inline_serializer(
            name="EcoRouteSummary",
            fields={
                "distance_meters": serializers.FloatField(),
                "duration_minutes": serializers.FloatField(),
                "duration_seconds": serializers.IntegerField(),
                "aqi_stations_detected": serializers.IntegerField(
                    help_text="Número de estaciones de calidad del aire encontradas"
                ),
            },
        ),
        "geometry": inline_serializer(
            name="EcoRouteGeometry",
            fields={
                "type": serializers.CharField(help_text="Siempre 'LineString'"),
                "coordinates": serializers.ListField(
                    child=serializers.ListField(child=serializers.FloatField()),
                    help_text="Lista de [lat, lon] en orden",
                ),
            },
        ),
        "pollution_details": serializers.ListField(
            child=serializers.ListField(child=serializers.FloatField()),
            help_text="Segmentos de contaminación: [[idx_inicio, idx_fin, aqi], ...]",
        ),
        "stations_info": serializers.ListField(
            child=serializers.DictField(),
            help_text="Datos completos de las estaciones AQI cercanas",
        ),
    },
)


class EcoRouteView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        tags=["Routes"],
        summary="Generar ruta ecològica",
        description=(
            "Calcula la ruta óptima entre puntos minimizando la exposición a la contaminación. "
            "Internamente consulta las estaciones de calidad del aire, llama a GraphHopper con un "
            "modelo de prioridad personalizado y persiste la ruta en base de datos. "
            "Devuelve la geometría GeoJSON de la ruta junto con los segmentos de contaminación."
        ),
        request=_EcoRouteRequest,
        responses={
            200: _EcoRouteResponse,
            400: OpenApiResponse(
                description="Coordenadas faltantes o con formato incorrecto"
            ),
            500: OpenApiResponse(
                description="GraphHopper no pudo calcular la ruta o error interno del servidor"
            ),
        },
    )
    def post(self, request):
        data = request.data
        raw_points = data.get("points", [])
        profile = data.get("profile", "eco_bike")

        if len(raw_points) < 2:
            return Response({"error": "Calen com a mínim dos punts (inici i final)."}, status=400)

        try:
            stations = get_air_quality_near(raw_points[0][0], raw_points[0][1], radio_km=20)

            # 3. Llamar a GraphHopper con el perfil especificado
            route_data = get_eco_route(raw_points, stations, profile=profile)

            if "paths" not in route_data:
                return Response(
                    {
                        "error": "GraphHopper no pudo calcular la ruta.",
                        "details": route_data.get("error", "Error desconocido"),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            path = route_data['paths'][0]
            punts_gh = path.get("points", {}).get("coordinates", [])
            segments_colors = generar_segments_contaminacio(
                punts_gh, stations
            )

            if segments_colors:
                suma_aqi = sum(s[2] * (s[1] - s[0] + 1) for s in segments_colors)
                avg_aqi = round(suma_aqi / len(punts_gh), 1)
            else:
                avg_aqi = 20.0

            distance_km = round(path.get("distance", 0) / 1000, 3)

            route_obj = Route.objects.create(
                name=(
                    f"{data.get('lat_start')},{data.get('lon_start')} "
                    f"→ {data.get('lat_end')},{data.get('lon_end')}"
                ),
                start_location=f"{raw_points[0]}",
                end_location=f"{raw_points[-1]}",
                distance=distance_km,
                air_quality=avg_aqi,
                is_safe=avg_aqi < 100,
            )

            return Response(
                {
                    "status": "success",
                    "route_id": route_obj.id,
                    "summary": {
                        "distance_meters": round(path.get("distance", 0), 2),
                        "duration_minutes": round(path.get("time", 0) / 60000, 2),
                        "duration_seconds": int(path.get("time", 0) / 1000),
                        "aqi_stations_detected": len(stations),
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": punts_gh,
                    },
                    "pollution_details": segments_colors,
                    "stations_info": stations,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error inesperado en el servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
