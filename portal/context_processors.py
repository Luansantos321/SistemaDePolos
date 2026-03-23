def polo_usuario(request):
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfilusuario', None)
        if perfil and perfil.polo:
            return {'polo_usuario': perfil.polo}
    return {}