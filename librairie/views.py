import logging
import datetime
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import User
from core.permissions import IsAdmin, IsSecretaryOrAbove
from accounts.core.response import standardized_response
from finances.models import Transaction
from finances.serializers import TransactionSerializer
from membres.models import Membre
from .models import Article, Vente
from .serializers import ArticleSerializer, VenteSerializer

logger = logging.getLogger(__name__)


class ArticleViewSet(viewsets.ModelViewSet):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]
        if self.action in ("list", "retrieve", "alertes"):
            return [IsAuthenticated()]
        return [IsSecretaryOrAbove()]

    def list(self, request, *args, **kwargs):
        logger.debug(f"Listing articles for user {request.user}")
        qs = self.get_queryset()
        logger.info(f"Retrieved {qs.count()} articles")
        serializer = self.get_serializer(qs, many=True)
        return Response(standardized_response(data=serializer.data))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.debug(f"Retrieving article {instance.id} for user {request.user}")
        serializer = self.get_serializer(instance)
        return Response(standardized_response(data=serializer.data))

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating article by user {request.user}: {request.data.get('nom', 'Unknown')}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        article = serializer.save()
        logger.info(f"Article created successfully: {article.id} ({article.nom})")
        return Response(
            standardized_response(data=serializer.data, message="Article ajouté"),
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        logger.info(f"Updating article {instance.id} by user {request.user} (partial={partial})")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(f"Article {instance.id} updated successfully")
        return Response(
            standardized_response(data=serializer.data, message="Article modifié")
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.warning(f"Deleting article {instance.id} ({instance.nom}) by user {request.user}")
        instance.delete()
        logger.info(f"Article {instance.id} deleted successfully")
        return Response(
            standardized_response(message="Article supprimé"),
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=False, methods=["get"], permission_classes=[IsSecretaryOrAbove])
    def alertes(self, request):
        logger.debug(f"Retrieving alert articles for user {request.user}")
        articles_alerte = [a for a in self.get_queryset() if a.en_alerte]
        logger.info(f"Found {len(articles_alerte)} articles in alert")
        serializer = self.get_serializer(articles_alerte, many=True)
        return Response(standardized_response(data=serializer.data))


class VenteViewSet(viewsets.ModelViewSet):
    queryset = Vente.objects.select_related("article", "membre", "enregistre_par").all()
    serializer_class = VenteSerializer
    transaction_model = Transaction
    membre_model = Membre
    article_model = Article
    http_method_names = ["get", "post", "head", "options"]
    permission_classes = [IsSecretaryOrAbove]

    def list(self, request, *args, **kwargs):
        logger.debug(f"Listing ventes for user {request.user}")
        qs = self.get_queryset()
        logger.info(f"Retrieved {qs.count()} ventes")
        serializer = self.get_serializer(qs, many=True)
        return Response(standardized_response(data=serializer.data))

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating vente by user {request.user}: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vente = serializer.save(enregistre_par=request.user)
        logger.debug(f"Vente {vente.id} saved, creating transaction")

        try:
            if serializer.is_valid:
                article = self.article_model.objects.get(id=request.data.get("article"))
                quantite = request.data.get("quantite")
                montant = article.prix_unitaire * quantite

                transaction = self.transaction_model.objects.create(
                    categorie="librairie",
                    type="recette",
                    description=f"Vente de l'article: {article.nom}, Qte: {quantite}, par: {request.user.first_name}",
                    montant=montant,
                    date=datetime.datetime.now(),
                    enregistre_par=request.user,
                    membre=self.membre_model.objects.get(id=request.data.get("membre"))
                )
                logger.info(f"Transaction {transaction.id} created for vente {vente.id}: {montant} (article: {article.nom}, qty: {quantite})")
        except Exception as e:
            logger.error(f"Error creating transaction for vente {vente.id}: {str(e)}")

        return Response(
            standardized_response(data=serializer.data, message="Vente enregistrée"),
            status=status.HTTP_201_CREATED,
        )
