from django.urls import path
from .views import GroupeListView, GroupeDetailView, GroupeMembresView

urlpatterns = [
    path("", GroupeListView.as_view(), name="groupe-list"),
    path("<int:pk>/", GroupeDetailView.as_view(), name="groupe-detail"),
    path("<int:pk>/membres/", GroupeMembresView.as_view(), name="groupe-membres"),
]
