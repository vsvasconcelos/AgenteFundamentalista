# -*- coding: utf-8 -*-
"""
Módulo de Configuração e Credenciais (config.py)
Responsável por:
  - Obter credenciais do Google Cloud Vertex AI via Application Default Credentials (ADC)
  - Inicializar o LLM via Vertex AI (endpoint compatível com OpenAI, modelo google/gemini-3-flash-preview)
  - Definir o dicionário de Setores e Segmentos da B3 conforme especificação
"""

import os
import google.auth
from google.auth.transport.requests import Request
import httpx
import openai
from langchain_openai import ChatOpenAI


class GoogleAuth(httpx.Auth):
    """
    Injeta o token de autenticação OAuth2 do Google Cloud nos headers de cada requisição
    HTTP síncrona, renovando automaticamente caso o token esteja expirado ou próximo de expirar.
    """
    def __init__(self, creds):
        self.creds = creds

    def auth_flow(self, request):
        if not self.creds.valid:
            self.creds.refresh(Request())
        request.headers["Authorization"] = f"Bearer {self.creds.token}"
        yield request


class AsyncGoogleAuth(httpx.Auth):
    """
    Injeta o token OAuth2 do Google Cloud nos headers para requisições assíncronas.
    """
    def __init__(self, creds):
        self.creds = creds

    async def async_auth_flow(self, request):
        if not self.creds.valid:
            self.creds.refresh(Request())
        request.headers["Authorization"] = f"Bearer {self.creds.token}"
        yield request


DEFAULT_GCP_PROJECT_ID = "genai-vsv"


def carregar_credenciais_gcp():
    """
    Obtém as credenciais do Google Cloud e o ID do projeto através de:
      1. Variável de ambiente GCP_PROJECT_ID (se definida)
      2. Application Default Credentials (ADC) do gcloud ou GOOGLE_APPLICATION_CREDENTIALS
      3. Projeto padrão configurado (DEFAULT_GCP_PROJECT_ID = "genai-vsv")

    Returns:
        tuple: (creds, project_id)
    """
    creds, detected_project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )
    if not creds.valid:
        creds.refresh(Request())

    project_id = os.getenv("GCP_PROJECT_ID") or detected_project or DEFAULT_GCP_PROJECT_ID
    if not project_id:
        raise ValueError(
            "Não foi possível determinar o GCP Project ID. "
            "Defina a variável de ambiente GCP_PROJECT_ID ou execute: "
            "`gcloud auth application-default login`"
        )

    return creds, project_id


def carregar_chaves(caminho_arquivo="keys.txt"):
    """
    Carrega as credenciais para execução. Retorna (serper_api_key, project_id).
    Lê a SERPER_API_KEY se keys.txt existir, mas não falha se ausente.
    Determina o project_id via ADC do Google Cloud.

    Returns:
        tuple(str, str): (serper_api_key, project_id)
    """
    serper_api_key = ""
    caminhos_busca = [
        caminho_arquivo,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), caminho_arquivo),
    ]

    for caminho in caminhos_busca:
        if os.path.exists(caminho):
            try:
                with open(caminho, "r", encoding="utf-8") as f:
                    linhas = [l.strip() for l in f.readlines() if l.strip()]
                    if linhas:
                        serper_api_key = linhas[0]
            except Exception:
                pass
            break

    _, project_id = carregar_credenciais_gcp()
    return serper_api_key, project_id


def inicializar_llm(project_id=None, location=None, model_name=None):
    """
    Inicializa o LLM via Vertex AI utilizando o endpoint compatível com OpenAI.
    O consumo é cobrado diretamente no projeto GCP e consome créditos do Vertex AI.

    Args:
        project_id (str, opcional): ID do projeto GCP. Se None, detecta via ADC.
        location (str, opcional): Região do Vertex AI (padrão: "global" ou via GCP_LOCATION).
        model_name (str, opcional): Modelo Gemini do Vertex AI (padrão: "google/gemini-3-flash-preview").

    Returns:
        ChatOpenAI: Instância do LLM pronta para uso nos agentes.
    """
    creds, detected_project = carregar_credenciais_gcp()
    proj = project_id or detected_project
    loc = location or os.getenv("GCP_LOCATION", "global")
    model = model_name or os.getenv("VERTEX_MODEL", "google/gemini-3-flash-preview")

    if loc == "global":
        base_url = f"https://aiplatform.googleapis.com/v1beta1/projects/{proj}/locations/global/endpoints/openapi"
    else:
        base_url = f"https://{loc}-aiplatform.googleapis.com/v1beta1/projects/{proj}/locations/{loc}/endpoints/openapi"

    # Clientes HTTP com renovação de token OAuth2 e timeout adequado
    sync_http = httpx.Client(auth=GoogleAuth(creds), timeout=120.0)
    async_http = httpx.AsyncClient(auth=AsyncGoogleAuth(creds), timeout=120.0)

    sync_client = openai.OpenAI(base_url=base_url, api_key="dummy-vertex", http_client=sync_http)
    async_client = openai.AsyncOpenAI(base_url=base_url, api_key="dummy-vertex", http_client=async_http)

    llm = ChatOpenAI(
        model_name=model,
        openai_api_key="dummy-vertex",
        openai_api_base=base_url,
        client=sync_client.chat.completions,
        async_client=async_client.chat.completions,
        max_tokens=12000,
        temperature=0.1,
    )
    return llm


