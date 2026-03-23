from usuarios.models import PerfilUsuario
from core.models import Polo

class PoloContextoMiddleware:
    """Define request.polo a partir do perfil do usuário logado."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                perfil = PerfilUsuario.objects.select_related('polo').get(user=request.user)
                if perfil.is_admin_global:
                    slug = request.session.get('polo_slug')
                    request.polo = Polo.objects.filter(slug=slug).first() if slug else None
                else:
                    request.polo = perfil.polo
            except PerfilUsuario.DoesNotExist:
                request.polo = None
        else:
            request.polo = None

        return self.get_response(request)

def is_global(user):
    return hasattr(user, 'perfilusuario') and user.perfilusuario.cargo == 'admin_global'
