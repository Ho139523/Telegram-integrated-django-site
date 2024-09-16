from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from utils.funcs.django_social_redirect import custom_complete

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('heartpred.urls')),
    path('api/', include('myapi.urls')),
    path('', include('cv.urls')),
    path('accounts/', include('accounts.urls')),
    path('socials/', include('social_django.urls', namespace='social')),
    path('socials/complete/google-oauth2/', custom_complete, name="custom_complete"),
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)