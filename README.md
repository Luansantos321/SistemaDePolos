# 🎓 Sistema de Gestão de Polos Educacionais

## 📌 Descrição

Este projeto consiste em um sistema web desenvolvido com o objetivo de auxiliar na gestão de polos educacionais, permitindo o controle de turmas, professores, disciplinas e organização acadêmica.

Um dos principais diferenciais do sistema é a geração automática de grades horárias utilizando técnicas de otimização, garantindo a distribuição eficiente das aulas e evitando conflitos entre professores e turmas.

---

## 🚀 Funcionalidades

- Cadastro e gerenciamento de polos
- Cadastro de turmas com ano letivo e turno
- Cadastro de professores e disciplinas
- Vinculação de professores às disciplinas por turma
- Visualização de grade horária por turma
- Visualização do perfil do professor com suas aulas
- Geração automática de grade horária por turma
- Geração automática de grades para todas as turmas
- Evita conflitos de horários entre professores
- Priorização de disciplinas na geração da grade

---

## 🧠 Inteligência do Sistema

O sistema utiliza um mecanismo de otimização baseado em restrições para gerar as grades horárias.

Essa abordagem permite:

- Distribuição equilibrada das aulas
- Respeito às regras definidas (como evitar conflitos de horário)
- Melhor aproveitamento dos horários disponíveis
- Geração automática de soluções viáveis mesmo com múltiplas restrições

---

## 🛠️ Tecnologias Utilizadas

- Python
- Django
- SQLite (padrão, podendo ser substituído por PostgreSQL)
- HTML / CSS / Bootstrap
- OR-Tools (Google) para otimização da grade horária

---

## ⚙️ Como Executar o Projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/seu-usuario/seu-repositorio.git
