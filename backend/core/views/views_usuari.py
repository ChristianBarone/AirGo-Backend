from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Usuari, UsuariTitol, UsuariRuta
from ..serializers import UsuariSerializer, UsuariTitolSerializer, UsuariRutaSerializer


class UsuariViewSet(viewsets.ModelViewSet):
    queryset = Usuari.objects.all()
    serializer_class = UsuariSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ["username"]

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

    # Helper privado para no repetir la lógica en cada vista
    def _get_usuari_from_token(self, request):
        google_id = request.auth.get("google_id")  # <-- leer del token
        return Usuari.objects.get(google_id=google_id)

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
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        serializer = self.get_serializer(usuari)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/routes",
        url_name="me-routes"
    )
    def get_saved_routes(self, request):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        rutes = UsuariRuta.objects.filter(usuari=usuari).select_related('route')
        serializer = UsuariRutaSerializer(rutes, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
        url_path="me/routes/save",
        url_name="me-routes-save"
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

    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path="me/routes/(?P<route_id>[^/.]+)",
        url_name="me-routes-delete"
    )
    def delete_saved_route(self, request, route_id=None):
        try:
            usuari = self._get_usuari_from_token(request)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        deleted, _ = UsuariRuta.objects.filter(usuari=usuari, route_id=route_id).delete()
        if not deleted:
            return Response({"error": "Ruta no encontrada en guardados"}, status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)
