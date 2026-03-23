from django.views.generic import ListView, CreateView
from .models import Aluno
from core.mixins import RestritoAoPoloMixin
from django.db.models.functions import Lower
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Turma, Professor, Aluno, Disciplina, TurmaProfessorDisciplina, DiaLetivo, Nota, Aula, Frequencia, HistoricoTurmaAluno, GradeHoraria
from usuarios.models import PerfilUsuario, Polo
from django.utils.dateparse import parse_date
from django.contrib.auth import get_user_model
from django.http import HttpResponse
import datetime
from datetime import date, timedelta, time
from core.middleware import is_global
from babel.dates import format_date, get_month_names
import calendar
from django.utils import timezone
from calendar import monthrange
from decimal import Decimal
from collections import defaultdict
from django.db.models import Q, CharField, Count , Avg , DecimalField
from django.core.exceptions import ValidationError
from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO
from django.db.models import Sum, Count, Q
from django.views import View
from django.db.models.functions import Cast
from django.utils.decorators import method_decorator
from django.urls import reverse
User = get_user_model()


def is_global(user):
    try:
        return user.perfilusuario.cargo == 'admin_global'
    except:
        return False


@login_required
def listar_turmas(request, polo_id=None):
    ano_atual = datetime.datetime.now().year
    ano_letivo = request.GET.get('ano_letivo', ano_atual)
    perfil = request.user.perfilusuario

    if perfil.is_admin_global:
        polo_id = request.session.get('polo_id')
        if not polo_id:
            messages.error(request, "Nenhum polo selecionado.")
            return redirect('portal:home')

    polo = get_object_or_404(Polo, id=polo_id)

    turmas = Turma.objects.select_related('polo').filter(polo=polo, ano_letivo=ano_letivo)

   
    if ano_letivo:  
        turmas = turmas.filter(ano_letivo=ano_letivo)

    return render(request, 'portal/listar_turmas.html', {
        'turmas': turmas,
        'polo': polo,
        'ano_letivo': ano_letivo,
    })


@login_required
def criar_turma(request):
    polo = request.user.perfilusuario.polo
    
    perfil = request.user.perfilusuario

    if perfil.cargo not in ['diretoria', 'secretaria', 'admin_global']:
        messages.error(request, "Você não tem permissão para criar turmas.")
        return redirect('escolas:listar_turmas', polo_id=perfil.polo.id)

    polos = Polo.objects.all() if perfil.is_admin_global else None

    if request.method == "POST":
        nome = request.POST.get("nome")
        turno = request.POST.get("turno")
        ano = request.POST.get("ano")
        ano_letivo = request.POST.get("ano_letivo")
        polo_id = request.POST.get("polo")

        if not nome or not turno or not ano:
            messages.error(request, "Preencha todos os campos obrigatórios.")
        else:
            polo = (
                get_object_or_404(Polo, id=polo_id)
                if perfil.is_admin_global
                else perfil.polo
            )

            # Evita IntegrityError
            turma, criada = Turma.objects.get_or_create(
                nome=nome,
                ano=ano,
                ano_letivo=ano_letivo,
                polo=polo,
                defaults={'turno': turno}
            )

            if criada:
                
                return redirect('escolas:listar_turmas', polo_id=polo.id)
            else:
                messages.warning(request, "A turma já existe. Não foi possivel criar.")
                # NÃO redireciona, continua na página de cadastro

    return render(request, 'portal/criar_turmas.html', {'polo': polo, 'polos':polos})

@login_required
def excluir_turma(request, turma_id):
    turma = get_object_or_404(Turma, id=turma_id)
    perfil = request.user.perfilusuario

    # Verifica permissão
    if perfil.cargo not in ['diretoria', 'secretaria', 'admin_global']:
        messages.error(request, "Você não tem permissão para excluir turmas.")
        # Aqui também precisa do polo_id
        return redirect('escolas:listar_turmas', polo_id=turma.polo.id)

    polo_id = turma.polo.id
    turma.delete()
    messages.success(request, "Turma excluída com sucesso!")
    return redirect('escolas:listar_turmas', polo_id=polo_id)

# ========== PROFESSORES ==========
@login_required
def listar_professores(request):
    perfil = request.user.perfilusuario

    # Verifica qual polo está sendo visualizado
    polo_id = request.session.get('polo_id')

    # Caso o usuário seja admin global e tenha um polo selecionado
    if perfil.is_admin_global and polo_id:
        professores = Professor.objects.filter(polo_id=polo_id)
    else:
        # Para usuários normais, mostra apenas o polo do próprio perfil
        professores = Professor.objects.filter(polo=perfil.polo)
    polo = get_object_or_404(Polo, id=polo_id)
    context = {
        'professores': professores,
        'polo':polo
    }
    return render(request, 'portal/listar_professores.html', context)

@login_required
def criar_professor(request):
    polo = request.user.perfilusuario.polo
    perfil = request.user.perfilusuario

    # Somente diretoria, secretaria ou admin_global podem cadastrar professores
    if perfil.cargo not in ['diretoria', 'secretaria', 'admin_global']:
        messages.error(request, "Você não tem permissão para cadastrar professores.")
        return redirect('escolas:listar_professores')

    # Polos disponíveis para escolha (apenas se for admin_global)
    polos = Polo.objects.all() if perfil.is_admin_global else None

    if request.method == "POST":
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        cpf = request.POST.get("cpf")
        rg = request.POST.get("rg")
        orgao_emissor = request.POST.get("orgao_emissor")
        uf_rg = request.POST.get("uf_rg")
        data_emissao_rg = parse_date(request.POST.get("data_emissao_rg"))
        data_nascimento = parse_date(request.POST.get("data_nascimento"))
        formacao_academica = request.POST.get("formacao_academica")
        nivel_superior = bool(request.POST.get("nivel_superior"))
        pos_graduacao = request.POST.get("pos_graduacao")
        curso_formacao = request.POST.get("curso_formacao")
        instituicao_formacao = request.POST.get("instituicao_formacao")

        criar_usuario = bool(request.POST.get("criar_usuario"))
        senha = request.POST.get("senha")

        # Campos obrigatórios
        if not nome or not cpf:
            messages.error(request, "Preencha os campos obrigatórios: nome e CPF.")
            return redirect('escolas:criar_professor')

        # Define o polo
        if perfil.is_admin_global:
            polo_id = request.POST.get("polo")
            if not polo_id:
                messages.error(request, "Selecione um polo.")
                return redirect('escolas:criar_professor')
            polo = get_object_or_404(Polo, id=polo_id)
        else:
            polo = perfil.polo

        # Criação do Professor
        professor = Professor(
            polo=polo,
            nome=nome,
            email=email,
            cpf=cpf,
            rg=rg,
            orgao_emissor=orgao_emissor,
            uf_rg=uf_rg,
            data_emissao_rg=data_emissao_rg,
            data_nascimento=data_nascimento,
            formacao_academica=formacao_academica,
            nivel_superior=nivel_superior,
            pos_graduacao=pos_graduacao,
            curso_formacao=curso_formacao,
            instituicao_formacao=instituicao_formacao,
        )

        # Cria conta de usuário para o professor, se solicitado
        if criar_usuario:
            if not email or not senha:
                messages.error(request, "Informe e-mail e senha para criar a conta do professor.")
                return redirect('escolas:criar_professor')

            # Cria o usuário Django
            user = User.objects.create_user(
                username=email,
                email=email,
                password=senha,
                first_name=nome
            )

            # Cria o perfil vinculado ao usuário e ao polo
            perfil_user = PerfilUsuario.objects.create(
                user=user,
                cargo='professor',
                polo=polo
            )

            # Vincula o perfil ao professor
            professor.user = perfil_user

        professor.save()
        messages.success(request, "Professor cadastrado com sucesso!")
        return redirect('escolas:listar_professores')

    context = {
        'polo': polo,
        'polos':polos,
    }
    return render(request, 'portal/criar_professores.html', context)

@login_required
def excluir_professor(request, professor_id):
   
    perfil = request.user.perfilusuario
    professor = get_object_or_404(Professor, id=professor_id)

    if not perfil.is_admin_global and professor.polo != perfil.polo:
        messages.error(request, "Você não pode excluir professores de outro polo.")
        return redirect('escola:listar_professores')

    professor.delete()
    messages.success(request, "Professor excluído com sucesso!")
    return redirect('escola:listar_professores')

# ========== ALUNOS ==========
@login_required
def listar_alunos(request):
    perfil = request.user.perfilusuario

    # Verifica qual polo está sendo visualizado
    polo_id = request.session.get('polo_id')

    # Caso o usuário seja admin global e tenha um polo selecionado
    if perfil.is_admin_global and polo_id:
        alunos = Aluno.objects.filter(polo_id=polo_id)
    else:
        # Para usuários normais, mostra apenas o polo do próprio perfil
        alunos = Aluno.objects.filter(polo=perfil.polo)
    polo = get_object_or_404(Polo, id=polo_id)
    context = {
        'alunos':alunos,
        'polo':polo,
    }
    return render(request, 'portal/listar_alunos.html', context)

