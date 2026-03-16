from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from ..models import Usuari
from ..serializers import UsuariSerializer

## View perfil de usuario
class UsuariViewSet(viewsets.ModelViewSet):
    queryset = Usuari.objects.all()
    serializer_class = UsuariSerializer

    @action(
        detail=False,
        methods=["patch"],
        url_path="me/profile-pic",
        parser_classes=[MultiPartParser, FormParser],
        permission_classes=[IsAuthenticated]
    )
    def change_profile_pic(self, request):
        user = request.user
        user.profile_pic = request.data.get("profile_pic")
        user.save()

        serializer = self.get_serializer(user)
        return Response(serializer.data)