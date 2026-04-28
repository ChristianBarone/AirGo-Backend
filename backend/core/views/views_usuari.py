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

from ..models import Usuari, UsuariTitol, UsuariRuta
from ..serializers import UsuariSerializer, UsuariTitolSerializer, UsuariRutaSerializer


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

        serializer = self.get_serializer(usuari, data=request.data, partial=True)
        if serializer.is_valid():
            usuari.actualitzarPerfilQuestionari(serializer.validated_data)
            return Response(serializer.data)

        # Si los datos no son válidos (ej: peso negativo), devuelve error 400
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
