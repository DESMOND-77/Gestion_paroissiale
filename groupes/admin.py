from django.contrib import admin

from .models import Groupe


@admin.register(Groupe)
class GroupeAdmin(admin.ModelAdmin):
    list_display = ["nom", "responsable", "date_creation"]
    search_fields = ["nom"]
