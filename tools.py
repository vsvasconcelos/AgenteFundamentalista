# -*- coding: utf-8 -*-
"""
Módulo de Ferramentas Customizadas (tools.py)
Define 3 ferramentas especializadas para a equipe de equity research B3:
  1. FundamentusScreenerTool  — triagem quantitativa via fundamentus.com.br
  2. AuditorHistoricoTool     — consistência histórica do ROE
  3. InvestigadorGovernancaTool — governança corporativa e risco estatal

As URLs de acesso ao Fundamentus seguem o padrão:
  - Por setor:    https://fundamentus.com.br/resultado.php?setor=<código>
  - Por segmento: https://fundamentus.com.br/resultado.php?segmento=<código>
onde os códigos são os definidos na especificação de arquitetura.
"""

import io
import re
import warnings
from typing import ClassVar
import pandas as pd
import requests
import requests_cache
import fundamentus as fund
from langchain.tools import BaseTool


# -----------------------------------------------------------------------
# Cache e utilitários para obtenção e formatação do nome das empresas B3
# -----------------------------------------------------------------------
_CACHE_NOMES_EMPRESAS: dict[str, str] = {}

# Nomes canônicos com acentuação impecável para empresas frequentes da B3
_NOMES_CANONICOS_B3: dict[str, str] = {
    "SLCE3": "SLC Agrícola S.A.",
    "AGRO3": "BrasilAgro S.A.",
    "TTEN3": "3tentos Agroindustrial S.A.",
    "SMTO3": "São Martinho S.A.",
    "JALL3": "Jalles Machado S.A.",
    "SBSP3": "Sabesp S.A.",
    "CSMG3": "Copasa S.A.",
    "SAPR4": "Sanepar S.A.",
    "SAPR11": "Sanepar S.A.",
    "MDIA3": "M. Dias Branco S.A.",
    "BEEF3": "Minerva S.A.",
    "JBSS3": "JBS S.A.",
    "MRFG3": "Marfrig Global Foods S.A.",
    "BRFS3": "BRF S.A.",
    "CAML3": "Camil Alimentos S.A.",
    "ABEV3": "Ambev S.A.",
    "ITUB4": "Itaú Unibanco Holding S.A.",
    "ITUB3": "Itaú Unibanco Holding S.A.",
    "BBDC4": "Banco Bradesco S.A.",
    "BBDC3": "Banco Bradesco S.A.",
    "BBAS3": "Banco do Brasil S.A.",
    "SANB11": "Banco Santander (Brasil) S.A.",
    "BPAC11": "Banco BTG Pactual S.A.",
    "BRSR6": "Banrisul S.A.",
    "ABCB4": "Banco ABC Brasil S.A.",
    "PETR4": "Petróleo Brasileiro S.A. - Petrobras",
    "PETR3": "Petróleo Brasileiro S.A. - Petrobras",
    "PRIO3": "PRIO S.A.",
    "RECV3": "PetroReconcavo S.A.",
    "VBBR3": "Vibra Energia S.A.",
    "UGPA3": "Ultrapar Participações S.A.",
    "VALE3": "Vale S.A.",
    "CMIN3": "CSN Mineração S.A.",
    "CBAV3": "Companhia Brasileira de Alumínio S.A.",
    "WEGE3": "WEG S.A.",
    "ELET3": "Eletrobras S.A.",
    "ELET6": "Eletrobras S.A.",
    "EGIE3": "Engie Brasil Energia S.A.",
    "CPFE3": "CPFL Energia S.A.",
    "TAEE11": "Taesa S.A.",
    "CMIG4": "Cemig S.A.",
    "EQTL3": "Equatorial Energia S.A.",
    "CPLE6": "Copel S.A.",
    "TRPL4": "ISA CTEEP S.A.",
    "ITSA4": "Itaúsa S.A.",
    "BBSE3": "BB Seguridade Participações S.A.",
    "CXSE3": "Caixa Seguridade Participações S.A.",
    "PSSA3": "Porto Seguro S.A.",
    "IRBR3": "IRB-Brasil Resseguros S.A.",
    "B3SA3": "B3 S.A. - Brasil, Bolsa, Balcão",
    "SUZB3": "Suzano S.A.",
    "KLBN11": "Klabin S.A.",
    "GGBR4": "Gerdau S.A.",
    "CSNA3": "Companhia Siderúrgica Nacional S.A.",
    "USIM5": "Usiminas S.A.",
    "RADL3": "Raia Drogasil S.A.",
    "HAPV3": "Hapvida Participações e Investimentos S.A.",
    "RDOR3": "Rede D'Or São Luiz S.A.",
    "FLRY3": "Fleury S.A.",
    "RENT3": "Localiza Rent a Car S.A.",
    "MOVI3": "Movida Participações S.A.",
    "LREN3": "Lojas Renner S.A.",
    "MGLU3": "Magazine Luiza S.A.",
    "ASAI3": "Sendas Distribuidora S.A. (Assaí)",
    "CRFB3": "Atacadão S.A. (Carrefour Brasil)",
    "TOTS3": "TOTVS S.A.",
    "VIVT3": "Telefônica Brasil S.A.",
    "TIMS3": "TIM S.A.",
    "EMBR3": "Embraer S.A.",
    "RAIL3": "Rumo S.A.",
    "CCRO3": "CCR S.A.",
    "ECOR3": "EcoRodovias Infraestrutura e Logística S.A.",
    "CYRE3": "Cyrela Brazil Realty S.A.",
    "EZTC3": "EZTEC Empreendimentos e Participações S.A.",
    "MRVE3": "MRV Engenharia e Participações S.A.",
    "MULT3": "Multiplan Empreendimentos Imobiliários S.A.",
    "ALOS3": "Allos S.A.",
}

