from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Usuari, UsuariTitol
from ..serializers import UsuariSerializer, UsuariTitolSerializer


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
