from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("charts/", include("charts.urls")),
    path("clients/", include("clients.urls")),
    path("reports/", include("reports.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.SERVE_MEDIA_FILES:
    urlpatterns += [
        path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
    ]
