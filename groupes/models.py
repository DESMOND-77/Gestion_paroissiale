from django.conf import settings
from django.db import models


class Groupe(models.Model):
    nom = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="groupes_responsable",
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Groupe"
        verbose_name_plural = "Groupes"
        ordering = ["nom"]
        indexes = [
            models.Index(fields=["nom"], name="groupe_nom_idx"),
            models.Index(fields=["responsable"], name="groupe_responsable_idx"),
        ]

    def __str__(self):
        return self.nom
