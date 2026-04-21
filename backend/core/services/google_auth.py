from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = "CLIENT_ID"


def verify_google_token(token):

    idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

    return {
        "email": idinfo["email"],
        "name": idinfo.get("name", ""),
        "picture": idinfo.get("picture", ""),
    }
