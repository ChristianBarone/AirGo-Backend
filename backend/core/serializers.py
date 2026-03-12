from rest_framework import serializers
from .models import Route
## Verificación cuando se recibe token Google Login
#  Se necesita de frontend:
#       POST /api/auth/google/
#       "token": "GOOGLE_ID_TOKEN" (en JSON)
class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'