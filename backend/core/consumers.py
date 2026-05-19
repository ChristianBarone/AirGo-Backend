import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import AnonymousUser
from django.db import models as dm
from .services.firebase import send_push_notification

from .models import Amistat, Conversa, EstatAmistat, Missatge, Usuari


class ChatConsumer(AsyncWebsocketConsumer):

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self):
        self.usuari = self.scope.get("usuari")

        # 1. Debe estar autenticado
        if not self.usuari or isinstance(self.usuari, AnonymousUser):
            await self.close(code=4001)
            return

        other_id = int(self.scope["url_route"]["kwargs"]["other_id"])

        # 2. Solo puede chatear con amigos
        if not await self._son_amics(self.usuari.pk, other_id):
            await self.close(code=4003)
            return

        # 3. Obtener/crear la conversación canónica
        self.conversa = await self._get_conversa(self.usuari.pk, other_id)
        self.room = f"chat_{self.conversa.pk}"

        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room"):
            await self.channel_layer.group_discard(self.room, self.channel_name)

    # ── Receive (client → server) ─────────────────────────────────────────────

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        contingut = data.get("missatge", "").strip()
        if not contingut:
            return

        missatge = await self._save_missatge(contingut)

        await self.channel_layer.group_send(
            self.room,
            {
                "type": "chat.missatge",
                "id": missatge.pk,
                "emissor_id": self.usuari.pk,
                "emissor_username": self.usuari.username,
                "contingut": contingut,
                "enviat_at": missatge.enviat_at.isoformat(),
            },
        )

    # ── Send (server → client) ────────────────────────────────────────────────

    async def chat_missatge(self, event):
        """Handler invocado por group_send; reenvía el mensaje a este WebSocket."""
        await self.send(
            text_data=json.dumps(
                {
                    "id": event["id"],
                    "emissor_id": event["emissor_id"],
                    "emissor_username": event["emissor_username"],
                    "contingut": event["contingut"],
                    "enviat_at": event["enviat_at"],
                }
            )
        )

    async def chat_messages_read(self, event):
        """Reenvía al WebSocket que los mensajes han sido leídos."""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "messages_read",
                    "read_by": event["read_by"],
                }
            )
        )

    # ── DB helpers (sync → async) ─────────────────────────────────────────────

    @database_sync_to_async
    def _son_amics(self, uid, other_id):
        return Amistat.objects.filter(
            dm.Q(solicitant_id=uid, receptor_id=other_id)
            | dm.Q(solicitant_id=other_id, receptor_id=uid),
            estat=EstatAmistat.ACCEPTED,
        ).exists()

    @database_sync_to_async
    def _get_conversa(self, uid, other_id):
        u1 = Usuari.objects.get(pk=uid)
        u2 = Usuari.objects.get(pk=other_id)
        return Conversa.entre(u1, u2)

    @database_sync_to_async
    def _save_missatge(self, contingut):
        missatge = Missatge.objects.create(
            conversa=self.conversa,
            emissor=self.usuari,
            contingut=contingut,
        )
        # Notificar al receptor si tiene fcm_token
        receptor = (
            self.conversa.usuari_2
            if self.conversa.usuari_1_id == self.usuari.pk
            else self.conversa.usuari_1
        )
        if receptor.fcm_token:
            send_push_notification(
                fcm_token=receptor.fcm_token,
                title=self.usuari.username,
                body=contingut[:100],
                data={
                    "type": "chat",
                    "conversa_id": str(self.conversa.pk),
                    "emissor_id": str(self.usuari.pk),
                },
            )
        return missatge
