from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from usuarios.models import PerfilUsuario

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            try:
                perfil = user.perfilusuario
            except PerfilUsuario.DoesNotExist:
                messages.error(request, "Usuário sem perfil associado. Contate o administrador.")
                logout(request)
                return redirect('usuarios:login')

            # 🔹 Salva o polo do usuário na sessão
            if perfil.polo:
                request.session['polo_id'] = perfil.polo.id

            # 🔹 Redireciona conforme o cargo
            if perfil.cargo == 'admin_global':
                return redirect('portal:home')  # painel global

            elif perfil.cargo in ['diretoria', 'coordenador', 'secretaria', 'professor']:
                return redirect('portal:home_polo')  # painel do polo

            elif perfil.cargo == 'aluno':
                return redirect('portal:home_aluno')  # painel do aluno (ajuste o nome da rota se diferente)

            else:
                messages.error(request, f"Cargo '{perfil.cargo}' desconhecido.")
                logout(request)
                return redirect('usuarios:login')

        else:
            messages.error(request, "Usuário ou senha incorretos.")

    return render(request, "login.html")

def logout_view(request):
    logout(request)
    return redirect('usuarios:login')

