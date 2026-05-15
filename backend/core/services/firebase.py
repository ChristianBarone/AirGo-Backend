import os
import firebase_admin
from firebase_admin import credentials, messaging

CREDENTIALS_PATH = os.path.join(
    os.path.dirname(__file__), "../../firebase-credentials.json"
)


def _init_firebase():
    if not firebase_admin._apps:
        if not os.path.exists(CREDENTIALS_PATH):
            print(
                "WARNING: firebase-credentials.json no encontrado, notificaciones push desactivadas"
            )
            return False
        cred = credentials.Certificate(CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred)
    return True


def send_push_notification(fcm_token: str, title: str, body: str, data: dict = None):
    if not _init_firebase():
        return  # sin credenciales, ignorar silenciosamente

    try:
        message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data={str(k): str(v) for k, v in (data or {}).items()},
            token=fcm_token,
            android=messaging.AndroidConfig(priority="high"),
        )
        messaging.send(message)
    except Exception as e:
        print(f"FCM error: {e}")
