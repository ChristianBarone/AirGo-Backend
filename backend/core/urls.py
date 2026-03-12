from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, home
from .views.views_auth import GoogleLoginView
from .views import RouteViewSet  # Importa la vista de la API

# Crea un router para registrar las vistas de la API
router = DefaultRouter()
router.register(r'routes', RouteViewSet)  # Registra la vista de rutas

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
    path("api/", include(router.urls)),  # Agrega las rutas de la API aquí
]