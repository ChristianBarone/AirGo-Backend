import requests


def get_eco_route(start_coords, end_coords, stations):
    """
    Llama a GraphHopper usando las estaciones de AQI como áreas de penalización.
    """
    gh_url = "http://localhost:8080/route"

    # 1. Construir el Custom Model basado en las estaciones reales
    areas = {}
    priority_rules = []

    for i, station in enumerate(stations):
        area_id = f"station_{i}"
        lat = station["geoPoint"]["lat"]
        lon = station["geoPoint"]["lon"]
        aqi = station["aqi"]

        # Crear un pequeño cuadrado de influencia alrededor del sensor (aprox 400m)
        d = 0.004
        polygon = [[
            [lon - d, lat - d], [lon + d, lat - d],
            [lon + d, lat + d], [lon - d, lat + d],
            [lon - d, lat - d]
        ]]

        areas[area_id] = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": polygon}
        }

        # Lógica de penalización: a más AQI, menos prioridad (0.1 = evitar casi siempre)
        if aqi > 100:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": 0.05})
        elif aqi > 50:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": 0.4})

    # 2. Configurar el JSON para GraphHopper
    payload = {
        "points": [
            [start_coords['lon'], start_coords['lat']],
            [end_coords['lon'], end_coords['lat']]
        ],
        "profile": "eco_bike",
        "ch.disable": True,
        "points_encoded": False,  # Para recibir las coordenadas legibles
        "custom_model": {
            "priority": priority_rules,
            "areas": areas
        }
    }

    try:
        response = requests.post(gh_url, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error conectando con GraphHopper: {str(e)}"}