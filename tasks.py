# -*- coding: utf-8 -*-
"""
Módulo de Definição de Tarefas (tasks.py)
Define as 4 tarefas sequenciais da equipe de equity research B3.
As tarefas são criadas via função fábrica para receber setor e
segmento como parâmetros em tempo de execução.
"""

from crewai import Task


def criar_tarefas(setor, segmento, triador, auditor, investigador, cio):
    """
    Fábrica de tarefas: recebe o setor, segmento e instâncias dos agentes,
    retornando a lista de 4 tarefas sequenciais já com as descrições preenchidas.

    Args:
        setor (str): Label do setor da B3 (ex: '06 – Bancos').
        segmento (str): Label do segmento/subsetor (pode ser vazio).
        triador: Instância do Agente 1 — Triador Fundamentalista.
        auditor: Instância do Agente 2 — Auditor Temporal.
        investigador: Instância do Agente 3 — Investigador de Governança.
        cio: Instância do Agente 4 — CIO.

    Returns:
        list[Task]: Lista ordenada das 4 tarefas sequenciais.
    """
    # Define o escopo de análise para exibição nas descrições
    escopo = f"setor '{setor}'"
    if segmento:
        escopo += f", segmento '{segmento}'"

    # Input formatado para a ferramenta de triagem
    input_triagem = f"setor={setor}" + (f",segmento={segmento}" if segmento else "")

    # ----------------------------------------------------------------
    # Tarefa 1 — Triagem Fundamentalista (dados reais do Fundamentus)
    # ----------------------------------------------------------------
    tarefa_triagem = Task(
        description=(
            f"Execute a triagem fundamentalista REAL de ações da B3 para o {escopo}.\n\n"
            f"**AÇÃO OBRIGATÓRIA:** Use imediatamente a ferramenta 'triagem_fundamentalista_b3' "
            f"com o seguinte input exato:\n"
            f"  {input_triagem}\n\n"
            "A ferramenta acessa o Fundamentus.com.br pelas URLs:\n"
            f"  - Por setor:    https://fundamentus.com.br/resultado.php?setor=<código>\n"
            f"  - Por segmento: https://fundamentus.com.br/resultado.php?segmento=<código>\n\n"
            "Ela aplica automaticamente o algoritmo de triagem:\n"
            "  1. Descarta imediatamente empresas com P/L negativo ou zerado\n"
            "  2. Ordena as restantes por ROE (Return on Equity) de forma decrescente\n"
            "  3. Cruza e pondera com o Dividend Yield (DY), priorizando maiores valores positivos\n"
            "  4. Retorna a lista limpa com exatamente os Top 5 Tickers resultantes\n\n"
            "Apresente o resultado da ferramenta como sua resposta, adicionando apenas "
            "uma breve observação sobre o critério aplicado."
        ),
        expected_output=(
            "Tabela com os Top 5 tickers da B3 do setor/segmento selecionado, com P/L, "
            "ROE (%) e DY (%), extraída de dados reais do Fundamentus.com.br."
        ),
        agent=triador,
    )

    # ----------------------------------------------------------------
    # Tarefa 2 — Auditoria Temporal (Consistência Histórica do ROE)
    # ----------------------------------------------------------------
    tarefa_auditoria = Task(
        description=(
            "Receba os Top 5 tickers identificados na tarefa anterior e audite a "
            "consistência histórica do ROE de cada empresa no portal Fundamentus.com.br.\n\n"
            "**AÇÃO OBRIGATÓRIA:** Use imediatamente a ferramenta 'auditoria_historica_roe' "
            "passando a lista de tickers como um único texto separado por vírgulas "
            "(exemplo: 'PETR4, VALE3, ITUB4').\n\n"
            "A ferramenta analisa o histórico de gráficos temporais do ROE e crescimento "
            "de receita para determinar se a rentabilidade é:\n"
            "  - Crescente e Consistente (aprovado)\n"
            "  - Estável (aprovado)\n"
            "  - Volátil / Decrescente (reprovado)\n\n"
            "**Procedimento de filtragem:**\n"
            "1. Analise os resultados retornados pela ferramenta.\n"
            "2. **Elimine** as empresas marcadas como 'Aprovado: Não'.\n"
            "3. **Reordene** a lista mantendo apenas empresas consistentes ou estáveis.\n\n"
            "Para cada empresa aprovada, informe na resposta final:\n"
            "- Ticker\n"
            "- ROE Atual (%)\n"
            "- Crescimento de Receita 5a (%)\n"
            "- Tendência do ROE\n"
            "- Aprovado para próxima fase: Sim/Não"
        ),
        expected_output=(
            "Lista reordenada dos tickers aprovados na auditoria histórica, com avaliação "
            "da consistência do ROE e indicação de quais avançam para análise de governança."
        ),
        agent=auditor,
    )

    # ----------------------------------------------------------------
    # Tarefa 3 — Investigação de Governança Corporativa
    # ----------------------------------------------------------------
    tarefa_governanca = Task(
        description=(
            "Receba a lista de empresas aprovadas pela Auditoria Temporal e investigue "
            "a governança corporativa e estrutura acionária de cada uma.\n\n"
            "**AÇÃO OBRIGATÓRIA:** Use imediatamente a ferramenta 'investigacao_governanca_b3' "
            "passando a lista de tickers aprovados separada por vírgulas.\n\n"
            "A ferramenta simula a investigação no portal Fundamentus.com.br e avalia:\n"
            "  - Percentual estimado de Free Float ON (Ações Ordinárias em circulação)\n"
            "  - Nível de Governança da B3 (Novo Mercado, N2, N1, Tradicional)\n"
            "  - Existência de sócios governamentais (risco político/estatal)\n"
            "  - Concentração excessiva de controle acionário\n\n"
            "**Para cada ticker, responda objetivamente:**\n"
            "1. **Free Float Estimado ON:** (retornado pela ferramenta)\n"
            "2. **Concentração de Controle:** (existe acionista majoritário dominante?)\n"
            "3. **Sócios Governamentais (Economia Mista):** Sim/Não e risco associado\n"
            "4. **Nível de Governança B3:** (retornado pela ferramenta)\n"
        ),
        expected_output=(
            "Relatório de governança para cada empresa aprovada, contendo: "
            "Free Float Estimado, Nível de Governança B3, Risco Estatal e "
            "análise de concentração acionária."
        ),
        agent=investigador,
    )

    # ----------------------------------------------------------------
    # Tarefa 4 — Relatório Executivo Final (CIO)
    # ----------------------------------------------------------------
    tarefa_relatorio_cio = Task(
        description=(
            f"Consolide todas as análises anteriores (triagem fundamentalista, auditoria "
            f"histórica e investigação de governança) para o {escopo} e produza o "
            f"Ranking Final de Investimento.\n\n"
            "**Estrutura obrigatória do relatório em Markdown premium:**\n\n"
            "## 📊 Ranking Final — Top Ações para Investimento\n"
            "Crie uma tabela de ranking com colunas:\n"
            "| # | Ticker | ROE (%) | DY (%) | Tendência ROE | Free Float | Risco Estatal | Score |\n\n"
            "## 📋 Justificativa por Empresa\n"
            "Para cada empresa no ranking, escreva um parágrafo executivo justificando "
            "a posição com base no equilíbrio entre:\n"
            "  - ROE estável e crescente (peso maior)\n"
            "  - Dividend Yield robusto e consistente\n"
            "  - Free Float alto (boa liquidez e dispersão acionária)\n"
            "  - Baixo risco de interferência estatal\n\n"
            "## 🎯 Conclusão e Recomendação do Comitê\n"
            "Redija um parágrafo final com a perspectiva geral do setor analisado "
            "e as empresas mais recomendadas para alocação de longo prazo.\n\n"
            "Use Markdown premium para formatação. Tom executivo, sóbrio e objetivo.\n"
            "⚠️ Inclua ao final: 'Este relatório é gerado por IA e não constitui "
            "recomendação de investimento. Consulte um profissional certificado.'"
        ),
        expected_output=(
            "Relatório executivo completo em Markdown com: tabela de ranking final com "
            "score ponderado, justificativas por empresa e conclusão do Comitê de Investimentos, "
            "seguido do disclaimer obrigatório."
        ),
        agent=cio,
    )

    return [tarefa_triagem, tarefa_auditoria, tarefa_governanca, tarefa_relatorio_cio]
