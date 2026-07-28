# Sistema de Polos

Sistema web desenvolvido com Python e Django para gerenciamento de múltiplos polos educacionais em uma única aplicação.

O sistema permite centralizar o gerenciamento de polos, usuários, turmas e demais informações administrativas, utilizando controle de permissões por perfil e uma arquitetura preparada para expansão.

## Funcionalidades

### Administração

- Cadastro de polos
- Gerenciamento de usuários
- Controle de perfis de acesso
- Painel administrativo

### Gestão Acadêmica

- Cadastro de turmas
- Associação de usuários aos polos
- Organização das informações por unidade
- Controle de acesso aos dados

### Controle de Usuários

- Autenticação
- Controle de permissões
- Diferentes níveis de acesso
- Administração centralizada

## Tecnologias

### Back-end

- Python
- Django

### Banco de Dados

- PostgreSQL
- SQLite (desenvolvimento)

### Front-end

- HTML
- CSS
- Bootstrap
- JavaScript

### Ferramentas

- Git
- GitHub

## Estrutura do Projeto

```text
SistemaDePolos/

├── core/
├── portal/
├── usuarios/
├── escolas/
├── templates/
├── static/
├── media/
├── manage.py
└── requirements.txt
```

## Executando o projeto

Clone o repositório:

```bash
git clone https://github.com/Luansantos321/SistemaDePolos.git
```

Entre na pasta do projeto:

```bash
cd SistemaDePolos
```

Crie um ambiente virtual:

```bash
python -m venv venv
```

Ative o ambiente:

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

Execute as migrações:

```bash
python manage.py migrate
```

Inicie o servidor:

```bash
python manage.py runserver
```

## Arquitetura

O sistema foi desenvolvido seguindo a arquitetura MTV do Django, com separação entre regras de negócio, modelos de dados e interface.

A aplicação foi projetada para suportar múltiplos polos em uma única instalação, permitindo que usuários possuam diferentes níveis de acesso e visualizem apenas as informações autorizadas.

Essa abordagem facilita a escalabilidade do sistema e reduz a duplicação de dados entre unidades.

## Conhecimentos aplicados

Durante o desenvolvimento foram utilizados conceitos como:

- Programação Orientada a Objetos
- Desenvolvimento Web com Django
- Modelagem de Banco de Dados Relacional
- Arquitetura MTV
- Controle de permissões
- Sistema de autenticação
- Relacionamentos entre modelos
- Organização modular de aplicações Django
- Versionamento com Git e GitHub

## Próximas melhorias

- API REST com Django REST Framework
- Dashboard com indicadores por polo
- Relatórios em PDF
- Auditoria de ações dos usuários
- Sistema de notificações
- Melhorias na interface responsiva

## Objetivos do Projeto

O projeto foi desenvolvido com o objetivo de criar uma plataforma centralizada para administração de polos educacionais, permitindo uma gestão organizada, segura e escalável.

Sua arquitetura possibilita o gerenciamento de diferentes unidades dentro de um único sistema, mantendo isolamento das informações e controle de acesso conforme o perfil de cada usuário.

## Autor

**Luan Santos da Silva**

Graduado em Gestão da Tecnologia da Informação.

Atualmente desenvolvendo aplicações web com Python e Django e estudando Java e Spring Boot.

- GitHub: https://github.com/Luansantos321
- LinkedIn: *(adicione seu perfil)*
- E-mail: *(adicione seu e-mail)*

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo `LICENSE` para mais informações.
