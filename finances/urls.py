from django.urls import path

from .views import (
    MembreDonsView,
    RapportFinancierView,
    TransactionDetailView,
    TransactionListView,
)

urlpatterns = [
    path("transactions/", TransactionListView.as_view(), name="transaction-list"),
    path(
        "transactions/<uuid:pk>/",
        TransactionDetailView.as_view(),
        name="transaction-detail",
    ),
    path("rapport/", RapportFinancierView.as_view(), name="rapport-financier"),
    path("membre/<uuid:pk>/dons/", MembreDonsView.as_view(), name="membre-dons"),
]
