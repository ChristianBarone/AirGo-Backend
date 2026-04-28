from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..services.air_quality import get_air_quality_near
from ..services.navigation import get_eco_route
from ..models import Route

import math


def haversine(lat1, lon1, lat2, lon2):
    """Calcula la distància en KM entre dos punts de la terra."""
    R = 6371.0  # Radi de la terra en km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generar_segments_contaminacio(punts_ruta, stations, radi_km=0.4):
    """
    Rep la llista de coordenades de la ruta i les estacions, i retorna els segments
    en el format de GraphHopper: [[inici_idx, fi_idx, valor_aqi], ...]
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
            st_lat = st["geoPoint"]["lat"]
            st_lon = st["geoPoint"]["lon"]
            dist = haversine(lat, lon, st_lat, st_lon)

            if dist <= radi_km:
                punt_aqi = max(punt_aqi, st["aqi"])

        if current_aqi is None:
            current_aqi = punt_aqi
        elif current_aqi != punt_aqi:
            details.append([start_idx, idx, current_aqi])
            start_idx = idx
            current_aqi = punt_aqi

    if current_aqi is not None and start_idx < len(punts_ruta) - 1:
        details.append([start_idx, len(punts_ruta) - 1, current_aqi])

    return details


class EcoRouteView(APIView):
    def post(self, request):
        data = request.data

        # 1. Validación de entrada
        try:
            start = {
                "lat": float(data.get("lat_start")),
                "lon": float(data.get("lon_start")),
            }
            end = {"lat": float(data.get("lat_end")), "lon": float(data.get("lon_end"))}
        except (TypeError, ValueError, KeyError):
            return Response(
                {
                    "error": "Coordenadas lat_start, lon_start, "
                    "lat_end, lon_end son obligatorias y deben ser números."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Obtener el perfil (por defecto: eco_bike)
        profile = data.get("profile", "eco_bike")

        try:
            # 2. Obtener datos de polución actuales (Capa Dinámica)
            stations = get_air_quality_near(start["lat"], start["lon"], radio_km=20)

            # 3. Llamar a GraphHopper con el perfil especificado
            route_data = get_eco_route(start, end, stations, profile=profile)

            # 4. Verificar si GraphHopper devolvió una ruta válida
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

            # 5. Guardar la ruta en BD
            distance_km = round(path.get("distance", 0) / 1000, 3)
            avg_aqi = (
                round(sum(s["aqi"] for s in stations) / len(stations), 2)
                if stations
                else 0.0
            )

            route_obj = Route.objects.create(
                name=f"{data.get('lat_start')},{data.get('lon_start')}"
                f" → {data.get('lat_end')},{data.get('lon_end')}",
                start_location=f"{start['lat']},{start['lon']}",
                end_location=f"{end['lat']},{end['lon']}",
                distance=distance_km,
                air_quality=avg_aqi,
                is_safe=avg_aqi < 100,
            )

            # 6. Formatear respuesta final para el Frontend
            response_payload = {
                "status": "success",
                "route_id": route_obj.id,
                "summary": {
                    "distance_meters": round(path.get("distance", 0), 2),
                    "duration_minutes": round(
                        path.get("time", 0) / 60000, 2
                    ),  # ms a mins
                    "duration_seconds": int(path.get("time", 0) / 1000),  # ms a s
                    "aqi_stations_detected": len(stations),
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [p[1], p[0]] for p in path["points"]["coordinates"]
                    ],
                },
                "pollution_details": segments_colors,
                # Opcional: enviar las estaciones usadas
                # para que el front las pinte como iconos
                "stations_info": stations,
            }

            return Response(response_payload, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error inesperado en el servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
