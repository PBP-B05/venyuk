from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("versus/", include(("versus.urls", "versus"), namespace="versus")),
    # routes app lain…
    path("promo/", include("promo.urls")),
    path("", include("venue.urls")),
    path("authenticate/", include("authenticate.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


