from rest_framework import serializers
from .models import (
    Route,
    Usuari,
    Titol,
    UsuariTitol,
    PlaEntrenament,
    TemplateExercici,
    Exercici,
    UsuariRuta,
    Amistat,
    Conversa,
    Missatge,
    Forum,
    ForumFavorit,
    Insignia,
    UsuariInsignia,
    PuntLog,
    ObjectiuExercici,
    MissioPermanent,
    MissioUsuari
)
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
            raise serializers.ValidationError(
                "El nombre de usuario no puede estar vacío"
            )
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


class AmistatSerializer(serializers.ModelSerializer):
    # Devuelve info básica del amigo, no del registro de amistad
    amic = serializers.SerializerMethodField()

    def get_amic(self, obj):
        # El "amigo" es el otro extremo de la relación
        request_user_id = self.context.get("request_user_id")
        amic = obj.receptor if obj.solicitant_id == request_user_id else obj.solicitant
        return {
            "id": amic.pk,
            "username": amic.username,
            "profile_pic": amic.profile_pic.url if amic.profile_pic else None,
            "titol": amic.titol,
            "punts": amic.punts,
        }

    class Meta:
        model = Amistat
        fields = ["id", "estat", "creat_at", "amic"]


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


class TemplateExerciciSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateExercici
        fields = ["id", "nom", "descripcio", "tipusExercici"]


class ObjectiuSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObjectiuExercici
        fields = ["id", "categoria", "descripcio", "recompensa"]


class ExerciciSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exercici
        fields = [
            "id",
            "template",
            "objectius",
            "medalla_obtinguda",
            "dataInici",
            "completat",
            "distanciaFeta",
            "distance_meters",
            "duration_seconds",
            "avg_speed_kmh",
            "route_points",
            "created_at",
            "sensacio",
            "comentari",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Si el ejercicio tiene una plantilla asignada, la serializamos con el detalle completo
        if instance.template:
            representation["template"] = TemplateExerciciSimpleSerializer(
                instance.template
            ).data
        # Obtenemos todos los objetivos asociados a este ejercicio
        representation["objectius"] = ObjectiuSimpleSerializer(
            instance.objectius.all(), many=True
        ).data
        return representation


class TemplateExerciciSerializer(serializers.ModelSerializer):
    exercicis = ExerciciSerializer(
        many=True, read_only=True, source="instancies_exercici"
    )

    class Meta:
        model = TemplateExercici
        fields = ["id", "nom", "descripcio", "tipusExercici", "exercicis"]


class PlaEntrenamentSerializer(serializers.ModelSerializer):
    templates = serializers.PrimaryKeyRelatedField(
        many=True, queryset=TemplateExercici.objects.all()
    )

    class Meta:
        model = PlaEntrenament
        fields = ["id", "diesDurada", "numEntrenamentsSetmanals", "templates"]

class MissioPermanentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissioPermanent
        fields = ['id', 'nom', 'descripcio', 'recompensa', 'metrica', 'fase_metrica', 'valor_objectiu']

class MissioUsuariSerializer(serializers.ModelSerializer):
    missio = MissioPermanentSerializer(read_only=True)

    class Meta:
        model = MissioUsuari
        fields = ['id', 'missio', 'completada']


class UsuariRutaSerializer(serializers.ModelSerializer):
    route = RouteSerializer(read_only=True)
    route_id = serializers.PrimaryKeyRelatedField(
        queryset=Route.objects.all(), source="route", write_only=True
    )

    class Meta:
        model = UsuariRuta
        fields = ["id", "route", "route_id", "saved_at"]


class MissatgeSerializer(serializers.ModelSerializer):
    emissor_username = serializers.CharField(source="emissor.username", read_only=True)

    class Meta:
        model = Missatge
        fields = [
            "id",
            "emissor",
            "emissor_username",
            "contingut",
            "enviat_at",
            "llegit",
        ]


class ConversaSerializer(serializers.ModelSerializer):
    other_user = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    def _other(self, obj):
        uid = self.context["request_user_id"]
        return obj.usuari_2 if obj.usuari_1_id == uid else obj.usuari_1

    def get_other_user(self, obj):
        u = self._other(obj)
        return {
            "id": u.pk,
            "username": u.username,
            "profile_pic": u.profile_pic.url if u.profile_pic else None,
        }

    def get_last_message(self, obj):
        last = obj.missatges.last()
        return (
            {"contingut": last.contingut, "enviat_at": last.enviat_at} if last else None
        )

    def get_unread_count(self, obj):
        uid = self.context["request_user_id"]
        return obj.missatges.filter(llegit=False).exclude(emissor_id=uid).count()

    chat_id = serializers.SerializerMethodField()

    def get_chat_id(self, obj):
        return f"{obj.usuari_1.pk}-{obj.usuari_2.pk}"

    class Meta:
        model = Conversa
        fields = ["chat_id", "other_user", "last_message", "unread_count", "creada_at"]


class ForumSerializer(serializers.ModelSerializer):
    creat_per = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Forum
        fields = ["id", "nom", "descripcio", "creat_per", "creat_at"]
        read_only_fields = ["id", "creat_per", "creat_at"]


class ForumFavoritSerializer(serializers.ModelSerializer):
    forum = ForumSerializer(read_only=True)

    class Meta:
        model = ForumFavorit
        fields = ["id", "forum", "afegit_at"]

        fields = ["id", "other_user", "last_message", "unread_count", "creada_at"]


class InsigniaSerializer(serializers.ModelSerializer):
    icona = serializers.SerializerMethodField()

    def get_icona(self, obj):
        if not obj.icona:
            return None
        base_url = os.environ.get("BASE_URL", "http://nattech.fib.upc.edu:40330")
        return f"{base_url}{obj.icona.url}"

    class Meta:
        model = Insignia
        fields = ["id", "nom", "descripcio", "icona", "tipus", "valor_requerit"]


class UsuariInsigniaSerializer(serializers.ModelSerializer):
    insignia = InsigniaSerializer(read_only=True)

    class Meta:
        model = UsuariInsignia
        fields = ["insignia", "data_guanyada"]


class PuntLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PuntLog
        fields = ["quantitat", "motiu", "data"]
