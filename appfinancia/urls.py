from django.urls import path
from . import views
 

app_name = "appfinancia" #añadido 2025/12/10 para fragmentación de pagos

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    #comentarios prestamos 225/11/17
    #no incluir rutas que incluyan /appfinancia/  ni rutas generales del proyecto. Solo especificas de prestamamos, plan pagos,etc
    #path('admin/consulta-causacion/', consulta_causacion_view, name='consulta_causacion'),
    path('admin/desembolso/<int:prestamo_id>/add-comentario/', views.add_comentario_prestamo, name='add_comentario_prestamo'),
    path('plan-pagos/<int:prestamo_id>/', views.plan_de_pagos_view, name='plan_pagos'),
    path('admin/exportar-historia/<int:prestamo_id>/', views.exportar_historia_xlsx, name='exportar_historia_xlsx'),                      
    path('estado_cuenta/<int:prestamo_id>/', views.estado_cuenta_view, name='estado_cuenta'),
    path('estado_cuenta/<int:prestamo_id>/excel/', views.estado_cuenta_view, name='estado_cuenta_excel'),
    path("fragmentacion/fragmentar/<int:pago_id>/", views.fragmentar_pago, name="fragmentar_pago"),
    path("regularizar-pago/<int:pago_id>/",views.regularizar_pago_view, name="regularizar_pago", ),
]

