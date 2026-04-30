from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, home
from .views.views_auth import GoogleLoginView
from .views.views_usuari import UsuariViewSet
from .views.route_pollution_view import EcoRouteView
from .views.views_air_quality import AirQualityView
from .views import RouteViewSet
from .views.views_bicing import BicingView
from .views.views_pla_entrenament import PlaEntrenamentViewSet
from .views.views_exercici import TemplateExerciciViewSet
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from core.views.views_exercici import ExerciciViewSet

router = DefaultRouter()
router.register(r"routes", RouteViewSet)
router.register(r"usuaris", UsuariViewSet)
router.register(r"pla-entrenament", PlaEntrenamentViewSet)
router.register(r'template-exercici', TemplateExerciciViewSet)
router.register(r'exercicis', ExerciciViewSet, basename='exercici')

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("air-quality/", AirQualityView.as_view(), name="air-quality"),
    path("eco-route/", EcoRouteView.as_view(), name="eco-route"),
    path("route-generation/", EcoRouteView.as_view(), name="air-quality"),
    path("bicing/", BicingView.as_view(), name="bicing"),
    path("api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)