from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, home
from .views.views_auth import GoogleLoginView
from .views.views_usuari import UsuariViewSet
from .views.views_air_quality import AirQualityView
from .views.views_bicing import BicingView
from .views import RouteViewSet
from django.conf import settings
from django.conf.urls.static import static

# Crea un router para registrar las vistas de la API
router = DefaultRouter()
router.register(r'routes', RouteViewSet)  # Registra la vista de rutas
router.register(r'usuaris', UsuariViewSet)  # Registra el viewset de Usuari

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
    path("air-quality/", AirQualityView.as_view(), name="air-quality"),
    path("bicing/", BicingView.as_view(), name="bicing"),
    path("api/", include(router.urls)),  # Incluir rutas del router para las API
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)