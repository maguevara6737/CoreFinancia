from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    #comentarios prestamos 225/11/17
    #no incluir rutas que incluyan /appfinancia/  ni rutas generales del proyecto. Solo especificas de prestamamos, plan pagos,etc
    path('admin/desembolso/<int:prestamo_id>/add-comentario/', views.add_comentario_prestamo, name='add_comentario_prestamo'),
    path('admin/plan-pagos/<int:prestamo_id>/', views.plan_de_pagos_view, name='plan_pagos'),
    path('admin/exportar-historia/<int:prestamo_id>/', views.exportar_historia_prestamo_xlsx, name='exportar_historia_xlsx'),
]
