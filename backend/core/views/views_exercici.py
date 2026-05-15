from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import Exercici, Usuari
from ..serializers import ExerciciSerializer
from ..models import TemplateExercici
from ..serializers import TemplateExerciciSerializer


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

    @action(detail=True, methods=["patch"], url_path="update-sensacio")
    def update_sensacio(self, request, pk=None):
        exercici = self.get_object()

        data = {
            "sensacio": request.data.get("sensacio", exercici.sensacio),
            "comentari_sensacio": request.data.get(
                "comentari_sensacio", exercici.comentari_sensacio
            ),
        }

        serializer = ExerciciSerializer(exercici, data=data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TemplateExerciciViewSet(viewsets.ModelViewSet):
    queryset = TemplateExercici.objects.all()
    serializer_class = TemplateExerciciSerializer
