
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, home
from .views.views_auth import GoogleLoginView
from .views.views_usuari import UsuariViewSet
from .views.route_pollution_view import EcoRouteView
from .views import RouteViewSet  # Importa la vista de la API
from django.conf import settings
from django.conf.urls.static import static

# Crea un router para registrar las vistas de la API
router = DefaultRouter()
router.register(r'routes', RouteViewSet)  # Registra la vista de rutas
router.register(r'usuaris', UsuariViewSet)

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
    path("air-quality/", EcoRouteView.as_view(), name="air-quality"),
    path("api/", include(router.urls)),  # Agrega las rutas de la API aquí
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
