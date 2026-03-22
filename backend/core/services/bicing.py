import requests

STATION_INFO_URL = "https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_information"
STATION_STATUS_URL = "https://api.bsmsa.eu/ext/api/bsm/gbfs/v2/en/station_status"

def get_stations_info():
    try:
        info_resp = requests.get(STATION_INFO_URL, timeout=5)
        info_resp.raise_for_status()
        return info_resp.json()["data"]["stations"]
    except requests.exceptions.RequestException:
        return []

def get_stations_status():
    try:
        status_resp = requests.get(STATION_STATUS_URL, timeout=5)
        status_resp.raise_for_status()
        return {s["station_id"]: s for s in status_resp.json()["data"]["stations"]}
    except requests.exceptions.RequestException:
        return {}

def get_bicing_near(lat, lon, radio_km=5):
    stations = get_stations_info()
    statuses = get_stations_status()

    result = []
    for station in stations:
        try:
            slat = float(station["lat"])
            slon = float(station["lon"])
            dist = ((slat - lat)**2 + (slon - lon)**2) ** 0.5

            if dist < radio_km * 0.01:
                status = statuses.get(station["station_id"], {})
                result.append({
                    "id": str(station["station_id"]),
                    "name": station.get("name", ""),
                    "geoPoint": {"lat": slat, "lon": slon},
                    "mechanicalBikes": status.get("num_bikes_available_types", {}).get("mechanical", 0),
                    "electricBikes": status.get("num_bikes_available_types", {}).get("ebike", 0),
                    "freeSlots": status.get("num_docks_available", 0),
                    "status": status.get("status", "unknown"),
                })
        except (KeyError, ValueError):
            continue

    return result