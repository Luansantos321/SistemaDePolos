
# Create your models here.
from django.db import models
from core.models import Polo
import datetime
from decimal import Decimal
from django.conf import settings
from usuarios.models import PerfilUsuario
from django.core.exceptions import ValidationError


def ano_atual():
    return datetime.date.today().year

class Turma(models.Model):
    polo = models.ForeignKey(Polo,on_delete=models.CASCADE, related_name='turmas')
    nome = models.CharField(max_length=20)
    turno = models.CharField(max_length=10, choices=[('Manhã', 'Manhã'),('Tarde','Tarde'), ('Integral', 'Integral')], default='Manhã')
    ano = models.IntegerField(default=ano_atual)  # <-- corrigido
    ano_letivo = models.IntegerField(default=datetime.date.today().year)
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['nome', 'ano', 'ano_letivo', 'polo'], name='unique_turma_por_polo')
        ]

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo}"


class Professor(models.Model):
    user = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, null=True, blank=True, related_name='professor')
    polo = models.ForeignKey(Polo, on_delete=models.CASCADE, related_name='professores')
    nome = models.CharField(max_length=150)
    email = models.EmailField(blank=True, null=True)

    # Documentos pessoais
    cpf = models.CharField(max_length=14, unique=True)
    rg = models.CharField(max_length=20, blank=True, null=True)
    orgao_emissor = models.CharField(max_length=20, blank=True, null=True)
    uf_rg = models.CharField(max_length=2, blank=True, null=True)
    data_emissao_rg = models.DateField(blank=True, null=True)
    data_nascimento = models.DateField(blank=True, null=True)

    # Formação acadêmica
    formacao_academica = models.CharField(max_length=200, blank=True, null=True)
    nivel_superior = models.BooleanField(default=False)
    pos_graduacao = models.CharField(max_length=200, blank=True, null=True)
    curso_formacao = models.CharField(max_length=150, blank=True, null=True)
    instituicao_formacao = models.CharField(max_length=150, blank=True, null=True)

    def __str__(self):
        return f"{self.nome} ({self.polo})"

class Aluno(models.Model):
    STATUS_MATRICULA_CHOICES = [
        ('ativo', 'Ativo'),
        ('transferido', 'Transferido'),
        ('cancelado', 'Cancelado'),
        ('concluido', 'Concluído'),
        ('trancado', 'Trancado'),
    ]
    polo = models.ForeignKey(Polo, on_delete=models.CASCADE, related_name='alunos')
    turma = models.ForeignKey('Turma', on_delete=models.SET_NULL, null=True, blank=True, related_name='alunos_turma')

    # DADOS BÁSICOS
    nome = models.CharField(max_length=150)
    matricula = models.CharField(max_length=50, unique=True)
    data_nascimento = models.DateField(null=True, blank=True)
    cor_raca = models.CharField(max_length=30, blank=True)
    sexo = models.CharField(
        max_length=10,
        choices=[('Masculino', 'Masculino'), ('Feminino', 'Feminino')],
        blank=True
    )
        # 🆕 Novos campos:
    status_matricula = models.CharField(max_length=20,choices=STATUS_MATRICULA_CHOICES,default='ativo')

    foto = models.ImageField(upload_to='alunos/fotos/',blank=True,null=True)
    nacionalidade = models.CharField(max_length=50, blank=True)
    estado_nascimento = models.CharField(max_length=10, blank=True)
    municipio_nascimento = models.CharField(max_length=100, blank=True)

    # SAÚDE E CONDIÇÕES ESPECIAIS
    tipo_deficiencia = models.CharField(max_length=100, blank=True)
    alergia_alimentar = models.BooleanField(default=False)
    descricao_alergia = models.CharField(max_length=200, blank=True)

    # DOCUMENTOS DO ALUNO
    rg = models.CharField("Nº da Identidade", max_length=30, blank=True)
    complemento_rg = models.CharField(max_length=50, blank=True)
    orgao_emissor = models.CharField(max_length=20, blank=True)
    uf_rg = models.CharField(max_length=10, blank=True)
    data_expedicao_rg = models.DateField(null=True, blank=True)
    cpf = models.CharField(max_length=14, blank=True)
    nis = models.CharField(max_length=20, blank=True)
    cartao_sus = models.CharField(max_length=20, blank=True)
    bolsa_familia = models.BooleanField(default=False)
    origem_quilombola = models.BooleanField(default=False)

    # CERTIDÃO (antiga)
    tipo_certidao = models.CharField(
        max_length=20,
        choices=[('Nascimento', 'Nascimento'), ('Casamento', 'Casamento')],
        blank=True
    )
    numero_termo = models.CharField(max_length=30, blank=True)
    numero_livro = models.CharField(max_length=30, blank=True)
    numero_folha = models.CharField(max_length=30, blank=True)
    uf_certidao = models.CharField(max_length=10, blank=True)
    data_emissao_certidao = models.DateField(null=True, blank=True)
    municipio_cartorio = models.CharField(max_length=100, blank=True)
    nome_cartorio = models.CharField(max_length=100, blank=True)

    # CERTIDÃO NOVA (versão atual)
    numero_certidao_nova = models.CharField(max_length=60, blank=True)

    # ENDEREÇO
    endereco = models.CharField(max_length=255, blank=True)
    numero = models.CharField(max_length=10, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    municipio = models.CharField(max_length=100, blank=True)
    uf_endereco = models.CharField(max_length=10, blank=True)

    # TRANSPORTE ESCOLAR
    transporte_escolar = models.BooleanField(default=False)
    tipo_veiculo = models.CharField(max_length=50, blank=True)

    # DADOS DOS RESPONSÁVEIS
    nome_mae = models.CharField(max_length=150, blank=True)
    contato_mae = models.CharField(max_length=20, blank=True)
    rg_mae = models.CharField(max_length=30, blank=True)
    estado_rg_mae = models.CharField(max_length=10, null=True, blank=True)
    data_emissao_rg_mae = models.DateField(null=True, blank=True)
    orgao_emissor_mae = models.CharField(max_length=20, blank=True)
    cpf_mae = models.CharField(max_length=14, blank=True)

    nome_pai = models.CharField(max_length=150, blank=True)
    contato_pai = models.CharField(max_length=20, blank=True)
    rg_pai = models.CharField(max_length=30, blank=True)
    estado_rg_pai = models.CharField(max_length=10, null=True, blank=True)
    data_emissao_rg_pai = models.DateField(null=True, blank=True)
    orgao_emissor_pai = models.CharField(max_length=20, blank=True)
    cpf_pai = models.CharField(max_length=14, blank=True)

    data_matricula = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.nome} - {self.matricula}"

    class Meta:
        verbose_name = "Aluno"
        verbose_name_plural = "Alunos"


