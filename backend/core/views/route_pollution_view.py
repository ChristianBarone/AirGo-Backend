import math

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from ..services.air_quality import get_air_quality_near
from ..services.navigation import get_eco_route
from ..models import Route


# ── Helpers de cálculo (sin cambios) ─────────────────────────────────────────

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


def generar_segments_contaminacio(punts_ruta, stations, radi_km=0.4):
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
        punt_aqi = 0
        for st in stations:
            dist = haversine(lat, lon, st["geoPoint"]["lat"], st["geoPoint"]["lon"])
            if dist <= radi_km:
                punt_aqi = max(punt_aqi, st["aqi"])

        # Lògica per agrupar segments continus amb el mateix valor
        if current_aqi is None:
            current_aqi = punt_aqi
        elif current_aqi != punt_aqi:
            # El valor ha canviat! Tanquem el segment anterior
            details.append([start_idx, idx, current_aqi])
            start_idx = idx
            current_aqi = punt_aqi

    # Tanquem l'últim segment fins al final de la ruta
    if current_aqi is not None and start_idx < len(punts_ruta) - 1:
        details.append([start_idx, len(punts_ruta) - 1, current_aqi])

    return details


# ── View ──────────────────────────────────────────────────────────────────────

_EcoRouteRequest = inline_serializer(
    name="EcoRouteRequest",
    fields={
        "lat_start": serializers.FloatField(help_text="Latitud del origen (ej: 41.385)"),
        "lon_start": serializers.FloatField(help_text="Longitud del origen (ej: 2.173)"),
        "lat_end": serializers.FloatField(help_text="Latitud del destino"),
        "lon_end": serializers.FloatField(help_text="Longitud del destino"),
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
        summary="Generar ruta ecológica",
        description=(
            "Calcula la ruta óptima entre dos puntos minimizando la exposición a la contaminación. "
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

        try:
            start = {"lat": float(data.get("lat_start")), "lon": float(data.get("lon_start"))}
            end = {"lat": float(data.get("lat_end")), "lon": float(data.get("lon_end"))}
        except (TypeError, ValueError, KeyError):
            return Response(
                {
                    "error": (
                        "Coordenadas lat_start, lon_start, lat_end, lon_end "
                        "son obligatorias y deben ser números."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stations = get_air_quality_near(start["lat"], start["lon"], radio_km=20)
            route_data = get_eco_route(start, end, stations)

            if "paths" not in route_data:
                return Response(
                    {
                        "error": "GraphHopper no pudo calcular la ruta.",
                        "details": route_data.get("error", "Error desconocido"),
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            path = route_data["paths"][0]
            punts_gh = path.get("points", {}).get("coordinates", [])
            segments_colors = generar_segments_contaminacio(
                punts_gh, stations, radi_km=0.4
            )

            distance_km = round(path.get("distance", 0) / 1000, 3)
            avg_aqi = round(sum(s["aqi"] for s in stations) / len(stations), 2) if stations else 0.0

            route_obj = Route.objects.create(
                name=(
                    f"{data.get('lat_start')},{data.get('lon_start')} "
                    f"→ {data.get('lat_end')},{data.get('lon_end')}"
                ),
                start_location=f"{start['lat']},{start['lon']}",
                end_location=f"{end['lat']},{end['lon']}",
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
                        "coordinates": [[p[1], p[0]] for p in path["points"]["coordinates"]],
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