# -*- coding: utf-8 -*-
"""
Vito Organizer — Pestaña de Notas Markdown
Módulo de gestión de notas con editor Markdown de vista dividida.
Panel izquierdo: lista de notas con búsqueda.
Panel derecho: barra de herramientas + editor/previsualizador Markdown.
"""

import os
import re
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTextEdit, QTextBrowser, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QLabel, QMessageBox,
    QToolBar, QFrame, QSizePolicy
)

# ── Importaciones del proyecto ──
from database import Database
from svg_icons import (
    icon_new, icon_save, icon_delete, icon_edit,
    icon_search, svg_to_qicon
)

# ── Importación de Markdown con manejo de extensiones opcionales ──
try:
    import markdown as md_lib
    _MD_DISPONIBLE = True
except ImportError:
    _MD_DISPONIBLE = False

# Extensiones deseadas para el renderizado Markdown
_EXTENSIONES_MD = []
if _MD_DISPONIBLE:
    _extensiones_candidatas = ['tables', 'fenced_code', 'codehilite', 'nl2br']
    for ext in _extensiones_candidatas:
        try:
            # Verificar que la extensión se pueda cargar
            md_lib.markdown("", extensions=[ext])
            _EXTENSIONES_MD.append(ext)
        except Exception:
            # Si la extensión no está disponible, continuar sin ella
            pass

# ── Color principal para iconos ──
_COLOR_ICONO = '#4A3728'


# ═══════════════════════════════════════════════════════════════════
# CSS para la vista previa HTML del Markdown
# ═══════════════════════════════════════════════════════════════════

_CSS_PREVIEW = """
<style>
    body {
        background-color: #FDF5E6;
        color: #3B2314;
        font-family: 'Georgia', 'Times New Roman', serif;
        font-size: 14px;
        line-height: 1.7;
        padding: 16px 20px;
        margin: 0;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #2C1810;
        font-family: 'Segoe UI', 'Arial', sans-serif;
        margin-top: 1.2em;
        margin-bottom: 0.5em;
        border-bottom: 1px solid #D4C5A9;
        padding-bottom: 4px;
    }
    h1 { font-size: 1.8em; }
    h2 { font-size: 1.5em; }
    h3 { font-size: 1.25em; border-bottom: none; }
    h4, h5, h6 { border-bottom: none; }
    p { margin: 0.6em 0; }
    a { color: #6B4226; text-decoration: underline; }
    a:hover { color: #8B5E3C; }
    code {
        background-color: #EDE0CC;
        color: #5D3A1A;
        padding: 2px 5px;
        border-radius: 3px;
        font-family: 'Courier New', monospace;
        font-size: 0.92em;
    }
    pre {
        background-color: #EDE0CC;
        border: 1px solid #D4C5A9;
        border-radius: 5px;
        padding: 12px 14px;
        overflow-x: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        line-height: 1.5;
    }
    pre code {
        background: none;
        padding: 0;
        border-radius: 0;
    }
    blockquote {
        border-left: 4px solid #A0896E;
        margin: 0.8em 0;
        padding: 8px 16px;
        background-color: #F5EDDC;
        color: #5D4E37;
        font-style: italic;
    }
    ul, ol {
        padding-left: 28px;
        margin: 0.5em 0;
    }
    li { margin: 0.25em 0; }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 1em 0;
    }
    th, td {
        border: 1px solid #C4AD8C;
        padding: 8px 12px;
        text-align: left;
    }
    th {
        background-color: #E8D9C0;
        color: #2C1810;
        font-weight: bold;
    }
    tr:nth-child(even) { background-color: #F7F0E3; }
    hr {
        border: none;
        border-top: 1px solid #C4AD8C;
        margin: 1.5em 0;
    }
    img { max-width: 100%; height: auto; border-radius: 4px; }
</style>
"""


# ═══════════════════════════════════════════════════════════════════
# Widget personalizado para ítems de la lista de notas
# ═══════════════════════════════════════════════════════════════════

