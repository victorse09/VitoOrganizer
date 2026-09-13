# =============================================================================
# Vito Organizer v2.2 - Biblioteca Plugin
# Gestor de Documentación, Manuales, Datasheets, Imágenes y Creador de Documentos Doki
# =============================================================================

import os
import shutil
import re
import json
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QUrl
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QDesktopServices
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QButtonGroup, QLineEdit, QStackedWidget,
    QTextEdit, QMessageBox, QFileDialog
)
from plugins.plugin_base import PluginBase, open_local_file, load_image_pixmap, IMAGE_EXTENSIONS
from data.data_store import DataStore
from plugins.biblioteca.dialogs import DocumentDialog, LibrarySettingsDialog, OpenDocChoiceDialog
from plugins.biblioteca.doc_viewer import DocViewerSinglePageWidget, get_themed_svg_icon
from plugins.biblioteca.doki_editor import DokiDocumentEditorWidget, NewDokiDialog, DokiManager


class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class BibLeftView(QWidget):
    """Vista de la página izquierda (Lista de Documentos en Biblioteca y Contenedor de Visor / Editor Single-Page)."""

    item_selected = pyqtSignal(dict)
    edit_item_requested = pyqtSignal(dict)
    pagination_changed = pyqtSignal(int, int) # (current_page, total_pages)
    create_doki_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.items = []
        self.active_type = 'Documentos Doki'
        self.search_query = ''
        self.page = 1
        self.icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 35, 15)
        layout.setSpacing(10)

        self.stack = QStackedWidget()

        # 0. List Container (Vista normal de lista)
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        self.list_layout.setSpacing(10)

        # Cabecera 3D
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(36)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0; border-radius: 4px;")
        self.hdr_layout = QHBoxLayout(self.hdr_frame)
        self.hdr_layout.setContentsMargins(10, 2, 10, 2)
        
        self.lbl_hdr_title = QLabel("Documentos Doki y Biblioteca")
        self.lbl_hdr_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        self.hdr_layout.addWidget(self.lbl_hdr_title)

        self.btn_new_doki = QPushButton("➕ Nuevo Documento Doki")
        self.btn_new_doki.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'new_note.svg'), '#FFFFFF', 14))
        self.btn_new_doki.setStyleSheet("QPushButton { background-color: #2E7D32; color: #FFFFFF; font-weight: bold; border-radius: 3px; padding: 4px 8px; font-size: 11px; } QPushButton:hover { background-color: #388E3C; }")
        self.btn_new_doki.clicked.connect(self.create_doki_requested.emit)
        self.hdr_layout.addWidget(self.btn_new_doki, alignment=Qt.AlignmentFlag.AlignRight)

        self.list_layout.addWidget(self.hdr_frame)

        # Área Scrollable
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)

        self.scroll.setWidget(self.scroll_content)
        self.list_layout.addWidget(self.scroll, 1)

        self.stack.addWidget(self.list_container)

        # 1. Editor / Visor Container (Modo Página Única)
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.editor_container)

        layout.addWidget(self.stack, 1)

    def set_data(self, items: list, active_type: str = 'Documentos Doki', search_query: str = '', page: int = 1, sort_order: str = 'alpha_asc', show_filename: bool = True):
        self.items = items
        self.active_type = active_type
        self.search_query = search_query.lower().strip()
        self.page = page
        self.sort_order = sort_order
        self.show_filename = show_filename
        
        if not hasattr(self, 'items_per_page'):
            self.items_per_page = 7
            
        self._refresh()

    def get_total_pages(self) -> int:
        return getattr(self, 'total_pages', 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalculate_items_per_page()

    def _recalculate_items_per_page(self):
        margins_y = 30
        hdr_y = 44
        available_y = self.height() - margins_y - hdr_y
        if available_y <= 0:
            return
            
        card_step = 44
        new_items_per_page = max(1, available_y // card_step)
        
        if not hasattr(self, 'items_per_page') or self.items_per_page != new_items_per_page:
            self.items_per_page = new_items_per_page
            self._refresh()
            self.pagination_changed.emit(self.page, self.get_total_pages())

    def _refresh(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child:
                w = child.widget()
                if w: w.deleteLater()

        clean_active = self.active_type.replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "").replace("📝 ", "")
        
        self.btn_new_doki.setVisible(clean_active in ('Documentos Doki', 'Documentos Propios (.doki)'))

        filtered = []
        for it in self.items:
            it_type = it.get('type', '').replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "").replace("📝 ", "")
            if it_type == 'Software / Firmware / Drivers':
                it_type = 'Software'
            if clean_active == 'Software / Firmware / Drivers':
                active_match = 'Software'
            elif clean_active in ('Documentos Doki', 'Documentos Propios (.doki)'):
                active_match = 'Documentos Doki'
            else:
                active_match = clean_active

            if it_type == active_match or (active_match == 'Documentos Doki' and it.get('relative_path', '').endswith('.doki')):
                if self.search_query:
                    name_m = self.search_query in it.get('name', '').lower()
                    desc_m = self.search_query in it.get('description', '').lower()
                    file_m = self.search_query in it.get('filename', '').lower()
                    if name_m or desc_m or file_m:
                        filtered.append(it)
                else:
                    filtered.append(it)

        # Ordenar elementos
        if self.sort_order == 'alpha_desc':
            filtered.sort(key=lambda x: x.get('name', '').lower(), reverse=True)
        elif self.sort_order == 'date_asc':
            filtered.sort(key=lambda x: x.get('id', ''))
        elif self.sort_order == 'date_desc':
            filtered.sort(key=lambda x: x.get('id', ''), reverse=True)
        else: # alpha_asc default
            filtered.sort(key=lambda x: x.get('name', '').lower())

        total_items = len(filtered)
        self.total_pages = max(1, (total_items + self.items_per_page - 1) // self.items_per_page)

        if self.page > self.total_pages:
            self.page = self.total_pages

        start_idx = (self.page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered[start_idx:end_idx]

        display_cat = "Documentos Propios (.doki)" if clean_active in ('Documentos Doki', 'Documentos Propios (.doki)') else self.active_type
        self.lbl_hdr_title.setText(f"{display_cat} ({total_items} archivos)")

        if not page_items:
            lbl_empty = QLabel("No hay documentos registrados en esta categoría.\nUsa '➕ Nuevo Documento Doki' para crear uno nuevo." if clean_active in ('Documentos Doki', 'Documentos Propios (.doki)') else "No hay documentos registrados en esta categoría.")
            lbl_empty.setStyleSheet("color: #666666; font-style: italic; font-size: 12px; margin-top: 20px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl_empty)
            self.scroll_layout.addStretch()
            return

        type_icons = {
            "Documentos Doki": "new_note.svg",
            "Imágenes": "image_file.svg",
            "Manuales": "manual.svg",
            "Datasheets": "datasheet.svg",
            "Libros": "manual.svg",
            "Revistas": "document.svg",
            "Información Técnica": "open_folder.svg",
            "Hojas de Seguridad": "safety.svg",
            "Software": "software.svg",
            "Otros Documentos": "document.svg"
        }
        icon_file = type_icons.get(clean_active, "document.svg")

        for item in page_items:
            card = ClickableFrame()
            card.setFixedHeight(40)
            card.setStyleSheet("""
                ClickableFrame { background-color: rgba(255, 255, 255, 0.9); border: 1px solid #D0C070; border-radius: 4px; }
                ClickableFrame:hover { background-color: #FFFFFF; border-color: #20B2AA; }
            """)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(10, 2, 8, 2)
            c_layout.setSpacing(10)

            # Icono
            lbl_ico = QLabel()
            lbl_ico.setPixmap(get_themed_svg_icon(os.path.join(self.icons_dir, icon_file), color_hex="#263238", size=20).pixmap(20, 20))
            c_layout.addWidget(lbl_ico)

            # Texto Nombre
            name_text = f"<b>{item.get('name')}</b>"
            if self.show_filename and item.get('filename'):
                name_text += f" <span style='color:#666; font-size:11px;'>({item.get('filename')})</span>"
            
            # Badges
            bms = item.get('bookmarks', [])
            arts = item.get('articles', [])
            badges = []
            if item.get('relative_path', '').endswith('.doki'):
                badges.append("📝 DOKI")
            if bms: badges.append(f"⭐ {len(bms)}")
            if arts: badges.append(f"📑 {len(arts)}")
            if badges:
                name_text += f" <span style='color:#E65100; font-size:10px; font-weight:bold;'>[{' '.join(badges)}]</span>"

            lbl_name = QLabel(name_text)
            lbl_name.setStyleSheet("color: #111111; font-size: 12px; border: none; background: transparent;")
            c_layout.addWidget(lbl_name, 1)

            # Botón Editar
            btn_edit = QPushButton()
            btn_edit.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'edit.svg'), color_hex="#455A64", size=18))
            btn_edit.setFixedSize(26, 26)
            btn_edit.setToolTip("Editar Información")
            btn_edit.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: #E0E0E0; border-radius: 3px; }")
            btn_edit.clicked.connect(lambda checked=False, it=item: self.edit_item_requested.emit(it))
            c_layout.addWidget(btn_edit)

            card.clicked.connect(lambda it=item: self.item_selected.emit(it))
            self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()


class BibRightView(QWidget):
    """Vista de la página derecha (Detalle de Documento, Editor Doki, Marcadores y Artículos)."""

    open_viewer_requested = pyqtSignal(dict, int) # (item, initial_page)
    open_file_requested = pyqtSignal(dict) # item
    open_doki_editor_requested = pyqtSignal(dict) # doki_item

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.current_item = None
        self.agenda_path = None
        self.lab_data = {}
        self.icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 15, 25, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0; border-radius: 4px;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_title = QLabel("Vista Previa y Lectura de Documento")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_title)
        layout.addWidget(self.hdr_frame)

        self.stack = QStackedWidget()

        # 0. Empty
        self.empty_lbl = QLabel("Selecciona un archivo de la lista para ver su vista previa, marcadores y artículos.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        self.stack.addWidget(self.empty_lbl)

        # 1. Detail Container (con Scroll)
        self.scroll_detail = QScrollArea()
        self.scroll_detail.setWidgetResizable(True)
        self.scroll_detail.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_detail.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.detail_container = QWidget()
        self.detail_container.setStyleSheet("background: transparent;")
        d_layout = QVBoxLayout(self.detail_container)
        d_layout.setContentsMargins(0, 0, 0, 0)
        d_layout.setSpacing(10)

        # Tarjeta 1: Información y Previsualización
        self.card_info = QFrame()
        self.card_info.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 10px; }")
        ci_layout = QVBoxLayout(self.card_info)

        self.img_preview = QLabel()
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setMaximumHeight(180)
        self.img_preview.setStyleSheet("border: 1px solid #DDD; background: #FAFAFA; border-radius: 4px;")
        ci_layout.addWidget(self.img_preview)

        # Contenedor de previsualización HTML para documentos Doki
        self.doki_preview = QTextEdit()
        self.doki_preview.setReadOnly(True)
        self.doki_preview.setMaximumHeight(220)
        self.doki_preview.setStyleSheet("background-color: #FFFFFF; color: #222; border: 1px solid #CCC; border-radius: 4px; padding: 8px; font-size: 12px;")
        ci_layout.addWidget(self.doki_preview)

        self.lbl_detail_text = QLabel()
        self.lbl_detail_text.setWordWrap(True)
        self.lbl_detail_text.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 12px;")
        ci_layout.addWidget(self.lbl_detail_text)

        # Botones de Acción para Documentos Doki
        self.doki_actions_layout = QVBoxLayout()
        self.btn_edit_doki = QPushButton(" ✏️ Editar Documento en Modo de Página Única")
        self.btn_edit_doki.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'pencil.svg'), '#FFFFFF', 16))
        self.btn_edit_doki.setStyleSheet("QPushButton { background-color: #1565C0; color: white; font-weight: bold; padding: 8px 14px; border-radius: 4px; font-size: 12px; } QPushButton:hover { background-color: #0D47A1; }")
        self.btn_edit_doki.clicked.connect(lambda: self.open_doki_editor_requested.emit(self.current_item))
        self.doki_actions_layout.addWidget(self.btn_edit_doki)

        doki_export_row = QHBoxLayout()
        doki_export_row.setSpacing(6)
        
        self.btn_exp_pdf = QPushButton("📄 PDF")
        self.btn_exp_pdf.setToolTip("Exportar a PDF")
        self.btn_exp_pdf.clicked.connect(lambda: self._export_current_doki('pdf'))
        doki_export_row.addWidget(self.btn_exp_pdf)

        self.btn_exp_epub = QPushButton("📚 EPUB")
        self.btn_exp_epub.setToolTip("Exportar a EPUB")
        self.btn_exp_epub.clicked.connect(lambda: self._export_current_doki('epub'))
        doki_export_row.addWidget(self.btn_exp_epub)

        self.btn_exp_odt = QPushButton("📑 OpenDocument (.odt)")
        self.btn_exp_odt.setToolTip("Exportar a OpenDocument (.odt)")
        self.btn_exp_odt.clicked.connect(lambda: self._export_current_doki('odt'))
        doki_export_row.addWidget(self.btn_exp_odt)

        self.btn_exp_xml = QPushButton("⚙️ XML")
        self.btn_exp_xml.setToolTip("Exportar a XML")
        self.btn_exp_xml.clicked.connect(lambda: self._export_current_doki('xml'))
        doki_export_row.addWidget(self.btn_exp_xml)

        self.doki_actions_layout.addLayout(doki_export_row)
        ci_layout.addLayout(self.doki_actions_layout)

        # Botones de Acción de Lectura y Apertura Estándar
        self.standard_actions_layout = QHBoxLayout()
        self.btn_open_viewer = QPushButton(" 📖 Leer en Visor Integrado")
        self.btn_open_viewer.setIcon(QIcon(os.path.join(self.icons_dir, 'manual.svg')))
        self.btn_open_viewer.setStyleSheet("QPushButton { background-color: #1E88E5; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #1565C0; }")
        self.btn_open_viewer.clicked.connect(lambda: self.open_viewer_requested.emit(self.current_item, 1))
        self.standard_actions_layout.addWidget(self.btn_open_viewer)

        self.btn_open_file = QPushButton(" 🖥️ Abrir en Sistema")
        self.btn_open_file.setIcon(QIcon(os.path.join(self.icons_dir, 'open_folder.svg')))
        self.btn_open_file.setStyleSheet("QPushButton { background-color: #455A64; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #37474F; }")
        self.btn_open_file.clicked.connect(lambda: self.open_file_requested.emit(self.current_item))
        self.standard_actions_layout.addWidget(self.btn_open_file)
        ci_layout.addLayout(self.standard_actions_layout)

        d_layout.addWidget(self.card_info)

        # Tarjeta 2: Marcadores Guardados (Bookmarks)
        self.card_bookmarks = QFrame()
        self.card_bookmarks.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 8px; }")
        bm_layout = QVBoxLayout(self.card_bookmarks)
        bm_layout.setContentsMargins(8, 8, 8, 8)
        bm_layout.setSpacing(6)

        lbl_bm_title = QLabel("⭐ Marcadores de Páginas Guardados:")
        lbl_bm_title.setStyleSheet("font-weight: bold; color: #E65100; font-size: 12px; border: none; background: transparent;")
        bm_layout.addWidget(lbl_bm_title)

        self.bookmarks_container = QVBoxLayout()
        self.bookmarks_container.setSpacing(4)
        bm_layout.addLayout(self.bookmarks_container)
        d_layout.addWidget(self.card_bookmarks)

        # Tarjeta 3: Artículos y Secciones Extraídas
        self.card_articles = QFrame()
        self.card_articles.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 8px; }")
        art_layout = QVBoxLayout(self.card_articles)
        art_layout.setContentsMargins(8, 8, 8, 8)
        art_layout.setSpacing(6)

        lbl_art_title = QLabel("📑 Artículos y Secciones Extraídas (PDFs):")
        lbl_art_title.setStyleSheet("font-weight: bold; color: #BF360C; font-size: 12px; border: none; background: transparent;")
        art_layout.addWidget(lbl_art_title)

        self.articles_container = QVBoxLayout()
        self.articles_container.setSpacing(4)
        art_layout.addLayout(self.articles_container)
        d_layout.addWidget(self.card_articles)

        # Tarjeta 4: Asignaciones a Elementos
        self.asgn_frame = QFrame()
        self.asgn_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; padding: 10px; }")
        af_layout = QVBoxLayout(self.asgn_frame)
        af_layout.setContentsMargins(8, 8, 8, 8)
        
        lbl_asgn_title = QLabel("Elementos de Laboratorio Vinculados:")
        lbl_asgn_title.setStyleSheet("font-weight: bold; color: #333; font-size: 12px; border: none; background: transparent;")
        af_layout.addWidget(lbl_asgn_title)

        self.lbl_assigned_elements = QLabel()
        self.lbl_assigned_elements.setWordWrap(True)
        self.lbl_assigned_elements.setStyleSheet("color: #111; font-size: 12px; border: none; background: transparent;")
        af_layout.addWidget(self.lbl_assigned_elements)
        d_layout.addWidget(self.asgn_frame)

        self.scroll_detail.setWidget(self.detail_container)
        self.stack.addWidget(self.scroll_detail)
        layout.addWidget(self.stack, 1)

    def set_item(self, item: dict, agenda_path: str, lab_data: dict = None):
        self.current_item = item
        self.agenda_path = agenda_path
        self.lab_data = lab_data or {}
        if not item:
            self.stack.setCurrentIndex(0)
            return

        self.stack.setCurrentIndex(1)
        self.lbl_title.setText(f"Documento: {item.get('name')}")

        rel_path = item.get('relative_path', '')
        full_path = os.path.join(agenda_path, rel_path) if agenda_path and rel_path else ""

        is_doki = rel_path.lower().endswith('.doki') or item.get('type') == 'Documentos Doki'

        txt = f"<h3 style='margin:0; color:#20B2AA;'>{item.get('name')}</h3>"
        txt += f"<b>Tipo:</b> {item.get('type')}<br>"
        txt += f"<b>Archivo:</b> {item.get('filename')}<br>"
        if item.get('author'):
            txt += f"<b>Autor:</b> {item.get('author')}<br>"
        txt += f"<b>Descripción:</b> {item.get('description', 'Sin descripción')}<br>"
        self.lbl_detail_text.setText(txt)

        # Mostrar controles según si es Doki o estándar
        for i in range(self.doki_actions_layout.count()):
            w = self.doki_actions_layout.itemAt(i).widget()
            if w: w.setVisible(is_doki)
        self.btn_edit_doki.setVisible(is_doki)
        self.btn_exp_pdf.setVisible(is_doki)
        self.btn_exp_epub.setVisible(is_doki)
        self.btn_exp_odt.setVisible(is_doki)
        self.btn_exp_xml.setVisible(is_doki)

        is_doc = rel_path.lower().endswith(('.pdf', '.epub')) and not is_doki
        self.btn_open_viewer.setVisible(is_doc and os.path.exists(full_path))
        self.btn_open_file.setVisible(os.path.exists(full_path))

        self.card_bookmarks.setVisible(not is_doki)
        self.card_articles.setVisible(not is_doki)

        # Previsualización
        if is_doki and os.path.exists(full_path):
            self.img_preview.setVisible(False)
            try:
                doki_content = DokiManager.load_doki(full_path)
                self.doki_preview.setHtml(doki_content.get('html', ''))
                self.doki_preview.setVisible(True)
            except Exception:
                self.doki_preview.setHtml("<p><i>No se pudo generar la vista previa del documento Doki.</i></p>")
                self.doki_preview.setVisible(True)
        else:
            self.doki_preview.setVisible(False)
            clean_type_str = item.get('type', '').replace("🖼️ ", "").replace("💻 ", "")
            is_img = clean_type_str == 'Imágenes' or rel_path.lower().endswith(IMAGE_EXTENSIONS)
            is_pdf = rel_path.lower().endswith('.pdf')
            
            preview_loaded = False
            if os.path.exists(full_path):
                if is_img:
                    pix = load_image_pixmap(full_path)
                    if not pix.isNull():
                        self.img_preview.setPixmap(pix.scaled(320, 170, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        preview_loaded = True
                elif is_pdf:
                    try:
                        import fitz
                        from PyQt6.QtGui import QImage
                        doc = fitz.open(full_path)
                        if len(doc) > 0:
                            page = doc[0]
                            pix = page.get_pixmap(dpi=100)
                            fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
                            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                            pixmap = QPixmap.fromImage(qimg.copy())
                            self.img_preview.setPixmap(pixmap.scaled(320, 170, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            preview_loaded = True
                    except Exception as e:
                        print(f"Error cargando preview PDF: {e}")
                        
            self.img_preview.setVisible(preview_loaded)

        # 1. Renderizar Marcadores
        while self.bookmarks_container.count():
            c = self.bookmarks_container.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        bookmarks = item.get('bookmarks', [])
        if not bookmarks:
            lbl_no_bm = QLabel("<span style='color:#777; font-style:italic;'>No hay marcadores guardados en este documento.</span>")
            self.bookmarks_container.addWidget(lbl_no_bm)
        else:
            for bm in bookmarks:
                p_num = bm.get('page', 1)
                bm_btn = QPushButton(f" Pág. {p_num}: {bm.get('title', 'Marcador')}  ({bm.get('date', '')})")
                bm_btn.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'pushpin.svg'), '#E65100', 14))
                bm_btn.setStyleSheet("""
                    QPushButton { text-align: left; background-color: #FFF3E0; border: 1px solid #FFE0B2; border-radius: 4px; padding: 4px 8px; color: #E65100; font-size: 11px; font-weight: bold; }
                    QPushButton:hover { background-color: #FFE0B2; }
                """)
                bm_btn.clicked.connect(lambda checked=False, p=p_num: self.open_viewer_requested.emit(self.current_item, p))
                self.bookmarks_container.addWidget(bm_btn)

        # 2. Renderizar Artículos
        while self.articles_container.count():
            c = self.articles_container.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        articles = item.get('articles', [])
        if not articles:
            lbl_no_art = QLabel("<span style='color:#777; font-style:italic;'>No hay artículos extraídos aún.</span>")
            self.articles_container.addWidget(lbl_no_art)
        else:
            for art in articles:
                art_frame = QFrame()
                art_frame.setStyleSheet("background-color: #FBE9E7; border: 1px solid #FFCCBC; border-radius: 4px; padding: 4px;")
                af_l = QHBoxLayout(art_frame)
                af_l.setContentsMargins(6, 2, 6, 2)
                af_l.setSpacing(6)

                lbl_art = QLabel(f"<b>{art.get('title')}</b> <span style='color:#666; font-size:10px;'>(Págs. {art.get('from_page')} a {art.get('to_page')})</span>")
                lbl_art.setStyleSheet("color: #BF360C; font-size: 11px; border: none;")
                af_l.addWidget(lbl_art, 1)

                btn_open_art = QPushButton(" Abrir PDF")
                btn_open_art.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'document.svg'), '#FFFFFF', 12))
                btn_open_art.setStyleSheet("QPushButton { background-color: #D84315; color: white; font-weight: bold; border-radius: 3px; padding: 3px 8px; font-size: 10px; } QPushButton:hover { background-color: #BF360C; }")
                art_rel_p = art.get('relative_path', '')
                art_full_p = os.path.join(agenda_path, art_rel_p) if agenda_path and art_rel_p else ""
                btn_open_art.clicked.connect(lambda checked=False, p=art_full_p: open_local_file(p))
                af_l.addWidget(btn_open_art)

                btn_jump = QPushButton(f" Ver Pág. {art.get('from_page', 1)}")
                btn_jump.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'right.svg'), '#37474F', 12))
                btn_jump.setStyleSheet("QPushButton { background-color: #ECEFF1; color: #37474F; font-weight: bold; border-radius: 3px; padding: 3px 8px; font-size: 10px; border: 1px solid #CFD8DC; } QPushButton:hover { background-color: #CFD8DC; }")
                btn_jump.clicked.connect(lambda checked=False, p=art.get('from_page', 1): self.open_viewer_requested.emit(self.current_item, p))
                af_l.addWidget(btn_jump)

                self.articles_container.addWidget(art_frame)

        # 3. Elementos Asignados
        assigned_ids = item.get('assigned_element_ids', [])
        target_cat = item.get('target_category', 'components')
        items_list = self.lab_data.get(target_cat, [])

        matched_names = []
        for it in items_list:
            if it.get('id') in assigned_ids or it.get('name') in assigned_ids:
                detail = it.get('category') or it.get('brand') or it.get('type') or ''
                detail_str = f" ({detail})" if detail else ""
                matched_names.append(f"• <b>{it.get('name')}</b>{detail_str}")

        if not matched_names:
            self.lbl_assigned_elements.setText("<span style='color:#777; font-style:italic;'>Este archivo no está asignado a ningún elemento actualmente.</span>")
        else:
            self.lbl_assigned_elements.setText("<br>".join(matched_names))

    def _export_current_doki(self, fmt: str):
        if not self.current_item or not self.agenda_path: return
        rel_p = self.current_item.get('relative_path', '')
        full_p = os.path.join(self.agenda_path, rel_p) if rel_p else ""
        if not os.path.exists(full_p):
            QMessageBox.warning(self, "Archivo no encontrado", "No se encuentra el archivo .doki para exportar.")
            return

        try:
            doki_data = DokiManager.load_doki(full_p)
            exp_dir = os.path.join(self.agenda_path, 'biblioteca', 'doki', 'exports')
            os.makedirs(exp_dir, exist_ok=True)
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', self.current_item.get('name', 'documento')).lower()

            if fmt == 'pdf':
                dest = os.path.join(exp_dir, f"{clean_name}.pdf")
                DokiManager.export_to_pdf(doki_data, dest)
                open_local_file(dest)
            elif fmt == 'epub':
                dest = os.path.join(exp_dir, f"{clean_name}.epub")
                DokiManager.export_to_epub(doki_data, dest)
                open_local_file(dest)
            elif fmt == 'odt':
                dest = os.path.join(exp_dir, f"{clean_name}.odt")
                DokiManager.export_to_odt(doki_data, dest)
                open_local_file(dest)
            elif fmt == 'xml':
                dest = os.path.join(exp_dir, f"{clean_name}.xml")
                DokiManager.export_to_xml(doki_data, dest)
                open_local_file(dest)

        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"Ocurrió un error al exportar el documento:\n{e}")


