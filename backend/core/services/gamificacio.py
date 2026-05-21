from django.db.models import Sum
from datetime import date
from ..models import UsuariInsignia, Insignia, PuntLog, Exercici
import sys


def gestionar_puntuacio_i_insignies(usuari, exercici=None):
    # S'executa en acabar un exercici, retorna les insignies guanyades amb l'exercici
    avui = date.today()
    usuari.refresh_from_db()

    usuari.verificar_i_resetejar_ratxa()

    if usuari.ultima_activitat != avui:
        usuari.ratxa += 1
        usuari.ultima_activitat = avui
        usuari.save()

    if exercici:
        punts_base = 50
        dist_m = exercici.distance_meters if exercici.distance_meters else 0
        distancia_km = dist_m / 1000
        punts_distancia = int(distancia_km * 10)

        usuari.punts += punts_base + punts_distancia
        usuari.save()

        PuntLog.objects.create(
            usuari=usuari,
            quantitat=punts_base + punts_distancia,
            motiu=f"Exercici completat: {distancia_km:.2f} km",
        )

    fita_actual = usuari.punts // 100  # Exemple: 250 punts // 100 = 2
    if fita_actual > usuari.ultim_milestone_titols:
        diferencia = fita_actual - usuari.ultim_milestone_titols
        usuari.titols_pendents += diferencia
        usuari.ultim_milestone_titols = fita_actual

    usuari.save()

    qs_anteriors = Exercici.objects.filter(usuari=usuari, completat=True)
    if exercici:
        qs_anteriors = qs_anteriors.exclude(pk=exercici.pk)

    dist_anterior_m = (
        qs_anteriors.aggregate(Sum("distance_meters"))["distance_meters__sum"] or 0
    )

    # SUMEM EL QUE ACABEM DE FER ARA (Truc per saltar-nos el delay de la BD)
    total_dist_acumulada_km = (dist_anterior_m / 1000) + distancia_km
    total_punts = usuari.punts
    total_ratxa = usuari.ratxa

    # Mirem quines medalles NO té
    ja_guanyades_ids = UsuariInsignia.objects.filter(usuari=usuari).values_list(
        "insignia_id", flat=True
    )
    pendents = Insignia.objects.exclude(id__in=ja_guanyades_ids)

    noves_badges = []

    for ins in pendents:
        guanyada = False
        t = str(ins.tipus).upper().strip()
        v = ins.valor_requerit

        if t == "PUNTS" and total_punts >= v:
            guanyada = True
        elif t == "DISTANCIA" and total_dist_acumulada_km >= v:
            guanyada = True
        elif t == "RATXA" and total_ratxa >= v:
            guanyada = True

        if guanyada:
            UsuariInsignia.objects.create(usuari=usuari, insignia=ins)
            noves_badges.append(
                {
                    "id": ins.id,
                    "nom": ins.nom,
                    "descripcio": ins.descripcio,
                    "icona": ins.icona.url if ins.icona else None,
                }
            )

    return noves_badges
