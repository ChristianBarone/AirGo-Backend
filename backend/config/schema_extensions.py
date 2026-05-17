"""
schema_extensions.py
Coloca este archivo en config/ (junto a settings.py y urls.py).

Registra el hook en settings.py:

    SPECTACULAR_SETTINGS = {
        ...
        "POSTPROCESSING_HOOKS": [
            "drf_spectacular.hooks.postprocess_schema_enums",
            "config.schema_extensions.add_websocket_paths",   # ← añadir esta línea
        ],
    }
"""


def add_websocket_paths(result, generator, request, public, **kwargs):
    """
    Inyecta los endpoints WebSocket en el schema OpenAPI generado por drf-spectacular.

    OpenAPI 3 no tiene soporte nativo para WebSockets, así que se documenta como
    paths con el prefijo /ws/ usando extensiones x- para indicar que son canales WS.
    Swagger UI los muestra agrupados bajo el tag 'WebSocket — Chat'.
    """

    ws_tag = "WebSocket — Chat"

    # ── Añadir descripción del tag ────────────────────────────────────────────
    if "tags" not in result:
        result["tags"] = []

    result["tags"].append(
        {
            "name": ws_tag,
            "description": (
                "Endpoints de tiempo real mediante **WebSocket** (Django Channels + Redis).\n\n"
                "> ⚠️ Estos endpoints no son HTTP — úsalos con un cliente WebSocket "
                "(navegador, `websocat`, Postman, etc.).\n\n"
                "**Autenticación:** el token JWT debe enviarse como query param:\n"
                "```\n"
                "ws://host/ws/chat/42/?token=<access_token>\n"
                "```\n"
                "*(o bien configurado en el middleware de tu ASGI según tu implementación)*"
            ),
        }
    )

    # ── Path del WebSocket de chat ────────────────────────────────────────────
    result["paths"]["/ws/chat/{other_id}/"] = {
        "get": {
            "tags": [ws_tag],
            "summary": "Chat en tiempo real",
            "operationId": "ws_chat_connect",
            "x-websocket": True,
            "description": (
                "Abre una conexión WebSocket para el chat en tiempo real entre dos usuarios.\n\n"
                "**URL:** `ws://host/ws/chat/{other_id}/`\n\n"
                "---\n\n"
                "### Flujo de conexión\n\n"
                "| Paso | Condición | Resultado |\n"
                "|------|-----------|----------|\n"
                "| 1 | Usuario autenticado | Continúa |\n"
                "| 1 ✗ | Sin token válido | Cierre `4001` |\n"
                "| 2 | `other_id` es amigo aceptado | Continúa |\n"
                "| 2 ✗ | No son amigos | Cierre `4003` |\n"
                "| 3 | Se obtiene/crea la conversación | Conexión aceptada |\n\n"
                "---\n\n"
                "### Mensajes: cliente → servidor\n\n"
                "Envía un objeto JSON con el texto del mensaje:\n\n"
                "```json\n"
                '{"missatge": "Hola, com estàs?"}\n'
                "```\n\n"
                "| Campo | Tipo | Descripción |\n"
                "|-------|------|-------------|\n"
                "| `missatge` | string | Texto del mensaje. Se hace trim; strings vacíos se ignoran. |\n\n"
                "---\n\n"
                "### Mensajes: servidor → cliente\n\n"
                "Se emite a **ambos participantes** cuando un mensaje es guardado:\n\n"
                "```json\n"
                "{\n"
                '  "id": 42,\n'
                '  "emissor_id": 7,\n'
                '  "emissor_username": "maria",\n'
                '  "contingut": "Hola, com estàs?",\n'
                '  "enviat_at": "2025-01-15T10:30:00Z"\n'
                "}\n"
                "```\n\n"
                "| Campo | Tipo | Descripción |\n"
                "|-------|------|-------------|\n"
                "| `id` | integer | PK del mensaje en BD. |\n"
                "| `emissor_id` | integer | ID del usuario que envió el mensaje. |\n"
                "| `emissor_username` | string | Username del emisor. |\n"
                "| `contingut` | string | Cuerpo del mensaje. |\n"
                "| `enviat_at` | string (ISO 8601) | Timestamp de persistencia. |\n\n"
                "---\n\n"
                "### Códigos de cierre\n\n"
                "| Código | Motivo |\n"
                "|--------|--------|\n"
                "| `4001` | No autenticado — token ausente o inválido. |\n"
                "| `4003` | Prohibido — los usuarios no son amigos aceptados. |\n\n"
                "---\n\n"
                "### Efectos secundarios\n\n"
                "- Cada mensaje se persiste en BD con `llegit = false`.\n"
                "- Si el receptor tiene `fcm_token`, se envía una push notification "
                "con el username del emisor y hasta 100 caracteres del mensaje.\n"
                "- Usa `PATCH /api/conversations/{chat_id}/read/` para marcar como leídos."
            ),
            "parameters": [
                {
                    "name": "other_id",
                    "in": "path",
                    "required": True,
                    "description": (
                        "ID del otro participante del chat. "
                        "El servidor deriva la conversación canónica a partir de ambos IDs."
                    ),
                    "schema": {"type": "integer", "example": 42},
                },
                {
                    "name": "token",
                    "in": "query",
                    "required": False,
                    "description": "JWT access token para autenticación WebSocket.",
                    "schema": {"type": "string"},
                },
            ],
            "responses": {
                "101": {
                    "description": "Switching Protocols — conexión WebSocket establecida."
                },
                "403": {
                    "description": (
                        "Conexión rechazada. Códigos de cierre WS:\n\n"
                        "- `4001` — no autenticado\n"
                        "- `4003` — no son amigos"
                    )
                },
            },
            "security": [{"BearerAuth": []}],
        }
    }

    return result