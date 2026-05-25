from datetime import timedelta, datetime
from django.utils import timezone
from ..models import Exercici, TemplateExercici
from .objectius_exercici import create_objectius


def create_plan_logic(usuari, pla):
    exercicis_per_setmana = {1: 2, 2: 4, 3: 6}
    num_sessions_setmana = exercicis_per_setmana.get(pla.nivell, 2)
    disponibilitat = sorted(pla.diesSetmana)
    if not disponibilitat:
        return [0, 1, 2, 3, 4, 5, 6]
    sessions_reals = min(num_sessions_setmana, len(disponibilitat))
    pas = len(disponibilitat) / sessions_reals
    dies_triats = [disponibilitat[int(i * pas)] for i in range(sessions_reals)]
    pla.diesSetmana = dies_triats
    pla.numEntrenamentsSetmanals = sessions_reals
    pla.dataFi = pla.dataInici + timedelta(days=pla.diesDurada)
    pla.save()

    templates = TemplateExercici.objects.filter(
        dificutat={1: "PRI", 2: "INT", 3: "AVA"}.get(pla.nivell, "INT"),
        tipusExercici=pla.esport,
    )
    if not templates.exists():
        templates = TemplateExercici.objects.filter(tipusExercici=pla.esport)

    template_list = list(templates)
    if not template_list:
        return []

    pla.templates.set(template_list)
    ejercicios_creados = []
    entrenaments_totals_comptador = 0

    for i in range(pla.diesDurada):
        data_actual = pla.dataInici + timedelta(days=i)

        if data_actual.weekday() in dies_triats:
            template = template_list[entrenaments_totals_comptador % len(template_list)]
            dt_aware = timezone.make_aware(
                datetime.combine(data_actual, datetime.min.time())
            )

            nou_ex = Exercici.objects.create(
                usuari=usuari,
                pla=pla,
                template=template,
                dataInici=dt_aware,
                completat=False,
            )

            objectius = create_objectius(usuari)
            if objectius:
                nou_ex.objectius.set(objectius)

            ejercicios_creados.append(nou_ex)
            entrenaments_totals_comptador += 1

    pla.numEntrenamentsSetmanals = sessions_reals
    pla.dataFi = pla.dataInici + timedelta(days=pla.diesDurada)
    pla.save()
    usuari.plans.add(pla)
    return ejercicios_creados


def create_ini_plan(usuari, pla):
    pla.diesDurada = 14
    pla.nivell = 1
    if not pla.diesSetmana:
        pla.diesSetmana = [0, 1, 2, 3, 4, 5, 6]
    pla.save()
    return create_plan_logic(usuari, pla)


def create_plan(usuari, pla):
    return create_plan_logic(usuari, pla)
