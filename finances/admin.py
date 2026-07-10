from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["type", "categorie", "montant", "date", "membre", "enregistre_par"]
    list_filter = ["type", "categorie"]
    search_fields = ["description", "membre__nom"]
    date_hierarchy = "date"
