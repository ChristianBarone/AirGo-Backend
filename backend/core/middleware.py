from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from .models import Usuari


@database_sync_to_async
def _resolve_usuari(token_str: str):
    try:
        token = AccessToken(token_str)
        google_id = token.get("google_id")
        if not google_id:
            return AnonymousUser()
        return Usuari.objects.get(google_id=google_id)
    except (InvalidToken, TokenError, Usuari.DoesNotExist):
        return AnonymousUser()


class JWTAuthMiddleware:
    """Adjunta `scope['usuari']` a partir del token JWT en ?token=."""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        qs = parse_qs(scope.get("query_string", b"").decode())
        tokens = qs.get("token", [])
        scope["usuari"] = await _resolve_usuari(tokens[0]) if tokens else AnonymousUser()
        return await self.inner(scope, receive, send)