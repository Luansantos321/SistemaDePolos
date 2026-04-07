from ortools.sat.python import cp_model
from collections import defaultdict

def gerar_grade_ortools(turma, dados, dias, horarios, prioridades):
    model = cp_model.CpModel()

    disciplinas = list(dados.keys())
    professores = dados

    # Índices
    D = range(len(disciplinas))
    S = range(len(dias))
    H = range(len(horarios))

    # Variável: x[d, s, h] = disciplina d no dia s e horário h
    x = {}
    for d in D:
        for s in S:
            for h in H:
                x[(d, s, h)] = model.NewBoolVar(f"x_{d}_{s}_{h}")

    # -----------------------------------
    # 🎯 RESTRIÇÃO 1: 1 aula por slot
    # -----------------------------------
    for s in S:
        for h in H:
            model.Add(sum(x[(d, s, h)] for d in D) <= 1)

    # -----------------------------------
    # 🎯 RESTRIÇÃO 2: carga por disciplina (máx 4 ou 5)
    # -----------------------------------
    for d in D:
        model.Add(sum(x[(d, s, h)] for s in S for h in H) <= 5)

    # -----------------------------------
    # 🎯 RESTRIÇÃO 3: não repetir disciplina no mesmo dia
    # -----------------------------------
    for d in D:
        for s in S:
            model.Add(sum(x[(d, s, h)] for h in H) <= 2)

    # -----------------------------------
    # 🎯 RESTRIÇÃO 4: professor não pode chocar horário
    # -----------------------------------
    prof_map = defaultdict(list)

    for d_index, disc in enumerate(disciplinas):
        prof = professores[disc]
        prof_map[prof].append(d_index)

    for prof, d_list in prof_map.items():
        for s in S:
            for h in H:
                model.Add(sum(x[(d, s, h)] for d in d_list) <= 1)

    # -----------------------------------
    # 🎯 FUNÇÃO OBJETIVO (prioridades)
    # -----------------------------------
    objective_terms = []

    for d_index, disc in enumerate(disciplinas):
        for s in S:
            for h in H:
                if disc in prioridades:
                    objective_terms.append(2 * x[(d_index, s, h)])
                else:
                    objective_terms.append(1 * x[(d_index, s, h)])

    model.Maximize(sum(objective_terms))

    # -----------------------------------
    # SOLVER
    # -----------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10

    status = solver.Solve(model)

    resultado = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for d_index, disc in enumerate(disciplinas):
            for s in S:
                for h in H:
                    if solver.Value(x[(d_index, s, h)]) == 1:
                        resultado.append({
                            "disciplina": disc,
                            "professor": professores[disc],
                            "dia": dias[s],
                            "inicio": horarios[h][0],
                            "fim": horarios[h][1],
                        })

    return resultado