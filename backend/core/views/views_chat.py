from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import viewsets, status

from ..models import Conversa, Missatge, Usuari
from ..serializers import ConversaSerializer, MissatgeSerializer


class ConversaViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def _me(self, request):
        google_id = request.auth.get("google_id")
        return Usuari.objects.get(google_id=google_id)

    # GET /api/conversations/
    def list(self, request):
        usuari = self._me(request)
        from django.db import models as dm
        converses = (
            Conversa.objects
            .filter(dm.Q(usuari_1=usuari) | dm.Q(usuari_2=usuari))
            .prefetch_related("missatges")
            .select_related("usuari_1", "usuari_2")
            .order_by("-creada_at")
        )
        serializer = ConversaSerializer(
            converses, many=True, context={"request_user_id": usuari.pk}
        )
        return Response(serializer.data)

    # GET /api/conversations/{id}/messages/?page=1
    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        usuari = self._me(request)
        try:
            conversa = Conversa.objects.get(pk=pk)
        except Conversa.DoesNotExist:
            return Response({"error": "Conversa no trobada"}, status=status.HTTP_404_NOT_FOUND)

        # Solo participantes pueden leer
        if usuari not in (conversa.usuari_1, conversa.usuari_2):
            return Response(status=status.HTTP_403_FORBIDDEN)

        # Paginación manual sencilla (últimos 50, scroll hacia arriba)
        limit  = int(request.query_params.get("limit",  50))
        before = request.query_params.get("before")          # id del mensaje más antiguo ya cargado

        qs = conversa.missatges.all()
        if before:
            qs = qs.filter(pk__lt=before)
        missatges = qs.order_by("-enviat_at")[:limit]

        serializer = MissatgeSerializer(reversed(list(missatges)), many=True)
        return Response(serializer.data)

    # PATCH /api/conversations/{id}/read/
    @action(detail=True, methods=["patch"], url_path="read")
    def mark_read(self, request, pk=None):
        usuari = self._me(request)
        try:
            conversa = Conversa.objects.get(pk=pk)
        except Conversa.DoesNotExist:
            return Response({"error": "Conversa no trobada"}, status=status.HTTP_404_NOT_FOUND)

        if usuari not in (conversa.usuari_1, conversa.usuari_2):
            return Response(status=status.HTTP_403_FORBIDDEN)

        conversa.missatges.filter(llegit=False).exclude(emissor=usuari).update(llegit=True)
        return Response({"message": "Missatges marcats com llegits"})