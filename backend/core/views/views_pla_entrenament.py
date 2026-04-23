from rest_framework import viewsets
from ..models import PlaEntrenament
from ..serializers import PlaEntrenamentSerializer


class PlaEntrenamentViewset(viewsets.ModelViewSet):
    queryset = PlaEntrenament.objects.all()
    serializer_class = PlaEntrenamentSerializer
