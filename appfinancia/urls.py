from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
    #comentarios prestamos 225/11/17
    path('admin/desembolso/<int:prestamo_id>/add-comentario/', views.add_comentario_prestamo, name='add_comentario_prestamo'),

]