_SIGLAS_MAIUSCULAS = {
    "SLC", "WEG", "BTG", "B3", "BB", "BR", "BRF", "JBS", "MRV", "CSN", "CCR",
    "CBA", "IRB", "CVC", "BMG", "ABC", "AES", "CPFL", "CTEEP", "ISA", "TIM",
    "RNI", "PRIO", "TOTVS", "KLBN", "TAESA", "ENGIE", "EZTEC", "FLEURY",
}

_PREPOSICOES_MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "em", "para", "com", "por"}

_CORRECOES_ACENTUACAO = {
    "Agricola": "Agrícola",
    "Agricolas": "Agrícolas",
    "Itau": "Itaú",
    "Petroleo": "Petróleo",
    "Eletrobras": "Eletrobrás",
    "Siderurgica": "Siderúrgica",
    "Participacoes": "Participações",
    "Mineracao": "Mineração",
    "Transmissao": "Transmissão",
    "Geracao": "Geração",
    "Distribuicao": "Distribuição",
    "Servicos": "Serviços",
    "Diagnosticos": "Diagnósticos",
    "Logistica": "Logística",
    "Construcoes": "Construções",
    "Comercio": "Comércio",
    "Industria": "Indústria",
    "Acucar": "Açúcar",
    "Alcool": "Álcool",
    "Saude": "Saúde",
    "Educacao": "Educação",
    "Imobiliarios": "Imobiliários",
    "Imobiliario": "Imobiliário",
    "Eletrica": "Elétrica",
}


def _formatar_razao_social(nome_raw: str) -> str:
    """
    Formata a razão social ou nome comercial retornado pelo Fundamentus
    para um padrão corporativo limpo (ex: 'SLC AGRICOLA SA' -> 'SLC Agrícola S.A.').
    """
    if not nome_raw:
        return ""
    nome = str(nome_raw).strip()
    nome = re.sub(r"\s+(ON|PN|PNA|PNB|UNT)\b(\s+(NM|N1|N2|MA|MB))?$", "", nome, flags=re.IGNORECASE).strip()
    nome = re.sub(r"\s+(S/A|S\.A\.?|SA)\.?$", " S.A.", nome, flags=re.IGNORECASE)

    palavras = nome.split()
    formatadas = []
    for i, p in enumerate(palavras):
        p_upper = p.upper().rstrip(".,")
        if p.upper() in ("S.A.", "S/A", "S.A", "SA"):
            formatadas.append("S.A.")
        elif p.upper() in ("LTDA", "LTDA."):
            formatadas.append("Ltda.")
        elif p_upper in _SIGLAS_MAIUSCULAS:
            formatadas.append(p.upper())
        elif i > 0 and p.lower() in _PREPOSICOES_MINUSCULAS:
            formatadas.append(p.lower())
        else:
            palavra_cap = p.capitalize()
            palavra_cap = _CORRECOES_ACENTUACAO.get(palavra_cap, palavra_cap)
            formatadas.append(palavra_cap)

    resultado = " ".join(formatadas)
    if not resultado.endswith("S.A.") and not resultado.endswith("Ltda.") and not resultado.endswith("Ltd."):
        resultado = f"{resultado} S.A."
    return resultado


