import requests
from rest_framework.views import APIView
from rest_framework.response import Response


class RoutePollutionView(APIView):
    def get(self, request):
        # Recibir parámetros del frontend
        start = request.query_params.get('start')  # ej: "41.38,2.17"
        end = request.query_params.get('end')

        gh_url = "http://localhost:8080/route"
        params = {
            "point": [start, end],
            "profile": "eco_bike",
            "details": ["pollution", "average_speed"],
            "points_encoded": "false",  # <--- Tu petición: coordenadas reales
            "locale": "es"
        }

        try:
            r = requests.get(gh_url, params=params)
            data = r.json()

            # Limpiamos la respuesta para el frontend
            path = data['paths'][0]
            payload = {
                "coordinates": path['points']['coordinates'],  # Ya vienen como [lon, lat]
                "pollution_segments": path['details']['pollution'],
                "distance": path['distance'],
                "time": path['time']
            }
            return Response(payload)
        except Exception as e:
            return Response({"error": str(e)}, status=500)