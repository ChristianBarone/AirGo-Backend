import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from core.middleware import JWTAuthMiddleware
import core.routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddleware(      # ← sin AllowedHostsOriginValidator
        URLRouter(core.routing.websocket_urlpatterns)
    ),
})