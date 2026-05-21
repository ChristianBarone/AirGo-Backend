from django.contrib import admin
from django.utils.html import format_html

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
    Insignia,
    UsuariInsignia,
    PuntLog,
)


# ── Usuarios y Perfiles ───────────────────────────────────────────────────────
@admin.register(Usuari)
class UsuariAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "punts",
        "pes",
        "altura",
        "idioma",
        "ratxa",
        "estat_compte",
    )
    search_fields = ("username", "google_id")
    list_filter = ("idioma", "dificultatPla", "teBici", "is_active")
    actions = ["bloquejar_usuaris", "desbloquejar_usuaris"]

    def estat_compte(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;">✅ Actiu</span>')
        return format_html('<span style="color:red;">🔒 Bloquejat</span>')

    estat_compte.short_description = "Estat"

    @admin.action(description="🔒 Bloquejar usuaris seleccionats")
    def bloquejar_usuaris(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} usuari(s) bloquejat(s).")

    @admin.action(description="🔓 Desbloquejar usuaris seleccionats")
    def desbloquejar_usuaris(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} usuari(s) desbloquejat(s).")


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


# ── Gamificación ──────────────────────────────────────────────────────────
@admin.register(Titol)
class TitolAdmin(admin.ModelAdmin):
    list_display = ("nom", "descripcio", "punts_minims")


@admin.register(UsuariTitol)
class UsuariTitolAdmin(admin.ModelAdmin):
    list_display = ("usuari", "titol")


@admin.register(Insignia)
class InsigniaAdmin(admin.ModelAdmin):
    list_display = ("nom", "tipus", "valor_requerit", "mostrar_icona")
    list_filter = ("tipus",)
    search_fields = ("nom",)

    def mostrar_icona(self, obj):
        if obj.icona:
            url_imatge = obj.icona.url
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: contain;" />',
                url_imatge,
            )
        return "Sense icona"

    mostrar_icona.short_description = "Previsualització Icona"


@admin.register(UsuariInsignia)
class UsuariInsigniaAdmin(admin.ModelAdmin):
    list_display = ("usuari", "insignia")
    list_filter = ("insignia",)


@admin.register(PuntLog)
class PuntLogAdmin(admin.ModelAdmin):
    list_display = ("usuari", "quantitat", "motiu", "data")
    list_filter = ("data",)
    search_fields = ("usuari__username", "motiu")
