import logging

from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response

from core.base_view import BaseAPIView
from core.permissions import IsAdmin, IsTreasurerOrAbove
from core.response import standardized_response
from .models import Transaction
from .serializers import TransactionSerializer
from .services import FinanceService

logger = logging.getLogger(__name__)


class TransactionListView(BaseAPIView):
    """
    GET  /api/finances/transactions/    — liste
    POST /api/finances/transactions/    — création
    """

    permission_classes = [IsTreasurerOrAbove]

    def get(self, request):
        logger.debug(f"Listing transactions for user {request.user}")
        qs = Transaction.objects.select_related("membre", "enregistre_par").all()
        logger.info(f"Retrieved {qs.count()} transactions")
        return Response(standardized_response(data=TransactionSerializer(qs, many=True).data))

    def post(self, request):
        logger.info(f"Creating transaction for user {request.user}: {request.data}")
        serializer = TransactionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        transaction = FinanceService.create_transaction(
            type_transaction=validated["type"],
            montant=validated["montant"],
            date=validated["date"],
            **{k: v for k, v in validated.items() if k not in ("type", "montant", "date")},
            enregistre_par=request.user,
        )
        logger.info(f"Transaction created successfully: {transaction.id} by user {request.user}")
        return Response(
            standardized_response(data=TransactionSerializer(transaction).data, message="Transaction enregistrée"),
            status=status.HTTP_201_CREATED,
        )


class TransactionDetailView(BaseAPIView):
    """
    GET    /api/finances/transactions/<pk>/     — détail
    DELETE /api/finances/transactions/<pk>/     — suppression (admin)
    """

    permission_classes = [IsTreasurerOrAbove]

    def _get_transaction(self, pk):
        return get_object_or_404(Transaction.objects.select_related("membre", "enregistre_par"), pk=pk)

    def get(self, request, pk):
        transaction = self._get_transaction(pk)
        logger.debug(f"Retrieving transaction {pk} for user {request.user}")
        return Response(standardized_response(data=TransactionSerializer(transaction).data))

    def delete(self, request, pk):
        self.check_extra_permission(request, IsAdmin())
        transaction = self._get_transaction(pk)
        logger.warning(f"Deleting transaction {pk} by user {request.user}")
        transaction.delete()
        logger.info(f"Transaction {pk} deleted successfully")
        return Response(standardized_response(message="Transaction supprimée"), status=status.HTTP_204_NO_CONTENT)


class RapportFinancierView(BaseAPIView):
    """
    GET /api/finances/rapport/
        Paramètres optionnels: ?date_debut=&date_fin=&categorie=
        Retourne les totaux + ventilation par catégorie + liste des transactions.
    """

    permission_classes = [IsTreasurerOrAbove]

    def get(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        categorie = request.query_params.get("categorie")
        logger.info(f"Generating financial report for user {request.user} ({date_debut} → {date_fin})")

        try:
            rapport = FinanceService.calculate_rapport(date_debut, date_fin)
            par_categorie = FinanceService.get_transactions_by_category(date_debut, date_fin, categorie)

            qs = Transaction.objects.select_related("membre", "enregistre_par").all()
            if date_debut:
                qs = qs.filter(date__gte=date_debut)
            if date_fin:
                qs = qs.filter(date__lte=date_fin)
            if categorie:
                qs = qs.filter(categorie=categorie)

            data = {
                "periode": {"debut": date_debut, "fin": date_fin},
                "total_recettes": rapport["recettes"],
                "total_depenses": rapport["depenses"],
                "solde": rapport["solde"],
                "par_categorie": par_categorie,
                "transactions": TransactionSerializer(qs, many=True).data,
            }
            return Response(standardized_response(data=data))
        except Exception as e:
            logger.error(f"Error generating rapport: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )


class MembreDonsView(BaseAPIView):
    """
    GET /api/finances/membre/<pk>/dons/
        Paramètres optionnels: ?date_debut=&date_fin=
        Retourne les dons d'un membre avec le total calculé via le service.
    """

    permission_classes = [IsTreasurerOrAbove]

    def get(self, request, pk):
        from membres.models import Membre
        logger.debug(f"Retrieving donations for membre {pk} by user {request.user}")

        try:
            membre = Membre.objects.get(pk=pk)
        except Membre.DoesNotExist:
            logger.warning(f"Membre {pk} not found")
            return Response(
                standardized_response(success=False, error="Membre introuvable"),
                status=status.HTTP_404_NOT_FOUND,
            )

        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")

        total = FinanceService.get_donor_total(membre, date_debut=date_debut, date_fin=date_fin)

        dons_qs = Transaction.objects.filter(membre=membre, categorie="don")
        if date_debut:
            dons_qs = dons_qs.filter(date__gte=date_debut)
        if date_fin:
            dons_qs = dons_qs.filter(date__lte=date_fin)

        logger.info(f"Retrieved {dons_qs.count()} donations for membre {pk}, total: {total}")
        return Response(
            standardized_response(data={
                "membre": str(membre),
                "total_dons": float(total),
                "periode": {"debut": date_debut, "fin": date_fin},
                "dons": TransactionSerializer(dons_qs, many=True).data,
            })
        )
