from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from core import views

admin.site.site_header = "Projeto Salvação"
admin.site.site_title = "Projeto Salvação"
admin.site.index_title = "Painel do professor"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("quero-treinar/", views.interesse, name="interesse"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
