from django.core.management.base import BaseCommand
from core.models import AirQualityHistoric
from core.services.air_quality import get_air_quality_near  # ajusta el import
from datetime import datetime


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        now = datetime.now()
        day_of_week = now.weekday()  # 0=lunes, 6=domingo
        hora = now.hour

        # Aquí defines los puntos de Barcelona que quieres cubrir
        puntos = [
            {"lat": 41.385, "lon": 2.173},  # Cerca de Plaça Catalunya
            {"lat": 41.390, "lon": 2.154},  # Cerca de la Sagrada Familia
            {"lat": 41.406, "lon": 2.191},  # Barrio de Gracia
            {"lat": 41.378, "lon": 2.192},  # Parc de la Ciutadella
            {"lat": 41.378, "lon": 2.195},  # Barceloneta
            {"lat": 41.414, "lon": 2.191},  # L'Eixample
            {"lat": 41.369, "lon": 2.167},  # Zona Universitaria
            {"lat": 41.408, "lon": 2.196},  # El Raval
            {"lat": 41.377, "lon": 2.190},  # Poble Sec
            {"lat": 41.423, "lon": 2.188},  # Poblenou
            {"lat": 41.423, "lon": 2.208},  # Diagonal Mar
            {"lat": 41.447, "lon": 2.188},  # Zona del Camp Nou
            {"lat": 41.452, "lon": 2.175},  # Zona del Mercado de Sant Antoni
            {"lat": 41.424, "lon": 2.191},  # Gracia
            {"lat": 41.413, "lon": 2.164},  # Zona de Sants
        ]

        for punto in puntos:
            try:
                estacions_properes = get_air_quality_near(punto["lat"], punto["lon"])
                if estacions_properes:
                    # Busquem el pitjor AQI d'entre totes les estacions properes al punt
                    aqi_maxim = max(estacio["aqi"] for estacio in estacions_properes)

                    AirQualityHistoric.objects.update_or_create(
                        lat=punto["lat"],
                        lon=punto["lon"],
                        day_of_week=day_of_week,
                        hora=hora,
                        defaults={"aqi": aqi_maxim},  # Ara sí, li passem un número!
                    )
                    self.stdout.write(
                        f"Punt {punto['lat']}, {punto['lon']} guardat amb AQI: {aqi_maxim}"
                    )
                else:
                    self.stdout.write(
                        f"No hi ha estacions a prop del punt {punto['lat']}, {punto['lon']}"
                    )

            except Exception as e:
                self.stdout.write(f"Error en {punto}: {e}")

            self.stdout.write(
                self.style.SUCCESS(f"Aire actualizado - día {day_of_week} hora {hora}")
            )
