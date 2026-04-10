import os
from django.db import models

## Atributos del esquema conceptual
class Idioma(models.TextChoices):
    ## OPCION = VALOR_GUARDADO_EN_BD , NOMBRE_LEGIBLE
    CAT = "CAT", "Catalan"
    ES = "ES", "Español"
    ENG = "ENG", "English"

class Usuari(models.Model):
    username = models.CharField(max_length=255, unique=True)
    punts = models.IntegerField()
    profile_pic = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    def __str__(self):
        return self.username
    teBici = models.BooleanField(default=False)
    pes = models.FloatField()
    altura = models.FloatField()
    ratxa = models.IntegerField()
    ## el default aqui es solo de fallback
    idioma = models.CharField(max_length=3, choices=Idioma.choices, default=Idioma.ES)
    limitRutes = models.IntegerField()
    titol = models.CharField(max_length=100)
    ## Cambiaria el 1..* a solo *
    insignies = models.ImageField(upload_to='insignies', blank=True, null=True)

    # Borra el path de la imagen antigua de la carpeta de profile_pics
    def saveImage(self, *args, **kwargs):
        try:
            old = Usuari.objects.get(pk=self.pk)
            if old.profile_pic and old.profile_pic != self.profile_pic:
                if os.path.isfile(old.profile_pic.path):
                    os.remove(old.profile_pic.path)
        except Usuari.DoesNotExist:
            pass

        super().save(*args, **kwargs)

class BicingEstacio(models.Model):
    station_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=200)
    lat = models.FloatField()
    lon = models.FloatField()
    capacity = models.IntegerField()
    bikes_available = models.IntegerField()
    docks_available = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class AirQualityHistoric(models.Model):
    lat = models.FloatField()
    lon = models.FloatField()
    aqi = models.FloatField()
    day_of_week = models.IntegerField()  # 0=lunes, 6=domingo
    hora = models.IntegerField()         # 8 o 18 por ejemplo
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Una entrada por ubicació, día y hora
        unique_together = ['lat', 'lon', 'day_of_week', 'hora']

class Route(models.Model):
    name = models.CharField(max_length=100)
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    distance = models.FloatField()
    air_quality = models.FloatField()
    is_safe = models.BooleanField(default=True)

    def __str__(self):
        return self.name