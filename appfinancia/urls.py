from django.urls import path
from . import views

app_name = "appfinancia" #añadido 2025/12/10 para fragmentación de pagos

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    #comentarios prestamos 225/11/17
    path('admin/desembolso/<int:prestamo_id>/add-comentario/', views.add_comentario_prestamo, name='add_comentario_prestamo'),
    #Fragmentación de pagos
    path("fragmentacion/fragmentar/<int:pago_id>/", views.fragmentar_pago, name="fragmentar_pago"),
     path("regularizar-pago/<int:pago_id>/",views.regularizar_pago_view, name="regularizar_pago", ),
]
