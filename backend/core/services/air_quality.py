import requests

AIR_QUALITY_URL = "https://analisi.transparenciacatalunya.cat/resource/tasf-thgu.json"

def calcular_aqi(contaminant, valor):
    try:
        valor = float(valor)
    except (ValueError, TypeError):
        return 0

    # Umbrales simplificados (µg/m3 → AQI 0-500)
    umbrales = {
        "PM10":  [(0,50,0,50), (50,100,51,100), (100,250,101,200), (250,350,201,300)],
        "PM2.5": [(0,12,0,50), (12,35,51,100), (35,55,101,150), (55,150,151,200)],
        "NO2":   [(0,40,0,50), (40,90,51,100), (90,120,101,150), (120,230,151,200)],
        "O3":    [(0,60,0,50), (60,100,51,100), (100,140,101,150), (140,180,151,200)],
    }

    if contaminant not in umbrales:
        return 50  # valor neutro si no conocemos el contaminante

    for (c_low, c_high, aqi_low, aqi_high) in umbrales[contaminant]:
        if c_low <= valor <= c_high:
            return int(aqi_low + (valor - c_low) * (aqi_high - aqi_low) / (c_high - c_low))

    return 300  # muy malo si supera todos los umbrales


def get_air_quality_near(lat, lon, radio_km=5):
    params = {"$limit": 1000}
    response = requests.get(AIR_QUALITY_URL, params=params)
    response.raise_for_status()
    data = response.json()

    # Agrupa por estación y calcula AQI máximo
    estacions = {}
    for station in data:
        try:
            slat = float(station["latitud"])
            slon = float(station["longitud"])
            dist = ((slat - lat)**2 + (slon - lon)**2) ** 0.5

            if dist < radio_km * 0.01:
                nom = station.get("nom_estacio")
                contaminant = station.get("contaminant", "")
                valor = station.get("h01", 0)
                aqi = calcular_aqi(contaminant, valor)

                if nom not in estacions or aqi > estacions[nom]["aqi"]:
                    estacions[nom] = {
                        "zone": nom,
                        "geoPoint": {"lat": slat, "lon": slon},
                        "aqi": aqi
                    }
        except (KeyError, ValueError):
            continue

    return list(estacions.values())