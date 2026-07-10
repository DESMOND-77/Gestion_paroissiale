from django.urls import path

from .views import MembreListView, MembreDetailView, MembreMeView, MembreSacrementsView

urlpatterns = [
    path("", MembreListView.as_view(), name="membre-list"),
    path("me/", MembreMeView.as_view(), name="membre-me"),
    path("<uuid:pk>/", MembreDetailView.as_view(), name="membre-detail"),
    path("<uuid:pk>/sacrements/", MembreSacrementsView.as_view(), name="membre-sacrements"),
]
