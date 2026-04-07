from ortools.sat.python import cp_model
from collections import defaultdict

def gerar_grade_global(turmas, dias, horarios, tpd_queryset, prioridades):
    model = cp_model.CpModel()

    # Estrutura:
    # (turma, disciplina) → professor
    dados = []
    for item in tpd_queryset:
        dados.append((item.turma, item.disciplina, item.professor))

    T = range(len(turmas))
    D = range(len(dados))
    S = range(len(dias))
    H = range(len(horarios))

    # Variável: x[d, s, h]
    x = {}
    for d in D:
        for s in S:
            for h in H:
                x[(d, s, h)] = model.NewBoolVar(f"x_{d}_{s}_{h}")

    # -----------------------------------
    # 🎯 1. UMA aula por turma por slot
    # -----------------------------------
    for t_index, turma in enumerate(turmas):
        d_list = [i for i, (t, _, _) in enumerate(dados) if t == turma]

        for s in S:
            for h in H:
                model.Add(sum(x[(d, s, h)] for d in d_list) <= 1)

    # -----------------------------------
    # 🎯 2. PROFESSOR NÃO PODE CHOCAR (GLOBAL)
    # -----------------------------------
    prof_map = defaultdict(list)

    for i, (turma, disc, prof) in enumerate(dados):
        prof_map[prof].append(i)

    for prof, d_list in prof_map.items():
        for s in S:
            for h in H:
                model.Add(sum(x[(d, s, h)] for d in d_list) <= 1)

    # -----------------------------------
    # 🎯 3. CARGA MÁXIMA
    # -----------------------------------
    for d in D:
        model.Add(sum(x[(d, s, h)] for s in S for h in H) <= 5)

    # -----------------------------------
    # 🎯 4. NÃO REPETIR MUITO NO MESMO DIA
    # -----------------------------------
    for d in D:
        for s in S:
            model.Add(sum(x[(d, s, h)] for h in H) <= 2)

    # -----------------------------------
    # 🎯 OBJETIVO (PRIORIDADES)
    # -----------------------------------
    objective = []

    for i, (turma, disc, prof) in enumerate(dados):
        for s in S:
            for h in H:
                if disc in prioridades:
                    objective.append(3 * x[(i, s, h)])
                else:
                    objective.append(1 * x[(i, s, h)])

    model.Maximize(sum(objective))

    # -----------------------------------
    # SOLVER
    # -----------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15

    status = solver.Solve(model)

    resultado = []

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i, (turma, disc, prof) in enumerate(dados):
            for s in S:
                for h in H:
                    if solver.Value(x[(i, s, h)]) == 1:
                        resultado.append({
                            "turma": turma,
                            "disciplina": disc,
                            "professor": prof,
                            "dia": dias[s],
                            "inicio": horarios[h][0],
                            "fim": horarios[h][1],
                        })

    return resultado