from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from drf_spectacular.types import OpenApiTypes

from ..models import Conversa, Missatge, Usuari
from ..serializers import ConversaSerializer, MissatgeSerializer


@extend_schema_view(
    list=extend_schema(
        tags=["Chat"],
        summary="Listar conversaciones",
        description="Devuelve todas las conversaciones del usuario autenticado con el último mensaje y mensajes no leídos.",
        responses={200: ConversaSerializer(many=True)},
    ),
)
class ConversaViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def _me(self, request):
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    def list(self, request):
        usuari = self._me(request)
        from django.db import models as dm

        converses = (
            Conversa.objects.filter(dm.Q(usuari_1=usuari) | dm.Q(usuari_2=usuari))
            .prefetch_related("missatges")
            .select_related("usuari_1", "usuari_2")
            .order_by("-creada_at")
        )
        serializer = ConversaSerializer(
            converses, many=True, context={"request_user_id": usuari.pk}
        )
        return Response(serializer.data)

    @extend_schema(
        tags=["Chat"],
        summary="Historial de mensajes",
        description="Devuelve los mensajes de una conversación paginados. Usa `before` con el ID del mensaje más antiguo ya cargado para cargar más hacia atrás (infinite scroll).",
        parameters=[
            OpenApiParameter(
                name="limit",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="Número de mensajes a devolver (default: 50)",
                required=False,
            ),
            OpenApiParameter(
                name="before",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description="ID del mensaje más antiguo ya cargado (para paginar hacia atrás)",
                required=False,
            ),
        ],
        responses={
            200: MissatgeSerializer(many=True),
            403: OpenApiResponse(description="No ets participant d'aquesta conversa"),
            404: OpenApiResponse(description="Conversa no trobada"),
        },
    )
    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        usuari = self._me(request)
        try:
            conversa = Conversa.objects.get(pk=pk)
        except Conversa.DoesNotExist:
            return Response(
                {"error": "Conversa no trobada"}, status=status.HTTP_404_NOT_FOUND
            )

        if usuari not in (conversa.usuari_1, conversa.usuari_2):
            return Response(status=status.HTTP_403_FORBIDDEN)

        limit = int(request.query_params.get("limit", 50))
        before = request.query_params.get("before")

        qs = conversa.missatges.all()
        if before:
            qs = qs.filter(pk__lt=before)
        missatges = qs.order_by("-enviat_at")[:limit]

        serializer = MissatgeSerializer(reversed(list(missatges)), many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["Chat"],
        summary="Marcar mensajes como leídos",
        description="Marca como leídos todos los mensajes no leídos de la conversación que no haya enviado el usuario autenticado.",
        responses={
            200: OpenApiResponse(description="Missatges marcats com llegits"),
            403: OpenApiResponse(description="No ets participant d'aquesta conversa"),
            404: OpenApiResponse(description="Conversa no trobada"),
        },
    )
    @action(detail=True, methods=["patch"], url_path="read")
    def mark_read(self, request, pk=None):
        usuari = self._me(request)
        try:
            conversa = Conversa.objects.get(pk=pk)
        except Conversa.DoesNotExist:
            return Response(
                {"error": "Conversa no trobada"}, status=status.HTTP_404_NOT_FOUND
            )

        if usuari not in (conversa.usuari_1, conversa.usuari_2):
            return Response(status=status.HTTP_403_FORBIDDEN)

        conversa.missatges.filter(llegit=False).exclude(emissor=usuari).update(
            llegit=True
        )
        return Response({"message": "Missatges marcats com llegits"})

    @extend_schema(
        tags=["Chat"],
        summary="Eliminar un mensaje",
        description="Elimina un mensaje propio. Solo el emissor del mensaje puede eliminarlo.",
        responses={
            204: OpenApiResponse(description="Missatge eliminat correctament"),
            403: OpenApiResponse(description="No pots eliminar aquest missatge"),
            404: OpenApiResponse(description="Missatge no trobat"),
        },
    )
    @action(
        detail=False, methods=["delete"], url_path="messages/(?P<missatge_id>[^/.]+)"
    )
    def delete_message(self, request, missatge_id=None):
        usuari = self._me(request)

        try:
            missatge = Missatge.objects.get(pk=missatge_id)
        except Missatge.DoesNotExist:
            return Response(
                {"error": "Missatge no trobat"}, status=status.HTTP_404_NOT_FOUND
            )

        if missatge.emissor != usuari:
            return Response(
                {"error": "No pots eliminar aquest missatge"},
                status=status.HTTP_403_FORBIDDEN,
            )

        missatge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
