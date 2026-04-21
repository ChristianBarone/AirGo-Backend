from rest_framework import serializers
from .models import Route, Usuari, Titol, UsuariTitol, UsuariRuta
import os

class UsuariSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    def get_profile_pic(self, obj):
        if not obj.profile_pic:
            return None
        base_url = os.environ.get("BASE_URL", "http://nattech.fib.upc.edu:40330")
        return f"{base_url}{obj.profile_pic.url}"

    def validate_username(self, value):
        if len(value) <= 3:
            raise serializers.ValidationError("El username es demasiado corto")
        return value

    def validate_profile_pic(self, value):
        max_size = 2 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("La imagen no puede superar 2MB")
        return value

    class Meta:
        model = Usuari
        fields = '__all__'


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = '__all__'


class TitolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Titol
        fields = ['id', 'nom', 'descripcio']


class UsuariTitolSerializer(serializers.ModelSerializer):
    titol = TitolSerializer(read_only=True)

    class Meta:
        model = UsuariTitol
        fields = ['titol']


class UsuariRutaSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all(), source='route', write_only=True
    )

    class Meta:
        model = UsuariRuta
        fields = ['id', 'route', 'route_id', 'saved_at']