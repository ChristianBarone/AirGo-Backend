from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import health, home
from .views.views_auth import GoogleLoginView
from .views.views_usuari import UsuariViewSet
from .views.route_pollution_view import EcoRouteView
from .views.views_air_quality import AirQualityView
from .views import RouteViewSet
from .views.views_bicing import BicingView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'routes', RouteViewSet)
router.register(r'usuaris', UsuariViewSet)

usuari_save_route = UsuariViewSet.as_view({'post': 'save_route'})
usuari_get_routes = UsuariViewSet.as_view({'get': 'get_saved_routes'})
usuari_delete_route = UsuariViewSet.as_view({'delete': 'delete_saved_route'})

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
    path("air-quality/", AirQualityView.as_view(), name="air-quality"),
    path("eco-route/", EcoRouteView.as_view(), name="eco-route"),
    path("route-generation/", EcoRouteView.as_view(), name="air-quality"),
    path("bicing/", BicingView.as_view(), name="bicing"),

    # Rutas explícitas ANTES del router para evitar conflicto con pk
    path("api/usuaris/me/routes/save/", usuari_save_route, name="usuari-save-route"),
    path("api/usuaris/me/routes/", usuari_get_routes, name="usuari-get-routes"),
    path("api/usuaris/me/routes/<int:route_id>/", usuari_delete_route, name="usuari-delete-route"),

    path("api/", include(router.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)