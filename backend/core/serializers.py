from rest_framework import serializers
from .models import Route, Usuari, Titol, UsuariTitol, PlaEntrenament, TemplateExercici, Exercici, UsuariRuta
import os

class UsuariSerializer(serializers.ModelSerializer):
    profile_pic = serializers.SerializerMethodField()

    def get_profile_pic(self, obj):
        if not obj.profile_pic:
            return None
        base_url = os.environ.get("BASE_URL", "http://nattech.fib.upc.edu:40330")
        return f"{base_url}{obj.profile_pic.url}"

    def validate_username(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("El nombre de usuario no puede estar vacío")
        if len(value) <= 3:
            raise serializers.ValidationError("El username es demasiado corto")
        return value

    def validate_profile_pic(self, value):
        max_size = 2 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("La imagen no puede superar 2MB")
        return value

    def validate_pes(self, value):
        if value <= 0:
            raise serializers.ValidationError("El peso debe ser mayor a 0 kg.")
        return value

    def validate_altura(self, value):
        if value <= 0:
            raise serializers.ValidationError("La altura debe ser mayor a 0 cm.")
        return value

    class Meta:
        model = Usuari
        fields = "__all__"


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = "__all__"


class TitolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Titol
        fields = ["id", "nom", "descripcio"]


class UsuariTitolSerializer(serializers.ModelSerializer):
    titol = TitolSerializer(read_only=True)

    class Meta:
        model = UsuariTitol
        fields = ["titol"]

class ExerciciPolymorphicSerializer(serializers.ModelSerializer):
    # Esto traerá toda la info de las subclases de Exercici (Exterior/Ruta o res)
    detalls_especifics = serializers.SerializerMethodField()

    class Meta:
        model = Exercici
        fields = ['dataInici', 'dataFi', 'completat', 'tipusExercici', 'detalls_especifics']

    def get_detalls_especifics(self, obj):
        # Intentamos acceder a las subclases
        if hasattr(obj, 'exerciciruta'):
            return {"dist_objectiu_km": obj.exerciciruta.dist_objectiu_km,
                    "dist_feta_km": obj.exerciciruta.dist_feta_km,
                    "calories": obj.exerciciruta.calories,}
        if hasattr(obj, 'exerciciexterior'):
            return {"dist_feta_km": obj.exerciciexterior.dist_feta_km,
                    "calories": obj.exerciciexterior.calories}
        return None

class TemplateExerciciSerializer(serializers.ModelSerializer):
    # Esto traerá todos los ejercicios que tengan este template como 'template_origen'
    exercicis = ExerciciPolymorphicSerializer(many=True, read_only=True, source='instancies_exercici')

    class Meta:
        model = TemplateExercici
        fields = ['nom', 'descripcio', 'tipusExercici', 'exercicis']

class PlaEntrenamentSerializer(serializers.ModelSerializer):
    # Esto traerá todos los Templates presentes en el plan
    templates = TemplateExerciciSerializer(many=True, read_only=True)

    class Meta:
        model = PlaEntrenament
        fields = ['diesDurada', 'numEntrenamentsSetmanals', 'templates']


class UsuariRutaSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all(), source="route", write_only=True
    )

    class Meta:
        model = UsuariRuta
        fields = ["id", "route", "route_id", "saved_at"]
