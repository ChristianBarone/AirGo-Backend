from django.core.management.base import BaseCommand
from core.models import BicingEstacio
from core.services.bicing import get_stations_info, get_stations_status


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        stations = get_stations_info()
        statuses = get_stations_status()

        for station in stations:
            try:
                station_id = str(station["station_id"])
                status = statuses.get(station_id, {})

                BicingEstacio.objects.update_or_create(
                    station_id=station_id,
                    defaults={
                        "name": station.get("name", ""),
                        "lat": float(station["lat"]),
                        "lon": float(station["lon"]),
                        "capacity": station.get("capacity", 0),
                        "bikes_available": status.get("num_bikes_available", 0),
                        "docks_available": status.get("num_docks_available", 0),
                    },
                )
            except (KeyError, ValueError, TypeError) as e:
                self.stdout.write(self.style.ERROR(f"Error en estació {station}: {e}"))

        self.stdout.write(self.style.SUCCESS("Bicing actualizado correctamente"))
