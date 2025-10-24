from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # Root langsung redirect ke /versus/
    path("", RedirectView.as_view(url="/versus/", permanent=False)),

    # Versus sebagai main page
    path("versus/", include(("versus.urls", "versus"), namespace="versus")),

    # (opsional) sisanya tetap
    path("promo/", include("promo.urls")),
    path("venue/", include("venue.urls")),
    path("authenticate/", include("authenticate.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

