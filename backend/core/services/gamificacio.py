from django.db import models
from datetime import date, timedelta
from ..models import UsuariInsignia, Insignia, PuntLog
from django.db.models import Sum

def gestionar_puntuacio_i_insignies(usuari, exercici=None):
    # S'executa en acabar un exercici, retorna les insignies guanyades amb l'exercici
    avui = date.today()
    ahir = avui - timedelta(days=1)

    if usuari.ultima_activitat == ahir:
        usuari.ratxa += 1
    elif usuari.ultima_activitat != avui:
        usuari.ratxa = 1

    usuari.ultima_activitat = avui
    usuari.save()

    if exercici:
        punts_base = 50
        distancia_km = exercici.distance_meters / 1000
        punts_distancia = int(distancia_km * 10)

        total_exercici = punts_base + punts_distancia

        usuari.punts += total_exercici
        usuari.save()

        PuntLog.objects.create(
            usuari=usuari,
            quantitat=total_exercici,
            motiu=f"Exercici completat: {distancia_km:.2f} km"
        )

    ja_guanyades_ids = usuari.insignies_guanyades.values_list("insignia_id", flat=True)
    pendents = Insignia.objects.exclude(id__in=ja_guanyades_ids)

    noves_badges = []

    total_dist = sum(e.distance_meters for e in usuari.exercicis.filter(completat=True)) / 1000
    total_ex = usuari.exercicis.filter(completat=True).count()

    for ins in pendents:
        guanyada = False
        if ins.tipus == "RATXA" and usuari.ratxa >= ins.valor_requerit:
            guanyada = True
        elif ins.tipus == "DISTANCIA" and total_dist >= ins.valor_requerit:
            guanyada = True
        elif ins.tipus == "REPTES_TOTALS" and total_ex >= ins.valor_requerit:
            guanyada = True

        if guanyada:
            UsuariInsignia.objects.create(usuari=usuari, insignia=ins)
            noves_badges.append({
                "id": ins.id,
                "nom": ins.nom,
                "descripcio": ins.descripcio,
                "nom_icona": ins.nom_icona
            })

    return noves_badges