# -----------------------------------------------------------------------
# Dicionário de Setores da B3 (código numérico - nome do setor)
# Usado pelo selectbox principal da interface Streamlit.
# Chave: "Código – Nome" | Valor: lista de segmentos disponíveis (strings)
# -----------------------------------------------------------------------
SETORES_B3 = {
    "01 – Agropecuária":                                    [],
    "02 – Água e Saneamento":                               [],
    "03 – Alimentos":                                       [],
    "04 – Bebidas":                                         [],
    "05 – Automóveis e Motocicletas / Autopeças":           [],
    "06 – Bancos":                                          [],
    "07 – Comércio (Geral, Varejo e Atacado)":              [],
    "08 – Construção Civil e Engenharia":                   [],
    "09 – Construção e Engenharia / Outros":                [],
    "10 – Diversos (Holding e Multissetoriais)":            [],
    "11 – Embalagens":                                      [],
    "12 – Educação / Aluguer de Carros":                    [],
    "13 – Equipamentos (Eletroeletrônicos e Industriais)":  [],
    "14 – Energia Elétrica":                                [],
    "15 – Exploração de Bens / Imóveis":                    [],
    "16 – Centros Comerciais (Shopping Centers)":           [],
    "17 – Financeiros Diversos":                            [],
    "18 – Fios e Tecidos / Vestuário":                      [],
    "19 – Gás e Distribuição de Combustíveis":              [],
    "20 – Holdings Diversificadas":                         [],
    "21 – Hotelaria e Lazer":                               [],
    "22 – Material de Transporte / Material Aeronáutico":   [],
    "23 – Madeira e Papel":                                 [],
    "24 – Máquinas e Equipamentos":                         [],
    "25 – Medicamentos e Produtos Médicos":                 [],
    "26 – Mídia (Comunicação e Entretenimento)":            [],
    "27 – Mineração":                                       [],
    "28 – Outros":                                          [],
    "29 – Outros Títulos":                                  [],
    "30 – Petróleo, Gás e Biocombustíveis":                 [],
    "31 – Previdência e Seguros":                           [],
    "32 – Produtos de Uso Pessoal e de Limpeza":            [],
    "33 – Programas e Serviços / TI":                       [],
    "34 – Químicos":                                        [],
    "35 – Securitizadoras de Recebíveis":                   [],
    "36 – Serviços Médicos, Hospitalares e Diagnósticos":   [],
    "37 – Serviços Diversos":                               [],
    "38 – Siderurgia e Metalurgia":                         [],
    "39 – Tecidos, Vestuário e Calçados":                   [],
    "40 – Telecomunicações":                                [],
    "41 – Transporte (Logística e Concessionárias)":        [],
    "42 – Utilidades Domésticas":                           [],
}


# -----------------------------------------------------------------------
# Dicionário de Segmentos por Grupo de Setor da B3
# Agrupa os segmentos (subsetores) com seus códigos numéricos.
# Chave: nome do grupo de setores | Valor: lista de segmentos com código
# -----------------------------------------------------------------------
SEGMENTOS_POR_GRUPO = {
    "Agro, Alimentos e Bebidas": [
        "01 ou 53 – Açúcar e Álcool / Agricultura",
        "03 – Alimentos Diversos",
        "04 – Bebidas",
        "54 – Carnes e Derivados / Frigoríficos",
    ],
    "Financeiro e Seguros": [
        "06 – Bancos",
        "17 – Serviços Financeiros Diversos",
        "20 – Holdings Diversificadas",
        "31 – Seguradoras e Corretoras",
        "35 – Securitizadoras de Recebíveis",
    ],
    "Energia, Água e Saneamento (Utilidade Pública)": [
        "02 – Água e Saneamento",
        "14 – Energia Elétrica (Integradas)",
        "70 – Geração de Energia Elétrica",
        "71 – Transmissão de Energia Elétrica",
        "72 – Distribuição de Energia Elétrica",
        "19 – Gás",
    ],
    "Construção, Siderurgia e Materiais Básicos": [
        "08 – Incorporações / Construção Civil",
        "11 – Embalagens",
        "23 – Papel e Celulose",
        "27 – Mineração",
        "34 – Petroquímicos e Químicos",
        "38 – Siderurgia",
    ],
    "Comércio, Vestuário e Consumo (Varejo/Atacado)": [
        "07 – Comércio / Varejo Geral",
        "32 – Produtos de Uso Pessoal / Cosméticos",
        "39 – Tecidos, Vestuário e Calçados",
        "57 – Alimentos / Supermercados e Atacado",
        "62 – Medicamentos e Farmácias",
    ],
    "Saúde, Educação e Serviços": [
        "12 – Educação",
        "36 – Serviços Médicos, Hospitalares e Análises",
        "77 – Planos de Saúde e Seguros-Saúde",
    ],
    "Logística, Transporte e Petróleo": [
        "30 – Exploração, Refino e Distribuição de Petróleo",
        "41 – Transporte / Logística",
        "82 – Concessionárias de Rodovias",
        "83 – Transporte Aéreo",
        "85 – Aluguel de Carros e Gestão de Frotas",
    ],
    "Tecnologia e Telecomunicações": [
        "33 – Programas e Serviços de TI",
        "40 – Telecomunicações",
    ],
}