def _carregar_tabela_nomes_fundamentus() -> None:
    """
    Carrega e faz cache em memória do mapeamento Papel -> Nome da Empresa
    a partir da página detalhes.php do Fundamentus.
    """
    if _CACHE_NOMES_EMPRESAS:
        return
    _CACHE_NOMES_EMPRESAS.update(_NOMES_CANONICOS_B3)
    try:
        url = "http://fundamentus.com.br/detalhes.php?papel="
        hdr = {
            "User-agent": "Mozilla/5.0 (Windows; U; Windows NT 6.1; rv:2.2) Gecko/20110201",
            "Accept": "text/html, text/plain, text/css, text/sgml, */*;q=0.01",
        }
        with requests_cache.enabled():
            content = requests.get(url, headers=hdr, timeout=15)
        df = pd.read_html(io.StringIO(content.text), decimal=",", thousands=".")[0]
        for _, row in df.iterrows():
            papel = str(row.get("Papel", "")).strip().upper()
            if not papel or papel in _CACHE_NOMES_EMPRESAS:
                continue
            razao = str(row.get("Razão Social", "")).strip()
            comercial = str(row.get("Nome Comercial", "")).strip()
            base = razao if razao and razao.lower() != "nan" else comercial
            if base and base.lower() != "nan":
                _CACHE_NOMES_EMPRESAS[papel] = _formatar_razao_social(base)
    except Exception:
        pass


def obter_nome_empresa(ticker: str) -> str:
    """
    Retorna o nome da empresa associado ao ticker da B3
    (ex: 'SLCE3' -> 'SLC Agrícola S.A.').
    """
    codigo = re.sub(r"[^A-Z0-9]", "", str(ticker).upper().split("(")[0].strip())
    if not codigo:
        return ""
    _carregar_tabela_nomes_fundamentus()
    if codigo in _CACHE_NOMES_EMPRESAS:
        return _CACHE_NOMES_EMPRESAS[codigo]
    try:
        df = fund.get_detalhes_papel(codigo)
        if df is not None and not df.empty and "Empresa" in df.columns:
            emp = _formatar_razao_social(str(df["Empresa"].iloc[0]))
            if emp:
                _CACHE_NOMES_EMPRESAS[codigo] = emp
                return emp
    except Exception:
        pass
    return ""


def formatar_ticker_com_empresa(ticker: str) -> str:
    """
    Formata o ticker acompanhado do nome da empresa entre parênteses.
    Exemplo: 'SLCE3' -> 'SLCE3 (SLC Agrícola S.A.)'
    """
    codigo = re.sub(r"[^A-Z0-9]", "", str(ticker).upper().split("(")[0].strip())
    nome = obter_nome_empresa(codigo)
    return f"{codigo} ({nome})" if nome else codigo


def enriquecer_primeira_ocorrencia_tickers(texto: str) -> str:
    """
    Garante que no texto/relatório a 1ª ocorrência de cada ticker da B3
    esteja acompanhada do nome da empresa no formato 'TICKER (Nome da Empresa)',
    ex: 'SLCE3 (SLC Agrícola S.A.)'.
    """
    if not texto:
        return texto

    padrao_ticker = re.compile(r"\b([A-Z]{4}(?:3|4|5|6|11|33|34))\b")
    tickers_vistos: set[str] = set()
    tickers_ordem: list[str] = []
    for match in padrao_ticker.finditer(texto):
        tk = match.group(1)
        if tk not in tickers_vistos:
            tickers_vistos.add(tk)
            tickers_ordem.append(tk)

    texto_enriquecido = texto
    for tk in tickers_ordem:
        nome = obter_nome_empresa(tk)
        if not nome:
            continue
        m = re.search(rf"\b{re.escape(tk)}\b", texto_enriquecido)
        if not m:
            continue
        pos_fim = m.end()
        sufixo = texto_enriquecido[pos_fim : pos_fim + 80]
        if re.match(r"^(\*\*)?\s*\(", sufixo):
            continue
        texto_enriquecido = (
            texto_enriquecido[: m.start()]
            + f"{tk} ({nome})"
            + texto_enriquecido[pos_fim:]
        )

    return texto_enriquecido


