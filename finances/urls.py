from django.urls import path
from .views import TransactionListView, TransactionDetailView, RapportFinancierView, MembreDonsView

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path("transactions/<int:pk>/", TransactionDetailView.as_view(), name="transaction-detail"),
    path("rapport/", RapportFinancierView.as_view(), name="rapport-financier"),
    path("membre/<int:pk>/dons/", MembreDonsView.as_view(), name="membre-dons"),
]
