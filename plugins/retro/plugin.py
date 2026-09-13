# =============================================================================
# Vito Organizer v2.11 - Retro Plugin
# Gestor de Colección Retro: Equipos, Medios, Periféricos y Modificaciones
# =============================================================================

import os
import shutil
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QUrl, QTime
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QDesktopServices, QPainter
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QButtonGroup, QLineEdit,
    QStackedWidget, QSizePolicy, QTableWidget, QTableWidgetItem, QHeaderView, QMenu
)

from plugins.plugin_base import PluginBase, open_local_file, load_image_pixmap, IMAGE_EXTENSIONS
from data.data_store import DataStore
from plugins.retro.dialogs import (
    ComputerDialog, MediaDialog, PeripheralDialog, ModificationDialog, 
    RetroSettingsDialog, RetroDocumentDialog, RetroRomDialog
)
from plugins.laboratorio.dialogs import ProjectDialog, ProjectCalculationDialog
from plugins.retro.retro_editors import (
    CodeEditorWidget, MindMapEditorWidget, FlowchartEditorWidget,
    PaintEditorWidget, STL3DViewerWidget, GerberKiCadViewerWidget,
    LibraryDocViewerWidget, SchematicEditorWidget
)

DEFAULT_LISTS = {
    'computer_types': [
        "Atari 8-bit", "Atari 16-bit", "Commodore 64", "Commodore Amiga",
        "ZX Spectrum", "MSX", "Amstrad CPC", "Apple II", "PC / MS-DOS", "Otro"
    ],
    'media_types': [
        "Cartridge / ROM", "Diskette 5.25\"", "Diskette 3.5\"", "Cassette", 
        "CD-ROM", "Flash Cart / SD", "Otro"
    ],
    'peripheral_types': [
        "Disk Drive", "Cassette Recorder", "Joystick / Gamepad", "Mouse",
        "Modem", "Impresora", "Monitor", "Expansión RAM", "SD / Modern Storage", "Otro"
    ],
    'modification_types': [
        "Video Mod (UAV/Sophia/S-Video)", "Audio Mod", "RAM Expansion",
        "OS / ROM Upgrade", "Repuesto (Custom Chip/IC)", "Mod de Fuente de Poder", "Otro"
    ],
    'conditions': [
        "Excelente / Mint", "Bueno / Con uso", "Regular / Desgaste visible", 
        "Malo / Roto", "Restaurado", "Amarillento / Yellowed"
    ],
    'statuses': [
        "100% Funcional", "Funciona parcialmente", "No enciende / Muerto", 
        "Requiere reparación", "No probado", "En restauración"
    ],
    'project_categories': [
        "Hardware", "Software / Firmware", "Diseño PCB",
        "Mecánica / 3D", "Investigación", "Restauración", "Otro"
    ]
}

