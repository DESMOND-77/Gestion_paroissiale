import logging
from datetime import datetime
from decimal import Decimal
from django.db.models import Sum, Q

from .models import Transaction

logger = logging.getLogger(__name__)


class FinanceService:
    """Service layer for finance business logic"""

    @staticmethod
    def create_transaction(type_transaction, montant, date, **kwargs):
        """Create a new transaction with validation"""
        try:
            transaction = Transaction.objects.create(
                type=type_transaction,
                montant=montant,
                date=date,
                **kwargs
            )
            logger.info(f"Transaction created: {transaction.id} ({type_transaction}) {montant} FCFA")
            return transaction
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            raise

    @staticmethod
    def calculate_rapport(date_debut, date_fin):
        """Calculate financial report between two dates"""
        try:
            recettes_data = Transaction.objects.filter(
                type="recette",
                date__range=[date_debut, date_fin]
            ).aggregate(total=Sum("montant"))

            depenses_data = Transaction.objects.filter(
                type="depense",
                date__range=[date_debut, date_fin]
            ).aggregate(total=Sum("montant"))

            recettes = recettes_data["total"] or Decimal("0.00")
            depenses = depenses_data["total"] or Decimal("0.00")
            solde = recettes - depenses

            rapport = {
                "date_debut": date_debut,
                "date_fin": date_fin,
                "recettes": float(recettes),
                "depenses": float(depenses),
                "solde": float(solde),
            }

            logger.info(f"Financial report: {date_debut} to {date_fin} - Solde: {solde} FCFA")
            return rapport
        except Exception as e:
            logger.error(f"Error calculating rapport: {e}")
            raise

    @staticmethod
    def get_transactions_by_category(date_debut, date_fin, categorie=None):
        """Get transactions grouped by category"""
        queryset = Transaction.objects.filter(date__range=[date_debut, date_fin])

        if categorie:
            queryset = queryset.filter(categorie=categorie)

        return queryset.values("categorie").annotate(total=Sum("montant"))

    @staticmethod
    def get_donor_total(membre, date_debut=None, date_fin=None):
        """Get total donations from a member"""
        queryset = Transaction.objects.filter(
            type="recette",
            categorie="don",
            membre=membre
        )

        if date_debut and date_fin:
            queryset = queryset.filter(date__range=[date_debut, date_fin])

        result = queryset.aggregate(total=Sum("montant"))
        return result["total"] or Decimal("0.00")
