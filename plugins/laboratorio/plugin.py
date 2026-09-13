# =============================================================================
# Vito Organizer v2.2 - Laboratorio Plugin
# Gestor de Componentes Electrónicos, Instrumentos y Herramientas
# =============================================================================

import os
import re
import base64
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QUrl, QByteArray
from PyQt6.QtGui import QFont, QColor, QIcon, QPixmap, QDesktopServices, QPainter
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QScrollArea, QFrame, QButtonGroup, QLineEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog, QStackedWidget,
    QDoubleSpinBox, QSpinBox, QSizePolicy, QMenu, QTabWidget, QMessageBox
)

from plugins.plugin_base import PluginBase, open_local_file, load_image_pixmap, IMAGE_EXTENSIONS
from data.data_store import DataStore
from plugins.laboratorio.dialogs import (
    ComponentDialog, InstrumentDialog, ToolDialog, SupplyDialog, CalibratorDialog,
    CalibrationLogDialog, LabSettingsDialog, CheckListManagerDialog, 
    CheckListEventDialog, CheckListViewDialog, AnalysisDialog, CalculationDialog,
    ProjectDialog, ProjectCalculationDialog
)
from plugins.laboratorio.analysis_editor import CalculationEditorWidget
from plugins.laboratorio.project_editors import (
    CodeEditorWidget, MindMapEditorWidget, FlowchartEditorWidget,
    PaintEditorWidget, STL3DViewerWidget, GerberKiCadViewerWidget,
    LibraryDocViewerWidget, SchematicEditorWidget
)
from plugins.laboratorio.instrument_records import (
    InstrumentNavSidebar, InstrumentRecordsContainer, get_instrument_dir
)


def get_themed_svg_icon(icon_path: str, color_hex: str = "#0D47A1", size: int = 18) -> QIcon:
    """Carga un archivo SVG y reemplaza cualquier trazo o relleno con color_hex para máxima visibilidad en fondos claros."""
    if not os.path.exists(icon_path):
        return QIcon()
    try:
        with open(icon_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Reemplazar trazos stroke="..." y stroke:... excepto 'none'
        content = re.sub(r'stroke="(?!none)[^"]+"', f'stroke="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'stroke:\s*(?!none)[^;"]+', f'stroke:{color_hex}', content, flags=re.IGNORECASE)

        # Reemplazar rellenos fill="..." y fill:... excepto 'none'
        content = re.sub(r'fill="(?!none)[^"]+"', f'fill="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'fill:\s*(?!none)[^;"]+', f'fill:{color_hex}', content, flags=re.IGNORECASE)

        renderer = QSvgRenderer(QByteArray(content.encode('utf-8')))
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return QIcon(pix)
    except Exception:
        return QIcon(icon_path)


def get_calibrator_dir(agenda_path: str, item: dict) -> str:
    """Devuelve y asegura la existencia del directorio de almacenamiento del calibrador en laboratorio/calibradores/."""
    if not agenda_path or not item:
        return ""
    safe_name = "".join([c for c in item.get('name', 'Calibrador') if c.isalnum() or c in (' ', '_', '-')]).strip() or 'Calibrador'
    safe_name = safe_name.replace(" ", "_")
    item_id = item.get('id', 'calib')
    folder_name = f"{item_id}_{safe_name}"
    cal_dir = os.path.join(agenda_path, 'laboratorio', 'calibradores', folder_name)
    os.makedirs(cal_dir, exist_ok=True)
    return cal_dir


CALIBRATION_UNITS = [
    # Tensión / Voltaje
    "V", "mV", "µV", "nV", "kV",
    # Corriente
    "A", "mA", "µA", "nA", "pA", "kA",
    # Resistencia
    "Ω", "kΩ", "MΩ", "GΩ", "mΩ",
    # Capacitancia
    "µF", "nF", "pF", "mF", "F",
    # Inductancia
    "mH", "µH", "nH", "H",
    # Frecuencia
    "Hz", "kHz", "MHz", "GHz",
    # Temperatura
    "°C", "°F", "K",
    # Potencia & Tiempo
    "W", "mW", "µW", "kW", "dBm",
    "s", "ms", "µs", "ns",
    # Proporción / Ratios
    "%", "ppm", "dB"
]


DEFAULT_LISTS = {
    'component_types': [
        "Pasivo (Resistencia/Capacitor/Inductor)", 
        "Semiconductor / Diodo / Transistor", 
        "Circuito Integrado / CI", 
        "Microcontrolador / Módulo", 
        "Sensor / Transductor", 
        "Conector / Cabezal", 
        "Otro"
    ],
    'component_categories': [
        "SMD 0805", 
        "DIP-8", 
        "TO-220", 
        "Arduino", 
        "SMD 1206", 
        "SOP-8"
    ],
    'component_conditions': [
        "Nuevo (Sin uso)", 
        "Reciclado / Desoldado", 
        "Usado (Buen estado)"
    ],
    'tool_types': [
        "Destornilladores / Puntas", 
        "Alicates / Pinzas", 
        "Llaves Allen / Torx / Fijas", 
        "Limatones / Limas", 
        "Brocas / Mechas", 
        "Taladro / Dremel / Herramienta Eléctrica", 
        "Desoldador / Extractor", 
        "Otra Herramienta"
    ],
    'tool_statuses': [
        "Excelente", 
        "Bueno (Uso normal)", 
        "Requiere Mantenimiento / Ajuste", 
        "Descarte / Rota"
    ],
    'supply_types': [
        "Flux / Fundente", 
        "Pasta Térmica / Grasa Siliconada", 
        "Pasta de Soldar / Estaño en Pasta", 
        "Adhesivo / Epóxico / Cianoacrilato", 
        "Esponja / Fibra Limpiadora", 
        "Cotonitos / Aplicadores", 
        "Paños de Limpieza / Wipes", 
        "Solvente / Alcohol Isopropílico", 
        "Hilo / Carrete de Soldadura", 
        "Malla Desoldadora", 
        "Otro Insumo"
    ],
    'supply_units': [
        "unidades", 
        "cc / ml", 
        "g / kg", 
        "frascos / potes", 
        "jeringas", 
        "rollos / carretes", 
        "paquetes / cajas"
    ],
    'instrument_types': [
        "Multímetro", 
        "Osciloscopio", 
        "Fuente de Poder Regulada", 
        "Generador de Funciones / Señales", 
        "Puente LCR / Medidor ESR", 
        "Estación de Soldadura / Cautín", 
        "Analizador Lógico", 
        "Otro Instrumento"
    ],
    'instrument_statuses': [
        "Operativo", 
        "No operativo", 
        "Falta Calibración", 
        "Falta Ajustes", 
        "Fallas de Componentes", 
        "Regular", 
        "No definido"
    ],
    'calibration_results': [
        "Calibrado / Operativo Ok", 
        "Calibrado con Desviación", 
        "Mantenimiento Realizado", 
        "Falla / Requiere Reparación"
    ],
    'calibrator_types': [
        "Placa Referencia",
        "Referencia de tensión",
        "Referencia de Corriente",
        "Referencia pasiva",
        "Otro"
    ],
    'analysis_categories': [
        "Análisis Químico",
        "Análisis Físico",
        "Medición Eléctrica",
        "Pruebas de Estrés",
        "Inspección Visual",
        "Otro"
    ],
    'project_categories': [
        "Hardware",
        "Software / Firmware",
        "Diseño PCB",
        "Mecánica / 3D",
        "Investigación",
        "Otro"
    ]
}



class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


class LabLeftView(QWidget):
    """Vista de la página izquierda (Lista de Inventario)."""

    item_selected = pyqtSignal(dict, str) # (item, module_type)
    edit_item_requested = pyqtSignal(dict, str)
    pagination_changed = pyqtSignal(int, int) # (current_page, total_pages)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.items = []
        self.module_type = 'components' # 'components', 'instruments', 'tools'
        self.search_query = ''
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 35, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.lbl_hdr_title = QLabel("Inventario de Componentes Electrónicos")
        self.lbl_hdr_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_hdr_title)
        layout.addWidget(self.hdr_frame)

        self.stack = QStackedWidget()
        
        # 0. List container
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área Scrollable
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_content.setMinimumWidth(0)
        self.scroll_content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)

        self.scroll.setWidget(self.scroll_content)
        self.list_layout.addWidget(self.scroll)
        
        self.stack.addWidget(self.list_container)
        
        # 1. Editor container (Single Page)
        self.editor_container = QWidget()
        self.editor_layout = QVBoxLayout(self.editor_container)
        self.editor_layout.setContentsMargins(0, 0, 0, 0)
        self.stack.addWidget(self.editor_container)
        
        # 2. Instrument Nav container (Modo Registros)
        self.instrument_nav = InstrumentNavSidebar()
        self.stack.addWidget(self.instrument_nav)
        
        layout.addWidget(self.stack, 1)

    def set_data(self, items: list, module_type: str = 'components', search_query: str = '', page: int = 1, sort_order: str = 'alpha_asc'):
        self.items = items
        self.module_type = module_type
        self.search_query = search_query.lower().strip()
        self.page = page
        self.sort_order = sort_order
        
        if not hasattr(self, 'items_per_page'):
            self.items_per_page = 7
            
        self._refresh()

    def get_total_pages(self) -> int:
        return getattr(self, 'total_pages', 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalculate_items_per_page()

    def _recalculate_items_per_page(self):
        margins_y = 30  # content margins (top 15, bottom 15)
        hdr_y = 44      # cabecera (34) + spacing (10)
        
        available_y = self.height() - margins_y - hdr_y
        if available_y <= 0:
            return
            
        # Altura promedio de tarjeta fija: 40px. Con el spacing de 4px: 44px.
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
                if w:
                    w.setParent(None)
                    w.deleteLater()

        titles = {
            'components': 'Componentes Electrónicos',
            'instruments': 'Instrumentos de Laboratorio',
            'calibrators': 'Dispositivos de Calibración / Calibradores',
            'tools': 'Herramientas de Taller',
            'supplies': 'Insumos y Materiales de Taller',
            'analysis': 'Gestor de Análisis y Pruebas',
            'projects': 'Gestor de Desarrollo y Proyectos'
        }
        self.lbl_hdr_title.setText(titles.get(self.module_type, 'Inventario'))

        filtered = []
        for it in self.items:
            if self.search_query:
                name_match = self.search_query in it.get('name', '').lower()
                cat_match = self.search_query in it.get('category', '').lower() or self.search_query in it.get('type', '').lower()
                loc_match = self.search_query in it.get('storage_location', '').lower()
                brand_match = self.search_query in it.get('brand', '').lower() or self.search_query in it.get('model', '').lower()
                origin_match = self.search_query in it.get('origin', '').lower()
                if not (name_match or cat_match or loc_match or brand_match or origin_match):
                    continue
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


        # Calcular métricas de paginación
        self.total_items = len(filtered)
        self.total_pages = max(1, (self.total_items + self.items_per_page - 1) // self.items_per_page)
        
        if self.page > self.total_pages:
            self.page = self.total_pages
            
        start_idx = (self.page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = filtered[start_idx:end_idx]

        if not page_items:
            lbl_empty = QLabel("No hay elementos registrados en esta categoría.")
            lbl_empty.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl_empty)
        else:
            for item in page_items:
                card = ClickableFrame()
                card.setFixedHeight(40)
                card.setMinimumWidth(0)
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.75); border: 1px solid #D0C070; border-radius: 6px; } QFrame:hover { background-color: rgba(255,255,255,0.95); border-color: #8A2BE2; }")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(10, 4, 10, 4)

                icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

                loc_img = f"<img src='{os.path.join(icons_dir, 'location.svg')}' width='13' height='13'>"
                box_img = f"<img src='{os.path.join(icons_dir, 'box.svg')}' width='13' height='13'>"
                check_img = f"<img src='{os.path.join(icons_dir, 'check.svg')}' width='13' height='13'>"
                warn_img = f"<img src='{os.path.join(icons_dir, 'warning.svg')}' width='13' height='13'>"
                ruler_img = f"<img src='{os.path.join(icons_dir, 'ruler.svg')}' width='13' height='13'>"

                if self.module_type == 'components':
                    tested_str = f"{check_img} Testeado" if item.get('tested', True) else f"{warn_img} No Testeado"
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>{loc_img} {item.get('storage_location', 'Sin loc')} | {box_img} Stock: <b>{item.get('stock_quantity', 0)}</b> | {tested_str}</span>"
                elif self.module_type == 'instruments':
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('brand')} {item.get('model')})<br><span style='color:#555; font-size:11px;'>Tipo: {item.get('type')} | S/N: {item.get('serial_number', 'N/A')} | Estado: <b>{item.get('status', 'Operativo')}</b></span>"
                elif self.module_type == 'calibrators':
                    calib_date = item.get('last_calibration_date', 'Sin fecha')
                    origin = item.get('origin', 'Comparada')
                    n_meas = len(item.get('measurements', []))
                    n_pts = len(item.get('reference_points', []))
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('type')})<br><span style='color:#555; font-size:11px;'>Ref: <b>{origin}</b> | {ruler_img} Calib: {calib_date} | Mediciones: <b>{n_meas}</b> | Puntos Patrón: <b>{n_pts}</b></span>"
                elif self.module_type == 'tools':
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('brand')} {item.get('model')})<br><span style='color:#555; font-size:11px;'>Tipo: {item.get('type')} | Estado: <b>{item.get('status', 'Excelente')}</b></span>"
                elif self.module_type in ('analysis', 'projects'):
                    lbl_txt = f"<b>{item.get('name')}</b><br><span style='color:#555; font-size:11px;'>Cat: <b>{item.get('category')}</b> | Docs: {len(item.get('calculations', []))}</span>"
                else:
                    lbl_txt = f"<b>{item.get('name')}</b> ({item.get('brand')} {item.get('model')})<br><span style='color:#555; font-size:11px;'>Tipo: {item.get('type')} | {box_img} Stock: <b>{item.get('stock_quantity', 0)} {item.get('unit', '')}</b> | {loc_img} {item.get('storage_location', '')}</span>"

                lbl = QLabel(lbl_txt)
                lbl.setMinimumWidth(0)
                lbl.setWordWrap(True)
                lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                lbl.setStyleSheet("border: none; background: transparent; color: #111111;")
                lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                c_layout.addWidget(lbl, 1)

                btn_edit = QPushButton("Editar")
                btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil.svg')))
                btn_edit.setFixedSize(65, 26)
                btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_edit.setStyleSheet("border: 1px solid #CCC; background: #F0F0F0; border-radius: 4px; font-size: 11px; font-weight: bold; color: #333;")
                btn_edit.clicked.connect(lambda checked, it=item: self.edit_item_requested.emit(it, self.module_type))
                c_layout.addWidget(btn_edit)

                # Evento clic en tarjeta
                card.clicked.connect(lambda checked=False, it=item: self.item_selected.emit(it, self.module_type))
                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()


