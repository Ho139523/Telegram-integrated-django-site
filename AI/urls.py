from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('heartpred.urls')),
    path('api/', include('myapi.urls')),
    path('', include('cv.urls')),
    path('accounts/', include('accounts.urls')),
    path('socials/', include('social_django.urls', namespace='social'))
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)