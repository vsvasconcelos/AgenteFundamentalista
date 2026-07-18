# -*- coding: utf-8 -*-
"""
Interface Principal Streamlit (app.py)
Plataforma de Triagem Fundamentalista de Ações da B3.

Design: Minimalista e profissional, paleta voltada para o mercado financeiro
com tons adequados para usuários com dificuldades visuais (alto contraste,
sem dependência exclusiva de cor para transmitir informação).

Componentes principais (conforme spec):
  - st.selectbox obrigatório para o Setor da B3
  - st.selectbox dinâmico e opcional para o Segmento (subsetor)
  - st.status() para feedback de execução em tempo real
  - st.dataframe() para o ranking final
  - st.expander() para detalhes de governança por empresa
"""

import streamlit as st

# ---------------------------------------------------------------
# Configuração da Página (deve ser o primeiro comando Streamlit)
# ---------------------------------------------------------------
st.set_page_config(
    page_title="B3 Fundamentalista | Equity Research Automatizado",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": (
            "**B3 Fundamentalista** — Triagem automatizada de ações por IA.\n\n"
            "⚠️ Este sistema não constitui recomendação de investimento."
        )
    },
)

# ---------------------------------------------------------------
# CSS Premium — Paleta financeira de alto contraste (acessível)
# Tons: azul navy, cinza ardósia, verde menta, âmbar para alertas
# ---------------------------------------------------------------
st.markdown(
    """
<style>
    /* Importação de fonte premium via Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* Fundo geral: azul navy escuro */
    .stApp {
        background-color: #0B1622;
    }

    /* Tipografia base */
    html, body, [class*="css"] {
        color: #CBD5E1;
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 15px;
    }

    /* ── Cabeçalho Hero ── */
    .hero-wrapper {
        text-align: center;
        padding: 2.5rem 1rem 1.5rem;
        border-bottom: 1px solid #1E3A52;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-size: 2.8rem;
        font-weight: 800;
        letter-spacing: -0.8px;
        background: linear-gradient(100deg, #38BDF8 0%, #34D399 60%, #A3E635 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.4rem;
        line-height: 1.1;
    }
    .hero-subtitle {
        color: #64748B;
        font-size: 1rem;
        font-weight: 400;
        letter-spacing: 0.3px;
    }
    .hero-badges {
        margin-top: 1rem;
        display: flex;
        justify-content: center;
        gap: 0.6rem;
        flex-wrap: wrap;
    }
    .badge {
        background: #112234;
        border: 1px solid #1E3A52;
        border-radius: 20px;
        padding: 0.28rem 0.9rem;
        font-size: 0.78rem;
        color: #38BDF8;
        font-weight: 500;
        letter-spacing: 0.3px;
    }

    /* ── Card de Configuração ── */
    .config-card {
        background: linear-gradient(135deg, #0F2035 0%, #112234 100%);
        border: 1px solid #1E3A52;
        border-radius: 20px;
        padding: 2rem 2.5rem 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
    }
    .config-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #E2E8F0;
        margin-bottom: 1.2rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Labels dos inputs ── */
    label {
        color: #94A3B8 !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }

    /* ── Selectbox estilo financeiro ── */
    .stSelectbox > div > div,
    .stMultiSelect > div > div {
        background-color: #0B1F32 !important;
        border: 1px solid #1E3A52 !important;
        border-radius: 12px !important;
        color: #E2E8F0 !important;
        font-size: 0.9rem !important;
    }
    .stSelectbox > div > div:focus-within,
    .stMultiSelect > div > div:focus-within {
        border-color: #38BDF8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }

    /* ── Painel de Seleção Ativa ── */
    .selecao-ativa {
        background: #091928;
        border: 1px solid #1E3A52;
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        margin-top: 1rem;
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
        align-items: center;
    }
    .sel-label {
        font-size: 0.78rem;
        color: #64748B;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 0.2rem;
    }
    .sel-valor {
        color: #38BDF8;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .sep { color: #1E3A52; margin: 0 0.3rem; }

    /* ── Botão principal ── */
    div.stButton {
        display: flex;
        justify-content: center;
        margin-top: 1.5rem;
    }
    div.stButton > button {
        background: linear-gradient(135deg, #1D4ED8 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 50px !important;
        padding: 0.8rem 4rem !important;
        font-size: 1rem !important;
        font-weight: 700 !important;
        letter-spacing: 0.6px !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 24px rgba(29, 78, 216, 0.35) !important;
        cursor: pointer !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px rgba(29, 78, 216, 0.55) !important;
        filter: brightness(1.08) !important;
    }
    div.stButton > button:active {
        transform: translateY(0) !important;
    }

    /* ── Divider ── */
    hr {
        border-color: #1E3A52 !important;
        margin: 1.8rem 0 !important;
    }

    /* ── Bloco do relatório final ── */
    .relatorio-final {
        background: linear-gradient(135deg, #091928 0%, #0B1F32 100%);
        border-left: 4px solid #34D399;
        border-radius: 0 16px 16px 0;
        padding: 2rem 2.5rem;
        margin-top: 0.5rem;
        line-height: 1.75;
    }

    /* ── Download button ── */
    div.stDownloadButton > button {
        background: #112234 !important;
        color: #38BDF8 !important;
        border: 1px solid #1E3A52 !important;
        border-radius: 50px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    div.stDownloadButton > button:hover {
        background: #1E3A52 !important;
        border-color: #38BDF8 !important;
    }

    /* ── Rodapé ── */
    .footer {
        text-align: center;
        color: #334155;
        font-size: 0.78rem;
        padding: 1.5rem 0 0.5rem;
        border-top: 1px solid #1E2D3D;
        margin-top: 2rem;
    }
    .footer a { color: #475569; text-decoration: none; }
    .footer a:hover { color: #64748B; }

    /* ── Info box de segmento ── */
    .info-segmento {
        background: #091928;
        border: 1px dashed #1E3A52;
        border-radius: 10px;
        padding: 0.7rem 1rem;
        font-size: 0.82rem;
        color: #64748B;
        margin-top: 0.3rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Cabeçalho Hero
# ---------------------------------------------------------------
st.markdown(
    """
<div class="hero-wrapper">
    <div class="hero-title">📈 B3 Fundamentalista</div>
    <div class="hero-subtitle">
        Equity Research Automatizado · Triagem Quantitativa · Governança Corporativa · CIO Report
    </div>
    <div class="hero-badges">
        <span class="badge">🤖 4 Agentes IA</span>
        <span class="badge">📊 Fundamentus.com.br</span>
        <span class="badge">🏦 42 Setores B3</span>
        <span class="badge">🔎 P/L · ROE · DY</span>
        <span class="badge">🏛️ Governança Corporativa</span>
    </div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# Carregamento dos módulos da Crew (com tratamento de erros)
# ---------------------------------------------------------------
sistema_ok = False
try:
    from crew import run_analysis
    from config import SETORES_B3, SEGMENTOS_POR_GRUPO, MAPA_SETOR_PARA_GRUPO
    sistema_ok = True
except Exception as e:
    st.error(
        f"### ⚠️ Falha ao Inicializar o Sistema\n\n"
        f"Não foi possível carregar os módulos de IA ou as credenciais.\n\n"
        f"**Verifique:**\n"
        f"- Arquivo `keys.txt` com SERPER_API_KEY (linha 1) e OPENROUTER_API_KEY (linha 2)\n"
        f"- Ou `openrouter-key.txt` com a chave OpenRouter separada\n\n"
        f"**Erro:** `{e}`"
    )

# ---------------------------------------------------------------
# Interface de Configuração da Análise
# ---------------------------------------------------------------
if sistema_ok:

    # ── Card de Configuração ──────────────────────────────────────
    st.markdown('<div class="config-card">', unsafe_allow_html=True)
    st.markdown(
        '<div class="config-title">⚙️ Configurar Triagem Fundamentalista</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 1], gap="large")

    # ── Selectbox obrigatório: Setor ───────────────────────────────
    with col1:
        opcoes_setor = list(SETORES_B3.keys())
        setor_selecionado = st.selectbox(
            "Setor da B3 (obrigatório):",
            options=opcoes_setor,
            index=0,
            help=(
                "Selecione o setor econômico da B3. A triagem será aplicada "
                "a todas as empresas do setor, ou refinada por segmento."
            ),
            key="setor_input",
        )

    # ── Selectbox dinâmico e opcional: Segmento ───────────────────
    with col2:
        # Usa o mapeamento explícito para descobrir o grupo de segmentos do setor
        grupo_ativo = MAPA_SETOR_PARA_GRUPO.get(setor_selecionado)

        if grupo_ativo and grupo_ativo in SEGMENTOS_POR_GRUPO:
            segmentos_disponiveis = SEGMENTOS_POR_GRUPO[grupo_ativo]
            opcoes_segmento = ["Todos os segmentos do setor"] + segmentos_disponiveis
            segmento_selecionado = st.selectbox(
                f"Segmento — {grupo_ativo} (opcional):",
                options=opcoes_segmento,
                index=0,
                help=(
                    "Opcional. Refina a busca para um segmento específico dentro do grupo "
                    f"'{grupo_ativo}'. Deixe em 'Todos' para analisar o setor completo."
                ),
                key="segmento_input",
            )
            # Exibe informação sobre o grupo de segmentos ativo
            st.markdown(
                f'<div class="info-segmento">📁 Grupo: <strong>{grupo_ativo}</strong> '
                f'— {len(segmentos_disponiveis)} segmentos disponíveis</div>',
                unsafe_allow_html=True,
            )
        else:
            # Setor sem segmentos específicos mapeados
            segmento_selecionado = "Todos os segmentos do setor"
            st.selectbox(
                "Segmento (opcional):",
                options=["Todos os segmentos do setor"],
                index=0,
                help="Este setor não possui segmentos específicos mapeados.",
                key="segmento_input",
                disabled=True,
            )
            st.markdown(
                '<div class="info-segmento">ℹ️ Este setor não possui subsetores mapeados. '
                "A análise cobrirá o setor completo.</div>",
                unsafe_allow_html=True,
            )

    # Normaliza o segmento (vazio se escolhido "Todos")
    segmento_final = (
        ""
        if segmento_selecionado == "Todos os segmentos do setor"
        else segmento_selecionado
    )

    # ── Painel de Seleção Ativa ────────────────────────────────────
    st.markdown(
        f'<div class="selecao-ativa">'
        f'<span class="sel-label">Setor:</span>'
        f'<span class="sel-valor">{setor_selecionado}</span>'
        f'<span class="sep">|</span>'
        f'<span class="sel-label">Segmento:</span>'
        f'<span class="sel-valor">'
        f'{segmento_final if segmento_final else "Todos"}'
        f"</span>"
        f'<span class="sep">|</span>'
        f'<span class="sel-label">Agentes:</span>'
        f'<span class="sel-valor">4 Agentes IA · Processo Sequencial</span>'
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)  # fecha config-card

    st.markdown("---")

    # ── Botão de Execução ─────────────────────────────────────────
    col_a, col_b, col_c = st.columns([2, 1.5, 2])
    with col_b:
        iniciar = st.button("🚀 Iniciar Triagem", use_container_width=True)

    # ── Fluxo de Execução com st.status() (UX Fantástico) ────────
    if iniciar:
        st.markdown("---")
        st.markdown("### 🔄 Execução da Equipe de Análise")

        with st.status(
            "🔍 Agente 1: Iniciando triagem fundamentalista no Fundamentus...",
            expanded=True,
        ) as status_box:
            log_placeholder = st.empty()

            resultado = None
            try:
                resultado = run_analysis(
                    setor=setor_selecionado,
                    segmento=segmento_final,
                    status_widget=status_box,
                    log_widget=log_placeholder,
                )
                status_box.update(
                    label="✅ Análise Concluída! Relatório do CIO disponível abaixo.",
                    state="complete",
                    expanded=False,
                )
            except Exception as ex:
                status_box.update(
                    label="❌ Erro durante a análise dos agentes.",
                    state="error",
                    expanded=True,
                )
                st.error(
                    f"**Erro na execução da Crew:** `{ex}`\n\n"
                    "Verifique as chaves de API e a conectividade com a internet."
                )

        # ── Exibição do Resultado Final ──────────────────────────
        if resultado:
            resultado_str = str(resultado)

            st.markdown("---")

            # Métricas de resumo
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            with col_m1:
                st.metric("Setor Analisado", setor_selecionado.split("–")[-1].strip())
            with col_m2:
                st.metric("Segmento", segmento_final.split("–")[-1].strip() if segmento_final else "Geral")
            with col_m3:
                st.metric("Agentes Executados", "4")
            with col_m4:
                st.metric("Top Empresas", "5")

            st.markdown("### 📋 Relatório Executivo — Comitê de Investimentos (CIO)")

            # Relatório principal dentro do container estilizado
            st.markdown(
                f'<div class="relatorio-final">\n\n{resultado_str}\n\n</div>',
                unsafe_allow_html=True,
            )

            st.markdown("")

            # Detalhes de governança por empresa (st.expander conforme spec)
            with st.expander("🏛️ Detalhes de Governança por Empresa", expanded=False):
                st.markdown(
                    "**Nota:** Os dados de governança abaixo são extraídos pelo Agente 3 "
                    "com base em heurísticas do Fundamentus. Para detalhes completos, "
                    "consulte o prospecto e os Formulários de Referência na CVM.\n\n"
                    "Os indicadores principais estão consolidados no relatório do CIO acima."
                )
                # Extrai seção de governança do relatório (se existir)
                if "Free Float" in resultado_str or "Governança" in resultado_str:
                    st.markdown(resultado_str)
                else:
                    st.info(
                        "Dados de governança consolidados no relatório do CIO acima. "
                        "Execute novamente para atualizar."
                    )

            # Botão de download
            st.markdown("")
            col_d1, col_d2, col_d3 = st.columns([2, 1.8, 2])
            with col_d2:
                setor_clean = (
                    setor_selecionado.split("–")[-1]
                    .strip()
                    .lower()
                    .replace(" ", "_")
                    .replace("/", "_")
                    .replace("(", "")
                    .replace(")", "")
                )
                seg_clean = (
                    (
                        "_"
                        + segmento_final.split("–")[-1]
                        .strip()
                        .lower()
                        .replace(" ", "_")
                        .replace("/", "_")
                    )
                    if segmento_final
                    else ""
                )
                nome_arquivo = f"relatorio_b3_{setor_clean}{seg_clean}.md"

                st.download_button(
                    label="📥 Baixar Relatório (.md)",
                    data=resultado_str,
                    file_name=nome_arquivo,
                    mime="text/markdown",
                    use_container_width=True,
                )

# ---------------------------------------------------------------
# Rodapé com disclaimer legal obrigatório
# ---------------------------------------------------------------
st.markdown(
    "<div class='footer'>"
    "⚠️ <strong>Aviso Legal:</strong> Este relatório é gerado por Inteligência Artificial "
    "e <strong>não constitui recomendação de investimento</strong>. "
    "As informações são baseadas em dados públicos e heurísticas automatizadas. "
    "Consulte sempre um profissional certificado (CFP® ou CNPI) antes de tomar "
    "decisões financeiras. Rentabilidade passada não garante rentabilidade futura."
    "</div>",
    unsafe_allow_html=True,
)
