import os
from django.db import models
from datetime import date


class Idioma(models.TextChoices):
    CAT = "CAT", "Catalan"
    ES = "ES", "Español"
    ENG = "ENG", "English"


class TExercici(models.TextChoices):
    CAMINAR = "CAM", "Caminar"
    BICI = "BIC", "Bici"


class DifPlaEntrenament(models.TextChoices):
    PRINCIPIANT = "PRI", "Principiant"
    INTERMEDI = "INT", "Intermedi"
    AVANÇAT = "AVA", "Avançat"


class CategoriaObjectiu(models.TextChoices):
    OR = "OR", "Or"
    PLATA = "PLA", "Plata"
    BRONZE = "BRO", "Bronze"


class SensacioExercici(models.IntegerChoices):
    MOLT_MALAMENT = 1, "Molt Malament"
    MALAMENT = 2, "Malament"
    NORMAL = 3, "Normal"
    BE = 4, "Be"
    MOLT_BE = 5, "Molt Be"


class Usuari(models.Model):
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    username = models.CharField(max_length=255, unique=True)
    punts = models.IntegerField()
    profile_pic = models.ImageField(upload_to="profile_pics", blank=True, null=True)
    teBici = models.BooleanField(default=False)
    pes = models.FloatField()
    altura = models.FloatField()
    ratxa = models.IntegerField()
    dificultatPla = models.CharField(
        max_length=3,
        choices=DifPlaEntrenament.choices,
        default=DifPlaEntrenament.INTERMEDI,
    )
    idioma = models.CharField(max_length=3, choices=Idioma.choices, default=Idioma.ES)
    limitRutes = models.IntegerField()
    titol = models.CharField(max_length=100, blank=True)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    plans = models.ManyToManyField("PlaEntrenament", blank=True, related_name="usuaris")
    ultima_activitat = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    titols_pendents = models.IntegerField(default=0)
    ultim_milestone_titols = models.IntegerField(default=0)

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

    def actualitzarPerfilQuestionari(self, dades):
        camps_permesos = ["titol", "pes", "altura", "dificultatPla"]
        hi_ha_canvis = False

        for camp, valor in dades.items():
            if camp in camps_permesos:
                setattr(self, camp, valor)
                hi_ha_canvis = True

        if hi_ha_canvis:
            self.save()
        return hi_ha_canvis

    def verificar_i_resetejar_ratxa(self):
        if self.ultima_activitat:
            avui = date.today()
            diferencia = (avui - self.ultima_activitat).days

            # Si han passat més de 3 dies sense fer exercici, la ratxa es perd
            if diferencia > 3:
                self.ratxa = 0
                self.save(update_fields=["ratxa"])
                return True
        return False


class EstatAmistat(models.TextChoices):
    PENDING = "PEN", "Pendent"
    ACCEPTED = "ACC", "Acceptada"
    REJECTED = "REJ", "Rebutjada"


class Amistat(models.Model):
    solicitant = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="amistats_enviades"
    )
    receptor = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="amistats_rebudes"
    )
    estat = models.CharField(
        max_length=3, choices=EstatAmistat.choices, default=EstatAmistat.PENDING
    )
    creat_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["solicitant", "receptor"]
        constraints = [
            # Evita que A→B y B→A coexistan
            models.CheckConstraint(
                check=~models.Q(solicitant=models.F("receptor")),
                name="no_self_friendship",
            )
        ]

    def __str__(self):
        return f"{self.solicitant} → {self.receptor} ({self.estat})"


class Titol(models.Model):
    nom = models.CharField(max_length=100)
    descripcio = models.TextField(blank=True)
    punts_minims = models.IntegerField(default=0)

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
    start_address = models.CharField(max_length=300, default="")
    end_location = models.CharField(max_length=200)
    end_address = models.CharField(max_length=300, default="")
    distance = models.FloatField()
    air_quality = models.FloatField()
    is_safe = models.BooleanField(default=True)
    route_points = models.JSONField(default=list)

    def __str__(self):
        return self.name


class PlaEntrenament(models.Model):
    diesDurada = models.IntegerField(default=0)
    numEntrenamentsSetmanals = models.IntegerField(default=0)
    esport = models.IntegerField(null=True, blank=True)
    nivell = models.IntegerField(null=True, blank=True)
    diesSetmana = models.JSONField(default=list, blank=True)
    dataFi = models.DateField(null=True, blank=True)
    templates = models.ManyToManyField(
        "TemplateExercici", related_name="plans", blank=True
    )


class TemplateExercici(models.Model):
    nom = models.CharField(max_length=100)
    descripcio = models.TextField(blank=True)
    dificutat = models.CharField(
        max_length=3,
        choices=DifPlaEntrenament.choices,
        default=DifPlaEntrenament.PRINCIPIANT,
    )
    tipusExercici = models.CharField(
        max_length=3, choices=TExercici.choices, default=TExercici.CAMINAR
    )

    def __str__(self):
        return self.nom


