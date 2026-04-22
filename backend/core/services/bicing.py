import requests

# Feed de información estática de estaciones
STATION_INFO_URL = (
    "https://barcelona.publicbikesystem.net/customer/gbfs/v3.0/station_information.json"
)

# Feed de estado en tiempo real
STATION_STATUS_URL = (
    "https://barcelona.publicbikesystem.net/ube/gbfs/v1/en/station_status.json"
)


def extract_station_name(name_field, preferred_lang="ca"):
    if isinstance(name_field, str):
        return name_field

    if isinstance(name_field, list):
        # 1) Intentar idioma preferido
        for item in name_field:
            if item.get("language") == preferred_lang and item.get("text"):
                return item["text"]

        # 2) Fallback a español
        for item in name_field:
            if item.get("language") == "es" and item.get("text"):
                return item["text"]

        # 3) Fallback a inglés
        for item in name_field:
            if item.get("language") == "en" and item.get("text"):
                return item["text"]

        # 4) Primer texto disponible
        for item in name_field:
            if item.get("text"):
                return item["text"]

    return ""


def get_stations_info():
    """
    Obtiene la información estática de las estaciones.
    """
    try:
        info_resp = requests.get(STATION_INFO_URL, timeout=5)
        info_resp.raise_for_status()
        return info_resp.json().get("data", {}).get("stations", [])
    except requests.exceptions.RequestException:
        return []


def get_stations_status():
    """
    Obtiene el estado en tiempo real de las estaciones.
    Devuelve un diccionario indexado por station_id.
    """
    try:
        status_resp = requests.get(STATION_STATUS_URL, timeout=5)
        status_resp.raise_for_status()
        stations = status_resp.json().get("data", {}).get("stations", [])

        return {
            str(station["station_id"]): station
            for station in stations
            if "station_id" in station
        }
    except requests.exceptions.RequestException:
        return {}


def get_bicing_near(lat, lon, radio_km=5):
    """
    Devuelve estaciones cercanas a una coordenada aproximando la distancia.
    Nota: esta lógica mantiene tu cálculo actual para no cambiar comportamiento.
    """
    stations = get_stations_info()
    statuses = get_stations_status()

    result = []

    for station in stations:
        try:
            slat = float(station["lat"])
            slon = float(station["lon"])

            # Aproximación simple en grados
            dist = ((slat - lat) ** 2 + (slon - lon) ** 2) ** 0.5

            if dist < radio_km * 0.01:
                station_id = str(station["station_id"])
                status = statuses.get(station_id, {})

                result.append(
                    {
                        "id": station_id,
                        "name": extract_station_name(station.get("name"), "ca"),
                        "geoPoint": {"lat": slat, "lon": slon},
                        "mechanicalBikes": status.get(
                            "num_bikes_available_types", {}
                        ).get("mechanical", 0),
                        "electricBikes": status.get(
                            "num_bikes_available_types", {}
                        ).get("ebike", 0),
                        "freeSlots": status.get("num_docks_available", 0),
                        "status": status.get("status", "unknown"),
                    }
                )

        except (KeyError, ValueError, TypeError):
            continue

    return result