# -----------------------------------------------------------------------
# Mapeamento explícito: Setor da B3 → Grupo de Segmentos
# Permite ao app.py descobrir rapidamente qual grupo de segmentos
# exibir no selectbox dinâmico ao selecionar um setor.
# Setores sem segmentos mapeados apontam para None.
# -----------------------------------------------------------------------
MAPA_SETOR_PARA_GRUPO = {
    # Agro, Alimentos e Bebidas
    "01 – Agropecuária":                                    "Agro, Alimentos e Bebidas",
    "03 – Alimentos":                                       "Agro, Alimentos e Bebidas",
    "04 – Bebidas":                                         "Agro, Alimentos e Bebidas",

    # Financeiro e Seguros
    "06 – Bancos":                                          "Financeiro e Seguros",
    "17 – Financeiros Diversos":                            "Financeiro e Seguros",
    "20 – Holdings Diversificadas":                         "Financeiro e Seguros",
    "31 – Previdência e Seguros":                           "Financeiro e Seguros",
    "35 – Securitizadoras de Recebíveis":                   "Financeiro e Seguros",

    # Energia, Água e Saneamento
    "02 – Água e Saneamento":                               "Energia, Água e Saneamento (Utilidade Pública)",
    "14 – Energia Elétrica":                                "Energia, Água e Saneamento (Utilidade Pública)",
    "19 – Gás e Distribuição de Combustíveis":              "Energia, Água e Saneamento (Utilidade Pública)",

    # Construção, Siderurgia e Materiais Básicos
    "08 – Construção Civil e Engenharia":                   "Construção, Siderurgia e Materiais Básicos",
    "09 – Construção e Engenharia / Outros":                "Construção, Siderurgia e Materiais Básicos",
    "11 – Embalagens":                                      "Construção, Siderurgia e Materiais Básicos",
    "23 – Madeira e Papel":                                 "Construção, Siderurgia e Materiais Básicos",
    "27 – Mineração":                                       "Construção, Siderurgia e Materiais Básicos",
    "34 – Químicos":                                        "Construção, Siderurgia e Materiais Básicos",
    "38 – Siderurgia e Metalurgia":                         "Construção, Siderurgia e Materiais Básicos",

    # Comércio, Vestuário e Consumo
    "07 – Comércio (Geral, Varejo e Atacado)":              "Comércio, Vestuário e Consumo (Varejo/Atacado)",
    "32 – Produtos de Uso Pessoal e de Limpeza":            "Comércio, Vestuário e Consumo (Varejo/Atacado)",
    "39 – Tecidos, Vestuário e Calçados":                   "Comércio, Vestuário e Consumo (Varejo/Atacado)",
    "25 – Medicamentos e Produtos Médicos":                 "Comércio, Vestuário e Consumo (Varejo/Atacado)",

    # Saúde, Educação e Serviços
    "12 – Educação / Aluguer de Carros":                    "Saúde, Educação e Serviços",
    "36 – Serviços Médicos, Hospitalares e Diagnósticos":   "Saúde, Educação e Serviços",

    # Logística, Transporte e Petróleo
    "30 – Petróleo, Gás e Biocombustíveis":                 "Logística, Transporte e Petróleo",
    "41 – Transporte (Logística e Concessionárias)":        "Logística, Transporte e Petróleo",

    # Tecnologia e Telecomunicações
    "33 – Programas e Serviços / TI":                       "Tecnologia e Telecomunicações",
    "40 – Telecomunicações":                                "Tecnologia e Telecomunicações",
}


def extrair_codigo(label: str) -> str:
    """
    Extrai o(s) código(s) numérico(s) de uma string no formato
    'XX – Nome do Setor/Segmento'. Retorna apenas o número ou
    o primeiro número em caso de múltiplos (ex: '01 ou 53' → '01').

    Args:
        label (str): String de setor ou segmento com código prefixado.

    Returns:
        str: Código numérico extraído.
    """
    parte = label.split("–")[0].strip()
    # Trata formatos como "01 ou 53"
    return parte.split(" ou ")[0].strip().split(" ")[0].strip()
