from django.contrib import admin
from .models import Membre, Sacrement


@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ["nom", "prenom", "groupe", "est_baptise", "est_confirme"]
    list_filter = ["groupe", "sexe", "est_baptise", "est_confirme"]
    search_fields = ["nom", "prenom", "email", ]


@admin.register(Sacrement)
class SacrementAdmin(admin.ModelAdmin):
    list_display = ["type", "membre", "date", "officiant"]
    list_filter = ["type"]
    search_fields = ["membre__nom", "membre__prenom"]
