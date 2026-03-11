from django.urls import path
from .views import health, home
from .views.views_auth import GoogleLoginView

urlpatterns = [
    path("", home, name="home"),
    path("health/", health, name="health"),
    path("auth/google/", GoogleLoginView.as_view()),
]