class ObjectiuExercici(models.Model):
    categoria = models.CharField(
        max_length=3,
        choices=CategoriaObjectiu.choices,
        default=CategoriaObjectiu.BRONZE,
    )
    descripcio = models.TextField(blank=True)
    recompensa = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.categoria} - {self.descripcio[:20]}"


class Exercici(models.Model):
    usuari = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="exercicis"
    )
    template = models.ForeignKey(
        "TemplateExercici",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="instancies_exercici",
    )
    objectius = models.ManyToManyField(
        ObjectiuExercici,
        blank=True,
        related_name="exercicis_asociats",
    )
    medalla_obtinguda = models.CharField(
        max_length=3, choices=CategoriaObjectiu.choices, null=True, blank=True
    )
    dataInici = models.DateTimeField(null=True, blank=True)
    completat = models.BooleanField(default=False)
    distanciaFeta = models.FloatField(default=0.0)
    distance_meters = models.FloatField(default=0.0)
    duration_seconds = models.IntegerField(default=0)
    avg_speed_kmh = models.FloatField(default=0.0)
    route_points = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    sensacio = models.CharField(
        max_length=3, choices=SensacioExercici.choices, default=SensacioExercici.NORMAL
    )
    comentari = models.TextField(blank=True)

    def __str__(self):
        return f"{self.usuari.username} - {self.distance_meters}m"


class UsuariRuta(models.Model):
    usuari = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="rutes_guardades"
    )
    route = models.ForeignKey(Route, on_delete=models.CASCADE)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["usuari", "route"]

    def __str__(self):
        return f"{self.usuari.username} - {self.route.name}"


class Conversa(models.Model):
    """
    Conversación entre exactamente dos usuarios.
    Siempre guardamos usuari_1.pk < usuari_2.pk para evitar duplicados.
    """

    usuari_1 = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="converses_com_1"
    )
    usuari_2 = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="converses_com_2"
    )
    creada_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["usuari_1", "usuari_2"]

    @staticmethod
    def entre(u1: "Usuari", u2: "Usuari") -> "Conversa":
        """Devuelve (o crea) la conversación canónica entre dos usuarios."""
        a, b = (u1, u2) if u1.pk < u2.pk else (u2, u1)
        conversa, _ = Conversa.objects.get_or_create(usuari_1=a, usuari_2=b)
        return conversa

    def __str__(self):
        return f"Conversa {self.usuari_1} ↔ {self.usuari_2}"


class Missatge(models.Model):
    conversa = models.ForeignKey(
        Conversa, on_delete=models.CASCADE, related_name="missatges"
    )
    emissor = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="missatges_enviats"
    )
    contingut = models.TextField()
    enviat_at = models.DateTimeField(auto_now_add=True)
    llegit = models.BooleanField(default=False)

    class Meta:
        ordering = ["enviat_at"]

    def __str__(self):
        return f"{self.emissor.username}: {self.contingut[:40]}"


class Forum(models.Model):
    nom = models.CharField(max_length=100)
    descripcio = models.CharField(max_length=500, blank=True)
    creat_per = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="forums_creats"
    )
    creat_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom


class ForumFavorit(models.Model):
    usuari = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="forums_favorits"
    )
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="favorits")
    afegit_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["usuari", "forum"]

    def __str__(self):
        return f"{self.usuari.username} → {self.forum.nom}"


class Insignia(models.Model):
    nom = models.CharField(max_length=100)
    descripcio = models.TextField()
    icona = models.ImageField(upload_to="insignies", null=True, blank=True)

    tipus = models.CharField(max_length=50)
    valor_requerit = models.FloatField()

    def __str__(self):
        return self.nom


class UsuariInsignia(models.Model):
    usuari = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="insignies_guanyades"
    )
    insignia = models.ForeignKey(Insignia, on_delete=models.CASCADE)
    data_guanyada = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["usuari", "insignia"]

    def __str__(self):
        return f"{self.usuari.username} - {self.insignia.nom}"


class PuntLog(models.Model):
    usuari = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="logs_punts"
    )
    quantitat = models.IntegerField()
    motiu = models.CharField(max_length=255)
    data = models.DateTimeField(auto_now_add=True)


class MissatgeForum(models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE, related_name="missatges")
    emissor = models.ForeignKey(
        Usuari, on_delete=models.CASCADE, related_name="missatges_forum_enviats"
    )
    contingut = models.TextField()
    enviat_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["enviat_at"]

    def __str__(self):
        return f"{self.emissor.username}@{self.forum.nom}: {self.contingut[:40]}"
