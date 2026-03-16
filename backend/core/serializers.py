from rest_framework import serializers
from .models import Route
from .models import Usuari

# Serializer clase Usuari
#  Se necesita de frontend:
#  Cambio de cualquier atributo de usuario (nombre, título, teBici):
#       PATCH /api/usuaris/<id>/
#  Cambio de imagen de perfil:
#       PATCH /api/usuaris/me/profile-pic/
class UsuariSerializer(serializers.ModelSerializer):
    # Username válido si tiene 4 o + caracteres
    def validate_username(self, value):
        if len(value) <= 3:
            raise serializers.ValidationError("El username es demasiado corto")
        return value

    # Imagen de perfil válida si tamaño < 2MB
    def validate_profile_pic(self, value):
        max_size = 2 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("La imagen no puede superar 2MB")
        return value

    class Meta:
        model = Usuari
        fields = '__all__'

# Verificación cuando se recibe token Google Login
#  Se necesita de frontend:
#       POST /api/auth/google/
#       "token": "GOOGLE_ID_TOKEN" (en JSON)
class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()

class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'