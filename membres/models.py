from django.conf import settings
from django.db import models

from core.models import SyncableModel


class Membre(SyncableModel):
    SEXE_CHOICES = [("M", "Masculin"), ("F", "Féminin")]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="membre",
        null=True,
        blank=True,
    )
    nom = models.CharField(max_length=100, verbose_name="Nom")
    prenom = models.CharField(max_length=100, verbose_name="Prénom")
    date_naissance = models.DateField(null=True, blank=True)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True)
    sacrement = models.ForeignKey(
        "Sacrement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membres",
    )
    quartier = models.CharField(max_length=200, null=True, blank=True)

    est_baptise = models.BooleanField(default=False)
    est_confirme = models.BooleanField(default=False)
    groupe = models.ForeignKey(
        "groupes.Groupe",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="membres",
    )

    class Meta:
        verbose_name = "Membre"
        verbose_name_plural = "Membres"
        ordering = ["nom", "prenom"]
        indexes = [
            models.Index(fields=["nom", "prenom"]),
            models.Index(fields=["date_naissance"]),
        ]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


class Sacrement(SyncableModel):
    TYPE_CHOICES = [
        ("bapteme", "Baptême"),
        ("mariage", "Mariage"),
        ("confirmation", "Confirmation"),
        ("communion", "Communion"),
        ("funerailles", "Funérailles"),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    membre = models.ForeignKey(Membre, on_delete=models.CASCADE, related_name="sacrements")
    date = models.DateField()
    officiant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sacrements_officies",
    )
    observations = models.TextField(blank=True)

    class Meta:
        verbose_name = "Sacrement"
        verbose_name_plural = "Sacrements"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} — {self.membre}"
