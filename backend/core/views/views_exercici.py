from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Exercici, Usuari, PuntLog
from ..serializers import ExerciciSerializer
from ..models import TemplateExercici
from ..serializers import TemplateExerciciSerializer
from ..services.gamificacio import gestionar_puntuacio_i_insignies
from ..services.objectius_exercici import (
    create_objectius,
    calcular_medalla_obtinguda,
    calcular_recompensa,
)


class ExerciciViewSet(viewsets.ModelViewSet):
    queryset = Exercici.objects.all()
    serializer_class = ExerciciSerializer
    permission_classes = [IsAuthenticated]

    def _aplicar_premis(self, exercici, usuari):
        medalla = calcular_medalla_obtinguda(exercici)
        airCoins = calcular_recompensa(medalla, exercici)
        exercici.medalla_obtinguda = medalla
        exercici.save()

        noves_insignies = gestionar_puntuacio_i_insignies(usuari, exercici=exercici)

        bonus_pla = 0
        if exercici.pla:
            pendents = exercici.pla.plans_entrenament.filter(completat=False).count()
            if pendents == 0 and exercici.pla.actiu:
                bonus_pla = 500
                usuari.punts += bonus_pla
                usuari.save()
                exercici.pla.actiu = False
                exercici.pla.save()

        return {
            "medalla": medalla,
            "airCoins_guanyats": airCoins,
            "new_badges": noves_insignies,
            "points_earned_total": usuari.punts,
            "current_streak": usuari.ratxa,
            "titols_pendents": usuari.titols_pendents,
            "bonus_final_pla": bonus_pla,
        }

    def _get_usuari_from_token(self, request):
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    def get_queryset(self):
        # Listar solo los del usuario actual
        usuari = self._get_usuari_from_token(self.request)
        return Exercici.objects.filter(usuari=usuari)

    @extend_schema(summary="Crear ruta lliure o sessió de calendari")
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuari = self._get_usuari_from_token(request)
        instance = serializer.save(usuari=usuari)

        if not instance.pla:
            from ..services.objectius_exercici import create_objectius

            objectius = create_objectius(usuari)
            if objectius:
                instance.objectius.set(objectius)

        response_data = serializer.data

        if request.data.get("completat") is True:
            premis = self._aplicar_premis(instance, usuari)
            response_data = self.get_serializer(instance).data
            response_data.update(premis)

        return Response(response_data, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Finalitzar exercici i rebre premis (Workflow principal)",
        description="Envia un PATCH amb completat: true i les dades de la ruta per rebre AirCoins i Punts.",
        responses={
            200: inline_serializer(
                name="ExerciciFinalitzatResponse",
                fields={
                    "id": serializers.IntegerField(),
                    "medalla_obtinguda": serializers.CharField(),
                    "airCoins_guanyats": serializers.IntegerField(),
                    "points_earned_total": serializers.IntegerField(),
                    "current_streak": serializers.IntegerField(),
                    "new_badges": serializers.ListField(),
                    "bonus_final_pla": serializers.IntegerField(),
                    "titols_pendents": serializers.IntegerField(),
                },
            )
        },
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ja_completat = instance.completat

        response = super().update(request, *args, **kwargs)

        # Si l'exercici s'ha marcat com a completat en aquesta crida
        if request.data.get("completat") is True and not ja_completat:
            usuari = self._get_usuari_from_token(request)
            instance.refresh_from_db()
            premis = self._aplicar_premis(instance, usuari)
            response = self.get_serializer(instance).data
            response.data.update(premis)
        return response

    @extend_schema(request=None, responses={200: ExerciciSerializer})
    @action(
        detail=True,
        methods=["post"],
        url_path="inicialitzar-objectius",
    )
    def inicialitzar_objectius(self, request, pk=None):
        exercici = self.get_object()
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        objectius = create_objectius(usuari)

        if not objectius:
            return Response(
                {"error": "No s'han pogut generar els objectius"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        exercici.objectius.set(objectius)
        serializer = ExerciciSerializer(exercici)

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="finalitzar-exercici")
    def finalitzar_exercici(self, request, pk=None):
        exercici = self.get_object()
        usuari = self._get_usuari_from_token(request)

        avg_speed_kmh = request.data.get("avg_speed_kmh", 0)

        if avg_speed_kmh and float(avg_speed_kmh) > 50:
            exercici.completat = False
            exercici.save()
            return Response(
                {
                    "error": "Activitat no vàlida",
                    "motiu": "S'ha detectat una velocitat mitjana superior a 50 km/h. Possible ús de vehicle de motor.",
                    "valid_per_punts": False,
                },
                status=status.HTTP_200_OK,
            )

        exercici.duration_seconds = request.data.get("duration_seconds")
        exercici.distance_meters = request.data.get("distance_meters")
        exercici.completat = request.data.get("completat")
        exercici.avg_speed_kmh = avg_speed_kmh
        exercici.save()

        medalla = calcular_medalla_obtinguda(exercici)
        airCoins = calcular_recompensa(medalla, exercici)

        exercici.medalla_obtinguda = medalla
        exercici.save()

        if exercici.pla:
            pendents = exercici.pla.plans_entrenament.filter(completat=False).count()

            if pendents == 0 and exercici.pla.actiu:
                plan_completed_bonus = 500
                usuari.punts += plan_completed_bonus
                usuari.save()

                PuntLog.objects.create(
                    usuari=usuari,
                    quantitat=plan_completed_bonus,
                    motiu="Enhorabona! Has completat el teu pla d'entrenament.",
                )

                exercici.pla.actiu = False
                exercici.pla.save()

        serializer = ExerciciSerializer(exercici)
        data = serializer.data
        data["airCoins_guanyats"] = airCoins

        return Response(data, status=status.HTTP_200_OK)


class TemplateExerciciViewSet(viewsets.ModelViewSet):
    queryset = TemplateExercici.objects.all().prefetch_related("instancies_exercici")
    serializer_class = TemplateExerciciSerializer
