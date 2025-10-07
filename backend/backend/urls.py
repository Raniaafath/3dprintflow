from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

def root(_request):
    return JsonResponse({
        "name": "3dprintflow-api",
        "status": "ok",
        "docs": "/admin/",
        "auth": "/api/auth/"
    })

urlpatterns = [
    path("", root, name="root"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", include("dj_rest_auth.registration.urls")),
    path("api/auth/legacy/", include("authapp.urls")),
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