@login_required
def criar_aluno(request):
    perfil = request.user.perfilusuario
    polo = perfil.polo

    #  Verifica permissão
    if perfil.cargo not in ['diretoria', 'secretaria', 'admin_global']:
        messages.error(request, "Você não tem permissão para criar alunos.")
        return redirect('escolas:listar_alunos')

    #  Filtra turmas conforme o polo
    if hasattr(perfil, 'is_admin_global') and perfil.is_admin_global:
        turmas = Turma.objects.all()
    else:
        turmas = Turma.objects.filter(polo=polo)

    if request.method == "POST":
        nome = request.POST.get("nome")
        matricula = request.POST.get("matricula")
        turma_id = request.POST.get("turma")

        if not nome or not matricula or not turma_id:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return redirect('escolas:criar_aluno')

        turma = get_object_or_404(Turma, id=turma_id)

        #  Impede que um usuário de outro polo cadastre aluno em turma diferente
        if not getattr(perfil, 'is_admin_global', False) and turma.polo != polo:
            messages.error(request, "A turma selecionada não pertence ao seu polo.")
            return redirect('escolas:criar_aluno')

        def safe_parse_date(value):
            """Evita erro se a data for None ou inválida"""
            if not value:
                return None
            try:
                return parse_date(value)
            except Exception:
                return None

        #  Criação segura do aluno
        aluno = Aluno(
            polo=polo if not getattr(perfil, 'is_admin_global', False) else turma.polo,
            turma=turma,
            nome=nome,
            matricula=matricula,

            # DADOS PESSOAIS
            data_nascimento=safe_parse_date(request.POST.get('data_nascimento')),
            cor_raca=request.POST.get('cor_raca'),
            sexo=request.POST.get('sexo'),
            nacionalidade=request.POST.get('nacionalidade'),
            estado_nascimento=request.POST.get('estado_nascimento'),
            municipio_nascimento=request.POST.get('municipio_nascimento'),

            # SAÚDE
            tipo_deficiencia=request.POST.get('tipo_deficiencia'),
            alergia_alimentar=bool(request.POST.get('alergia_alimentar')),
            descricao_alergia=request.POST.get('descricao_alergia'),

            # DOCUMENTOS
            rg=request.POST.get('rg'),
            complemento_rg=request.POST.get('complemento_rg'),
            orgao_emissor=request.POST.get('orgao_emissor'),
            uf_rg=request.POST.get('uf_rg'),
            data_expedicao_rg=safe_parse_date(request.POST.get('data_expedicao_rg')),
            cpf=request.POST.get('cpf'),
            nis=request.POST.get('nis'),
            cartao_sus=request.POST.get('cartao_sus'),
            bolsa_familia=bool(request.POST.get('bolsa_familia')),
            origem_quilombola=bool(request.POST.get('origem_quilombola')),

            # CERTIDÃO
            tipo_certidao=request.POST.get('tipo_certidao'),
            numero_termo=request.POST.get('numero_termo'),
            numero_livro=request.POST.get('numero_livro'),
            numero_folha=request.POST.get('numero_folha'),
            uf_certidao=request.POST.get('uf_certidao'),
            data_emissao_certidao=safe_parse_date(request.POST.get('data_emissao_certidao')),
            municipio_cartorio=request.POST.get('municipio_cartorio'),
            nome_cartorio=request.POST.get('nome_cartorio'),
            numero_certidao_nova=request.POST.get('numero_certidao_nova'),

            # ENDEREÇO
            endereco=request.POST.get('endereco'),
            numero=request.POST.get('numero'),
            complemento=request.POST.get('complemento'),
            bairro=request.POST.get('bairro'),
            municipio=request.POST.get('municipio'),
            uf_endereco=request.POST.get('uf_endereco'),

            # TRANSPORTE
            transporte_escolar=bool(request.POST.get('transporte_escolar')),
            tipo_veiculo=request.POST.get('tipo_veiculo'),

            # RESPONSÁVEIS
            nome_mae=request.POST.get('nome_mae'),
            contato_mae=request.POST.get('contato_mae'),
            rg_mae=request.POST.get('rg_mae'),
            estado_rg_mae=request.POST.get('estado_rg_mae'),
            data_emissao_rg_mae=safe_parse_date(request.POST.get('data_emissao_rg_mae')),
            orgao_emissor_mae=request.POST.get('orgao_emissor_mae'),
            cpf_mae=request.POST.get('cpf_mae'),

            nome_pai=request.POST.get('nome_pai'),
            contato_pai=request.POST.get('contato_pai'),
            rg_pai=request.POST.get('rg_pai'),
            estado_rg_pai=request.POST.get('estado_rg_pai'),
            data_emissao_rg_pai=safe_parse_date(request.POST.get('data_emissao_rg_pai')),
            orgao_emissor_pai=request.POST.get('orgao_emissor_pai'),
            cpf_pai=request.POST.get('cpf_pai'),

            data_matricula=safe_parse_date(request.POST.get('data_matricula')),
        )

        aluno.save()
        messages.success(request, "Aluno cadastrado com sucesso!")
        return redirect('escolas:listar_alunos')

    return render(request, 'portal/cadastrar_aluno.html', {
        'turmas': turmas,
        'polo': polo
    })

@login_required
def editar_aluno(request, aluno_id):
    perfil = request.user.perfilusuario
    polo = perfil.polo

    aluno = get_object_or_404(Aluno, id=aluno_id)

    # Permissão
    if perfil.cargo not in ['diretoria', 'secretaria', 'admin_global']:
        messages.error(request, "Você não tem permissão para editar alunos.")
        return redirect('escolas:listar_alunos')

    # Evita que funcionários de um polo editem alunos de outro polo
    if not getattr(perfil, 'is_admin_global', False) and aluno.polo != polo:
        messages.error(request, "Você não pode editar alunos de outro polo.")
        return redirect('escolas:listar_alunos')

    # Turmas filtradas
    if getattr(perfil, 'is_admin_global', False):
        turmas = Turma.objects.all()
    else:
        turmas = Turma.objects.filter(polo=polo)

    def safe_parse_date(value):
        if not value:
            return None
        try:
            return parse_date(value)
        except Exception:
            return None

    if request.method == "POST":
        nome = request.POST.get("nome")
        matricula = request.POST.get("matricula")
        turma_id = request.POST.get("turma")

        if not nome or not matricula or not turma_id:
            messages.error(request, "Preencha todos os campos obrigatórios.")
            return redirect('escolas:editar_aluno', aluno_id=aluno.id)

        turma = get_object_or_404(Turma, id=turma_id)

        # Restrição de polo ao editar
        if not getattr(perfil, 'is_admin_global', False) and turma.polo != polo:
            messages.error(request, "A turma selecionada não pertence ao seu polo.")
            return redirect('escolas:editar_aluno', aluno_id=aluno.id)

        # -------- Atualizando aluno --------
        aluno.nome = nome
        aluno.matricula = matricula
        aluno.turma = turma
        aluno.polo = turma.polo if getattr(perfil, 'is_admin_global', False) else polo

        # DADOS PESSOAIS
        aluno.data_nascimento = safe_parse_date(request.POST.get('data_nascimento'))
        aluno.cor_raca = request.POST.get('cor_raca')
        aluno.sexo = request.POST.get('sexo')
        aluno.nacionalidade = request.POST.get('nacionalidade')
        aluno.estado_nascimento = request.POST.get('estado_nascimento')
        aluno.municipio_nascimento = request.POST.get('municipio_nascimento')

        # SAÚDE
        aluno.tipo_deficiencia = request.POST.get('tipo_deficiencia')
        aluno.alergia_alimentar = bool(request.POST.get('alergia_alimentar'))
        aluno.descricao_alergia = request.POST.get('descricao_alergia')

        # DOCUMENTOS
        aluno.rg = request.POST.get('rg')
        aluno.complemento_rg = request.POST.get('complemento_rg')
        aluno.orgao_emissor = request.POST.get('orgao_emissor')
        aluno.uf_rg = request.POST.get('uf_rg')
        aluno.data_expedicao_rg = safe_parse_date(request.POST.get('data_expedicao_rg'))
        aluno.cpf = request.POST.get('cpf')
        aluno.nis = request.POST.get('nis')
        aluno.cartao_sus = request.POST.get('cartao_sus')
        aluno.bolsa_familia = bool(request.POST.get('bolsa_familia'))
        aluno.origem_quilombola = bool(request.POST.get('origem_quilombola'))

        # CERTIDÃO
        aluno.tipo_certidao = request.POST.get('tipo_certidao')
        aluno.numero_termo = request.POST.get('numero_termo')
        aluno.numero_livro = request.POST.get('numero_livro')
        aluno.numero_folha = request.POST.get('numero_folha')
        aluno.uf_certidao = request.POST.get('uf_certidao')
        aluno.data_emissao_certidao = safe_parse_date(request.POST.get('data_emissao_certidao'))
        aluno.municipio_cartorio = request.POST.get('municipio_cartorio')
        aluno.nome_cartorio = request.POST.get('nome_cartorio')
        aluno.numero_certidao_nova = request.POST.get('numero_certidao_nova')

        # ENDEREÇO
        aluno.endereco = request.POST.get('endereco')
        aluno.numero = request.POST.get('numero')
        aluno.complemento = request.POST.get('complemento')
        aluno.bairro = request.POST.get('bairro')
        aluno.municipio = request.POST.get('municipio')
        aluno.uf_endereco = request.POST.get('uf_endereco')

        # TRANSPORTE
        aluno.transporte_escolar = bool(request.POST.get('transporte_escolar'))
        aluno.tipo_veiculo = request.POST.get('tipo_veiculo')

        # RESPONSÁVEIS
        aluno.nome_mae = request.POST.get('nome_mae')
        aluno.contato_mae = request.POST.get('contato_mae')
        aluno.rg_mae = request.POST.get('rg_mae')
        aluno.estado_rg_mae = request.POST.get('estado_rg_mae')
        aluno.data_emissao_rg_mae = safe_parse_date(request.POST.get('data_emissao_rg_mae'))
        aluno.orgao_emissor_mae = request.POST.get('orgao_emissor_mae')
        aluno.cpf_mae = request.POST.get('cpf_mae')

        aluno.nome_pai = request.POST.get('nome_pai')
        aluno.contato_pai = request.POST.get('contato_pai')
        aluno.rg_pai = request.POST.get('rg_pai')
        aluno.estado_rg_pai = request.POST.get('estado_rg_pai')
        aluno.data_emissao_rg_pai = safe_parse_date(request.POST.get('data_emissao_rg_pai'))
        aluno.orgao_emissor_pai = request.POST.get('orgao_emissor_pai')
        aluno.cpf_pai = request.POST.get('cpf_pai')

        aluno.data_matricula = safe_parse_date(request.POST.get('data_matricula'))

        aluno.save()
        messages.success(request, "Aluno atualizado com sucesso!")
        return redirect('escolas:listar_alunos')

    # GET → carregar dados no template
    return render(request, 'portal/cadastrar_aluno.html', {
        'turmas': turmas,
        'polo': polo,
        'aluno': aluno,   # ← Enviando o aluno para preencher o template
        'editando': True  # ← Para o template saber que é edição
    })


