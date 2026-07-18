# -*- coding: utf-8 -*-
"""
Módulo de Orquestração da Crew (crew.py)
Configura e executa a equipe de equity research B3 de forma sequencial.
Compatível com crewai 0.11+ (kickoff() sem parâmetro inputs).
"""

import sys
from crewai import Crew, Process
from agents import (
    triador_fundamentalista,
    auditor_temporal,
    investigador_governanca,
    cio_alocacao,
)
from tasks import criar_tarefas


# ---------------------------------------------------------------
# Redirecionador de stdout para logs ao vivo no Streamlit
# ---------------------------------------------------------------
class StreamlitLogRedirector:
    """
    Intercepta a saída padrão (stdout) e redireciona para um widget
    Streamlit st.empty(), exibindo os logs dos agentes em tempo real.
    Detecta qual agente está ativo e atualiza o label do st.status().
    """

    # Mensagens de progresso customizadas para cada agente (conforme spec)
    AGENT_LABELS = {
        "Analista de Triagem": (
            "🔍 Agente 1: Aplicando filtros fundamentalistas no Fundamentus..."
        ),
        "Auditor de Consistência": (
            "📊 Agente 2: Analisando consistência histórica do ROE no portal Fundamentus..."
        ),
        "Especialista em Governança": (
            "🏛️ Agente 3: Investigando estrutura acionária e governança corporativa..."
        ),
        "Diretor de Investimentos": (
            "📋 Agente 4: CIO consolidando ranking final de investimento..."
        ),
    }

    def __init__(self, status_widget, log_widget):
        self.status_widget   = status_widget
        self.log_widget      = log_widget
        self.original_stdout = sys.stdout
        self.log_lines       = []

    def write(self, text):
        self.original_stdout.write(text)
        stripped = text.strip()
        if not stripped:
            return

        # Filtra avisos desnecessários das bibliotecas internas
        ignorar = ["UserWarning", "Mixing V1 models", "pydantic", "warnings.warn", "DeprecationWarning"]
        if any(p in stripped for p in ignorar):
            return

        # Detecta qual agente está trabalhando e atualiza o label do status
        for chave, label in self.AGENT_LABELS.items():
            if chave in stripped:
                try:
                    self.status_widget.update(label=label, state="running")
                except Exception:
                    pass
                break

        # Acumula logs e exibe os últimos 30 para não sobrecarregar a tela
        self.log_lines.append(stripped)
        logs_visiveis = "\n".join(self.log_lines[-30:])
        try:
            self.log_widget.code(logs_visiveis, language="text")
        except Exception:
            pass

    def flush(self):
        self.original_stdout.flush()


# ---------------------------------------------------------------
# Função principal de execução da análise
# ---------------------------------------------------------------
def run_analysis(setor, segmento, status_widget=None, log_widget=None):
    """
    Cria as tarefas com o setor/segmento informados, monta a Crew
    e executa o fluxo sequencial de análise fundamentalista B3.

    Args:
        setor (str): Label do setor da B3 selecionado na interface.
        segmento (str): Label do segmento (opcional; pode ser vazio).
        status_widget: Referência ao st.status do Streamlit (opcional).
        log_widget: Referência ao st.empty do Streamlit (opcional).

    Returns:
        str: Relatório executivo final em Markdown produzido pelo CIO.
    """
    # Cria as tarefas com os inputs já interpolados nas descrições
    tarefas = criar_tarefas(
        setor=setor,
        segmento=segmento or "",
        triador=triador_fundamentalista,
        auditor=auditor_temporal,
        investigador=investigador_governanca,
        cio=cio_alocacao,
    )

    # Monta a equipe com processo estritamente sequencial
    equipe = Crew(
        agents=[
            triador_fundamentalista,
            auditor_temporal,
            investigador_governanca,
            cio_alocacao,
        ],
        tasks=tarefas,
        process=Process.sequential,
        verbose=True,
    )

    # Instala o redirecionador de logs se os widgets do Streamlit forem fornecidos
    redirector = None
    if status_widget is not None and log_widget is not None:
        redirector = StreamlitLogRedirector(status_widget, log_widget)
        sys.stdout = redirector

    try:
        resultado = equipe.kickoff()
    finally:
        # Restaura stdout original independentemente de erros
        if redirector is not None:
            sys.stdout = redirector.original_stdout

    return resultado
