import requests

def get_eco_route(start_coords, end_coords, stations):
    gh_url = "http://localhost:8080/route"

    features_list = []
    priority_rules = []

    for i, station in enumerate(stations):
        area_id = f"station_{i}"
        lat = station["geoPoint"]["lat"]
        lon = station["geoPoint"]["lon"]
        aqi = station["aqi"]

        d = 0.004 # Radio de influencia
        polygon_coords = [[
            [lon - d, lat - d], [lon + d, lat - d],
            [lon + d, lat + d], [lon - d, lat + d],
            [lon - d, lat - d]
        ]]

        # Construcción correcta del Feature GeoJSON
        feature = {
            "type": "Feature",
            "id": area_id,
            "geometry": {
                "type": "Polygon",
                "coordinates": polygon_coords
            },
            "properties": { "aqi": aqi }
        }
        features_list.append(feature)

        # Reglas de prioridad (usando números, no strings)
        if aqi > 100:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": 0.1})
        elif aqi > 50:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": 0.5})

    payload = {
        "points": [
            [start_coords['lon'], start_coords['lat']],
            [end_coords['lon'], end_coords['lat']]
        ],
        "profile": "eco_bike",
        "ch.disable": True,
        "points_encoded": False,
        "details": ["pollution", "time", "distance"],
        "custom_model": {
            "priority": priority_rules,
            "areas": {
                "type": "FeatureCollection",
                "features": features_list
            }
        }
    }

    try:
        response = requests.post(gh_url, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}