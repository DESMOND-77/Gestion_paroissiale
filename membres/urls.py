from django.urls import path
from .views import MembreListView, MembreDetailView, MembreSacrementsView

urlpatterns = [
    path("", MembreListView.as_view(), name="membre-list"),
    path("<int:pk>/", MembreDetailView.as_view(), name="membre-detail"),
    path("<int:pk>/sacrements/", MembreSacrementsView.as_view(), name="membre-sacrements"),
]