def extrair_tickers_com_empresas(texto: str) -> list[str]:
    """
    Extrai os tickers da B3 presentes em um texto na ordem da 1ª aparição,
    retornando cada um formatado como 'TICKER (Nome da Empresa)'.
    """
    if not texto:
        return []
    padrao_ticker = re.compile(r"\b([A-Z]{4}(?:3|4|5|6|11|33|34))\b")
    vistos: set[str] = set()
    resultado: list[str] = []
    for m in padrao_ticker.finditer(texto):
        tk = m.group(1)
        if tk not in vistos:
            vistos.add(tk)
            resultado.append(formatar_ticker_com_empresa(tk))
    return resultado



# -----------------------------------------------------------------------
# Mapeamento: label da spec → código numérico do Fundamentus
# Usado para converter a seleção do usuário em parâmetro de API.
# -----------------------------------------------------------------------
MAPA_SETOR_CODIGO = {
    # Setores (código único)
    "01 – Agropecuária":                                    ("setor", "01"),
    "02 – Água e Saneamento":                               ("setor", "02"),
    "03 – Alimentos":                                       ("setor", "03"),
    "04 – Bebidas":                                         ("setor", "04"),
    "05 – Automóveis e Motocicletas / Autopeças":           ("setor", "05"),
    "06 – Bancos":                                          ("setor", "06"),
    "07 – Comércio (Geral, Varejo e Atacado)":              ("setor", "07"),
    "08 – Construção Civil e Engenharia":                   ("setor", "08"),
    "09 – Construção e Engenharia / Outros":                ("setor", "09"),
    "10 – Diversos (Holding e Multissetoriais)":            ("setor", "10"),
    "11 – Embalagens":                                      ("setor", "11"),
    "12 – Educação / Aluguer de Carros":                    ("setor", "12"),
    "13 – Equipamentos (Eletroeletrônicos e Industriais)":  ("setor", "13"),
    "14 – Energia Elétrica":                                ("setor", "14"),
    "15 – Exploração de Bens / Imóveis":                    ("setor", "15"),
    "16 – Centros Comerciais (Shopping Centers)":           ("setor", "16"),
    "17 – Financeiros Diversos":                            ("setor", "17"),
    "18 – Fios e Tecidos / Vestuário":                      ("setor", "18"),
    "19 – Gás e Distribuição de Combustíveis":              ("setor", "19"),
    "20 – Holdings Diversificadas":                         ("setor", "20"),
    "21 – Hotelaria e Lazer":                               ("setor", "21"),
    "22 – Material de Transporte / Material Aeronáutico":   ("setor", "22"),
    "23 – Madeira e Papel":                                 ("setor", "23"),
    "24 – Máquinas e Equipamentos":                         ("setor", "24"),
    "25 – Medicamentos e Produtos Médicos":                 ("setor", "25"),
    "26 – Mídia (Comunicação e Entretenimento)":            ("setor", "26"),
    "27 – Mineração":                                       ("setor", "27"),
    "28 – Outros":                                          ("setor", "28"),
    "29 – Outros Títulos":                                  ("setor", "29"),
    "30 – Petróleo, Gás e Biocombustíveis":                 ("setor", "30"),
    "31 – Previdência e Seguros":                           ("setor", "31"),
    "32 – Produtos de Uso Pessoal e de Limpeza":            ("setor", "32"),
    "33 – Programas e Serviços / TI":                       ("setor", "33"),
    "34 – Químicos":                                        ("setor", "34"),
    "35 – Securitizadoras de Recebíveis":                   ("setor", "35"),
    "36 – Serviços Médicos, Hospitalares e Diagnósticos":   ("setor", "36"),
    "37 – Serviços Diversos":                               ("setor", "37"),
    "38 – Siderurgia e Metalurgia":                         ("setor", "38"),
    "39 – Tecidos, Vestuário e Calçados":                   ("setor", "39"),
    "40 – Telecomunicações":                                ("setor", "40"),
    "41 – Transporte (Logística e Concessionárias)":        ("setor", "41"),
    "42 – Utilidades Domésticas":                           ("setor", "42"),

    # Segmentos (código numérico para ?segmento=)
    "01 ou 53 – Açúcar e Álcool / Agricultura":             ("segmento", "01"),
    "03 – Alimentos Diversos":                              ("segmento", "03"),
    "04 – Bebidas":                                         ("segmento", "04"),
    "54 – Carnes e Derivados / Frigoríficos":               ("segmento", "54"),
    "17 – Serviços Financeiros Diversos":                   ("segmento", "17"),
    "31 – Seguradoras e Corretoras":                        ("segmento", "31"),
    "35 – Securitizadoras de Recebíveis":                   ("segmento", "35"),
    "14 – Energia Elétrica (Integradas)":                   ("segmento", "14"),
    "70 – Geração de Energia Elétrica":                     ("segmento", "70"),
    "71 – Transmissão de Energia Elétrica":                 ("segmento", "71"),
    "72 – Distribuição de Energia Elétrica":                ("segmento", "72"),
    "19 – Gás":                                             ("segmento", "19"),
    "08 – Incorporações / Construção Civil":                ("segmento", "08"),
    "11 – Embalagens":                                      ("segmento", "11"),
    "23 – Papel e Celulose":                                ("segmento", "23"),
    "34 – Petroquímicos e Químicos":                        ("segmento", "34"),
    "38 – Siderurgia":                                      ("segmento", "38"),
    "07 – Comércio / Varejo Geral":                         ("segmento", "07"),
    "32 – Produtos de Uso Pessoal / Cosméticos":            ("segmento", "32"),
    "57 – Alimentos / Supermercados e Atacado":             ("segmento", "57"),
    "62 – Medicamentos e Farmácias":                        ("segmento", "62"),
    "36 – Serviços Médicos, Hospitalares e Análises":       ("segmento", "36"),
    "77 – Planos de Saúde e Seguros-Saúde":                 ("segmento", "77"),
    "30 – Exploração, Refino e Distribuição de Petróleo":   ("segmento", "30"),
    "82 – Concessionárias de Rodovias":                     ("segmento", "82"),
    "83 – Transporte Aéreo":                                ("segmento", "83"),
    "85 – Aluguel de Carros e Gestão de Frotas":            ("segmento", "85"),
    "33 – Programas e Serviços de TI":                      ("segmento", "33"),
}

