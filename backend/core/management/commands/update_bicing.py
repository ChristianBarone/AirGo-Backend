from django.core.management.base import BaseCommand
from core.models import BicingEstacio
from core.services.bicing import get_bicing_near


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        estacions = get_bicing_data()  # ja ho tenim al servei
        for e in estacions:
            BicingEstacio.objects.update_or_create(
                station_id=e["station_id"],
                defaults={
                    "name": e["name"],
                    "lat": e["lat"],
                    "lon": e["lon"],
                    "capacity": e["capacity"],
                    "bikes_available": e["bikes_available"],
                    "docks_available": e["docks_available"],
                },
            )
        self.stdout.write("Bicing actualizado correctamente")
