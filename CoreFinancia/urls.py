print(">>> CARGANDO CoreFinancia/urls.py <<<")

from django.contrib import admin

from django.urls import path, include 
from appfinancia.views import login_view, logout_view # type: ignore
# para prueba de login \ logout 2025.10.28

from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static

from appfinancia.views import login_view, logout_view


urlpatterns = [
    path('admin/', admin.site.urls),

    # ...para login\logout 2025.10.28
    path('chaining/', include('smart_selects.urls')), 

    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path(
        'appfinancia/',
        include(('appfinancia.urls', 'appfinancia'), namespace='appfinancia')
    ),

    path('smart_selects/', include('smart_selects.urls')),
]


# ✅ SOLO PARA DESARROLLO
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

