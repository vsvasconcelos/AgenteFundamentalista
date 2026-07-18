#!/bin/bash
# setup.sh — Recriação do ambiente virtual e instalação das dependências
# Execute com: bash setup.sh
# Requer Python 3.13 (instale com: sudo apt install python3.13 python3.13-venv)

set -e

echo "╔══════════════════════════════════════════════════════╗"
echo "║   B3 Fundamentalista — Setup do Ambiente Virtual     ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Verificação da versão do Python
PYTHON_BIN=""
for py in python3.13 python3.12 python3.11 python3.10; do
    if command -v $py &>/dev/null; then
        PYTHON_BIN=$py
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    echo "❌ Nenhum Python 3.10-3.13 encontrado no sistema."
    echo "   Instale com: sudo apt install python3.13 python3.13-venv"
    exit 1
fi

echo "✅ Python encontrado: $PYTHON_BIN ($(${PYTHON_BIN} --version))"

# Diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/.venv"

echo ""
echo "📁 Diretório do projeto: ${SCRIPT_DIR}"
echo "🐍 Criando ambiente virtual em: ${VENV_DIR}"
echo ""

# Recria o ambiente virtual
if [ -d "${VENV_DIR}" ]; then
    echo "⚠️  Ambiente virtual existente encontrado. Recriando..."
    rm -rf "${VENV_DIR}"
fi

${PYTHON_BIN} -m venv "${VENV_DIR}"
echo "✅ Ambiente virtual criado com sucesso."
echo ""

# Ativa o ambiente virtual
source "${VENV_DIR}/bin/activate"
echo "✅ Ambiente ativado: $(python --version)"

# Atualiza pip
echo ""
echo "📦 Atualizando pip..."
pip install --upgrade pip --quiet

# Instala as dependências
echo "📦 Instalando dependências do requirements.txt..."
pip install -r "${SCRIPT_DIR}/requirements.txt"

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ Instalação concluída com sucesso!               ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║   Para executar a aplicação:                         ║"
echo "║                                                      ║"
echo "║   source .venv/bin/activate                          ║"
echo "║   streamlit run app.py                               ║"
echo "╚══════════════════════════════════════════════════════╝"
