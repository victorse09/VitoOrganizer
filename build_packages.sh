#!/bin/bash
# =============================================================================
# VitoOrganizer Package Builder (.deb and .flatpak) -> Output to ./dist/
# =============================================================================
set -e

APP_NAME="vitoorganizer"
VERSION=$(grep 'APP_VERSION = ' core/version.py | cut -d '"' -f 2)
ARCH="all"
BUILD_DIR="build_packages_tmp"
DIST_DIR="dist"

echo "========================================="
echo "   Empaquetador VitoOrganizer v$VERSION   "
echo "========================================="

# Asegurar carpeta dist y limpiar temporales
mkdir -p "$DIST_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# -----------------------------------------------------------------------------
# 1. Construcción del Paquete Debian (.deb)
# -----------------------------------------------------------------------------
echo "[1/2] Construyendo paquete Debian (.deb)..."

DEB_ROOT="$BUILD_DIR/deb_root"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/share/vitoorganizer"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps"

# Archivo de control Debian
cat <<EOF > "$DEB_ROOT/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Vitokin <vitokin@naseriana.org>
Depends: python3, python3-pyqt6, python3-pyqt6.qtsvg, fonts-noto-color-emoji, fonts-dejavu-core
Description: Vito Organizer v$VERSION
 Agenda personal esqueumórfica al estilo clásico de Lotus Organizer
 con soporte para calendarios, tareas, notas multimedia, gestión de
 proyectos con Gantt panorámico, laboratorio de electrónica y biblioteca.
EOF

# Copiar archivos del proyecto al destino /usr/share/vitoorganizer
cp -r config core data graphics plugins resources tools main.py "$DEB_ROOT/usr/share/vitoorganizer/"

# Crear ejecutable autocontenido en /usr/bin/vitoorganizer
cat <<EOF > "$DEB_ROOT/usr/bin/vitoorganizer"
#!/bin/bash
export PYTHONPATH="/usr/share/vitoorganizer:\$PYTHONPATH"
cd /usr/share/vitoorganizer
exec python3 main.py "\$@"
EOF
chmod +x "$DEB_ROOT/usr/bin/vitoorganizer"

# Crear lanzador de escritorio (.desktop)
cat <<EOF > "$DEB_ROOT/usr/share/applications/vitoorganizer.desktop"
[Desktop Entry]
Name=Vito Organizer
Comment=Agenda personal esqueumórfica estilo Lotus Organizer
Exec=/usr/bin/vitoorganizer
Icon=vitoorganizer
Terminal=false
Type=Application
Categories=Utility;Office;Clock;Calendar;
StartupWMClass=vitoorganizer
EOF

# Copiar icono de la aplicación
cp resources/icons/vito_organizer_icon.svg "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps/vitoorganizer.svg"

# Asegurar permisos correctos en directorios debian
chmod -R 0755 "$DEB_ROOT"
chmod 0755 "$DEB_ROOT/DEBIAN"

# Empaquetar debian y mover a dist/
dpkg-deb --build "$DEB_ROOT" "$DIST_DIR/${APP_NAME}_${VERSION}.deb"
echo "✅ Paquete DEB creado en dist/: ${APP_NAME}_${VERSION}.deb"

# -----------------------------------------------------------------------------
# 2. Construcción del Paquete Flatpak (.flatpak)
# -----------------------------------------------------------------------------
echo "[2/2] Construyendo paquete Flatpak (.flatpak)..."

FLATPAK_ID="org.naseriana.VitoOrganizer"
FLATPAK_DIR="$BUILD_DIR/flatpak"
mkdir -p "$FLATPAK_DIR"

# Manifest Flatpak con instalación de PyQt6
cat <<EOF > "$FLATPAK_DIR/$FLATPAK_ID.json"
{
  "app-id": "$FLATPAK_ID",
  "runtime": "org.kde.Platform",
  "runtime-version": "6.6",
  "sdk": "org.kde.Sdk",
  "command": "vitoorganizer",
  "finish-args": [
    "--share=ipc",
    "--socket=fallback-x11",
    "--socket=wayland",
    "--socket=session-bus",
    "--filesystem=host",
    "--device=dri"
  ],
  "build-options": {
    "build-args": [
      "--share=network"
    ]
  },
  "modules": [
    {
      "name": "pyqt6-deps",
      "buildsystem": "simple",
      "build-commands": [
        "python3 -m pip install --prefix=/app PyQt6 PyQt6-sip"
      ]
    },
    {
      "name": "$APP_NAME",
      "buildsystem": "simple",
      "build-commands": [
        "mkdir -p /app/share/vitoorganizer /app/bin /app/share/applications /app/share/icons/hicolor/scalable/apps",
        "cp -r config core data graphics plugins resources tools main.py /app/share/vitoorganizer/",
        "echo '#!/bin/sh' > /app/bin/vitoorganizer",
        "echo 'export PYTHONPATH=/app/share/vitoorganizer:\$PYTHONPATH' >> /app/bin/vitoorganizer",
        "echo 'cd /app/share/vitoorganizer && exec python3 main.py \"\$@\"' >> /app/bin/vitoorganizer",
        "chmod +x /app/bin/vitoorganizer",
        "cp resources/icons/vito_organizer_icon.svg /app/share/icons/hicolor/scalable/apps/$FLATPAK_ID.svg"
      ],
      "sources": [
        {
          "type": "dir",
          "path": "../.."
        }
      ]
    }
  ]
}
EOF

if flatpak-builder --version >/dev/null 2>&1; then
    echo "Compilando aplicación Flatpak..."
    flatpak-builder --force-clean --state-dir="$BUILD_DIR/flatpak-state" "$BUILD_DIR/flatpak-build" "$FLATPAK_DIR/$FLATPAK_ID.json"
    echo "Inicializando repositorio ostree local..."
    mkdir -p "$BUILD_DIR/repo"
    if ! ostree refs --repo="$BUILD_DIR/repo" >/dev/null 2>&1; then
        ostree init --mode=archive-z2 --repo="$BUILD_DIR/repo"
    fi
    ostree config --repo="$BUILD_DIR/repo" set "core.min-free-space-percent" "0"
    echo "Exportando a repositorio local..."
    flatpak build-export "$BUILD_DIR/repo" "$BUILD_DIR/flatpak-build"
    echo "Generando bundle .flatpak..."
    flatpak build-bundle --arch=x86_64 "$BUILD_DIR/repo" "$DIST_DIR/${APP_NAME}_${VERSION}.flatpak" "$FLATPAK_ID"
    echo "✅ Paquete Flatpak creado en dist/: ${APP_NAME}_${VERSION}.flatpak"
fi

# Eliminar cualquier paquete viejo suelto de la raíz para mantener orden
rm -f vitoorganizer_*.deb vitoorganizer_*.flatpak

echo "========================================="
echo "   ¡Empaquetado completado en ./dist/!   "
echo "========================================="
