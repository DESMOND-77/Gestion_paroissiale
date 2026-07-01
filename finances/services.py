import logging
from decimal import Decimal
from django.db.models import Sum

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
    def calculate_rapport(date_debut=None, date_fin=None):
        """Calculate financial report; both dates are optional."""
        try:
            qs_recettes = Transaction.objects.filter(type="recette")
            qs_depenses = Transaction.objects.filter(type="depense")

            if date_debut:
                qs_recettes = qs_recettes.filter(date__gte=date_debut)
                qs_depenses = qs_depenses.filter(date__gte=date_debut)
            if date_fin:
                qs_recettes = qs_recettes.filter(date__lte=date_fin)
                qs_depenses = qs_depenses.filter(date__lte=date_fin)

            recettes = qs_recettes.aggregate(total=Sum("montant"))["total"] or Decimal("0.00")
            depenses = qs_depenses.aggregate(total=Sum("montant"))["total"] or Decimal("0.00")
            solde = recettes - depenses

            logger.info(f"Financial report: {date_debut} to {date_fin} — Solde: {solde} FCFA")
            return {
                "date_debut": date_debut,
                "date_fin": date_fin,
                "recettes": float(recettes),
                "depenses": float(depenses),
                "solde": float(solde),
            }
        except Exception as e:
            logger.error(f"Error calculating rapport: {e}")
            raise

    @staticmethod
    def get_transactions_by_category(date_debut=None, date_fin=None, categorie=None):
        """Get transaction totals grouped by category; all filters are optional."""
        queryset = Transaction.objects.all()
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
        if categorie:
            queryset = queryset.filter(categorie=categorie)
        return list(queryset.values("categorie").annotate(total=Sum("montant")))

    @staticmethod
    def get_donor_total(membre, date_debut=None, date_fin=None):
        """Get total donations from a member, optionally filtered by date range."""
        queryset = Transaction.objects.filter(type="recette", categorie="don", membre=membre)
        if date_debut:
            queryset = queryset.filter(date__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(date__lte=date_fin)
        result = queryset.aggregate(total=Sum("montant"))
        return result["total"] or Decimal("0.00")
