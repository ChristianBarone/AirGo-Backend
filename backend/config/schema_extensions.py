def add_websocket_paths(result, generator, request, public, **kwargs):
    ws_chat_tag = "WebSocket — Chat"
    ws_forum_tag = "WebSocket — Fòrum"

    if "tags" not in result:
        result["tags"] = []

    result["tags"].append(
        {
            "name": ws_chat_tag,
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

    result["tags"].append(
        {
            "name": ws_forum_tag,
            "description": (
                "Endpoints de tiempo real mediante **WebSocket** para foros públicos.\n\n"
                "> ⚠️ Estos endpoints no son HTTP — úsalos con un cliente WebSocket.\n\n"
                "**Autenticación:** el token JWT debe enviarse como query param:\n"
                "```\n"
                "ws://host/ws/forum/3/?token=<access_token>\n"
                "```"
            ),
        }
    )

    result["paths"]["/ws/chat/{other_id}/"] = {
        "get": {
            "tags": [ws_chat_tag],
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
                "```json\n"
                '{"missatge": "Hola, com estàs?"}\n'
                "```\n\n"
                "---\n\n"
                "### Mensajes: servidor → cliente\n\n"
                "```json\n"
                "{\n"
                '  "id": 42,\n'
                '  "emissor_id": 7,\n'
                '  "emissor_username": "maria",\n'
                '  "contingut": "Hola, com estàs?",\n'
                '  "enviat_at": "2025-01-15T10:30:00Z"\n'
                "}\n"
                "```\n\n"
                "### Códigos de cierre\n\n"
                "| Código | Motivo |\n"
                "|--------|--------|\n"
                "| `4001` | No autenticado. |\n"
                "| `4003` | No son amigos. |\n"
            ),
            "parameters": [
                {
                    "name": "other_id",
                    "in": "path",
                    "required": True,
                    "description": "ID del otro participante del chat.",
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
                    "description": "Códigos de cierre WS: `4001` no autenticado, `4003` no son amigos."
                },
            },
            "security": [{"BearerAuth": []}],
        }
    }

    result["paths"]["/ws/forum/{forum_id}/"] = {
        "get": {
            "tags": [ws_forum_tag],
            "summary": "Foro en tiempo real",
            "operationId": "ws_forum_connect",
            "x-websocket": True,
            "description": (
                "Abre una conexión WebSocket para el chat público de un foro.\n\n"
                "**URL:** `ws://host/ws/forum/{forum_id}/`\n\n"
                "---\n\n"
                "### Flujo de conexión\n\n"
                "| Paso | Condición | Resultado |\n"
                "|------|-----------|----------|\n"
                "| 1 | Usuario autenticado | Continúa |\n"
                "| 1 ✗ | Sin token válido | Cierre `4001` |\n"
                "| 2 | Foro existe | Conexión aceptada |\n"
                "| 2 ✗ | Foro no encontrado | Cierre `4004` |\n\n"
                "---\n\n"
                "### Mensajes: cliente → servidor\n\n"
                "```json\n"
                '{"missatge": "Hola a tothom!"}\n'
                "```\n\n"
                "---\n\n"
                "### Mensajes: servidor → cliente\n\n"
                "```json\n"
                "{\n"
                '  "id": 17,\n'
                '  "emissor_id": 3,\n'
                '  "emissor_username": "joan",\n'
                '  "contingut": "Hola a tothom!",\n'
                '  "enviat_at": "2025-01-15T10:30:00Z"\n'
                "}\n"
                "```\n\n"
                "### Códigos de cierre\n\n"
                "| Código | Motivo |\n"
                "|--------|--------|\n"
                "| `4001` | No autenticado. |\n"
                "| `4004` | Foro no encontrado. |\n"
            ),
            "parameters": [
                {
                    "name": "forum_id",
                    "in": "path",
                    "required": True,
                    "description": "ID del foro al que conectarse.",
                    "schema": {"type": "integer", "example": 3},
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
                "101": {"description": "Switching Protocols — conexión establecida."},
                "403": {
                    "description": "Códigos de cierre WS: `4001` no autenticado, `4004` foro no encontrado."
                },
            },
            "security": [{"BearerAuth": []}],
        }
    }

    return result