class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class RetroSidebar(QWidget):
    module_changed = pyqtSignal(str)
    search_changed = pyqtSignal(str)
    add_computer_clicked = pyqtSignal()
    add_media_clicked = pyqtSignal()
    add_periph_clicked = pyqtSignal()
    add_mod_clicked = pyqtSignal()
    add_project_clicked = pyqtSignal()
    add_library_clicked = pyqtSignal()
    add_rom_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Botón único unificado con menú desplegable para nuevos elementos
        self.btn_new_item = QPushButton(" Nuevo Elemento")
        self.btn_new_item.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_new_item.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new_item.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 20px 6px 8px;
                border-radius: 5px;
                background-color: #d2691e;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton::menu-indicator {
                subcontrol-origin: padding;
                subcontrol-position: center right;
                right: 6px;
            }
        """)

        # Menú desplegable con los distintos elementos
        self.menu_new = QMenu(self.btn_new_item)
        self.menu_new.setStyleSheet("""
            QMenu {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 16px 6px 10px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }
            QMenu::item:selected {
                background-color: #45475a;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #313244;
                margin: 4px 6px;
            }
        """)

        act_comp = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'retro.svg')), "Nuevo Equipo / Consola")
        act_comp.triggered.connect(self.add_computer_clicked.emit)

        act_media = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'datasheet.svg')), "Nuevo Medio (Cartucho / Disco)")
        act_media.triggered.connect(self.add_media_clicked.emit)

        act_periph = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'tools.svg')), "Nuevo Periférico")
        act_periph.triggered.connect(self.add_periph_clicked.emit)

        act_mod = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'component.svg')), "Nueva Modificación / Repuesto")
        act_mod.triggered.connect(self.add_mod_clicked.emit)

        self.menu_new.addSeparator()

        act_proj = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'new_project.svg')), "Nuevo Proyecto / Desarrollo")
        act_proj.triggered.connect(self.add_project_clicked.emit)

        act_doc = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'library.svg')), "Nuevo Documento / Esquema")
        act_doc.triggered.connect(self.add_library_clicked.emit)

        act_rom = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'rom.svg')), "Nueva ROM / Dump")
        act_rom.triggered.connect(self.add_rom_clicked.emit)

        self.btn_new_item.setMenu(self.menu_new)
        layout.addWidget(self.btn_new_item)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.addAction(QIcon(os.path.join(icons_dir, 'search.svg')), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setStyleSheet("QLineEdit { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px 8px; }")
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        lbl_mod = QLabel("Módulos Retro")
        lbl_mod.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_mod)

        mods_layout = QVBoxLayout()
        mods_layout.setSpacing(2)
        self.mod_group = QButtonGroup(self)
        
        m_list = [
            ('computers', ' Equipos / Consolas', 'retro.svg'),
            ('media', ' Medios (Cartuchos)', 'datasheet.svg'),
            ('peripherals', ' Periféricos', 'tools.svg'),
            ('modifications', ' Mods / Repuestos', 'component.svg'),
            ('projects', ' Desarrollo y Mods', 'new_project.svg'),
            ('library', ' 📚 Biblioteca / Doc.', 'library.svg'),
            ('roms', ' 🕹️ Software y ROMs', 'rom.svg')
        ]
        for i, (mid, mname, micon) in enumerate(m_list):
            btn = QPushButton(mname)
            btn.setIcon(QIcon(os.path.join(icons_dir, micon)))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 5px 8px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; font-size: 11px; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #f9e2af; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)
            btn.clicked.connect(lambda checked, m=mid: self.module_changed.emit(m))
            self.mod_group.addButton(btn, i)
            mods_layout.addWidget(btn)
            if mid == 'computers': btn.setChecked(True)
        layout.addLayout(mods_layout)

        layout.addStretch()

        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(icons_dir, 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }")
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)


class RetroLeftView(QWidget):
    item_selected = pyqtSignal(dict, str)
    edit_item_requested = pyqtSignal(dict, str)
    pagination_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.items = []
        self.module_type = 'computers'
        self.search_query = ''
        self.page = 1
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 35, 15)
        layout.setSpacing(10)

        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_hdr_title = QLabel("Inventario Retro")
        self.lbl_hdr_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #D2691E; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_hdr_title)
        layout.addWidget(self.hdr_frame)

        self.stack = QStackedWidget()
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        
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
        self.list_layout.addWidget(self.scroll)
        self.stack.addWidget(self.list_container)

        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.editor_container)

        layout.addWidget(self.stack, 1)

    def set_data(self, items: list, module_type: str = 'computers', search_query: str = '', page: int = 1, sort_order: str = 'alpha_asc', show_filename: bool = True):
        self.items = items
        self.module_type = module_type
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
        if available_y <= 0: return
        card_step = 44
        new_items_per_page = max(1, available_y // card_step)
        
        if getattr(self, 'items_per_page', -1) != new_items_per_page:
            self.items_per_page = new_items_per_page
            self._refresh()
            self.pagination_changed.emit(self.page, self.get_total_pages())

    def _refresh(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        titles = {
            'computers': 'Equipos y Computadoras', 
            'media': 'Medios (Cartuchos/Discos)', 
            'peripherals': 'Periféricos y Expansiones', 
            'modifications': 'Modificaciones y Repuestos',
            'projects': 'Proyectos y Restauraciones',
            'library': 'Biblioteca Documental Retro',
            'roms': 'Almacenamiento de Software y ROMs'
        }
        self.lbl_hdr_title.setText(titles.get(self.module_type, 'Inventario Retro'))

        filtered = []
        for it in self.items:
            if self.search_query:
                name_match = self.search_query in it.get('name', '').lower()
                plat_match = self.search_query in it.get('platform', '').lower() or self.search_query in it.get('type', '').lower()
                loc_match = self.search_query in it.get('storage_location', '').lower() or self.search_query in it.get('filename', '').lower()
                if not (name_match or plat_match or loc_match): continue
            filtered.append(it)

        # Ordenar elementos
        sort_order = getattr(self, 'sort_order', 'alpha_asc')
        if sort_order == 'alpha_asc':
            filtered.sort(key=lambda x: str(x.get('name', '')).lower())
        elif sort_order == 'alpha_desc':
            filtered.sort(key=lambda x: str(x.get('name', '')).lower(), reverse=True)
        elif sort_order == 'date_asc':
            filtered.sort(key=lambda x: str(x.get('id', '')))
        elif sort_order == 'date_desc':
            filtered.sort(key=lambda x: str(x.get('id', '')), reverse=True)

        self.total_items = len(filtered)
        self.total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
        if self.page > self.total_pages: self.page = max(1, self.total_pages)
            
        start_idx = (self.page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered[start_idx:end_idx]

        if not page_items:
            lbl_empty = QLabel("No hay elementos registrados en esta categoría.")
            lbl_empty.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl_empty)
        else:
            icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
            for item in page_items:
                card = ClickableFrame()
                card.setFixedHeight(40)
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.75); border: 1px solid #CD853F; border-radius: 6px; } QFrame:hover { background-color: rgba(255,255,255,0.95); border-color: #FF8C00; }")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(10, 4, 10, 4)

                loc_img = f"<img src='{os.path.join(icons_dir, 'location.svg')}' width='13' height='13'>"

                if self.module_type == 'computers':
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Estado: <b>{item.get('status')}</b> | {loc_img} {item.get('storage_location', '')}</span>"
                elif self.module_type == 'media':
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Para: {item.get('platform')} | {loc_img} {item.get('storage_location', '')}</span>"
                elif self.module_type == 'peripherals':
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Plataforma: {item.get('platform')} | {loc_img} {item.get('storage_location', '')}</span>"
                elif self.module_type == 'projects':
                    lbl_txt = f"<b>{item.get('name')}</b><br><span style='color:#555; font-size:11px;'>Cat: <b>{item.get('category')}</b> | Docs: {len(item.get('calculations', []))}</span>"
                elif self.module_type == 'library':
                    assigned_cnt = len(item.get('assigned_element_ids', []))
                    show_fn = getattr(self, 'show_filename', True)
                    if show_fn:
                        lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Asignados: <b>{assigned_cnt} elementos</b> | {item.get('filename', '')}</span>"
                    else:
                        lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Asignados: <b>{assigned_cnt} elementos</b></span>"
                elif self.module_type == 'roms':
                    show_fn = getattr(self, 'show_filename', True)
                    if show_fn:
                        lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Plataforma: <b>{item.get('platform')}</b> | Archivo: {item.get('filename', '')}</span>"
                    else:
                        lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Plataforma: <b>{item.get('platform')}</b></span>"
                else:
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Plataforma: {item.get('platform')} | Stock: {item.get('stock_quantity',0)} | {loc_img} {item.get('storage_location', '')}</span>"

                lbl = QLabel(lbl_txt)
                lbl.setStyleSheet("border: none; background: transparent; color: #111111;")
                lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                c_layout.addWidget(lbl, 1)

                btn_edit = QPushButton("Editar")
                btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil.svg')))
                btn_edit.setFixedSize(65, 26)
                btn_edit.setStyleSheet("border: 1px solid #CCC; background: #F0F0F0; border-radius: 4px; font-size: 11px; font-weight: bold; color: #333;")
                btn_edit.clicked.connect(lambda checked, it=item: self.edit_item_requested.emit(it, self.module_type))
                c_layout.addWidget(btn_edit)

                card.clicked.connect(lambda checked=False, it=item: self.item_selected.emit(it, self.module_type))
                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()


class RetroRightView(QWidget):
    item_updated = pyqtSignal(dict, str)
    add_calculation_requested = pyqtSignal(dict)
    edit_calculation_requested = pyqtSignal(dict, dict)
    open_single_page_requested = pyqtSignal(dict, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.current_item = None
        self.module_type = 'computers'
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 15, 25, 15)
        layout.setSpacing(10)

        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_title = QLabel("Detalles")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #D2691E; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_title, 1)

        layout.addWidget(self.hdr_frame)
        self.stack = QStackedWidget()
        
        self.empty_lbl = QLabel("Selecciona un elemento de la lista para ver sus detalles.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        self.stack.addWidget(self.empty_lbl)

        self.detail_container = QWidget()
        d_layout = QVBoxLayout(self.detail_container)
        d_layout.setContentsMargins(0, 0, 0, 0)
        
        self.info_stack = QStackedWidget()
        
        # Ficha Tecnica
        self.tech_sheet_page = QWidget()
        ts_layout = QVBoxLayout(self.tech_sheet_page)
        ts_layout.setContentsMargins(0, 0, 0, 0)
        
        self.card_info = QFrame()
        self.card_info.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #CD853F; border-radius: 6px; padding: 10px; }")
        ci_layout = QVBoxLayout(self.card_info)

        # Previsualizador de Imagen / PDF
        self.img_preview = QLabel()
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setStyleSheet("border: 1px solid #CD853F; border-radius: 4px; background: #000000; margin-bottom: 8px;")
        self.img_preview.setFixedHeight(160)
        self.img_preview.setVisible(False)
        ci_layout.addWidget(self.img_preview)

        self.lbl_detail_text = QLabel()
        self.lbl_detail_text.setWordWrap(True)
        self.lbl_detail_text.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 13px;")
        self.lbl_detail_text.setAlignment(Qt.AlignmentFlag.AlignTop)
        ci_layout.addWidget(self.lbl_detail_text, 1)

        # Marco de Documentos de Biblioteca Asociados
        self.bib_files_frame = QFrame()
        self.bib_files_frame.setStyleSheet("QFrame { background-color: rgba(230,245,250,0.9); border: 1px solid #80CBC4; border-radius: 6px; padding: 6px; margin-top: 8px; }")
        self.bib_files_layout = QVBoxLayout(self.bib_files_frame)
        self.bib_files_layout.setContentsMargins(4, 4, 4, 4)
        self.bib_files_layout.setSpacing(4)
        self.lbl_bib_hdr = QLabel("<b>📚 Documentación y Archivos Asociados:</b>")
        self.lbl_bib_hdr.setStyleSheet("color: #004D40; font-size: 11px;")
        self.bib_files_layout.addWidget(self.lbl_bib_hdr)
        self.bib_files_frame.setVisible(False)
        ci_layout.addWidget(self.bib_files_frame)

        ts_layout.addWidget(self.card_info)
        self.info_stack.addWidget(self.tech_sheet_page)

        # Proyectos / Analisis
        self.analysis_page = QWidget()
        an_layout = QVBoxLayout(self.analysis_page)
        an_layout.setContentsMargins(0, 0, 0, 0)
        an_layout.setSpacing(10)
        
        self.lbl_an_summary = QLabel()
        self.lbl_an_summary.setWordWrap(True)
        self.lbl_an_summary.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 13px;")
        an_layout.addWidget(self.lbl_an_summary)
        
        an_hdr = QHBoxLayout()
        self.lbl_calc_section_title = QLabel("Documentos y Módulos")
        self.lbl_calc_section_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333333;")
        an_hdr.addWidget(self.lbl_calc_section_title)
        an_hdr.addStretch()
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.btn_add_calc = QPushButton(" Agregar Documento")
        self.btn_add_calc.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_calc.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; }")
        self.btn_add_calc.clicked.connect(lambda: self.add_calculation_requested.emit(self.current_item))
        an_hdr.addWidget(self.btn_add_calc)
        an_layout.addLayout(an_hdr)
        
        calc_scroll = QScrollArea()
        calc_scroll.setWidgetResizable(True)
        calc_scroll.setStyleSheet("QScrollArea { background-color: rgba(255,255,255,0.7); border: 1px solid #CCC; border-radius: 6px; }")
        self.calc_container = QWidget()
        self.calc_container.setStyleSheet("background: transparent;")
        self.calc_layout = QVBoxLayout(self.calc_container)
        self.calc_layout.setContentsMargins(5, 5, 5, 5)
        self.calc_layout.setSpacing(4)
        calc_scroll.setWidget(self.calc_container)
        an_layout.addWidget(calc_scroll, 1)

        self.info_stack.addWidget(self.analysis_page)
        
        d_layout.addWidget(self.info_stack, 1)
        self.stack.addWidget(self.detail_container)
        layout.addWidget(self.stack, 1)

    def set_item(self, item: dict, module_type: str, agenda_path: str = None, retro_data: dict = None):
        self.current_item = item
        self.module_type = module_type

        if not item:
            self.stack.setCurrentIndex(0)
            return

        self.stack.setCurrentIndex(1)
        if module_type == 'projects':
            self.info_stack.setCurrentIndex(1)
            self._refresh_calculations()
        else:
            self.info_stack.setCurrentIndex(0)

        self.img_preview.setVisible(False)
        self.bib_files_frame.setVisible(False)
        while self.bib_files_layout.count() > 1:
            child = self.bib_files_layout.takeAt(1)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                sub = child.layout()
                while sub.count():
                    c = sub.takeAt(0)
                    if c.widget():
                        c.widget().deleteLater()
                sub.deleteLater()

        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        cost = item.get('cost_value', 0.0)

        if module_type == 'computers':
            self.lbl_title.setText(f"Equipo: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#FF8C00;'>{item.get('name')}</h3>"
            txt += f"<b>Tipo/Plataforma:</b> {item.get('type')}<br>"
            txt += f"<b>Marca:</b> {item.get('brand')}<br>"
            txt += f"<b>Número de Serie:</b> {item.get('serial_number')}<br>"
            txt += f"<b>Lugar Almacenado:</b> {item.get('storage_location')}<br>"
            txt += f"<b>Condición Estética:</b> {item.get('condition')}<br>"
            txt += f"<b>Estado Funcional:</b> <b>{item.get('status')}</b><br>"
            txt += f"<b>Modificaciones:</b> {item.get('modifications')}<br>"
            txt += f"<b>Valor Estimado:</b> <span style='color: #2E8B57; font-weight:bold;'>{cost:.2f} {currency}</span><br>"
            txt += f"<br><b>Notas:</b><br>{item.get('notes')}<br>"
            self.lbl_detail_text.setText(txt)

        elif module_type == 'media':
            self.lbl_title.setText(f"Medio: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#8A2BE2;'>{item.get('name')}</h3>"
            txt += f"<b>Plataforma:</b> {item.get('platform')}<br>"
            txt += f"<b>Tipo de Medio:</b> {item.get('type')}<br>"
            txt += f"<b>Ubicación:</b> {item.get('storage_location')}<br>"
            txt += f"<b>Condición:</b> {item.get('condition')}<br>"
            txt += f"<b>Valor Estimado:</b> <span style='color: #2E8B57; font-weight:bold;'>{cost:.2f} {currency}</span><br>"
            txt += f"<br><b>Notas:</b><br>{item.get('notes')}<br>"
            self.lbl_detail_text.setText(txt)

        elif module_type == 'peripherals':
            self.lbl_title.setText(f"Periférico: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#008B8B;'>{item.get('name')}</h3>"
            txt += f"<b>Plataforma:</b> {item.get('platform')}<br>"
            txt += f"<b>Tipo:</b> {item.get('type')}<br>"
            txt += f"<b>Marca:</b> {item.get('brand')}<br>"
            txt += f"<b>Ubicación:</b> {item.get('storage_location')}<br>"
            txt += f"<b>Estado Funcional:</b> <b>{item.get('status')}</b><br>"
            txt += f"<br><b>Notas:</b><br>{item.get('notes')}<br>"
            self.lbl_detail_text.setText(txt)

        elif module_type == 'projects':
            self.lbl_title.setText("Resumen de Proyecto Retro")
            txt = f"<h3 style='margin:0; color:#8A2BE2;'>{item.get('name')}</h3>"
            txt += f"<b>Categoría:</b> {item.get('category')}<br>"
            txt += f"<b>Comentarios:</b><br><span style='color:#444;'>{item.get('comment', 'Sin comentarios.')}</span><br>"
            self.lbl_an_summary.setText(txt)

        elif module_type == 'library':
            self.lbl_title.setText(f"Documento: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#008080;'>{item.get('name')}</h3>"
            txt += f"<b>Tipo de Archivo:</b> {item.get('type')}<br>"
            txt += f"<b>Categoría Destino:</b> {item.get('target_category')}<br>"
            txt += f"<b>Archivo Físico:</b> {item.get('filename')}<br>"
            txt += f"<br><b>Descripción:</b><br>{item.get('description', 'Sin descripción.')}<br>"

            assigned_ids = item.get('assigned_element_ids', [])
            assigned_names = []
            if retro_data:
                for cat in ['computers', 'media', 'peripherals', 'modifications', 'projects']:
                    for el in retro_data.get(cat, []):
                        if el.get('id') in assigned_ids or el.get('name') in assigned_ids:
                            assigned_names.append(f"• {el.get('name')} ({cat})")

            if assigned_names:
                txt += f"<br><b>Elementos Asignados:</b><br>" + "<br>".join(assigned_names) + "<br>"
            else:
                txt += "<br><i>No asignado a ningún elemento específico.</i><br>"

            self.lbl_detail_text.setText(txt)

            full_path = None
            if agenda_path and item.get('relative_path'):
                full_path = os.path.join(agenda_path, item.get('relative_path'))

            if full_path and os.path.exists(full_path):
                if item.get('type') == 'Imágenes' or full_path.lower().endswith(IMAGE_EXTENSIONS):
                    pix = load_image_pixmap(full_path)
                    if not pix.isNull():
                        self.img_preview.setPixmap(pix.scaled(320, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        self.img_preview.setVisible(True)
                elif full_path.lower().endswith('.pdf'):
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
                            self.img_preview.setPixmap(pixmap.scaled(320, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            self.img_preview.setVisible(True)
                    except Exception:
                        pass

                self.bib_files_frame.setVisible(True)
                btn_open = QPushButton(f"📂 Abrir Archivo Físico ({item.get('filename')})")
                btn_open.setStyleSheet("QPushButton { text-align: left; background: #004D40; color: #ffffff; font-weight: bold; padding: 6px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #00796B; }")
                btn_open.clicked.connect(lambda checked, p=full_path: open_local_file(p))
                self.bib_files_layout.addWidget(btn_open)

        elif module_type == 'roms':
            self.lbl_title.setText(f"ROM / Software: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#DAA520;'>{item.get('name')}</h3>"
            txt += f"<b>Tipo de Volcado:</b> {item.get('type')}<br>"
            txt += f"<b>Plataforma:</b> {item.get('platform')}<br>"
            txt += f"<b>Archivo ROM/Dump:</b> {item.get('filename')}<br>"

            assigned_m_id = item.get('assigned_media_id')
            if assigned_m_id and retro_data:
                media_list = retro_data.get('media', [])
                m_obj = next((m for m in media_list if m.get('id') == assigned_m_id or m.get('name') == assigned_m_id), None)
                if m_obj:
                    txt += f"<b>Medio Físico Asociado:</b> <b>{m_obj.get('name')} ({m_obj.get('platform')})</b><br>"
                else:
                    txt += f"<b>Medio Físico Asociado:</b> <i>{assigned_m_id}</i><br>"
            else:
                txt += "<b>Medio Físico Asociado:</b> <i>Ninguno / Software Digital</i><br>"

            txt += f"<br><b>Notas / Descripción:</b><br>{item.get('notes', 'Sin notas.')}<br>"
            self.lbl_detail_text.setText(txt)

            img_rel = item.get('image_relative_path')
            if img_rel and agenda_path:
                full_img_p = os.path.join(agenda_path, img_rel)
                if os.path.exists(full_img_p):
                    pix = QPixmap(full_img_p)
                    if not pix.isNull():
                        self.img_preview.setPixmap(pix.scaled(320, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        self.img_preview.setVisible(True)

            full_rom_p = None
            if agenda_path and item.get('relative_path'):
                full_rom_p = os.path.join(agenda_path, item.get('relative_path'))

            if full_rom_p and os.path.exists(full_rom_p):
                self.bib_files_frame.setVisible(True)
                
                rom_btns_layout = QHBoxLayout()
                
                btn_rom_open = QPushButton(f"🕹️ Abrir Archivo de ROM / Dump ({item.get('filename')})")
                btn_rom_open.setStyleSheet("QPushButton { text-align: left; background: #B8860B; color: #ffffff; font-weight: bold; padding: 6px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #DAA520; }")
                btn_rom_open.clicked.connect(lambda checked, p=full_rom_p: open_local_file(p))
                rom_btns_layout.addWidget(btn_rom_open, 1)
                
                btn_rom_download = QPushButton("Descargar / Exportar")
                btn_rom_download.setStyleSheet("QPushButton { background: #4682B4; color: #ffffff; font-weight: bold; padding: 6px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #5F9EA0; }")
                btn_rom_download.clicked.connect(lambda checked, p=full_rom_p, fn=item.get('filename', 'rom.bin'): self._download_file(p, fn))
                rom_btns_layout.addWidget(btn_rom_download)
                
                self.bib_files_layout.addLayout(rom_btns_layout)

        else: # modifications
            self.lbl_title.setText(f"Modificación: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#B22222;'>{item.get('name')}</h3>"
            txt += f"<b>Plataforma:</b> {item.get('platform')}<br>"
            txt += f"<b>Tipo de Mod:</b> {item.get('type')}<br>"
            txt += f"<b>Ubicación:</b> {item.get('storage_location')}<br>"
            txt += f"<b>Stock disponible:</b> <b>{item.get('stock_quantity', 0)}</b><br>"
            txt += f"<br><b>Notas de Instalación:</b><br>{item.get('notes')}<br>"
            self.lbl_detail_text.setText(txt)

        # Buscar imágenes y documentos asignados a este elemento desde la Biblioteca Retro
        if module_type != 'library' and retro_data and agenda_path:
            library_docs = retro_data.get('library', [])
            item_id = item.get('id')
            item_name = item.get('name')
            assigned_docs = []
            bib_img_path = None

            for doc in library_docs:
                a_ids = doc.get('assigned_element_ids', [])
                if item_id in a_ids or item_name in a_ids:
                    rel = doc.get('relative_path', '')
                    full = os.path.join(agenda_path, rel) if rel else None
                    if full and os.path.exists(full):
                        if not bib_img_path and (doc.get('type') == 'Imágenes' or rel.lower().endswith(IMAGE_EXTENSIONS)):
                            bib_img_path = full
                        else:
                            assigned_docs.append((doc.get('name'), doc.get('type'), full))

            preview_loaded = False
            if bib_img_path and os.path.exists(bib_img_path):
                pix = load_image_pixmap(bib_img_path)
                if not pix.isNull():
                    self.img_preview.setPixmap(pix.scaled(320, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.img_preview.setVisible(True)
                    preview_loaded = True

            if not preview_loaded:
                for d_name, d_type, d_path in assigned_docs:
                    if d_path.lower().endswith('.pdf'):
                        try:
                            import fitz
                            from PyQt6.QtGui import QImage
                            doc = fitz.open(d_path)
                            if len(doc) > 0:
                                page = doc[0]
                                pix = page.get_pixmap(dpi=100)
                                fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
                                qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                                pixmap = QPixmap.fromImage(qimg.copy())
                                self.img_preview.setPixmap(pixmap.scaled(320, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                                self.img_preview.setVisible(True)
                                preview_loaded = True
                                break
                        except Exception:
                            pass

            if assigned_docs:
                self.bib_files_frame.setVisible(True)
                for d_name, d_type, d_path in assigned_docs:
                    btn_d = QPushButton(f"{d_type} - {d_name}")
                    btn_d.setStyleSheet("QPushButton { text-align: left; background: #E0F2F1; color: #004D40; font-weight: bold; padding: 4px 8px; border: 1px solid #80CBC4; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #B2DFDB; }")
                    btn_d.clicked.connect(lambda checked, p=d_path: open_local_file(p))
                    self.bib_files_layout.addWidget(btn_d)

            if module_type == 'media' and retro_data and agenda_path:
                roms = retro_data.get('roms', [])
                assigned_roms = []
                for r in roms:
                    if r.get('assigned_media_id') in [item.get('id'), item.get('name')]:
                        assigned_roms.append(r)
                if assigned_roms:
                    self.bib_files_frame.setVisible(True)
                    for r in assigned_roms:
                        full_rom_p = None
                        if r.get('relative_path'):
                            full_rom_p = os.path.join(agenda_path, r.get('relative_path'))
                        if full_rom_p and os.path.exists(full_rom_p):
                            r_layout = QHBoxLayout()
                            
                            btn_r = QPushButton(f"🕹️ ROM: {r.get('name')} ({r.get('filename')})")
                            btn_r.setStyleSheet("QPushButton { text-align: left; background: #B8860B; color: #ffffff; font-weight: bold; padding: 4px 8px; border: 1px solid #DAA520; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #DAA520; }")
                            btn_r.clicked.connect(lambda checked, p=full_rom_p: open_local_file(p))
                            r_layout.addWidget(btn_r, 1)
                            
                            btn_r_down = QPushButton("Descargar / Exportar")
                            btn_r_down.setStyleSheet("QPushButton { background: #4682B4; color: #ffffff; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #5F9EA0; }")
                            btn_r_down.clicked.connect(lambda checked, p=full_rom_p, fn=r.get('filename', 'rom.bin'): self._download_file(p, fn))
                            r_layout.addWidget(btn_r_down)
                            
                            self.bib_files_layout.addLayout(r_layout)

    def _refresh_calculations(self):
        while self.calc_layout.count():
            child = self.calc_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()
                
        if not self.current_item: return
        calcs = self.current_item.get('calculations', [])
        if not calcs:
            lbl = QLabel("No hay documentos agregados aún.")
            lbl.setStyleSheet("color: #666; font-style: italic;")
            self.calc_layout.addWidget(lbl)
        else:
            icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
            for calc in calcs:
                card = ClickableFrame()
                card.setFixedHeight(45)
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #CCC; border-radius: 4px; } QFrame:hover { border-color: #8A2BE2; background-color: #F8F0FF; }")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(10, 5, 10, 5)
                
                type_map = {
                    'Texto': 'document.svg', 'Imagen': 'image_file.svg', 'Markdown (MD)': 'edit.svg',
                    'Texto Enriquecido': 'edit.svg', 'Editor de Código': 'document.svg',
                    'Mapa Mental': 'planner.svg', 'Diagrama de Flujo (Draw.io)': 'edit.svg',
                    'Dibujo / Paint': 'edit.svg', 'Visor 3D STL / G-Code': 'box.svg',
                    'Visor KiCad / Gerber': 'component.svg', 'Editor de Diagramas Esquemáticos': 'component.svg',
                    'Documentación Biblioteca': 'library.svg'
                }
                icon_file = type_map.get(calc.get('type'), 'document.svg')
                
                icon_lbl = QLabel()
                icon_lbl.setFixedSize(20, 20)
                icon_lbl.setStyleSheet("border: none; background: transparent;")
                
                svg_path = os.path.join(icons_dir, icon_file)
                if os.path.exists(svg_path):
                    pm = QPixmap(svg_path).scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    if not pm.isNull():
                        p = QPainter(pm)
                        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                        p.fillRect(pm.rect(), QColor("#8A2BE2"))
                        p.end()
                        icon_lbl.setPixmap(pm)
                c_layout.addWidget(icon_lbl)
                
                lbl = QLabel(f"<b>{calc.get('name')}</b><br><span style='color:#666; font-size:10px;'>Tipo: {calc.get('type')}</span>")
                lbl.setStyleSheet("border: none; background: transparent; color: #111111;")
                c_layout.addWidget(lbl, 1)
                
                btn_edit = QPushButton("Editar")
                btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil.svg')))
                btn_edit.setFixedSize(65, 26)
                btn_edit.setStyleSheet("border: 1px solid #CCC; background: #F0F0F0; border-radius: 4px; font-size: 11px; font-weight: bold; color: #333;")
                btn_edit.clicked.connect(lambda checked, c=calc, a=self.current_item: self.edit_calculation_requested.emit(c, a))
                c_layout.addWidget(btn_edit)
                
                card.clicked.connect(lambda checked=False, c=calc, a=self.current_item: self.open_single_page_requested.emit(c, a))
                self.calc_layout.addWidget(card)
        self.calc_layout.addStretch()

    def _download_file(self, source_path: str, default_filename: str):
        import shutil
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        save_path, _ = QFileDialog.getSaveFileName(self, "Descargar / Exportar Archivo", default_filename)
        if save_path:
            try:
                shutil.copy2(source_path, save_path)
                QMessageBox.information(self, "Exportación Exitosa", f"El archivo se ha exportado correctamente a:\n{save_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Ocurrió un error al intentar exportar el archivo:\n{e}")

class RetroPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._data = {'computers': [], 'media': [], 'peripherals': [], 'modifications': [], 'projects': [], 'library': [], 'roms': [], 'lists': dict(DEFAULT_LISTS), '_trash': []}
        self.active_module = 'computers'
        self.search_query = ''
        self._current_page = 1

        self._sidebar = RetroSidebar()
        self._sidebar.module_changed.connect(self._on_module_changed)
        self._sidebar.search_changed.connect(self._on_search_changed)
        self._sidebar.add_computer_clicked.connect(self._on_add_computer)
        self._sidebar.add_media_clicked.connect(self._on_add_media)
        self._sidebar.add_periph_clicked.connect(self._on_add_periph)
        self._sidebar.add_mod_clicked.connect(self._on_add_mod)
        self._sidebar.add_project_clicked.connect(self._on_add_project)
        self._sidebar.add_library_clicked.connect(self._on_add_library)
        self._sidebar.add_rom_clicked.connect(self._on_add_rom)
        self._sidebar.settings_clicked.connect(self._on_show_settings)

        self._left_page = RetroLeftView()
        self._right_page = RetroRightView()

        self._left_page.item_selected.connect(self._on_item_selected)
        self._left_page.edit_item_requested.connect(self._on_edit_item)
        self._left_page.pagination_changed.connect(self._on_left_page_pagination_changed)

        self._right_page.item_updated.connect(self._on_item_updated)
        self._right_page.add_calculation_requested.connect(self._on_add_calculation)
        self._right_page.edit_calculation_requested.connect(self._on_edit_calculation)
        self._right_page.open_single_page_requested.connect(self._on_open_single_page)

    def get_name(self) -> str: return "Retro"
    def get_id(self) -> str: return "retro"
    def get_icon(self) -> str: return "retro.svg"
    def get_tab_color(self) -> str: return "#FF8C00"
    def get_order(self) -> int: return 7

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

    def get_total_pages(self) -> int: return self._left_page.get_total_pages()
    def get_current_page(self) -> int: return self._current_page

    def go_to_page(self, page_num: int):
        total = self.get_total_pages()
        self._current_page = max(1, min(page_num, total))
        self._update_views()

    def _update_views(self):
        items = self._data.get(self.active_module, [])
        sort_order = self._data.get('sort_order', 'alpha_asc')
        show_filename = self._data.get('show_filename', True)
        self._left_page.set_data(items, self.active_module, self.search_query, self._current_page, sort_order=sort_order, show_filename=show_filename)
        total = self._left_page.get_total_pages()
        if self._current_page > total:
            self._current_page = total
        self.page_changed.emit(self._current_page, total)

    def _on_left_page_pagination_changed(self, page: int, total: int):
        self._current_page = page
        self.page_changed.emit(page, total)

    def _on_module_changed(self, module_name: str):
        self.active_module = module_name
        self._current_page = 1
        
        if self._left_page.stack.currentIndex() != 0:
            self._left_page.stack.setCurrentIndex(0)
            self.single_page_requested.emit(False)
            
        self._update_views()
        self._right_page.set_item(None, module_name, self.get_agenda_path(), self._data)

    def _on_search_changed(self, query: str):
        self.search_query = query
        self._current_page = 1
        self._update_views()

    def _on_item_selected(self, item: dict, module_type: str):
        self._right_page.set_item(item, module_type, self.get_agenda_path(), self._data)

    def _on_item_updated(self, item: dict, module_type: str):
        self._is_modified = True
        self._update_views()

    def _on_add_computer(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = ComputerDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('computers', []).append(dlg.item_data)
            self.active_module = 'computers'
            self._is_modified = True
            self._update_views()

    def _on_add_media(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = MediaDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('media', []).append(dlg.item_data)
            self.active_module = 'media'
            self._is_modified = True
            self._update_views()

    def _on_add_periph(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = PeripheralDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('peripherals', []).append(dlg.item_data)
            self.active_module = 'peripherals'
            self._is_modified = True
            self._update_views()

    def _on_add_mod(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = ModificationDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('modifications', []).append(dlg.item_data)
            self.active_module = 'modifications'
            self._is_modified = True
            self._update_views()

    def _on_add_project(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = ProjectDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('projects', []).append(dlg.item_data)
            self.active_module = 'projects'
            self._is_modified = True
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'projects', self.get_agenda_path(), self._data)

    def _on_add_library(self):
        dlg = RetroDocumentDialog(retro_data=self._data, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            item_doc = dlg.item_data
            if dlg.selected_file_path and self.get_agenda_path():
                bib_dir = os.path.join(self.get_agenda_path(), 'retro', 'biblioteca')
                os.makedirs(bib_dir, exist_ok=True)
                filename = os.path.basename(dlg.selected_file_path)
                dest_path = os.path.join(bib_dir, filename)
                try:
                    shutil.copy2(dlg.selected_file_path, dest_path)
                    item_doc['relative_path'] = os.path.join('retro', 'biblioteca', filename)
                    item_doc['filename'] = filename
                except Exception as e:
                    print(f"[Retro] Error al copiar archivo a biblioteca: {e}")

            self._data.setdefault('library', []).append(item_doc)
            self.active_module = 'library'
            self._is_modified = True
            self._update_views()
            self._right_page.set_item(item_doc, 'library', self.get_agenda_path(), self._data)

    def _on_add_rom(self):
        dlg = RetroRomDialog(retro_data=self._data, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            item_rom = dlg.item_data
            if dlg.selected_rom_path and self.get_agenda_path():
                roms_dir = os.path.join(self.get_agenda_path(), 'retro', 'roms')
                os.makedirs(roms_dir, exist_ok=True)
                filename = os.path.basename(dlg.selected_rom_path)
                dest_path = os.path.join(roms_dir, filename)
                try:
                    shutil.copy2(dlg.selected_rom_path, dest_path)
                    item_rom['relative_path'] = os.path.join('retro', 'roms', filename)
                    item_rom['filename'] = filename
                except Exception as e:
                    print(f"[Retro] Error al copiar archivo de ROM: {e}")

            self._data.setdefault('roms', []).append(item_rom)
            self.active_module = 'roms'
            self._is_modified = True
            self._update_views()
            self._right_page.set_item(item_rom, 'roms', self.get_agenda_path(), self._data)

    def _on_edit_item(self, item: dict, module_type: str):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = None
        if module_type == 'computers': dlg = ComputerDialog(item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'media': dlg = MediaDialog(item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'peripherals': dlg = PeripheralDialog(item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'projects': dlg = ProjectDialog(item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'library': dlg = RetroDocumentDialog(item, retro_data=self._data, parent=self._sidebar.window())
        elif module_type == 'roms': dlg = RetroRomDialog(item, retro_data=self._data, parent=self._sidebar.window())
        else: dlg = ModificationDialog(item, lists=lists, parent=self._sidebar.window())

        if dlg.exec():
            items = self._data.get(module_type, [])
            if getattr(dlg, 'is_delete', False):
                if item in items:
                    items.remove(item)
                    self.move_to_trash(item)
                    self._is_modified = True
                    self._update_views()
                    self._right_page.set_item(None, module_type, self.get_agenda_path(), self._data)
            elif dlg.item_data:
                if module_type == 'library' and getattr(dlg, 'selected_file_path', None) and self.get_agenda_path():
                    bib_dir = os.path.join(self.get_agenda_path(), 'retro', 'biblioteca')
                    os.makedirs(bib_dir, exist_ok=True)
                    filename = os.path.basename(dlg.selected_file_path)
                    dest_path = os.path.join(bib_dir, filename)
                    try:
                        shutil.copy2(dlg.selected_file_path, dest_path)
                        dlg.item_data['relative_path'] = os.path.join('retro', 'biblioteca', filename)
                        dlg.item_data['filename'] = filename
                    except Exception as e:
                        print(f"[Retro] Error al copiar archivo editado a biblioteca: {e}")

                if module_type == 'roms' and getattr(dlg, 'selected_rom_path', None) and self.get_agenda_path():
                    roms_dir = os.path.join(self.get_agenda_path(), 'retro', 'roms')
                    os.makedirs(roms_dir, exist_ok=True)
                    filename = os.path.basename(dlg.selected_rom_path)
                    dest_path = os.path.join(roms_dir, filename)
                    try:
                        shutil.copy2(dlg.selected_rom_path, dest_path)
                        dlg.item_data['relative_path'] = os.path.join('retro', 'roms', filename)
                        dlg.item_data['filename'] = filename
                    except Exception as e:
                        print(f"[Retro] Error al copiar archivo editado de ROM: {e}")

                idx = items.index(item) if item in items else -1
                if idx >= 0:
                    items[idx] = dlg.item_data
                    self._is_modified = True
                    self._update_views()
                    self._right_page.set_item(dlg.item_data, module_type, self.get_agenda_path(), self._data)

    def _on_show_settings(self):
        dialog = RetroSettingsDialog(lists=self._data['lists'], plugin_data=self._data, parent=self._sidebar.window())
        if dialog.exec():
            self._is_modified = True
            self._update_views()

    def _on_add_calculation(self, item_analysis: dict):
        if not item_analysis: return
        dlg = ProjectCalculationDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            item_analysis.setdefault('calculations', []).append(dlg.item_data)
            self._is_modified = True
            self._right_page._refresh_calculations()

    def _on_edit_calculation(self, calc: dict, item_analysis: dict):
        dlg = ProjectCalculationDialog(item_to_edit=calc, parent=self._sidebar.window())
        if dlg.exec():
            calcs = item_analysis.setdefault('calculations', [])
            if getattr(dlg, 'is_delete', False):
                if calc in calcs:
                    calcs.remove(calc)
                    calc['_parent_project_id'] = item_analysis.get('id')
                    calc['_parent_project_name'] = item_analysis.get('name')
                    self.move_to_trash(calc)
                    self._is_modified = True
                    self._right_page._refresh_calculations()
            elif dlg.item_data:
                idx = calcs.index(calc) if calc in calcs else -1
                if idx >= 0:
                    calcs[idx] = dlg.item_data
                    self._is_modified = True
                    self._right_page._refresh_calculations()

    def _on_open_single_page(self, calc: dict, item_analysis: dict):
        if not self.get_agenda_path(): return
        
        while self._left_page.editor_layout.count():
            child = self._left_page.editor_layout.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()
                
        calc_type = calc.get('type')
        if calc_type == 'Editor de Código':
            editor = CodeEditorWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        elif calc_type == 'Mapa Mental':
            editor = MindMapEditorWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        elif calc_type == 'Diagrama de Flujo (Draw.io)':
            editor = FlowchartEditorWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        elif calc_type == 'Dibujo / Paint':
            editor = PaintEditorWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        elif calc_type == 'Visor 3D STL / G-Code':
            editor = STL3DViewerWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        elif calc_type == 'Visor KiCad / Gerber':
            editor = GerberKiCadViewerWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        elif calc_type == 'Editor de Diagramas Esquemáticos':
            editor = SchematicEditorWidget(calc, item_analysis, self.get_agenda_path(), parent=self._left_page.editor_container)
        else:
            editor = QLabel("Editor no soportado.")
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
        if hasattr(editor, 'closed'):
            editor.closed.connect(self._on_close_single_page)
            
        self._left_page.editor_layout.addWidget(editor)
        self._left_page.stack.setCurrentIndex(1)
        self.single_page_requested.emit(True)

    def _on_close_single_page(self):
        self._left_page.stack.setCurrentIndex(0)
        self.single_page_requested.emit(False)
        self._right_page._refresh_calculations()
        self._is_modified = True

    def on_activate(self):
        super().on_activate()
        if self.get_agenda_path():
            self.load_data(self.get_agenda_path())
        self._update_views()

    def load_data(self, agenda_path: str):
        self.set_agenda_path(agenda_path)
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data = loaded
            self._trash = loaded.get('_trash', [])
            if 'lists' not in self._data: self._data['lists'] = dict(DEFAULT_LISTS)
            if 'library' not in self._data: self._data['library'] = []
            if 'roms' not in self._data: self._data['roms'] = []
        else:
            self._data = {
                'computers': [], 'media': [], 'peripherals': [], 'modifications': [], 'projects': [], 'library': [], 'roms': [],
                'lists': dict(DEFAULT_LISTS), '_trash': []
            }
            self._trash = []
        
        project_path = os.path.join(agenda_path, 'retro', 'desarrollo.json')
        project_loaded = DataStore.load(project_path)
        if project_loaded and 'projects' in project_loaded:
            self._data['projects'] = project_loaded['projects']
        elif 'projects' not in self._data:
            self._data['projects'] = []
            
        self._update_views()
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            
            project_data = {'projects': self._data.get('projects', [])}
            project_path = os.path.join(agenda_path, 'retro', 'desarrollo.json')
            
            main_data = self._data.copy()
            if 'projects' in main_data: del main_data['projects']
                
            DataStore.save(data_path, main_data)
            DataStore.save(project_path, project_data)
            
            self._is_modified = False
