from rest_framework import serializers

## Verificación cuando se recibe token Google Login
#  Se necesita de frontend:
#       POST /api/auth/google/
#       "token": "GOOGLE_ID_TOKEN" (en JSON)
class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()