class Disciplina(models.Model):
    polo = models.ForeignKey(Polo, on_delete=models.CASCADE, related_name='disciplinas')
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class TurmaProfessorDisciplina(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='turma_prof_disciplinas')
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('turma', 'disciplina')

    def __str__(self):
        return f"{self.turma} - {self.professor} - {self.disciplina}"

class DiaLetivo(models.Model):
    TIPOS_DIAS = [
        ('normal', 'Dia Normal'),
        ('letivo', 'Dia Letivo / Aulas'),
        ('feriado', 'Feriado'),
        ('sabado_letivo', 'Sábado Letivo'),
        ('avaliacao', 'Dia de Avaliação'),
        ('reuniao', 'Reunião Pedagógica'),
        ('eventos', 'Eventos da Escola'),
    ]
    cor = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    data = models.DateField(unique=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_DIAS, default='normal')
    descricao = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['data']

    def __str__(self):
        return f"{self.data} - {self.get_tipo_display()}"


class Nota(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='notas')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.SET_NULL, null=True, blank=True)
    polo = models.ForeignKey(Polo, on_delete=models.CASCADE, related_name='notas')

    notas = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    simulado = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))
    recuperacao = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    bimestre = models.CharField(max_length=10, choices=[('1º', '1º'), ('2º', '2º'), ('3º', '3º')])
    media_final = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, default='Em andamento')

    #  Dados de quem lançou
    usuario_lancou = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    cargo_lancou = models.CharField(max_length=30, null=True, blank=True)

    class Meta:
        unique_together = ('aluno', 'disciplina', 'turma', 'bimestre', 'polo')

    def __str__(self):
        return f'{self.aluno.nome} - {self.disciplina.nome} - {self.bimestre} UND'

    def media_unidades(self):
        notas_val = self.notas if self.notas else 0
        simulado_val = self.simulado if self.simulado else 0
        return (notas_val + simulado_val) / 2

    def save(self, *args, **kwargs):
        if self.recuperacao is not None and self.recuperacao <= 0:
            self.recuperacao = None

        media_unidades = self.media_unidades()
        self.media_final = max(media_unidades, self.recuperacao) if self.recuperacao else media_unidades

        if self.media_final >= 6:
            self.status = 'Aprovado'
        else:
            self.status = 'Recuperação pendente' if self.recuperacao is None else 'Reprovado'

        super().save(*args, **kwargs)

class Aula(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE )
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE, null=True, blank=True)
    data =models.DateField()
    horario =models.TimeField()

    def clean(self):
        from django.utils.timezone import make_aware, datetime

        conflito = Aula.objects.filter(
            turma=self.turma,
            data=self.data,
            horario=self.horario
        ).exclude(id=self.id).exists()

        if conflito:
            raise ValidationError("Já existe uma aula para essa turma nesse horário.")

    def save(self, *args, **kwargs):

        # Se o professor não foi informado, buscar automaticamente
        if not self.professor:
            relacao = TurmaProfessorDisciplina.objects.filter(
                turma=self.turma,
                disciplina=self.disciplina
            ).first()

            if relacao:
                self.professor = relacao.professor

        self.full_clean()
        super().save(*args, **kwargs)
    def __str__(self):
        return f"{self.turma.nome}  - {self.disciplina.nome} - {self.data} -  {self.horario}"
class Frequencia(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='frequencias')
    aula = models.ForeignKey(Aula, on_delete=models.CASCADE, related_name='frequencias',null=True, blank=True)  # link para a aula específica
    presente = models.BooleanField(default=True)

    class Meta:
        unique_together = ('aluno', 'aula')
        permissions = [
            ("view_relatorio_faltas", "Pode visualizar o relatório de faltas"),
        ]

    def __str__(self):
        return f"{self.aluno.nome} - {self.aula} - {'Presente' if self.presente else 'Ausente'}"
    
class HistoricoTurmaAluno(models.Model):
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='historico')
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE)
    data_inicio = models.DateField(auto_now_add=True)
    data_fim = models.DateField(null=True, blank=True)

class GradeHoraria(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='horarios')
    disciplina = models.ForeignKey(Disciplina, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    dia_semana = models.CharField(max_length=10, choices=[
        ('Segunda', 'Segunda'),
        ('Terça', 'Terça'),
        ('Quarta', 'Quarta'),
        ('Quinta', 'Quinta'),
        ('Sexta', 'Sexta'),
    ])
    horario_inicio = models.TimeField()
    horario_fim = models.TimeField()

    class Meta:
        unique_together = ('turma', 'dia_semana', 'horario_inicio')  # evita conflito de horários

    def __str__(self):
        return f"{self.turma} - {self.disciplina} ({self.dia_semana} {self.horario_inicio})"