class BibliotecaSidebar(QWidget):
    """Barra lateral de Biblioteca con navegación de tipos y búsqueda."""

    type_changed = pyqtSignal(str)
    search_changed = pyqtSignal(str)
    upload_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarWidget")
        self.setStyleSheet("""
            QWidget#sidebarWidget { background-color: #1e1e2e; border-right: 1px solid #313244; }
            QLabel { color: #cdd6f4; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 15, 10, 15)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # 1. Botón Subir Archivo
        btn_upload = QPushButton(" Subir Archivo...")
        btn_upload.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        btn_upload.setStyleSheet("""
            QPushButton { background-color: #20B2AA; color: #ffffff; font-weight: bold; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background-color: #3CB371; }
        """)
        btn_upload.clicked.connect(self.upload_clicked.emit)
        layout.addWidget(btn_upload)

        # 2. Buscador
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar documentos...")
        self.search_input.addAction(QIcon(os.path.join(icons_dir, 'search.svg')), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setStyleSheet("QLineEdit { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px 8px; }")
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        # 3. Categorías de Documentación
        lbl_cat = QLabel("Filtro por Tipo")
        lbl_cat.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_cat)

        types_layout = QVBoxLayout()
        types_layout.setSpacing(2)
        self.type_group = QButtonGroup(self)

        t_list = [
            ("Documentos Doki", " 📝 Documentos Propios (.doki)", "new_note.svg"),
            ("Imágenes", " Imágenes", "image_file.svg"),
            ("Manuales", " Manuales", "manual.svg"),
            ("Datasheets", " Datasheets", "datasheet.svg"),
            ("Libros", " Libros", "manual.svg"),
            ("Revistas", " Revistas", "document.svg"),
            ("Información Técnica", " Información Técnica", "open_folder.svg"),
            ("Hojas de Seguridad", " Hojas de Seguridad", "safety.svg"),
            ("Software", " Software / Firmware / Drivers", "software.svg"),
            ("Otros Documentos", " Otros Documentos", "document.svg")
        ]
        for i, (tid, tname, ticon) in enumerate(t_list):
            btn = QPushButton(tname)
            btn.setIcon(QIcon(os.path.join(icons_dir, ticon)))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 5px 8px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; font-size: 11px; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #20B2AA; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)
            btn.clicked.connect(lambda checked, t=tid: self.type_changed.emit(t))
            self.type_group.addButton(btn, i)
            types_layout.addWidget(btn)
            if i == 0: btn.setChecked(True)
        layout.addLayout(types_layout)

        layout.addStretch()

        # 4. Botón de engranaje inferior izquierdo
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Biblioteca")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)


class BibliotecaPlugin(PluginBase):
    """Plugin para la sección de Biblioteca."""

    trash_changed = pyqtSignal()
    page_changed = pyqtSignal(int, int)
    single_page_requested = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._data = {'documents': [], '_trash': [], 'default_open_action': 'integrated'}
        self._trash = []
        self._is_modified = False
        self.active_type = 'Documentos Doki'
        self.search_query = ''
        self.agenda_path = None
        self._current_page = 1
        self.active_viewer = None
        self.active_doki_editor = None

        # Sidebar
        self._sidebar = BibliotecaSidebar()
        self._sidebar.type_changed.connect(self._on_type_changed)
        self._sidebar.search_changed.connect(self._on_search_changed)
        self._sidebar.upload_clicked.connect(self._on_upload_document)
        self._sidebar.settings_clicked.connect(self._on_show_settings)

        # Pages
        self._left_page = BibLeftView()
        self._right_page = BibRightView()

        self._left_page.item_selected.connect(self._on_item_selected)
        self._left_page.edit_item_requested.connect(self._on_edit_item)
        self._left_page.pagination_changed.connect(self._on_left_page_pagination_changed)
        self._left_page.create_doki_requested.connect(self._on_create_new_doki)

        self._right_page.open_viewer_requested.connect(self._on_open_viewer)
        self._right_page.open_file_requested.connect(self._on_open_file_action)
        self._right_page.open_doki_editor_requested.connect(self._on_open_doki_editor)

    def get_total_pages(self) -> int:
        return self._left_page.get_total_pages()

    def get_current_page(self) -> int:
        return self._current_page

    def go_to_page(self, page_num: int):
        total = self.get_total_pages()
        self._current_page = max(1, min(page_num, total))
        self._update_views()

    def set_plugin_manager(self, pm):
        self.plugin_manager = pm

    def _get_lab_plugin_data(self) -> dict:
        if hasattr(self, 'plugin_manager') and self.plugin_manager:
            lab_p = self.plugin_manager.get_plugin_by_id('laboratorio')
            if lab_p and hasattr(lab_p, '_data') and lab_p._data:
                return lab_p._data
        if self.agenda_path:
            lab_path = DataStore.get_plugin_data_path(self.agenda_path, 'laboratorio')
            return DataStore.load(lab_path) or {}
        return {}

    def _ensure_library_folders(self):
        """Garantiza la creación física de las subcarpetas dentro de <agenda_path>/biblioteca/."""
        if not self.agenda_path: return
        bib_dir = os.path.join(self.agenda_path, 'biblioteca')
        subfolders = ['doki', 'Manuales', 'Datasheets', 'Libros', 'Revistas', 'Informacion_Tecnica', 'Hojas_de_Seguridad', 'Imagenes', 'Software', 'Documentacion', 'Otros_Documentos', 'Articulos']
        for sf in subfolders:
            os.makedirs(os.path.join(bib_dir, sf), exist_ok=True)
        os.makedirs(os.path.join(bib_dir, 'doki', 'exports'), exist_ok=True)

    def _sync_doki_files(self):
        """Sincroniza archivos .doki físicos de la carpeta biblioteca/doki/ con la lista de documentos."""
        if not self.agenda_path: return
        doki_dir = os.path.join(self.agenda_path, 'biblioteca', 'doki')
        if not os.path.exists(doki_dir): return

        docs = self._data.setdefault('documents', [])
        existing_rel_paths = {d.get('relative_path') for d in docs}

        for fn in os.listdir(doki_dir):
            if fn.endswith('.doki'):
                rel_p = f"biblioteca/doki/{fn}"
                if rel_p not in existing_rel_paths:
                    full_p = os.path.join(doki_dir, fn)
                    try:
                        d_info = DokiManager.load_doki(full_p)
                        meta = d_info.get('metadata', {})
                        doc_item = {
                            'id': meta.get('id', fn.replace('.doki', '')),
                            'name': meta.get('title', fn),
                            'type': 'Documentos Doki',
                            'author': meta.get('author', 'Usuario'),
                            'description': meta.get('description', ''),
                            'filename': fn,
                            'relative_path': rel_p,
                            'bookmarks': [],
                            'articles': []
                        }
                        docs.append(doc_item)
                        self._is_modified = True
                    except Exception:
                        pass

    def _update_views(self):
        self._sync_doki_files()
        items = self._data.get('documents', [])
        sort_order = self._data.get('sort_order', 'alpha_asc')
        show_filename = self._data.get('show_filename', True)
        self._left_page.set_data(items, self.active_type, self.search_query, self._current_page, sort_order=sort_order, show_filename=show_filename)
        total = self._left_page.get_total_pages()
        if self._current_page > total:
            self._current_page = total
        self.page_changed.emit(self._current_page, total)

    def _on_left_page_pagination_changed(self, page: int, total: int):
        self._current_page = page
        self.page_changed.emit(page, total)

    def _on_type_changed(self, doc_type: str):
        self.active_type = doc_type
        self._current_page = 1
        self._update_views()
        self._right_page.set_item(None, self.agenda_path, self._get_lab_plugin_data())

    def _on_search_changed(self, query: str):
        self.search_query = query
        self._current_page = 1
        self._update_views()

    def _on_item_selected(self, item: dict):
        self._right_page.set_item(item, self.agenda_path, self._get_lab_plugin_data())

    # =========================================================================
    # CREADOR Y EDITOR DE DOCUMENTOS DOKI
    # =========================================================================

    def _on_create_new_doki(self):
        if not self.agenda_path: return
        dlg = NewDokiDialog(parent=self._sidebar.window())
        if dlg.exec():
            d = dlg.get_data()
            meta = DokiManager.create_empty_doki(self.agenda_path, d['title'], d['author'], d['description'])
            
            doc_item = {
                'id': meta['id'],
                'name': meta['title'],
                'type': 'Documentos Doki',
                'author': meta['author'],
                'description': meta['description'],
                'filename': meta['filename'],
                'relative_path': meta['relative_path'],
                'bookmarks': [],
                'articles': []
            }
            self._data.setdefault('documents', []).append(doc_item)
            self._is_modified = True
            self.save_data(self.agenda_path)
            self._update_views()
            self._on_open_doki_editor(doc_item)

    def _on_open_doki_editor(self, item: dict):
        if not item or not self.agenda_path: return

        while self._left_page.editor_layout.count():
            c = self._left_page.editor_layout.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        self.active_doki_editor = DokiDocumentEditorWidget(item, self.agenda_path, parent=self._left_page.editor_container)
        self.active_doki_editor.back_requested.connect(self._on_close_doki_editor)
        self.active_doki_editor.document_saved.connect(self._on_doki_saved)

        self._left_page.editor_layout.addWidget(self.active_doki_editor)
        self._left_page.stack.setCurrentIndex(1)
        self.single_page_requested.emit(True)

    def _on_close_doki_editor(self):
        self._left_page.stack.setCurrentIndex(0)
        self.single_page_requested.emit(False)
        self.active_doki_editor = None
        self._update_views()
        if self._right_page.current_item:
            self._right_page.set_item(self._right_page.current_item, self.agenda_path, self._get_lab_plugin_data())

    def _on_doki_saved(self, item: dict):
        self._is_modified = True
        if self.agenda_path:
            self.save_data(self.agenda_path)
        self._update_views()
        if self._right_page.current_item and self._right_page.current_item.get('id') == item.get('id'):
            self._right_page.set_item(item, self.agenda_path, self._get_lab_plugin_data())

    # =========================================================================
    # VISOR DE DOCUMENTOS
    # =========================================================================

    def _on_open_viewer(self, item: dict, initial_page: int = 1):
        if not item or not self.agenda_path: return

        while self._left_page.editor_layout.count():
            c = self._left_page.editor_layout.takeAt(0)
            if c.widget(): c.widget().deleteLater()

        self.active_viewer = DocViewerSinglePageWidget(item, self.agenda_path, initial_page=initial_page, parent=self._left_page.editor_container)
        self.active_viewer.back_requested.connect(self._on_close_viewer)
        self.active_viewer.bookmarks_updated.connect(lambda bms: self._on_bookmarks_updated(item, bms))
        self.active_viewer.articles_updated.connect(lambda arts: self._on_articles_updated(item, arts))

        self._left_page.editor_layout.addWidget(self.active_viewer)
        self._left_page.stack.setCurrentIndex(1)
        self.single_page_requested.emit(True)

    def _on_close_viewer(self):
        self._left_page.stack.setCurrentIndex(0)
        self.single_page_requested.emit(False)
        self.active_viewer = None
        self._update_views()
        if self._right_page.current_item:
            self._right_page.set_item(self._right_page.current_item, self.agenda_path, self._get_lab_plugin_data())

    def _on_bookmarks_updated(self, item: dict, bookmarks: list):
        item['bookmarks'] = bookmarks
        self._is_modified = True
        if self.agenda_path:
            self.save_data(self.agenda_path)
        self._right_page.set_item(item, self.agenda_path, self._get_lab_plugin_data())

    def _on_articles_updated(self, item: dict, articles: list):
        item['articles'] = articles
        self._is_modified = True
        if self.agenda_path:
            self.save_data(self.agenda_path)
        self._right_page.set_item(item, self.agenda_path, self._get_lab_plugin_data())

    def _on_open_file_action(self, item: dict):
        if not item or not self.agenda_path: return
        rel_path = item.get('relative_path', '')
        full_path = os.path.join(self.agenda_path, rel_path) if rel_path else ""

        if rel_path.lower().endswith('.doki'):
            self._on_open_doki_editor(item)
            return

        is_doc = rel_path.lower().endswith(('.pdf', '.epub'))
        if not is_doc or not os.path.exists(full_path):
            open_local_file(full_path)
            return

        action_pref = self._data.get('default_open_action', 'integrated')

        if action_pref == 'ask':
            dlg = OpenDocChoiceDialog(item.get('name', 'Documento'), parent=self._sidebar.window())
            if dlg.exec() and dlg.choice:
                if dlg.remember:
                    self._data['default_open_action'] = dlg.choice
                    self._is_modified = True
                    self.save_data(self.agenda_path)
                if dlg.choice == 'integrated':
                    self._on_open_viewer(item)
                else:
                    open_local_file(full_path)
        elif action_pref == 'integrated':
            self._on_open_viewer(item)
        else: # system
            open_local_file(full_path)

    def _on_upload_document(self):
        lab_data = self._get_lab_plugin_data()
        dlg = DocumentDialog(lab_data=lab_data, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            item_data = dlg.item_data
            if dlg.selected_file_path and self.agenda_path:
                self._ensure_library_folders()
                clean_item_t = item_data.get('type', '').replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "").replace("📝 ", "")
                type_map = {
                    "Documentos Doki": ("doki", "doki"),
                    "Imágenes": ("Imagenes", "img"),
                    "Manuales": ("Manuales", "man"),
                    "Datasheets": ("Datasheets", "data"),
                    "Libros": ("Libros", "book"),
                    "Revistas": ("Revistas", "mag"),
                    "Información Técnica": ("Informacion_Tecnica", "inf"),
                    "Hojas de Seguridad": ("Hojas_de_Seguridad", "msds"),
                    "Software": ("Software", "soft"),
                    "Software / Firmware / Drivers": ("Software", "soft"),
                    "Firmware": ("Software", "fw"),
                    "Drivers": ("Software", "drv"),
                    "Documentación": ("Documentacion", "doc"),
                    "Otros Documentos": ("Otros_Documentos", "oth")
                }
                subfolder, prefix = type_map.get(clean_item_t, ("Otros_Documentos", "oth"))
                
                docs = self._data.get('documents', [])
                count = sum(1 for d in docs if d.get('type', '').replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "").replace("📝 ", "") == clean_item_t) + 1
                
                ext = os.path.splitext(dlg.selected_file_path)[1].lower()
                clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', item_data.get('name', 'file')).lower()
                new_filename = f"{prefix}{count:03d}_{clean_name}{ext}"
                
                dest_folder = os.path.join(self.agenda_path, 'biblioteca', subfolder)
                dest_path = os.path.join(dest_folder, new_filename)
                shutil.copy2(dlg.selected_file_path, dest_path)

                item_data['filename'] = new_filename
                item_data['relative_path'] = f"biblioteca/{subfolder}/{new_filename}"

            self._data.setdefault('documents', []).append(item_data)
            self.active_type = item_data.get('type')
            self._is_modified = True
            self._update_views()
            self._right_page.set_item(item_data, self.agenda_path, lab_data)

    def _on_edit_item(self, item: dict):
        lab_data = self._get_lab_plugin_data()
        dlg = DocumentDialog(item_to_edit=item, lab_data=lab_data, parent=self._sidebar.window())
        if dlg.exec():
            docs = self._data.get('documents', [])
            if dlg.is_delete:
                if item in docs:
                    docs.remove(item)
                    self.move_to_trash(item)
                    self._is_modified = True
                    self._update_views()
                    self._right_page.set_item(None, self.agenda_path, lab_data)
                    self.trash_changed.emit()
            elif dlg.item_data:
                item_data = dlg.item_data
                if dlg.selected_file_path and self.agenda_path:
                    self._ensure_library_folders()
                    clean_item_t = item_data.get('type', '').replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "").replace("📝 ", "")
                    type_map = {
                        "Documentos Doki": ("doki", "doki"),
                        "Imágenes": ("Imagenes", "img"),
                        "Manuales": ("Manuales", "man"),
                        "Datasheets": ("Datasheets", "data"),
                        "Libros": ("Libros", "book"),
                        "Revistas": ("Revistas", "mag"),
                        "Información Técnica": ("Informacion_Tecnica", "inf"),
                        "Hojas de Seguridad": ("Hojas_de_Seguridad", "msds"),
                        "Software": ("Software", "soft"),
                        "Software / Firmware / Drivers": ("Software", "soft"),
                        "Firmware": ("Software", "fw"),
                        "Drivers": ("Software", "drv"),
                        "Documentación": ("Documentacion", "doc"),
                        "Otros Documentos": ("Otros_Documentos", "oth")
                    }
                    subfolder, prefix = type_map.get(clean_item_t, ("Otros_Documentos", "oth"))
                    ext = os.path.splitext(dlg.selected_file_path)[1].lower()
                    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', item_data.get('name', 'file')).lower()
                    new_filename = f"{prefix}_{clean_name}{ext}"
                    dest_folder = os.path.join(self.agenda_path, 'biblioteca', subfolder)
                    dest_path = os.path.join(dest_folder, new_filename)
                    shutil.copy2(dlg.selected_file_path, dest_path)
                    item_data['filename'] = new_filename
                    item_data['relative_path'] = f"biblioteca/{subfolder}/{new_filename}"

                # Preservar marcadores y artículos existentes al editar metadata
                if 'bookmarks' in item: item_data['bookmarks'] = item['bookmarks']
                if 'articles' in item: item_data['articles'] = item['articles']

                idx = docs.index(item) if item in docs else -1
                if idx >= 0: docs[idx] = item_data
                self._is_modified = True
                self._update_views()
                self._right_page.set_item(item_data, self.agenda_path, lab_data)

    def _on_show_settings(self):
        dlg = LibrarySettingsDialog(plugin_data=self._data, parent=self._sidebar.window())
        if dlg.exec():
            self._is_modified = True
            self._update_views()
            if self.agenda_path:
                self.save_data(self.agenda_path)

    # --- Papelera ---
    def move_to_trash(self, item: dict): self._trash.append(item)
    def get_trash_items(self) -> list: return self._trash
    def restore_item(self, index: int):
        if 0 <= index < len(self._trash):
            item = self._trash.pop(index)
            self._data.setdefault('documents', []).append(item)
            self._is_modified = True
            self._update_views()
            self.trash_changed.emit()

    def get_name(self) -> str: return "Biblioteca"
    def get_id(self) -> str: return "biblioteca"
    def get_icon(self) -> str: return "library.svg"
    def get_tab_color(self) -> str: return "#20B2AA"
    def get_order(self) -> int: return 7

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

    def load_data(self, agenda_path: str):
        self.agenda_path = agenda_path
        self._ensure_library_folders()
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
            self._trash = loaded.get('_trash', [])
        self._sync_doki_files()
        self._update_views()
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            DataStore.save(data_path, self._data)
            self._is_modified = False
