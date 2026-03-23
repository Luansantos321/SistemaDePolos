from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.painel_view, name='painel'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('home/global/', views.home, name='home'),
    path('home/polo/', views.home_polo, name='home_polo'),  # <- esse é o nome correto
    path('polo/criar/', views.Criar_polo, name='criar_polo'),
    path('polo/<int:polo_id>/editar/', views.Editar_polo, name='editar_polo'),
    path('polo/<int:polo_id>/acessar/', views.acessar_polo, name='acessar_polo'),
    path('criar-usuario/', views.criar_usuario_global, name='criar_usuario'),
    path('usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('usuarios/excluir/<int:user_id>/', views.excluir_usuario, name='excluir_usuario'),
    path('usuarios/remover-acesso/<int:user_id>/', views.remover_acesso, name='remover_acesso'),
    path('usuarios/reativar/<int:user_id>/', views.reativar_acesso, name='reativar_acesso'),

]