# Mapeamento de código inteiro (usado pela lib fundamentus) por tipo
MAPA_CODIGO_SETOR_INT = {
    "01": 1,  "02": 2,  "03": 3,  "04": 4,  "05": 5,
    "06": 6,  "07": 7,  "08": 8,  "09": 9,  "10": 10,
    "11": 11, "12": 12, "13": 13, "14": 14, "15": 15,
    "16": 16, "17": 17, "18": 18, "19": 19, "20": 20,
    "21": 21, "22": 22, "23": 23, "24": 24, "25": 25,
    "26": 26, "27": 27, "28": 28, "29": 29, "30": 30,
    "31": 31, "32": 32, "33": 33, "34": 34, "35": 35,
    "36": 36, "37": 37, "38": 38, "39": 39, "40": 40,
    "41": 41, "42": 42,
    # Segmentos extras
    "53": 53, "54": 54, "57": 57, "62": 62, "70": 70,
    "71": 71, "72": 72, "77": 77, "82": 82, "83": 83, "85": 85,
}


def _resolver_parametro(label: str) -> tuple:
    """
    Resolve o label da interface para (tipo, codigo_int).
    tipo pode ser 'setor' ou 'segmento'.

    Args:
        label (str): Label exato vindo do selectbox (setor ou segmento).

    Returns:
        tuple: (tipo: str, codigo: int) ou (None, None) se não mapeado.
    """
    entrada = MAPA_SETOR_CODIGO.get(label)
    if not entrada:
        # Tenta resolver pelo nome sem código (fallback robusto)
        for chave, val in MAPA_SETOR_CODIGO.items():
            if label.lower() in chave.lower():
                entrada = val
                break

    if not entrada:
        return None, None

    tipo, codigo_str = entrada
    codigo_int = MAPA_CODIGO_SETOR_INT.get(codigo_str)
    return tipo, codigo_int


