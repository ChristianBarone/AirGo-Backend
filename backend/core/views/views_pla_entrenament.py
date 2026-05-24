from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from ..models import PlaEntrenament, Usuari
from ..serializers import PlaEntrenamentSerializer, ExerciciSerializer
from ..services.plans_entrenament import create_ini_plan, create_plan


class PlaEntrenamentViewSet(viewsets.ModelViewSet):
    queryset = PlaEntrenament.objects.all().prefetch_related(
        "templates__instancies_exercici"
    )
    serializer_class = PlaEntrenamentSerializer

    def _get_usuari_from_token(self, request):
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    @extend_schema(
        summary="Crear un nou pla d'entrenament complet",
        description="Envia els detalls del pla. El backend calcularà la data de fi i generarà els exercicis automàticament.",
        responses={
            201: inline_serializer(
                name="PlaCreateDetailedResponse",
                fields={
                    "status": serializers.CharField(),
                    "message": serializers.CharField(),
                    "plan": PlaEntrenamentSerializer(),
                    "exercicis": ExerciciSerializer(
                        many=True
                    ),  # <--- Això farà que surtin a l'exemple!
                    "num_exercicis_creats": serializers.IntegerField(),
                },
            )
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuari = self._get_usuari_from_token(request)
        pla = serializer.save(usuari=usuari)

        is_initial = request.data.get("is_initial", False)
        if is_initial:
            ejercicios = create_ini_plan(usuari, pla)
        else:
            ejercicios = create_plan(usuari, pla)

        ex_serializer = ExerciciSerializer(ejercicios, many=True)

        return Response(
            {
                "status": "success",
                "plan": self.get_serializer(pla).data,
                "exercicis": ex_serializer.data,
                "num_exercicis_creats": len(ejercicios),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="inicialitzar-pla-ini")
    def inicialitzar_pla_ini(self, request, pk=None):
        pla = self.get_object()
        usuari = self._get_usuari_from_token(request)

        ejercicios = create_ini_plan(usuari, pla)
        if not ejercicios:
            return Response(
                {
                    "error": "No s'han trobat templates (Comprova si has creat templates a la BD de Caminar/Bici)"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(pla)
        return Response(
            {
                "message": "Pla d'iniciació creat correctament.",
                "plan": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="inicialitzar-pla-seg")
    def inicialitzar_pla_seg(self, request, pk=None):
        pla = self.get_object()
        usuari = self._get_usuari_from_token(request)

        ejercicios = create_plan(usuari, pla)
        if not ejercicios:
            return Response(
                {"error": "No s'han trobat templates per a aquest esport i nivell."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(pla)
        return Response(
            {
                "message": f"Pla creat correctament amb {len(ejercicios)} exercicis.",
                "plan": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )
