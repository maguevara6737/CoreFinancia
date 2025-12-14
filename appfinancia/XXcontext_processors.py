# appfinancia/context_processors.py

def admin_permissions(request):
    """
    Agrega permisos personalizados al contexto del admin.
    """
    if request.user.is_authenticated:
        puede_consultar_causacion = request.user.has_perm('appfinancia.puede_consultar_causacion')
    else:
        puede_consultar_causacion = False
    
    return {
        'puede_consultar_causacion': puede_consultar_causacion,
    }