@login_required
def excluir_aluno(request, aluno_id):
    polo = request.user.perfilusuario.polo
    perfil = request.user.perfilusuario
    aluno = get_object_or_404(Aluno, id=aluno_id)

    if not perfil.is_admin_global and aluno.polo != perfil.polo:
        messages.error(request, "Você não pode excluir alunos de outro polo.")
        return redirect('escola:listar_alunos')

    aluno.delete()
    messages.success(request, "Aluno excluído com sucesso!")
    return redirect('escola:listar_alunos', {'polo':polo})


@login_required
def cadastrar_disciplina(request, polo_id):
    perfil = request.user.perfilusuario

    # Verifica permissão
    if perfil.cargo not in ['diretoria', 'secretaria', 'admin_global']:
        messages.error(request, "Você não tem permissão para criar alunos.")
        return redirect('escolas:listar_alunos')
    polo = get_object_or_404(Polo, id=polo_id)

    if request.method == 'POST':
        nome = request.POST.get('nome')

        if not nome:
            return render(request, 'portal/cadastrar_disciplina.html', {
                'erro': 'Preencha o nome da disciplina.',
                'polo': polo
            })

        # Verifica se já existe disciplina com esse nome no polo
        if Disciplina.objects.filter(nome__iexact=nome, polo=polo).exists():
            return render(request, 'portal/cadastrar_disciplina.html', {
                'erro': 'Essa disciplina já existe neste polo.',
                'polo': polo
            })

        Disciplina.objects.create(nome=nome, polo=polo)
        return redirect('escolas:listar_turmas', polo_id=polo.id)

    return render(request, 'portal/cadastrar_disciplina.html', {'polo': polo})

@login_required
def atribuir_professor_disciplina(request, turma_id):
    polo = request.user.perfilusuario.polo
    turma = get_object_or_404(Turma, id=turma_id)

    # Lista apenas professores e disciplinas do mesmo polo
    professores = Professor.objects.filter(polo=turma.polo)
    disciplinas = Disciplina.objects.filter(polo=turma.polo)

    if request.method == 'POST':
        professor_id = request.POST.get('professor')
        disciplina_id = request.POST.get('disciplina')

        # Impedir duplicação da disciplina na turma
        if TurmaProfessorDisciplina.objects.filter(turma=turma, disciplina_id=disciplina_id).exists():
            return render(request, 'portal/vincular_turmaprof.html', {
                'erro': 'Essa disciplina já foi atribuída a essa turma.',
                'turma': turma,
                'professores': professores,
                'disciplinas': disciplinas
            })

        TurmaProfessorDisciplina.objects.create(
            turma=turma,
            professor_id=professor_id,
            disciplina_id=disciplina_id
        )

        return redirect('escolas:detalhes_da_turma', polo_id=turma.polo.id, turma_id=turma.id)

    return render(request, 'portal/vincular_turmaprof.html', {
        'turma': turma,
        'polo': polo,
        'professores': professores,
        'disciplinas': disciplinas
    })

@login_required
def remover_disciplina_turma(request, polo_id, turma_id, tpd_id):
    polo = get_object_or_404(Polo, id=polo_id)
    turma = get_object_or_404(Turma, id=turma_id)

    perfil = request.user.perfilusuario

    # Garantir permissão de acesso ao polo
    if not is_global(request.user) and perfil.polo != polo:
        messages.error(request, "Você não tem permissão para acessar este polo.")
        return redirect('portal:home')

    # Buscar o vínculo professor-disciplina-turma
    tpd = get_object_or_404(TurmaProfessorDisciplina, id=tpd_id, turma=turma)

    # Remover vínculo
    tpd.delete()

    messages.success(request, "A disciplina foi removida da turma com sucesso.")
    return redirect("escolas:detalhes_da_turma", polo_id=polo_id, turma_id=turma_id)

from django.db.models.functions import Lower

@login_required
def detalhes_da_turma(request, polo_id, turma_id):
    polo = get_object_or_404(Polo, id=polo_id)
    turma = get_object_or_404(Turma, id=turma_id, polo=polo)
    perfil = request.user.perfilusuario  

    # Alunos
    alunos = turma.alunos_turma.all().order_by(Lower('nome'))

    # Buscar cada disciplina com seu vínculo
    vinculos = TurmaProfessorDisciplina.objects.filter(
        turma=turma
    ).select_related("disciplina", "professor")

    disciplinas_vinculadas = [
        {
            "disciplina": v.disciplina,
            "tpd_id": v.id,
        }
        for v in vinculos
    ]

    return render(request, "portal/detalhes_da_turma.html", {
        "polo": polo,
        "turma": turma,
        "alunos": alunos,
        "disciplinas_vinculadas": disciplinas_vinculadas,
    })


@login_required
def gerar_calendario(request):
    if not is_global(request.user):
        return HttpResponse("Acesso negado")

    ano = int(request.POST.get('ano', date.today().year))

    # Verifica se já existem dias no ano
    if not DiaLetivo.objects.filter(data__year=ano).exists():
        data_atual = date(ano, 1, 1)
        data_fim = date(ano, 12, 31)

        while data_atual <= data_fim:
            DiaLetivo.objects.get_or_create(data=data_atual)
            data_atual += timedelta(days=1)

    return redirect('escolas:calendario_admin_ano', ano=ano)


@login_required
def calendario_admin(request, ano=None):
    if not is_global(request.user):
        return redirect('escolas:calendario_publico')

    # pega o ano da URL ou da querystring ?ano=2025 ou usa o ano atual
    if ano is None:
        ano = request.GET.get("ano", date.today().year)

    try:
        ano = int(ano)
    except:
        ano = date.today().year

    # GARANTE que o calendário exista
    if not DiaLetivo.objects.filter(data__year=ano).exists():
        data_atual = date(ano, 1, 1)
        data_fim = date(ano, 12, 31)

        while data_atual <= data_fim:
            DiaLetivo.objects.get_or_create(data=data_atual)
            data_atual += timedelta(days=1)

    dias = DiaLetivo.objects.filter(data__year=ano)
    dias_dict = {d.data: d for d in dias}
    # aqui vamos enviar os meses estruturados
    from calendar import monthrange
    import calendar

    meses = []
    dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
    cores = {
    'normal': None,
    'letivo': 'green',
    'feriado': 'red',
    'sabado_letivo': 'yellow',
    'avaliacao': 'blue',
    'reuniao': 'purple',
    'eventos': 'orange',
}

    for mes in range(1, 13):
        nome_mes = calendar.month_name[mes]

        primeiro_dia_semana, total_dias = monthrange(ano, mes)

        offset = (primeiro_dia_semana + 1) % 7
        dias_mes = [None] * offset # espaços em branco antes do primeiro dia

        for dia_num in range(1, total_dias + 1):
            data_dia = date(ano, mes, dia_num)
            dia_info = dias_dict.get(data_dia)

            dias_mes.append({
                    "data": data_dia,
                    "cor": cores.get(dia_info.tipo, None) if dia_info else None,
                    "hoje": data_dia == date.today(),
                    "id": getattr(dia_info, "id", None), 
            })

        meses.append({
            "nome": nome_mes,
            "dias": dias_mes
        })
    legend = {
        'green': 'Início/Fim do Período Letivo',
        'red': 'Feriado',
        'yellow': 'Sábado Letivo',
        'blue': 'Avaliação',
        'purple': 'Reunião',
        'orange': 'Eventos',
        None: 'Dia de Aula'
        } 

    return render(request, "portal/calendario_admin.html", {
        "ano": ano,
        "meses": meses,
        "dias_semana": dias_semana,
        "legend": legend,
    })


