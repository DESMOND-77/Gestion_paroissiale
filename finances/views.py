import logging
from django.db.models import Sum
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.base_view import BaseModelViewSet, BaseViewSet
from core.permissions import IsAdmin, IsTreasurerOrAbove
from core.response import standardized_response
from .models import Transaction
from .serializers import TransactionSerializer
from .services import FinanceService

logger = logging.getLogger(__name__)


class TransactionViewSet(BaseModelViewSet):
    queryset = Transaction.objects.select_related("membre", "enregistre_par").all()
    serializer_class = TransactionSerializer

    def get_permissions(self):
        if self.action == "destroy":
            return [IsAdmin()]
        return [IsTreasurerOrAbove()]

    def list(self, request, *args, **kwargs):
        logger.debug(f"Listing transactions for user {request.user}")
        qs = self.get_queryset()
        serializer = self.get_serializer(qs, many=True)
        logger.info(f"Retrieved {qs.count()} transactions")
        return Response(standardized_response(data=serializer.data))

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.debug(f"Retrieving transaction {instance.id} for user {request.user}")
        serializer = self.get_serializer(instance)
        return Response(standardized_response(data=serializer.data))

    def create(self, request, *args, **kwargs):
        logger.info(f"Creating transaction for user {request.user}: {request.data}")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        transaction = serializer.save(enregistre_par=request.user)
        logger.info(f"Transaction created successfully: {transaction.id} by user {request.user}")
        return Response(
            standardized_response(data=serializer.data, message="Transaction enregistrée"),
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        logger.warning(f"Deleting transaction {instance.id} by user {request.user}")
        instance.delete()
        logger.info(f"Transaction {instance.id} deleted successfully")
        return Response(standardized_response(message="Transaction supprimée"), status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], permission_classes=[IsTreasurerOrAbove])
    def rapport(self, request):
        date_debut = request.query_params.get("date_debut")
        date_fin = request.query_params.get("date_fin")
        logger.info(f"Generating financial report for user {request.user} (date_debut={date_debut}, date_fin={date_fin})")

        try:
            # Delegate to service layer for report calculation
            rapport = FinanceService.calculate_rapport(date_debut, date_fin)

            # Get transactions for detailed breakdown
            qs = self.get_queryset()
            if date_debut:
                qs = qs.filter(date__gte=date_debut)
            if date_fin:
                qs = qs.filter(date__lte=date_fin)

            data = {
                "periode": {"debut": date_debut, "fin": date_fin},
                "total_recettes": rapport["recettes"],
                "total_depenses": rapport["depenses"],
                "solde": rapport["solde"],
                "transactions": TransactionSerializer(qs, many=True).data,
            }
            return Response(standardized_response(data=data))
        except Exception as e:
            logger.error(f"Error generating rapport: {e}")
            return Response(
                standardized_response(success=False, error=str(e)),
                status=status.HTTP_400_BAD_REQUEST,
            )


class MembreDonsView(BaseViewSet):
    permission_classes = [IsTreasurerOrAbove]

    def retrieve(self, request, pk=None):
        from membres.models import Membre
        logger.debug(f"Retrieving donations for membre {pk} by user {request.user}")
        try:
            membre = Membre.objects.get(pk=pk)
            logger.debug(f"Found membre: {membre}")
        except Membre.DoesNotExist:
            logger.warning(f"Membre {pk} not found")
            return Response(
                standardized_response(success=False, error="Membre introuvable"),
                status=status.HTTP_404_NOT_FOUND,
            )
        dons = Transaction.objects.filter(membre=membre, categorie="don")
        serializer = TransactionSerializer(dons, many=True)
        total = dons.aggregate(total=Sum("montant"))["total"] or 0
        logger.info(f"Retrieved {dons.count()} donations for membre {pk}, total: {total}")
        return Response(standardized_response(data={"membre": str(membre), "total_dons": total, "dons": serializer.data}))
