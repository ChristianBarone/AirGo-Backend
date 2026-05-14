from datetime import datetime, timedelta
from django.utils import timezone
from ..models import Exercici, SensacioExercici


#     Filtra templates que contienen 'ini',
#     Fuerza un plan de 2 semanas con 3 sesiones/semana
#     Habrán 6 templates, se creará 1 ejercicio usando cada uno
def create_ini_plan(usuari, pla):
    # 1. Filtrar solo los templates del plan que contienen "ini" en el nombre
    templates_ini = pla.templates.filter(nom__icontains="ini")

    if not templates_ini.exists():
        return []

    # 2. Forzamos los parámetros del plan (2 semanas * 3 ejercicios)
    total_entrenamientos = 6
    ejercicios_creados = []

    # MAYBE: preguntar en el cuestionario dias y horas preferentes
    # Plan comienza a las 8am
    fecha_inicio_plan = (timezone.now() + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
    # Siempre Semana 1: Lun, Mie, Vie; Semana 2: Lun, Mie, Vie
    dias_relativos = [0, 2, 4, 7, 9, 11]

    # 3. Creación cíclica
    for i in range(total_entrenamientos):
        template = templates_ini[i % templates_ini.count()]

        # 3. Calculamos la fecha específica para este ejercicio
        fecha_ejercicio = fecha_inicio_plan + timedelta(days=dias_relativos[i])

        # 4. Generar ejercicio
        nuevo_ejercicio = Exercici.objects.create(
            usuari=usuari,
            template = template,
            distance_meters=0.0,
            duration_seconds=0,
            avg_speed_kmh=0.0,
            route_points=[],
            dataIni = fecha_ejercicio,
            sensacio=SensacioExercici.NORMAL,
            comentari_sensacio=""
        )
        ejercicios_creados.append(nuevo_ejercicio)

    # Actualizamos los datos del plan
    pla.diesDurada = 14
    pla.numEntrenamentsSetmanals = 3
    pla.save()
    usuari.plans.add(pla)

    return ejercicios_creados

#     Plan de 3 semanas
#     Entrenamientos por semana influenciado por dificultatPla
def create_plan(usuari, pla):
    templates = pla.templates.all()
    if not templates.exists():
        return []

    # siempre empieza a las 8 AM
    fecha_inicio_plan = (timezone.now() + timedelta(days=1)).replace(
        hour=8, minute=0, second=0, microsecond=0
    )

    # NOR es default
    dias_relativos = [0, 2, 4, 7, 9, 11, 14, 16, 18]
    # 2. Asignación de días según dificultad
    dificultad = getattr(usuari, 'dificultatPla', 'NOR')

    if dificultad == "REL":
        dias_relativos = [0, 3, 7, 10, 14, 17]
    elif dificultad == "INT":
        dias_relativos = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 18, 19]

    ejercicios_creados = []


    # 3. Creación cíclica
    for i in range(len(dias_relativos)):
        # TODO: filtrar por nombre del template cada iteracion para tener diferentes tipos de ejercicios
        template = templates[i]

        # 3. Calculamos la fecha específica para este ejercicio
        fecha_ejercicio = fecha_inicio_plan + timedelta(days=dias_relativos[i])

        # 4. Generar ejercicio
        nuevo_ejercicio = Exercici.objects.create(
            usuari=usuari,
            template = template,
            distance_meters=0.0,
            duration_seconds=0,
            avg_speed_kmh=0.0,
            route_points=[],
            dataIni = fecha_ejercicio,
            sensacio=SensacioExercici.NORMAL,
            comentari_sensacio=""
        )
        ejercicios_creados.append(nuevo_ejercicio)

    # Actualizamos los datos del plan
    pla.diesDurada = 21
    pla.save()
    pla.numEntrenamentsSetmanals = len(dias_relativos) // 3
    usuari.plans.add(pla)

    return ejercicios_creados