class _WidgetItemNota(QWidget):
    """
    Widget compacto que muestra el título y la fecha de una nota
    dentro de un QListWidgetItem.
    """

    def __init__(self, titulo: str, fecha: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # ── Título en negrita ──
        self.lbl_titulo = QLabel(titulo)
        self.lbl_titulo.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.lbl_titulo.setStyleSheet("color: #2C1810;")
        self.lbl_titulo.setWordWrap(False)
        layout.addWidget(self.lbl_titulo)

        # ── Fecha en gris, tamaño menor ──
        self.lbl_fecha = QLabel(self._formatear_fecha(fecha))
        self.lbl_fecha.setFont(QFont("Segoe UI", 9))
        self.lbl_fecha.setStyleSheet("color: #8B7D6B;")
        layout.addWidget(self.lbl_fecha)

    @staticmethod
    def _formatear_fecha(fecha_iso: str) -> str:
        """Convierte fecha ISO a formato legible en español."""
        try:
            dt = datetime.fromisoformat(fecha_iso)
            return dt.strftime("%d/%m/%Y  %H:%M")
        except (ValueError, TypeError):
            return fecha_iso or ""


# ═══════════════════════════════════════════════════════════════════
# Clase principal: TabNotes
# ═══════════════════════════════════════════════════════════════════

class TabNotes(QWidget):
    """
    Pestaña de Notas Markdown para Vito Organizer.
    
    Proporciona un gestor completo de notas con:
    - Lista lateral con búsqueda
    - Editor de texto Markdown en fuente monoespaciada
    - Vista previa HTML en tiempo real con debounce
    - Operaciones CRUD completas (crear, leer, actualizar, eliminar)
    
    Args:
        db: Instancia de la base de datos.
        notas_dir: Ruta al directorio donde se almacenan los archivos .md.
    """

    def __init__(self, db: Database, notas_dir: str, parent=None):
        super().__init__(parent)
        self.db = db
        self.notas_dir = notas_dir

        # Asegurar que el directorio de notas existe
        os.makedirs(self.notas_dir, exist_ok=True)

        # ── Estado interno ──
        self._nota_actual_id: int | None = None       # ID de la nota seleccionada
        self._nota_actual_filename: str | None = None  # Nombre del archivo .md

        # ── Timer de debounce para actualizar la vista previa ──
        self._timer_preview = QTimer(self)
        self._timer_preview.setSingleShot(True)
        self._timer_preview.setInterval(300)  # 300 ms de debounce
        self._timer_preview.timeout.connect(self._actualizar_preview)

        # ── Construir la interfaz ──
        self._construir_ui()
        self._aplicar_estilos()

        # ── Cargar la lista de notas ──
        self._recargar_lista_notas()

    # ───────────────────────────────────────────────────────────
    # Construcción de la interfaz
    # ───────────────────────────────────────────────────────────

    def _construir_ui(self):
        """Construye todos los elementos de la interfaz."""
        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Panel izquierdo (lista de notas) ──
        panel_izquierdo = self._crear_panel_izquierdo()
        layout_principal.addWidget(panel_izquierdo)

        # ── Separador vertical sutil ──
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.VLine)
        separador.setStyleSheet("color: #C4AD8C;")
        layout_principal.addWidget(separador)

        # ── Panel derecho (editor + preview) ──
        panel_derecho = self._crear_panel_derecho()
        layout_principal.addWidget(panel_derecho, 1)  # Stretch = 1

    def _crear_panel_izquierdo(self) -> QWidget:
        """Crea el panel izquierdo con barra de búsqueda y lista de notas."""
        panel = QWidget()
        panel.setFixedWidth(260)
        panel.setObjectName("panelListaNotas")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Encabezado ──
        lbl_titulo = QLabel("Notas")
        lbl_titulo.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #2C1810; padding: 4px 0;")
        layout.addWidget(lbl_titulo)

        # ── Barra de búsqueda ──
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("Buscar notas...")
        self.input_busqueda.setClearButtonEnabled(True)
        # Icono de búsqueda como acción del campo
        icono_busqueda = svg_to_qicon(icon_search(), size=16, color='#8B7D6B')
        self.input_busqueda.addAction(icono_busqueda, QLineEdit.ActionPosition.LeadingPosition)
        self.input_busqueda.textChanged.connect(self._filtrar_notas)
        layout.addWidget(self.input_busqueda)

        # ── Lista de notas ──
        self.lista_notas = QListWidget()
        self.lista_notas.setObjectName("listaNotas")
        self.lista_notas.setSpacing(2)
        self.lista_notas.currentRowChanged.connect(self._al_seleccionar_nota)
        layout.addWidget(self.lista_notas, 1)

        return panel

    def _crear_panel_derecho(self) -> QWidget:
        """Crea el panel derecho con barra de herramientas, editor y preview."""
        panel = QWidget()
        panel.setObjectName("panelEditorNotas")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Barra de herramientas ──
        toolbar = self._crear_toolbar()
        layout.addWidget(toolbar)

        # ── Splitter vertical: editor arriba, preview abajo ──
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.setObjectName("splitterNotas")

        # Editor Markdown (texto plano, monoespaciado)
        self.editor = QTextEdit()
        self.editor.setObjectName("editorMarkdown")
        self.editor.setFont(QFont("Courier New", 12))
        self.editor.setPlaceholderText("Escribe tu nota en Markdown aquí...")
        self.editor.setAcceptRichText(False)
        self.editor.textChanged.connect(self._programar_preview)
        self.splitter.addWidget(self.editor)

        # Vista previa HTML
        self.preview = QTextBrowser()
        self.preview.setObjectName("previewMarkdown")
        self.preview.setOpenExternalLinks(True)
        self.splitter.addWidget(self.preview)

        # División inicial 50/50
        self.splitter.setSizes([400, 400])

        layout.addWidget(self.splitter, 1)

        return panel

    def _crear_toolbar(self) -> QWidget:
        """Crea la barra de herramientas del editor."""
        toolbar = QWidget()
        toolbar.setObjectName("toolbarNotas")
        toolbar.setFixedHeight(48)
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        # ── Botón Nueva Nota ──
        self.btn_nueva = QPushButton("Nueva Nota")
        self.btn_nueva.setIcon(svg_to_qicon(icon_new(), size=20, color=_COLOR_ICONO))
        self.btn_nueva.setIconSize(QSize(20, 20))
        self.btn_nueva.setToolTip("Crear una nueva nota")
        self.btn_nueva.clicked.connect(self._crear_nota)
        layout.addWidget(self.btn_nueva)

        # ── Botón Guardar ──
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setIcon(svg_to_qicon(icon_save(), size=20, color=_COLOR_ICONO))
        self.btn_guardar.setIconSize(QSize(20, 20))
        self.btn_guardar.setToolTip("Guardar la nota actual")
        self.btn_guardar.clicked.connect(self._guardar_nota)
        layout.addWidget(self.btn_guardar)

        # ── Botón Eliminar ──
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setIcon(svg_to_qicon(icon_delete(), size=20, color=_COLOR_ICONO))
        self.btn_eliminar.setIconSize(QSize(20, 20))
        self.btn_eliminar.setToolTip("Eliminar la nota seleccionada")
        self.btn_eliminar.clicked.connect(self._eliminar_nota)
        layout.addWidget(self.btn_eliminar)

        # ── Separador visual ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedHeight(28)
        sep.setStyleSheet("color: #C4AD8C;")
        layout.addWidget(sep)

        # ── Campo de título de nota ──
        lbl_titulo = QLabel("Titulo:")
        lbl_titulo.setFont(QFont("Segoe UI", 10))
        lbl_titulo.setStyleSheet("color: #4A3728;")
        layout.addWidget(lbl_titulo)

        self.input_titulo = QLineEdit()
        self.input_titulo.setPlaceholderText("Titulo de la nota")
        self.input_titulo.setMinimumWidth(200)
        self.input_titulo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.input_titulo, 1)

        return toolbar

    # ───────────────────────────────────────────────────────────
    # Estilos CSS
    # ───────────────────────────────────────────────────────────

    def _aplicar_estilos(self):
        """Aplica la hoja de estilos completa al widget."""
        self.setStyleSheet("""
            /* ── Fondo general ── */
            #panelListaNotas {
                background-color: #FDF5E6;
                border-right: 1px solid #D4C5A9;
            }
            #panelEditorNotas {
                background-color: #FDF5E6;
            }

            /* ── Barra de búsqueda ── */
            #panelListaNotas QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #C4AD8C;
                border-radius: 4px;
                padding: 6px 8px 6px 28px;
                font-size: 12px;
                color: #3B2314;
            }
            #panelListaNotas QLineEdit:focus {
                border-color: #8B6F47;
            }

            /* ── Lista de notas ── */
            #listaNotas {
                background-color: #FDF5E6;
                border: none;
                outline: none;
            }
            #listaNotas::item {
                border-bottom: 1px solid #E8DCC8;
                padding: 2px;
            }
            #listaNotas::item:selected {
                background-color: #E8D9C0;
                border-left: 3px solid #8B6F47;
            }
            #listaNotas::item:hover {
                background-color: #F5EDDC;
            }

            /* ── Toolbar ── */
            #toolbarNotas {
                background-color: #F5EDDC;
                border-bottom: 1px solid #D4C5A9;
            }
            #toolbarNotas QPushButton {
                background-color: #EDE0CC;
                border: 1px solid #C4AD8C;
                border-radius: 4px;
                padding: 5px 12px;
                color: #4A3728;
                font-size: 11px;
                font-weight: bold;
            }
            #toolbarNotas QPushButton:hover {
                background-color: #E0D0B8;
                border-color: #A0896E;
            }
            #toolbarNotas QPushButton:pressed {
                background-color: #D4C5A9;
            }
            #toolbarNotas QLineEdit {
                background-color: #FFFFFF;
                border: 1px solid #C4AD8C;
                border-radius: 4px;
                padding: 5px 8px;
                font-size: 12px;
                color: #3B2314;
            }
            #toolbarNotas QLineEdit:focus {
                border-color: #8B6F47;
            }

            /* ── Editor Markdown ── */
            #editorMarkdown {
                background-color: #FDF5E6;
                color: #4A3728;
                border: none;
                padding: 12px;
                selection-background-color: #D4C5A9;
                selection-color: #2C1810;
            }

            /* ── Vista previa Markdown ── */
            #previewMarkdown {
                background-color: #FDF5E6;
                border: none;
                border-top: 1px solid #D4C5A9;
                padding: 0;
            }

            /* ── Splitter handle ── */
            #splitterNotas::handle {
                background-color: #D4C5A9;
                height: 3px;
            }
            #splitterNotas::handle:hover {
                background-color: #A0896E;
            }

            /* ── Scrollbars ── */
            QScrollBar:vertical {
                background: #F5EDDC;
                width: 10px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: #C4AD8C;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0896E;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QScrollBar:horizontal {
                background: #F5EDDC;
                height: 10px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: #C4AD8C;
                min-width: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #A0896E;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0;
            }
        """)

    # ───────────────────────────────────────────────────────────
    # Gestión de la lista de notas
    # ───────────────────────────────────────────────────────────

    def _recargar_lista_notas(self, texto_filtro: str = ""):
        """
        Recarga la lista de notas desde la base de datos.
        
        Args:
            texto_filtro: Texto para filtrar notas por título (sin distinción
                          de mayúsculas/minúsculas).
        """
        self.lista_notas.blockSignals(True)
        self.lista_notas.clear()

        notas = self.db.obtener_notas()
        filtro = texto_filtro.strip().lower()

        for nota in notas:
            titulo = nota.get('title', 'Sin titulo')
            # Aplicar filtro de búsqueda
            if filtro and filtro not in titulo.lower():
                continue

            fecha = nota.get('updated_at', nota.get('created_at', ''))
            nota_id = nota.get('id')

            # Crear ítem con widget personalizado
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, nota_id)
            item.setSizeHint(QSize(240, 54))

            widget = _WidgetItemNota(titulo, fecha)
            self.lista_notas.addItem(item)
            self.lista_notas.setItemWidget(item, widget)

        self.lista_notas.blockSignals(False)

    def _filtrar_notas(self, texto: str):
        """Filtra la lista de notas según el texto de búsqueda."""
        self._recargar_lista_notas(texto)

    def _al_seleccionar_nota(self, fila: int):
        """Maneja la selección de una nota en la lista."""
        if fila < 0:
            return

        item = self.lista_notas.item(fila)
        if not item:
            return

        nota_id = item.data(Qt.ItemDataRole.UserRole)
        self._cargar_nota(nota_id)

    # ───────────────────────────────────────────────────────────
    # Operaciones CRUD
    # ───────────────────────────────────────────────────────────

    def _crear_nota(self):
        """Crea una nueva nota con título por defecto."""
        # Generar título y nombre de archivo
        ahora = datetime.now()
        titulo = "Nueva nota"
        nombre_archivo = self._generar_nombre_archivo(titulo, ahora)

        # Crear archivo .md vacío
        ruta_archivo = os.path.join(self.notas_dir, nombre_archivo)
        contenido_inicial = f"# {titulo}\n\n"
        try:
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido_inicial)
        except OSError as e:
            QMessageBox.critical(
                self, "Error",
                f"No se pudo crear el archivo:\n{e}"
            )
            return

        # Registrar en la base de datos
        nota_id = self.db.crear_nota(titulo, nombre_archivo)

        # Recargar lista y seleccionar la nueva nota
        self._recargar_lista_notas(self.input_busqueda.text())
        self._seleccionar_nota_en_lista(nota_id)
        self._cargar_nota(nota_id)

        # Enfocar el campo de título para renombrar
        self.input_titulo.setFocus()
        self.input_titulo.selectAll()

    def _guardar_nota(self):
        """Guarda el contenido y título de la nota actual."""
        if self._nota_actual_id is None:
            QMessageBox.information(
                self, "Sin nota",
                "No hay ninguna nota seleccionada para guardar."
            )
            return

        # Obtener contenido del editor
        contenido = self.editor.toPlainText()
        titulo = self.input_titulo.text().strip()

        if not titulo:
            QMessageBox.warning(
                self, "Titulo vacio",
                "El titulo de la nota no puede estar vacio."
            )
            self.input_titulo.setFocus()
            return

        # Escribir contenido al archivo .md
        if self._nota_actual_filename:
            ruta_archivo = os.path.join(self.notas_dir, self._nota_actual_filename)
            try:
                with open(ruta_archivo, 'w', encoding='utf-8') as f:
                    f.write(contenido)
            except OSError as e:
                QMessageBox.critical(
                    self, "Error al guardar",
                    f"No se pudo escribir el archivo:\n{e}"
                )
                return

        # Actualizar registro en la base de datos (título + timestamp)
        self.db.actualizar_nota(self._nota_actual_id, titulo)

        # Recargar lista manteniendo el filtro actual
        filtro_actual = self.input_busqueda.text()
        self._recargar_lista_notas(filtro_actual)
        self._seleccionar_nota_en_lista(self._nota_actual_id)

    def _eliminar_nota(self):
        """Elimina la nota actual previa confirmación del usuario."""
        if self._nota_actual_id is None:
            QMessageBox.information(
                self, "Sin nota",
                "No hay ninguna nota seleccionada para eliminar."
            )
            return

        # Obtener datos de la nota
        nota = self.db.obtener_nota_por_id(self._nota_actual_id)
        if not nota:
            return

        titulo = nota.get('title', 'Sin titulo')

        # Diálogo de confirmación
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminacion",
            f"Desea eliminar la nota \"{titulo}\"?\n\n"
            "Esta accion no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta != QMessageBox.StandardButton.Yes:
            return

        # Eliminar archivo .md del disco
        if self._nota_actual_filename:
            ruta_archivo = os.path.join(self.notas_dir, self._nota_actual_filename)
            try:
                if os.path.exists(ruta_archivo):
                    os.remove(ruta_archivo)
            except OSError:
                pass  # Continuar aunque falle la eliminación del archivo

        # Eliminar registro de la base de datos
        self.db.eliminar_nota(self._nota_actual_id)

        # Limpiar el editor
        self._nota_actual_id = None
        self._nota_actual_filename = None
        self.editor.clear()
        self.preview.clear()
        self.input_titulo.clear()

        # Recargar lista
        self._recargar_lista_notas(self.input_busqueda.text())

    def _cargar_nota(self, nota_id: int):
        """
        Carga una nota desde la base de datos y el archivo .md al editor.
        
        Args:
            nota_id: ID de la nota a cargar.
        """
        nota = self.db.obtener_nota_por_id(nota_id)
        if not nota:
            return

        self._nota_actual_id = nota_id
        self._nota_actual_filename = nota.get('filename', '')
        titulo = nota.get('title', '')

        # Cargar título
        self.input_titulo.setText(titulo)

        # Leer contenido del archivo .md
        contenido = ""
        if self._nota_actual_filename:
            ruta_archivo = os.path.join(self.notas_dir, self._nota_actual_filename)
            try:
                if os.path.exists(ruta_archivo):
                    with open(ruta_archivo, 'r', encoding='utf-8') as f:
                        contenido = f.read()
            except OSError:
                contenido = ""

        # Cargar contenido en el editor (esto disparará textChanged → preview)
        self.editor.blockSignals(True)
        self.editor.setPlainText(contenido)
        self.editor.blockSignals(False)

        # Actualizar preview inmediatamente
        self._actualizar_preview()

    # ───────────────────────────────────────────────────────────
    # Vista previa Markdown
    # ───────────────────────────────────────────────────────────

    def _programar_preview(self):
        """Programa la actualización de la vista previa con debounce de 300ms."""
        self._timer_preview.start()

    def _actualizar_preview(self):
        """Renderiza el Markdown del editor y lo muestra en la vista previa."""
        texto_md = self.editor.toPlainText()

        if _MD_DISPONIBLE:
            try:
                html_body = md_lib.markdown(
                    texto_md,
                    extensions=_EXTENSIONES_MD
                )
            except Exception:
                html_body = f"<pre>{self._escapar_html(texto_md)}</pre>"
        else:
            # Fallback: mostrar texto plano si la librería no está instalada
            html_body = f"<pre>{self._escapar_html(texto_md)}</pre>"

        # Envolver con CSS y estructura HTML
        html_completo = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="utf-8">{_CSS_PREVIEW}</head>
        <body>{html_body}</body>
        </html>
        """
        self.preview.setHtml(html_completo)

    @staticmethod
    def _escapar_html(texto: str) -> str:
        """Escapa caracteres especiales de HTML."""
        return (texto
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

    # ───────────────────────────────────────────────────────────
    # Utilidades internas
    # ───────────────────────────────────────────────────────────

    @staticmethod
    def _sanitizar_para_nombre_archivo(texto: str) -> str:
        """
        Sanitiza un texto para usarlo como nombre de archivo.
        Elimina caracteres especiales y reemplaza espacios por guiones bajos.
        """
        # Convertir a minúsculas y reemplazar espacios
        nombre = texto.lower().strip()
        nombre = nombre.replace(' ', '_')
        # Eliminar caracteres no alfanuméricos (excepto guión bajo y guión)
        nombre = re.sub(r'[^a-z0-9_\-áéíóúñü]', '', nombre)
        # Limitar longitud
        nombre = nombre[:50] if len(nombre) > 50 else nombre
        # Evitar nombre vacío
        return nombre if nombre else "nota"

    def _generar_nombre_archivo(self, titulo: str, fecha: datetime) -> str:
        """
        Genera un nombre de archivo único basado en el título y la marca temporal.
        
        Args:
            titulo: Título de la nota.
            fecha: Fecha/hora para la marca temporal.
        
        Returns:
            Nombre de archivo con extensión .md.
        """
        base = self._sanitizar_para_nombre_archivo(titulo)
        timestamp = fecha.strftime("%Y%m%d_%H%M%S")
        return f"{base}_{timestamp}.md"

    def _seleccionar_nota_en_lista(self, nota_id: int):
        """
        Selecciona una nota en la lista por su ID.
        
        Args:
            nota_id: ID de la nota a seleccionar.
        """
        for i in range(self.lista_notas.count()):
            item = self.lista_notas.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == nota_id:
                self.lista_notas.blockSignals(True)
                self.lista_notas.setCurrentRow(i)
                self.lista_notas.blockSignals(False)
                return
