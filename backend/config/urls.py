from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.conf import settings
from django.conf.urls.static import static

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from core.views import health, home, RouteViewSet
from core.views.views_auth import GoogleLoginView
from core.views.views_usuari import UsuariViewSet
from core.views.route_pollution_view import EcoRouteView
from core.views.views_air_quality import AirQualityView, ExternalAirQualityView
from core.views.views_bicing import BicingView
from core.views.views_pla_entrenament import PlaEntrenamentViewSet  # Importar PlaEntrenamentViewSet
from rest_framework_simplejwt.views import TokenRefreshView
from core.views.views_exercici import ExerciciViewSet
from core.views.views_exercici import TemplateExerciciViewSet

router = DefaultRouter()
router.register(r"routes", RouteViewSet)
router.register(r"usuaris", UsuariViewSet)
router.register(r"pla-entrenament", PlaEntrenamentViewSet)  # Registrar la vista de PlaEntrenament
router.register(r'exercicis', ExerciciViewSet, basename='exercici')
router.register(r'template-exercici', TemplateExerciciViewSet)

usuari_save_route = UsuariViewSet.as_view({"post": "save_route"})
usuari_get_routes = UsuariViewSet.as_view({"get": "get_saved_routes"})
usuari_delete_route = UsuariViewSet.as_view({"delete": "delete_saved_route"})

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view(), name="auth-google"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("air-quality/", AirQualityView.as_view(), name="air-quality"),
    path("route-generation/", EcoRouteView.as_view(), name="route-generation"),
    path('zone-air-quality/', ExternalAirQualityView.as_view(), name='external-air-quality'),
    path("bicing/", BicingView.as_view(), name="bicing"),
    path("api/usuaris/me/routes/save/", usuari_save_route, name="usuari-save-route"),
    path("api/usuaris/me/routes/", usuari_get_routes, name="usuari-get-routes"),
    path(
        "api/usuaris/me/routes/<int:route_id>/",
        usuari_delete_route,
        name="usuari-delete-route",
    ),
    path("api/", include(router.urls)),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="api-schema"),
        name="api-redoc",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)