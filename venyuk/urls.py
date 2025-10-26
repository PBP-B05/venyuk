from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('promo/', include('promo.urls')),
    path('', include('venue.urls')),
    path('authenticate/', include('authenticate.urls')),
    path('match_up/', include('match_up.urls')),
    path('ven_shop/', include('ven_shop.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
