#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Vito Organizer — Script de Empaquetado .deb
# Genera un paquete Debian instalable usando PyInstaller.
# ═══════════════════════════════════════════════════════════

set -e

# ── Configuración ──
APP_NAME="vito-organizer"
APP_VERSION="1.0.0"
APP_DESCRIPTION="Agenda personal esqueumórfica inspirada en Lotus Organizer"
MAINTAINER="Vito <vito@vitoorganizer.local>"
ARCHITECTURE="amd64"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
BUILD_DIR="build_deb_temp"
PKG_DIR="${BUILD_DIR}/${APP_NAME}_${APP_VERSION}"

echo "══════════════════════════════════════════"
echo "  Vito Organizer — Empaquetado .deb"
echo "══════════════════════════════════════════"

# ── 1. Verificar entorno virtual ──
if [ ! -d "$VENV_DIR" ]; then
    echo "[*] Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# ── 2. Instalar dependencias y PyInstaller ──
echo "[*] Instalando dependencias..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pyinstaller

# ── 3. Compilar con PyInstaller ──
echo "[*] Compilando binario con PyInstaller..."
pyinstaller --onefile \
    --name "$APP_NAME" \
    --windowed \
    --clean \
    --noconfirm \
    --add-data "svg_icons.py:." \
    main.py

echo "[✓] Binario compilado en dist/$APP_NAME"

# ── 4. Crear estructura de directorios Debian ──
echo "[*] Creando estructura del paquete Debian..."
rm -rf "$BUILD_DIR"
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"
mkdir -p "${PKG_DIR}/usr/share/doc/${APP_NAME}"

# ── 5. Crear archivo control ──
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${APP_VERSION}
Section: utils
Priority: optional
Architecture: ${ARCHITECTURE}
Maintainer: ${MAINTAINER}
Depends: libgl1, libglib2.0-0, libfontconfig1, libxkbcommon0, libdbus-1-3
Description: ${APP_DESCRIPTION}
 Vito Organizer es una agenda personal moderna con interfaz
 esqueumórfica que replica el aspecto clásico de Lotus Organizer.
 Incluye: Calendario, Notas Markdown, Inventario de componentes,
 Control de instrumentos y Gestor de enlaces.
EOF

# ── 6. Script postinst (permisos) ──
cat > "${PKG_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
chmod +x /usr/bin/vito-organizer
EOF
chmod 755 "${PKG_DIR}/DEBIAN/postinst"

# ── 7. Copiar binario ──
echo "[*] Copiando binario al paquete..."
cp "dist/$APP_NAME" "${PKG_DIR}/usr/bin/"
chmod 755 "${PKG_DIR}/usr/bin/$APP_NAME"

# ── 8. Copiar archivo .desktop ──
cp "vito_organizer.desktop" "${PKG_DIR}/usr/share/applications/"

# ── 9. Generar icono SVG para el sistema ──
cat > "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/vito-organizer.svg" << 'EOF'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect x="4" y="4" width="56" height="56" rx="6" fill="#2C1810"/>
  <rect x="8" y="8" width="22" height="48" rx="2" fill="#FDF5E6"/>
  <rect x="34" y="8" width="22" height="48" rx="2" fill="#FDF5E6"/>
  <circle cx="32" cy="16" r="4" fill="#C0C0C0" stroke="#808080" stroke-width="1"/>
  <circle cx="32" cy="32" r="4" fill="#C0C0C0" stroke="#808080" stroke-width="1"/>
  <circle cx="32" cy="48" r="4" fill="#C0C0C0" stroke="#808080" stroke-width="1"/>
  <rect x="52" y="12" width="6" height="10" rx="1" fill="#E74C3C"/>
  <rect x="52" y="24" width="6" height="10" rx="1" fill="#F1C40F"/>
  <rect x="52" y="36" width="6" height="10" rx="1" fill="#27AE60"/>
  <rect x="52" y="48" width="6" height="10" rx="1" fill="#3498DB"/>
</svg>
EOF

# ── 10. Documentación ──
cat > "${PKG_DIR}/usr/share/doc/${APP_NAME}/README" << 'EOF'
Vito Organizer v1.0.0
=====================

Agenda personal esqueumórfica inspirada en Lotus Organizer.

Módulos:
- Calendario / Agenda
- Gestor de Notas (Markdown)
- Inventario de Componentes
- Control de Instrumentos
- Enlaces de Interés

Los datos se almacenan en ~/.local/share/VitoOrganizer/
EOF

# ── 11. Construir el paquete .deb ──
echo "[*] Construyendo paquete .deb..."
dpkg-deb --build "${PKG_DIR}"

# ── 12. Mover resultado ──
mv "${PKG_DIR}.deb" "./${APP_NAME}_${APP_VERSION}_${ARCHITECTURE}.deb"

# ── 13. Limpiar ──
echo "[*] Limpiando archivos temporales..."
rm -rf "$BUILD_DIR" build dist *.spec

# ── Resultado final ──
deactivate 2>/dev/null || true

echo ""
echo "══════════════════════════════════════════"
echo "  Paquete generado exitosamente:"
echo "  ./${APP_NAME}_${APP_VERSION}_${ARCHITECTURE}.deb"
echo ""
echo "  Para instalar:"
echo "  sudo dpkg -i ${APP_NAME}_${APP_VERSION}_${ARCHITECTURE}.deb"
echo "══════════════════════════════════════════"
