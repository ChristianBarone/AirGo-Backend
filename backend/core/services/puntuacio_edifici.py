import requests

URL_EXTERNA = "http://nginx:9999/api/servei/puntuacio-edifici/"


def consultar_puntuacio_edifici(municipi, adreca, numero):
    payload = {"municipio": municipi, "direccion": adreca, "numero": str(numero)}
    try:
        # Posem un timeout de 5 segons per si l'altre servidor va lent
        response = requests.post(URL_EXTERNA, json=payload, timeout=20)
        if response.status_code == 200:
            return response.json().get("punts", -1)
        return -1
    except Exception:
        # Si hi ha qualsevol error de xarxa, tornem -1
        return -1
