from rest_framework import viewsets
from ..models import Usuari
from ..serializers import UsuariSerializer

## View perfil de usuario
class UsuariViewSet(viewsets.ModelViewSet):
    queryset = Usuari.objects.all()
    serializer_class = UsuariSerializer