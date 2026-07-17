from django.urls import path

from .views import GroupeDetailView, GroupeListView, GroupeMembresView

urlpatterns = [
    path("", GroupeListView.as_view(), name="groupe-list"),
    path("<uuid:pk>/", GroupeDetailView.as_view(), name="groupe-detail"),
    path("<uuid:pk>/membres/", GroupeMembresView.as_view(), name="groupe-membres"),
]
