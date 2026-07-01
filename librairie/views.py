import logging
import datetime
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.base_view import BaseAPIView
from core.permissions import IsAdmin, IsSecretaryOrAbove
from core.response import standardized_response
from finances.models import Transaction
from membres.models import Membre
from .models import Article, Vente
from .serializers import ArticleSerializer, VenteSerializer
from .services import LibrairieService

logger = logging.getLogger(__name__)


class ArticleListView(BaseAPIView):
    """
    GET  /api/librairie/articles/   — liste
    POST /api/librairie/articles/   — création
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsSecretaryOrAbove()]
        return [IsAuthenticated()]

    def get(self, request):
        logger.debug(f"Listing articles for user {request.user}")
        qs = Article.objects.all()
        logger.info(f"Retrieved {qs.count()} articles")
        return Response(standardized_response(data=ArticleSerializer(qs, many=True).data))

    def post(self, request):
        logger.info(f"Creating article by user {request.user}: {request.data.get('nom', 'Unknown')}")
        serializer = ArticleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        article = LibrairieService.create_article(
            nom=validated["nom"],
            categorie=validated["categorie"],
            prix_unitaire=validated["prix_unitaire"],
            **{k: v for k, v in validated.items() if k not in ("nom", "categorie", "prix_unitaire")},
        )
        logger.info(f"Article created successfully: {article.id} ({article.nom})")
        return Response(
            standardized_response(data=ArticleSerializer(article).data, message="Article ajouté"),
            status=status.HTTP_201_CREATED,
        )


class ArticleDetailView(BaseAPIView):
    """
    GET    /api/librairie/articles/<pk>/    — détail
    PUT    /api/librairie/articles/<pk>/    — mise à jour complète
    PATCH  /api/librairie/articles/<pk>/    — mise à jour partielle
    DELETE /api/librairie/articles/<pk>/    — suppression (admin)
    """

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        if self.request.method == "DELETE":
            return [IsAdmin()]
        return [IsSecretaryOrAbove()]

    def _get_article(self, pk):
        return get_object_or_404(Article, pk=pk)

    def get(self, request, pk):
        article = self._get_article(pk)
        logger.debug(f"Retrieving article {pk} for user {request.user}")
        return Response(standardized_response(data=ArticleSerializer(article).data))

    def put(self, request, pk):
        article = self._get_article(pk)
        logger.info(f"Updating article {pk} by user {request.user}")
        serializer = ArticleSerializer(article, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Article {pk} updated successfully")
        return Response(standardized_response(data=serializer.data, message="Article modifié"))

    def patch(self, request, pk):
        article = self._get_article(pk)
        logger.info(f"Partial update article {pk} by user {request.user}")
        serializer = ArticleSerializer(article, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Article {pk} updated successfully")
        return Response(standardized_response(data=serializer.data, message="Article modifié"))

    def delete(self, request, pk):
        article = self._get_article(pk)
        logger.warning(f"Deleting article {pk} ({article.nom}) by user {request.user}")
        article.delete()
        logger.info(f"Article {pk} deleted successfully")
        return Response(standardized_response(message="Article supprimé"), status=status.HTTP_204_NO_CONTENT)


class ArticleAlertesView(BaseAPIView):
    """
    GET /api/librairie/alertes/     — articles dont le stock est sous le seuil d'alerte
    """

    permission_classes = [IsSecretaryOrAbove]

    def get(self, request):
        logger.debug(f"Retrieving alert articles for user {request.user}")
        try:
            articles_alerte = LibrairieService.get_articles_alerte()
            logger.info(f"Found {len(articles_alerte)} articles in alert")
            return Response(standardized_response(data=articles_alerte))
        except Exception as e:
            logger.error(f"Error retrieving alertes: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )


class VenteListView(BaseAPIView):
    """
    GET  /api/librairie/ventes/     — liste des ventes
    POST /api/librairie/ventes/     — enregistrer une vente (validation stock via service)
    """

    permission_classes = [IsSecretaryOrAbove]

    def get(self, request):
        logger.debug(f"Listing ventes for user {request.user}")
        qs = Vente.objects.select_related("article", "membre", "enregistre_par").all()
        logger.info(f"Retrieved {qs.count()} ventes")
        return Response(standardized_response(data=VenteSerializer(qs, many=True).data))

    def post(self, request):
        logger.info(f"Creating vente by user {request.user}: {request.data}")
        serializer = VenteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        article = validated["article"]
        quantite = validated["quantite"]
        membre = validated.get("membre")

        try:
            vente = LibrairieService.record_vente(
                article=article,
                quantite=quantite,
                membre=membre,
                enregistre_par=request.user,
            )
            logger.info(f"Vente {vente.id} created via service")
        except ValueError as e:
            logger.warning(f"Stock insuffisant: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Enregistrer la transaction financière correspondante
        try:
            montant = article.prix_unitaire * Decimal(quantite)
            transaction = Transaction.objects.create(
                categorie="librairie",
                type="recette",
                description=f"Vente: {article.nom} × {quantite}, par {request.user.prenom}",
                montant=montant,
                date=datetime.datetime.now(),
                enregistre_par=request.user,
                membre=membre,
            )
            logger.info(f"Transaction {transaction.id} created for vente {vente.id}: {montant} FCFA")
        except Exception as e:
            logger.error(f"Error creating transaction for vente {vente.id}: {e}")

        return Response(
            standardized_response(data=VenteSerializer(vente).data, message="Vente enregistrée"),
            status=status.HTTP_201_CREATED,
        )


class VenteRapportView(BaseAPIView):
    """
    GET /api/librairie/ventes/rapport/
        Paramètres optionnels: ?date_debut=&date_fin=
        Retourne les ventes agrégées par catégorie d'article.
    """

    permission_classes = [IsSecretaryOrAbove]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        logger.info(f"Generating vente report for user {request.user} ({date_debut} → {date_fin})")

        try:
            rapport = LibrairieService.get_ventes_report(date_debut, date_fin)
            return Response(standardized_response(data={
                "periode": {"debut": date_debut, "fin": date_fin},
                "par_categorie": list(rapport),
            }))
        except Exception as e:
            logger.error(f"Error generating vente rapport: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )
