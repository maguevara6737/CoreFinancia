#from django.shortcuts import render
#----------------------------------------------------


#--------------------------------------------------------------
# Create your views here.
# En views.py de tu app
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpRequest

def login_view(request: HttpRequest):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'home.html', {'usuario': request.user})


#2025/11/17 para ventana emergente a comentarios
# appfinancia/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import user_passes_test
from .models import Desembolsos, Comentarios_Prestamos, Comentarios

###@csrf_exempt <-- suspedido 2025-11-17
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET","POST"])
def add_comentario_prestamo(request, prestamo_id):
    try:
        desembolso = Desembolsos.objects.get(prestamo_id=prestamo_id)
        comentario_cat_id = request.POST.get('comentario_catalogo')

        if not comentario_cat_id:
            return JsonResponse({'error': 'Debe seleccionar un comentario del catálogo.'}, status=400)

        # Obtener comentario habilitado
        try:
            comentario_cat = Comentarios.objects.get(
                pk=comentario_cat_id,
                estado='HABILITADO'
            )
        except Comentarios.DoesNotExist:
            return JsonResponse({'error': 'Comentario no válido o no habilitado.'}, status=400)

        # Crear comentario
        comentario = Comentarios_Prestamos.objects.create(
            prestamo=desembolso,
            comentario_catalogo=comentario_cat,
            creado_por=request.user
            # ¡comentario="" por defecto (blank=True)!
        )

        return JsonResponse({
            'success': True,
            'comentario': {
                'id': comentario.numero_comentario,
                'catalogo': str(comentario_cat),
                'creado_por': str(comentario.creado_por),
                'fecha': comentario.fecha_comentario.strftime('%Y-%m-%d %H:%M')
            }
        })

    except Desembolsos.DoesNotExist:
        return JsonResponse({'error': 'Desembolso no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)