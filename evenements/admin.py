from django.contrib import admin

from .models import Evenement, Participation


@admin.register(Evenement)
class EvenementAdmin(admin.ModelAdmin):
    list_display = ["titre", "type", "date_debut", "lieu", "est_inscription_requise"]
    list_filter = ["type", "est_inscription_requise"]
    search_fields = ["titre", "lieu"]


@admin.register(Participation)
class ParticipationAdmin(admin.ModelAdmin):
    list_display = ["evenement", "membre", "date_inscription"]
    list_filter = ["evenement"]
