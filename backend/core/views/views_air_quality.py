import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from ..services.air_quality import get_air_quality_near
from ..services.navigation import get_eco_route


def get_eco_route(start_coords, end_coords, stations):
    gh_url = "http://localhost:8080/route"

    # 1. Crear la lista de Features (Polígonos)
    features_list = []
    priority_rules = []

    for i, station in enumerate(stations):
        area_id = f"station_{i}"
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