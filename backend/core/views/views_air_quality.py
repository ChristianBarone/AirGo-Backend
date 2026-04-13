from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from ..services.air_quality import get_air_quality_near
import requests


class AirQualityView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            lat = float(request.GET.get("lat"))
            lon = float(request.GET.get("lon"))
            radio = float(request.GET.get("radio", 5))
        except (TypeError, ValueError):
            return Response(
                {"error": "Los parámetros lat, lon y radio deben ser numéricos"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            pollution_points = get_air_quality_near(lat, lon, radio)
            return Response(pollution_points, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error obteniendo calidad del aire: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

def get_eco_route(start_coords, end_coords, stations):
    gh_url = "http://localhost:8080/route"

    # 1. Crear la lista de Features (Polígonos)
    features_list = []
    priority_rules = []

    for i, station in enumerate(stations):
        area_id = f"s{i}"
        lat = station["geoPoint"]["lat"]
        lon = station["geoPoint"]["lon"]
        aqi = station["aqi"]

        # Definir el polígono (cuadrado de influencia)
        d = 0.004
        polygon_coords = [[
            [lon - d, lat - d], [lon + d, lat - d],
            [lon + d, lat + d], [lon - d, lat + d],
            [lon - d, lat - d]
        ]]

        # objeto feature GeoJSON
        feature = {
            "type": "Feature",
            "id": area_id,
            "geometry": {
                "type": "Polygon",
                "coordinates": polygon_coords
            },
            "properties": {
                "aqi_value": aqi,
                "name": station.get("zone", "sensor")
            }
        }
        features_list.append(feature)

        # Regla de prioridad basada en el ID del Feature
        if aqi > 100:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": "0.05"})
        elif aqi > 50:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": "0.4"})

    # 2. Configurar el Payload con el Custom Model correcto
    payload = {
        "points": [
            [start_coords['lon'], start_coords['lat']],
            [end_coords['lon'], end_coords['lat']]
        ],
        "profile": "eco_bike",
        "ch.disable": True,
        "points_encoded": False,
        "details": ["pollution", "average_speed", "time", "distance"], # Pide todos los detalles
        "custom_model": {
            "priority": priority_rules,
            "areas": {
                "type": "FeatureCollection",
                "features": features_list # <--- Aquí va la lista que creamos
            }
        }
    }

    try:
        # Usamos POST porque el JSON del custom_model puede ser muy grande
        response = requests.post(gh_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error en GraphHopper: {str(e)}"}