@login_required
def editar_dia(request, id):
    if not is_global(request.user):
        return HttpResponse("Acesso negado")

    dia = get_object_or_404(DiaLetivo, id=id)

    if request.method == 'POST':
        dia.tipo = request.POST.get('tipo')
        dia.descricao = request.POST.get('descricao')
        dia.save()
        return redirect('escolas:calendario_admin_ano', ano=dia.data.year)

    return render(request, 'portal/editar_dia.html', {'dia': dia})

@login_required
def calendario_publico(request, polo_id, ano=None):
    polo = get_object_or_404(Polo, id=polo_id)

    hoje = timezone.now().date()

    # Ano selecionado ou ano atual
    ano_atual = ano if ano else int(request.GET.get('ano', hoje.year))

    dias_ano = DiaLetivo.objects.filter(data__year=ano_atual).order_by('data')
    dias_dict = {dia.data: dia for dia in dias_ano}

    cal = calendar.Calendar(firstweekday=6)  # Domingo

    busca = request.GET.get('q', '').strip().lower()
    mes_num = None
    if busca:
        meses_dict = get_month_names(locale='pt_BR')
        mes_num = next((num for num, nome in meses_dict.items() if nome.lower() == busca), None)

    meses_para_exibir = [mes_num] if mes_num else range(1, 13)

    # Mapeamento tipo -> cor usada no template
    cores = {
        'normal': None,
        'letivo': 'green',
        'feriado': 'red',
        'sabado_letivo': 'yellow',
        'avaliacao': 'blue',
        'reuniao': 'purple',
        'eventos': 'orange',
    }

    meses = []
    for mes in meses_para_exibir:
        data_ref = date(ano_atual, mes, 1)
        mes_nome = format_date(data_ref, format='MMMM', locale='pt_BR').capitalize()

        semanas_numeros = list(cal.monthdayscalendar(ano_atual, mes))
        dias = []
        for semana in semanas_numeros:
            for dia_num in semana:
                if dia_num == 0:
                    dias.append(None)
                else:
                    data_atual = date(ano_atual, mes, dia_num)
                    dia_obj = dias_dict.get(data_atual)

                    if dia_obj:
                        cor = cores.get(dia_obj.tipo, None)
                        dias.append({
                            'id': dia_obj.id,
                            'data': dia_obj.data,
                            'hoje': data_atual == hoje,
                            'cor': cor,
                            'descricao': dia_obj.descricao,
                        })
                    else:
                        dias.append({
                            'id': None,
                            'data': data_atual,
                            'hoje': data_atual == hoje,
                            'cor': None,
                        })

        while len(dias) < 42:
            dias.append(None)

        meses.append({
            'numero': mes,
            'nome': mes_nome,
            'dias': dias,
            'busca': busca,
        })

    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sab']
    legend = {
    'green': 'Início/Fim do Período Letivo',
    'red': 'Feriado',
    'yellow': 'Sábado Letivo',
    'blue': 'Avaliação',
    'purple': 'Reunião',
    'orange': 'Eventos',
    None: 'Dia de Aula'
    }   

    contexto = {
        'ano': ano_atual,
        'meses': meses,
        'dias_semana': dias_semana,
        'busca': busca,
        'polo': polo,
        'legend': legend,
    }

    return render(request, 'portal/calendario_academico.html', contexto)


@login_required
def lancar_notas_turma(request):
    perfil = request.user.perfilusuario  # PerfilUsuario
    polo = getattr(perfil, 'polo', None)

    # Verifica se o perfil está vinculado a um polo
    if not polo:
        messages.error(request, "Seu perfil não está vinculado a um polo.")
        return redirect('portal:home')

    # Tenta identificar se o perfil é professor
    professor = Professor.objects.filter(user=perfil).first()

    # 🔒 Filtra turmas e disciplinas conforme cargo
    if perfil.cargo == 'professor' and professor:
        turmas = Turma.objects.filter(
            polo=polo,
            turma_prof_disciplinas__professor=professor
        ).distinct()
        disciplinas = Disciplina.objects.filter(
            polo=polo,
            id__in=TurmaProfessorDisciplina.objects.filter(
                professor=professor
            ).values_list('disciplina_id', flat=True)
        ).distinct()
    else:
        # secretaria, coordenação, diretoria, admin_global...
        turmas = Turma.objects.filter(polo=polo)
        disciplinas = Disciplina.objects.filter(polo=polo)

    bimestres = ['1º', '2º', '3º']
    turma_id = request.POST.get('turma')
    disciplina_id = request.POST.get('disciplina')
    bimestre = request.POST.get('bimestre')
    acao = request.POST.get('acao')

    alunos = []
    notas_existentes = {}

    # ========== FILTRAR ALUNOS E NOTAS ==========
    if acao == 'filtrar' and turma_id and disciplina_id and bimestre:
        turma = get_object_or_404(Turma, id=turma_id)
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)

        if perfil.cargo != 'admin_global' and turma.polo != polo:
            messages.error(request, "Você não tem acesso a essa turma.")
            return redirect('escolas:lancar_notas')

        alunos = Aluno.objects.filter(turma=turma).order_by('nome')

        # Verifica permissão do professor
        if perfil.cargo == 'professor' and professor:
            autorizado = TurmaProfessorDisciplina.objects.filter(
                turma=turma, disciplina=disciplina, professor=professor
            ).exists()
            if not autorizado:
                messages.error(request, "Você não tem permissão para lançar notas nesta turma ou disciplina.")
                return redirect('escolas:lancar_notas')

        notas_existentes = {
            n.aluno.id: n for n in Nota.objects.filter(
                turma=turma, disciplina=disciplina, bimestre=bimestre
            )
        }

    # ========== SALVAR NOTAS ==========
    if acao == 'salvar' and turma_id and disciplina_id and bimestre:
        turma = get_object_or_404(Turma, id=turma_id)
        disciplina = get_object_or_404(Disciplina, id=disciplina_id)
        alunos = Aluno.objects.filter(turma=turma)

        for aluno in alunos:
            nota_val = request.POST.get(f'nota_{aluno.id}') or '0'
            simulado_val = request.POST.get(f'simulado_{aluno.id}') or '0'
            recuperacao_val = request.POST.get(f'recuperacao_{aluno.id}') or ''

            try:
                nota_val = Decimal(nota_val)
                simulado_val = Decimal(simulado_val)
                recuperacao_val = Decimal(recuperacao_val) if recuperacao_val else None
            except:
                continue

            nota, _ = Nota.objects.get_or_create(
                aluno=aluno,
                turma=turma,
                disciplina=disciplina,
                bimestre=bimestre,
                defaults={
                    'usuario_lancou': request.user,
                    'cargo_lancou': perfil.cargo,
                    'polo': turma.polo if hasattr(turma, 'polo') else None,
                    'professor': professor if perfil.cargo == 'professor' else None
                }
            )

            nota.notas = nota_val
            nota.simulado = simulado_val
            nota.recuperacao = recuperacao_val
            nota.usuario_lancou = request.user
            nota.cargo_lancou = perfil.cargo
            nota.save()

        messages.success(request, "Notas salvas com sucesso!")
        return redirect('escolas:lancar_notas')

    # ========== CONTEXTO ==========
    context = {
        'turmas': turmas,
        'disciplinas': disciplinas,
        'bimestres': bimestres,
        'turma_id': turma_id,
        'disciplina_id': disciplina_id,
        'bimestre': bimestre,
        'alunos': alunos,
        'polo': polo,
        'notas_existentes': notas_existentes,
    }

    return render(request, 'portal/lancar_notas.html', context)

