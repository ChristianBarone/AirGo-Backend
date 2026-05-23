from datetime import datetime, timedelta
from django.utils import timezone
from ..models import Exercici  # Solo importamos Exercici


def create_ini_plan(usuari, pla):
    templates_ini = pla.templates.all()

    if not templates_ini.exists():
        return []

    total_entrenamientos = 6
    ejercicios_creados = []

    # 3. Creación cíclica
    for i in range(total_entrenamientos):
        template = templates_ini[i % templates_ini.count()]

        # Creamos el ejercicio usando SOLO los campos que existen en tu modelo actual
        nuevo_ejercicio = Exercici.objects.create(
            usuari=usuari,
            template=template,  # ← añadir esto
            dataInici=timezone.now(),  # ← añadir esto
            distanciaFeta=0.0,
            completat=False,
            distance_meters=0.0,
            duration_seconds=0,
            avg_speed_kmh=0.0,
            route_points=[],
        )

        ejercicios_creados.append(nuevo_ejercicio)

    # Actualizamos los datos del plan
    pla.diesDurada = 14
    pla.numEntrenamentsSetmanals = 3
    pla.save()
    usuari.plans.add(pla)

    return ejercicios_creados


def create_plan(usuari, pla):
    templates = pla.templates.all()
    if not templates.exists():
        return []

    # Usar nivell del plan en lugar de dificultatPla del usuario
    if pla.nivell == 1:
        num_ejercicios = 6
    elif pla.nivell == 2:
        num_ejercicios = 9
    else:
        num_ejercicios = 12

    ejercicios_creados = []
    for i in range(num_ejercicios):
        template = templates[i % templates.count()]
        nuevo_ejercicio = Exercici.objects.create(
            usuari=usuari,
            template=template,
            dataInici=timezone.now(),
            distanciaFeta=0.0,
            completat=False,
            distance_meters=0.0,
            duration_seconds=0,
            avg_speed_kmh=0.0,
            route_points=[],
        )
        ejercicios_creados.append(nuevo_ejercicio)

    pla.diesDurada = 21
    pla.numEntrenamentsSetmanals = num_ejercicios // 3
    pla.save()
    usuari.plans.add(pla)

    return ejercicios_creados
