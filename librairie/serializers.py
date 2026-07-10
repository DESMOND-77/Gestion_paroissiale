from rest_framework import serializers

from core.serializers import WritableIDModelSerializer

from .models import Article, Vente


class ArticleSerializer(WritableIDModelSerializer):
    categorie_display = serializers.CharField(source="get_categorie_display", read_only=True)
    en_alerte = serializers.ReadOnlyField()

    class Meta:
        model = Article
        fields = [
            "id", "nom", "description", "categorie", "categorie_display",
            "prix_unitaire", "stock_disponible", "seuil_alerte", "en_alerte", "date_ajout",
        ]
        read_only_fields = ["date_ajout ", "en_alerte", "categorie_display"]


class VenteSerializer(WritableIDModelSerializer):
    article_nom = serializers.CharField(source="article.nom", read_only=True)
    membre_nom = serializers.SerializerMethodField()
    enregistre_par_nom = serializers.SerializerMethodField()

    class Meta:
        model = Vente
        fields = [
            "id", "article", "article_nom", "quantite", "prix_total",
            "date", "membre", "membre_nom", "enregistre_par", "enregistre_par_nom",
        ]
        read_only_fields = ["prix_total", "date", "article_nom", "membre_nom", "enregistre_par_nom"]

    def get_membre_nom(self, obj):
        return str(obj.membre) if obj.membre else None

    def get_enregistre_par_nom(self, obj):
        if obj.enregistre_par:
            return obj.enregistre_par.full_name or obj.enregistre_par.email
        return None

    def validate(self, data):
        article = data.get("article")
        quantite = data.get("quantite", 0)
        if article and article.stock_disponible < quantite:
            raise serializers.ValidationError(
                {"quantite": f"Stock insuffisant. Disponible : {article.stock_disponible}"}
            )
        return data
