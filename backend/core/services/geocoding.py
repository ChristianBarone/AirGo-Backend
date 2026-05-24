import requests


def get_address_from_coords(lat, lon):
    url = "https://eines.icgc.cat/geocodificador/invers"
    params = {"lat": lat, "lon": lon, "layers": "address", "size": 1}

    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            features = data.get("features", [])

            if features:
                return features[0]["properties"].get("etiqueta")

            params["layers"] = "tops"
            response = requests.get(url, params=params, timeout=5)
            data = response.json()
            features = data.get("features", [])
            if features:
                return features[0]["properties"].get("etiqueta")

        return f"{lat}, {lon}"
    except Exception as e:
        print(f"Error Geocoding ICGC: {e}")
        return f"{lat}, {lon}"
