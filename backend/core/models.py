# core/models.py
from django.db import models

## Atributos del esquema conceptual
class Idioma(models.TextChoices):
    ## OPCION = VALOR_GUARDADO_EN_BD , NOMBRE_LEGIBLE
    CAT = "CAT", "Catalan"
    ES = "ES", "Español"
    ENG = "ENG", "English"

class Usuari(models.Model):
    username = models.CharField(max_length=25)
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


class Route(models.Model):
    name = models.CharField(max_length=100)
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    distance = models.FloatField()
    air_quality = models.FloatField()
    is_safe = models.BooleanField(default=True)

    def __str__(self):
        return self.name