def _coletar_tickers(tipo: str, codigo: int) -> list:
    """
    Coleta os tickers do Fundamentus para um dado código de setor ou segmento.

    Args:
        tipo (str): 'setor' ou 'segmento'
        codigo (int): Código numérico da B3

    Returns:
        list[str]: Lista de tickers encontrados.
    """
    try:
        if tipo == "setor":
            return list(set(fund.list_papel_setor(setor=codigo)))
        else:
            # segmento
            return list(set(fund.list_papel_segmento(segmento=codigo)))
    except Exception:
        return []


def triar_acoes(setor_label: str, segmento_label: str = "", top_n: int = 5) -> str:
    """
    Executa a triagem fundamentalista real no Fundamentus.com.br.

    Algoritmo (conforme spec):
      1. Descarta empresas com P/L <= 0
      2. Ordena por ROE decrescente
      3. Cruza e pondera com Dividend Yield (score = ROE*0.7 + DY*0.3)
      4. Retorna os Top N tickers

    Args:
        setor_label (str): Label do setor selecionado na interface.
        segmento_label (str): Label do segmento selecionado (opcional).
        top_n (int): Número de empresas no ranking final.

    Returns:
        str: Relatório de triagem em formato tabular.
    """
    warnings.filterwarnings("ignore")

    # Determina qual label usar: segmento tem prioridade sobre setor
    label_ativo = segmento_label if segmento_label else setor_label
    tipo, codigo = _resolver_parametro(label_ativo)

    # Se o segmento não foi mapeado, cai para o setor
    if tipo is None and segmento_label:
        tipo, codigo = _resolver_parametro(setor_label)
        label_ativo = setor_label

    if tipo is None:
        return (
            f"Setor/segmento '{label_ativo}' não mapeado no dicionário do Fundamentus. "
            "Verifique a seleção e tente novamente."
        )

    # Coleta tickers do setor/segmento escolhido
    tickers = _coletar_tickers(tipo, codigo)
    if not tickers:
        return (
            f"Nenhum ticker encontrado para '{label_ativo}' "
            f"(tipo={tipo}, código={codigo}) no Fundamentus."
        )

    # Obtém todos os dados fundamentalistas do mercado
    try:
        df_all = fund.get_resultado_raw()
    except Exception as e:
        return f"Erro ao acessar o Fundamentus: {e}"

    # Filtra apenas os tickers do setor/segmento escolhido
    df = df_all[df_all.index.isin(tickers)].copy()
    if df.empty:
        return (
            f"Nenhum dado encontrado no Fundamentus para os tickers de '{label_ativo}'. "
            "O mercado pode estar fechado ou o código do setor está desatualizado."
        )

    # ── Algoritmo de Triagem (conforme spec) ─────────────────────────
    # 1. Descarta P/L negativo ou zero
    df = df[df["P/L"] > 0].copy()
    if df.empty:
        return f"Após filtro P/L > 0, nenhuma empresa restou para '{label_ativo}'."

    # 2. Ordena por ROE decrescente
    df = df.sort_values("ROE", ascending=False)

    # 3. Cruza e pondera com Dividend Yield
    roe_max = df["ROE"].max() if df["ROE"].max() > 0 else 1
    dy_max  = df["Div.Yield"].max() if df["Div.Yield"].max() > 0 else 1
    df["score"] = (df["ROE"] / roe_max * 0.7) + (df["Div.Yield"] / dy_max * 0.3)
    df = df.sort_values("score", ascending=False)

    # 4. Seleciona Top N
    top = df.head(top_n)[["P/L", "ROE", "Div.Yield", "score"]].copy()
    top.columns = ["P/L", "ROE (%)", "DY (%)", "Score"]

    # Converte ROE e DY para percentual legível
    top["ROE (%)"] = (top["ROE (%)"] * 100).round(2)
    top["DY (%)"]  = (top["DY (%)"]  * 100).round(2)
    top["Score"]   = top["Score"].round(4)

    # Formata o índice para incluir o nome da empresa na 1ª aparição: Ex: SLCE3 (SLC Agrícola S.A.)
    top.index = [formatar_ticker_com_empresa(tk) for tk in top.index]
    top.index.name = "Ticker (Empresa)"

    n_analisadas = len(df_all[df_all.index.isin(tickers)])
    resultado = (
        f"=== TRIAGEM FUNDAMENTALISTA — {label_ativo.upper()} ===\n"
        f"URL Fundamentus: https://fundamentus.com.br/resultado.php?"
        f"{tipo}={codigo}\n"
        f"Empresas analisadas: {n_analisadas} | Após filtro P/L>0: {len(df)}\n\n"
        f"TOP {top_n} AÇÕES (ROE decrescente, ponderado por DY):\n\n"
        + top.to_string()
        + "\n\n"
        "Legenda: P/L = Preço/Lucro | ROE = Retorno sobre PL | "
        "DY = Dividend Yield | Score = índice combinado (ROE*0.7 + DY*0.3)"
    )
    return resultado


