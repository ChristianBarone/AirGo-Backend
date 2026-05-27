from rest_framework import viewsets, filters, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
    inline_serializer,
)
from drf_spectacular.types import OpenApiTypes

from ..models import (
    Usuari,
    UsuariTitol,
    UsuariRuta,
    Amistat,
    EstatAmistat,
    Titol,
    PlaEntrenament,
)
from ..serializers import (
    UsuariSerializer,
    UsuariTitolSerializer,
    UsuariRutaSerializer,
    AmistatSerializer,
    UsuariInsigniaSerializer,
    PuntLogSerializer,
    PlaEntrenamentSerializer,
    InsigniaSerializer,
)
from django.db import models as django_models

from ..services.gamificacio import gestionar_puntuacio_i_insignies
from ..services.firebase import send_push_notification


@extend_schema_view(
    list=extend_schema(
        tags=["Usuaris"],
        summary="Listar todos los usuarios",
        description="Devuelve la lista de todos los usuarios. Permite búsqueda por `username` con `?search=`.",
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Filtrar por username",
                required=False,
            )
        ],
    ),
    retrieve=extend_schema(
        tags=["Usuaris"],
        summary="Obtener un usuario por ID",
    ),
    create=extend_schema(
        tags=["Usuaris"],
        summary="Crear un usuario",
    ),
    update=extend_schema(
        tags=["Usuaris"],
        summary="Actualizar un usuario (PUT)",
    ),
    partial_update=extend_schema(
        tags=["Usuaris"],
        summary="Actualizar parcialmente un usuario (PATCH)",
    ),
    destroy=extend_schema(
        tags=["Usuaris"],
        summary="Eliminar un usuario por ID",
    ),
)
class UsuariViewSet(viewsets.ModelViewSet):
    queryset = Usuari.objects.all()
    serializer_class = UsuariSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username"]

    # ── Helper privado ────────────────────────────────────────────────────────

    def _get_usuari_from_token(self, request):
        """Lee el google_id del JWT y devuelve el Usuari correspondiente."""
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    # ── Acciones custom ───────────────────────────────────────────────────────

    @extend_schema(
        tags=["Usuaris"],
        summary="Títulos desbloqueados de un usuario",
        description="Devuelve todos los títulos que ha desbloqueado el usuario indicado por `pk`.",
        responses={
            200: UsuariTitolSerializer(many=True),
            404: OpenApiResponse(description="Usuario no encontrado"),
        },
    )
    @action(detail=True, methods=["get"], url_path="titols", url_name="titols")
    def get_titols(self, request, pk=None):
        try:
            usuari = Usuari.objects.get(pk=pk)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        titols = UsuariTitol.objects.filter(usuari=usuari).select_related("titol")
        serializer = UsuariTitolSerializer(titols, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Usuaris · Me"],
        summary="Cambiar foto de perfil",
        description=(
            "Actualiza la foto de perfil del usuario autenticado. "
            "Enviar como `multipart/form-data` con el campo `profile_pic`."
        ),
        request=inline_serializer(
            name="ProfilePicRequest",
            fields={"profile_pic": serializers.ImageField(help_text="Imagen ≤ 2 MB")},
        ),
        responses={
            200: UsuariSerializer,
            404: OpenApiResponse(description="Usuario no encontrado"),
        },
    )
    @action(
        detail=False,
        methods=["patch"],
        url_path="me/profile-pic",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsAuthenticated],
    )
    def change_profile_pic(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        usuari.profile_pic = request.data.get("profile_pic")
        usuari.save()
        serializer = self.get_serializer(usuari)
        return Response(serializer.data)

    @extend_schema(
        tags=["Usuaris · Me"],
        summary="Eliminar cuenta propia",
        description="Elimina permanentemente la cuenta del usuario autenticado y su Django User asociado.",
        responses={
            204: OpenApiResponse(description="Cuenta eliminada correctamente"),
            404: OpenApiResponse(description="Usuario no encontrado"),
        },
    )
    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path="me",
    )
    def delete_account(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        usuari.delete()
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Usuaris · Me"],
        summary="Obtener perfil propio",
        description="Devuelve los datos del perfil del usuario autenticado.",
        responses={
            200: UsuariSerializer,
            404: OpenApiResponse(description="Usuario no encontrado"),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/profile",
        url_name="me-profile",
    )
    def retrieve_profile(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
            usuari.verificar_i_resetejar_ratxa()
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        serializer = self.get_serializer(usuari)
        return Response(serializer.data)

    @extend_schema(
        tags=["Usuaris · Me · Rutas"],
        summary="Obtener rutas guardadas",
        description="Devuelve todas las rutas guardadas por el usuario autenticado.",
        responses={
            200: UsuariRutaSerializer(many=True),
            404: OpenApiResponse(description="Usuario no encontrado"),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/routes",
        url_name="me-routes",
    )
    def get_saved_routes(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        rutes = UsuariRuta.objects.filter(usuari=usuari).select_related("route")
        serializer = UsuariRutaSerializer(rutes, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Usuaris · Me · Rutas"],
        summary="Guardar una ruta",
        description="Asocia una ruta existente al usuario autenticado. Devuelve 409 si ya estaba guardada.",
        request=inline_serializer(
            name="SaveRouteRequest",
            fields={
                "route_id": serializers.IntegerField(
                    help_text="ID de la ruta a guardar"
                )
            },
        ),
        responses={
            201: OpenApiResponse(description="Ruta guardada correctamente"),
            400: OpenApiResponse(description="Error de validación"),
            404: OpenApiResponse(description="Usuario no encontrado"),
            409: OpenApiResponse(description="La ruta ya estaba guardada"),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="me/routes/save",
        url_name="me-routes-save",
    )
    def save_route(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = UsuariRutaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        route = serializer.validated_data["route"]

        if UsuariRuta.objects.filter(usuari=usuari, route=route).exists():
            return Response(
                {"error": "La ruta ya está guardada"}, status=status.HTTP_409_CONFLICT
            )

        UsuariRuta.objects.create(usuari=usuari, route=route)
        return Response(
            {"message": "Ruta guardada correctamente"}, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=["Usuaris · Me · Rutas"],
        summary="Eliminar una ruta guardada",
        description="Elimina la asociación entre el usuario autenticado y la ruta indicada por `route_id`.",
        parameters=[
            OpenApiParameter(
                name="route_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description="ID de la ruta a eliminar de guardados",
            )
        ],
        responses={
            204: OpenApiResponse(description="Ruta eliminada de guardados"),
            404: OpenApiResponse(description="Usuario o ruta no encontrada"),
        },
    )
    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/routes/(?P<route_id>[^/.]+)",
        url_name="me-routes-delete",
    )
    def delete_saved_route(self, request, route_id=None):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        deleted, _ = UsuariRuta.objects.filter(
            usuari=usuari, route_id=route_id
        ).delete()
        if not deleted:
            return Response(
                {"error": "Ruta no encontrada en guardados"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="me/update-form",
        url_name="me-update-form",
    )
    def update_usuari_questionari(self, request, *args, **kwargs):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        new_username = request.data.get("username")
        if new_username is not None:
            if not str(new_username).strip():
                return Response(
                    {"username": ["El nombre de usuario no puede estar vacío."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if (
                Usuari.objects.filter(username__iexact=new_username)
                .exclude(pk=usuari.pk)
                .exists()
            ):
                return Response(
                    {"username": ["Este nombre de usuario ya existe."]},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = self.get_serializer(usuari, data=request.data, partial=True)
        if serializer.is_valid():
            usuari.actualitzarPerfilQuestionari(serializer.validated_data)
            return Response(serializer.data)

        # Si los datos no son válidos (ej: peso negativo), devuelve error 400
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Listar amigos del usuario autenticado",
        description="Devuelve todas las amistades aceptadas del usuario autenticado.",
        responses={200: AmistatSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends",
        url_name="me-friends",
    )
    def list_friends(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        amistats = Amistat.objects.filter(
            django_models.Q(solicitant=usuari) | django_models.Q(receptor=usuari),
            estat=EstatAmistat.ACCEPTED,
        ).select_related("solicitant", "receptor")

        serializer = AmistatSerializer(
            amistats, many=True, context={"request_user_id": usuari.pk}
        )
        return Response(serializer.data)

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Enviar solicitud de amistad",
        request=inline_serializer(
            name="FriendRequestBody",
            fields={"receptor_id": serializers.IntegerField()},
        ),
        responses={
            201: OpenApiResponse(description="Solicitud enviada"),
            400: OpenApiResponse(description="Error de validación"),
            409: OpenApiResponse(
                description="Ya existe una solicitud entre estos usuarios"
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/request",
        url_name="me-friends-request",
    )
    def send_friend_request(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        receptor_id = request.data.get("receptor_id")
        if not receptor_id:
            return Response(
                {"error": "receptor_id és obligatori"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if receptor_id == usuari.pk:
            return Response(
                {"error": "No pots afegir-te a tu mateix"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            receptor = Usuari.objects.get(pk=receptor_id)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuari receptor no trobat"}, status=status.HTTP_404_NOT_FOUND
            )

        # Comprueba duplicado en ambas direcciones
        ja_existeix = Amistat.objects.filter(
            django_models.Q(solicitant=usuari, receptor=receptor)
            | django_models.Q(solicitant=receptor, receptor=usuari)
        ).exists()
        if ja_existeix:
            return Response(
                {"error": "Ja existeix una sol·licitud entre aquests usuaris"},
                status=status.HTTP_409_CONFLICT,
            )

        amistat = Amistat.objects.create(solicitant=usuari, receptor=receptor)

        if receptor.fcm_token:
            send_push_notification(
                fcm_token=receptor.fcm_token,
                title="Nova sol·licitud d'amistat",
                body=f"{usuari.username} t'ha enviat una sol·licitud d'amistat.",
                data={"type": "friend_request", "usuari_id": str(usuari.pk), "amistat_id": str(amistat.pk), "solicitant_username": usuari.username, "solicitant_profile_pic": str(usuari.profile_pic.url) if usuari.profile_pic else "",},
            )

        return Response(
            {"message": "Sol·licitud enviada"}, status=status.HTTP_201_CREATED
        )

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Responder solicitud de amistad",
        description="Acepta o rechaza una solicitud. `accio` puede ser `accept` o `reject`.",
        responses={
            200: OpenApiResponse(description="Solicitud actualizada"),
            403: OpenApiResponse(
                description="No ets el receptor d'aquesta sol·licitud"
            ),
            404: OpenApiResponse(description="Sol·licitud no trobada"),
        },
    )
    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/(?P<amistat_id>[^/.]+)/respond",
        url_name="me-friends-respond",
    )
    def respond_friend_request(self, request, amistat_id=None):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            amistat = Amistat.objects.get(pk=amistat_id)
        except Amistat.DoesNotExist:
            return Response(
                {"error": "Sol·licitud no trobada"}, status=status.HTTP_404_NOT_FOUND
            )

        if amistat.receptor != usuari:
            return Response(
                {"error": "No ets el receptor d'aquesta sol·licitud"},
                status=status.HTTP_403_FORBIDDEN,
            )

        accio = request.data.get("accio")
        if accio == "accept":
            amistat.estat = EstatAmistat.ACCEPTED
            amistat.save()
            if amistat.solicitant.fcm_token:
                send_push_notification(
                    fcm_token=amistat.solicitant.fcm_token,
                    title="Sol·licitud acceptada",
                    body=f"{usuari.username} ha acceptat la teva sol·licitud d'amistat.",
                    data={"type": "friend_accepted", "usuari_id": str(usuari.pk), "usuari_username": usuari.username, "usuari_profile_pic": str(usuari.profile_pic.url) if usuari.profile_pic else ""},
                )
            return Response({"message": "Amistat acceptada"})
        elif accio == "reject":
            amistat.delete()
            return Response(
                {"message": "Sol·licitud rebutjada"}, status=status.HTTP_200_OK
            )

        return Response(
            {"error": "accio ha de ser 'accept' o 'reject'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Listar solicitudes de amistad recibidas",
        description="Devuelve las solicitudes de amistad pendientes recibidas por el usuario autenticado.",
        responses={200: OpenApiResponse(description="Lista de solicitudes")},
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/requests",
        url_name="me-friends-requests",
    )
    def list_friend_requests(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        solicituds = Amistat.objects.filter(
            receptor=usuari,
            estat=EstatAmistat.PENDING,
        ).select_related("solicitant")

        data = [
            {
                "id": s.pk,
                "solicitant_id": s.solicitant.pk,
                "solicitant_username": s.solicitant.username,
            }
            for s in solicituds
        ]
        return Response(data)

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Eliminar un amigo",
        description="Elimina una amistad aceptada con el usuario indicado.",
        responses={
            204: OpenApiResponse(description="Amistat eliminada"),
            404: OpenApiResponse(description="Amistat no trobada"),
        },
    )
    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/(?P<amic_id>[0-9]+)",
        url_name="me-friends-delete",
    )
    def delete_friend(self, request, amic_id=None):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        from django.db import models as django_models

        deleted, _ = Amistat.objects.filter(
            django_models.Q(solicitant=usuari, receptor_id=amic_id)
            | django_models.Q(solicitant_id=amic_id, receptor=usuari),
            estat=EstatAmistat.ACCEPTED,
        ).delete()

        if not deleted:
            return Response(
                {"error": "Amistat no trobada"}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Usuaris · Me"],
        summary="Registrar FCM token",
        description="El dispositivo Android llama a este endpoint al iniciar sesión para registrar su token de notificaciones push.",
        request=inline_serializer(
            name="FcmTokenRequest",
            fields={"fcm_token": serializers.CharField()},
        ),
        responses={200: OpenApiResponse(description="Token registrado")},
    )
    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="me/fcm-token",
        url_name="me-fcm-token",
    )
    def update_fcm_token(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        fcm_token = request.data.get("fcm_token", "").strip()
        if not fcm_token:
            return Response(
                {"error": "fcm_token és obligatori"}, status=status.HTTP_400_BAD_REQUEST
            )

        usuari.fcm_token = fcm_token
        usuari.save(update_fields=["fcm_token"])
        return Response({"message": "Token registrat correctament"})

    @extend_schema(tags=["Usuaris · Me"], summary="Llistar les meves insígnies")
    @action(
        detail=False,
        methods=["get"],
        url_path="me/insignies",
        permission_classes=[IsAuthenticated],
    )
    def get_my_insignies(self, request):
        usuari = self._get_usuari_from_token(request)
        registres = usuari.insignies_guanyades.select_related("insignia")
        serializer = UsuariInsigniaSerializer(registres, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Usuaris · Me"], summary="Comprovar i otorgar noves insígnies")
    @action(
        detail=False,
        methods=["post"],
        url_path="me/premis/check",
        permission_classes=[IsAuthenticated],
    )
    def check_gamificacio(self, request):
        usuari = self._get_usuari_from_token(request)
        noves_insignies = gestionar_puntuacio_i_insignies(usuari)
        return Response(
            {
                "status": "success",
                "new_badges": noves_insignies,
                "current_points": usuari.punts,
                "current_streak": usuari.ratxa,
            }
        )

    @extend_schema(tags=["Gamificació"], summary="Veure el log de punts d'un usuari")
    @action(detail=False, methods=["get"], url_path="me/points-log")
    def get_points_log(self, request):
        usuari = self._get_usuari_from_token(request)
        logs = usuari.logs_punts.all().order_by("-data")[:20]
        serializer = PuntLogSerializer(logs, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Gamificació"],
        summary="Llista de totes les insígnies existents al sistema",
    )
    @action(detail=False, methods=["get"], url_path="insignies")
    def list_all_insignies(self, request):
        from ..models import Insignia
        from ..serializers import InsigniaSerializer

        insignies = Insignia.objects.all()
        serializer = InsigniaSerializer(insignies, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Gamificació"], summary="Rànquing global d'usuaris")
    @action(detail=False, methods=["get"], url_path="leaderboard")
    def leaderboard(self, request):
        top_usuaris = Usuari.objects.all().order_by("-punts")[:50]
        data = []
        for i, u in enumerate(top_usuaris):
            data.append(
                {
                    "posicio": i + 1,
                    "username": u.username,
                    "punts": u.punts,
                    "titol": u.titol,
                    "profile_pic": u.profile_pic.url if u.profile_pic else None,
                }
            )
        return Response(data)

    @action(detail=False, methods=["get"], url_path="me/titols-disponibles")
    def get_available_titles(self, request):
        usuari = self._get_usuari_from_token(request)

        if usuari.titols_pendents <= 0:
            return Response({"error": "No tens cap tria de títol pendent"}, status=400)

        # Busquem títols que:
        # 1. L'usuari encara NO tingui
        # 2. El seu rang (punts_minims) sigui apte per a la puntuació actual
        ja_tinguts = UsuariTitol.objects.filter(usuari=usuari).values_list(
            "titol_id", flat=True
        )
        pool = list(
            Titol.objects.exclude(id__in=ja_tinguts).filter(
                punts_minims__lte=usuari.punts
            )
        )

        # Triem 5 aleatoris d'aquest pool
        import random

        titols_triats = random.sample(pool, min(len(pool), 5))

        from ..serializers import TitolSerializer

        serializer = TitolSerializer(titols_triats, many=True)
        return Response(
            {"titols_pendents": usuari.titols_pendents, "opcions": serializer.data}
        )

    @action(detail=False, methods=["post"], url_path="me/desbloquejar-titol")
    def unlock_title(self, request):
        usuari = self._get_usuari_from_token(request)
        titol_id = request.data.get("titol_id")

        if usuari.titols_pendents <= 0:
            return Response({"error": "No tens cap tria de títol pendent"}, status=400)

        try:
            titol = Titol.objects.get(id=titol_id)
            # Vinculem el títol triat i restem una oportunitat
            UsuariTitol.objects.get_or_create(usuari=usuari, titol=titol)
            usuari.titols_pendents -= 1
            usuari.save()
            return Response({"status": "success", "titol_desbloquejat": titol.nom})
        except Titol.DoesNotExist:
            return Response({"error": "El títol no existeix"}, status=404)

    @extend_schema(
        tags=["Usuaris · Me"],
        summary="Llistar els meus plans d'entrenament amb el seu calendari",
        responses={200: PlaEntrenamentSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="me/plans-entrenament",
        permission_classes=[IsAuthenticated],
    )
    def get_my_plans(self, request):
        from ..serializers import ExerciciSerializer

        usuari = self._get_usuari_from_token(request)
        plans = PlaEntrenament.objects.filter(usuari=usuari).order_by("-dataInici")

        resultat = []
        for pla in plans:
            plan_data = PlaEntrenamentSerializer(pla).data

            exercicis = pla.plans_entrenament.filter(template__isnull=False).order_by(
                "dataInici"
            )

            plan_data["exercicis"] = ExerciciSerializer(exercicis, many=True).data
            resultat.append(plan_data)

        return Response(resultat)

    @extend_schema(
        tags=["Serveis Externs"],
        summary="Consultar eficiència d'edifici i guanyar insígnia",
        description="Cridada al servei extern de WattsApp per obtenir la puntuació d'eficiència energètica d'un edifici.",
        request=inline_serializer(
            name="CheckBuildingRequest",
            fields={
                "municipi": serializers.CharField(help_text="Ex: Barcelona"),
                "adreca": serializers.CharField(help_text="Ex: Carrer de Balmes"),
                "numero": serializers.CharField(help_text="Ex: 10"),
            },
        ),
        responses={
            200: inline_serializer(
                name="CheckBuildingResponse",
                fields={
                    "puntuacio": serializers.IntegerField(
                        help_text="Puntuació de 0 a 10 (o -1 si no hi ha dades)"
                    ),
                    "insignia_guanyada": serializers.BooleanField(),
                    "missatge": serializers.CharField(),
                    "badge": InsigniaSerializer(allow_null=True),
                },
            ),
            404: OpenApiResponse(
                description="No s'han trobat dades per aquesta adreça."
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="me/comprovar-edifici",
        permission_classes=[IsAuthenticated],
    )
    def comprovar_edifici(self, request):
        from ..services.puntuacio_edifici import consultar_puntuacio_edifici
        from ..models import Insignia, UsuariInsignia

        usuari = self._get_usuari_from_token(request)

        municipi = request.data.get("municipi")
        adreca = request.data.get("adreca")
        numero = request.data.get("numero")

        puntuacio = consultar_puntuacio_edifici(municipi, adreca, numero)

        if puntuacio == -1:
            return Response(
                {"error": "No s'han trobat dades per aquesta adreça."}, status=404
            )

        badge_data = None

        if puntuacio >= 7:
            ins = Insignia.objects.filter(tipus="EDIFICI").first()

            if ins:
                usuari_insignia, _ = UsuariInsignia.objects.get_or_create(
                    usuari=usuari, insignia=ins
                )
                badge_data = InsigniaSerializer(ins).data

        return Response(
            {
                "badge": badge_data,
                "data_guanyada": (
                    int(usuari_insignia.data_guanyada.timestamp()) if badge_data else 0
                ),
            }
        )

    @extend_schema(
        tags=["Serveis Externs"],
        summary="Atorgar insígnia d'edifici",
        description="Si la puntuació de l'edifici és >= 7, es donen 100 punts i la insígnia.",
        request=inline_serializer(
            name="GrantBuildingBadgeRequest",
            fields={
                "puntuacio": serializers.IntegerField(
                    help_text="Puntuació obtinguda pel front-end (0-10)"
                ),
            },
        ),
        responses={
            200: inline_serializer(
                name="GrantBuildingBadgeResponse",
                fields={
                    "insignia_guanyada": serializers.BooleanField(),
                    "missatge": serializers.CharField(),
                    "badge": InsigniaSerializer(allow_null=True),
                    "punts_totals": serializers.IntegerField(),
                    "titols_pendents": serializers.IntegerField(),
                },
            ),
        },
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="me/edifici-insignia",
        permission_classes=[IsAuthenticated],
    )
    def otorgar_insignia_edifici(self, request):
        from ..models import Insignia, UsuariInsignia, PuntLog

        usuari = self._get_usuari_from_token(request)

        try:
            puntuacio = int(request.data.get("puntuacio", -1))
        except (ValueError, TypeError):
            return Response(
                {"error": "La puntuació ha de ser un número vàlid."}, status=400
            )

        badge_data = None
        missatge = f"L'edifici té una puntuació de {puntuacio}/10. "

        if puntuacio >= 7:
            punts_bonus = 100
            usuari.punts += punts_bonus
            usuari.save()
            PuntLog.objects.create(
                usuari=usuari, quantitat=punts_bonus, motiu="Edifici Sostenible"
            )

            gestionar_puntuacio_i_insignies(usuari)

            ins = Insignia.objects.filter(tipus="EDIFICI").first()
            if ins:
                rel, _ = UsuariInsignia.objects.get_or_create(
                    usuari=usuari, insignia=ins
                )
                data_guanyada = rel.data_guanyada
                missatge += "Felicitats! Has guanyat 100 punts i la insígnia d'edifici sostenible."
                badge_data = InsigniaSerializer(ins).data
            else:
                missatge += "Puntuació excel·lent (100 punts sumats), però la insígnia no està configurada a l'Admin."
        else:
            missatge += (
                "La puntuació no és prou alta per rebre la insígnia (mínim 7/10)."
            )

        return Response(
            {
                "badge": badge_data,
                "data_guanyada": data_guanyada,
            }
        )
