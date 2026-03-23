from django.shortcuts import render, redirect, get_object_or_404
from core.models import Polo
from django.contrib.auth.decorators import login_required
from usuarios.models import PerfilUsuario
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import get_user_model

def is_admin_global(user):
    try:
        return user.perfilusuario.cargo == 'admin_global'
    except PerfilUsuario.DoesNotExist:
        return False

def painel_view(request):
    polo = getattr(request, 'polo', None)
    return render(request, 'portal/painel.html', {'polo': polo})

def trocar_polo_view(request):
    if request.method == 'POST' and request.user.perfilusuario.is_admin_global:
        request.session['polo_slug'] = request.POST.get('polo_slug')
    return redirect('portal:painel')

@login_required
def dashboard(request):
    perfil = PerfilUsuario.objects.get(user=request.user)

    if perfil.cargo == 'admin_global':
        return redirect('portal:home')  # painel global

    elif perfil.cargo in ['diretoria', 'coordenador', 'secretaria', 'professor']:
        return redirect('portal:home_polo')  # painel do polo

    elif perfil.cargo == 'aluno':
        return redirect('portal:home_aluno')  # painel do aluno

    else:
        messages.error(request, "Cargo do usuário desconhecido.")
        return redirect('usuarios:login')

@login_required
def home(request):
    polos = Polo.objects.all()
    return render(request, 'portal/home.html', {'polos': polos, 'polo': None})
@login_required
def Criar_polo(request):
    perfil = PerfilUsuario.objects.get(user=request.user)
    if not perfil.is_admin_global:
        return redirect('home')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        endereco = request.POST.get('endereco')
        telefone = request.POST.get('telefone')
        logo = request.FILES.get('logo')

        Polo.objects.create(
            nome=nome,
            endereco=endereco,
            telefone=telefone,
            
            logo=logo
        )
        return redirect('portal:home')

    return render(request, 'portal/criar_polo.html', {'polo': None})

@login_required
def Editar_polo(request, polo_id):
    perfil = PerfilUsuario.objects.get(user=request.user)
    # Verifica se o usuário logado é global
    try:
        perfil = request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Você não possui perfil associado.")
        return redirect('home')

    # Verifica se o usuário é admin_global
    if perfil.cargo != 'admin_global':
        messages.error(request, "Você não tem permissão para criar usuários.")
        return redirect('home')

    polo = get_object_or_404(Polo, id=polo_id)

    if request.method == 'POST':
        polo.nome = request.POST.get('nome')
        polo.endereco = request.POST.get('endereco')
        polo.telefone = request.POST.get('telefone')
        polo.cor_principal = request.POST.get('cor_principal')
        polo.cor_secundaria = request.POST.get('cor_secundaria')
        logo = request.FILES.get('logo')
        if logo:
            polo.logo = logo
        polo.save()
        return redirect('portal:home')

    return render(request, 'portal/criar_polo.html', {'polo': polo})

@login_required
def home_polo(request, polo_id=None):
    perfil = request.user.perfilusuario

    if perfil.is_admin_global:
        if polo_id:
            request.session['polo_id'] = polo_id
        polo_id = request.session.get('polo_id')
        if not polo_id:
            messages.error(request, "Selecione um polo para acessar.")
            return redirect('portal:home')
        polo = get_object_or_404(Polo, id=polo_id)
    else:
        polo = perfil.polo

    turmas = polo.turmas.all()
    professores = polo.professores.all()
    alunos = polo.alunos.all()

    return render(request, 'portal/home_polo.html', {
        'polo': polo,
        'turmas': turmas,
        'professores': professores,
        'alunos': alunos
    })

@login_required
def acessar_polo(request, polo_id):
    perfil = PerfilUsuario.objects.get(user=request.user)

    if not perfil.is_admin_global:
        return redirect('portal:home_polo')

    polo = get_object_or_404(Polo, id=polo_id)

    # Salva o polo selecionado na sessão
    request.session['polo_id'] = polo.id

    # Redireciona para a home do polo
    return redirect('portal:home_polo')

