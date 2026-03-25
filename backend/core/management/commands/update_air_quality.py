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
            {"lat": 41.385, "lon": 2.173},
            {"lat": 41.390, "lon": 2.154},
            # añade más puntos según necesites
        ]

        for punto in puntos:
            try:
                data = get_air_quality_near(punto["lat"], punto["lon"])
                AirQualityHistoric.objects.update_or_create(
                    lat=punto["lat"],
                    lon=punto["lon"],
                    day_of_week=day_of_week,
                    hora=hora,
                    defaults={"aqi": data["aqi"]}
                )
            except Exception as e:
                self.stdout.write(f"Error en {punto}: {e}")

        self.stdout.write(f"Aire actualizado - día {day_of_week} hora {hora}")