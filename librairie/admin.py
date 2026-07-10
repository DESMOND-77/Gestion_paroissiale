from django.contrib import admin

from .models import Article, Vente


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ["nom", "categorie", "prix_unitaire", "stock_disponible", "seuil_alerte", "en_alerte"]
    list_filter = ["categorie"]
    search_fields = ["nom"]


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = ["article", "quantite", "prix_total", "date", "membre"]
    list_filter = ["article__categorie"]
    # date_hierarchy = "date"
