from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action

from ..models import MissioUsuari, MissioPermanent, Usuari
from ..serializers import MissioUsuariSerializer, MissioPermanentSerializer
from ..services.missions_permanents import verificar_i_actualitzar_missions, inicialitzar_missions_usuari_nou


class MissionsViewSet(viewsets.GenericViewSet):
    queryset = MissioUsuari.objects.all()
    serializer_class = MissioUsuariSerializer
    permission_classes = [IsAuthenticated]

    def _get_usuari_from_token(self, request):
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    def get_queryset(self):
        usuari = self._get_usuari_from_token(self.request)
        return MissioUsuari.objects.filter(usuari=usuari).select_related('missio')

    def list(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        if not self.get_queryset().exists():
            inicialitzar_missions_usuari_nou(usuari)

        verificar_i_actualitzar_missions(usuari)

        queryset = self.get_queryset().order_by('missio__metrica', 'missio__fase_metrica')
        serializer = MissioUsuariSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """
        Crea una nueva misión permanente en el sistema global.
        No dejar al usuario común hacer esta petición
        """
        serializer = MissioPermanentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)