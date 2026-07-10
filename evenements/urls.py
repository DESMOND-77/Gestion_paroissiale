from django.urls import path

from .views import (
    EvenementListView,
    EvenementDetailView,
    EvenementInscrireView,
    EvenementParticipantsView,
)

urlpatterns = [
    path("", EvenementListView.as_view(), name="evenement-list"),
    path("<uuid:pk>/", EvenementDetailView.as_view(), name="evenement-detail"),
    path(
        "<uuid:pk>/inscrire/", EvenementInscrireView.as_view(), name="evenement-inscrire"
    ),
    path(
        "<uuid:pk>/participants/",
        EvenementParticipantsView.as_view(),
        name="evenement-participants",
    ),
]
