from django.urls import path
from . import views

app_name = 'escolas'

urlpatterns = [
    
    # Turmas
 
    path('turmas/<int:polo_id>/', views.listar_turmas, name='listar_turmas'),
    path('turmas/criar/', views.criar_turma, name='criar_turma'),
    path('turmas/excluir/<int:turma_id>/', views.excluir_turma, name='excluir_turma'),
    path('polo/<int:polo_id>/turma/<int:turma_id>/detalhes/', views.detalhes_da_turma, name='detalhes_da_turma'),
    path('lancar/notas/', views.lancar_notas_turma, name='lancar_notas'),
    path('polo/<int:polo_id>/turma/<int:turma_id>/disciplina/<int:disciplina_id>/notas/', views.Ver_notas, name='ver_notas_da_turma'),
    path('frequencia/<int:polo_id>/lancar/', views.lancar_frequencia, name='lancar_frequencia'),
    path('frequencia/<int:polo_id>/<int:aula_id>/editar/', views.editar_frequencia, name='editar_frequencia'),
    path('turma/<int:polo_id>/<int:turma_id>/aulas', views.Aulas_da_turma, name='aulas_da_turma'),
    path('frequencia/<int:turma_id>/<int:polo_id>/turmas/', views.FrequenciaTurma, name='frequencia_por_turma'),
    path('turmas/<int:polo_id>/<int:turma_id>/gerar-grade/', views.Gerar_grade_horaria, name='gerar_grade_horaria'),
    path('gerar-todas-grades/<int:polo_id>/',views.gerar_todas_grades,name='gerar_todas_grades'),
    path('turmas/<int:polo_id>/<int:turma_id>/gerar-grade-opcoes/', views.Opcoes_grade_horaria, name='opcoes_grade_horaria'),
    path('turmas/<int:polo_id>/<int:turma_id>/grade/', views.Visualizar_grade, name='visualizar_grade_horaria'),
    path("turmas/<int:polo_id>/<int:turma_id>/remover-disciplina/<int:tpd_id>/", views.remover_disciplina_turma, name="remover_disciplina_turma"),

    # Professores
    path('professores/', views.listar_professores, name='listar_professores'),
    path('professores/criar/', views.criar_professor, name='criar_professor'),
    path('professores/excluir/<int:professor_id>/', views.excluir_professor, name='excluir_professor'),
    path('professor/perfil/<int:professor_id>/', views.perfil_professor, name='perfil_professor'),


    # Alunos
    path('alunos/', views.listar_alunos, name='listar_alunos'),
    path('alunos/criar/', views.criar_aluno, name='cadastrar_alunos'),
    path('alunos/<int:aluno_id>/editar/', views.editar_aluno, name='editar_aluno'),
    path('alunos/excluir/<int:aluno_id>/', views.excluir_aluno, name='excluir_aluno'),
    path('aluno/<int:aluno_id>/perfil/<int:polo_id>/', views.perfil_aluno, name='perfil_aluno'),
    path('polo/<int:polo_id>/aprovar/alunos/',views.AprovarAlunoView.as_view(),name='aprovar_alunos'),
    path('polo/<int:polo_id>/aluno/<int:aluno_id>/historico/', views.Historico_escolar, name='historico_escolar'),
    # PDF do histórico da turma selecionada
    path('polo/<int:polo_id>/aluno/<int:aluno_id>/historico/pdf/',views.Enviar_historico_pdf, name='historico_escolar_pdf'),
    # PDF completo (todas as turmas)
    path('polo/<int:polo_id>/aluno/<int:aluno_id>/historico/completo/pdf/', views.Enviar_historico_completo_pdf, name='historico_completo_pdf'),

    #disciplina
    path('polo/<int:polo_id>/disciplinas/cadastrar/', views.cadastrar_disciplina, name='cadastrar_disciplina'),
    path('turma/<int:turma_id>/atribuir-professor-disciplina/', views.atribuir_professor_disciplina, name='atribuir_professor_disciplina'),

    #calendario academico
    path('calendario/admin/', views.calendario_admin, name='calendario_admin'),
    path('calendario/admin/<int:ano>/', views.calendario_admin, name='calendario_admin_ano'),
    path('polo/<int:polo_id>/calendario/', views.calendario_publico, name='calendario_publico'),
    path('calendario/gerar/', views.gerar_calendario, name='gerar_calendario'),
    path('calendario/editar/<int:id>/', views.editar_dia, name='editar_dia'),

    
]