class FundamentusScreenerTool(BaseTool):
    """
    Ferramenta CrewAI que executa triagem fundamentalista real
    diretamente no Fundamentus.com.br via biblioteca Python.
    Algoritmo: P/L>0 → ordena ROE desc → pondera DY → Top 5.
    """
    name: str = "triagem_fundamentalista_b3"
    description: str = (
        "Executa triagem fundamentalista REAL de ações da B3 usando dados do Fundamentus.com.br. "
        "Input esperado: string no formato 'setor=<label_setor>' ou "
        "'setor=<label_setor>,segmento=<label_segmento>'. "
        "Os labels devem ser exatamente os exibidos na interface (ex: '06 – Bancos'). "
        "Retorna os Top 5 tickers com P/L, ROE e Dividend Yield."
    )

    def _run(self, query: str) -> str:
        """Executa a triagem a partir de uma string de query do agente."""
        setor, segmento = "", ""
        # Parseia o input do agente (ex: "setor=06 – Bancos,segmento=06 – Bancos")
        for parte in query.split(","):
            parte = parte.strip()
            if parte.lower().startswith("setor="):
                setor = parte.split("=", 1)[1].strip()
            elif parte.lower().startswith("segmento="):
                segmento = parte.split("=", 1)[1].strip()

        # Fallback: agente enviou o nome direto sem prefixo
        if not setor:
            setor = query.strip()

        return triar_acoes(setor_label=setor, segmento_label=segmento)

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("Modo assíncrono não suportado.")


class AuditorHistoricoTool(BaseTool):
    """
    Ferramenta para o Auditor Temporal avaliar a consistência histórica do ROE.
    Usa dados reais de Crescimento de Receita (5 anos) e ROE atual do Fundamentus
    para inferir a consistência de longo prazo de cada empresa.
    """
    name: str = "auditoria_historica_roe"
    description: str = (
        "Avalia a consistência histórica do ROE e crescimento de receita das empresas. "
        "Input esperado: lista de tickers separados por vírgula (ex: 'PETR4, VALE3, ITUB4'). "
        "Retorna a tendência histórica e aprovação de cada empresa para a próxima fase."
    )

    def _run(self, query: str) -> str:
        tickers = [
            re.sub(r"[^A-Z0-9]", "", t.split("(")[0].strip().upper())
            for t in query.split(",")
            if t.strip()
        ]
        tickers = [t for t in tickers if t]
        if not tickers:
            return "Nenhum ticker fornecido para auditoria."

        resultados = []
        for ticker in tickers:
            try:
                df = fund.get_detalhes_papel(ticker)
                if df is None or df.empty:
                    resultados.append(f"Ticker: {ticker} | Dado não encontrado no Fundamentus.")
                    continue

                roe_str  = str(df["ROE"].iloc[0]).replace("%", "").replace(",", ".")
                cresc_str = str(df["Cres_Rec_5a"].iloc[0]).replace("%", "").replace(",", ".")

                roe   = float(roe_str)  if roe_str  not in ("-", "nan", "") else 0.0
                cresc = float(cresc_str) if cresc_str not in ("-", "nan", "") else 0.0

                # Heurística de consistência histórica baseada em ROE e crescimento
                if roe > 10 and cresc > 5:
                    tendencia = "Crescente e Consistente"
                    aprovado  = "Sim"
                elif roe > 5 and cresc >= 0:
                    tendencia = "Estável"
                    aprovado  = "Sim"
                else:
                    tendencia = "Volátil / Decrescente"
                    aprovado  = "Não"

                ticker_fmt = formatar_ticker_com_empresa(ticker)
                resultados.append(
                    f"Ticker: {ticker_fmt} | ROE Atual: {roe:.1f}% | "
                    f"Cresc. Receita 5a: {cresc:.1f}% | "
                    f"Tendência: {tendencia} | Aprovado: {aprovado}"
                )
            except Exception as e:
                resultados.append(f"Ticker: {ticker} | Erro ao buscar dados: {e}")

        return "\n".join(resultados)

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("Modo assíncrono não suportado.")


