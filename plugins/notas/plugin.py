# =============================================================================
# Vito Organizer v2.2 - Notas Plugin
# =============================================================================

import os
import base64
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QUrl
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QDesktopServices
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QScrollArea, QFrame, QButtonGroup, QLineEdit,
    QTextEdit, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QSplitter, QToolBar, QComboBox
)

from plugins.plugin_base import PluginBase, load_image_pixmap, IMAGE_FILE_FILTER
from data.data_store import DataStore
from plugins.notas.dialogs import NoteDialog, NotebookDialog, LinkDialog, NoteSettingsDialog
from plugins.notas.canvas import HandwritingCanvasWidget


class NoteCardWidget(QFrame):
    """Widget de tarjeta resumen para una nota en la lista izquierda."""
    
    selected = pyqtSignal(dict)

    def __init__(self, note: dict, notebook_name: str = "", parent=None):
        super().__init__(parent)
        self.note = note
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.7);
                border: 1px solid #D0C070;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.95);
                border-color: #4682B4;
            }
        """)
        self._setup_ui(notebook_name)

    def _setup_ui(self, notebook_name):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Header: Icono + Título + Fecha
        hdr_layout = QHBoxLayout()
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        type_icons = {
            'text': 'document_dark.svg',
            'markdown': 'manual_dark.svg',
            'links': 'link_dark.svg',
            'image': 'image_file_dark.svg',
            'handwriting': 'pencil_dark.svg'
        }
        icon_file = type_icons.get(self.note.get('type'), 'document.svg')
        icon_img = f"<img src='{os.path.join(icons_dir, icon_file)}' width='14' height='14'>"
        
        lbl_title = QLabel(f"{icon_img} <b>{self.note.get('title', 'Sin Título')}</b>")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #111111; border: none; background: transparent;")
        hdr_layout.addWidget(lbl_title, 1)

        lbl_date = QLabel(self.note.get('updated_at', ''))
        lbl_date.setStyleSheet("font-size: 10px; color: #666666; border: none; background: transparent;")
        hdr_layout.addWidget(lbl_date)
        layout.addLayout(hdr_layout)

        # Footer: Cuaderno badge + Categoría
        ftr_layout = QHBoxLayout()
        if notebook_name:
            nb_img = f"<img src='{os.path.join(icons_dir, 'manual_dark.svg')}' width='12' height='12'>"
            lbl_nb = QLabel(f"{nb_img} <b>{notebook_name}</b>")
            lbl_nb.setStyleSheet("font-size: 10px; font-weight: bold; color: #4682B4; border: none; background: transparent;")
            ftr_layout.addWidget(lbl_nb)
            
        cat = self.note.get('category')
        if cat:
            tag_img = f"<img src='{os.path.join(icons_dir, 'tag_dark.svg')}' width='12' height='12'>"
            lbl_cat = QLabel(f"{tag_img} {cat}")
            lbl_cat.setStyleSheet("font-size: 10px; color: #555555; font-style: italic; border: none; background: transparent;")
            ftr_layout.addWidget(lbl_cat)

        ftr_layout.addStretch()
        layout.addLayout(ftr_layout)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.note)


class NotesLeftView(QWidget):
    """Vista de la página izquierda (Lista de Notas)."""
    
    note_selected = pyqtSignal(dict)
    edit_note_props_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.notes = []
        self.notebooks = []
        self.active_notebook_id = None
        self.active_type_filter = 'all'
        self.search_query = ''
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 15, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        hdr_frame = QFrame()
        hdr_frame.setFixedHeight(32)
        hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        notes_img = f"<img src='{os.path.join(icons_dir, 'notes_dark.svg')}' width='15' height='15'>"
        title = QLabel(f"{notes_img} Lista y Colección de Notas")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(title)
        layout.addWidget(hdr_frame)

        # Área Scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll, 1)

    def set_data(self, notebooks: list, notes: list, active_notebook_id=None, type_filter='all', search_query=''):
        self.notebooks = notebooks
        self.notes = notes
        self.active_notebook_id = active_notebook_id
        self.active_type_filter = type_filter
        self.search_query = search_query.lower().strip()
        self._refresh()

    def _refresh(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

        nb_map = {nb.get('id'): nb.get('title') for nb in self.notebooks}

        filtered = []
        for n in self.notes:
            # Filtro cuaderno
            if self.active_notebook_id and n.get('notebook_id') != self.active_notebook_id:
                continue
            # Filtro tipo
            if self.active_type_filter != 'all' and n.get('type') != self.active_type_filter:
                continue
            # Buscador
            if self.search_query:
                t_match = self.search_query in n.get('title', '').lower()
                c_match = self.search_query in n.get('category', '').lower()
                if not (t_match or c_match):
                    continue
            filtered.append(n)

        if not filtered:
            lbl_empty = QLabel("No se encontraron notas en esta categoría.")
            lbl_empty.setStyleSheet("color: #666666; font-style: italic; font-size: 12px; padding: 20px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl_empty)
        else:
            for n in filtered:
                nb_name = nb_map.get(n.get('notebook_id'), '')
                card = NoteCardWidget(n, notebook_name=nb_name)
                card.selected.connect(self.note_selected.emit)
                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()


class NotesRightView(QWidget):
    """Vista de la página derecha (Editor dinámico de notas)."""

    content_saved = pyqtSignal(dict)
    edit_props_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.current_note = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 25, 15)
        layout.setSpacing(10)

        # Cabecera con título de nota activa y botón de propiedades
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.lbl_note_title = QLabel("Selecciona una nota")
        self.lbl_note_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_note_title, 1)

        self.btn_props = QPushButton("Propiedades")
        self.btn_props.setIcon(QIcon(os.path.join(icons_dir, 'settings.svg')))
        self.btn_props.setToolTip("Editar título, cuaderno o etiqueta de esta nota")
        self.btn_props.setStyleSheet("QPushButton { border: 1px solid #CCC; background: #F0F0F0; font-weight: bold; color: #333333; padding: 4px 8px; border-radius: 4px; } QPushButton:hover { background-color: #E0E0E0; }")
        self.btn_props.clicked.connect(lambda: self.edit_props_requested.emit(self.current_note) if self.current_note else None)
        hdr_layout.addWidget(self.btn_props)
        layout.addWidget(self.hdr_frame)

        # Stack de editores
        self.stack = QStackedWidget()
        
        # 0. Placeholder (Sin nota)
        self.empty_widget = QLabel("Selecciona o crea una nota para comenzar a editar.")
        self.empty_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_widget.setStyleSheet("color: #666666; font-size: 14px; font-style: italic;")
        self.stack.addWidget(self.empty_widget)

        # 1. Editor Texto Plano
        self.text_editor = QTextEdit()
        self.text_editor.setStyleSheet("QTextEdit { background-color: rgba(255,255,255,0.8); border: 1px solid #D0C070; border-radius: 6px; font-size: 13px; padding: 10px; color: #111111; }")
        self.text_editor.textChanged.connect(self._on_text_changed)
        self.stack.addWidget(self.text_editor)

        # 2. Editor Markdown (Editor + Preview)
        self.md_container = QWidget()
        md_layout = QVBoxLayout(self.md_container)
        md_layout.setContentsMargins(0, 0, 0, 0)
        
        md_tb = QHBoxLayout()
        self.btn_md_edit = QPushButton(" Editar Markdown")
        self.btn_md_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil_dark.svg')))
        self.btn_md_preview = QPushButton(" Vista Previa")
        for b in (self.btn_md_edit, self.btn_md_preview):
            b.setCheckable(True)
            b.setStyleSheet("QPushButton { padding: 4px 10px; border-radius: 4px; background: rgba(255,255,255,0.6); font-weight: bold; } QPushButton:checked { background: #4682B4; color: white; }")
        self.btn_md_edit.setChecked(True)
        self.btn_md_edit.clicked.connect(lambda: self._switch_md_view(0))
        self.btn_md_preview.clicked.connect(lambda: self._switch_md_view(1))
        md_tb.addWidget(self.btn_md_edit)
        md_tb.addWidget(self.btn_md_preview)
        md_tb.addStretch()
        md_layout.addLayout(md_tb)

        self.md_stack = QStackedWidget()
        self.md_input = QTextEdit()
        self.md_input.setStyleSheet("QTextEdit { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; font-family: monospace; font-size: 12px; padding: 10px; color: #111111; }")
        self.md_input.textChanged.connect(self._on_md_changed)
        
        self.md_preview = QTextEdit()
        self.md_preview.setReadOnly(True)
        self.md_preview.setStyleSheet("QTextEdit { background-color: rgba(255,255,255,0.95); border: 1px solid #D0C070; border-radius: 6px; padding: 12px; color: #111111; }")
        
        self.md_stack.addWidget(self.md_input)
        self.md_stack.addWidget(self.md_preview)
        md_layout.addWidget(self.md_stack, 1)
        self.stack.addWidget(self.md_container)

        # 3. Editor Enlaces Web
        self.links_container = QWidget()
        links_layout = QVBoxLayout(self.links_container)
        links_layout.setContentsMargins(0, 0, 0, 0)
        
        links_tb = QHBoxLayout()
        btn_add_link = QPushButton(" Agregar Enlace Web")
        btn_add_link.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        btn_add_link.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }")
        btn_add_link.clicked.connect(self._on_add_link)
        links_tb.addWidget(btn_add_link)
        links_tb.addStretch()
        links_layout.addLayout(links_tb)

        self.links_table = QTableWidget()
        self.links_table.setColumnCount(4)
        self.links_table.setHorizontalHeaderLabels(["Categoría", "Título", "URL", "Acción"])
        self.links_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.links_table.setStyleSheet("QTableWidget { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; }")
        links_layout.addWidget(self.links_table, 1)
        self.stack.addWidget(self.links_container)

        # 4. Editor Imagen
        self.img_container = QWidget()
        img_layout = QVBoxLayout(self.img_container)
        img_layout.setContentsMargins(0, 0, 0, 0)
        
        img_tb = QHBoxLayout()
        btn_load_img = QPushButton(" Seleccionar Imagen...")
        btn_load_img.setIcon(QIcon(os.path.join(icons_dir, 'image_file.svg')))
        btn_load_img.setStyleSheet("QPushButton { background-color: #4682B4; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }")
        btn_load_img.clicked.connect(self._on_select_image)
        img_tb.addWidget(btn_load_img)
        img_tb.addStretch()
        img_layout.addLayout(img_tb)

        self.lbl_img_preview = QLabel("No hay imagen cargada.")
        self.lbl_img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_img_preview.setStyleSheet("QLabel { background-color: rgba(255,255,255,0.85); border: 1px dashed #D0C070; border-radius: 6px; }")
        img_layout.addWidget(self.lbl_img_preview, 1)
        self.stack.addWidget(self.img_container)

        # 5. Editor Mano Alzada (Canvas)
        self.canvas_widget = HandwritingCanvasWidget()
        self.canvas_widget.canvas_changed.connect(self._on_canvas_changed)
        self.stack.addWidget(self.canvas_widget)

        layout.addWidget(self.stack, 1)

    def set_note(self, note: dict):
        self.current_note = note
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        if not note:
            self.lbl_note_title.setText("Selecciona una nota")
            self.stack.setCurrentIndex(0)
            return

        type_icons = {
            'text': 'document_dark.svg',
            'markdown': 'manual_dark.svg',
            'links': 'link_dark.svg',
            'image': 'image_file_dark.svg',
            'handwriting': 'pencil_dark.svg'
        }
        icon_file = type_icons.get(note.get('type'), 'document.svg')
        icon_img = f"<img src='{os.path.join(icons_dir, icon_file)}' width='15' height='15'>"
        self.lbl_note_title.setText(f"{icon_img} <b>{note.get('title', 'Sin Título')}</b>")

        n_type = note.get('type', 'text')
        content = note.get('content', '')

        if n_type == 'text':
            self.text_editor.blockSignals(True)
            self.text_editor.setText(str(content) if content else "")
            self.text_editor.blockSignals(False)
            self.stack.setCurrentIndex(1)

        elif n_type == 'markdown':
            self.md_input.blockSignals(True)
            self.md_input.setText(str(content) if content else "")
            self.md_input.blockSignals(False)
            self.md_preview.setMarkdown(str(content) if content else "")
            self._switch_md_view(0)
            self.stack.setCurrentIndex(2)

        elif n_type == 'links':
            self._refresh_links_table(content if isinstance(content, list) else [])
            self.stack.setCurrentIndex(3)

        elif n_type == 'image':
            if content and isinstance(content, str) and content.startswith("data:image"):
                try:
                    b64_data = content.split(",")[1]
                    raw = base64.b64decode(b64_data)
                    pix = QPixmap()
                    pix.loadFromData(raw)
                    self.lbl_img_preview.setPixmap(pix.scaled(450, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                except Exception as e:
                    self.lbl_img_preview.setText(f"Error cargando imagen: {e}")
            else:
                self.lbl_img_preview.setText("No hay imagen cargada. Presiona 'Seleccionar Imagen...'")
            self.stack.setCurrentIndex(4)

        elif n_type == 'handwriting':
            self.canvas_widget.load_image_base64(str(content) if content else "")
            self.stack.setCurrentIndex(5)

    def _switch_md_view(self, idx):
        self.btn_md_edit.setChecked(idx == 0)
        self.btn_md_preview.setChecked(idx == 1)
        if idx == 1:
            self.md_preview.setMarkdown(self.md_input.toPlainText())
        self.md_stack.setCurrentIndex(idx)

    def _on_text_changed(self):
        if self.current_note and self.current_note.get('type') == 'text':
            self.current_note['content'] = self.text_editor.toPlainText()
            self.current_note['updated_at'] = QDate.currentDate().toString("dd/MM/yyyy")
            self.content_saved.emit(self.current_note)

    def _on_md_changed(self):
        if self.current_note and self.current_note.get('type') == 'markdown':
            self.current_note['content'] = self.md_input.toPlainText()
            self.current_note['updated_at'] = QDate.currentDate().toString("dd/MM/yyyy")
            self.content_saved.emit(self.current_note)

    def _on_canvas_changed(self):
        if self.current_note and self.current_note.get('type') == 'handwriting':
            self.current_note['content'] = self.canvas_widget.get_image_base64()
            self.current_note['updated_at'] = QDate.currentDate().toString("dd/MM/yyyy")
            self.content_saved.emit(self.current_note)

    def _refresh_links_table(self, links_list: list):
        self.links_table.setRowCount(0)
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        for i, l in enumerate(links_list):
            self.links_table.insertRow(i)
            self.links_table.setItem(i, 0, QTableWidgetItem(l.get('category', 'General')))
            self.links_table.setItem(i, 1, QTableWidgetItem(l.get('title', '')))
            self.links_table.setItem(i, 2, QTableWidgetItem(l.get('url', '')))
            
            btn_open = QPushButton("Abrir")
            btn_open.setIcon(QIcon(os.path.join(icons_dir, 'link.svg')))
            btn_open.setStyleSheet("QPushButton { background-color: #1e88e5; color: white; border-radius: 3px; font-size: 11px; padding: 2px 6px; }")
            url = l.get('url', '')
            btn_open.clicked.connect(lambda checked, u=url: QDesktopServices.openUrl(QUrl(u)))
            self.links_table.setCellWidget(i, 3, btn_open)

    def _on_add_link(self):
        if not self.current_note or self.current_note.get('type') != 'links':
            return
        links = self.current_note.get('content')
        if not isinstance(links, list):
            links = []
        cats = list(set(l.get('category', 'General') for l in links))
        dlg = LinkDialog(categories=cats, parent=self)
        if dlg.exec() and dlg.link_data:
            links.append(dlg.link_data)
            self.current_note['content'] = links
            self.current_note['updated_at'] = QDate.currentDate().toString("dd/MM/yyyy")
            self._refresh_links_table(links)
            self.content_saved.emit(self.current_note)

    def _on_select_image(self):
        if not self.current_note or self.current_note.get('type') != 'image':
            return
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", IMAGE_FILE_FILTER)
        if path:
            try:
                pix = load_image_pixmap(path)
                if not pix.isNull():
                    from PyQt6.QtCore import QBuffer, QIODevice
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    pix.save(buffer, "PNG")
                    encoded = base64.b64encode(buffer.data().data()).decode('utf-8')
                    data_uri = f"data:image/png;base64,{encoded}"
                    self.current_note['content'] = data_uri
                    self.current_note['updated_at'] = QDate.currentDate().toString("dd/MM/yyyy")
                    self.lbl_img_preview.setPixmap(pix.scaled(450, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.content_saved.emit(self.current_note)
            except Exception as e:
                print(f"Error cargando imagen: {e}")


class NotasSidebar(QWidget):
    """Barra lateral para la sección de Notas."""
    
    filter_type_changed = pyqtSignal(str)
    filter_notebook_changed = pyqtSignal(str) # notebook_id
    search_changed = pyqtSignal(str)
    add_note_clicked = pyqtSignal()
    add_notebook_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.notebooks = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        # 1. Botón Nueva Nota y Nuevo Cuaderno
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        btn_add_note = QPushButton(" Nueva Nota")
        btn_add_note.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        btn_add_nb = QPushButton(" Nuevo Cuaderno")
        btn_add_nb.setIcon(QIcon(os.path.join(icons_dir, 'manual.svg')))

        btn_style = """
            QPushButton { text-align: left; padding: 8px 12px; border-radius: 6px; background-color: rgba(255, 255, 255, 0.08); color: #ffffff; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """
        btn_add_note.setStyleSheet(btn_style)
        btn_add_nb.setStyleSheet(btn_style)

        btn_add_note.clicked.connect(self.add_note_clicked.emit)
        btn_add_nb.clicked.connect(self.add_notebook_clicked.emit)

        actions_layout.addWidget(btn_add_note)
        actions_layout.addWidget(btn_add_nb)
        layout.addLayout(actions_layout)

        # 2. Buscador
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar nota...")
        self.search_input.setStyleSheet("QLineEdit { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px 8px; }")
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        # 3. Filtros por Tipo
        lbl_type = QLabel("Tipos de Nota")
        lbl_type.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_type)

        types_layout = QVBoxLayout()
        types_layout.setSpacing(2)
        self.type_group = QButtonGroup(self)
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        type_filters = [
            ('all', ' Todas las notas', 'notes.svg'),
            ('text', ' Texto Plano', 'document.svg'),
            ('markdown', ' Markdown', 'manual.svg'),
            ('links', ' Enlaces Web', 'link.svg'),
            ('image', ' Gráficas', 'image_file.svg'),
            ('handwriting', ' Mano Alzada', 'pencil.svg')
        ]
        for i, (tf_id, tf_name, tf_icon) in enumerate(type_filters):
            btn = QPushButton(tf_name)
            btn.setIcon(QIcon(os.path.join(icons_dir, tf_icon)))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 4px 8px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; font-size: 12px; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #f9e2af; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)
            btn.clicked.connect(lambda checked, t=tf_id: self.filter_type_changed.emit(t))
            self.type_group.addButton(btn, i)
            types_layout.addWidget(btn)
            if tf_id == 'all': btn.setChecked(True)
        layout.addLayout(types_layout)

        # 4. Cuadernos / Listas
        lbl_nb = QLabel("Cuadernos")
        lbl_nb.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px; margin-top: 6px;")
        layout.addWidget(lbl_nb)

        self.nb_combo = QComboBox()
        self.nb_combo.setStyleSheet("QComboBox { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px; }")
        self.nb_combo.addItem("📂 Todos los cuadernos", None)
        self.nb_combo.currentIndexChanged.connect(self._on_nb_combo_changed)
        layout.addWidget(self.nb_combo)

        layout.addStretch()

        # 5. Botón de engranaje inferior izquierdo
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configuración de Notas")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def set_notebooks(self, notebooks: list):
        self.notebooks = notebooks
        self.nb_combo.blockSignals(True)
        curr_data = self.nb_combo.currentData()
        self.nb_combo.clear()
        self.nb_combo.addItem("📂 Todos los cuadernos", None)
        sel_idx = 0
        for i, nb in enumerate(notebooks):
            self.nb_combo.addItem(f"📓 {nb.get('title')}", nb.get('id'))
            if curr_data and curr_data == nb.get('id'):
                sel_idx = i + 1
        self.nb_combo.setCurrentIndex(sel_idx)
        self.nb_combo.blockSignals(False)

    def _on_nb_combo_changed(self, idx):
        nb_id = self.nb_combo.currentData()
        self.filter_notebook_changed.emit(nb_id)


