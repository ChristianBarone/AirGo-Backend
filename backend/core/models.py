import os
from django.db import models


class Idioma(models.TextChoices):
    CAT = "CAT", "Catalan"
    ES = "ES", "Español"
    ENG = "ENG", "English"


class Usuari(models.Model):
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)
    punts = models.IntegerField()
    profile_pic = models.ImageField(upload_to="profile_pics", blank=True, null=True)
    teBici = models.BooleanField(default=False)
    pes = models.FloatField()
    altura = models.FloatField()
    ratxa = models.IntegerField()
    idioma = models.CharField(max_length=3, choices=Idioma.choices, default=Idioma.ES)
    limitRutes = models.IntegerField()
    titol = models.CharField(max_length=100, blank=True)  # Título activo en el perfil
    insignies = models.ImageField(upload_to="insignies", blank=True, null=True)

    def __str__(self):
        return self.username

    def saveImage(self, *args, **kwargs):
        try:
            old = Usuari.objects.get(pk=self.pk)
            if old.profile_pic and old.profile_pic != self.profile_pic:
                if os.path.isfile(old.profile_pic.path):
                    os.remove(old.profile_pic.path)
        except Usuari.DoesNotExist:
            pass
        super().save(*args, **kwargs)


class Titol(models.Model):
    nom = models.CharField(max_length=100)
    descripcio = models.TextField(blank=True)

    def __str__(self):
        return self.nom


class UsuariTitol(models.Model):
    usuari = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="titols_desbloquejats"
    )
    titol = models.ForeignKey(Titol, on_delete=models.CASCADE)

    class Meta:
        unique_together = ["usuari", "titol"]

    def __str__(self):
        return f"{self.usuari.username} - {self.titol.nom}"


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
    hora = models.IntegerField()  # 8 o 18 por ejemplo
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["lat", "lon", "day_of_week", "hora"]


class Route(models.Model):
    name = models.CharField(max_length=100)
    start_location = models.CharField(max_length=200)
    end_location = models.CharField(max_length=200)
    distance = models.FloatField()
    air_quality = models.FloatField()
    is_safe = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class UsuariRuta(models.Model):
    usuari = models.ForeignKey(Usuari, on_delete=models.CASCADE, related_name='rutes_guardades')
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['usuari', 'route']

    def __str__(self):
        return f"{self.usuari.username} - {self.route.name}"
    
