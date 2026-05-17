from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Exercici, Usuari
from ..serializers import ExerciciSerializer
from ..models import TemplateExercici
from ..serializers import TemplateExerciciSerializer
from ..services.gamificacio import gestionar_puntuacio_i_insignies


class ExerciciViewSet(viewsets.ModelViewSet):
    queryset = Exercici.objects.all()
    serializer_class = ExerciciSerializer
    permission_classes = [IsAuthenticated]

    def _get_usuari_from_token(self, request):
        google_id = request.auth.get('google_id')
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
        if request.data.get('completat') is True and not ja_completat:
            usuari = self._get_usuari_from_token(request)
            noves_insignies = gestionar_puntuacio_i_insignies(usuari, exercici=instance)

            response.data["new_badges"] = noves_insignies
            response.data["points_earned"] = usuari.punts
            response.data["current_streak"] = usuari.ratxa

        return response

class TemplateExerciciViewSet(viewsets.ModelViewSet):
    queryset = TemplateExercici.objects.all()
    serializer_class = TemplateExerciciSerializer