class NotasPlugin(PluginBase):
    """Plugin para la sección de Notas."""

    trash_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._data = {'notebooks': [], 'notes': [], '_trash': []}
        self._trash = []
        self._is_modified = False
        self.active_notebook_id = None
        self.active_type_filter = 'all'
        self.search_query = ''

        # Sidebar
        self._sidebar = NotasSidebar()
        self._sidebar.filter_type_changed.connect(self._on_type_filter_changed)
        self._sidebar.filter_notebook_changed.connect(self._on_nb_filter_changed)
        self._sidebar.search_changed.connect(self._on_search_changed)
        self._sidebar.add_note_clicked.connect(self._on_add_note)
        self._sidebar.add_notebook_clicked.connect(self._on_add_notebook)
        self._sidebar.settings_clicked.connect(self._on_show_settings)

        # Pages
        self._left_page = NotesLeftView()
        self._right_page = NotesRightView()

        self._left_page.note_selected.connect(self._on_note_selected)
        self._right_page.content_saved.connect(self._on_content_saved)
        self._right_page.edit_props_requested.connect(self._on_edit_note_props)

    def _update_views(self):
        notebooks = self._data.get('notebooks', [])
        notes = self._data.get('notes', [])
        self._sidebar.set_notebooks(notebooks)
        self._left_page.set_data(notebooks, notes, self.active_notebook_id, self.active_type_filter, self.search_query)

    def _on_type_filter_changed(self, tf_id: str):
        self.active_type_filter = tf_id
        self._update_views()

    def _on_nb_filter_changed(self, nb_id: str):
        self.active_notebook_id = nb_id
        self._update_views()

    def _on_search_changed(self, query: str):
        self.search_query = query
        self._update_views()

    def _on_note_selected(self, note: dict):
        self._right_page.set_note(note)

    def _on_content_saved(self, note: dict):
        self._is_modified = True
        self._update_views()

    def _on_add_note(self):
        notebooks = self._data.get('notebooks', [])
        dlg = NoteDialog(notebooks=notebooks, selected_notebook_id=self.active_notebook_id, parent=self._sidebar)
        if dlg.exec() and dlg.note_data:
            self._data.setdefault('notes', []).append(dlg.note_data)
            self._is_modified = True
            self._update_views()
            self._right_page.set_note(dlg.note_data)

    def _on_add_notebook(self):
        dlg = NotebookDialog(parent=self._sidebar)
        if dlg.exec() and dlg.notebook_data:
            self._data.setdefault('notebooks', []).append(dlg.notebook_data)
            self._is_modified = True
            self._update_views()

    def _on_edit_note_props(self, note_dict: dict):
        if not note_dict: return
        notebooks = self._data.get('notebooks', [])
        dlg = NoteDialog(notebooks=notebooks, note_to_edit=note_dict, parent=self._sidebar)
        if dlg.exec():
            notes = self._data.get('notes', [])
            if dlg.is_delete:
                if note_dict in notes:
                    notes.remove(note_dict)
                    self.move_to_trash(note_dict)
                    self._is_modified = True
                    self._update_views()
                    self._right_page.set_note(None)
                    self.trash_changed.emit()
            elif dlg.note_data:
                idx = notes.index(note_dict) if note_dict in notes else -1
                if idx >= 0:
                    notes[idx] = dlg.note_data
                self._is_modified = True
                self._update_views()
                self._right_page.set_note(dlg.note_data)

    def _on_show_settings(self):
        dlg = NoteSettingsDialog(parent=self._sidebar)
        dlg.exec()

    # --- Papelera ---
    def move_to_trash(self, item: dict):
        self._trash.append(item)

    def get_trash_items(self) -> list:
        return self._trash

    def restore_item(self, index: int):
        if 0 <= index < len(self._trash):
            item = self._trash.pop(index)
            self._data.setdefault('notes', []).append(item)
            self._is_modified = True
            self._update_views()
            self.trash_changed.emit()

    def get_name(self) -> str: return "Notas"
    def get_id(self) -> str: return "notas"
    def get_icon(self) -> str: return "notes.svg"
    def get_tab_color(self) -> str: return "#4682B4"
    def get_order(self) -> int: return 4

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

    def load_data(self, agenda_path: str):
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
            self._trash = loaded.get('_trash', [])
        self._update_views()
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            DataStore.save(data_path, self._data)
            self._is_modified = False
