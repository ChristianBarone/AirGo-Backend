from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Usuari, PlaEntrenament
from core.services.firebase import send_push_notification


class Command(BaseCommand):
    help = "Envia notificacions als usuaris que tenen un exercici planificat avui"

    def handle(self, *args, **kwargs):
        avui = timezone.now().weekday()  # 0=lunes, 6=domingo

        # Buscar todos los planes que tienen ejercicio hoy
        plans_avui = PlaEntrenament.objects.filter(
            diesSetmana__contains=avui
        )

        self.stdout.write(f"Plans amb exercici avui (dia {avui}): {plans_avui.count()}")

        for pla in plans_avui:
            # Obtener los usuarios que tienen este plan
            usuaris = pla.usuaris.filter(fcm_token__isnull=False).exclude(fcm_token="")

            for usuari in usuaris:
                try:
                    send_push_notification(
                        fcm_token=usuari.fcm_token,
                        title="💪 Tens entrenament avui!",
                        body="No oblidis fer el teu exercici d'avui. A per totes!",
                        data={
                            "type": "reminder",
                            "pla_id": str(pla.pk),
                        }
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f"Notificació enviada a {usuari.username}")
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Error enviant a {usuari.username}: {e}")
                    )