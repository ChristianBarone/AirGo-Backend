from django.contrib import admin
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
    BicingEstacio,
    AirQualityHistoric,
)

# ── Usuarios y Perfiles ───────────────────────────────────────────────────────


@admin.register(Usuari)
class UsuariAdmin(admin.ModelAdmin):
    # Solo campos que existen en tu models.py actual
    list_display = ("username", "punts", "pes", "altura", "idioma", "ratxa")
    search_fields = ("username", "google_id")
    list_filter = ("idioma", "dificultatPla", "teBici")


@admin.register(Amistat)
class AmistatAdmin(admin.ModelAdmin):
    list_display = ("id", "solicitant", "receptor", "estat", "creat_at")
    list_filter = ("estat", "creat_at")


# ── Rutas y Bicing ────────────────────────────────────────────────────────────

admin.site.register(Route)


@admin.register(UsuariRuta)
class UsuariRutaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuari", "route", "saved_at")


@admin.register(BicingEstacio)
class BicingEstacioAdmin(admin.ModelAdmin):
    list_display = (
        "station_id",
        "name",
        "capacity",
        "bikes_available",
        "docks_available",
    )
    search_fields = ("name",)


@admin.register(AirQualityHistoric)
class AirQualityHistoricAdmin(admin.ModelAdmin):
    list_display = ("lat", "lon", "aqi", "day_of_week", "hora")
    list_filter = ("day_of_week", "hora")


# ── Entrenamientos y Ejercicios ───────────────────────────────────────────────


@admin.register(PlaEntrenament)
class PlaEntrenamentAdmin(admin.ModelAdmin):
    list_display = ("id", "diesDurada", "numEntrenamentsSetmanals")


@admin.register(TemplateExercici)
class TemplateExerciciAdmin(admin.ModelAdmin):
    list_display = ("nom", "tipusExercici")
    search_fields = ("nom",)


@admin.register(Exercici)
class ExerciciAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "usuari",
        "dataInici",
        "completat",
        "distanciaObjectiu",
        "distanciaFeta",
    )
    list_filter = ("completat",)


# ── Chat y Mensajes ───────────────────────────────────────────────────────────


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuari_1", "usuari_2", "creada_at")


@admin.register(Missatge)
class MissatgeAdmin(admin.ModelAdmin):
    list_display = ("emissor", "conversa", "enviat_at", "llegit")
    list_filter = ("llegit", "enviat_at")
    search_fields = ("contingut",)


# ── Foros ─────────────────────────────────────────────────────────────────────


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ("nom", "creat_per", "creat_at")
    search_fields = ("nom", "descripcio")


@admin.register(ForumFavorit)
class ForumFavoritAdmin(admin.ModelAdmin):
    list_display = ("usuari", "forum", "afegit_at")


# ── Títulos y Logros ──────────────────────────────────────────────────────────


@admin.register(Titol)
class TitolAdmin(admin.ModelAdmin):
    list_display = ("nom", "descripcio")


@admin.register(UsuariTitol)
class UsuariTitolAdmin(admin.ModelAdmin):
    list_display = ("usuari", "titol")
