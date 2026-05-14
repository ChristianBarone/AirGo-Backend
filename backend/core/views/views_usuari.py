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

from ..models import Usuari, UsuariTitol, UsuariRuta, Amistat, EstatAmistat, Insignia
from ..serializers import UsuariSerializer, UsuariTitolSerializer, UsuariRutaSerializer, AmistatSerializer, \
    UsuariInsigniaSerializer, PuntLogSerializer
from django.db import models as django_models

from ..services.gamificacio import gestionar_puntuacio_i_insignies


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
        google_id = request.auth.get('google_id')
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
        url_path="me"
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
        url_name="me-profile"
    )
    def retrieve_profile(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
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
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        rutes = UsuariRuta.objects.filter(usuari=usuari).select_related('route')
        serializer = UsuariRutaSerializer(rutes, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Usuaris · Me · Rutas"],
        summary="Guardar una ruta",
        description="Asocia una ruta existente al usuario autenticado. Devuelve 409 si ya estaba guardada.",
        request=inline_serializer(
            name="SaveRouteRequest",
            fields={"route_id": serializers.IntegerField(help_text="ID de la ruta a guardar")},
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
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        serializer = UsuariRutaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        route = serializer.validated_data['route']

        if UsuariRuta.objects.filter(usuari=usuari, route=route).exists():
            return Response({"error": "La ruta ya está guardada"}, status=status.HTTP_409_CONFLICT)

        UsuariRuta.objects.create(usuari=usuari, route=route)
        return Response({"message": "Ruta guardada correctamente"}, status=status.HTTP_201_CREATED)

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
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = UsuariRuta.objects.filter(usuari=usuari, route_id=route_id).delete()
        if not deleted:
            return Response(
                {"error": "Ruta no encontrada en guardados"}, status=status.HTTP_404_NOT_FOUND
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
                return Response({"username": ["El nombre de usuario no puede estar vacío."]},
                                status=status.HTTP_400_BAD_REQUEST)
            if Usuari.objects.filter(username__iexact=new_username).exclude(pk=usuari.pk).exists():
                return Response({"username": ["Este nombre de usuario ya existe."]}, status=status.HTTP_400_BAD_REQUEST)

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
        detail=False, methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends", url_name="me-friends",
    )
    def list_friends(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

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
            409: OpenApiResponse(description="Ya existe una solicitud entre estos usuarios"),
        },
    )
    @action(
        detail=False, methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/request", url_name="me-friends-request",
    )
    def send_friend_request(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        receptor_id = request.data.get("receptor_id")
        if not receptor_id:
            return Response({"error": "receptor_id és obligatori"}, status=status.HTTP_400_BAD_REQUEST)

        if receptor_id == usuari.pk:
            return Response({"error": "No pots afegir-te a tu mateix"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            receptor = Usuari.objects.get(pk=receptor_id)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuari receptor no trobat"}, status=status.HTTP_404_NOT_FOUND)

        # Comprueba duplicado en ambas direcciones
        ja_existeix = Amistat.objects.filter(
            django_models.Q(solicitant=usuari, receptor=receptor) |
            django_models.Q(solicitant=receptor, receptor=usuari)
        ).exists()
        if ja_existeix:
            return Response({"error": "Ja existeix una sol·licitud entre aquests usuaris"},
                            status=status.HTTP_409_CONFLICT)

        Amistat.objects.create(solicitant=usuari, receptor=receptor)
        return Response({"message": "Sol·licitud enviada"}, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Responder solicitud de amistad",
        description="Acepta o rechaza una solicitud. `accio` puede ser `accept` o `reject`.",
        responses={
            200: OpenApiResponse(description="Solicitud actualizada"),
            403: OpenApiResponse(description="No ets el receptor d'aquesta sol·licitud"),
            404: OpenApiResponse(description="Sol·licitud no trobada"),
        },
    )
    @action(
        detail=False, methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/(?P<amistat_id>[^/.]+)/respond",
        url_name="me-friends-respond",
    )
    def respond_friend_request(self, request, amistat_id=None):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        try:
            amistat = Amistat.objects.get(pk=amistat_id)
        except Amistat.DoesNotExist:
            return Response({"error": "Sol·licitud no trobada"}, status=status.HTTP_404_NOT_FOUND)

        if amistat.receptor != usuari:
            return Response({"error": "No ets el receptor d'aquesta sol·licitud"}, status=status.HTTP_403_FORBIDDEN)

        accio = request.data.get("accio")
        if accio == "accept":
            amistat.estat = EstatAmistat.ACCEPTED
            amistat.save()
            return Response({"message": "Amistat acceptada"})
        elif accio == "reject":
            amistat.delete()
            return Response({"message": "Sol·licitud rebutjada"}, status=status.HTTP_200_OK)

        return Response({"error": "accio ha de ser 'accept' o 'reject'"}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Usuaris · Me · Amics"],
        summary="Listar solicitudes de amistad recibidas",
        description="Devuelve las solicitudes de amistad pendientes recibidas por el usuario autenticado.",
        responses={200: OpenApiResponse(description="Lista de solicitudes")},
    )
    @action(
        detail=False, methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/requests", url_name="me-friends-requests",
    )
    def list_friend_requests(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

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
        detail=False, methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/friends/(?P<amic_id>[0-9]+)",
        url_name="me-friends-delete",
    )
    def delete_friend(self, request, amic_id=None):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        from django.db import models as django_models
        deleted, _ = Amistat.objects.filter(
            django_models.Q(solicitant=usuari, receptor_id=amic_id) |
            django_models.Q(solicitant_id=amic_id, receptor=usuari),
            estat=EstatAmistat.ACCEPTED,
        ).delete()

        if not deleted:
            return Response({"error": "Amistat no trobada"}, status=status.HTTP_404_NOT_FOUND)

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
        detail=False, methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="me/fcm-token",
        url_name="me-fcm-token",
    )
    def update_fcm_token(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        fcm_token = request.data.get("fcm_token", "").strip()
        if not fcm_token:
            return Response({"error": "fcm_token és obligatori"}, status=status.HTTP_400_BAD_REQUEST)

        usuari.fcm_token = fcm_token
        usuari.save(update_fields=["fcm_token"])
        return Response({"message": "Token registrat correctament"})

    @extend_schema(tags=["Usuaris · Me"], summary="Llistar les meves insígnies")
    @action(detail=False, methods=["get"], url_path="me/insignies", permission_classes=[IsAuthenticated])
    def get_my_insignies(self, request):
        usuari = self._get_usuari_from_token(request)
        registres = usuari.insignies_guanyades.select_related('insignia')
        serializer = UsuariInsigniaSerializer(registres, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["Usuaris · Me"], summary="Comprovar i otorgar noves insígnies")
    @action(detail=False, methods=["post"], url_path="me/premis/check", permission_classes=[IsAuthenticated])
    def check_gamificacio(self, request):
        usuari = self._get_usuari_from_token(request)
        noves_insignies = gestionar_puntuacio_i_insignies(usuari)
        return Response({
            "status": "success",
            "new_badges": noves_insignies,
            "current_points": usuari.punts,
            "current_streak": usuari.ratxa
        })

    @action(detail=False, methods=["get"], url_path="me/points-log")
    def get_points_log(self, request):
        usuari = self._get_usuari_from_token(request)
        logs = usuari.logs_punts.all().order_by('-data')[:20]
        serializer = PuntLogSerializer(logs, many=True)
        return Response(serializer.data)
