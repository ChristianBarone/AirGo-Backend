from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import Usuari
from ..serializers import UsuariSerializer

class UsuariViewSet(viewsets.ModelViewSet):
    queryset = Usuari.objects.all()
    serializer_class = UsuariSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['username']

    @action(
        detail=False,
        methods=["patch"],
        url_path="me/profile-pic",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsAuthenticated]
    )
    def change_profile_pic(self, request):
        try:
            usuari = Usuari.objects.get(username=request.user.email)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        usuari.profile_pic = request.data.get("profile_pic")
        usuari.save()

        serializer = self.get_serializer(usuari)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["delete"],
        permission_classes=[IsAuthenticated],
        url_path="me"
    )
    def delete_account(self, request):
        try:
            usuari = Usuari.objects.get(username=request.user.email)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        usuari.delete()
        request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="me/profile",
        url_name = "me-profile"
    )
    def retrieve_profile(self, request):
        try:
            # Obtener el 'Usuari' basado en el correo electrónico del usuario autenticado
            usuari = Usuari.objects.get(username=request.user.email)
        except Usuari.DoesNotExist:
            return Response({"error": "Usuario no encontrado"}, status=404)

        # Serializar la información y devolverla
        serializer = self.get_serializer(usuari)
        return Response(serializer.data)