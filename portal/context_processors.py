def polo_usuario(request):
    if request.user.is_authenticated:
        perfil = getattr(request.user, 'perfilusuario', None)
        if perfil and perfil.polo:
            return {'polo_usuario': perfil.polo}
    return {}

from core.models import Polo
from escolas.models import Turma
import datetime

def turmas_menu(request):
    polo_id = request.session.get("polo_id")

    turmas = Turma.objects.none()
    polo = None

    if polo_id:
        polo = Polo.objects.filter(id=polo_id).first()
        turmas = Turma.objects.filter(
            polo_id=polo_id,
            ano_letivo=datetime.date.today().year
        )

    return {
        "turmas_menu": turmas,
        "polo": polo
    }