class InvestigadorGovernancaTool(BaseTool):
    """
    Ferramenta para investigar Governança Corporativa e estrutura acionária.
    Analisa dados do Fundamentus para determinar nível de governança B3,
    estimativa de free float e exposição a risco estatal.
    Fontes: fundamentus.com.br (dados de papel e composição acionária).
    """
    name: str = "investigacao_governanca_b3"
    description: str = (
        "Investiga a governança corporativa, free float e risco estatal das empresas da B3. "
        "Input esperado: lista de tickers separados por vírgula (ex: 'PETR4, VALE3'). "
        "Retorna o percentual de Free Float estimado, nível de governança B3 e risco estatal."
    )

    # Lista de empresas com participação estatal relevante
    ESTATAIS: ClassVar[list[str]] = [
        "petrobras", "banco do brasil", "caixa", "eletrobras",
        "cemig", "copel", "sanepar", "sabesp", "banrisul",
        "eletrosul", "chesf", "furnas", "copasa", "transmissao paulista",
    ]

    def _run(self, query: str) -> str:
        tickers = [
            re.sub(r"[^A-Z0-9]", "", t.split("(")[0].strip().upper())
            for t in query.split(",")
            if t.strip()
        ]
        tickers = [t for t in tickers if t]
        if not tickers:
            return "Nenhum ticker fornecido para investigação de governança."

        resultados = []
        for ticker in tickers:
            try:
                df = fund.get_detalhes_papel(ticker)
                if df is None or df.empty:
                    resultados.append(
                        f"Ticker: {ticker} | Dado não encontrado no Fundamentus."
                    )
                    continue

                tipo    = str(df["Tipo"].iloc[0])
                empresa = str(df["Empresa"].iloc[0]).lower()

                # ── Nível de Governança B3 ────────────────────────────────────
                # ON (terminam em 3) geralmente listadas no Novo Mercado ou N2
                # PN (terminam em 4) geralmente em segmentos de menor governança
                # UNITs (terminam em 11) variam por empresa
                if ticker.endswith("3"):
                    nivel_gov      = "Novo Mercado / N2 (Alta Governança)"
                    free_float_est = "> 25% — Adequado para investimento"
                elif ticker.endswith("11"):
                    nivel_gov      = "BDR / Unit — verificar prospecto"
                    free_float_est = "Variável — verificar prospecto"
                else:
                    nivel_gov      = "Nível 1 / Tradicional (Governança Moderada)"
                    free_float_est = "< 25% — Atenção recomendada"

                # ── Risco Estatal ─────────────────────────────────────────────
                risco_estatal = (
                    "Sim — Alto Risco Político / Interferência Governamental"
                    if any(e in empresa for e in self.ESTATAIS)
                    else "Não — Empresa Privada (Baixo Risco Político)"
                )

                # ── Concentração Acionária ────────────────────────────────────
                # Heurística: empresas ON no NM têm dispersão maior
                conc_controle = (
                    "Alta dispersão acionária (Free Float elevado)"
                    if ticker.endswith("3")
                    else "Possível concentração de controle — verificar DFP"
                )

                ticker_fmt = formatar_ticker_com_empresa(ticker)
                resultados.append(
                    f"Ticker: {ticker_fmt} | Tipo: {tipo} | "
                    f"Nível Governança B3: {nivel_gov} | "
                    f"Free Float Estimado: {free_float_est} | "
                    f"Risco Estatal: {risco_estatal} | "
                    f"Estrutura de Controle: {conc_controle}"
                )
            except Exception as e:
                resultados.append(f"Ticker: {ticker} | Erro ao buscar dados: {e}")

        return "\n".join(resultados)

    async def _arun(self, query: str) -> str:
        raise NotImplementedError("Modo assíncrono não suportado.")