User = get_user_model()

@login_required
def criar_usuario_global(request):
    try:
        perfil = request.user.perfilusuario
    except PerfilUsuario.DoesNotExist:
        messages.error(request, "Você não possui perfil associado.")
        return redirect('portal:home')

    if perfil.cargo != 'admin_global':
        messages.error(request, "Você não tem permissão para criar usuários.")
        return redirect('portal:home')

    polos = Polo.objects.all()
    usuarios = User.objects.all().order_by('username')  # LISTA PARA A TABELA

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        cargo = request.POST.get('cargo')
        polo_id = request.POST.get('polo')

        if not username or not senha or not cargo:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return redirect('portal:criar_usuario')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Esse nome de usuário já existe.")
            return redirect('portal:criar_usuario')

        # Define tipo e polo
        if cargo == 'admin_global':
            tipo_usuario = 'global'
            polo = None
        else:
            tipo_usuario = 'polo'
            polo = get_object_or_404(Polo, id=polo_id)

        # Cria usuário
        user = User.objects.create_user(
            username=username,
            email=email,
            password=senha,
            tipo=tipo_usuario,
            polo=polo
        )

        PerfilUsuario.objects.create(
            user=user,
            cargo=cargo,
            polo=polo
        )

        messages.success(request, f"Usuário '{username}' criado com sucesso!")
        return redirect('portal:criar_usuario')

    return render(request, 'portal/criar_usuario.html', {
        'polos': polos,
        'usuarios': usuarios
    })


@login_required
def editar_usuario(request, user_id):
    if not is_admin_global(request.user):
        messages.error(request, "Você não tem permissão para isso.")
        return redirect('portal:home')

    user = get_object_or_404(User, id=user_id)
    perfil = user.perfilusuario
    polos = Polo.objects.all()

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        cargo = request.POST.get("cargo")
        polo_id = request.POST.get("polo")

        # Validações
        if username != user.username and User.objects.filter(username=username).exists():
            messages.error(request, "Esse nome de usuário já está em uso.")
            return redirect(request.path)

        user.username = username
        user.email = email
        user.save()

        perfil.cargo = cargo
        perfil.polo = Polo.objects.get(id=polo_id) if polo_id and cargo != 'admin_global' else None
        perfil.save()

        messages.success(request, "Usuário atualizado com sucesso!")
        return redirect('portal:criar_usuario')

    return render(request, 'portal/editar_usuario.html', {
        'alvo': user,
        'perfil': perfil,
        'polos': polos
    })

@login_required
def excluir_usuario(request, user_id):
    if not is_admin_global(request.user):
        messages.error(request, "Apenas administradores globais podem excluir usuários.")
        return redirect('portal:home')

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()
        messages.success(request, "Usuário excluído com sucesso!")
        return redirect('portal:criar_usuario')

    # Nunca retorna GET → evita erro
    messages.error(request, "Requisição inválida.")
    return redirect('portal:criar_usuario')



@login_required
def remover_acesso(request, user_id):
    if not is_admin_global(request.user):
        messages.error(request, "Apenas administradores globais podem remover acessos.")
        return redirect('portal:home')

    user = get_object_or_404(User, id=user_id)

    # desativa o acesso
    user.is_active = False
    user.save()

    messages.success(request, f"Acesso de '{user.username}' foi removido.")
    return redirect('portal:criar_usuario')

@login_required
def reativar_acesso(request, user_id):
    if not is_admin_global(request.user):
        messages.error(request, "Apenas administradores globais podem reativar acessos.")
        return redirect('portal:home')

    user = get_object_or_404(User, id=user_id)

    # Reativa o acesso
    user.is_active = True
    user.save()

    messages.success(request, f"O acesso do usuário '{user.username}' foi reativado com sucesso!")
    return redirect('portal:criar_usuario')
