from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from store.views import custom_404_view

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('store.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom 404 page. Django only renders this automatically when DEBUG=False —
# while developing (DEBUG=True) Django shows its own technical error page for
# real missing URLs instead, so visit /preview-404/ below to see this design.
handler404 = custom_404_view

if settings.DEBUG:
    urlpatterns += [
        # TEMPORARY: lets you preview the custom 404 design while DEBUG=True.
        # Safe to delete once DEBUG=False in production, since handler404
        # above takes over automatically at that point.
        path('preview-404/', custom_404_view, name='preview_404'),
    ]