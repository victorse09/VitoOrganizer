#!/bin/bash
# =============================================================================
# Vito Organizer v2.3 - Script de inicio
# Gestiona el entorno virtual y ejecuta la aplicación
# =============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
REQ_FILE="$SCRIPT_DIR/requirements.txt"
REQ_HASH_FILE="$VENV_DIR/.req_hash"

cd "$SCRIPT_DIR"

# --- Colores para output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Vito Organizer v2.3             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"

# --- Crear entorno virtual si no existe ---
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}⚙ Creando entorno virtual...${NC}"
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Error al crear el entorno virtual${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
fi

# --- Activar entorno virtual ---
echo -e "${YELLOW}⚙ Activando entorno virtual...${NC}"
source "$VENV_DIR/bin/activate"
echo -e "${GREEN}✓ Entorno virtual activado${NC}"

# --- Verificar e instalar dependencias ---
CURRENT_HASH=""
if [ -f "$REQ_FILE" ]; then
    CURRENT_HASH=$(md5sum "$REQ_FILE" | awk '{print $1}')
fi

STORED_HASH=""
if [ -f "$REQ_HASH_FILE" ]; then
    STORED_HASH=$(cat "$REQ_HASH_FILE")
fi

if [ "$CURRENT_HASH" != "$STORED_HASH" ]; then
    echo -e "${YELLOW}⚙ Instalando/actualizando dependencias...${NC}"
    pip install -r "$REQ_FILE" --quiet
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Error al instalar dependencias${NC}"
        deactivate
        exit 1
    fi
    echo "$CURRENT_HASH" > "$REQ_HASH_FILE"
    echo -e "${GREEN}✓ Dependencias instaladas${NC}"
else
    echo -e "${GREEN}✓ Dependencias al día${NC}"
fi

# --- Ejecutar la aplicación ---
echo -e "${GREEN}▶ Iniciando Vito Organizer...${NC}"
echo ""
python3 "$SCRIPT_DIR/main.py" "$@"
EXIT_CODE=$?

# --- Desactivar entorno virtual ---
echo ""
echo -e "${YELLOW}⚙ Desactivando entorno virtual...${NC}"
deactivate
echo -e "${GREEN}✓ Entorno virtual desactivado${NC}"
echo -e "${GREEN}✓ Vito Organizer cerrado correctamente (código: $EXIT_CODE)${NC}"

exit $EXIT_CODE
