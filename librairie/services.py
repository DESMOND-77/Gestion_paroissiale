import logging
from decimal import Decimal
from django.db.models import Sum

from .models import Article, Vente

logger = logging.getLogger(__name__)


class LibrairieService:
    """Service layer for Librairie business logic"""

    @staticmethod
    def create_article(nom, categorie, prix_unitaire, **kwargs):
        """Create a new article"""
        try:
            article = Article.objects.create(
                nom=nom,
                categorie=categorie,
                prix_unitaire=prix_unitaire,
                **kwargs
            )
            logger.info(f"Article created: {article.id} ({nom})")
            return article
        except Exception as e:
            logger.error(f"Error creating article: {e}")
            raise

    @staticmethod
    def record_vente(article, quantite, membre=None, enregistre_par=None):
        """Record a sale and update stock"""
        try:
            if article.stock_disponible < quantite:
                raise ValueError(f"Insufficient stock for {article.nom}")

            prix_total = article.prix_unitaire * Decimal(quantite)

            vente = Vente.objects.create(
                article=article,
                quantite=quantite,
                prix_total=prix_total,
                membre=membre,
                enregistre_par=enregistre_par
            )

            logger.info(f"Vente created: {vente.id} ({article.nom} × {quantite})")
            return vente
        except Exception as e:
            logger.error(f"Error recording vente: {e}")
            raise

    @staticmethod
    def check_stock_alerts():
        """Check articles below alert threshold"""
        articles_alerte = []
        for article in Article.objects.all():
            if article.stock_disponible <= article.seuil_alerte:
                articles_alerte.append(article)
        logger.debug(f"Stock alerts: {len(articles_alerte)} articles")
        return articles_alerte

    @staticmethod
    def get_articles_alerte():
        """Get articles on alert"""
        articles = []
        for article in Article.objects.all():
            if article.en_alerte:
                articles.append({
                    "id": article.id,
                    "nom": article.nom,
                    "stock": article.stock_disponible,
                    "seuil": article.seuil_alerte
                })
        logger.debug(f"Articles in alert: {len(articles)}")
        return articles

    @staticmethod
    def get_ventes_report(date_debut=None, date_fin=None):
        """Get sales report; both dates are optional."""
        qs = Vente.objects.all()
        if date_debut:
            qs = qs.filter(date__gte=date_debut)
        if date_fin:
            qs = qs.filter(date__lte=date_fin)
        result = qs.values("article__categorie").annotate(
            total_ventes=Sum("quantite"),
            total_montant=Sum("prix_total"),
        )
        logger.debug(f"Sales report: {date_debut} to {date_fin}")
        return result