@login_required
def Ver_notas(request, polo_id, turma_id, disciplina_id):
    perfil = request.user.perfilusuario
    professor = Professor.objects.filter(user=perfil).first() if perfil else None
    polo = get_object_or_404(Polo, id=polo_id)

    #  Professores podem ver suas turmas e disciplinas
    if perfil.cargo == 'professor':
        if not TurmaProfessorDisciplina.objects.filter(
            professor=professor,
            turma_id=turma_id,
            disciplina_id=disciplina_id
        ).exists():
            messages.error(request, "Você não tem permissão para ver notas desta turma.")
            return redirect('portal:home')
    elif perfil.cargo != 'admin_global' and perfil.polo != polo:
        messages.error(request, "Você não tem permissão para acessar este polo.")
        return redirect('portal:home')

    turma = get_object_or_404(Turma, id=turma_id, polo=polo)
    disciplina = get_object_or_404(Disciplina, id=disciplina_id, polo=polo)

    # Monta dicionário de notas por aluno
    notas_por_aluno = defaultdict(dict)
    notas = Nota.objects.filter(
        turma=turma,
        disciplina=disciplina,
        aluno__turma=turma,
        aluno__polo=polo
    ).order_by('aluno__nome')

    bimestres_existentes = sorted(
        set(n.bimestre for n in notas if n.bimestre != 'Recuperação'),
        key=lambda x: ['1º', '2º', '3º'].index(x)
    )

    for nota in notas:
        aluno_id = nota.aluno.id
        notas_por_aluno[aluno_id]['nome'] = nota.aluno.nome
        notas_por_aluno[aluno_id][str(nota.bimestre)] = nota

    # Calcula média final de cada aluno e situação
    medias_finais = []
    for aluno_id, dados in notas_por_aluno.items():
        soma_unidades = 0
        count_unidades = 0
        recuperacao = None

        for bimestre in bimestres_existentes:
            nota = dados.get(bimestre)
            if nota:
                media_bimestre = float(nota.notas or 0) + float(nota.simulado or 0)
                soma_unidades += media_bimestre
                count_unidades += 1
                if nota.recuperacao is not None:
                    recuperacao = nota.recuperacao

        media_final = round(soma_unidades / count_unidades, 2) if count_unidades > 0 else 0
        dados['media_final'] = media_final
        dados['recuperacao'] = recuperacao

        # Situação
        if media_final >= 6:
            dados['status'] = 'Aprovado'
        else:
            if recuperacao is not None:
                dados['status'] = 'Aprovado após recuperação' if recuperacao >= 6 else 'Reprovado'
            else:
                dados['status'] = 'Recuperação Necessária'

        medias_finais.append(media_final)

    # Média da turma
    media_turma = round(sum(medias_finais) / len(medias_finais), 2) if medias_finais else 0

    # Frequência média da turma
    frequencias = Frequencia.objects.filter(
        aula__turma=turma,
        aula__disciplina=disciplina,
        aluno__polo=polo
    )
    resumo_frequencia = frequencias.values('aluno__nome').annotate(
        presencas=Count('id', filter=Q(presente=True)),
        total=Count('id')
    )
    total_presencas = sum(item['presencas'] for item in resumo_frequencia)
    total_aulas = sum(item['total'] for item in resumo_frequencia)
    frequencia_media = round((total_presencas / total_aulas) * 100, 1) if total_aulas > 0 else 0
    frequencia_faltas = 100 - frequencia_media

    context = {
        'polo': polo,
        'turma': turma,
        'disciplina': disciplina,
        'notas_por_aluno': dict(notas_por_aluno),
        'bimestres': bimestres_existentes,
        'media_turma': media_turma,
        'frequencia_media': frequencia_media,
        'frequencia_faltas': frequencia_faltas,
        'cargo_usuario': perfil.cargo,  # 👈 para mostrar no template
    }

    return render(request, 'portal/ver_notas_da_turma.html', context)

@login_required
def perfil_aluno(request, polo_id, aluno_id):

    usuario = request.user
    perfil = usuario.perfilusuario
    polo = get_object_or_404(Polo, id=polo_id)

    # ADMIN GLOBAL — pode acessar tudo
    if is_global(usuario):
        pass

    else:
        # Usuário comum precisa estar no polo correto
        if not perfil.polo or perfil.polo != polo:
            messages.error(request, "Você não tem permissão para acessar este polo.")
            return redirect('portal:home')


    # 3. Buscar aluno sempre pelo polo da URL
    aluno = get_object_or_404(Aluno, id=aluno_id, polo=polo)

    turma_atual = aluno.turma
    disciplinas = []

    # #  Envio de mensagem via WhatsApp
    # if request.method == 'POST':
    #     if usuario.cargo not in ['secretaria', 'diretoria']:
    #         messages.error(request, "Você não tem permissão para enviar mensagens.")
    #         return redirect('escolas:perfil_aluno', aluno_id=aluno.id)

    #     texto = request.POST.get('mensagem')
    #     numero = aluno.contato_mae or aluno.contato_pai or ''  # Pega número do responsável
    #     numero = numero.replace(" ", "").replace("(", "").replace(")", "").replace("-", "")

    #     if not numero:
    #         messages.error(request, "O aluno não possui número de contato cadastrado.")
    #         return redirect('escolas:perfil_aluno', aluno_id=aluno.id)

    #     # Garante formato +55DDDNÚMERO
    #     if not numero.startswith('+'):
    #         numero = f'+55{numero}'

    #     token = "dtxuuvfhmrpn8evi"
    #     instance_id = "instance145663"
    #     url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    #     payload = {"to": numero, "body": texto}
    #     headers = {'Content-Type': 'application/json'}

    #     try:
    #         response = requests.post(url, json=payload, headers=headers, params={"token": token})
    #         if response.status_code == 200:
    #             MensagensWhatsapp.objects.create(
    #                 remetente=usuario,
    #                 aluno=aluno,
    #                 mensagem=texto,
    #                 status='Enviada'
    #             )
    #             messages.success(request, f"Mensagem enviada com sucesso para o responsável de {aluno.nome}!")
    #         else:
    #             messages.error(request, f"Erro ao enviar mensagem: {response.text}")
    #     except Exception as e:
    #         messages.error(request, f"Falha ao conectar com o WhatsApp: {str(e)}")

    #     return redirect('escolas:perfil_aluno', aluno_id=aluno.id)

    # Monta informações de desempenho
    if turma_atual:
        tpd_list = TurmaProfessorDisciplina.objects.filter(turma=turma_atual)

        for tpd in tpd_list:
            disciplina = tpd.disciplina
            notas_obj = Nota.objects.filter(aluno=aluno, disciplina=disciplina, turma=turma_atual)

            if not notas_obj.exists():
                continue

            bimestres_existentes = ['1º', '2º', '3º']
            notas_por_bimestre = {}
            soma_notas = 0
            quantidade_bimestres = 0

            for b in bimestres_existentes:
                n = notas_obj.filter(bimestre=b).first()
                if n:
                    total_bimestre = float(n.notas or 0) + float(n.simulado or 0)
                    notas_por_bimestre[b] = total_bimestre
                    soma_notas += total_bimestre
                    quantidade_bimestres += 1
                else:
                    notas_por_bimestre[b] = 0

            media_final = round(soma_notas / quantidade_bimestres, 2) if quantidade_bimestres else 0

            # Status
            if media_final >= 6:
                status = 'Aprovado'
            elif any(n.recuperacao for n in notas_obj):
                status = 'Aprovado após recuperação' if media_final >= 6 else 'Reprovado'
            else:
                status = 'Recuperação Necessária'

            # Frequência
            total_aulas = Aula.objects.filter(turma=turma_atual, disciplina=disciplina).count()
            presencas = Frequencia.objects.filter(
                aluno=aluno,
                aula__turma=turma_atual,
                aula__disciplina=disciplina,
                presente=True
            ).count()

            frequencia_media = round((presencas / total_aulas) * 100, 1) if total_aulas else 0
            frequencia_faltas = 100 - frequencia_media

            disciplinas.append({
                'disciplina': disciplina,
                'media_final': media_final,
                'status': status,
                'frequencia_media': frequencia_media,
                'frequencia_faltas': frequencia_faltas,
                'notas_por_bimestre': notas_por_bimestre,
            })

    contexto = {
        'aluno': aluno,
        'dados_aluno': aluno,
        'usuario': usuario,
        'turma_atual': turma_atual,
        'disciplinas': disciplinas,
        'polo': polo,
    }

    return render(request, 'portal/perfil_aluno.html', contexto)

