from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, home
from .views.views_auth import GoogleLoginView
from .views.views_usuari import UsuariViewSet
from .views.route_pollution_view import EcoRouteView
from .views.views_air_quality import AirQualityView, ExternalAirQualityView
from .views import RouteViewSet
from .views.views_bicing import BicingView
from .views.views_pla_entrenament import PlaEntrenamentViewSet
from .views.views_exercici import TemplateExerciciViewSet
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from core.views.views_exercici import ExerciciViewSet
from core.views.views_exercici import TemplateExerciciViewSet
from core.views.views_chat import ConversaViewSet
from core.views.views_forum import ForumViewSet, UsuariForumsFavoritsView

router = DefaultRouter()
router.register(r"routes", RouteViewSet)
router.register(r"usuaris", UsuariViewSet)
router.register(r"pla-entrenament", PlaEntrenamentViewSet)
router.register(r'template-exercici', TemplateExerciciViewSet)
router.register(r'exercicis', ExerciciViewSet, basename='exercici')
router.register(r'template-exercici', TemplateExerciciViewSet)
router.register(r"conversations", ConversaViewSet, basename="conversa")
router.register(r"forums", ForumViewSet, basename="forum")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),
    path("air-quality/", AirQualityView.as_view(), name="air-quality"),
    path('zone-air-quality/', ExternalAirQualityView.as_view(), name='external-air-quality'),
    path("route-generation/", EcoRouteView.as_view(), name="air-quality"),
    path("bicing/", BicingView.as_view(), name="bicing"),
    path("api/", include(router.urls)),
    path("api/usuaris/me/forums/", UsuariForumsFavoritsView.as_view(), name="usuari-forums-favorits"),
    path("api/usuaris/me/forums/<int:forum_id>/", UsuariForumsFavoritsView.as_view(), name="usuari-forum-favorit-delete"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)