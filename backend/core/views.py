from rest_framework import viewsets
from .models import Route
from .serializers import RouteSerializer

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()  # Esto obtiene todas las rutas
    serializer_class = RouteSerializer  # Conecta con el serializer