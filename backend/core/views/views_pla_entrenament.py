from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from ..models import PlaEntrenament, Usuari
from ..serializers import PlaEntrenamentSerializer
from ..services.plans_entrenament import create_ini_plan
from ..services.plans_entrenament import create_plan



class PlaEntrenamentViewSet(viewsets.ModelViewSet):
    queryset = PlaEntrenament.objects.all().prefetch_related('templates__instancies_exercici')
    serializer_class = PlaEntrenamentSerializer

    # ELIMINAR LUEGO (logica repetida)
    def _get_usuari_from_token(self, request):
        google_id = request.auth.get("google_id")  # <-- leer del token
        return Usuari.objects.get(google_id=google_id)

    @action(detail=True, methods=['post'], url_path='inicialitzar-pla-ini')
    def inicialitzar_pla_ini(self, request, pk=None):
        #Endpoint: POST /api/pla-entrenament/{id}/inicialitzar-pla-ini/
        # 1. Obtenemos el plan y el usuario
        pla = self.get_object()

        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        # 2. Llamamos a tu función lógica
        ejercicios = create_ini_plan(usuari, pla)

        if not ejercicios:
            return Response(
                {"error": "No s'han trobat templates amb el nom 'ini' en aquest pla"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Respondemos con el plan actualizado y sus nuevos ejercicios
        pla_refresc = PlaEntrenament.objects.prefetch_related('templates__instancies_exercici').get(pk=pla.pk)
        serializer = self.get_serializer(pla_refresc)
        return Response({
            "message": "Pla d'iniciació creat correctament amb 6 exercicis.",
            "plan": serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='inicialitzar-pla-seg')
    def inicialitzar_pla_seg(self, request, pk=None):
        # Endpoint: POST /api/pla-entrenament/{id}/inicialitzar-pla-seg/
        # 1. Obtenemos el plan y el usuario
        pla = self.get_object()

        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        # 2. Llamamos a tu función lógica
        ejercicios = create_plan(usuari, pla)

        if not ejercicios:
            return Response(
                {"error": "No s'han trobat templates"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Respondemos con el plan actualizado y sus nuevos ejercicios
        pla_refresc = PlaEntrenament.objects.prefetch_related('templates__instancies_exercici').get(pk=pla.pk)
        serializer = self.get_serializer(pla_refresc)
        return Response({
            "message": f"Pla de seguiment creat correctament amb {len(ejercicios)} exercicis.",
            "plan": serializer.data
        }, status=status.HTTP_201_CREATED)