import math
import requests

AIR_QUALITY_URL = "https://analisi.transparenciacatalunya.cat/resource/tasf-thgu.json"


def calcular_aqi(contaminant, valor):
    """
    Convierte un valor de contaminante a un AQI aproximado.
    Se usa una tabla simplificada para mantener una salida estable y fácil
    de consumir desde el frontend.
    """
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return 0

    umbrales = {
        "PM10": [
            (0, 50, 0, 50),
            (50, 100, 51, 100),
            (100, 250, 101, 200),
            (250, 350, 201, 300),
        ],
        "PM2.5": [
            (0, 12, 0, 50),
            (12, 35, 51, 100),
            (35, 55, 101, 150),
            (55, 150, 151, 200),
        ],
        "NO2": [
            (0, 40, 0, 50),
            (40, 90, 51, 100),
            (90, 120, 101, 150),
            (120, 230, 151, 200),
        ],
        "O3": [
            (0, 60, 0, 50),
            (60, 100, 51, 100),
            (100, 140, 101, 150),
            (140, 180, 151, 200),
        ],
    }

    if contaminant not in umbrales:
        return 50

    for c_low, c_high, aqi_low, aqi_high in umbrales[contaminant]:
        if c_low <= valor <= c_high:
            return int(
                aqi_low + (valor - c_low) * (aqi_high - aqi_low) / (c_high - c_low)
            )

    return 300


def haversine_km(lat1, lon1, lat2, lon2):
    """
    Distancia real entre dos coordenadas en kilómetros.
    """
    r = 6371.0

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return r * c


def get_latest_hour_value(station_row):
    """
    Obtiene el último valor horario disponible del registro.
    El dataset incluye campos como h01, h02, h03... y no siempre todos vienen rellenos.
    Priorizamos el último valor no vacío.
    """
    hourly_keys = [f"h{i:02d}" for i in range(24, 0, -1)]

    for key in hourly_keys:
        value = station_row.get(key)
        if value not in (None, "", " "):
            return value

    return None


def get_air_quality_near(lat, lon, radio_km=5):
    """
    Devuelve una lista con este formato:
    [
        {
            "zone": "Eixample",
            "geoPoint": {"lat": 41.38, "lon": 2.17},
            "aqi": 73
        }
    ]

    Se agrupa por estación y se conserva el peor AQI encontrado entre los contaminantes
    disponibles para esa estación.
    """
    params = {"$limit": 5000}

    response = requests.get(AIR_QUALITY_URL, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    estaciones = {}

    for station in data:
        try:
            slat = float(station["latitud"])
            slon = float(station["longitud"])

            dist_km = haversine_km(lat, lon, slat, slon)
            if dist_km > radio_km:
                continue

            station_name = station.get("nom_estacio", "").strip()
            contaminant = station.get("contaminant", "").strip()
            latest_value = get_latest_hour_value(station)

            if not station_name or latest_value is None:
                continue

            aqi = calcular_aqi(contaminant, latest_value)

            # Nos quedamos con el AQI más alto por estación
            if station_name not in estaciones or aqi > estaciones[station_name]["aqi"]:
                estaciones[station_name] = {
                    "zone": station_name,
                    "geoPoint": {"lat": slat, "lon": slon},
                    "aqi": aqi,
                }

        except (KeyError, ValueError, TypeError):
            continue

    return list(estaciones.values())


def get_eco_route(start_coords, end_coords, stations):
    gh_url = "http://localhost:8080/route"

    features_list = []
    priority_rules = []

    for i, station in enumerate(stations):
        area_id = f"station_{i}"
        lat = station["geoPoint"]["lat"]
        lon = station["geoPoint"]["lon"]
        aqi = station["aqi"]

        d = 0.004
        polygon_coords = [
            [
                [lon - d, lat - d],
                [lon + d, lat - d],
                [lon + d, lat + d],
                [lon - d, lat + d],
                [lon - d, lat - d],
            ]
        ]

        feature = {
            "type": "Feature",
            "id": area_id,
            "geometry": {"type": "Polygon", "coordinates": polygon_coords},
            "properties": {"aqi_value": aqi, "name": station.get("zone", "sensor")},
        }
        features_list.append(feature)

        if aqi > 100:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": "0.05"})
        elif aqi > 50:
            priority_rules.append({"if": f"in_area_{area_id}", "multiply_by": "0.4"})

    payload = {
        "points": [
            [start_coords["lon"], start_coords["lat"]],
            [end_coords["lon"], end_coords["lat"]],
        ],
        "profile": "eco_bike",
        "ch.disable": True,
        "points_encoded": False,
        "details": ["pollution", "average_speed", "time", "distance"],
        "custom_model": {
            "priority": priority_rules,
            "areas": {"type": "FeatureCollection", "features": features_list},
        },
    }

    try:
        response = requests.post(gh_url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Error en GraphHopper: {str(e)}"}
