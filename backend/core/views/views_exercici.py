from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Exercici, Usuari
from ..serializers import ExerciciSerializer
from ..models import TemplateExercici
from ..serializers import TemplateExerciciSerializer
from ..services.gamificacio import gestionar_puntuacio_i_insignies
from ..services.objectius_exercici import create_objectius


class ExerciciViewSet(viewsets.ModelViewSet):
    queryset = Exercici.objects.all()
    serializer_class = ExerciciSerializer
    permission_classes = [IsAuthenticated]

    def _get_usuari_from_token(self, request):
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    def get_queryset(self):
        # Listar solo los del usuario actual
        usuari = self._get_usuari_from_token(self.request)
        return Exercici.objects.filter(usuari=usuari)

    def perform_create(self, serializer):
        # Al guardar, le pegamos el usuario que viene del token
        usuari = self._get_usuari_from_token(self.request)
        serializer.save(usuari=usuari)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        ja_completat = instance.completat

        response = super().update(request, *args, **kwargs)

        # Si l'exercici s'ha marcat com a completat en aquesta crida
        if request.data.get("completat") is True and not ja_completat:
            usuari = self._get_usuari_from_token(request)
            noves_insignies = gestionar_puntuacio_i_insignies(usuari, exercici=instance)

            response.data["new_badges"] = noves_insignies
            response.data["points_earned"] = usuari.punts
            response.data["current_streak"] = usuari.ratxa

        return response

    @action(detail=True, methods=["post"], url_path="inicialitzar-objectius")
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


class TemplateExerciciViewSet(viewsets.ModelViewSet):
    queryset = TemplateExercici.objects.all().prefetch_related("instancies_exercici")
    serializer_class = TemplateExerciciSerializer
