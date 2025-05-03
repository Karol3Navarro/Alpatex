
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', include('index.urls')),
    path('autenticacion/', include('autenticacion.urls')),

    path('accounts/', include("django.contrib.auth.urls")), #Autentificacion
    path('', include('Dm.urls')),
    path('admin_dashboard/', include('admin_alpatex.urls')), 

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

