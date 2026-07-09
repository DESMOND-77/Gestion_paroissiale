from django.contrib import admin
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.urls import path, include
from core.views import HealthCheckView
from accounts.verification.web_views import (
    EmailVerifyPageView,
    PasswordResetPageView,
)

from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
    openapi.Info(
        title="API GESTION PAROISSIALE",
        default_version="V1",
        description="API pour la gestion des paroisses",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # Le health check reste NON versionné : c'est un point de terminaison
    # d'infrastructure (référencé par le HEALTHCHECK du Dockerfile et Render).
    path("api/health/", HealthCheckView.as_view(), name="health-check"),

    # API versionnée sous /api/v1/. Toutes les routes métier passent par ce
    # préfixe. Pour introduire une v2, ajouter un bloc `api/v2/` en parallèle.
    path("api/v1/", include("accounts.urls")),
    path("api/v1/groupes/", include("groupes.urls")),
    path("api/v1/membres/", include("membres.urls")),
    path("api/v1/evenements/", include("evenements.urls")),
    path("api/v1/finances/", include("finances.urls")),
    path("api/v1/librairie/", include("librairie.urls")),
    path("docs/", schema_view.with_ui("swagger", cache_timeout=10), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=10), name="schema-redoc-ui"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
