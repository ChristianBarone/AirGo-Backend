import requests

def get_eco_route(start_coords, end_coords, stations):
    gh_url = "http://graphhopper:8989/route"

    stations = sorted(stations, key=lambda x: x["aqi"], reverse=True)[:5]


    features_list = []
    priority_rules = []

    for i, station in enumerate(stations):
        area_id = f"s{i}"
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
            "properties": {}
        }
        features_list.append(feature)

        # Reglas de prioridad (usando números, no strings)
        if aqi > 100:
            priority_rules.append({"if": f"in_{area_id}", "multiply_by": 0.1})
        elif aqi > 50:
            priority_rules.append({"if": f"in_{area_id}", "multiply_by": 0.5})

    payload = {
        "points": [
            [start_coords['lon'], start_coords['lat']],
            [end_coords['lon'], end_coords['lat']]
        ],
        "profile": "eco_bike",
        "ch.disable": True,
        "points_encoded": False,
        "details": ["time", "distance"],
        "custom_model": {
            "priority": priority_rules,
            "areas": {
                "type": "FeatureCollection",
                "features": features_list
            }
        }
    }

    # try:
        # response = requests.post(gh_url, json=payload)
        # response.raise_for_status()
        # return response.json()
    # except Exception as e:
        # return {"error": str(e)}

    try:
        response = requests.post(gh_url, json=payload)
        # Si GraphHopper ens dóna un error 400 (ex: ruta fora del mapa, error de sintaxi)
        if response.status_code != 200:
            return {"error": f"Error de GraphHopper: {response.text}"}

        return response.json()
    except Exception as e:
        return {"error": f"Error de connexió amb GraphHopper: {str(e)}"}