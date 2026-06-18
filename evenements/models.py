from django.conf import settings
from django.db import models


class Evenement(models.Model):
    TYPE_CHOICES = [
        ("messe", "Messe"),
        ("fete_liturgique", "Fête liturgique"),
        ("reunion", "Réunion"),
        ("kermesse", "Kermesse"),
        ("reservation", "Réservation"),
    ]

    titre = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, )
    description = models.TextField(blank=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField(null=True, blank=True)
    lieu = models.CharField(max_length=255, blank=True)
    est_inscription_requise = models.BooleanField(default=False)
    createur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="evenements_crees",
    )

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        ordering = ["-date_debut"]
        indexes = [
            models.Index(fields=["type"],name="evenement_type_idx"),
            models.Index(fields=["date_debut"],name="evenement_date_debut_idx"),
        ]

    def __str__(self):
        return self.titre


class Participation(models.Model):
    evenement = models.ForeignKey(Evenement, on_delete=models.CASCADE, related_name="participations")
    membre = models.ForeignKey(
        "membres.Membre", on_delete=models.CASCADE, related_name="participations"
    )
    date_inscription = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Participation"
        verbose_name_plural = "Participations"
        unique_together = ("evenement", "membre")

    def __str__(self):
        return f"{self.membre} → {self.evenement}"