class LabRightView(QWidget):
    """Vista de la página derecha (Ficha Técnica y Registro de Calibración/Datasheet)."""

    item_updated = pyqtSignal(dict, str)
    add_calculation_requested = pyqtSignal(dict) # item_analysis
    edit_calculation_requested = pyqtSignal(dict, dict) # calculation, item_analysis
    open_single_page_requested = pyqtSignal(dict, dict) # calculation, item_analysis
    open_single_page_right_requested = pyqtSignal(dict, str) # item, module_type
    open_instrument_records_requested = pyqtSignal(dict) # item_instrument

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.current_item = None
        self.module_type = 'components'
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 15, 25, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_title = QLabel("Ficha Técnica y Registro")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_title, 1)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        self.btn_single_page = QPushButton(" Pantalla")
        self.btn_single_page.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'panoramic.svg'), color_hex="#0D47A1", size=16))
        self.btn_single_page.setToolTip("Mostrar el contenido de la página derecha en modo de página única (pantalla completa)")
        self.btn_single_page.setStyleSheet("QPushButton { border: 1px solid #1976D2; background: #E3F2FD; font-weight: bold; color: #0D47A1; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #BBDEFB; }")
        self.btn_single_page.clicked.connect(self._on_single_page_clicked)
        self.btn_single_page.setVisible(False)
        hdr_layout.addWidget(self.btn_single_page)

        self.btn_records = QPushButton(" Registros")
        self.btn_records.setIcon(QIcon(os.path.join(icons_dir, 'notes_dark.svg')))
        self.btn_records.setToolTip("Ver y gestionar registros, documentación, descripción HTML, checklists y calibración del instrumento")
        self.btn_records.setStyleSheet("QPushButton { border: 1px solid #1e88e5; background: #e3f2fd; font-weight: bold; color: #1565c0; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #bbdefb; }")
        self.btn_records.clicked.connect(self._on_open_records_clicked)
        self.btn_records.setVisible(False)
        hdr_layout.addWidget(self.btn_records)

        self.btn_toggle_view = QPushButton("Movimientos")
        self.btn_toggle_view.setIcon(QIcon(os.path.join(icons_dir, 'history.svg')))
        self.btn_toggle_view.setToolTip("Ver historial de ingresos y egresos de stock")
        self.btn_toggle_view.setStyleSheet("QPushButton { border: 1px solid #CCC; background: #F0F0F0; font-weight: bold; color: #333333; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #E0E0E0; }")
        self.btn_toggle_view.clicked.connect(self._toggle_movements_view)
        self.btn_toggle_view.setVisible(False)
        hdr_layout.addWidget(self.btn_toggle_view)

        layout.addWidget(self.hdr_frame)

        self.stack = QStackedWidget()
        
        # 0. Placeholder
        self.empty_lbl = QLabel("Selecciona un elemento de la lista para ver su ficha técnica.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        self.stack.addWidget(self.empty_lbl)

        # 1. Visor Ficha Detallada / Movimientos
        self.detail_container = QWidget()
        d_layout = QVBoxLayout(self.detail_container)
        d_layout.setContentsMargins(0, 0, 0, 0)
        d_layout.setSpacing(10)

        self.info_stack = QStackedWidget()

        # 1a. Página de Ficha Técnica
        self.tech_sheet_page = QWidget()
        ts_layout = QVBoxLayout(self.tech_sheet_page)
        ts_layout.setContentsMargins(0, 0, 0, 0)
        ts_layout.setSpacing(10)

        self.card_info = QFrame()
        self.card_info.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; padding: 10px; }")
        ci_layout = QVBoxLayout(self.card_info)

        self.img_preview = QLabel()
        self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_preview.setMaximumHeight(160)
        self.img_preview.setStyleSheet("border: 1px solid #DDD; background: #FAFAFA; border-radius: 4px;")
        ci_layout.addWidget(self.img_preview)

        self.lbl_detail_text = QLabel()
        self.lbl_detail_text.setWordWrap(True)
        self.lbl_detail_text.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 13px;")
        ci_layout.addWidget(self.lbl_detail_text)

        # Controles de edición en línea dentro de card_info
        self.edit_frame = QFrame()
        self.edit_frame.setStyleSheet("QFrame { border: none; background: transparent; padding: 0px; }")
        edit_layout = QHBoxLayout(self.edit_frame)
        edit_layout.setContentsMargins(0, 5, 0, 5)
        edit_layout.setSpacing(10)
        
        lbl_min = QLabel("Stock Mín.:")
        lbl_min.setStyleSheet("color: #333; font-weight: bold; border: none; background: transparent; font-size: 11px;")
        self.spin_min_stock = QSpinBox()
        self.spin_min_stock.setRange(0, 999999)
        self.spin_min_stock.setStyleSheet("background-color: white; color: black; border: 1px solid #CCC; border-radius: 4px; padding: 2px; font-size: 11px;")
        
        lbl_cost = QLabel("Costo Unit.:")
        lbl_cost.setStyleSheet("color: #333; font-weight: bold; border: none; background: transparent; font-size: 11px;")
        self.spin_cost = QDoubleSpinBox()
        self.spin_cost.setRange(0.0, 99999999.0)
        self.spin_cost.setDecimals(2)
        self.spin_cost.setStyleSheet("background-color: white; color: black; border: 1px solid #CCC; border-radius: 4px; padding: 2px; font-size: 11px;")
        
        self.btn_save_card = QPushButton("Guardar")
        self.btn_save_card.setStyleSheet("QPushButton { background-color: #f57c00; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #e64a19; }")
        self.btn_save_card.clicked.connect(self._on_save_card_changes)
        
        edit_layout.addWidget(lbl_min)
        edit_layout.addWidget(self.spin_min_stock)
        edit_layout.addWidget(lbl_cost)
        edit_layout.addWidget(self.spin_cost)
        edit_layout.addWidget(self.btn_save_card)
        
        ci_layout.addWidget(self.edit_frame)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.btn_action_doc = QPushButton(" Abrir Documento / Datasheet / Manual")
        self.btn_action_doc.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
        self.btn_action_doc.setStyleSheet("QPushButton { background-color: #1e88e5; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }")
        self.btn_action_doc.clicked.connect(self._open_document)
        ci_layout.addWidget(self.btn_action_doc)

        self.btn_action_msds = QPushButton(" Abrir Hoja de Seguridad (MSDS)")
        self.btn_action_msds.setIcon(QIcon(os.path.join(icons_dir, 'safety.svg')))
        self.btn_action_msds.setStyleSheet("QPushButton { background-color: #d81b60; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; }")
        self.btn_action_msds.clicked.connect(self._open_msds)
        ci_layout.addWidget(self.btn_action_msds)

        ts_layout.addWidget(self.card_info)

        # Tabla de Calibraciones / Mantenimientos
        self.history_frame = QFrame()
        self.history_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.8); border: 1px solid #D0C070; border-radius: 6px; }")
        hf_layout = QVBoxLayout(self.history_frame)
        hf_layout.setContentsMargins(10, 8, 10, 8)

        h_tb = QHBoxLayout()
        self.lbl_hist_title = QLabel("Historial de Calibraciones / Pruebas / Chequeos")
        self.lbl_hist_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333333; border: none; background: transparent;")
        h_tb.addWidget(self.lbl_hist_title)
        h_tb.addStretch()

        self.btn_add_log = QPushButton(" Registrar Evento")
        self.btn_add_log.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_log.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; }")
        self.btn_add_log.clicked.connect(self._on_add_log)
        h_tb.addWidget(self.btn_add_log)
        hf_layout.addLayout(h_tb)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Fecha", "Resultado", "Notas"])
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.log_table.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #CCC; }")
        hf_layout.addWidget(self.log_table, 1)
        self.log_table.itemDoubleClicked.connect(self._on_log_table_double_clicked)

        ts_layout.addWidget(self.history_frame, 1)

        # Sección de Archivos Asignados de Biblioteca
        self.bib_files_frame = QFrame()
        self.bib_files_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #20B2AA; border-radius: 6px; padding: 8px; }")
        bff_layout = QVBoxLayout(self.bib_files_frame)
        bff_layout.setContentsMargins(6, 6, 6, 6)
        
        lbl_bff_title = QLabel("Archivos de Biblioteca Asignados:")
        lbl_bff_title.setStyleSheet("font-weight: bold; color: #008B8B; font-size: 12px; border: none; background: transparent;")
        bff_layout.addWidget(lbl_bff_title)

        self.bib_files_layout = QVBoxLayout()
        self.bib_files_layout.setSpacing(4)
        bff_layout.addLayout(self.bib_files_layout)

        ts_layout.addWidget(self.bib_files_frame)

        self.info_stack.addWidget(self.tech_sheet_page)

        # 1b. Página de Movimientos
        self.movements_page = QWidget()
        mv_layout = QVBoxLayout(self.movements_page)
        mv_layout.setContentsMargins(0, 0, 0, 0)
        mv_layout.setSpacing(10)

        self.lbl_mv_title = QLabel("Historial de Ingresos y Egresos (Kardex)")
        self.lbl_mv_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333333; border: none; background: transparent;")
        mv_layout.addWidget(self.lbl_mv_title)

        self.mv_table = QTableWidget()
        self.mv_table.setColumnCount(4)
        self.mv_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Cantidad", "Detalles / Motivo"])
        self.mv_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.mv_table.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #CCC; }")
        mv_layout.addWidget(self.mv_table, 1)

        self.info_stack.addWidget(self.movements_page)

        # 1c. Página de Análisis
        self.analysis_page = QWidget()
        an_layout = QVBoxLayout(self.analysis_page)
        an_layout.setContentsMargins(0, 0, 0, 0)
        an_layout.setSpacing(10)
        
        self.lbl_an_summary = QLabel()
        self.lbl_an_summary.setWordWrap(True)
        self.lbl_an_summary.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 13px;")
        an_layout.addWidget(self.lbl_an_summary)
        
        an_hdr = QHBoxLayout()
        self.lbl_calc_section_title = QLabel("Cálculos y Registros de Pruebas")
        self.lbl_calc_section_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333333; border: none; background: transparent;")
        an_hdr.addWidget(self.lbl_calc_section_title)
        an_hdr.addStretch()
        
        self.btn_add_calc = QPushButton(" Agregar Cálculo")
        self.btn_add_calc.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_calc.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; }")
        self.btn_add_calc.clicked.connect(lambda: self.add_calculation_requested.emit(self.current_item))
        an_hdr.addWidget(self.btn_add_calc)
        
        an_layout.addLayout(an_hdr)
        
        # Area scrollable para calculos
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

        # 1d. Página de Calibradores / Dispositivos de Calibración
        self.calibrator_page = QWidget()
        cal_layout = QVBoxLayout(self.calibrator_page)
        cal_layout.setContentsMargins(0, 0, 0, 0)
        cal_layout.setSpacing(8)

        # Tarjeta de Información General del Calibrador
        self.card_calib_info = QFrame()
        self.card_calib_info.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; padding: 8px; }")
        cci_layout = QVBoxLayout(self.card_calib_info)
        cci_layout.setContentsMargins(8, 6, 8, 6)
        cci_layout.setSpacing(4)

        self.lbl_calib_title = QLabel()
        self.lbl_calib_title.setWordWrap(True)
        self.lbl_calib_title.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 13px;")
        cci_layout.addWidget(self.lbl_calib_title)
        
        cal_layout.addWidget(self.card_calib_info)

        # Tab Widget con los dos apartados
        self.calib_tabs = QTabWidget()
        self.calib_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #B0B0B0;
                background-color: #FFFFFF;
                border-radius: 4px;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #E2E4E9;
                color: #2B2D42;
                border: 1px solid #B0B0B0;
                border-bottom: none;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 11px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #FFFFFF;
                color: #0D47A1;
                border-color: #B0B0B0;
                border-bottom: 2px solid #0D47A1;
            }
            QTabBar::tab:hover:!selected {
                background-color: #D5D8E0;
                color: #111111;
            }
        """)

        table_style = """
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                color: #111111;
                gridline-color: #E0E0E0;
            }
            QHeaderView::section {
                background-color: #2B2D42;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 4px;
                border: 1px solid #3D405B;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                padding: 2px 4px;
            }
            QLineEdit:focus {
                border: 1px solid #1976D2;
                background-color: #F5F9FF;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 4px;
                font-weight: bold;
            }
            QComboBox:focus {
                border: 1px solid #1976D2;
                background-color: #F5F9FF;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #111111;
                selection-background-color: #1976D2;
                selection-color: #FFFFFF;
                border: 1px solid #90A4AE;
                outline: 0px;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item {
                color: #111111;
                background-color: #FFFFFF;
                min-height: 22px;
                padding: 3px 6px;
            }
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected {
                background-color: #1976D2;
                color: #FFFFFF;
            }
        """

        # --- Apartado 1: Mediciones Realizadas e Importación ---
        self.tab_calib_measurements = QWidget()
        tcm_layout = QVBoxLayout(self.tab_calib_measurements)
        tcm_layout.setContentsMargins(8, 8, 8, 8)
        tcm_layout.setSpacing(6)

        tcm_bar = QHBoxLayout()
        tcm_bar.setSpacing(6)

        lbl_tcm_title = QLabel("<b>Mediciones y Documentos de Calibración:</b>")
        lbl_tcm_title.setStyleSheet("color: #222222; font-size: 11px;")
        tcm_bar.addWidget(lbl_tcm_title, 1)

        self.btn_add_meas = QPushButton(" Nueva Medición")
        self.btn_add_meas.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_meas.setStyleSheet("QPushButton { background-color: #0288d1; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #0277bd; }")
        self.btn_add_meas.clicked.connect(self._add_measurement_row)
        tcm_bar.addWidget(self.btn_add_meas)

        self.btn_import_meas = QPushButton(" Importar XLS / CSV")
        self.btn_import_meas.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
        self.btn_import_meas.setStyleSheet("QPushButton { background-color: #7b1fa2; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #6a1b9a; }")
        self.btn_import_meas.clicked.connect(self._import_measurements_file)
        tcm_bar.addWidget(self.btn_import_meas)

        self.btn_export_meas = QPushButton(" Exportar CSV")
        self.btn_export_meas.setIcon(QIcon(os.path.join(icons_dir, 'history.svg')))
        self.btn_export_meas.setStyleSheet("QPushButton { background-color: #546e7a; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #455a64; }")
        self.btn_export_meas.clicked.connect(self._export_measurements_csv)
        tcm_bar.addWidget(self.btn_export_meas)

        self.btn_save_meas = QPushButton(" Guardar Mediciones")
        self.btn_save_meas.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
        self.btn_save_meas.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save_meas.clicked.connect(self._save_calibrator_measurements)
        tcm_bar.addWidget(self.btn_save_meas)

        tcm_layout.addLayout(tcm_bar)

        self.tbl_calib_measurements = QTableWidget()
        self.tbl_calib_measurements.setColumnCount(7)
        self.tbl_calib_measurements.setHorizontalHeaderLabels([
            "Valor Nominal", "Unidad", "Valor Medido", "Desviación / Error", "Temp. (°C)", "Fecha / Notas", "Acción"
        ])
        self.tbl_calib_measurements.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.tbl_calib_measurements.setStyleSheet(table_style)
        tcm_layout.addWidget(self.tbl_calib_measurements, 1)

        self.calib_tabs.addTab(
            self.tab_calib_measurements,
            get_themed_svg_icon(os.path.join(icons_dir, 'document.svg'), color_hex="#1565C0", size=16),
            "1. Mediciones Realizadas (XLS/CSV)"
        )

        # --- Apartado 2: Tabla de Valores Patrón para Pruebas ---
        self.tab_calib_ref_points = QWidget()
        tcr_layout = QVBoxLayout(self.tab_calib_ref_points)
        tcr_layout.setContentsMargins(8, 8, 8, 8)
        tcr_layout.setSpacing(6)

        tcr_bar = QHBoxLayout()
        tcr_bar.setSpacing(6)

        lbl_tcr_title = QLabel("<b>Valores Patrón para Pruebas en Instrumentos:</b>")
        lbl_tcr_title.setStyleSheet("color: #222222; font-size: 11px;")
        tcr_bar.addWidget(lbl_tcr_title, 1)

        self.btn_add_ref_point = QPushButton(" Agregar Punto Patrón")
        self.btn_add_ref_point.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_ref_point.setStyleSheet("QPushButton { background-color: #0288d1; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #0277bd; }")
        self.btn_add_ref_point.clicked.connect(self._add_ref_point_row)
        tcr_bar.addWidget(self.btn_add_ref_point)

        self.btn_sync_from_meas = QPushButton(" Sincronizar desde Mediciones")
        self.btn_sync_from_meas.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
        self.btn_sync_from_meas.setStyleSheet("QPushButton { background-color: #7b1fa2; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #6a1b9a; }")
        self.btn_sync_from_meas.clicked.connect(self._sync_ref_points_from_measurements)
        tcr_bar.addWidget(self.btn_sync_from_meas)

        self.btn_save_ref_points = QPushButton(" Guardar Puntos")
        self.btn_save_ref_points.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
        self.btn_save_ref_points.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save_ref_points.clicked.connect(self._save_calibrator_ref_points)
        tcr_bar.addWidget(self.btn_save_ref_points)

        tcr_layout.addLayout(tcr_bar)

        self.tbl_ref_points = QTableWidget()
        self.tbl_ref_points.setColumnCount(6)
        self.tbl_ref_points.setHorizontalHeaderLabels([
            "Magnitud / Función", "Valor Patrón", "Unidad", "Tolerancia (+/-)", "Instrucciones / Notas", "Acción"
        ])
        self.tbl_ref_points.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tbl_ref_points.setStyleSheet(table_style)
        tcr_layout.addWidget(self.tbl_ref_points, 1)

        self.calib_tabs.addTab(
            self.tab_calib_ref_points,
            get_themed_svg_icon(os.path.join(icons_dir, 'ruler.svg'), color_hex="#1565C0", size=16),
            "2. Tabla de Valores Patrón para Pruebas"
        )

        cal_layout.addWidget(self.calib_tabs, 1)
        self.info_stack.addWidget(self.calibrator_page)

        d_layout.addWidget(self.info_stack, 1)

        self.stack.addWidget(self.detail_container)

        # 2. Contenedor de Registros de Instrumentos (Modo Registros)
        self.instrument_records_container = InstrumentRecordsContainer()
        self.instrument_records_container.item_updated.connect(lambda it: self.item_updated.emit(it, 'instruments'))
        self.stack.addWidget(self.instrument_records_container)

        layout.addWidget(self.stack, 1)

    def _on_open_records_clicked(self):
        if self.current_item and self.module_type == 'instruments':
            self.open_instrument_records_requested.emit(self.current_item)

    def _toggle_movements_view(self):
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        if self.info_stack.currentIndex() == 0:
            self.info_stack.setCurrentIndex(1)
            self.btn_toggle_view.setText("Ver Ficha")
            self.btn_toggle_view.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
            self._refresh_movements_table()
        else:
            self.info_stack.setCurrentIndex(0)
            self.btn_toggle_view.setText("Movimientos")
            self.btn_toggle_view.setIcon(QIcon(os.path.join(icons_dir, 'history.svg')))

    def _refresh_movements_table(self):
        self.mv_table.setRowCount(0)
        if not self.current_item: return
        movements = self.current_item.get('movements', [])
        for i, mv in enumerate(movements):
            self.mv_table.insertRow(i)
            
            # Fecha
            item_date = QTableWidgetItem(mv.get('date', ''))
            item_date.setForeground(QColor("#111111"))
            self.mv_table.setItem(i, 0, item_date)
            
            # Tipo
            item_type = QTableWidgetItem(mv.get('type', '').capitalize())
            item_type.setForeground(QColor("#111111"))
            self.mv_table.setItem(i, 1, item_type)
            
            # Cantidad (Verde para ingresos, Rojo para egresos)
            qty_val = mv.get('quantity', 0)
            is_ingreso = mv.get('type') == 'ingreso'
            qty_str = f"+{qty_val}" if is_ingreso else f"-{qty_val}"
            item_qty = QTableWidgetItem(qty_str)
            item_qty.setForeground(QColor("#2e7d32" if is_ingreso else "#c62828"))
            item_qty.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.mv_table.setItem(i, 2, item_qty)
            
    def _on_single_page_clicked(self):
        if self.current_item:
            self.open_single_page_right_requested.emit(self.current_item, self.module_type)

    def set_item(self, item: dict, module_type: str, agenda_path: str = None):
        self.current_item = item
        self.module_type = module_type
        if agenda_path: self.agenda_path = agenda_path
        cur_agenda = getattr(self, 'agenda_path', None)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        if not item:
            self.stack.setCurrentIndex(0)
            self.btn_single_page.setVisible(False)
            self.btn_toggle_view.setVisible(False)
            self.btn_records.setVisible(False)
            return

        self.btn_single_page.setVisible(True)
        self.stack.setCurrentIndex(1)
        self.info_stack.setCurrentIndex(0)
        self.btn_toggle_view.setText("Movimientos")
        self.btn_toggle_view.setIcon(QIcon(os.path.join(icons_dir, 'history.svg')))
        self.btn_toggle_view.setVisible(module_type in ('components', 'supplies'))
        self.btn_records.setVisible(module_type == 'instruments')
        
        if module_type in ('analysis', 'projects'):
            self.info_stack.setCurrentIndex(2) # Analysis & Projects page
            
        # Cargar valores en los controles de edición en línea
        self.edit_frame.setVisible(module_type in ('components', 'supplies'))
        if module_type in ('components', 'supplies'):
            self.spin_min_stock.setValue(item.get('min_stock_quantity', 0))
            self.spin_cost.setValue(item.get('cost_value', 0.0))
            from config.settings import Settings
            settings = Settings.load()
            currency = getattr(settings.general, 'cost_currency', 'CLP')
            self.spin_cost.setSuffix(f" {currency}")

        doc_url = ""
        msds_url = ""
        if module_type == 'components':
            self.lbl_title.setText(f"Ficha de Componente: {item.get('name')}")
            tested_str = "Testeado Operativo" if item.get('tested', True) else "No Testeado"
            
            from config.settings import Settings
            settings = Settings.load()
            currency = getattr(settings.general, 'cost_currency', 'CLP')
            
            stock = item.get('stock_quantity', 0)
            cost = item.get('cost_value', 0.0)
            total = stock * cost
            
            txt = f"<h3 style='margin:0; color:#8A2BE2;'>{item.get('name')}</h3>"
            txt += f"<b>Tipo:</b> {item.get('type')}<br>"
            txt += f"<b>Categoría/Encapsulado:</b> {item.get('category')}<br>"
            txt += f"<b>Lugar de Almacenado:</b> {item.get('storage_location')}<br>"
            txt += f"<b>Cantidad en Stock:</b> <b>{stock}</b> unidades<br>"
            txt += f"<b>Stock Mínimo:</b> {item.get('min_stock_quantity', 0)} unidades<br>"
            txt += f"<b>Costo Unitario:</b> {cost:.2f} {currency}<br>"
            txt += f"<b>Valor Total de Stock:</b> <span style='font-weight: bold; color: #1565C0;'>{total:.2f} {currency}</span><br>"
            txt += f"<b>Estado de Prueba:</b> {tested_str}<br>"
            txt += f"<b>Condición Física:</b> {item.get('condition')}<br>"
            doc_url = item.get('datasheet', '')
            self.history_frame.setVisible(False)

        elif module_type == 'instruments':
            self.lbl_title.setText(f"Ficha de Instrumento: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#1e88e5;'>{item.get('name')}</h3>"
            txt += f"<b>Marca y Modelo:</b> {item.get('brand')} {item.get('model')}<br>"
            txt += f"<b>Tipo:</b> {item.get('type')} | <b>S/N:</b> {item.get('serial_number')}<br>"
            txt += f"<b>Estado Operativo:</b> <b>{item.get('status', 'Operativo')}</b><br>"
            txt += f"<b>Insumos / Accesorios:</b> {item.get('supplies')}<br>"
            txt += f"<b>Descripción/Detalles:</b> {item.get('description')}<br>"
            doc_url = item.get('manual', '')
            self.history_frame.setVisible(False)

        elif module_type == 'tools':
            self.lbl_title.setText(f"Ficha de Herramienta: {item.get('name')}")
            txt = f"<h3 style='margin:0; color:#43a047;'>{item.get('name')}</h3>"
            txt += f"<b>Marca y Modelo:</b> {item.get('brand')} {item.get('model')}<br>"
            txt += f"<b>Tipo:</b> {item.get('type')}<br>"
            txt += f"<b>Estado Operativo:</b> <b>{item.get('status')}</b><br>"
            doc_url = ""
            self.history_frame.setVisible(True)
            self.lbl_hist_title.setText("Historial de Chequeos y Mantenimientos")
            self._refresh_history_table(item.get('history', []))

        elif module_type in ('analysis', 'projects'):
            if module_type == 'projects':
                self.lbl_title.setText("Resumen de Proyecto / Desarrollo")
                self.lbl_calc_section_title.setText("Documentos y Módulos de Proyecto")
                self.btn_add_calc.setText(" Agregar Elemento")
            else:
                self.lbl_title.setText("Resumen de Análisis y Pruebas")
                self.lbl_calc_section_title.setText("Cálculos y Registros de Pruebas")
                self.btn_add_calc.setText(" Agregar Cálculo")
                
            txt = f"<h3 style='margin:0; color:#8A2BE2;'>{item.get('name')}</h3>"
            txt += f"<b>Categoría:</b> {item.get('category')}<br>"
            txt += f"<b>Comentarios:</b><br><span style='color:#444;'>{item.get('comment', 'Sin comentarios.')}</span><br>"
            self.lbl_an_summary.setText(txt)
            self._refresh_calculations()
            doc_url = ""
            msds_url = ""

        elif module_type == 'calibrators':
            self.lbl_title.setText(f"Dispositivo de Calibración: {item.get('name')}")
            self.info_stack.setCurrentIndex(3)
            last_date = item.get('last_calibration_date', 'No registrada')
            origin = item.get('origin', 'Comparada')
            comments = item.get('comments', 'Sin comentarios')
            txt = f"<h3 style='margin:0; color:#1565C0;'>{item.get('name')}</h3>"
            txt += f"<b>Tipo de Dispositivo:</b> {item.get('type')}<br>"
            txt += f"<b>Origen / Clasificación:</b> <b>{origin}</b> | <b>Última Calibración:</b> {last_date}<br>"
            txt += f"<b>Comentarios:</b> <span style='color:#444;'>{comments}</span><br>"
            self.lbl_calib_title.setText(txt)
            self._load_calibrator_data(item)
            doc_url = ""
            msds_url = ""

        else: # supplies
            self.lbl_title.setText(f"Ficha de Insumo: {item.get('name')}")
            
            from config.settings import Settings
            settings = Settings.load()
            currency = getattr(settings.general, 'cost_currency', 'CLP')
            
            stock = item.get('stock_quantity', 0)
            cost = item.get('cost_value', 0.0)
            total = stock * cost
            unit = item.get('unit', 'unidades')
            
            txt = f"<h3 style='margin:0; color:#e67e22;'>{item.get('name')}</h3>"
            txt += f"<b>Tipo de Insumo:</b> {item.get('type')}<br>"
            txt += f"<b>Marca y Modelo:</b> {item.get('brand')} {item.get('model')}<br>"
            txt += f"<b>Envase / Presentación:</b> {item.get('container')}<br>"
            txt += f"<b>Lugar de Almacenado:</b> {item.get('storage_location')}<br>"
            txt += f"<b>Cantidad en Stock:</b> <b>{stock} {unit}</b><br>"
            txt += f"<b>Stock Mínimo:</b> {item.get('min_stock_quantity', 0)} {unit}<br>"
            txt += f"<b>Costo Unitario:</b> {cost:.2f} {currency}<br>"
            txt += f"<b>Valor Total de Stock:</b> <span style='font-weight: bold; color: #1565C0;'>{total:.2f} {currency}</span><br>"
            doc_url = item.get('manual', '')
            msds_url = item.get('msds', '')
            self.history_frame.setVisible(True)
            self.lbl_hist_title.setText("Registro de Uso y Mantenimiento de Insumo")
            self._refresh_history_table(item.get('history', []))

        while self.bib_files_layout.count():
            child = self.bib_files_layout.takeAt(0)
            w = child.widget()
            if w:
                w.setParent(None)
                w.deleteLater()

        bib_img_path = None
        if item.get('image'):
            img_rel = item.get('image')
            full_img = os.path.join(cur_agenda, img_rel) if cur_agenda and not os.path.isabs(img_rel) else img_rel
            if os.path.exists(full_img):
                bib_img_path = full_img
        assigned_docs_list = []

        if cur_agenda:
            bib_path = DataStore.get_plugin_data_path(cur_agenda, 'biblioteca')
            bib_data = DataStore.load(bib_path)
            if bib_data:
                docs = bib_data.get('documents', [])
                item_id = item.get('id')
                for d in docs:
                    if item_id in d.get('assigned_element_ids', []):
                        rel = d.get('relative_path', '')
                        full = os.path.join(cur_agenda, rel)
                        if not bib_img_path and (d.get('type') == '🖼️ Imágenes' or rel.lower().endswith(IMAGE_EXTENSIONS)):
                            if os.path.exists(full):
                                bib_img_path = full
                        else:
                            if os.path.exists(full):
                                assigned_docs_list.append((d.get('name'), d.get('type'), full))

        # Buscar el primer PDF si no hay imagen
        bib_pdf_path = None
        for d_name, d_type, d_path in assigned_docs_list:
            if d_path.lower().endswith('.pdf'):
                bib_pdf_path = d_path
                break

        preview_loaded = False
        if bib_img_path and os.path.exists(bib_img_path):
            pix = load_image_pixmap(bib_img_path)
            if not pix.isNull():
                self.img_preview.setPixmap(pix.scaled(300, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                self.img_preview.setVisible(True)
                preview_loaded = True

        if not preview_loaded and bib_pdf_path and os.path.exists(bib_pdf_path):
            try:
                import fitz
                from PyQt6.QtGui import QImage
                doc = fitz.open(bib_pdf_path)
                if len(doc) > 0:
                    page = doc[0]
                    pix = page.get_pixmap(dpi=100)
                    fmt = QImage.Format.Format_RGBA8888 if pix.alpha else QImage.Format.Format_RGB888
                    qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
                    pixmap = QPixmap.fromImage(qimg.copy())
                    self.img_preview.setPixmap(pixmap.scaled(300, 150, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    self.img_preview.setVisible(True)
                    preview_loaded = True
            except Exception as e:
                print(f"Error cargando preview PDF en laboratorio: {e}")

        if not preview_loaded:
            self.img_preview.setVisible(False)

        if not assigned_docs_list and not bib_img_path:
            self.bib_files_frame.setVisible(False)
        else:
            self.bib_files_frame.setVisible(True)
            for d_name, d_type, d_path in assigned_docs_list:
                btn_d = QPushButton(f"{d_type} - {d_name}")
                btn_d.setStyleSheet("QPushButton { text-align: left; background: #E0F2F1; color: #004D40; font-weight: bold; padding: 4px 8px; border: 1px solid #80CBC4; border-radius: 4px; font-size: 11px; } QPushButton:hover { background: #B2DFDB; }")
                btn_d.clicked.connect(lambda checked, p=d_path: open_local_file(p))
                self.bib_files_layout.addWidget(btn_d)

        self.lbl_detail_text.setText(txt)
        self.btn_action_doc.setVisible(bool(doc_url))
        self.btn_action_doc.setProperty("doc_url", doc_url)
        self.btn_action_msds.setVisible(bool(msds_url))
        self.btn_action_msds.setProperty("msds_url", msds_url)

    def _refresh_calculations(self):
        while self.calc_layout.count():
            child = self.calc_layout.takeAt(0)
            w = child.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
                
        if not self.current_item: return
        
        calcs = self.current_item.get('calculations', [])
        if not calcs:
            lbl = QLabel("No hay cálculos o documentos agregados aún.")
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
                    'Texto': 'document.svg',
                    'Imagen': 'image_file.svg',
                    'Markdown (MD)': 'edit.svg',
                    'Texto Enriquecido': 'edit.svg',
                    'Editor de Código': 'document.svg',
                    'Mapa Mental': 'planner.svg',
                    'Diagrama de Flujo (Draw.io)': 'edit.svg',
                    'Dibujo / Paint': 'edit.svg',
                    'Visor 3D STL / G-Code': 'box.svg',
                    'Visor KiCad / Gerber': 'component.svg',
                    'Editor de Diagramas Esquemáticos': 'component.svg',
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

    def _open_msds(self):
        url = self.btn_action_msds.property("msds_url")
        if url:
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))

    def _open_document(self):
        url = self.btn_action_doc.property("doc_url")
        if url:
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))

    def _refresh_history_table(self, history_list: list):
        self.log_table.setRowCount(0)
        for i, log in enumerate(history_list):
            self.log_table.insertRow(i)
            
            # Fecha
            item_date = QTableWidgetItem(log.get('date', ''))
            item_date.setForeground(QColor("#111111"))
            self.log_table.setItem(i, 0, item_date)
            
            # Resultado
            res_text = log.get('result', '')
            if log.get('check_number'):
                res_text += f" (Nº: {log.get('check_number')})"
            item_result = QTableWidgetItem(res_text)
            item_result.setForeground(QColor("#111111"))
            self.log_table.setItem(i, 1, item_result)
            
            # Notas
            item_notes = QTableWidgetItem(log.get('notes', ''))
            item_notes.setForeground(QColor("#111111"))
            self.log_table.setItem(i, 2, item_notes)

    def _on_add_log(self):
        if not self.current_item: return
        
        checklist = None
        cur_agenda = getattr(self, 'agenda_path', None)
        if cur_agenda:
            data_path = DataStore.get_plugin_data_path(cur_agenda, 'laboratorio')
            data = DataStore.load(data_path)
            if data:
                checklists = data.get('checklists', [])
                for chk in checklists:
                    chk_ids = chk.get('assigned_element_ids', [])
                    if not chk_ids and chk.get('assigned_element_id'):
                        chk_ids = [chk.get('assigned_element_id')]
                    if self.current_item.get('id') in chk_ids:
                        checklist = chk
                        break

        if checklist:
            dlg = CheckListEventDialog(checklist, cur_agenda, getattr(self, 'lists', {}), parent=self)
        else:
            dlg = CalibrationLogDialog(getattr(self, 'lists', {}), parent=self)

        if dlg.exec() and dlg.log_data:
            self.current_item.setdefault('history', []).append(dlg.log_data)
            self._refresh_history_table(self.current_item.get('history', []))
            self.item_updated.emit(self.current_item, self.module_type)

    def _on_log_table_double_clicked(self, item):
        if not self.current_item: return
        row = item.row()
        history = self.current_item.get('history', [])
        if 0 <= row < len(history):
            log_entry = history[row]
            if 'checklist_answers' in log_entry:
                chk_def = None
                cur_agenda = getattr(self, 'agenda_path', None)
                if cur_agenda:
                    data_path = DataStore.get_plugin_data_path(cur_agenda, 'laboratorio')
                    data = DataStore.load(data_path)
                    if data:
                        checklists = data.get('checklists', [])
                        chk_id = log_entry.get('checklist_id', '')
                        for chk in checklists:
                            if chk.get('id') == chk_id:
                                chk_def = chk
                                break
                
                dlg = CheckListViewDialog(log_entry, chk_def, self.current_item, cur_agenda, parent=self)
                dlg.exec()

    def _on_save_card_changes(self):
        if not self.current_item: return
        self.current_item['min_stock_quantity'] = self.spin_min_stock.value()
        self.current_item['cost_value'] = self.spin_cost.value()
        self.item_updated.emit(self.current_item, self.module_type)
        self.set_item(self.current_item, self.module_type)

    # --- Calibradores: Mediciones y Puntos Patrón ---
    def _load_calibrator_data(self, item: dict):
        # 1. Cargar mediciones realizadas
        self.tbl_calib_measurements.setRowCount(0)
        measurements = item.get('measurements', [])
        for m in measurements:
            self._insert_measurement_row_data(m)

        # 2. Cargar puntos de referencia patrón
        self.tbl_ref_points.setRowCount(0)
        ref_points = item.get('reference_points', [])
        for p in ref_points:
            self._insert_ref_point_row_data(p)

    def _insert_measurement_row_data(self, m: dict):
        row = self.tbl_calib_measurements.rowCount()
        self.tbl_calib_measurements.insertRow(row)

        txt_nom = QLineEdit(str(m.get('nominal', '')))
        self.tbl_calib_measurements.setCellWidget(row, 0, txt_nom)

        cb_unit = QComboBox()
        cb_unit.setEditable(True)
        cb_unit.addItems(CALIBRATION_UNITS)
        cb_unit.setCurrentText(str(m.get('unit', 'V')))
        cb_unit.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 4px;
                font-weight: bold;
            }
            QComboBox:focus {
                border: 1px solid #1976D2;
                background-color: #F5F9FF;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #111111;
                selection-background-color: #1976D2;
                selection-color: #FFFFFF;
                border: 1px solid #90A4AE;
                outline: 0px;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item {
                color: #111111;
                background-color: #FFFFFF;
                min-height: 22px;
                padding: 3px 6px;
            }
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected {
                background-color: #1976D2;
                color: #FFFFFF;
            }
        """)
        if cb_unit.view():
            cb_unit.view().setStyleSheet("QAbstractItemView { background-color: #FFFFFF; color: #111111; selection-background-color: #1976D2; selection-color: #FFFFFF; } QAbstractItemView::item { color: #111111; background-color: #FFFFFF; min-height: 20px; } QAbstractItemView::item:hover, QAbstractItemView::item:selected { background-color: #1976D2; color: #FFFFFF; }")
        self.tbl_calib_measurements.setCellWidget(row, 1, cb_unit)

        txt_med = QLineEdit(str(m.get('measured', '')))
        self.tbl_calib_measurements.setCellWidget(row, 2, txt_med)

        txt_desv = QLineEdit(str(m.get('deviation', '')))
        self.tbl_calib_measurements.setCellWidget(row, 3, txt_desv)

        txt_temp = QLineEdit(str(m.get('temperature', '23.0')))
        self.tbl_calib_measurements.setCellWidget(row, 4, txt_temp)

        txt_notes = QLineEdit(str(m.get('notes', '')))
        self.tbl_calib_measurements.setCellWidget(row, 5, txt_notes)

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("background-color: #e57373; color: white; font-size: 10px; border-radius: 3px; font-weight: bold;")
        btn_del.clicked.connect(lambda checked, r=row: self._delete_measurement_row(r))
        self.tbl_calib_measurements.setCellWidget(row, 6, btn_del)

        # Auto cálculo de desviación
        def _calc_dev():
            try:
                nom_v = float(txt_nom.text())
                med_v = float(txt_med.text())
                diff = med_v - nom_v
                txt_desv.setText(f"{diff:+.6f}")
            except Exception:
                pass

        txt_nom.textChanged.connect(_calc_dev)
        txt_med.textChanged.connect(_calc_dev)

    def _add_measurement_row(self):
        self._insert_measurement_row_data({
            'nominal': '10.0000',
            'unit': 'V',
            'measured': '10.0002',
            'deviation': '+0.000200',
            'temperature': '23.0',
            'notes': 'Medición nominal'
        })

    def _delete_measurement_row(self, row: int):
        self.tbl_calib_measurements.removeRow(row)

    def _save_calibrator_measurements(self):
        if not self.current_item: return
        meas = []
        for r in range(self.tbl_calib_measurements.rowCount()):
            w_nom = self.tbl_calib_measurements.cellWidget(r, 0)
            w_unit = self.tbl_calib_measurements.cellWidget(r, 1)
            w_med = self.tbl_calib_measurements.cellWidget(r, 2)
            w_desv = self.tbl_calib_measurements.cellWidget(r, 3)
            w_temp = self.tbl_calib_measurements.cellWidget(r, 4)
            w_not = self.tbl_calib_measurements.cellWidget(r, 5)

            unit_val = w_unit.currentText().strip() if hasattr(w_unit, 'currentText') else 'V'
            meas.append({
                'nominal': w_nom.text().strip() if w_nom else '',
                'unit': unit_val or 'V',
                'measured': w_med.text().strip() if w_med else '',
                'deviation': w_desv.text().strip() if w_desv else '',
                'temperature': w_temp.text().strip() if w_temp else '23.0',
                'notes': w_not.text().strip() if w_not else ''
            })
        self.current_item['measurements'] = meas
        self.item_updated.emit(self.current_item, 'calibrators')
        self.btn_save_meas.setText(" ¡Guardado!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn_save_meas.setText(" Guardar Mediciones"))

    def _import_measurements_file(self):
        if not self.current_item: return
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar Archivo de Mediciones", "",
            "Archivos de Mediciones (*.csv *.tsv *.txt *.xlsx *.xls);;Archivos CSV (*.csv);;Archivos Excel (*.xlsx *.xls);;Todos los archivos (*.*)"
        )
        if not path: return

        imported_rows = []
        try:
            if path.lower().endswith(('.xlsx', '.xls')):
                import pandas as pd
                df = pd.read_excel(path)
                imported_rows = self._parse_dataframe_measurements(df)
            else:
                try:
                    import pandas as pd
                    df = pd.read_csv(path, sep=None, engine='python', encoding='utf-8-sig')
                    imported_rows = self._parse_dataframe_measurements(df)
                except Exception:
                    import csv
                    with open(path, 'r', encoding='utf-8-sig', errors='replace') as f:
                        sample = f.read(2048)
                        f.seek(0)
                        try:
                            dialect = csv.Sniffer().sniff(sample)
                            delimiter = dialect.delimiter
                        except Exception:
                            delimiter = ',' if ',' in sample else (';' if ';' in sample else '\t')
                        reader = csv.reader(f, delimiter=delimiter)
                        header = next(reader, None)
                        if header:
                            for row in reader:
                                if not row: continue
                                imported_rows.append(self._parse_row_list_measurements(header, row))

            if not imported_rows:
                QMessageBox.warning(self, "Importación", "No se encontraron filas con datos válidos en el archivo seleccionado.")
                return

            # Guardar copia del archivo en la carpeta del calibrador dentro de laboratorio/calibradores/
            if getattr(self, 'agenda_path', None) and self.current_item:
                cal_dir = get_calibrator_dir(self.agenda_path, self.current_item)
                dest_file = os.path.join(cal_dir, os.path.basename(path))
                if os.path.abspath(path) != os.path.abspath(dest_file):
                    try:
                        import shutil
                        shutil.copy2(path, dest_file)
                    except Exception:
                        pass

            for item_row in imported_rows:
                self._insert_measurement_row_data(item_row)

            self._save_calibrator_measurements()
            QMessageBox.information(self, "Importación Exitosa", f"Se importaron {len(imported_rows)} mediciones correctamente desde '{os.path.basename(path)}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Importación", f"Ocurrió un error al procesar el archivo: {e}")

    def _parse_dataframe_measurements(self, df) -> list:
        results = []
        col_names = [str(c).lower().strip() for c in df.columns]

        nom_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('nominal', 'patron', 'target', 'ref'))), 0 if len(col_names) > 0 else -1)
        unit_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('unit', 'unidad', 'u_med', 'u.'))), -1)
        med_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('medid', 'measur', 'valor', 'lectura')) and i not in (nom_idx, unit_idx)), 1 if len(col_names) > 1 and unit_idx != 1 else -1)
        desv_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('desv', 'error', 'diff', 'delta'))), -1)
        temp_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('temp', '°c', 'grados'))), -1)
        note_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('nota', 'date', 'fecha', 'coment', 'obs', 'item', 'desc'))), -1)

        import re
        for _, row in df.iterrows():
            vals = row.values
            raw_nom = str(vals[nom_idx]).strip() if 0 <= nom_idx < len(vals) and str(vals[nom_idx]) != 'nan' else ''
            raw_unit = str(vals[unit_idx]).strip() if 0 <= unit_idx < len(vals) and str(vals[unit_idx]) != 'nan' else ''
            med = str(vals[med_idx]).strip() if 0 <= med_idx < len(vals) and str(vals[med_idx]) != 'nan' else ''
            desv = str(vals[desv_idx]).strip() if 0 <= desv_idx < len(vals) and str(vals[desv_idx]) != 'nan' else ''
            temp = str(vals[temp_idx]).strip() if 0 <= temp_idx < len(vals) and str(vals[temp_idx]) != 'nan' else '23.0'
            note = str(vals[note_idx]).strip() if 0 <= note_idx < len(vals) and str(vals[note_idx]) != 'nan' else ''

            # Extraer unidad si está pegada al valor nominal
            nom = raw_nom
            unit = raw_unit
            if not unit and nom:
                m_match = re.match(r'^([+-]?[\d\.]+)\s*([a-zA-ZΩµ%°]+.*)?$', nom)
                if m_match and m_match.group(2):
                    nom = m_match.group(1).strip()
                    unit = m_match.group(2).strip()

            if nom or med:
                if not desv or desv == 'nan':
                    try:
                        desv = f"{(float(med) - float(nom)):+.6f}"
                    except Exception:
                        desv = ''
                results.append({
                    'nominal': nom,
                    'unit': unit or 'V',
                    'measured': med,
                    'deviation': desv,
                    'temperature': temp if temp != 'nan' else '23.0',
                    'notes': note if note != 'nan' else ''
                })
        return results

    def _parse_row_list_measurements(self, header: list, row: list) -> dict:
        col_names = [str(c).lower().strip() for c in header]
        vals = row
        nom_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('nominal', 'patron', 'target', 'ref'))), 0 if len(col_names) > 0 else -1)
        unit_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('unit', 'unidad', 'u_med', 'u.'))), -1)
        med_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('medid', 'measur', 'valor', 'lectura')) and i not in (nom_idx, unit_idx)), 1 if len(col_names) > 1 and unit_idx != 1 else -1)
        desv_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('desv', 'error', 'diff', 'delta'))), -1)
        temp_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('temp', '°c', 'grados'))), -1)
        note_idx = next((i for i, c in enumerate(col_names) if any(k in c for k in ('nota', 'date', 'fecha', 'coment', 'obs', 'item', 'desc'))), -1)

        raw_nom = str(vals[nom_idx]).strip() if 0 <= nom_idx < len(vals) else ''
        raw_unit = str(vals[unit_idx]).strip() if 0 <= unit_idx < len(vals) else ''
        med = str(vals[med_idx]).strip() if 0 <= med_idx < len(vals) else ''
        desv = str(vals[desv_idx]).strip() if 0 <= desv_idx < len(vals) else ''
        temp = str(vals[temp_idx]).strip() if 0 <= temp_idx < len(vals) else '23.0'
        note = str(vals[note_idx]).strip() if 0 <= note_idx < len(vals) else ''

        import re
        nom = raw_nom
        unit = raw_unit
        if not unit and nom:
            m_match = re.match(r'^([+-]?[\d\.]+)\s*([a-zA-ZΩµ%°]+.*)?$', nom)
            if m_match and m_match.group(2):
                nom = m_match.group(1).strip()
                unit = m_match.group(2).strip()

        if not desv:
            try:
                desv = f"{(float(med) - float(nom)):+.6f}"
            except Exception:
                desv = ''

        return {
            'nominal': nom,
            'unit': unit or 'V',
            'measured': med,
            'deviation': desv,
            'temperature': temp or '23.0',
            'notes': note
        }

    def _export_measurements_csv(self):
        if not self.current_item: return
        cal_dir = get_calibrator_dir(self.agenda_path, self.current_item) if getattr(self, 'agenda_path', None) and self.current_item else ""
        def_file = os.path.join(cal_dir, f"mediciones_{self.current_item.get('name', 'calibrador')}.csv") if cal_dir else f"mediciones_{self.current_item.get('name', 'calibrador')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Mediciones a CSV", def_file,
            "Archivos CSV (*.csv);;Todos los archivos (*.*)"
        )
        if not path: return
        import csv
        try:
            with open(path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Valor Nominal", "Unidad", "Valor Medido", "Desviacion / Error", "Temperatura (C)", "Fecha / Notas"])
                for r in range(self.tbl_calib_measurements.rowCount()):
                    w_nom = self.tbl_calib_measurements.cellWidget(r, 0)
                    w_unit = self.tbl_calib_measurements.cellWidget(r, 1)
                    w_med = self.tbl_calib_measurements.cellWidget(r, 2)
                    w_desv = self.tbl_calib_measurements.cellWidget(r, 3)
                    w_temp = self.tbl_calib_measurements.cellWidget(r, 4)
                    w_not = self.tbl_calib_measurements.cellWidget(r, 5)
                    unit_val = w_unit.currentText().strip() if hasattr(w_unit, 'currentText') else 'V'
                    writer.writerow([
                        w_nom.text() if w_nom else '',
                        unit_val,
                        w_med.text() if w_med else '',
                        w_desv.text() if w_desv else '',
                        w_temp.text() if w_temp else '',
                        w_not.text() if w_not else ''
                    ])
            QMessageBox.information(self, "Exportación Exitosa", f"Se exportaron las mediciones a '{os.path.basename(path)}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo guardar el archivo: {e}")

    def _insert_ref_point_row_data(self, p: dict):
        row = self.tbl_ref_points.rowCount()
        self.tbl_ref_points.insertRow(row)

        txt_mag = QLineEdit(str(p.get('magnitude', '')))
        self.tbl_ref_points.setCellWidget(row, 0, txt_mag)

        txt_nom = QLineEdit(str(p.get('nominal', '')))
        self.tbl_ref_points.setCellWidget(row, 1, txt_nom)

        cb_unit = QComboBox()
        cb_unit.setEditable(True)
        cb_unit.addItems(CALIBRATION_UNITS)
        cb_unit.setCurrentText(str(p.get('unit', 'V')))
        cb_unit.setStyleSheet("""
            QComboBox {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 4px;
                font-weight: bold;
            }
            QComboBox:focus {
                border: 1px solid #1976D2;
                background-color: #F5F9FF;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #111111;
                selection-background-color: #1976D2;
                selection-color: #FFFFFF;
                border: 1px solid #90A4AE;
                outline: 0px;
                padding: 2px;
            }
            QComboBox QAbstractItemView::item {
                color: #111111;
                background-color: #FFFFFF;
                min-height: 22px;
                padding: 3px 6px;
            }
            QComboBox QAbstractItemView::item:hover,
            QComboBox QAbstractItemView::item:selected {
                background-color: #1976D2;
                color: #FFFFFF;
            }
        """)
        if cb_unit.view():
            cb_unit.view().setStyleSheet("QAbstractItemView { background-color: #FFFFFF; color: #111111; selection-background-color: #1976D2; selection-color: #FFFFFF; } QAbstractItemView::item { color: #111111; background-color: #FFFFFF; min-height: 20px; } QAbstractItemView::item:hover, QAbstractItemView::item:selected { background-color: #1976D2; color: #FFFFFF; }")
        self.tbl_ref_points.setCellWidget(row, 2, cb_unit)

        txt_tol = QLineEdit(str(p.get('tolerance', '0.1%')))
        self.tbl_ref_points.setCellWidget(row, 3, txt_tol)

        txt_notes = QLineEdit(str(p.get('notes', '')))
        self.tbl_ref_points.setCellWidget(row, 4, txt_notes)

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("background-color: #e57373; color: white; font-size: 10px; border-radius: 3px; font-weight: bold;")
        btn_del.clicked.connect(lambda checked, r=row: self._delete_ref_point_row(r))
        self.tbl_ref_points.setCellWidget(row, 5, btn_del)

    def _add_ref_point_row(self):
        self._insert_ref_point_row_data({
            'magnitude': 'Voltaje DC (Punto Ref.)',
            'nominal': '10.0000',
            'unit': 'V',
            'tolerance': '0.05%',
            'notes': 'Punto de prueba estándar'
        })

    def _delete_ref_point_row(self, row: int):
        self.tbl_ref_points.removeRow(row)

    def _sync_ref_points_from_measurements(self):
        if not self.current_item: return
        self._save_calibrator_measurements()
        meas = self.current_item.get('measurements', [])
        if not meas:
            QMessageBox.information(self, "Sin Mediciones", "No hay mediciones registradas para sincronizar.")
            return

        self.tbl_ref_points.setRowCount(0)
        seen = set()
        for m in meas:
            nom = m.get('nominal', '').strip()
            unit = m.get('unit', 'V').strip() or 'V'
            key = (nom, unit)
            if not nom or key in seen:
                continue
            seen.add(key)
            cal_type = self.current_item.get('type', 'Referencia')
            note = m.get('notes', '').strip() or f"Punto patrón nominal {nom} {unit}"
            mag_name = f"{cal_type} ({nom} {unit})"
            self._insert_ref_point_row_data({
                'magnitude': mag_name,
                'nominal': nom,
                'unit': unit,
                'tolerance': '0.05%',
                'notes': note
            })
        self._save_calibrator_ref_points()
        QMessageBox.information(self, "Sincronización Completa", f"Se generaron {len(seen)} puntos patrón a partir de las mediciones.")

    def _save_calibrator_ref_points(self):
        if not self.current_item: return
        pts = []
        for r in range(self.tbl_ref_points.rowCount()):
            w_mag = self.tbl_ref_points.cellWidget(r, 0)
            w_nom = self.tbl_ref_points.cellWidget(r, 1)
            w_unit = self.tbl_ref_points.cellWidget(r, 2)
            w_tol = self.tbl_ref_points.cellWidget(r, 3)
            w_not = self.tbl_ref_points.cellWidget(r, 4)

            unit_val = w_unit.currentText().strip() if hasattr(w_unit, 'currentText') else 'V'
            pts.append({
                'magnitude': w_mag.text().strip() if w_mag else '',
                'nominal': w_nom.text().strip() if w_nom else '',
                'unit': unit_val or 'V',
                'tolerance': w_tol.text().strip() if w_tol else '',
                'notes': w_not.text().strip() if w_not else ''
            })
        self.current_item['reference_points'] = pts
        self.item_updated.emit(self.current_item, 'calibrators')
        self.btn_save_ref_points.setText(" ¡Guardado!")
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1500, lambda: self.btn_save_ref_points.setText(" Guardar Puntos"))