@login_required
def lancar_frequencia(request, polo_id):
    usuario = request.user
    perfil = usuario.perfilusuario

    polo = get_object_or_404(Polo, id=polo_id)
    turmas = Turma.objects.filter(polo=polo)

  
    # Captura de parâmetros
  
    turma_id = request.POST.get("turma") or request.GET.get("turma_id")
    disciplina_id = request.POST.get("disciplina")
    professor_id = request.POST.get("professor")
    data = request.POST.get("data")
    horario = request.POST.get("horario")
    aula_id = request.POST.get("aula_id")

    disciplinas = []
    professores = []
    alunos = []
    aula = None
    frequencias = {}

   
    # CARREGA DISCIPLINAS E PROFESSORES VINCULADOS À TURMA
    
    if turma_id:
        disciplinas = Disciplina.objects.filter(
            id__in=TurmaProfessorDisciplina.objects.filter(
                turma_id=turma_id
            ).values("disciplina_id")
        )
        professores = Professor.objects.filter(
            id__in=TurmaProfessorDisciplina.objects.filter(
                turma_id=turma_id
            ).values("professor_id")
        )
        alunos = Aluno.objects.filter(
            turma_id=turma_id,
            status_matricula="ativo"
        )

    # -------------------------------------------------------------
    # BOTÃO "BUSCAR ALUNOS" — CRIAR OU RECUPERAR AULA
    # -------------------------------------------------------------
    if "buscar_alunos" in request.POST:

        # Validação obrigatória
        if not (turma_id and disciplina_id and professor_id and data and horario):
            messages.error(request, "Selecione Turma, Disciplina, Professor, Data e Horário.")
            return redirect(request.path + f"?turma_id={turma_id}")

        # Primeiro tenta buscar aula existente
        aula = Aula.objects.filter(
            turma_id=turma_id,
            disciplina_id=disciplina_id,
            data=data,
            horario=horario
        ).first()

        # Se não existir → cria
        if not aula:
            try:
                aula = Aula.objects.create(
                    turma_id=turma_id,
                    disciplina_id=disciplina_id,
                    professor_id=professor_id,
                    data=data,
                    horario=horario
                )
            except ValidationError:
                messages.error(request, "Já existe uma aula para essa turma neste horário.")
                return redirect(request.path + f"?turma_id={turma_id}")

        aula_id = aula.id

        # Carrega frequências existentes
        frequencias = {
            f.aluno_id: f.presente
            for f in Frequencia.objects.filter(aula=aula)
        }

    # -------------------------------------------------------------
    # BOTÃO "SALVAR FREQUÊNCIA"
    # -------------------------------------------------------------
    if "salvar_frequencia" in request.POST:
        if not aula_id:
            messages.error(request, "Nenhuma aula foi encontrada. Clique primeiro em Buscar Alunos.")
            return redirect(f"{request.path}?turma_id={turma_id or ''}")

        # Recupera aula com segurança
        aula = Aula.objects.filter(id=aula_id).first()
        if not aula:
            messages.error(request, "A aula escolhida não existe mais.")
            return redirect(request.path)

        # Salva presença aluno a aluno
        for aluno in aula.turma.alunos_turma.all():
            presente = request.POST.get(f"presente_{aluno.id}") == "on"

            freq, created = Frequencia.objects.get_or_create(
                aula=aula,
                aluno=aluno,
                defaults={"presente": presente}
            )
            if not created:
                freq.presente = presente
                freq.save()

        messages.success(request, "Frequência salva com sucesso!")

        # Redireciona para continuar editando a mesma aula
        return redirect(
            reverse("escolas:frequencia_por_turma", args=[aula.turma.id, polo_id])
        )

    # -------------------------------------------------------------
    # QUANDO A VIEW CARREGA COM AULA ID VIA GET (EDIÇÃO)
    # -------------------------------------------------------------
    if not aula and aula_id:
        aula = Aula.objects.filter(id=aula_id).first()
        if aula:
            turma_id = aula.turma.id
            disciplina_id = aula.disciplina.id
            professor_id = aula.professor.id
            data = aula.data
            horario = aula.horario

            alunos = Aluno.objects.filter(
                turma_id=turma_id,
                status_matricula="ativo"
            )

            frequencias = {
                f.aluno_id: f.presente
                for f in Frequencia.objects.filter(aula=aula)
            }

    context = {
        "turmas": turmas,
        "disciplinas": disciplinas,
        "professores": professores,
        "turma_id": turma_id,
        "disciplina_id": disciplina_id,
        "professor_id": professor_id,
        "data": data,
        "horario": horario,
        "alunos": alunos,
        "aula": aula,
        "frequencias": frequencias,
        "polo": polo,
    }

    return render(request, "portal/lancar_frequencia.html", context)

@login_required
def editar_frequencia(request, polo_id, aula_id):
    usuario = request.user
    perfil = usuario.perfilusuario

    polo = get_object_or_404(Polo, id=polo_id)
    aula = get_object_or_404(Aula, id=aula_id)

    turma = aula.turma
    disciplina = aula.disciplina
    professor = aula.professor

    turmas = Turma.objects.filter(polo=polo)

    disciplinas = Disciplina.objects.filter(
        id__in=TurmaProfessorDisciplina.objects.filter(
            turma=turma
        ).values('disciplina_id')
    )

    professores = Professor.objects.filter(
        id__in=TurmaProfessorDisciplina.objects.filter(
            turma=turma
        ).values('professor_id')
    )

    alunos = Aluno.objects.filter(turma=turma, status_matricula='ativo')

    # =====================================================
    #  SALVAR FREQUÊNCIA AO EDITAR
    # =====================================================
    if "salvar_frequencia" in request.POST:
        for aluno in alunos:
            presente = request.POST.get(f"presente_{aluno.id}") == "on"

            freq, created = Frequencia.objects.get_or_create(
                aula=aula,
                aluno=aluno,
                defaults={'presente': presente}
            )

            if not created:
                freq.presente = presente
                freq.save()

        messages.success(request, "Frequência editada com sucesso!")
        return redirect(f"/escolas/frequencia/{polo_id}/lancar/?turma_id={turma.id}&aula_id={aula.id}")

    # Frequências atuais para exibição
    frequencias = {
        f.aluno_id: f.presente
        for f in Frequencia.objects.filter(aula=aula)
    }

    context = {
        'turma_id': str(turma.id),
        'disciplina_id': str(disciplina.id),
        'professor_id': str(professor.id) if professor else "",
        'data': aula.data.strftime("%Y-%m-%d"),
        'horario': aula.horario,

        'turmas': turmas,
        'disciplina': disciplina,
        'disciplinas': disciplinas,
        'professores': professores,

        'aula_id': aula.id,
        'aula': aula,
        'alunos': alunos,
        'frequencias': frequencias,
        'polo': polo,
    }

    return render(request, "portal/lancar_frequencia.html", context)

@login_required
def Historico_escolar(request, polo_id, aluno_id):

    usuario = request.user
    perfil = usuario.perfilusuario

    polo = get_object_or_404(Polo, id=polo_id)

    # Permissão
    if not is_global(usuario):
        if not perfil.polo or perfil.polo != polo:
            messages.error(request, "Você não tem permissão para acessar este polo.")
            return redirect('portal:home')

    # Aluno
    aluno = get_object_or_404(Aluno, id=aluno_id, polo=polo)

    turma_id = request.GET.get('turma_id')

    # Turma atual ou turma selecionada
    if turma_id:
        turma = get_object_or_404(Turma, id=turma_id, polo=polo)
    else:
        turma = aluno.turma

    # Busca notas e frequência
    notas = Nota.objects.filter(
        aluno=aluno,
        turma=turma
    ).select_related('disciplina')

    frequencias = Frequencia.objects.filter(
        aluno=aluno,
        aula__turma=turma
    ).select_related('aula')

    # Todas relações da turma (disciplinas)
    relacoes = TurmaProfessorDisciplina.objects.filter(
        turma=turma
    ).select_related('disciplina')

    historico = []

    for relacao in relacoes:
        disciplina = relacao.disciplina

        # Filtra notas dessa disciplina
        notas_disciplina = [
            n for n in notas if n.disciplina_id == disciplina.id
        ]

        # Filtra frequência dessa disciplina corretamente
        frequencias_disciplina = [
            f for f in frequencias if f.aula.disciplina_id == disciplina.id
        ]

        # Média
        medias_bimestre = [
            (n.notas or 0) + (n.simulado or 0) for n in notas_disciplina
        ]

        media = sum(medias_bimestre) / 3 if medias_bimestre else None

        # Recuperação
        recuperacoes = [n.recuperacao for n in notas_disciplina if n.recuperacao]
        recuperacao_max = max(recuperacoes) if recuperacoes else None

        # Status da disciplina
        if media is None:
            status = "Sem notas"
        else:
            media_final = media
            if recuperacao_max:
                media_final = max(media, recuperacao_max)

            status = "Aprovado" if media_final >= 6 else "Reprovado"

        # Frequência
        total_freq = len(frequencias_disciplina)
        presentes = len([f for f in frequencias_disciplina if f.presente])

        freq_percentual = (presentes / total_freq) * 100 if total_freq else None

        historico.append({
            'disciplina': disciplina,
            'notas': notas_disciplina,
            'media': media,
            'frequencia': freq_percentual,
            'status': status,
        })

    # TODAS AS TURMAS DO ALUNO
    turmas_ids = list(
        HistoricoTurmaAluno.objects.filter(aluno=aluno)
        .values_list('turma_id', flat=True)
    )

    if aluno.turma:
        turmas_ids.append(aluno.turma.id)

    turmas_do_aluno = Turma.objects.filter(
        id__in=turmas_ids,
        polo=polo
    ).order_by('ano', 'nome').distinct()

    context = {
        'aluno': aluno,
        'turma': turma,
        'historico': historico,
        'data_hoje': date.today(),
        'turmas_do_aluno': turmas_do_aluno,
        'polo': polo,
    }

    return render(request, 'portal/historico_escolar.html', context)




