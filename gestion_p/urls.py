from django.contrib import admin
from django.urls import path
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.urls import path, include

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
    path("api/", include("accounts.urls")),
    path("api/groupes/", include("groupes.urls")),
    path("api/membres/", include("membres.urls")),
    path("api/evenements/", include("evenements.urls")),
    path("api/finances/", include("finances.urls")),
    path("api/librairie/", include("librairie.urls")),
    path("docs/", schema_view.with_ui("swagger", cache_timeout=10), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=10), name="schema-redoc-ui"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