class LabRightSinglePageViewer(QWidget):
    """
    Widget de pantalla completa (single_page) para mostrar el contenido completo
    de la página derecha en modo de página única expandida.
    """
    close_requested = pyqtSignal()
    item_updated = pyqtSignal(dict, str)

    def __init__(self, item: dict, module_type: str, agenda_path: str, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item = item
        self.module_type = module_type
        self.agenda_path = agenda_path
        self.lists = lists or {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(8)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Barra superior de control
        top_bar = QFrame()
        top_bar.setFixedHeight(38)
        top_bar.setStyleSheet("background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 6px;")
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(8, 4, 10, 4)
        tb_layout.setSpacing(10)

        self.btn_back = QPushButton(" Volver a Doble Página")
        self.btn_back.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'left.svg'), color_hex="#0D47A1", size=16))
        self.btn_back.setStyleSheet("""
            QPushButton {
                border: 1px solid #1976D2;
                background: #E3F2FD;
                font-weight: bold;
                color: #0D47A1;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        self.btn_back.clicked.connect(self.close_requested.emit)
        tb_layout.addWidget(self.btn_back)

        item_name = self.item.get('name', 'Detalle del Elemento')
        item_type = self.item.get('type', self.module_type.capitalize())
        lbl_title = QLabel(f"<b>{item_name}</b> ({item_type}) — <i>Modo de Página Única</i>")
        lbl_title.setStyleSheet("font-size: 13px; color: #0D47A1; font-weight: bold; border: none; background: transparent;")
        tb_layout.addWidget(lbl_title, 1)

        layout.addWidget(top_bar)

        # Vista interna de la página derecha adaptada a pantalla completa
        self.right_view = LabRightView()
        self.right_view.hdr_frame.setVisible(False)
        self.right_view.btn_single_page.setVisible(False)
        self.right_view.layout().setContentsMargins(5, 5, 5, 5)
        self.right_view.item_updated.connect(self.item_updated.emit)
        self.right_view.set_item(self.item, self.module_type, self.agenda_path)

        layout.addWidget(self.right_view, 1)


class LaboratorioSidebar(QWidget):
    """Barra lateral para la sección de Laboratorio."""
    
    module_changed = pyqtSignal(str) # 'components', 'instruments', 'calibrators', 'tools', 'supplies', 'analysis', 'projects'
    search_changed = pyqtSignal(str)
    add_component_clicked = pyqtSignal()
    add_instrument_clicked = pyqtSignal()
    add_calibrator_clicked = pyqtSignal()
    add_tool_clicked = pyqtSignal()
    add_supply_clicked = pyqtSignal()
    add_analysis_clicked = pyqtSignal()
    add_project_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    manage_checklists_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        # 1. Acciones principales
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)

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
                background-color: #2e7d32;
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #388e3c;
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

        act_comp = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'component.svg')), "Nuevo Componente")
        act_comp.triggered.connect(self.add_component_clicked.emit)

        act_inst = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'lab.svg')), "Nuevo Instrumento")
        act_inst.triggered.connect(self.add_instrument_clicked.emit)

        act_calib = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'ruler.svg')), "Nuevo Calibrador / Referencia")
        act_calib.triggered.connect(self.add_calibrator_clicked.emit)

        act_tool = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'tools.svg')), "Nueva Herramienta")
        act_tool.triggered.connect(self.add_tool_clicked.emit)

        act_sup = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'supplies.svg')), "Nuevo Insumo")
        act_sup.triggered.connect(self.add_supply_clicked.emit)

        self.menu_new.addSeparator()

        act_an = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'tasks.svg')), "Nuevo Análisis / Prueba")
        act_an.triggered.connect(self.add_analysis_clicked.emit)

        act_proj = self.menu_new.addAction(QIcon(os.path.join(icons_dir, 'new_project.svg')), "Nuevo Proyecto / Desarrollo")
        act_proj.triggered.connect(self.add_project_clicked.emit)

        self.btn_new_item.setMenu(self.menu_new)
        actions_layout.addWidget(self.btn_new_item)

        # Botón de Listas de Chequeo (Independiente)
        btn_style = """
            QPushButton { text-align: left; padding: 5px 8px; border-radius: 5px; background-color: rgba(255, 255, 255, 0.08); color: #ffffff; font-weight: bold; font-size: 11px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """
        btn_checklists = QPushButton(" Listas de Chequeo")
        btn_checklists.setIcon(QIcon(os.path.join(icons_dir, 'tasks.svg')))
        btn_checklists.setStyleSheet(btn_style)
        btn_checklists.clicked.connect(self.manage_checklists_clicked.emit)
        actions_layout.addWidget(btn_checklists)

        layout.addLayout(actions_layout)

        # 2. Buscador
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en lab/taller...")
        self.search_input.addAction(QIcon(os.path.join(icons_dir, 'search.svg')), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setStyleSheet("QLineEdit { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px 8px; }")
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        # 3. Módulos / Categorías
        lbl_mod = QLabel("Módulos de Laboratorio")
        lbl_mod.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_mod)

        mods_layout = QVBoxLayout()
        mods_layout.setSpacing(2)
        self.mod_group = QButtonGroup(self)
        
        m_list = [
            ('components', ' Componentes', 'component.svg'),
            ('instruments', ' Instrumentos', 'lab.svg'),
            ('calibrators', ' Calibradores', 'ruler.svg'),
            ('tools', ' Herramientas', 'tools.svg'),
            ('supplies', ' Insumos & Mat.', 'supplies.svg'),
            ('analysis', ' Análisis y Pruebas', 'tasks.svg'),
            ('projects', ' Desarrollo y Proyectos', 'new_project.svg')
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
            if mid == 'components': btn.setChecked(True)
        layout.addLayout(mods_layout)

        layout.addStretch()

        # 4. Botón de engranaje inferior izquierdo
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Laboratorio")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)


class LaboratorioPlugin(PluginBase):
    """Plugin para la sección de Laboratorio."""

    trash_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._data = {'components': [], 'instruments': [], 'calibrators': [], 'tools': [], 'supplies': [], 'lists': dict(DEFAULT_LISTS), 'checklists': [], '_trash': []}
        self._trash = []
        self._is_modified = False
        self.active_module = 'components'
        self.search_query = ''
        self._current_page = 1

        # Sidebar
        self._sidebar = LaboratorioSidebar()
        self._sidebar.module_changed.connect(self._on_module_changed)
        self._sidebar.search_changed.connect(self._on_search_changed)
        self._sidebar.add_component_clicked.connect(self._on_add_component)
        self._sidebar.add_instrument_clicked.connect(self._on_add_instrument)
        self._sidebar.add_calibrator_clicked.connect(self._on_add_calibrator)
        self._sidebar.add_tool_clicked.connect(self._on_add_tool)
        self._sidebar.add_supply_clicked.connect(self._on_add_supply)
        self._sidebar.add_analysis_clicked.connect(self._on_add_analysis)
        self._sidebar.add_project_clicked.connect(self._on_add_project)
        self._sidebar.settings_clicked.connect(self._on_show_settings)
        self._sidebar.manage_checklists_clicked.connect(self._on_manage_checklists)

        # Pages
        self._left_page = LabLeftView()
        self._right_page = LabRightView()

        self._left_page.item_selected.connect(self._on_item_selected)
        self._left_page.edit_item_requested.connect(self._on_edit_item)
        self._left_page.pagination_changed.connect(self._on_left_page_pagination_changed)
        self._left_page.instrument_nav.back_requested.connect(self._on_close_instrument_records)
        self._left_page.instrument_nav.section_changed.connect(self._on_instrument_section_changed)
        
        self._right_page.item_updated.connect(self._on_item_updated)
        self._right_page.add_calculation_requested.connect(self._on_add_calculation)
        self._right_page.edit_calculation_requested.connect(self._on_edit_calculation)
        self._right_page.open_single_page_requested.connect(self._on_open_single_page)
        self._right_page.open_single_page_right_requested.connect(self._on_open_right_single_page)
        self._right_page.open_instrument_records_requested.connect(self._on_open_instrument_records)
        self._right_page.instrument_records_container.single_page_requested.connect(self._on_toggle_specs_single_page)
        self._right_page.instrument_records_container.open_structure_editor_requested.connect(self._on_open_structure_editor)
        self._right_page.instrument_records_container.open_guide_runner_requested.connect(self._on_open_guide_runner)

    def get_total_pages(self) -> int:
        return self._left_page.get_total_pages()

    def get_current_page(self) -> int:
        return self._current_page

    def go_to_page(self, page_num: int):
        total = self.get_total_pages()
        self._current_page = max(1, min(page_num, total))
        self._update_views()

    def _update_views(self):
        items = self._data.get(self.active_module, [])
        sort_order = self._data.get('sort_order', 'alpha_asc')
        self._left_page.set_data(items, self.active_module, self.search_query, self._current_page, sort_order=sort_order)
        total = self._left_page.get_total_pages()
        if self._current_page > total:
            self._current_page = total
        self.page_changed.emit(self._current_page, total)

    def _on_left_page_pagination_changed(self, page: int, total: int):
        self._current_page = page
        self.page_changed.emit(page, total)

    def _on_module_changed(self, module_name: str):
        if self._left_page.stack.currentIndex() == 2:
            self._left_page.hdr_frame.setVisible(True)
            self._left_page.stack.setCurrentIndex(0)
            self._right_page.hdr_frame.setVisible(True)
        self.active_module = module_name
        self._current_page = 1
        self._update_views()
        self._right_page.set_item(None, module_name, getattr(self, 'agenda_path', None))

    def _on_search_changed(self, query: str):
        self.search_query = query
        self._current_page = 1
        self._update_views()

    def _on_item_selected(self, item: dict, module_type: str):
        if self._left_page.stack.currentIndex() == 2:
            self._left_page.hdr_frame.setVisible(True)
            self._left_page.stack.setCurrentIndex(0)
            self._right_page.hdr_frame.setVisible(True)
        self._right_page.set_item(item, module_type, getattr(self, 'agenda_path', None))

    def _on_item_updated(self, item: dict, module_type: str):
        self._is_modified = True
        self._update_views()
        if getattr(self, 'agenda_path', None):
            self.save_data(self.agenda_path)

    def _on_add_component(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = ComponentDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('components', []).append(dlg.item_data)
            self.active_module = 'components'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'components')

    def _on_add_instrument(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = InstrumentDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('instruments', []).append(dlg.item_data)
            self.active_module = 'instruments'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'instruments')

    def _on_add_calibrator(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = CalibratorDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('calibrators', []).append(dlg.item_data)
            self.active_module = 'calibrators'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'calibrators')

    def _on_add_tool(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = ToolDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('tools', []).append(dlg.item_data)
            self.active_module = 'tools'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'tools')

    def _on_add_supply(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = SupplyDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('supplies', []).append(dlg.item_data)
            self.active_module = 'supplies'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'supplies')

    def _on_add_analysis(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = AnalysisDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('analysis', []).append(dlg.item_data)
            self.active_module = 'analysis'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'analysis')

    def _on_add_project(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = ProjectDialog(lists=lists, parent=self._sidebar.window())
        if dlg.exec() and dlg.item_data:
            self._data.setdefault('projects', []).append(dlg.item_data)
            self.active_module = 'projects'
            self._is_modified = True
            self._current_page = 9999
            self._update_views()
            self._right_page.set_item(dlg.item_data, 'projects')

    def _on_edit_item(self, item: dict, module_type: str):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        old_name = item.get('name')
        if module_type == 'components':
            dlg = ComponentDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'instruments':
            dlg = InstrumentDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'calibrators':
            dlg = CalibratorDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'tools':
            dlg = ToolDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'analysis':
            dlg = AnalysisDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())
        elif module_type == 'projects':
            dlg = ProjectDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())
        else:
            dlg = SupplyDialog(item_to_edit=item, lists=lists, parent=self._sidebar.window())

        if dlg.exec():
            items = self._data.get(module_type, [])
            if getattr(dlg, 'is_delete', False):
                if item in items:
                    items.remove(item)
                    self.move_to_trash(item)
                    self._is_modified = True
                    self._update_views()
                    self._right_page.set_item(None, module_type)
                    self.trash_changed.emit()
            elif dlg.item_data:
                idx = items.index(item) if item in items else -1
                if idx >= 0:
                    items[idx] = dlg.item_data
                    
                    if module_type in ('analysis', 'projects') and getattr(self, 'agenda_path', None):
                        sub_folder = 'desarrollo' if module_type == 'projects' else 'analisis'
                        new_name = dlg.item_data.get('name')
                        if old_name and new_name and old_name != new_name:
                            old_safe = "".join([c for c in old_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip()
                            new_safe = "".join([c for c in new_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip()
                            if old_safe and new_safe and old_safe != new_safe:
                                old_dir = os.path.join(self.agenda_path, 'laboratorio', sub_folder, old_safe)
                                new_dir = os.path.join(self.agenda_path, 'laboratorio', sub_folder, new_safe)
                                if os.path.exists(old_dir) and not os.path.exists(new_dir):
                                    try:
                                        import shutil
                                        shutil.move(old_dir, new_dir)
                                    except Exception as e:
                                        print(f"Error renaming directory: {e}")
                                        
                    self._is_modified = True
                    self._update_views()
                    self._right_page.set_item(dlg.item_data, module_type)

    def _on_add_calculation(self, item_analysis: dict):
        if not item_analysis: return
        if self.active_module == 'projects':
            dlg = ProjectCalculationDialog(parent=self._sidebar.window())
        else:
            dlg = CalculationDialog(parent=self._sidebar.window())
            
        if dlg.exec() and dlg.item_data:
            item_analysis.setdefault('calculations', []).append(dlg.item_data)
            self._is_modified = True
            self._right_page._refresh_calculations()
            if getattr(self, 'agenda_path', None):
                self.save_data(self.agenda_path)

    def _on_edit_calculation(self, calc: dict, item_analysis: dict):
        if self.active_module == 'projects':
            dlg = ProjectCalculationDialog(item_to_edit=calc, parent=self._sidebar.window())
        else:
            dlg = CalculationDialog(item_to_edit=calc, parent=self._sidebar.window())
            
        if dlg.exec():
            calcs = item_analysis.setdefault('calculations', [])
            if getattr(dlg, 'is_delete', False):
                if calc in calcs:
                    calcs.remove(calc)
                    
                    if self.active_module == 'projects':
                        calc['_parent_project_id'] = item_analysis.get('id')
                        calc['_parent_project_name'] = item_analysis.get('name')
                    else:
                        calc['_parent_analysis_id'] = item_analysis.get('id')
                        calc['_parent_analysis_name'] = item_analysis.get('name')
                    
                    self.move_to_trash(calc)
                    self.trash_changed.emit()
                    
                    self._is_modified = True
                    self._right_page._refresh_calculations()
                    if getattr(self, 'agenda_path', None):
                        self.save_data(self.agenda_path)
            elif dlg.item_data:
                idx = calcs.index(calc) if calc in calcs else -1
                if idx >= 0:
                    calcs[idx] = dlg.item_data
                    self._is_modified = True
                    self._right_page._refresh_calculations()
                    if getattr(self, 'agenda_path', None):
                        self.save_data(self.agenda_path)

    def _on_open_single_page(self, calc: dict, item_analysis: dict):
        if not getattr(self, 'agenda_path', None): return
        
        # Clear existing editor if any
        while self._left_page.editor_layout.count():
            child = self._left_page.editor_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()
                
        sub_folder = 'desarrollo' if self.active_module == 'projects' else 'analisis'
        calc_type = calc.get('type')
        if calc_type == 'Editor de Código':
            editor = CodeEditorWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Mapa Mental':
            editor = MindMapEditorWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Diagrama de Flujo (Draw.io)':
            editor = FlowchartEditorWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Dibujo / Paint':
            editor = PaintEditorWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Visor 3D STL / G-Code':
            editor = STL3DViewerWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Visor KiCad / Gerber':
            editor = GerberKiCadViewerWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Editor de Diagramas Esquemáticos':
            editor = SchematicEditorWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        elif calc_type == 'Documentación Biblioteca':
            editor = LibraryDocViewerWidget(calc, item_analysis, self.agenda_path, parent=self._left_page.editor_container)
        else:
            editor = CalculationEditorWidget(calc, item_analysis, self.agenda_path, sub_folder=sub_folder, parent=self._left_page.editor_container)
        
        def _close_single_page():
            self._left_page.stack.setCurrentIndex(0)
            while self._left_page.editor_layout.count():
                child = self._left_page.editor_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()
            self.single_page_requested.emit(False)
            self._left_page._refresh()
            
        def _on_save():
            self._is_modified = True
            if getattr(self, 'agenda_path', None):
                self.save_data(self.agenda_path)
                
        editor.close_requested.connect(_close_single_page)
        editor.saved.connect(_on_save)
        
        self._left_page.editor_layout.addWidget(editor)
        self._left_page.stack.setCurrentIndex(1)
        
        self.single_page_requested.emit(True)

    def _on_open_right_single_page(self, item: dict, module_type: str):
        if not getattr(self, 'agenda_path', None) or not item: return

        # Limpiar cualquier vista previa del editor
        while self._left_page.editor_layout.count():
            child = self._left_page.editor_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        viewer = LabRightSinglePageViewer(item, module_type, self.agenda_path, lists=self._data.get('lists', {}), parent=self._left_page.editor_container)

        def _close():
            self._left_page.stack.setCurrentIndex(0)
            while self._left_page.editor_layout.count():
                child = self._left_page.editor_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()
            self.single_page_requested.emit(False)
            self._left_page._refresh()
            self._right_page.set_item(item, module_type, self.agenda_path)

        def _on_updated(up_item, m_type):
            self._on_item_updated(up_item, m_type)

        viewer.close_requested.connect(_close)
        viewer.item_updated.connect(_on_updated)

        self._left_page.editor_layout.addWidget(viewer)
        self._left_page.stack.setCurrentIndex(1)

        self.single_page_requested.emit(True)

    def _on_open_instrument_records(self, item: dict):
        if not getattr(self, 'agenda_path', None) or not item:
            return

        # Asegurar creación de directorio del instrumento
        get_instrument_dir(self.agenda_path, item)

        self._left_page.instrument_nav.set_instrument(item, self.agenda_path)
        self._left_page.hdr_frame.setVisible(False)
        self._left_page.stack.setCurrentIndex(2)

        self._right_page.hdr_frame.setVisible(False)
        self._right_page.instrument_records_container.set_data(item, self.agenda_path, self._data.get('lists', {}))
        self._right_page.instrument_records_container.show_section('ficha')
        self._right_page.stack.setCurrentIndex(2)

    def _on_close_instrument_records(self):
        self._left_page.hdr_frame.setVisible(True)
        self._left_page.stack.setCurrentIndex(0)

        self._right_page.hdr_frame.setVisible(True)
        self._right_page.stack.setCurrentIndex(1 if self._right_page.current_item else 0)
        if self._right_page.current_item:
            self._right_page.set_item(self._right_page.current_item, self.active_module, getattr(self, 'agenda_path', None))
        self._update_views()

    def _on_instrument_section_changed(self, section_id: str):
        self._right_page.instrument_records_container.show_section(section_id)

    def _on_toggle_specs_single_page(self, enable: bool):
        if enable:
            if not getattr(self, 'agenda_path', None) or not self._right_page.instrument_records_container.item:
                return
            item = self._right_page.instrument_records_container.item

            # Limpiar editor previo
            while self._left_page.editor_layout.count():
                child = self._left_page.editor_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()

            # Crear vista de especificaciones para página única (panorámica)
            from plugins.laboratorio.instrument_records import InstrumentSpecificationsView
            specs_single = InstrumentSpecificationsView()
            specs_single.set_single_page_mode(True)
            specs_single.set_data(item, self.agenda_path)
            specs_single.single_page_requested.connect(self._on_toggle_specs_single_page)

            self._left_page.editor_layout.addWidget(specs_single)
            self._left_page.stack.setCurrentIndex(1)
            self.single_page_requested.emit(True)
        else:
            # Volver a vista individual normal (doble página)
            self._left_page.stack.setCurrentIndex(2) # Volver al panel de navegación del instrumento
            while self._left_page.editor_layout.count():
                child = self._left_page.editor_layout.takeAt(0)
                if child and child.widget():
                    child.widget().deleteLater()
            self.single_page_requested.emit(False)
            if self._right_page.instrument_records_container.item:
                self._right_page.instrument_records_container.view_specs.set_data(
                    self._right_page.instrument_records_container.item, self.agenda_path
                )

    def _on_open_structure_editor(self, item: dict, agenda_path: str):
        if not item or not agenda_path: return
        while self._left_page.editor_layout.count():
            child = self._left_page.editor_layout.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()

        from plugins.laboratorio.instrument_records import GuideStructureEditorWidget
        editor = GuideStructureEditorWidget(item, agenda_path, parent=self._left_page.editor_container)
        editor.back_requested.connect(self._on_close_calibration_single_page)

        self._left_page.editor_layout.addWidget(editor)
        self._left_page.stack.setCurrentIndex(1)
        self.single_page_requested.emit(True)

    def _on_open_guide_runner(self, item: dict, agenda_path: str, test_run: dict, structure: dict):
        if not item or not agenda_path: return
        while self._left_page.editor_layout.count():
            child = self._left_page.editor_layout.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()

        from plugins.laboratorio.instrument_records import GuideRunnerWidget
        runner = GuideRunnerWidget(item, agenda_path, test_run, structure, parent=self._left_page.editor_container)
        runner.back_requested.connect(self._on_close_calibration_single_page)

        self._left_page.editor_layout.addWidget(runner)
        self._left_page.stack.setCurrentIndex(1)
        self.single_page_requested.emit(True)

    def _on_close_calibration_single_page(self):
        self._left_page.stack.setCurrentIndex(2) # Volver al panel de navegación del instrumento
        while self._left_page.editor_layout.count():
            child = self._left_page.editor_layout.takeAt(0)
            if child and child.widget(): child.widget().deleteLater()
        self.single_page_requested.emit(False)
        if self._right_page.instrument_records_container.item:
            self._right_page.instrument_records_container.view_calib.set_data(
                self._right_page.instrument_records_container.item, self.agenda_path
            )

    def _on_show_settings(self):
        lists = self._data.setdefault('lists', dict(DEFAULT_LISTS))
        dlg = LabSettingsDialog(lists=lists, plugin_data=self._data, parent=self._sidebar.window())
        if dlg.exec():
            self._is_modified = True
            self._update_views()
            if getattr(self, 'agenda_path', None):
                self.save_data(self.agenda_path)

    def _on_manage_checklists(self):
        dlg = CheckListManagerDialog(plugin_data=self._data, parent=self._sidebar.window())
        if dlg.exec():
            self._is_modified = True
            if getattr(self, 'agenda_path', None):
                self.save_data(self.agenda_path)

    # --- Papelera ---
    def move_to_trash(self, item: dict):
        self._trash.append(item)

    def get_trash_items(self) -> list:
        return self._trash

    def restore_item(self, index: int):
        if 0 <= index < len(self._trash):
            item = self._trash.pop(index)
            if '_parent_analysis_id' in item:
                parent_id = item.get('_parent_analysis_id')
                parent_name = item.get('_parent_analysis_name')
                restored = False
                for an in self._data.get('analysis', []):
                    if an.get('id') == parent_id or an.get('name') == parent_name:
                        an.setdefault('calculations', []).append(item)
                        restored = True
                        break
                if not restored and self._data.get('analysis'):
                    self._data['analysis'][0].setdefault('calculations', []).append(item)
            elif '_parent_project_id' in item:
                parent_id = item.get('_parent_project_id')
                parent_name = item.get('_parent_project_name')
                restored = False
                for pr in self._data.get('projects', []):
                    if pr.get('id') == parent_id or pr.get('name') == parent_name:
                        pr.setdefault('calculations', []).append(item)
                        restored = True
                        break
                if not restored and self._data.get('projects'):
                    self._data['projects'][0].setdefault('calculations', []).append(item)
            elif 'tested' in item:
                self._data.setdefault('components', []).append(item)
            elif 'serial_number' in item:
                self._data.setdefault('instruments', []).append(item)
            elif item.get('id', '').startswith('calib_') or ('origin' in item and 'reference_points' in item):
                self._data.setdefault('calibrators', []).append(item)
            elif 'status' in item:
                self._data.setdefault('tools', []).append(item)
            elif 'calculations' in item:
                # Si es un proyecto o un análisis
                if item.get('id', '').startswith('proj_'):
                    self._data.setdefault('projects', []).append(item)
                else:
                    self._data.setdefault('analysis', []).append(item)
            else:
                self._data.setdefault('supplies', []).append(item)
            self._is_modified = True
            self._update_views()
            self.trash_changed.emit()

    def get_name(self) -> str: return "Laboratorio"
    def get_id(self) -> str: return "laboratorio"
    def get_icon(self) -> str: return "lab.svg"
    def get_tab_color(self) -> str: return "#8A2BE2"
    def get_order(self) -> int: return 6

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

    def on_activate(self):
        super().on_activate()
        if getattr(self, 'agenda_path', None):
            self.load_data(self.agenda_path)
        self._update_views()

    def load_data(self, agenda_path: str):
        self.agenda_path = agenda_path
        self._right_page.agenda_path = agenda_path
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data = loaded
            self._trash = loaded.get('_trash', [])
            if 'calibrators' not in self._data:
                self._data['calibrators'] = []
            if 'lists' not in self._data:
                self._data['lists'] = dict(DEFAULT_LISTS)
            else:
                for k, v in DEFAULT_LISTS.items():
                    if k not in self._data['lists']:
                        self._data['lists'][k] = v
            if 'checklists' not in self._data:
                self._data['checklists'] = []
        else:
            self._data = {
                'components': [], 'instruments': [], 'calibrators': [], 'tools': [], 'supplies': [], 'analysis': [],
                'lists': dict(DEFAULT_LISTS), 'checklists': [], '_trash': []
            }
            self._trash = []
            
        # Load analysis data from separate file inside laboratorio/
        self._migrate_analysis_storage(agenda_path)
        
        analysis_path = os.path.join(agenda_path, 'laboratorio', 'analisis.json')
        analysis_loaded = DataStore.load(analysis_path)
        if analysis_loaded and 'analysis' in analysis_loaded:
            self._data['analysis'] = analysis_loaded['analysis']
        elif 'analysis' not in self._data:
            self._data['analysis'] = []

        # Load projects data from separate file inside laboratorio/
        project_path = os.path.join(agenda_path, 'laboratorio', 'desarrollo.json')
        project_loaded = DataStore.load(project_path)
        if project_loaded and 'projects' in project_loaded:
            self._data['projects'] = project_loaded['projects']
        elif 'projects' not in self._data:
            self._data['projects'] = []

        # Load calibrators data from separate file inside laboratorio/
        calibrators_path = os.path.join(agenda_path, 'laboratorio', 'calibradores.json')
        calibrators_loaded = DataStore.load(calibrators_path)
        if calibrators_loaded and 'calibrators' in calibrators_loaded:
            self._data['calibrators'] = calibrators_loaded['calibrators']
        elif 'calibrators' not in self._data:
            self._data['calibrators'] = []

        self._migrate_id_folders_to_name(agenda_path, self._data.get('analysis', []))
        self._migrate_id_folders_to_name(agenda_path, self._data.get('projects', []), folder_name='desarrollo')
        
        self._right_page.agenda_path = self.agenda_path
        self._right_page.lists = self._data['lists']
        self._update_views()
        self._is_modified = False

    def _migrate_analysis_storage(self, agenda_path: str):
        """Migra archivos y carpetas desde data/laboratorio hacia laboratorio/."""
        import shutil
        old_base = os.path.join(agenda_path, 'data', 'laboratorio')
        new_base = os.path.join(agenda_path, 'laboratorio')
        
        if os.path.exists(old_base):
            os.makedirs(new_base, exist_ok=True)
            old_json = os.path.join(old_base, 'analisis.json')
            new_json = os.path.join(new_base, 'analisis.json')
            if os.path.exists(old_json) and not os.path.exists(new_json):
                try: shutil.move(old_json, new_json)
                except Exception: pass
            elif os.path.exists(old_json) and os.path.exists(new_json):
                try: os.remove(old_json)
                except Exception: pass
                    
            old_bak = os.path.join(old_base, 'analisis.json.bak')
            new_bak = os.path.join(new_base, 'analisis.json.bak')
            if os.path.exists(old_bak):
                try:
                    if not os.path.exists(new_bak): shutil.move(old_bak, new_bak)
                    else: os.remove(old_bak)
                except Exception: pass

            old_dir = os.path.join(old_base, 'analisis')
            new_dir = os.path.join(new_base, 'analisis')
            if os.path.exists(old_dir):
                os.makedirs(new_dir, exist_ok=True)
                for item in os.listdir(old_dir):
                    s = os.path.join(old_dir, item)
                    d = os.path.join(new_dir, item)
                    if not os.path.exists(d):
                        try: shutil.move(s, d)
                        except Exception: pass
                try: shutil.rmtree(old_dir, ignore_errors=True)
                except Exception: pass
                    
            try:
                if os.path.exists(old_base) and not os.listdir(old_base):
                    os.rmdir(old_base)
                data_dir = os.path.join(agenda_path, 'data')
                if os.path.exists(data_dir) and not os.listdir(data_dir):
                    os.rmdir(data_dir)
            except Exception: pass

    def _migrate_id_folders_to_name(self, agenda_path: str, analysis_items: list, folder_name: str = 'analisis'):
        """Migra carpetas con ID a carpetas nombradas según el nombre del elemento de análisis/proyecto."""
        import shutil
        analisis_dir = os.path.join(agenda_path, 'laboratorio', folder_name)
        if not os.path.exists(analisis_dir): return
        for item in analysis_items:
            item_id = item.get('id')
            item_name = item.get('name')
            if item_id and item_name:
                safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
                id_dir = os.path.join(analisis_dir, item_id)
                name_dir = os.path.join(analisis_dir, safe_name)
                if os.path.exists(id_dir) and id_dir != name_dir:
                    if not os.path.exists(name_dir):
                        try: shutil.move(id_dir, name_dir)
                        except Exception as e: print(f"Error migrating ID folder: {e}")

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            
            # Guardar analisis.json, desarrollo.json y calibradores.json dentro de laboratorio/
            analysis_data = {'analysis': self._data.get('analysis', [])}
            analysis_path = os.path.join(agenda_path, 'laboratorio', 'analisis.json')

            project_data = {'projects': self._data.get('projects', [])}
            project_path = os.path.join(agenda_path, 'laboratorio', 'desarrollo.json')

            calibrator_data = {'calibrators': self._data.get('calibrators', [])}
            calibrator_path = os.path.join(agenda_path, 'laboratorio', 'calibradores.json')
            
            # Preparar datos principales sin duplicar 'analysis', 'projects' ni 'calibrators'
            main_data = self._data.copy()
            if 'analysis' in main_data: del main_data['analysis']
            if 'projects' in main_data: del main_data['projects']
            if 'calibrators' in main_data: del main_data['calibrators']
                
            DataStore.save(data_path, main_data)
            DataStore.save(analysis_path, analysis_data)
            DataStore.save(project_path, project_data)
            DataStore.save(calibrator_path, calibrator_data)
            
            self._is_modified = False
