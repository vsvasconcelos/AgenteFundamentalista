# -*- coding: utf-8 -*-
"""
Módulo de Configuração e Credenciais (config.py)
Responsável por:
  - Carregar as chaves de API dos arquivos keys.txt e openrouter-key.txt
  - Inicializar o LLM via OpenRouter (Gemini 2.5 Flash)
  - Definir o dicionário de Setores e Segmentos da B3 conforme especificação
"""

import os
from langchain_openai import ChatOpenAI


def carregar_chaves(caminho_arquivo="keys.txt"):
    """
    Carrega as chaves SERPER_API_KEY e OPENROUTER_API_KEY a partir do
    arquivo keys.txt. O arquivo deve ter as chaves em linhas separadas:
        Linha 1: SERPER_API_KEY
        Linha 2: OPENROUTER_API_KEY

    Caso keys.txt tenha apenas uma linha, tenta ler a chave do OpenRouter
    do arquivo auxiliar openrouter-key.txt.

    Returns:
        tuple(str, str): (serper_api_key, openrouter_api_key)
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado.
        ValueError: Se alguma chave estiver vazia.
    """
    # Busca o arquivo tanto no diretório atual quanto no diretório do script
    caminhos_busca = [
        caminho_arquivo,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), caminho_arquivo),
    ]

    linhas = []
    for caminho in caminhos_busca:
        if os.path.exists(caminho):
            with open(caminho, "r", encoding="utf-8") as f:
                linhas = [l.strip() for l in f.readlines() if l.strip()]
            break

    if not linhas:
        raise FileNotFoundError(
            f"Arquivo '{caminho_arquivo}' não encontrado ou vazio. "
            "Certifique-se de que o arquivo existe na raiz do projeto."
        )

    if len(linhas) >= 2:
        serper_api_key = linhas[0]
        openrouter_api_key = linhas[1]
    else:
        # Uma única linha — assume Serper; lê OpenRouter de arquivo separado
        serper_api_key = linhas[0]
        try:
            or_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "openrouter-key.txt")
            with open(or_path, "r", encoding="utf-8") as f:
                openrouter_api_key = f.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(
                "Chave do OpenRouter não encontrada. Adicione-a como segunda linha do "
                "arquivo keys.txt ou crie o arquivo openrouter-key.txt."
            )

    if not serper_api_key:
        raise ValueError("SERPER_API_KEY está vazia no arquivo de chaves.")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY está vazia no arquivo de chaves.")

    return serper_api_key, openrouter_api_key


def inicializar_llm(openrouter_api_key):
    """
    Inicializa o LLM via OpenRouter usando a API compatível com langchain-openai.
    max_tokens=4000 garante que o request não exceda o saldo disponível.

    Args:
        openrouter_api_key (str): Chave de API do OpenRouter.

    Returns:
        ChatOpenAI: Instância do LLM pronta para uso nos agentes.
    """
    llm = ChatOpenAI(
        model_name="nvidia/nemotron-3-super-120b-a12b:free",  # Nemotron Super — GRATUITO no OpenRouter
        openai_api_key=openrouter_api_key,              # Chave do OpenRouter
        openai_api_base="https://openrouter.ai/api/v1", # Base URL do OpenRouter
        max_tokens=4000,   # Modelos :free no OpenRouter não cobram créditos
        temperature=0.1,   # Temperatura baixa = respostas objetivas e factuais
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
