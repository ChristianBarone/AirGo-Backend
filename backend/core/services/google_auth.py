from google.oauth2 import id_token
from google.auth.transport import requests

GOOGLE_CLIENT_ID = "500956123135-fidfq8ecmd60e6pak1e4ds5r1ai9sojp.apps.googleusercontent.com"

def verify_google_token(token):

    idinfo = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        GOOGLE_CLIENT_ID
    )

    return {
        "email": idinfo["email"],
        "name": idinfo.get("name", ""),
        "picture": idinfo.get("picture", "")
    }