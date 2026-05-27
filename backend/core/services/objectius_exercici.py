import numpy as np
import re
from datetime import timedelta
from django.utils import timezone
from django.db.models import F, ExpressionWrapper, FloatField, Avg
from ..models import Exercici, ObjectiuExercici


def format_ritme_min_km(segons_per_km):
    if not segons_per_km or np.isnan(segons_per_km):
        return "0:00"
    minuts = int(segons_per_km // 60)
    segons = int(segons_per_km % 60)
    return f"{minuts}:{segons:02d}"


def format_ritme_seg(descripcio):
    match = re.search(r"(\d+):(\d{2})", descripcio)
    if match:
        minuts, segons = map(int, match.groups())
        return (minuts * 60) + segons
    return None


def calcular_medalla_obtinguda(exercici):
    if (
        not exercici.completat
        or exercici.distance_meters <= 0
        or exercici.duration_seconds <= 0
    ):
        return None

    ritme_real_segons_km = exercici.duration_seconds / (
        exercici.distance_meters / 1000.0
    )
    objectius = exercici.objectius.all()
    obj_or = objectius.filter(categoria="OR").first()
    obj_plata = objectius.filter(categoria="PLA").first()
    obj_bronze = objectius.filter(categoria="BRO").first()

    if obj_or:
        if "Completar l'exercici." in obj_or.descripcio:
            return "OR"

        segons_requerits_or = format_ritme_seg(obj_or.descripcio)
        if segons_requerits_or and ritme_real_segons_km <= segons_requerits_or:
            return "OR"

    if obj_plata:
        if "Completar l'exercici." in obj_plata.descripcio:
            return "PLA"

        segons_requerits_plata = format_ritme_seg(obj_plata.descripcio)
        if segons_requerits_plata and ritme_real_segons_km <= segons_requerits_plata:
            return "PLA"

    if obj_bronze:
        return "BRO"

    return None


def calcular_recompensa(medalla, exercici):
    if medalla is None:
        return 0

    objectius = exercici.objectius.all()
    obj_or = objectius.filter(categoria="OR").first()
    obj_plata = objectius.filter(categoria="PLA").first()
    obj_bronze = objectius.filter(categoria="BRO").first()
    recompensa = obj_bronze.recompensa

    if medalla != "BRO":
        recompensa += obj_plata.recompensa
        if medalla != "PLA":
            recompensa += obj_or.recompensa
        else:
            return recompensa
    return recompensa


# todo: MAYBE implementar més objectius depenent de tipusExercici
# todo: MAYBE implementar més objectius depenent de distància de ruta
def create_objectius(usuari):
    historico = Exercici.objects.filter(
        usuari=usuari, completat=True, duration_seconds__gt=0, distance_meters__gt=0
    )

    # no me fio del average speed xdd
    historico_ritmos = historico.annotate(
        ritme_segons_km=ExpressionWrapper(
            F("duration_seconds") / (F("distance_meters") / 1000.0),
            output_field=FloatField(),
        )
    )

    # Bronze: completar
    req_bronze = "Completar l'exercici."

    # Plata: promig històric
    fa_tres_mesos = timezone.now() - timedelta(days=90)
    hi_ha_exercicis_antics = historico_ritmos.filter(
        created_at__lt=fa_tres_mesos
    ).exists()
    hi_ha_exercicis_recents = historico_ritmos.filter(
        created_at__gte=fa_tres_mesos
    ).exists()

    # si l'usuari no ha completat el pla inicial o no ha sigut actiu, completar exercici
    if historico_ritmos.count() < 6 or not hi_ha_exercicis_recents:
        req_plata = "Completar l'exercici."
    else:
        # canviar a últims tres mesos si fa exercicis fa més temps i ha sigut actiu recentment
        if hi_ha_exercicis_antics and hi_ha_exercicis_recents:
            ritmos_filtrados_plata = historico_ritmos.filter(
                created_at__gte=fa_tres_mesos
            )
            promig_segons_km = ritmos_filtrados_plata.aggregate(Avg("ritme_segons_km"))[
                "ritme_segons_km__avg"
            ]
            ritme_formatejat = format_ritme_min_km(promig_segons_km)
            req_plata = (
                f"Completar l'exercici superant el teu ritme promig recent:"
                f" {ritme_formatejat}."
            )
        else:
            promig_segons_km = historico_ritmos.aggregate(Avg("ritme_segons_km"))[
                "ritme_segons_km__avg"
            ]
            ritme_formatejat = format_ritme_min_km(promig_segons_km)
            req_plata = (
                f"Completar l'exercici superant el teu ritme promig històric: "
                f" {ritme_formatejat}."
            )

    # Or: Top 25% superior de ritmes
    # si l'usuari no ha completat el pla inicial, completar exercici
    if historico_ritmos.count() < 6 or not hi_ha_exercicis_recents:
        req_or = "Completar l'exercici."
    else:
        # canviar a últims tres mesos si fa exercicis fa més temps i ha sigut actiu recentment
        if hi_ha_exercicis_antics and hi_ha_exercicis_recents:
            ritmos_filtrados_or = historico_ritmos.filter(created_at__gte=fa_tres_mesos)
            llista_ritmos = list(
                ritmos_filtrados_or.values_list("ritme_segons_km", flat=True)
            )
            tall_top_25_segons = np.percentile(llista_ritmos, 25)
            ritme_or_formatejat = format_ritme_min_km(tall_top_25_segons)
            req_or = "Completar l'exercici superant el ritme: " + ritme_or_formatejat
        else:
            llista_ritmos = list(
                historico_ritmos.values_list("ritme_segons_km", flat=True)
            )
            tall_top_25_segons = np.percentile(llista_ritmos, 25)
            ritme_or_formatejat = format_ritme_min_km(tall_top_25_segons)
            req_or = "Completar l'exercici superant el ritme: " + ritme_or_formatejat

    obj_bronze = ObjectiuExercici.objects.create(
        categoria="BRO", descripcio=req_bronze, recompensa=10
    )

    obj_plata = ObjectiuExercici.objects.create(
        categoria="PLA", descripcio=req_plata, recompensa=20
    )

    obj_or = ObjectiuExercici.objects.create(
        categoria="OR", descripcio=req_or, recompensa=30
    )

    return [obj_bronze, obj_plata, obj_or]
