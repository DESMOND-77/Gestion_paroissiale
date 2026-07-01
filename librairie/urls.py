from django.urls import path
from .views import ArticleListView, ArticleDetailView, ArticleAlertesView, VenteListView, VenteRapportView

urlpatterns = [
    path("articles/", ArticleListView.as_view(), name="article-list"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="article-detail"),
    path("alertes/", ArticleAlertesView.as_view(), name="alertes-stock"),
    path("ventes/", VenteListView.as_view(), name="vente-list"),
    path("ventes/rapport/", VenteRapportView.as_view(), name="vente-rapport"),
]
