from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets
from ..models import Route
from ..serializers import RouteSerializer

def home(request):
    return HttpResponse("AirGo backend operativo")

def health(request):
    return JsonResponse({"status": "ok"})

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()  # Esto obtiene todas las rutas
    serializer_class = RouteSerializer  # Conecta con el serializer