@login_required
def Enviar_historico_pdf(request, polo_id, aluno_id):
    perfil = request.user.perfilusuario
    polo = get_object_or_404(Polo, id=polo_id)

    # Permissão
    if not is_global(request.user) and perfil.polo != polo:
        messages.error(request, "Você não tem permissão para acessar este polo.")
        return redirect('portal:home')

    aluno = get_object_or_404(Aluno, id=aluno_id, polo=polo)

    # ===============================
    # COLETAR TODAS AS TURMAS DO ALUNO (SEGURO E À PROVA DE ERROS)
    # ===============================
    turmas = []

    # 1 — Histórico de turmas
    historico_ids = HistoricoTurmaAluno.objects.filter(
        aluno=aluno
    ).values_list("turma", flat=True)

    if historico_ids:
        turmas += list(
            Turma.objects.filter(id__in=historico_ids, polo=polo)
        )

    # 2 — Turma atual (FK normal)
    if hasattr(aluno, "turma") and aluno.turma:
        turmas.append(aluno.turma)

    # 3 — ManyToMany
    if hasattr(aluno.turma, "all"):
        turmas += list(aluno.turma.all())

    # Remover None e duplicados
    turmas = [t for t in turmas if t]
    turmas = list(dict.fromkeys(turmas))  # remove duplicados mantendo ordem

    # Ordenação (mais organizado)
    turmas = sorted(turmas, key=lambda x: (x.ano if hasattr(x,'ano') else 0, x.nome))

    # Se não houver nenhuma turma, evitar PDF vazio
    if not turmas:
        turmas = []

    # ===============================
    # GERAR HISTÓRICO DE CADA TURMA
    # ===============================
    historico_geral = []

    for turma in turmas:

        notas = Nota.objects.filter(
            aluno=aluno, turma=turma
        ).select_related('disciplina')

        frequencias = Frequencia.objects.filter(
            aluno=aluno, aula__turma=turma
        )

        relacoes = TurmaProfessorDisciplina.objects.filter(
            turma=turma
        )

        historico = []

        for relacao in relacoes:
            disciplina = relacao.disciplina

            notas_disciplina = [
                n for n in notas if n.disciplina == disciplina
            ]

            frequencias_disciplina = [
                f for f in frequencias
                if f.aula and f.aula.disciplina == disciplina
            ]

            # Média
            medias = [(n.notas or 0) + (n.simulado or 0)
                      for n in notas_disciplina]

            media = sum(medias) / len(medias) if medias else None

            # Recuperação
            recuperacoes = [n.recuperacao for n in notas_disciplina if n.recuperacao]
            recuperacao_max = max(recuperacoes) if recuperacoes else None

            if media is not None:
                if media >= 6:
                    status = "Aprovado"
                elif recuperacao_max and max(media, recuperacao_max) >= 6:
                    status = "Aprovado"
                else:
                    status = "Reprovado"
            else:
                status = "Sem notas"

            # Frequência
            total_freq = len(frequencias_disciplina)
            presentes = len([f for f in frequencias_disciplina if f.presente])

            frequencia_percentual = (
                (presentes / total_freq) * 100 if total_freq else None
            )

            historico.append({
                'disciplina': disciplina,
                'notas': notas_disciplina,
                'media': media,
                'frequencia': frequencia_percentual,
                'status': status,
            })

        historico_geral.append({
            'turma': turma,
            'historico': historico,
        })

    # ===============================
    # RENDERIZAR PDF
    # ===============================
    template = get_template('portal/historico_escolar_pdf.html')

    html = template.render({
        'aluno': aluno,
        'turmas': historico_geral,
        'data_hoje': datetime.date.today(),
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="historico_{aluno.nome}.pdf"'
    )

    result = pisa.CreatePDF(
        BytesIO(html.encode('utf-8')),
        dest=response,
        encoding='UTF-8'
    )

    # DEBUG — Se der erro, mostre o HTML
    if result.err:
        return HttpResponse(html)

    return response



@login_required
def Enviar_historico_completo_pdf(request, polo_id, aluno_id):
    perfil = request.user.perfilusuario
    polo = get_object_or_404(Polo, id=polo_id)

    # Permissão
    if not is_global(request.user) and perfil.polo != polo:
        messages.error(request, "Você não tem permissão para acessar este polo.")
        return redirect('portal:home')

    aluno = get_object_or_404(Aluno, id=aluno_id, polo=polo)

    data_hoje = datetime.date.today()

    # ===============================
    # COLETAR TODAS AS TURMAS DO ALUNO
    # ===============================
    turmas = []

    # Turmas de histórico
    historico_ids = list(
        HistoricoTurmaAluno.objects.filter(aluno=aluno).values_list("turma", flat=True)
    )

    if historico_ids:
        turmas += list(Turma.objects.filter(id__in=historico_ids, polo=polo))

    # Turma atual FK
    if hasattr(aluno, "turma") and aluno.turma:
        turmas.append(aluno.turma)

    # Turma ManyToMany
    if hasattr(aluno.turma, "all"):
        turmas += list(aluno.turma.all())

    # Remover None e duplicados
    turmas = [t for t in turmas if t]
    turmas = list(dict.fromkeys(turmas))

    # Ordenar
    turmas = sorted(turmas, key=lambda x: (x.ano if hasattr(x,'ano') else 0, x.nome))

    # ===============================
    # GERAR HISTÓRICO COMPLETO
    # ===============================
    historico_geral = []

    for turma in turmas:

        notas = Nota.objects.filter(
            aluno=aluno, turma=turma
        ).select_related('disciplina')

        frequencias = Frequencia.objects.filter(
            aluno=aluno, aula__turma=turma
        )

        disciplinas = TurmaProfessorDisciplina.objects.filter(turma=turma)

        historico_turma = []

        for r in disciplinas:
            disciplina = r.disciplina

            notas_disciplina = [n for n in notas if n.disciplina == disciplina]

            frequencias_disciplina = [
                f for f in frequencias if f.aula and f.aula.disciplina == disciplina
            ]

            medias = [(n.notas or 0) + (n.simulado or 0) for n in notas_disciplina]
            media = sum(medias) / len(medias) if medias else None

            recuperacoes = [n.recuperacao for n in notas_disciplina if n.recuperacao]
            recuperacao_max = max(recuperacoes) if recuperacoes else None

            if media is not None:
                if media >= 6 or (recuperacao_max and recuperacao_max >= 6):
                    status = "Aprovado"
                else:
                    status = "Reprovado"
            else:
                status = "Sem notas"

            total_freq = len(frequencias_disciplina)
            presentes = len([f for f in frequencias_disciplina if f.presente])
            freq_percentual = (presentes / total_freq) * 100 if total_freq else None

            historico_turma.append({
                'disciplina': disciplina,
                'notas': notas_disciplina,
                'media': media,
                'frequencia': freq_percentual,
                'status': status,
            })

        historico_geral.append({
            'turma': turma,
            'historico': historico_turma,
        })

    # ===============================
    # GERAR PDF
    # ===============================
    template = get_template('portal/historico_escolar_completo.html')

    html = template.render({
        'aluno': aluno,
        'turmas': historico_geral,
        'data_hoje': data_hoje,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        f'attachment; filename="historico_{aluno.nome}.pdf"'
    )

    result = pisa.CreatePDF(
        BytesIO(html.encode('utf-8')),
        dest=response,
        encoding='UTF-8'
    )

    # DEBUG — Se der erro, mostre o HTML
    if result.err:
        return HttpResponse(html)

    return response



@method_decorator(login_required, name='dispatch')
class AprovarAlunoView(View):
    template_name = 'portal/aprovar_alunos.html'

    def get(self, request, polo_id):
        polo = get_object_or_404(Polo, id=polo_id)

        ano_atual = timezone.now().year

        turmas_atuais = Turma.objects.filter(
            polo=polo,
            ano_letivo=ano_atual
        ).order_by('nome')

        return render(request, self.template_name, {
            'polo': polo,
            'turmas_atuais': turmas_atuais,
        })

    def post(self, request, polo_id):
        polo = get_object_or_404(Polo, id=polo_id)

        turma_atual_id = request.POST.get('turma_atual')
        turma_atual = get_object_or_404(Turma, id=turma_atual_id)

        ano_novo = turma_atual.ano_letivo + 1  

        def criar_turma(nome):
            turma, criada = Turma.objects.get_or_create(
                nome=nome,
                ano=turma_atual.ano,
                ano_letivo=ano_novo,
                polo=polo
            )
            return turma

        def proxima_serie(nome):
            try:
                numero = int(nome.split("º")[0])
                return nome.replace(f"{numero}º", f"{numero+1}º")
            except:
                return nome  

        nome_turma_nova = proxima_serie(turma_atual.nome)

        turma_aprovados = criar_turma(nome_turma_nova)
        turma_reprovados = criar_turma(turma_atual.nome)

        alunos_aprovados = []
        alunos_reprovados = []

        for aluno in Aluno.objects.filter(turma=turma_atual):
            disciplinas_da_turma = Disciplina.objects.filter(
                turmaprofessordisciplina__turma=turma_atual
            ).distinct()

            aprovado_em_todas_disciplinas = True

            for disciplina in disciplinas_da_turma:
                notas_disciplina = Nota.objects.filter(
                    aluno=aluno,
                    turma=turma_atual,
                    disciplina=disciplina
                )

                if not notas_disciplina.exists():
                    aprovado_em_todas_disciplinas = False
                    break

                soma_total = 0
                quantidade_bimestres = 0

                for nota in notas_disciplina:
                    soma_total += (nota.notas or 0) + (nota.simulado or 0)
                    quantidade_bimestres += 1

                media_final_disciplina = soma_total / 3 if quantidade_bimestres else 0

                recuperacoes = notas_disciplina.values_list('recuperacao', flat=True)
                maior_recuperacao = max([r for r in recuperacoes if r is not None] + [0])

                if media_final_disciplina < 6 and maior_recuperacao > 0:
                    media_final_disciplina = maior_recuperacao

                if media_final_disciplina < 6:
                    aprovado_em_todas_disciplinas = False
                    break

            total_aulas = Frequencia.objects.filter(
                aluno=aluno,
                aula__turma=turma_atual
            ).count()

            presencas = Frequencia.objects.filter(
                aluno=aluno,
                aula__turma=turma_atual,
                presente=True
            ).count()

            frequencia_total = (presencas / total_aulas) * 100 if total_aulas else 0

            aprovado_freq = frequencia_total >= 75

            if aprovado_em_todas_disciplinas and aprovado_freq:
                nova_turma = turma_aprovados
                alunos_aprovados.append(aluno)
            else:
                nova_turma = turma_reprovados
                alunos_reprovados.append(aluno)

            hist = HistoricoTurmaAluno.objects.filter(
                aluno=aluno,
                turma=turma_atual,
                data_fim__isnull=True
            ).first()

            if hist:
                hist.data_fim = timezone.now().date()
                hist.save()

            novo_hist = HistoricoTurmaAluno.objects.create(
                aluno=aluno,
                turma=nova_turma
            )

            aluno.turma = nova_turma
            aluno.turma_atual = nova_turma
            aluno.save()

        messages.success(request, f"{len(alunos_aprovados)} alunos aprovados!")
        messages.warning(request, f"{len(alunos_reprovados)} alunos reprovados!")

        return render(request, self.template_name, {
            'polo': polo,
            'turmas_atuais': Turma.objects.filter(polo=polo, ano_letivo=turma_atual.ano_letivo),
            'alunos_aprovados': alunos_aprovados,
            'alunos_reprovados': alunos_reprovados,
            'turma_antiga': turma_atual,
            'turma_nova': turma_aprovados,
            'turma_repetida': turma_reprovados
        })
    
import random
@login_required
def Gerar_grade_horaria(request, polo_id, turma_id):
    turma = get_object_or_404(Turma, id=turma_id, polo_id=polo_id)
    perfil = request.user.perfilusuario
    polo = get_object_or_404(Polo, id=polo_id)

    if not is_global(request.user) and perfil.polo != polo:
        messages.error(request, "Você não tem permissão para acessar este polo.")
        return redirect('portal:home')

    # Horários
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    horarios = [
        (time(7,30), time(8,20)),
        (time(8,20), time(9,10)),
        (time(9,10), time(10,0)),
        (time(10,20), time(11,10)),
        (time(11,10), time(12,0)),
    ]

    # Cria lista de slots
    slots = [(dia, inicio, fim) for dia in dias for inicio, fim in horarios]
    random.shuffle(slots)  # embaralha → distribuição aleatória

    # Busca prioridades
    prioridades_ids = request.session.get("prioridades_grade", [])
    prioridades = Disciplina.objects.filter(id__in=prioridades_ids)

    # Mapeia Disciplina → Professor
    tpd = TurmaProfessorDisciplina.objects.filter(turma=turma)
    dados = {x.disciplina: x.professor for x in tpd}

    # Limpa grade antiga
    GradeHoraria.objects.filter(turma=turma).delete()

    # Controle de aulas por disciplina
    contador = {disc: 0 for disc in dados.keys()}

    # ALOCA PRIORIDADES (máx 4)
    for disc in prioridades:
        prof = dados.get(disc)
        for dia, inicio, fim in slots:
            if contador[disc] >= 4:
                break

            # Verifica professor livre
            if GradeHoraria.objects.filter(
                professor=prof,
                dia_semana=dia,
                horario_inicio=inicio
            ).exists():
                continue

            # Verifica turma livre
            if GradeHoraria.objects.filter(
                turma=turma,
                dia_semana=dia,
                horario_inicio=inicio
            ).exists():
                continue

            # Aloca aula
            GradeHoraria.objects.create(
                turma=turma,
                disciplina=disc,
                professor=prof,
                dia_semana=dia,
                horario_inicio=inicio,
                horario_fim=fim
            )
            contador[disc] += 1

    # ALOCA RESTANTE (máximo 4)
    restantes = [d for d in dados.keys() if d not in prioridades]
    restantes = random.sample(restantes, len(restantes))  # embaralhar ordem

    for disc in restantes:
        prof = dados.get(disc)
        for dia, inicio, fim in slots:
            if contador[disc] >= 4:
                break

            # Colisão professor
            if GradeHoraria.objects.filter(
                professor=prof,
                dia_semana=dia,
                horario_inicio=inicio
            ).exists():
                continue

            # Colisão turma
            if GradeHoraria.objects.filter(
                turma=turma,
                dia_semana=dia,
                horario_inicio=inicio
            ).exists():
                continue

            # Alocar
            GradeHoraria.objects.create(
                turma=turma,
                disciplina=disc,
                professor=prof,
                dia_semana=dia,
                horario_inicio=inicio,
                horario_fim=fim
            )
            contador[disc] += 1

    return redirect("escolas:visualizar_grade_horaria", polo_id=polo.id, turma_id=turma.id)


@login_required
def Opcoes_grade_horaria(request, polo_id, turma_id):
    turma = get_object_or_404(Turma, id=turma_id, polo_id=polo_id)
    perfil = request.user.perfilusuario
    polo = get_object_or_404(Polo, id=polo_id)

    if not is_global(request.user) and perfil.polo != polo:
        messages.error(request, "Você não tem permissão para acessar este polo.")
        return redirect('portal:home')

    # AGORA CARREGA TODAS AS DISCIPLINAS
    disciplinas = Disciplina.objects.all().order_by("nome")

    if request.method == "POST":
        prioridades = request.POST.getlist("prioridade")
        request.session["prioridades_grade"] = prioridades
        return redirect("escolas:gerar_grade_horaria", polo_id=polo_id, turma_id=turma_id)

    return render(request, "portal/opcoes_grade_horaria.html", {
        "turma": turma,
        "disciplinas": disciplinas,
        "polo_id": polo_id,
    })


@login_required
def Visualizar_grade(request, turma_id, polo_id):
    perfil = request.user.perfilusuario
    polo = get_object_or_404(Polo, id=polo_id)
    

# Permissão
    # if not is_global(perfil):
    #     if not perfil.polo or perfil.polo != polo:
    #         messages.error(request, "Você não tem permissão para acessar este polo.")
    #         return redirect('portal:home')

    turma = get_object_or_404(Turma, id=turma_id)

    horarios_slots = [
        (time(7,30), time(8,20)),
        (time(8,20), time(9,10)),
        (time(9,10), time(10,0)),
        (time(10,20), time(11,10)),
        (time(11,10), time(12,0)),
    ]

    dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]

    grade_final = []
    for inicio, fim in horarios_slots:
        linha = {"horario": (inicio, fim), "dias": []}
        for dia in dias_semana:
            aula = GradeHoraria.objects.filter(
                turma=turma,
                dia_semana=dia,
                horario_inicio=inicio,
                horario_fim=fim
            ).first()
            linha["dias"].append(aula)
        grade_final.append(linha)

    return render(request, "portal/visualizar_grade.html", {
        "turma": turma,
        "grade": grade_final,
        "dias_semana": dias_semana,
        "polo":polo,
    })

@login_required
def FrequenciaTurma(request, turma_id, polo_id):
    turma = get_object_or_404(Turma, id=turma_id)
    polo = get_object_or_404(Polo, id=polo_id)

    aulas = Aula.objects.filter(turma=turma).order_by('-data', 'horario')
    frequencias_por_aula = {}
    busca = request.GET.get('q', '').strip()

    if busca:
        data_formatada = None
        try:
            if "/" in busca:
                dia, mes, ano = busca.split("/")
                data_formatada = datetime.date(int(ano), int(mes), int(dia))
        except:
            pass

        aulas = aulas.annotate(
            horario_str=Cast('horario', output_field=CharField()),
        ).filter(
            Q(disciplina__nome__icontains=busca) |
            Q(professor__nome__icontains=busca) |
            Q(horario_str__icontains=busca) |
            (Q(data=data_formatada) if data_formatada else Q())
        ).distinct()

    for aula in aulas:

        # 🔥 SE A AULA AINDA NÃO TEM PROFESSOR, PEGAR AUTOMATICAMENTE
        if not aula.professor:
            relacao = TurmaProfessorDisciplina.objects.filter(
                turma=aula.turma,
                disciplina=aula.disciplina
            ).select_related('professor').first()

            if relacao:
                aula.professor = relacao.professor
                aula.save()  # grava no banco para nunca mais ficar None

        # Frequências
        lista_frequencias = Frequencia.objects.filter(aula=aula).select_related('aluno')

        # 🔥 Aqui enviamos para o template um dicionário com professor + frequências
        frequencias_por_aula[aula] = {
            "professor": aula.professor,
            "frequencias": lista_frequencias
        }

    return render(request, 'portal/frequencia_por_turma.html', {
        'turma': turma,
        'frequencias_por_aula': frequencias_por_aula,
        'busca': busca,
        'polo': polo
    })

@login_required
def Aulas_da_turma(request, turma_id, polo_id):
    turma = get_object_or_404(Turma, id=turma_id)
    polo = get_object_or_404(Polo, id=polo_id)
    aulas = Aula.objects.filter(turma=turma).order_by('-data', 'horario')
    busca = request.GET.get('q', '').strip()

    if busca:
        # Tenta converter a busca em data (ex: de "25/05/2025" para "2025-05-25")
        data_formatada = None
        try:
            if "/" in busca:
                dia, mes, ano = busca.split("/")
                data_formatada = datetime.date(int(ano), int(mes), int(dia))
        except:
            pass

        aulas = aulas.annotate(
            horario_str=Cast('horario', output_field=CharField()),
        ).filter(
            Q(disciplina__nome__icontains=busca) |
            Q(professor__nome__icontains=busca) |
            Q(horario_str__icontains=busca) |
            (Q(data=data_formatada) if data_formatada else Q())
        )
    return render(request, 'portal/aulas_da_turma.html',{
        'turma':turma,
        'aulas':aulas, 
        'busca':busca,
        'polo': polo,
        } )