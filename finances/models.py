from django.conf import settings
from django.db import models

from core.models import SyncableModel


class Transaction(SyncableModel):
    TYPE_CHOICES = [("recette", "Recette"), ("depense", "Dépense")]
    CATEGORIE_CHOICES = [
        ("quete", "Quête"),
        ("don", "Don"),
        ("location", "Location"),
        ("librairie", "Librairie"),
        ("autre", "Autre"),
    ]

    type = models.CharField(max_length=10, choices=TYPE_CHOICES, )
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, )
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    date = models.DateField()
    membre = models.ForeignKey(
        "membres.Membre",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    enregistre_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="transactions_enregistrees",
    )

    class Meta:
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["categorie"], name="transaction_categorie_idx"),
            models.Index(fields=["type", "date"], name="transaction_type_idx"),
            models.Index(fields=["date"], name="transaction_date_idx"),
        ]

    def __str__(self):
        return f"{self.get_type_display()} — {self.montant} FCFA ({self.date})"
