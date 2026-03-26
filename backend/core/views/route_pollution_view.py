from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from ..services.air_quality import get_air_quality_near
from ..services.navigation import get_eco_route

class EcoRouteView(APIView):
    def post(self, request):
        data = request.data

        # 1. Validación de entrada
        try:
            start = {
                "lat": float(data.get("lat_start")),
                "lon": float(data.get("lon_start"))
            }
            end = {
                "lat": float(data.get("lat_end")),
                "lon": float(data.get("lon_end"))
            }
        except (TypeError, ValueError, KeyError):
            return Response(
                {"error": "Coordenadas lat_start, lon_start, lat_end, lon_end son obligatorias y deben ser números."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 2. Obtener datos de polución actuales (Capa Dinámica)
            # Usamos un radio de 15-20km para cubrir el área metropolitana
            stations = get_air_quality_near(start["lat"], start["lon"], radio_km=20)

            # 3. Llamar a GraphHopper enviando las estaciones como áreas de penalización
            # Esto se combinará con tu Custom Model estático de Java
            route_data = get_eco_route(start, end, stations)

            # 4. Verificar si GraphHopper devolvió una ruta válida
            if "paths" not in route_data:
                return Response({
                    "error": "GraphHopper no pudo calcular la ruta.",
                    "details": route_data.get("message", "Error desconocido")
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            path = route_data['paths'][0]

            # 5. Formatear respuesta final para el Frontend
            response_payload = {
                "status": "success",
                "summary": {
                    "distance_meters": round(path.get("distance", 0), 2),
                    "duration_minutes": round(path.get("time", 0) / 60000, 2), # ms a mins
                    "duration_seconds": int(path.get("time", 0) / 1000), # ms a s
                    "aqi_stations_detected": len(stations)
                },
                # Convertimos [lon, lat] de GH a [lat, lon] para Leaflet/Google Maps
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[p[1], p[0]] for p in path["points"]["coordinates"]]
                },
                # Segmentos de polución para pintar la línea por colores
                "pollution_details": path.get("details", {}).get("pollution", []),
                # Opcional: enviar las estaciones usadas para que el front las pinte como iconos
                "stations_info": stations
            }

            return Response(response_payload, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error inesperado en el servidor: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )