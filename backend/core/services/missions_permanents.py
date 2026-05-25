from django.db.models import Sum, Max
from django.db import transaction
from ..models import Exercici, MissioPermanent, MissioUsuari


def verificar_i_actualitzar_missions(usuari):
    historico = Exercici.objects.filter(usuari=usuari, completat=True)
    metrics = {
        "DIST_CAM": (historico.filter(template__tipusExercici="CAM").aggregate(Sum('distance_meters'))[
                         'distance_meters__sum'] or 0) / 1000.0,
        "DIST_BIC": (historico.filter(template__tipusExercici="BIC").aggregate(Sum('distance_meters'))[
                         'distance_meters__sum'] or 0) / 1000.0,
        "TOTAL_EXE": historico.count(),
        "MED_PLA_OR": historico.filter(medalla_obtinguda__in=["OR", "PLA"]).count(),
        "MED_OR": historico.filter(medalla_obtinguda="OR").count(),
        "MAX_DIST_CAM": (historico.filter(template__tipusExercici="CAM").aggregate(Max('distance_meters'))[
                             'distance_meters__max'] or 0) / 1000.0,
        "MAX_DIST_BIC": (historico.filter(template__tipusExercici="BIC").aggregate(Max('distance_meters'))[
                             'distance_meters__max'] or 0) / 1000.0,
        "MAX_TEMPS": (historico.aggregate(Max('duration_seconds'))['duration_seconds__max'] or 0) / 3600.0,
    }

    # Transacción atómica para asegurar que si algo falla no se guarden datos corruptos
    with transaction.atomic():
        missions_actives = MissioUsuari.objects.filter(usuari=usuari, completada=False).select_related('missio')
        metriques_completades = set()

        for relacio in missions_actives:
            missio = relacio.missio
            valor_actual = metrics.get(missio.metrica, 0)

            if valor_actual >= missio.valor_objectiu:
                relacio.completada = True
                relacio.save()

                # Otorgar recompensa al usuario
                # perfil = usuari.perfil
                # perfil.punts += missio.recompensa
                # perfil.save()

                metriques_completades.add(missio.metrica)

        for metrica in metriques_completades:
            # Buscamos cuál era la fase que se acaba de completar
            # Hacemos un max para asegurar el tiro si se completaran dos de golpe por cargas masivas
            fase_max_completada = MissioUsuari.objects.filter(
                usuari=usuari,
                missio__metrica=metrica,
                completada=True
            ).aggregate(Max('missio__fase_metrica'))['missio__fase_metrica__max'] or 0

            proxima_fase = fase_max_completada + 1

            # Buscamos si el sistema tiene definida la siguiente fase para esa métrica
            seguent_missio_sistema = MissioPermanent.objects.filter(
                metrica=metrica,
                fase_metrica=proxima_fase
            ).first()

            # Si existe la siguiente fase y el usuario no la tiene ya asignada, se la activamos
            if seguent_missio_sistema:
                MissioUsuari.objects.get_or_create(
                    usuari=usuari,
                    missio=seguent_missio_sistema,
                    defaults={'completada': False}
                )

def inicialitzar_missions_usuari_nou(usuari):
    fases_inicials = MissioPermanent.objects.filter(fase_metrica=1)

    for missio in fases_inicials:
        MissioUsuari.objects.get_or_create(
            usuari=usuari,
            missio=missio,
            defaults={'completada': False}
        )