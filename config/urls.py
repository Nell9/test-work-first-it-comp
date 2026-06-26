from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # REST API
    path("api/", include("cashflow.api_urls")),
    # Веб-страницы приложения
    path("", include("cashflow.urls")),
]
