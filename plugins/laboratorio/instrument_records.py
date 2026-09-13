# =============================================================================
# Vito Organizer v2.2 - Laboratorio Plugin: Registros de Instrumentos
# =============================================================================

import os
import re
import shutil
import json
import base64
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QDate, QSize, QByteArray, QTimer
from PyQt6.QtGui import (
    QIcon, QPixmap, QDesktopServices, QTextCursor, QTextCharFormat, 
    QFont, QTextListFormat, QColor, QImage, QPainter
)
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QFileDialog, QMessageBox, QFrame, QTableWidget, 
    QTableWidgetItem, QHeaderView, QStackedWidget, QSizePolicy,
    QColorDialog, QInputDialog, QComboBox, QLineEdit, QDateEdit,
    QDoubleSpinBox, QScrollArea, QDialog, QMenu
)
from tools.math_renderer import MathRichTextEdit, FormulaDialog

from plugins.plugin_base import open_local_file, load_image_pixmap, IMAGE_EXTENSIONS, IMAGE_FILE_FILTER
from data.data_store import DataStore
from core.correlativos_manager import CorrelativosManager
from plugins.laboratorio.dialogs import (
    CalibrationLogDialog, CheckListEventDialog, CheckListViewDialog
)


def get_themed_svg_icon(icon_path: str, color_hex: str = "#0D47A1", size: int = 18) -> QIcon:
    """Carga un archivo SVG y reemplaza cualquier trazo o relleno con color_hex para máxima visibilidad en fondos claros."""
    if not os.path.exists(icon_path):
        return QIcon()
    try:
        with open(icon_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'stroke="(?!none)[^"]+"', f'stroke="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'stroke:\s*(?!none)[^;"]+', f'stroke:{color_hex}', content, flags=re.IGNORECASE)
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


def get_instrument_dir(agenda_path: str, item: dict) -> str:
    """Devuelve y asegura la existencia del directorio de almacenamiento del instrumento."""
    if not agenda_path or not item:
        return ""
    safe_name = "".join([c for c in item.get('name', 'Instrumento') if c.isalnum() or c in (' ', '_', '-')]).strip() or 'Instrumento'
    safe_name = safe_name.replace(" ", "_")
    item_id = item.get('id', 'ID000')
    folder_name = f"{item_id}_{safe_name}"
    inst_dir = os.path.join(agenda_path, 'laboratorio', 'instrumentos', folder_name)
    os.makedirs(inst_dir, exist_ok=True)
    return inst_dir


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


# =============================================================================
# 1. BARRA DE NAVEGACIÓN IZQUIERDA (Página Izquierda en Modo Registros)
# =============================================================================

class InstrumentNavSidebar(QWidget):
    """Página izquierda interactiva para navegar por los apartados de un instrumento."""
    
    back_requested = pyqtSignal()
    section_changed = pyqtSignal(str) # 'ficha', 'documentacion', 'descripcion', 'checklist', 'calibracion'

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_section = 'ficha'
        self.item = None
        self.agenda_path = None
        self.buttons = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 35, 15)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Cabecera con botón de Volver
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(6, 0, 6, 0)

        self.btn_back = QPushButton(" Volver al Inventario")
        self.btn_back.setIcon(QIcon(os.path.join(icons_dir, 'left.svg')))
        self.btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_back.setStyleSheet("""
            QPushButton {
                border: 1px solid #B0B0B0;
                background-color: #F0F0F0;
                font-weight: bold;
                font-size: 11px;
                color: #8B0000;
                padding: 3px 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border-color: #8B0000;
            }
        """)
        self.btn_back.clicked.connect(self.back_requested.emit)
        hdr_layout.addWidget(self.btn_back)
        hdr_layout.addStretch()

        layout.addWidget(self.hdr_frame)

        # Tarjeta identificadora del Instrumento con Imagen Miniatura
        self.info_card = QFrame()
        self.info_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 6px; }")
        ic_layout = QHBoxLayout(self.info_card)
        ic_layout.setContentsMargins(8, 8, 8, 8)
        ic_layout.setSpacing(10)

        # Imagen miniatura
        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(54, 54)
        self.lbl_thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_thumb.setStyleSheet("QLabel { background-color: #F4F4F4; border: 1px solid #C0C0C0; border-radius: 5px; }")
        ic_layout.addWidget(self.lbl_thumb)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(3)

        self.lbl_inst_title = QLabel("Instrumento")
        self.lbl_inst_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1565C0; border: none; background: transparent;")
        self.lbl_inst_title.setWordWrap(True)
        text_layout.addWidget(self.lbl_inst_title)

        self.lbl_inst_subtitle = QLabel("Modo Registros")
        self.lbl_inst_subtitle.setStyleSheet("color: #444444; font-size: 11px; font-weight: 500; border: none; background: transparent;")
        self.lbl_inst_subtitle.setWordWrap(True)
        text_layout.addWidget(self.lbl_inst_subtitle)

        ic_layout.addLayout(text_layout, 1)

        layout.addWidget(self.info_card)

        # Contenedor de Botones de Opciones
        options_frame = QFrame()
        options_frame.setStyleSheet("background: transparent; border: none;")
        opts_layout = QVBoxLayout(options_frame)
        opts_layout.setContentsMargins(0, 5, 0, 0)
        opts_layout.setSpacing(6)

        sections = [
            ('ficha', ' Ficha del Instrumento', 'document_dark.svg', 'document.svg'),
            ('especificaciones', ' Especificaciones', 'ruler_dark.svg', 'ruler.svg'),
            ('documentacion', ' Documentación', 'manual_dark.svg', 'manual.svg'),
            ('descripcion', ' Descripción (HTML)', 'notes_dark.svg', 'notes.svg'),
            ('checklist', ' Check List', 'check_dark.svg', 'check.svg'),
            ('calibracion', ' Calibración', 'chart.svg', 'chart.svg')
        ]

        self.section_icons = {}

        for sec_id, sec_title, dark_icon, light_icon in sections:
            btn = QPushButton(sec_title)
            self.section_icons[sec_id] = (
                os.path.join(icons_dir, dark_icon),
                os.path.join(icons_dir, light_icon)
            )
            btn.setIcon(QIcon(self.section_icons[sec_id][0]))
            btn.setFixedHeight(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(self._get_btn_style(False))
            btn.clicked.connect(lambda checked, s=sec_id: self._on_btn_clicked(s))
            opts_layout.addWidget(btn)
            self.buttons[sec_id] = btn

        opts_layout.addStretch()
        layout.addWidget(options_frame, 1)

        self._update_button_selection('ficha')

    def set_instrument(self, item: dict, agenda_path: str = None):
        self.item = item
        self.agenda_path = agenda_path
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        if item:
            name = item.get('name', 'Sin Nombre')
            brand = item.get('brand', '')
            model = item.get('model', '')
            brand_model = f"{brand} {model}".strip() if (brand or model) else name
            inst_type = item.get('type', 'Instrumento')
            self.lbl_inst_title.setText(name)
            self.lbl_inst_subtitle.setText(f"{brand_model} • {inst_type}")

            # Buscar imagen asociada para la miniatura
            thumb_loaded = False

            # 1. Campo directo de imagen (soporta ruta relativa a agenda, absoluta o base64)
            img_prop = item.get('image') or item.get('image_path')
            if img_prop:
                full_img = os.path.join(agenda_path, img_prop) if agenda_path and not os.path.isabs(img_prop) else img_prop
                if isinstance(full_img, str) and os.path.exists(full_img):
                    pix = load_image_pixmap(full_img)
                    if not pix.isNull():
                        self.lbl_thumb.setPixmap(pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        thumb_loaded = True
                elif isinstance(img_prop, str) and img_prop.startswith('data:image'):
                    try:
                        base64_data = img_prop.split(',', 1)[1] if ',' in img_prop else img_prop
                        pix = QPixmap()
                        pix.loadFromData(base64.b64decode(base64_data))
                        if not pix.isNull():
                            self.lbl_thumb.setPixmap(pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            thumb_loaded = True
                    except Exception:
                        pass

            # 2. Buscar en biblioteca si está asignada (priorizando imágenes antes que PDFs)
            if not thumb_loaded and agenda_path:
                bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
                bib_data = DataStore.load(bib_path)
                if bib_data:
                    assigned_images = []
                    assigned_pdfs = []
                    for d in bib_data.get('documents', []):
                        if item.get('id') in d.get('assigned_element_ids', []):
                            rel = d.get('relative_path', '')
                            full = os.path.join(agenda_path, rel)
                            if (d.get('type') == '🖼️ Imágenes' or rel.lower().endswith(IMAGE_EXTENSIONS)) and os.path.exists(full):
                                assigned_images.append(full)
                            elif rel.lower().endswith('.pdf') and os.path.exists(full):
                                assigned_pdfs.append(full)
                    
                    if assigned_images:
                        pix = load_image_pixmap(assigned_images[0])
                        if not pix.isNull():
                            self.lbl_thumb.setPixmap(pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            thumb_loaded = True
                    elif assigned_pdfs:
                        try:
                            import fitz
                            doc = fitz.open(assigned_pdfs[0])
                            if len(doc) > 0:
                                page = doc[0]
                                pix_f = page.get_pixmap(dpi=72)
                                fmt = QImage.Format.Format_RGBA8888 if pix_f.alpha else QImage.Format.Format_RGB888
                                qimg = QImage(pix_f.samples, pix_f.width, pix_f.height, pix_f.stride, fmt)
                                pix = QPixmap.fromImage(qimg)
                                self.lbl_thumb.setPixmap(pix.scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                                thumb_loaded = True
                        except Exception:
                            pass

            # 3. Fallback: icono vectorial de lab
            if not thumb_loaded:
                ico_pix = QIcon(os.path.join(icons_dir, 'lab.svg')).pixmap(30, 30)
                self.lbl_thumb.setPixmap(ico_pix)
        else:
            self.lbl_inst_title.setText("Instrumento")
            self.lbl_inst_subtitle.setText("Modo Registros")
            ico_pix = QIcon(os.path.join(icons_dir, 'lab.svg')).pixmap(30, 30)
            self.lbl_thumb.setPixmap(ico_pix)

    def _get_btn_style(self, active: bool) -> str:
        if active:
            return """
                QPushButton {
                    background-color: #1e88e5;
                    color: #FFFFFF;
                    border: 1px solid #1565C0;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                    text-align: left;
                    padding-left: 14px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: rgba(255, 255, 255, 0.85);
                    color: #111111;
                    border: 1px solid #C0B060;
                    border-radius: 6px;
                    font-weight: bold;
                    font-size: 12px;
                    text-align: left;
                    padding-left: 14px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.98);
                    border-color: #1e88e5;
                    color: #1e88e5;
                }
            """

    def _on_btn_clicked(self, sec_id: str):
        self.current_section = sec_id
        self._update_button_selection(sec_id)
        self.section_changed.emit(sec_id)

    def _update_button_selection(self, active_sec_id: str):
        for sec_id, btn in self.buttons.items():
            is_active = (sec_id == active_sec_id)
            btn.setStyleSheet(self._get_btn_style(is_active))
            if sec_id in self.section_icons:
                icon_path = self.section_icons[sec_id][1] if is_active else self.section_icons[sec_id][0]
                btn.setIcon(QIcon(icon_path))


# =============================================================================
# 2. VISTAS DE PÁGINA DERECHA PARA CADA SECCIÓN
# =============================================================================

# --- 2.1 Vista Ficha ---
class InstrumentFichaView(QWidget):
    """Muestra la ficha técnica detallada del instrumento."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.card_info = QFrame()
        self.card_info.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.88); border: 1px solid #D0C070; border-radius: 6px; padding: 12px; }")
        ci_layout = QVBoxLayout(self.card_info)
        ci_layout.setSpacing(8)

        self.lbl_title = QLabel()
        self.lbl_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1565C0; border: none; background: transparent;")
        ci_layout.addWidget(self.lbl_title)

        self.lbl_details = QLabel()
        self.lbl_details.setWordWrap(True)
        self.lbl_details.setStyleSheet("font-size: 13px; color: #111111; border: none; background: transparent; line-height: 1.4;")
        ci_layout.addWidget(self.lbl_details)

        ci_layout.addStretch()
        layout.addWidget(self.card_info, 1)

    def set_data(self, item: dict):
        self.item = item
        if not item:
            self.lbl_title.setText("Sin instrumento")
            self.lbl_details.setText("")
            return

        self.lbl_title.setText(f"{item.get('name', 'Instrumento')} ({item.get('brand', '')} {item.get('model', '')})")
        
        status_color = "#2e7d32" if item.get('status') == 'Operativo' else "#c62828"
        txt = f"<b>ID:</b> {item.get('id', 'N/A')}<br>"
        txt += f"<b>Tipo de Instrumento:</b> {item.get('type', 'General')}<br>"
        txt += f"<b>Marca:</b> {item.get('brand', 'N/A')} | <b>Modelo:</b> {item.get('model', 'N/A')}<br>"
        txt += f"<b>Número de Serie (S/N):</b> {item.get('serial_number', 'N/A')}<br>"
        txt += f"<b>Estado Operativo:</b> <span style='font-weight:bold; color:{status_color};'>{item.get('status', 'Operativo')}</span><br>"
        txt += f"<b>Insumos / Accesorios:</b> {item.get('supplies', 'Ninguno')}<br>"
        txt += f"<b>Ubicación / Almacenamiento:</b> {item.get('storage_location', 'Laboratorio')}<br><br>"
        txt += f"<b>Resumen / Detalles:</b><br>{item.get('description', 'Sin detalles adicionales.')}"
        
        self.lbl_details.setText(txt)


# --- 2.2 Vista Especificaciones Técnicas y Rangos de Medición ---
class FunctionTableCard(QFrame):
    """Tarjeta individual que aloja una tabla de rangos/escalas para una función específica del instrumento."""
    
    delete_requested = pyqtSignal(object)

    def __init__(self, func_data: dict = None, parent=None):
        super().__init__(parent)
        self.func_data = func_data or {}
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            FunctionTableCard {
                background-color: #FFFFFF;
                border: 1px solid #B0BEC5;
                border-radius: 6px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Barra superior de la Función
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        lbl_f = QLabel("<b>Función:</b>")
        lbl_f.setStyleSheet("color: #0D47A1; font-size: 12px;")
        hdr.addWidget(lbl_f)

        self.txt_func_name = QLineEdit(self.func_data.get('name', 'Tensión DC (Vdc)'))
        self.txt_func_name.setPlaceholderText("Nombre de la función, ej: Tensión DC (Vdc)")
        self.txt_func_name.setStyleSheet("QLineEdit { font-weight: bold; color: #0D47A1; font-size: 12px; background: #F0F4F8; border: 1px solid #90A4AE; border-radius: 3px; padding: 3px 6px; }")
        hdr.addWidget(self.txt_func_name, 2)

        lbl_n = QLabel("<b>Condiciones / Notas:</b>")
        lbl_n.setStyleSheet("color: #455A64; font-size: 11px;")
        hdr.addWidget(lbl_n)

        self.txt_func_desc = QLineEdit(self.func_data.get('description', ''))
        self.txt_func_desc.setPlaceholderText("Ej: Impedancia 10MΩ, Ancho de banda 45Hz-1kHz, Sobrecarga 1000V")
        self.txt_func_desc.setStyleSheet("QLineEdit { color: #222222; font-size: 11px; background: #FFFFFF; border: 1px solid #CCCCCC; border-radius: 3px; padding: 3px 6px; }")
        hdr.addWidget(self.txt_func_desc, 3)

        self.btn_add_range = QPushButton(" Agregar Rango")
        self.btn_add_range.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_range.setStyleSheet("QPushButton { background-color: #00838f; color: white; font-weight: bold; padding: 4px 8px; border-radius: 3px; font-size: 10px; } QPushButton:hover { background-color: #006064; }")
        self.btn_add_range.clicked.connect(self._add_empty_row)
        hdr.addWidget(self.btn_add_range)

        self.btn_del_func = QPushButton(" Eliminar Tabla")
        self.btn_del_func.setIcon(QIcon(os.path.join(icons_dir, 'close.svg')))
        self.btn_del_func.setStyleSheet("QPushButton { background-color: #d32f2f; color: white; font-weight: bold; padding: 4px 8px; border-radius: 3px; font-size: 10px; } QPushButton:hover { background-color: #b71c1c; }")
        self.btn_del_func.clicked.connect(lambda: self.delete_requested.emit(self))
        hdr.addWidget(self.btn_del_func)

        layout.addLayout(hdr)

        # Tabla de Rangos / Escalas
        self.tbl_ranges = QTableWidget()
        self.tbl_ranges.setColumnCount(6)
        self.tbl_ranges.setHorizontalHeaderLabels([
            "Rango / Escala", "Resolución", "Exactitud %", "Exactitud Dígitos / Cuentas", "Comentarios / Condiciones", "Acción"
        ])
        self.tbl_ranges.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tbl_ranges.setStyleSheet("""
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
        """)
        layout.addWidget(self.tbl_ranges)

        ranges = self.func_data.get('ranges', [])
        for r in ranges:
            self._insert_row_data(r)
        if not ranges:
            self._add_empty_row()

    def _insert_row_data(self, r_data: dict):
        row = self.tbl_ranges.rowCount()
        self.tbl_ranges.insertRow(row)

        txt_range = QLineEdit(str(r_data.get('range', '')))
        txt_range.setPlaceholderText("Ej: 200 mV / 20 V")
        self.tbl_ranges.setCellWidget(row, 0, txt_range)

        txt_res = QLineEdit(str(r_data.get('resolution', '')))
        txt_res.setPlaceholderText("Ej: 0.1 mV / 0.01 V")
        self.tbl_ranges.setCellWidget(row, 1, txt_res)

        txt_acc_pct = QLineEdit(str(r_data.get('accuracy_pct', '')))
        txt_acc_pct.setPlaceholderText("Ej: ±(0.5%) / 0.8%")
        self.tbl_ranges.setCellWidget(row, 2, txt_acc_pct)

        txt_acc_dig = QLineEdit(str(r_data.get('accuracy_digits', '')))
        txt_acc_dig.setPlaceholderText("Ej: 1 / 3 / 5 cuentas")
        self.tbl_ranges.setCellWidget(row, 3, txt_acc_dig)

        txt_notes = QLineEdit(str(r_data.get('notes', '')))
        txt_notes.setPlaceholderText("Ej: 45 Hz ~ 1 kHz / Cat III")
        self.tbl_ranges.setCellWidget(row, 4, txt_notes)

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("background-color: #e57373; color: white; font-size: 10px; border-radius: 3px; font-weight: bold;")
        btn_del.clicked.connect(lambda checked, r=row: self._delete_row(r))
        self.tbl_ranges.setCellWidget(row, 5, btn_del)

        self._adjust_height()

    def _add_empty_row(self):
        self._insert_row_data({'range': '', 'resolution': '', 'accuracy_pct': '', 'accuracy_digits': '', 'notes': ''})

    def _delete_row(self, row: int):
        self.tbl_ranges.removeRow(row)
        self._adjust_height()

    def _adjust_height(self):
        row_h = 28
        hdr_h = 28
        n_rows = max(1, self.tbl_ranges.rowCount())
        total_h = hdr_h + (n_rows * row_h) + 12
        self.tbl_ranges.setFixedHeight(min(total_h, 350))

    def get_data(self) -> dict:
        ranges = []
        for r in range(self.tbl_ranges.rowCount()):
            w_range = self.tbl_ranges.cellWidget(r, 0)
            w_res = self.tbl_ranges.cellWidget(r, 1)
            w_pct = self.tbl_ranges.cellWidget(r, 2)
            w_dig = self.tbl_ranges.cellWidget(r, 3)
            w_notes = self.tbl_ranges.cellWidget(r, 4)

            range_val = w_range.text().strip() if w_range else ''
            if range_val or (w_pct and w_pct.text().strip()) or (w_res and w_res.text().strip()):
                ranges.append({
                    'range': range_val,
                    'resolution': w_res.text().strip() if w_res else '',
                    'accuracy_pct': w_pct.text().strip() if w_pct else '',
                    'accuracy_digits': w_dig.text().strip() if w_dig else '',
                    'notes': w_notes.text().strip() if w_notes else ''
                })
        return {
            'name': self.txt_func_name.text().strip(),
            'description': self.txt_func_desc.text().strip(),
            'ranges': ranges
        }


class InstrumentSpecificationsView(QWidget):
    """Muestra y gestiona las especificaciones técnicas y tablas de rangos de medición del instrumento."""

    specifications_saved = pyqtSignal()
    single_page_requested = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.agenda_path = None
        self.specs_data = {}
        self.cards = []
        self.is_single_page = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Barra de Acciones Superior
        act_bar = QHBoxLayout()
        act_bar.setSpacing(6)

        self.btn_back_individual = QPushButton(" Volver a Vista Individual")
        self.btn_back_individual.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'left.svg'), color_hex="#0D47A1", size=16))
        self.btn_back_individual.setToolTip("Volver a la vista de libro normal de dos páginas")
        self.btn_back_individual.setStyleSheet("""
            QPushButton {
                border: 1px solid #1976D2;
                background: #E3F2FD;
                font-weight: bold;
                color: #0D47A1;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        self.btn_back_individual.clicked.connect(lambda: self.single_page_requested.emit(False))
        self.btn_back_individual.setVisible(False)
        act_bar.addWidget(self.btn_back_individual)

        self.btn_panoramic = QPushButton(" Vista Panorámica")
        self.btn_panoramic.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'panoramic.svg'), color_hex="#0D47A1", size=16))
        self.btn_panoramic.setToolTip("Ver y editar las especificaciones en modo de página única (pantalla completa)")
        self.btn_panoramic.setStyleSheet("""
            QPushButton {
                border: 1px solid #1976D2;
                background: #E3F2FD;
                font-weight: bold;
                color: #0D47A1;
                padding: 4px 10px;
                border-radius: 4px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #BBDEFB;
            }
        """)
        self.btn_panoramic.clicked.connect(lambda: self.single_page_requested.emit(True))
        act_bar.addWidget(self.btn_panoramic)

        lbl_title = QLabel("<b>Especificaciones y Escalas de Medición:</b>")
        lbl_title.setStyleSheet("font-size: 12px; color: #222222;")
        act_bar.addWidget(lbl_title, 1)

        self.btn_add_func = QPushButton(" Agregar Función")
        self.btn_add_func.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_func.setStyleSheet("QPushButton { background-color: #0288d1; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #0277bd; }")
        self.btn_add_func.clicked.connect(self._add_function_dialog)
        act_bar.addWidget(self.btn_add_func)

        self.btn_import_tpl = QPushButton(" Plantillas")
        self.btn_import_tpl.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
        self.btn_import_tpl.setStyleSheet("QPushButton { background-color: #7b1fa2; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #6a1b9a; }")
        self.btn_import_tpl.clicked.connect(self._import_template)
        act_bar.addWidget(self.btn_import_tpl)

        self.btn_save_specs = QPushButton(" Guardar Especificaciones")
        self.btn_save_specs.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
        self.btn_save_specs.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save_specs.clicked.connect(self.save_specifications)
        act_bar.addWidget(self.btn_save_specs)

        layout.addLayout(act_bar)

        # Scroll Area que aloja las tarjetas de tablas
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: 1px solid #CCCCCC; background-color: #FAFAFA; border-radius: 4px; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(8, 8, 8, 8)
        self.scroll_layout.setSpacing(12)

        self.empty_lbl = QLabel("No hay tablas de funciones configuradas. Haz clic en 'Agregar Función' o 'Plantillas' para comenzar.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #777777; font-style: italic; padding: 30px;")
        self.scroll_layout.addWidget(self.empty_lbl)

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

    def set_single_page_mode(self, enabled: bool):
        self.is_single_page = enabled
        self.btn_panoramic.setVisible(not enabled)
        self.btn_back_individual.setVisible(enabled)

    def set_data(self, item: dict, agenda_path: str):
        self.item = item
        self.agenda_path = agenda_path
        self._load_specifications()

    def _clear_cards(self):
        for card in self.cards:
            self.scroll_layout.removeWidget(card)
            card.deleteLater()
        self.cards.clear()

    def _load_specifications(self):
        self._clear_cards()
        if not self.item or not self.agenda_path:
            self.empty_lbl.setVisible(True)
            return

        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        file_json = os.path.join(inst_dir, 'specifications.json')

        functions = []
        if os.path.exists(file_json):
            try:
                with open(file_json, 'r', encoding='utf-8') as f:
                    self.specs_data = json.load(f)
                    functions = self.specs_data.get('functions', [])
            except Exception as e:
                print(f"Error loading specifications.json: {e}")
        else:
            self.specs_data = {}

        if functions:
            self.empty_lbl.setVisible(False)
            for f_data in functions:
                self._add_function_card(f_data)
        else:
            self.empty_lbl.setVisible(True)

    def _add_function_card(self, f_data: dict):
        self.empty_lbl.setVisible(False)
        card = FunctionTableCard(f_data, parent=self.scroll_content)
        card.delete_requested.connect(self._delete_function_card)
        self.scroll_layout.addWidget(card)
        self.cards.append(card)

    def _delete_function_card(self, card):
        if card in self.cards:
            self.cards.remove(card)
            self.scroll_layout.removeWidget(card)
            card.deleteLater()
        if not self.cards:
            self.empty_lbl.setVisible(True)

    def _add_function_dialog(self):
        common_funcs = [
            "Tensión DC (Vdc)",
            "Tensión AC (Vac)",
            "Corriente DC (Adc)",
            "Corriente AC (Aac)",
            "Resistencia (Ω)",
            "Capacitancia (F)",
            "Inductancia (H)",
            "Frecuencia (Hz)",
            "Temperatura (°C)",
            "Continuidad / Diodo (V)",
            "Ciclo de Trabajo / Duty Cycle (%)",
            "Potencia / dBm"
        ]
        choice, ok = QInputDialog.getItem(self, "Agregar Función de Medición", "Selecciona o escribe la función:", common_funcs, 0, True)
        if ok and choice.strip():
            self._add_function_card({
                'name': choice.strip(),
                'description': '',
                'ranges': []
            })

    def _import_template(self):
        templates = {
            "Multímetro Digital Estándar (3 1/2 Dígitos)": [
                {
                    'name': 'Tensión DC (Vdc)',
                    'description': 'Impedancia de entrada 10 MΩ | Sobrecarga 1000V DC',
                    'ranges': [
                        {'range': '200 mV', 'resolution': '0.1 mV', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '2 V', 'resolution': '1 mV', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '20 V', 'resolution': '10 mV', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '200 V', 'resolution': '100 mV', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '1000 V', 'resolution': '1 V', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '2', 'notes': ''}
                    ]
                },
                {
                    'name': 'Tensión AC (Vac)',
                    'description': 'Impedancia 10 MΩ | Rango de frecuencia 45 Hz ~ 400 Hz',
                    'ranges': [
                        {'range': '200 mV', 'resolution': '0.1 mV', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '2 V', 'resolution': '1 mV', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '20 V', 'resolution': '10 mV', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '200 V', 'resolution': '100 mV', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '750 V', 'resolution': '1 V', 'accuracy_pct': '±(1.2%)', 'accuracy_digits': '3', 'notes': ''}
                    ]
                },
                {
                    'name': 'Corriente DC (Adc)',
                    'description': 'Protección por fusible 500mA / 10A sin fusible',
                    'ranges': [
                        {'range': '200 µA', 'resolution': '0.1 µA', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '2 mA', 'resolution': '1 µA', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '20 mA', 'resolution': '10 µA', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '200 mA', 'resolution': '100 µA', 'accuracy_pct': '±(1.2%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '10 A', 'resolution': '10 mA', 'accuracy_pct': '±(2.0%)', 'accuracy_digits': '5', 'notes': 'Máx 10 seg'}
                    ]
                },
                {
                    'name': 'Corriente AC (Aac)',
                    'description': 'Frecuencia 45 Hz ~ 400 Hz',
                    'ranges': [
                        {'range': '2 mA', 'resolution': '1 µA', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '20 mA', 'resolution': '10 µA', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '200 mA', 'resolution': '100 µA', 'accuracy_pct': '±(1.5%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '10 A', 'resolution': '10 mA', 'accuracy_pct': '±(3.0%)', 'accuracy_digits': '5', 'notes': 'Máx 10 seg'}
                    ]
                },
                {
                    'name': 'Resistencia (Ω)',
                    'description': 'Tensión circuito abierto < 0.5V',
                    'ranges': [
                        {'range': '200 Ω', 'resolution': '0.1 Ω', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '2 kΩ', 'resolution': '1 Ω', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '20 kΩ', 'resolution': '10 Ω', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '200 kΩ', 'resolution': '100 Ω', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '2 MΩ', 'resolution': '1 kΩ', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '1', 'notes': ''},
                        {'range': '20 MΩ', 'resolution': '10 kΩ', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '2', 'notes': ''}
                    ]
                },
                {
                    'name': 'Capacitancia (F)',
                    'description': 'Medición en bornes descargados',
                    'ranges': [
                        {'range': '20 nF', 'resolution': '10 pF', 'accuracy_pct': '±(4.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '200 nF', 'resolution': '100 pF', 'accuracy_pct': '±(4.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '2 µF', 'resolution': '1 nF', 'accuracy_pct': '±(4.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '20 µF', 'resolution': '10 nF', 'accuracy_pct': '±(4.0%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '200 µF', 'resolution': '100 nF', 'accuracy_pct': '±(5.0%)', 'accuracy_digits': '5', 'notes': ''}
                    ]
                },
                {
                    'name': 'Frecuencia (Hz)',
                    'description': 'Sensibilidad 100mV ~ 1V RMS',
                    'ranges': [
                        {'range': '2 kHz', 'resolution': '1 Hz', 'accuracy_pct': '±(1.5%)', 'accuracy_digits': '5', 'notes': ''},
                        {'range': '20 kHz', 'resolution': '10 Hz', 'accuracy_pct': '±(1.5%)', 'accuracy_digits': '5', 'notes': ''},
                        {'range': '200 kHz', 'resolution': '100 Hz', 'accuracy_pct': '±(1.5%)', 'accuracy_digits': '5', 'notes': ''}
                    ]
                }
            ],
            "Multímetro True-RMS Industrial (4 1/2 Dígitos / 20.000 Cuentas)": [
                {
                    'name': 'Tensión DC (Vdc)',
                    'description': 'True-RMS | Ancho de banda DC a 100 kHz',
                    'ranges': [
                        {'range': '200 mV', 'resolution': '0.01 mV', 'accuracy_pct': '±(0.05%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '2 V', 'resolution': '0.0001 V', 'accuracy_pct': '±(0.05%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '20 V', 'resolution': '0.001 V', 'accuracy_pct': '±(0.05%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '200 V', 'resolution': '0.01 V', 'accuracy_pct': '±(0.05%)', 'accuracy_digits': '3', 'notes': ''},
                        {'range': '1000 V', 'resolution': '0.1 V', 'accuracy_pct': '±(0.08%)', 'accuracy_digits': '3', 'notes': ''}
                    ]
                },
                {
                    'name': 'Tensión AC (Vac)',
                    'description': 'True-RMS AC+DC',
                    'ranges': [
                        {'range': '200 mV', 'resolution': '0.01 mV', 'accuracy_pct': '±(0.7%)', 'accuracy_digits': '4', 'notes': '45Hz - 20kHz'},
                        {'range': '2 V', 'resolution': '0.0001 V', 'accuracy_pct': '±(0.7%)', 'accuracy_digits': '4', 'notes': '45Hz - 20kHz'},
                        {'range': '20 V', 'resolution': '0.001 V', 'accuracy_pct': '±(0.7%)', 'accuracy_digits': '4', 'notes': '45Hz - 20kHz'},
                        {'range': '200 V', 'resolution': '0.01 V', 'accuracy_pct': '±(0.7%)', 'accuracy_digits': '4', 'notes': '45Hz - 20kHz'},
                        {'range': '1000 V', 'resolution': '0.1 V', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '4', 'notes': '45Hz - 20kHz'}
                    ]
                }
            ],
            "Medidor LCR / Puente de Componentes": [
                {
                    'name': 'Inductancia (L)',
                    'description': 'Frecuencias de prueba: 100Hz / 1kHz / 10kHz',
                    'ranges': [
                        {'range': '200 µH', 'resolution': '0.1 µH', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '5', 'notes': '10 kHz'},
                        {'range': '2 mH', 'resolution': '1 µH', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '3', 'notes': '1 kHz'},
                        {'range': '20 mH', 'resolution': '10 µH', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '3', 'notes': '1 kHz'},
                        {'range': '200 mH', 'resolution': '0.1 mH', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '3', 'notes': '100 Hz'},
                        {'range': '2 H', 'resolution': '1 mH', 'accuracy_pct': '±(0.8%)', 'accuracy_digits': '3', 'notes': '100 Hz'}
                    ]
                },
                {
                    'name': 'Capacitancia (C)',
                    'description': 'Frecuencias de prueba: 100Hz / 1kHz / 10kHz',
                    'ranges': [
                        {'range': '200 pF', 'resolution': '0.1 pF', 'accuracy_pct': '±(1.0%)', 'accuracy_digits': '5', 'notes': '10 kHz'},
                        {'range': '2 nF', 'resolution': '1 pF', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '3', 'notes': '1 kHz'},
                        {'range': '20 nF', 'resolution': '10 pF', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '3', 'notes': '1 kHz'},
                        {'range': '200 nF', 'resolution': '0.1 nF', 'accuracy_pct': '±(0.5%)', 'accuracy_digits': '3', 'notes': '100 Hz'},
                        {'range': '2000 µF', 'resolution': '1 µF', 'accuracy_pct': '±(1.5%)', 'accuracy_digits': '5', 'notes': '100 Hz'}
                    ]
                }
            ]
        }

        names = list(templates.keys())
        choice, ok = QInputDialog.getItem(self, "Cargar Plantilla de Especificaciones", "Selecciona una plantilla base:", names, 0, False)
        if ok and choice in templates:
            self._clear_cards()
            for f_data in templates[choice]:
                self._add_function_card(f_data)
            QMessageBox.information(self, "Plantilla Cargada", f"Se cargó la plantilla '{choice}' con {len(templates[choice])} funciones y tablas.")

    def save_specifications(self):
        if not self.item or not self.agenda_path: return
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        file_json = os.path.join(inst_dir, 'specifications.json')

        funcs = []
        for card in self.cards:
            c_data = card.get_data()
            if c_data.get('name'):
                funcs.append(c_data)

        data = {
            'instrument_id': self.item.get('id', ''),
            'instrument_name': self.item.get('name', ''),
            'functions': funcs
        }

        try:
            with open(file_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.btn_save_specs.setText(" ¡Guardado!")
            self.specifications_saved.emit()
            QTimer.singleShot(1500, lambda: self.btn_save_specs.setText(" Guardar Especificaciones"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar specifications.json: {e}")


# --- 2.3 Vista Documentación del Instrumento ---
class InstrumentDocView(QWidget):
    """Muestra la documentación técnica y manuales directamente relacionados al instrumento."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.agenda_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Tarjeta 1: Manual de Usuario / Guía Técnica
        card_manual = QFrame()
        card_manual.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 12px; }")
        cm_layout = QVBoxLayout(card_manual)
        cm_layout.setSpacing(8)

        cm_hdr = QHBoxLayout()
        ico_man = QLabel()
        ico_man.setPixmap(QIcon(os.path.join(icons_dir, 'manual_dark.svg')).pixmap(20, 20))
        ico_man.setStyleSheet("border: none; background: transparent;")
        cm_hdr.addWidget(ico_man)

        lbl_man_title = QLabel("Manual de Usuario / Guía de Operación")
        lbl_man_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #1565C0; border: none; background: transparent;")
        cm_hdr.addWidget(lbl_man_title, 1)
        cm_layout.addLayout(cm_hdr)

        self.lbl_man_status = QLabel("Ruta / Enlace no configurado.")
        self.lbl_man_status.setStyleSheet("color: #444444; font-size: 11px; border: none; background: transparent;")
        self.lbl_man_status.setWordWrap(True)
        cm_layout.addWidget(self.lbl_man_status)

        self.btn_open_manual = QPushButton(" Abrir Manual de Usuario")
        self.btn_open_manual.setIcon(QIcon(os.path.join(icons_dir, 'manual.svg')))
        self.btn_open_manual.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_open_manual.setStyleSheet("QPushButton { background-color: #1e88e5; color: white; font-weight: bold; padding: 7px 14px; border-radius: 4px; font-size: 12px; } QPushButton:hover { background-color: #1565C0; }")
        self.btn_open_manual.clicked.connect(self._open_manual)
        cm_layout.addWidget(self.btn_open_manual)

        layout.addWidget(card_manual)

        # Tarjeta 2: Documentos vinculados desde la Biblioteca de VitoOrganizer
        card_bib = QFrame()
        card_bib.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #20B2AA; border-radius: 6px; padding: 10px; }")
        cb_layout = QVBoxLayout(card_bib)
        cb_layout.setSpacing(6)

        lbl_bib_hdr = QLabel("Archivos de Biblioteca Asignados:")
        lbl_bib_hdr.setStyleSheet("font-weight: bold; font-size: 12px; color: #004D40; border: none; background: transparent;")
        cb_layout.addWidget(lbl_bib_hdr)

        self.scroll_files = QScrollArea()
        self.scroll_files.setWidgetResizable(True)
        self.scroll_files.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.container_files = QWidget()
        self.container_files.setStyleSheet("background: transparent;")
        self.files_layout = QVBoxLayout(self.container_files)
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        self.files_layout.setSpacing(4)
        self.scroll_files.setWidget(self.container_files)
        cb_layout.addWidget(self.scroll_files, 1)

        layout.addWidget(card_bib, 1)

    def set_data(self, item: dict, agenda_path: str):
        self.item = item
        self.agenda_path = agenda_path

        if not item:
            self.lbl_man_status.setText("Sin instrumento seleccionado.")
            self.btn_open_manual.setEnabled(False)
            return

        manual_url = (item.get('manual') or '').strip()
        if manual_url:
            self.lbl_man_status.setText(f"<b>Ubicación / Enlace:</b> {manual_url}")
            self.btn_open_manual.setEnabled(True)
        else:
            self.lbl_man_status.setText("Este instrumento no tiene un archivo o enlace de manual configurado en su ficha técnica.")
            self.btn_open_manual.setEnabled(False)

        self._refresh_bib_documents()

    def _open_manual(self):
        if not self.item: return
        url = (self.item.get('manual') or '').strip()
        if not url:
            QMessageBox.information(self, "Manual", "No hay un manual configurado para este instrumento.")
            return

        # Comprobar si es URL web o archivo local
        if url.startswith("http://") or url.startswith("https://"):
            QDesktopServices.openUrl(QUrl(url))
        elif os.path.isabs(url) and os.path.exists(url):
            open_local_file(url)
        elif self.agenda_path and os.path.exists(os.path.join(self.agenda_path, url)):
            open_local_file(os.path.join(self.agenda_path, url))
        elif self.agenda_path and os.path.exists(os.path.join(self.agenda_path, 'biblioteca', url)):
            open_local_file(os.path.join(self.agenda_path, 'biblioteca', url))
        else:
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
                web_url = "https://" + url
                QDesktopServices.openUrl(QUrl(web_url))
            else:
                QDesktopServices.openUrl(QUrl(url))

    def _refresh_bib_documents(self):
        while self.files_layout.count():
            child = self.files_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        if not self.item or not self.agenda_path:
            return

        data_path = DataStore.get_plugin_data_path(self.agenda_path, 'biblioteca')
        bib_data = DataStore.load(data_path)
        found_any = False

        if bib_data:
            assigned = []
            for doc in bib_data.get('documents', []):
                doc_assigned_ids = doc.get('assigned_element_ids', [])
                tags = [str(t).lower() for t in doc.get('tags', [])]
                item_id = str(self.item.get('id', '')).lower()
                item_name = str(self.item.get('name', '')).lower()
                item_model = str(self.item.get('model', '')).lower()

                if self.item.get('id') in doc_assigned_ids:
                    assigned.append(doc)
                elif item_name and item_name in tags:
                    assigned.append(doc)
                elif item_id and item_id in tags:
                    assigned.append(doc)
                elif item_model and item_model in tags:
                    assigned.append(doc)

            for doc in assigned:
                found_any = True
                doc_name = doc.get('name') or doc.get('title') or doc.get('filename') or 'Documento'
                doc_type = doc.get('type') or doc.get('category') or 'Biblioteca'
                clean_type = doc_type.replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "")

                btn_d = QPushButton(f"{clean_type} - {doc_name}")
                btn_d.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_d.setStyleSheet("""
                    QPushButton {
                        text-align: left;
                        background: #E0F2F1;
                        color: #004D40;
                        font-weight: bold;
                        padding: 4px 8px;
                        border: 1px solid #80CBC4;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background: #B2DFDB;
                        border-color: #004D40;
                    }
                """)
                btn_d.clicked.connect(lambda checked, d=doc: self._open_bib_doc(d))
                self.files_layout.addWidget(btn_d)

        if not found_any:
            lbl_none = QLabel("No hay documentos vinculados desde la Biblioteca para este instrumento.")
            lbl_none.setStyleSheet("color: #555555; font-style: italic; border: none; padding: 10px;")
            self.files_layout.addWidget(lbl_none)

        self.files_layout.addStretch()

    def _open_bib_doc(self, doc: dict):
        url = (doc.get('url') or doc.get('link') or '').strip()
        if url:
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("file://")):
                url = "https://" + url
            QDesktopServices.openUrl(QUrl(url))
            return

        rel_path = doc.get('relative_path') or ''
        filename = doc.get('filename') or ''

        target_path = None
        if self.agenda_path:
            if rel_path:
                p = os.path.join(self.agenda_path, rel_path)
                if os.path.exists(p):
                    target_path = p
            if not target_path and filename:
                p = os.path.join(self.agenda_path, 'biblioteca', filename)
                if os.path.exists(p):
                    target_path = p
            if not target_path and filename:
                p = os.path.join(self.agenda_path, filename)
                if os.path.exists(p):
                    target_path = p

        if target_path and os.path.exists(target_path):
            open_local_file(target_path)
        else:
            QMessageBox.warning(self, "Archivo no encontrado", f"No se pudo encontrar el archivo en el disco:\n{rel_path or filename}")


# --- 2.3 Vista Descripción (Editor HTML) ---
class InstrumentDescriptionView(QWidget):
    """Editor de texto enriquecido guardado nativamente como documento HTML."""

    description_saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.agenda_path = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Barra de herramientas superior
        toolbar_card = QFrame()
        toolbar_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.95); border: 1px solid #B0B0B0; border-radius: 5px; padding: 2px; }")
        tb_layout = QHBoxLayout(toolbar_card)
        tb_layout.setContentsMargins(6, 3, 6, 3)
        tb_layout.setSpacing(4)

        btn_style = """
            QPushButton {
                border: 1px solid #A0A0A0;
                background-color: #FFFFFF;
                border-radius: 4px;
                padding: 2px;
            }
            QPushButton:hover {
                background-color: #E2E8F0;
                border-color: #1e88e5;
            }
            QPushButton:pressed {
                background-color: #CBD5E1;
            }
        """

        # 1. Negrita (Bold)
        self.btn_bold = QPushButton()
        self.btn_bold.setIcon(QIcon(os.path.join(icons_dir, 'bold_dark.svg')))
        self.btn_bold.setIconSize(QSize(16, 16))
        self.btn_bold.setFixedSize(28, 28)
        self.btn_bold.setToolTip("Negrita (Bold)")
        self.btn_bold.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bold.setStyleSheet(btn_style)
        self.btn_bold.clicked.connect(self._toggle_bold)
        tb_layout.addWidget(self.btn_bold)

        # 2. Cursiva (Italic)
        self.btn_italic = QPushButton()
        self.btn_italic.setIcon(QIcon(os.path.join(icons_dir, 'italic_dark.svg')))
        self.btn_italic.setIconSize(QSize(16, 16))
        self.btn_italic.setFixedSize(28, 28)
        self.btn_italic.setToolTip("Cursiva (Italic)")
        self.btn_italic.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_italic.setStyleSheet(btn_style)
        self.btn_italic.clicked.connect(self._toggle_italic)
        tb_layout.addWidget(self.btn_italic)

        # 3. Subrayado (Underline)
        self.btn_underline = QPushButton()
        self.btn_underline.setIcon(QIcon(os.path.join(icons_dir, 'underline_dark.svg')))
        self.btn_underline.setIconSize(QSize(16, 16))
        self.btn_underline.setFixedSize(28, 28)
        self.btn_underline.setToolTip("Subrayado (Underline)")
        self.btn_underline.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_underline.setStyleSheet(btn_style)
        self.btn_underline.clicked.connect(self._toggle_underline)
        tb_layout.addWidget(self.btn_underline)

        # Separador visual
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFrameShadow(QFrame.Shadow.Sunken)
        sep1.setStyleSheet("background-color: #B0B0B0; max-width: 1px; margin: 3px 2px;")
        tb_layout.addWidget(sep1)

        # 4. Selector de Tamaño de Fuente
        lbl_size_ico = QLabel()
        lbl_size_ico.setPixmap(QIcon(os.path.join(icons_dir, 'font_size_dark.svg')).pixmap(16, 16))
        lbl_size_ico.setToolTip("Tamaño de Fuente")
        lbl_size_ico.setStyleSheet("border: none; background: transparent; padding-left: 2px;")
        tb_layout.addWidget(lbl_size_ico)

        self.combo_font_size = QComboBox()
        self.combo_font_size.addItems(["9", "10", "11", "12", "13", "14", "16", "18", "20", "24", "28", "32", "36"])
        self.combo_font_size.setCurrentText("13")
        self.combo_font_size.setToolTip("Tamaño de Fuente")
        self.combo_font_size.setFixedSize(56, 28)
        self.combo_font_size.setStyleSheet("""
            QComboBox {
                border: 1px solid #A0A0A0;
                background-color: #FFFFFF;
                color: #111111;
                font-weight: bold;
                font-size: 11px;
                border-radius: 4px;
                padding-left: 4px;
            }
            QComboBox:hover {
                border-color: #1e88e5;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #111111;
                selection-background-color: #1e88e5;
                selection-color: #FFFFFF;
            }
        """)
        self.combo_font_size.currentTextChanged.connect(self._change_font_size)
        tb_layout.addWidget(self.combo_font_size)

        # Separador visual
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFrameShadow(QFrame.Shadow.Sunken)
        sep2.setStyleSheet("background-color: #B0B0B0; max-width: 1px; margin: 3px 2px;")
        tb_layout.addWidget(sep2)

        # 5. Color de Texto
        self.btn_color = QPushButton()
        self.btn_color.setIcon(QIcon(os.path.join(icons_dir, 'pencil_dark.svg')))
        self.btn_color.setIconSize(QSize(16, 16))
        self.btn_color.setFixedSize(28, 28)
        self.btn_color.setToolTip("Color de Texto")
        self.btn_color.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_color.setStyleSheet(btn_style)
        self.btn_color.clicked.connect(self._choose_color)
        tb_layout.addWidget(self.btn_color)

        # 6. Lista con Viñetas
        self.btn_bullet = QPushButton()
        self.btn_bullet.setIcon(QIcon(os.path.join(icons_dir, 'tasks_dark.svg')))
        self.btn_bullet.setIconSize(QSize(16, 16))
        self.btn_bullet.setFixedSize(28, 28)
        self.btn_bullet.setToolTip("Insertar Lista con Viñetas")
        self.btn_bullet.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_bullet.setStyleSheet(btn_style)
        self.btn_bullet.clicked.connect(self._insert_bullet_list)
        tb_layout.addWidget(self.btn_bullet)

        # 7. Tabla
        self.btn_table = QPushButton()
        self.btn_table.setIcon(QIcon(os.path.join(icons_dir, 'table_dark.svg')))
        self.btn_table.setIconSize(QSize(16, 16))
        self.btn_table.setFixedSize(28, 28)
        self.btn_table.setToolTip("Insertar Tabla")
        self.btn_table.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_table.setStyleSheet(btn_style)
        self.btn_table.clicked.connect(self._insert_table)
        tb_layout.addWidget(self.btn_table)

        # 8. Imagen
        self.btn_img = QPushButton()
        self.btn_img.setIcon(QIcon(os.path.join(icons_dir, 'image_file_dark.svg')))
        self.btn_img.setIconSize(QSize(16, 16))
        self.btn_img.setFixedSize(28, 28)
        self.btn_img.setToolTip("Insertar Imagen Local")
        self.btn_img.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_img.setStyleSheet(btn_style)
        self.btn_img.clicked.connect(self._insert_image)
        tb_layout.addWidget(self.btn_img)

        # 9. Fórmula Matemática
        self.btn_formula = QPushButton("📐")
        self.btn_formula.setFixedSize(28, 28)
        self.btn_formula.setToolTip("Insertar Fórmula Matemática (LaTeX)")
        self.btn_formula.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_formula.setStyleSheet(btn_style)
        self.btn_formula.clicked.connect(self._insert_formula_dialog)
        tb_layout.addWidget(self.btn_formula)

        tb_layout.addStretch()

        self.btn_save = QPushButton(" Guardar HTML")
        self.btn_save.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
        self.btn_save.setIconSize(QSize(16, 16))
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedHeight(28)
        self.btn_save.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 12px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self.save_content)
        tb_layout.addWidget(self.btn_save)

        layout.addWidget(toolbar_card)

        # Editor de texto enriquecido
        self.rich_editor = MathRichTextEdit()
        self.rich_editor.setStyleSheet("QTextEdit { background-color: rgba(255,255,255,0.92); border: 1px solid #CCC; border-radius: 6px; font-size: 13px; color: #111; padding: 10px; }")
        self.rich_editor.setPlaceholderText("Escribe y formatea la descripción detallada del instrumento (se guardará como documento HTML)...")
        layout.addWidget(self.rich_editor, 1)

    def set_data(self, item: dict, agenda_path: str):
        self.item = item
        self.agenda_path = agenda_path
        self._load_content()

    def _load_content(self):
        if not self.item or not self.agenda_path:
            self.rich_editor.clear()
            return

        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        file_html = os.path.join(inst_dir, 'description.html')

        if os.path.exists(file_html):
            try:
                with open(file_html, 'r', encoding='utf-8') as f:
                    self.rich_editor.setHtml(f.read())
            except Exception as e:
                print(f"Error loading instrument description html: {e}")
        else:
            initial_desc = self.item.get('description', '')
            if initial_desc:
                self.rich_editor.setHtml(f"<p>{initial_desc}</p>")
            else:
                self.rich_editor.clear()

    def save_content(self):
        if not self.item or not self.agenda_path: return
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        file_html = os.path.join(inst_dir, 'description.html')

        html_data = self.rich_editor.toHtml()
        try:
            with open(file_html, 'w', encoding='utf-8') as f:
                f.write(html_data)
            
            self.btn_save.setText(" ¡Guardado!")
            self.description_saved.emit()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500, lambda: self.btn_save.setText(" Guardar HTML"))
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar description.html: {e}")

    def _toggle_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.rich_editor.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        self.rich_editor.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.rich_editor.fontItalic())
        self.rich_editor.mergeCurrentCharFormat(fmt)

    def _toggle_underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.rich_editor.fontUnderline())
        self.rich_editor.mergeCurrentCharFormat(fmt)

    def _change_font_size(self, size_str: str):
        try:
            size = float(size_str)
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            self.rich_editor.mergeCurrentCharFormat(fmt)
            self.rich_editor.setFontPointSize(size)
        except (ValueError, TypeError):
            pass

    def _choose_color(self):
        col = QColorDialog.getColor(self.rich_editor.textColor(), self, "Seleccionar Color de Texto")
        if col.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(col)
            self.rich_editor.mergeCurrentCharFormat(fmt)

    def _insert_bullet_list(self):
        cursor = self.rich_editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDisc)

    def _insert_table(self):
        cursor = self.rich_editor.textCursor()
        rows, ok1 = QInputDialog.getInt(self, "Insertar Tabla", "Número de filas:", 3, 1, 50)
        if not ok1: return
        cols, ok2 = QInputDialog.getInt(self, "Insertar Tabla", "Número de columnas:", 3, 1, 20)
        if not ok2: return
        
        cursor.insertTable(rows, cols)

    def _insert_image(self):
        if not self.item or not self.agenda_path: return
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Insertar Imagen", "", IMAGE_FILE_FILTER
        )
        if file_path:
            inst_dir = get_instrument_dir(self.agenda_path, self.item)
            img_dir = os.path.join(inst_dir, 'images')
            os.makedirs(img_dir, exist_ok=True)
            fname = os.path.basename(file_path)
            dest = os.path.join(img_dir, fname)
            try:
                shutil.copy2(file_path, dest)
                cursor = self.rich_editor.textCursor()
                cursor.insertHtml(f'<br><img src="{dest}" style="max-width:100%;"><br>')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo insertar la imagen: {e}")

    def _insert_formula_dialog(self):
        if not hasattr(self, 'rich_editor'): return
        cursor = self.rich_editor.textCursor()
        selected_text = cursor.selectedText().strip()
        dlg = FormulaDialog(self, initial_latex=selected_text)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            tag = dlg.get_formula_html()
            if tag:
                cursor.insertHtml(tag)


# --- 2.4 Vista Check List ---
class InstrumentCheckListView(QWidget):
    """Muestra el historial y la ejecución de listas de chequeo asignadas al instrumento."""

    item_updated = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.agenda_path = None
        self.lists = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Cabecera de Checklist
        card_header = QFrame()
        card_header.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; padding: 10px; }")
        ch_layout = QHBoxLayout(card_header)
        ch_layout.setContentsMargins(6, 4, 6, 4)

        self.lbl_chk_status = QLabel("Historial de Chequeos y Mantenimientos")
        self.lbl_chk_status.setStyleSheet("font-weight: bold; font-size: 12px; color: #222222; border: none; background: transparent;")
        ch_layout.addWidget(self.lbl_chk_status, 1)

        self.btn_add_event = QPushButton(" Registrar Chequeo / Evento")
        self.btn_add_event.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_add_event.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add_event.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 5px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_add_event.clicked.connect(self._on_add_event)
        ch_layout.addWidget(self.btn_add_event)

        layout.addWidget(card_header)

        # Tabla de Historial
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Fecha", "Resultado / Nº", "Observaciones / Notas"])
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.log_table.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #CCC; border-radius: 4px; }")
        self.log_table.itemDoubleClicked.connect(self._on_log_double_clicked)
        layout.addWidget(self.log_table, 1)

        lbl_hint = QLabel("Haz doble clic en una fila para abrir el detalle completo del checklist.")
        lbl_hint.setStyleSheet("font-size: 11px; color: #444444; font-style: italic; border: none; background: transparent;")
        layout.addWidget(lbl_hint)

    def set_data(self, item: dict, agenda_path: str, lists: dict):
        self.item = item
        self.agenda_path = agenda_path
        self.lists = lists or {}
        self._refresh_table()

    def _refresh_table(self):
        self.log_table.setRowCount(0)
        if not self.item: return
        history = self.item.get('history', [])
        for i, log in enumerate(history):
            self.log_table.insertRow(i)

            item_date = QTableWidgetItem(log.get('date', ''))
            item_date.setForeground(QColor("#111111"))
            self.log_table.setItem(i, 0, item_date)

            res_text = log.get('result', '')
            if log.get('check_number'):
                res_text += f" (#{log.get('check_number')})"
            item_res = QTableWidgetItem(res_text)
            item_res.setForeground(QColor("#111111"))
            self.log_table.setItem(i, 1, item_res)

            item_notes = QTableWidgetItem(log.get('notes', ''))
            item_notes.setForeground(QColor("#111111"))
            self.log_table.setItem(i, 2, item_notes)

    def _on_add_event(self):
        if not self.item or not self.agenda_path: return

        checklist = None
        data_path = DataStore.get_plugin_data_path(self.agenda_path, 'laboratorio')
        data = DataStore.load(data_path)
        if data:
            checklists = data.get('checklists', [])
            for chk in checklists:
                chk_ids = chk.get('assigned_element_ids', [])
                if not chk_ids and chk.get('assigned_element_id'):
                    chk_ids = [chk.get('assigned_element_id')]
                if self.item.get('id') in chk_ids:
                    checklist = chk
                    break

        if checklist:
            dlg = CheckListEventDialog(checklist, self.agenda_path, self.lists, parent=self)
        else:
            dlg = CalibrationLogDialog(self.lists, parent=self)

        if dlg.exec() and dlg.log_data:
            self.item.setdefault('history', []).append(dlg.log_data)
            self._refresh_table()
            self.item_updated.emit(self.item)

    def _on_log_double_clicked(self, table_item):
        if not self.item or not self.agenda_path: return
        row = table_item.row()
        history = self.item.get('history', [])
        if 0 <= row < len(history):
            log_entry = history[row]
            if 'checklist_answers' in log_entry:
                chk_def = None
                data_path = DataStore.get_plugin_data_path(self.agenda_path, 'laboratorio')
                data = DataStore.load(data_path)
                if data:
                    checklists = data.get('checklists', [])
                    chk_id = log_entry.get('checklist_id', '')
                    for chk in checklists:
                        if chk.get('id') == chk_id:
                            chk_def = chk
                            break

class GuideBlockCardWidget(QFrame):
    """Tarjeta individual que representa y configura un bloque dentro del editor de estructura."""

    block_changed = pyqtSignal()
    move_up_requested = pyqtSignal(object)
    move_down_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    duplicate_requested = pyqtSignal(object)

    def __init__(self, block_data: dict, calibrators_list: list = None, specs_data: dict = None, parent=None):
        super().__init__(parent)
        self.block_data = block_data or {}
        self.calibrators_list = calibrators_list or []
        self.specs_data = specs_data or {}

        # Extraer funciones y rangos del instrumento si existen especificaciones
        self.inst_functions = []
        self.inst_ranges_by_func = {}
        for f in self.specs_data.get('functions', []):
            fname = f.get('name', '').strip()
            if fname:
                self.inst_functions.append(fname)
                self.inst_ranges_by_func[fname] = f.get('ranges', [])

        self.default_functions = [
            "Tensión DC (Vdc)", "Tensión AC (Vac)", "Corriente DC (Adc)", 
            "Corriente AC (Aac)", "Resistencia (Ω)", "Capacitancia (F)",
            "Inductancia (H)", "Frecuencia (Hz)", "Temperatura (°C)", 
            "Continuidad / Diodo (V)", "Ciclo de Trabajo / Duty Cycle (%)", "Potencia / dBm"
        ]

        self._setup_ui()

    def _setup_ui(self):
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        b_type = self.block_data.get('type', 'text')
        type_labels = {
            'text': ('Texto Enriquecido', '#2E7D32', '#E8F5E9'),
            'ref_measurements': ('Mediciones con Referencias', '#1565C0', '#E3F2FD'),
            'manual_measurements': ('Mediciones sin Referencias', '#6A1B9A', '#F3E5F5'),
            'functional': ('Prueba Funcional / Operativa', '#E65100', '#FFF3E0'),
            'special_functions': ('Funciones Especiales', '#C2185B', '#FCE4EC'),
            'levels': ('Mediciones de Niveles / Ruido', '#00838F', '#E0F7FA'),
            'images': ('Imágenes de Mediciones', '#455A64', '#ECEFF1')
        }
        type_name, type_color, border_tint = type_labels.get(b_type, ('Bloque', '#333333', '#ECEFF1'))

        self.setStyleSheet(f"""
            GuideBlockCardWidget {{
                background-color: #FFFFFF;
                border: 1px solid #C0C8D0;
                border-left: 5px solid {type_color};
                border-radius: 6px;
            }}
            QLabel {{ color: #212121; }}
            QLineEdit {{
                background-color: #FFFFFF; color: #111111; border: 1px solid #B0BEC5; border-radius: 3px;
                padding: 3px 6px; font-size: 11px;
            }}
            QComboBox {{
                background-color: #FFFFFF; color: #111111; border: 1px solid #B0BEC5; border-radius: 3px; padding: 2px 6px; font-size: 11px;
            }}
            QTableWidget {{
                background-color: #FFFFFF; color: #111111; border: 1px solid #CFD8DC; font-size: 11px;
            }}
        """)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)
        main_layout.setSpacing(8)

        # 1. Cabecera
        hdr_layout = QHBoxLayout()
        lbl_badge = QLabel(f" {type_name} ")
        lbl_badge.setStyleSheet(f"background-color: {type_color}; color: #FFFFFF; font-weight: bold; font-size: 10px; border-radius: 3px; padding: 2px 6px;")
        hdr_layout.addWidget(lbl_badge)

        self.txt_title = QLineEdit(self.block_data.get('title', ''))
        self.txt_title.setPlaceholderText("Título o encabezado de la sección...")
        self.txt_title.setStyleSheet("QLineEdit { font-weight: bold; font-size: 12px; color: #111111; background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 4px; padding: 3px 6px; }")
        self.txt_title.textChanged.connect(self._on_title_changed)
        hdr_layout.addWidget(self.txt_title, 1)

        btn_style = "QPushButton { background-color: #ECEFF1; border: 1px solid #B0BEC5; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 3px 8px; color: #263238; } QPushButton:hover { background-color: #CFD8DC; color: #000000; }"
        
        self.btn_up = QPushButton()
        self.btn_up.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'up.svg'), '#263238', 14))
        self.btn_up.setStyleSheet(btn_style)
        self.btn_up.clicked.connect(lambda: self.move_up_requested.emit(self))
        hdr_layout.addWidget(self.btn_up)

        self.btn_down = QPushButton()
        self.btn_down.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'down.svg'), '#263238', 14))
        self.btn_down.setStyleSheet(btn_style)
        self.btn_down.clicked.connect(lambda: self.move_down_requested.emit(self))
        hdr_layout.addWidget(self.btn_down)

        self.btn_dup = QPushButton(" Duplicar")
        self.btn_dup.setStyleSheet(btn_style)
        self.btn_dup.clicked.connect(lambda: self.duplicate_requested.emit(self))
        hdr_layout.addWidget(self.btn_dup)

        self.btn_del = QPushButton()
        self.btn_del.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'trash_empty.svg'), '#C62828', 14))
        self.btn_del.setStyleSheet("QPushButton { background-color: #FFEBEE; border: 1px solid #FFCDD2; border-radius: 3px; padding: 3px 8px; color: #C62828; } QPushButton:hover { background-color: #FFCDD2; }")
        self.btn_del.clicked.connect(lambda: self.delete_requested.emit(self))
        hdr_layout.addWidget(self.btn_del)
        main_layout.addLayout(hdr_layout)

        self.body_container = QWidget()
        body_layout = QVBoxLayout(self.body_container)
        body_layout.setContentsMargins(4, 4, 4, 4)

        if b_type == 'text':
            tb_card = QFrame()
            tb_card.setStyleSheet("background-color: #F8FAFC; border: 1px solid #CFD8DC; border-radius: 4px; padding: 2px;")
            tb_layout = QHBoxLayout(tb_card)
            tb_layout.setContentsMargins(4, 3, 4, 3)
            tb_layout.setSpacing(4)

            t_btn_style = "QPushButton { background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 2px 6px; color: #263238; } QPushButton:hover { background-color: #E2E8F0; color: #000000; }"

            btn_b = QPushButton("B")
            btn_b.setFixedSize(26, 26)
            btn_b.setToolTip("Negrita")
            btn_b.setStyleSheet(t_btn_style)
            btn_b.clicked.connect(self._text_toggle_bold)
            tb_layout.addWidget(btn_b)

            btn_i = QPushButton("I")
            btn_i.setFixedSize(26, 26)
            btn_i.setToolTip("Cursiva")
            btn_i.setStyleSheet("QPushButton { background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 3px; font-style: italic; font-weight: bold; font-size: 11px; color: #263238; } QPushButton:hover { background-color: #E2E8F0; }")
            btn_i.clicked.connect(self._text_toggle_italic)
            tb_layout.addWidget(btn_i)

            btn_u = QPushButton("U")
            btn_u.setFixedSize(26, 26)
            btn_u.setToolTip("Subrayado")
            btn_u.setStyleSheet(t_btn_style)
            btn_u.clicked.connect(self._text_toggle_underline)
            tb_layout.addWidget(btn_u)

            # Font size combo
            cb_size = QComboBox()
            cb_size.addItems(["9", "10", "11", "12", "13", "14", "16", "18", "20", "24"])
            cb_size.setCurrentText("13")
            cb_size.setFixedWidth(52)
            cb_size.setStyleSheet("QComboBox { background-color: #FFFFFF; color: #111111; border: 1px solid #B0BEC5; border-radius: 3px; font-size: 11px; padding: 2px 4px; }")
            cb_size.currentTextChanged.connect(self._text_change_font_size)
            tb_layout.addWidget(cb_size)

            # Color
            btn_col = QPushButton()
            btn_col.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'pencil_dark.svg'), '#263238', 14))
            btn_col.setFixedSize(26, 26)
            btn_col.setToolTip("Color de Texto")
            btn_col.setStyleSheet(t_btn_style)
            btn_col.clicked.connect(self._text_choose_color)
            tb_layout.addWidget(btn_col)

            # Align Left
            btn_al = QPushButton("⇤")
            btn_al.setFixedSize(26, 26)
            btn_al.setToolTip("Alinear a la Izquierda")
            btn_al.setStyleSheet(t_btn_style)
            btn_al.clicked.connect(lambda: self._text_align(Qt.AlignmentFlag.AlignLeft))
            tb_layout.addWidget(btn_al)

            # Align Center
            btn_ac = QPushButton("⇥⇤")
            btn_ac.setFixedSize(26, 26)
            btn_ac.setToolTip("Centrar")
            btn_ac.setStyleSheet(t_btn_style)
            btn_ac.clicked.connect(lambda: self._text_align(Qt.AlignmentFlag.AlignHCenter))
            tb_layout.addWidget(btn_ac)

            # Align Right
            btn_ar = QPushButton("⇥")
            btn_ar.setFixedSize(26, 26)
            btn_ar.setToolTip("Alinear a la Derecha")
            btn_ar.setStyleSheet(t_btn_style)
            btn_ar.clicked.connect(lambda: self._text_align(Qt.AlignmentFlag.AlignRight))
            tb_layout.addWidget(btn_ar)

            # Bullet List
            btn_bl = QPushButton("• Lista")
            btn_bl.setToolTip("Insertar Lista con Viñetas")
            btn_bl.setStyleSheet("QPushButton { background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 3px 6px; color: #263238; } QPushButton:hover { background-color: #E2E8F0; }")
            btn_bl.clicked.connect(self._text_insert_bullet_list)
            tb_layout.addWidget(btn_bl)

            # Numbered List
            btn_nl = QPushButton("1. Lista")
            btn_nl.setToolTip("Insertar Lista Numerada")
            btn_nl.setStyleSheet("QPushButton { background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 3px 6px; color: #263238; } QPushButton:hover { background-color: #E2E8F0; }")
            btn_nl.clicked.connect(self._text_insert_numbered_list)
            tb_layout.addWidget(btn_nl)

            # Table
            btn_tb = QPushButton(" Tabla")
            btn_tb.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'table_dark.svg'), '#263238', 14))
            btn_tb.setToolTip("Insertar Tabla en el texto")
            btn_tb.setStyleSheet("QPushButton { background-color: #FFFFFF; border: 1px solid #B0BEC5; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 3px 6px; color: #263238; } QPushButton:hover { background-color: #E2E8F0; }")
            btn_tb.clicked.connect(self._text_insert_table)
            tb_layout.addWidget(btn_tb)

            # Image
            btn_im = QPushButton(" Imagen")
            btn_im.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'image_file_dark.svg'), '#0D47A1', 14))
            btn_im.setToolTip("Insertar Imagen en el documento")
            btn_im.setStyleSheet("QPushButton { background-color: #E3F2FD; border: 1px solid #90CAF9; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 3px 6px; color: #0D47A1; } QPushButton:hover { background-color: #BBDEFB; }")
            btn_im.clicked.connect(self._text_insert_image)
            tb_layout.addWidget(btn_im)

            # Formula
            btn_fm = QPushButton(" Fórmula")
            btn_fm.setToolTip("Insertar Fórmula Matemática (LaTeX)")
            btn_fm.setStyleSheet("QPushButton { background-color: #EDE7F6; border: 1px solid #D1C4E9; border-radius: 3px; font-weight: bold; font-size: 11px; padding: 3px 6px; color: #4A148C; } QPushButton:hover { background-color: #D1C4E9; }")
            btn_fm.clicked.connect(self._text_insert_formula)
            tb_layout.addWidget(btn_fm)

            tb_layout.addStretch()
            body_layout.addWidget(tb_card)

            self.txt_content = MathRichTextEdit()
            self.txt_content.setMinimumHeight(130)
            self.txt_content.setStyleSheet("""
                QTextEdit {
                    background-color: #FFFFFF;
                    color: #111111;
                    border: 1px solid #B0BEC5;
                    border-radius: 4px;
                    font-size: 13px;
                    padding: 8px;
                    selection-background-color: #BBDEFB;
                    selection-color: #0D47A1;
                }
            """)
            self.txt_content.setPlaceholderText("Escribe las instrucciones o información de la sección en texto enriquecido...")
            self.txt_content.setHtml(self.block_data.get('content', ''))
            self.txt_content.textChanged.connect(self._on_text_content_changed)
            body_layout.addWidget(self.txt_content)

        elif b_type == 'ref_measurements':
            ref_bar = QHBoxLayout()
            self.cb_calib = QComboBox()
            self.cb_calib.addItem("— Seleccionar Calibrador —", None)
            sel_cal_id = self.block_data.get('calibrator_id', '')
            for cal in self.calibrators_list:
                self.cb_calib.addItem(f"{cal.get('name')} ({cal.get('type')})", cal)
                if cal.get('id') == sel_cal_id: self.cb_calib.setCurrentIndex(self.cb_calib.count() - 1)
            self.cb_calib.currentIndexChanged.connect(self._on_calib_changed)
            ref_bar.addWidget(QLabel("<b>Patrón:</b>"), 0)
            ref_bar.addWidget(self.cb_calib, 1)

            btn_pts = QPushButton(" Importar Puntos")
            btn_pts.setStyleSheet("QPushButton { background-color: #E3F2FD; color: #0D47A1; border: 1px solid #90CAF9; border-radius: 4px; font-weight: bold; font-size: 11px; padding: 4px 10px; } QPushButton:hover { background-color: #BBDEFB; }")
            btn_pts.clicked.connect(self._import_calibrator_points)
            ref_bar.addWidget(btn_pts)
            btn_add = QPushButton(" Agregar Punto")
            btn_add.setStyleSheet("QPushButton { background-color: #E8F5E9; color: #1B5E20; border: 1px solid #A5D6A7; border-radius: 4px; font-weight: bold; font-size: 11px; padding: 4px 10px; } QPushButton:hover { background-color: #C8E6C9; }")
            btn_add.clicked.connect(self._add_ref_point_row)
            ref_bar.addWidget(btn_add)
            body_layout.addLayout(ref_bar)

            self.tbl_pts = QTableWidget()
            self.tbl_pts.setColumnCount(8)
            self.tbl_pts.setHorizontalHeaderLabels([
                "Función del Instrumento", "Escala / Rango Instrumento", "Valor Patrón", "Unidad", "% Tol.", "Dígitos", "Res. (Dec)", "Acción"
            ])
            self.tbl_pts.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(0, 180)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(1, 160)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(2, 95)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(3, 70)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(4, 75)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(5, 65)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(6, 70)
            self.tbl_pts.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
            self.tbl_pts.horizontalHeader().resizeSection(7, 70)

            self.tbl_pts.horizontalHeader().setFixedHeight(28)
            self.tbl_pts.verticalHeader().setVisible(False)
            self.tbl_pts.verticalHeader().setDefaultSectionSize(34)
            self.tbl_pts.setStyleSheet("""
                QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                QHeaderView { background-color: #37474F; border: none; }
                QHeaderView::section { background-color: #37474F; color: #FFFFFF; font-weight: bold; padding: 4px; border: 1px solid #455A64; }
            """)
            body_layout.addWidget(self.tbl_pts)
            self._load_ref_points()

        elif b_type == 'manual_measurements':
            bar = QHBoxLayout()
            bar.addWidget(QLabel("<b>Puntos de Medición:</b>"), 1)
            btn_add = QPushButton(" Agregar Punto")
            btn_add.setStyleSheet("QPushButton { background-color: #EDE7F6; color: #4A148C; border: 1px solid #D1C4E9; border-radius: 4px; font-weight: bold; font-size: 11px; padding: 4px 10px; } QPushButton:hover { background-color: #D1C4E9; }")
            btn_add.clicked.connect(self._add_manual_point_row)
            bar.addWidget(btn_add)
            body_layout.addLayout(bar)
            self.tbl_manual = QTableWidget()
            self.tbl_manual.setColumnCount(6)
            self.tbl_manual.setHorizontalHeaderLabels(["Descripción / Parámetro", "Valor Nominal", "Unidad", "Límite Mín", "Límite Máx", "Acción"])
            self.tbl_manual.horizontalHeader().setFixedHeight(28)
            self.tbl_manual.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.tbl_manual.verticalHeader().setVisible(False)
            self.tbl_manual.verticalHeader().setDefaultSectionSize(34)
            self.tbl_manual.setStyleSheet("""
                QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                QHeaderView { background-color: #4A148C; border: none; }
                QHeaderView::section { background-color: #4A148C; color: #FFFFFF; font-weight: bold; padding: 4px; border: 1px solid #3D405B; }
            """)
            body_layout.addWidget(self.tbl_manual)
            self._load_manual_points()

        elif b_type in ('functional', 'special_functions'):
            bar = QHBoxLayout()
            bar.addWidget(QLabel("<b>Ítems y Criterios:</b>"), 1)
            btn_add = QPushButton(" Agregar Ítem")
            btn_add.setStyleSheet("QPushButton { background-color: #FBE9E7; color: #BF360C; border: 1px solid #FFCCBC; border-radius: 4px; font-weight: bold; font-size: 11px; padding: 4px 10px; } QPushButton:hover { background-color: #FFCCBC; }")
            btn_add.clicked.connect(self._add_functional_row)
            bar.addWidget(btn_add)
            body_layout.addLayout(bar)
            self.tbl_func = QTableWidget()
            self.tbl_func.setColumnCount(3)
            self.tbl_func.setHorizontalHeaderLabels(["Ítem / Función a Probar", "Criterio de Aceptación / Descripción", "Acción"])
            self.tbl_func.horizontalHeader().setFixedHeight(28)
            self.tbl_func.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
            self.tbl_func.horizontalHeader().resizeSection(0, 220)
            self.tbl_func.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            self.tbl_func.verticalHeader().setVisible(False)
            self.tbl_func.verticalHeader().setDefaultSectionSize(34)
            self.tbl_func.setStyleSheet("""
                QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                QHeaderView { background-color: #BF360C; border: none; }
                QHeaderView::section { background-color: #BF360C; color: #FFFFFF; font-weight: bold; padding: 4px; border: 1px solid #3D405B; }
            """)
            body_layout.addWidget(self.tbl_func)
            self._load_functional_items()

        elif b_type == 'levels':
            bar = QHBoxLayout()
            bar.addWidget(QLabel("<b>Mediciones de Niveles:</b>"), 1)
            btn_add = QPushButton(" Agregar Nivel")
            btn_add.setStyleSheet("QPushButton { background-color: #E0F2F1; color: #006064; border: 1px solid #80CBC4; border-radius: 4px; font-weight: bold; font-size: 11px; padding: 4px 10px; } QPushButton:hover { background-color: #B2DFDB; }")
            btn_add.clicked.connect(self._add_level_row)
            bar.addWidget(btn_add)
            body_layout.addLayout(bar)
            self.tbl_levels = QTableWidget()
            self.tbl_levels.setColumnCount(5)
            self.tbl_levels.setHorizontalHeaderLabels(["Parámetro / Prueba", "Valor Nominal", "Unidad", "Límite Máximo Aceptable", "Acción"])
            self.tbl_levels.horizontalHeader().setFixedHeight(28)
            self.tbl_levels.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            self.tbl_levels.verticalHeader().setVisible(False)
            self.tbl_levels.verticalHeader().setDefaultSectionSize(34)
            self.tbl_levels.setStyleSheet("""
                QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                QHeaderView { background-color: #006064; border: none; }
                QHeaderView::section { background-color: #006064; color: #FFFFFF; font-weight: bold; padding: 4px; border: 1px solid #3D405B; }
            """)
            body_layout.addWidget(self.tbl_levels)
            self._load_level_items()

        elif b_type == 'images':
            self.txt_inst = QLineEdit(self.block_data.get('instructions', ''))
            self.txt_inst.setPlaceholderText("Instrucciones para el técnico...")
            self.txt_inst.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; padding: 4px 8px; border: 1px solid #B0BEC5; border-radius: 4px; font-size: 11px; }")
            self.txt_inst.textChanged.connect(lambda t: self.block_data.update({'instructions': t}))
            body_layout.addWidget(self.txt_inst)

        main_layout.addWidget(self.body_container)

    def _on_title_changed(self, text):
        self.block_data['title'] = text
        self.block_changed.emit()

    def _on_text_content_changed(self):
        if hasattr(self, 'txt_content'):
            self.block_data['content'] = self.txt_content.toHtml()
            self.block_changed.emit()

    def _text_toggle_bold(self):
        if not hasattr(self, 'txt_content'): return
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Bold if self.txt_content.fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        self.txt_content.mergeCurrentCharFormat(fmt)

    def _text_toggle_italic(self):
        if not hasattr(self, 'txt_content'): return
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.txt_content.fontItalic())
        self.txt_content.mergeCurrentCharFormat(fmt)

    def _text_toggle_underline(self):
        if not hasattr(self, 'txt_content'): return
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.txt_content.fontUnderline())
        self.txt_content.mergeCurrentCharFormat(fmt)

    def _text_change_font_size(self, size_str: str):
        if not hasattr(self, 'txt_content'): return
        try:
            size = float(size_str)
            fmt = QTextCharFormat()
            fmt.setFontPointSize(size)
            self.txt_content.mergeCurrentCharFormat(fmt)
            self.txt_content.setFontPointSize(size)
        except (ValueError, TypeError):
            pass

    def _text_choose_color(self):
        if not hasattr(self, 'txt_content'): return
        col = QColorDialog.getColor(self.txt_content.textColor(), self, "Seleccionar Color de Texto")
        if col.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(col)
            self.txt_content.mergeCurrentCharFormat(fmt)

    def _text_align(self, alignment):
        if hasattr(self, 'txt_content'):
            self.txt_content.setAlignment(alignment)

    def _text_insert_bullet_list(self):
        if not hasattr(self, 'txt_content'): return
        cursor = self.txt_content.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDisc)

    def _text_insert_numbered_list(self):
        if not hasattr(self, 'txt_content'): return
        cursor = self.txt_content.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDecimal)

    def _text_insert_table(self):
        if not hasattr(self, 'txt_content'): return
        rows, ok1 = QInputDialog.getInt(self, "Insertar Tabla", "Número de filas:", 3, 1, 30)
        if not ok1: return
        cols, ok2 = QInputDialog.getInt(self, "Insertar Tabla", "Número de columnas:", 3, 1, 10)
        if not ok2: return
        html_tbl = "<table border='1' style='border-collapse:collapse; width:100%; border:1px solid #B0BEC5; margin:6px 0;'>"
        for r in range(rows):
            html_tbl += "<tr>"
            for c in range(cols):
                if r == 0:
                    html_tbl += f"<th style='background-color:#ECEFF1; color:#263238; padding:4px 8px; font-weight:bold;'>Cabecera {c+1}</th>"
                else:
                    html_tbl += f"<td style='padding:4px 8px; color:#111111;'>Dato {r},{c+1}</td>"
            html_tbl += "</tr>"
        html_tbl += "</table><br>"
        cursor = self.txt_content.textCursor()
        cursor.insertHtml(html_tbl)
        self._on_text_content_changed()

    def _text_insert_image(self):
        if not hasattr(self, 'txt_content'): return
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", IMAGE_FILE_FILTER)
        if filepath:
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
                ext = os.path.splitext(filepath)[1].lower().replace('.', '')
                if ext == 'jpg': ext = 'jpeg'
                elif ext == 'svg': ext = 'svg+xml'
                b64 = base64.b64encode(data).decode('utf-8')
                data_uri = f"data:image/{ext};base64,{b64}"
                cursor = self.txt_content.textCursor()
                cursor.insertHtml(f'<img src="{data_uri}" style="max-width:100%; border-radius:4px; margin:6px 0;" /><br>')
                self._on_text_content_changed()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo insertar la imagen: {e}")

    def _text_insert_formula(self):
        if not hasattr(self, 'txt_content'): return
        dlg = FormulaDialog(self)
        if dlg.exec():
            dlg.insert_into_editor(self.txt_content)
            self._on_text_content_changed()

    def _on_calib_changed(self):
        cal = self.cb_calib.currentData()
        if cal:
            self.block_data['calibrator_id'] = cal.get('id', '')
            self.block_data['calibrator_name'] = f"{cal.get('name', '')} ({cal.get('type', '')})"
        else:
            self.block_data['calibrator_id'] = ''
            self.block_data['calibrator_name'] = ''
        self.block_changed.emit()

    # --- Métodos para ref_measurements ---
    def _load_ref_points(self):
        pts = self.block_data.setdefault('points', [])
        self.tbl_pts.setRowCount(0)
        for p in pts:
            self._insert_ref_point_row_ui(p)
        self._adjust_pts_height()

    def _adjust_pts_height(self):
        if not hasattr(self, 'tbl_pts'): return
        row_h = 32
        hdr_h = 28
        n_rows = max(1, self.tbl_pts.rowCount())
        total_h = hdr_h + (n_rows * row_h) + 12
        self.tbl_pts.setFixedHeight(min(total_h, 320))

    def _get_ranges_for_function(self, fn_name: str) -> list:
        """Devuelve las opciones de rangos conocidas para la función dada."""
        for fname, r_list in self.inst_ranges_by_func.items():
            if fname.lower() == fn_name.lower() or fname.split()[0].lower() in fn_name.lower():
                return [r.get('range', '') for r in r_list if r.get('range')]
        fn_l = fn_name.lower()
        if 'vdc' in fn_l or 'tensión dc' in fn_l or 'voltaje dc' in fn_l:
            return ["200 mV", "2 V", "20 V", "200 V", "1000 V"]
        elif 'vac' in fn_l or 'tensión ac' in fn_l or 'voltaje ac' in fn_l:
            return ["200 mV", "2 V", "20 V", "200 V", "750 V"]
        elif 'adc' in fn_l or 'corriente dc' in fn_l:
            return ["200 µA", "2 mA", "20 mA", "200 mA", "2 A", "10 A", "20 A"]
        elif 'aac' in fn_l or 'corriente ac' in fn_l:
            return ["200 µA", "2 mA", "20 mA", "200 mA", "2 A", "10 A", "20 A"]
        elif 'resistencia' in fn_l or 'Ω' in fn_name or 'ohm' in fn_l:
            return ["200 Ω", "2 kΩ", "20 kΩ", "200 kΩ", "2 MΩ", "20 MΩ"]
        elif 'capacitancia' in fn_l or 'f' in fn_l:
            return ["20 nF", "200 nF", "2 µF", "20 µF", "200 µF", "2 mF"]
        elif 'frecuencia' in fn_l or 'hz' in fn_l:
            return ["200 Hz", "2 kHz", "20 kHz", "200 kHz", "2 MHz", "20 MHz"]
        elif 'temperatura' in fn_l:
            return ["-40°C ~ 400°C", "-40°C ~ 1000°C"]
        return ["Auto", "Escala 1", "Escala 2"]

    def _insert_ref_point_row_ui(self, p: dict):
        row = self.tbl_pts.rowCount()
        self.tbl_pts.insertRow(row)
        self.tbl_pts.setRowHeight(row, 34)

        cb_fn = QComboBox()
        cb_fn.setEditable(True)
        all_funcs = list(self.inst_functions)
        for df in self.default_functions:
            if df not in all_funcs: all_funcs.append(df)
        cb_fn.addItems(all_funcs)
        
        cur_fn = str(p.get('function', 'Tensión DC (Vdc)')).strip()
        idx_f = cb_fn.findText(cur_fn)
        if idx_f >= 0: cb_fn.setCurrentIndex(idx_f)
        else: cb_fn.setEditText(cur_fn)

        cb_rng = QComboBox()
        cb_rng.setEditable(True)

        def update_ranges_dropdown(selected_fn_text):
            cur_r_text = cb_rng.currentText()
            cb_rng.blockSignals(True)
            cb_rng.clear()
            ranges = self._get_ranges_for_function(selected_fn_text)
            cb_rng.addItems(ranges)
            if cur_r_text:
                idx_r = cb_rng.findText(cur_r_text)
                if idx_r >= 0: cb_rng.setCurrentIndex(idx_r)
                else: cb_rng.setEditText(cur_r_text)
            cb_rng.blockSignals(False)

        update_ranges_dropdown(cur_fn)
        cur_rng = str(p.get('range', '20 V')).strip()
        idx_r = cb_rng.findText(cur_rng)
        if idx_r >= 0: cb_rng.setCurrentIndex(idx_r)
        else: cb_rng.setEditText(cur_rng)

        txt_nom = QLineEdit(str(p.get('nominal', '10.000')))
        cb_u = QComboBox()
        cb_u.setEditable(True)
        cb_u.addItems(CALIBRATION_UNITS)
        u_val = str(p.get('unit', 'V'))
        idx_u = cb_u.findText(u_val)
        if idx_u >= 0: cb_u.setCurrentIndex(idx_u)
        else: cb_u.setEditText(u_val)

        txt_pct = QLineEdit(str(p.get('percent_tol', '0.05')))
        txt_dig = QLineEdit(str(p.get('digits_tol', '2')))
        txt_res = QLineEdit(str(p.get('resolution', '4')))

        for w in (txt_nom, txt_pct, txt_dig, txt_res):
            w.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-size: 11px; padding: 2px 4px; border: 1px solid #B0BEC5; border-radius: 2px; }")
        for w in (cb_fn, cb_rng, cb_u):
            w.setStyleSheet("QComboBox { background-color: #FFFFFF; color: #111111; font-size: 11px; padding: 2px; border: 1px solid #B0BEC5; border-radius: 2px; } QComboBox QAbstractItemView { background-color: #FFFFFF; color: #111111; }")

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("background-color: #FFCDD2; color: #B71C1C; font-size: 10px; border-radius: 2px; font-weight: bold;")
        btn_del.clicked.connect(lambda checked, r=row: self._delete_ref_row(r))

        self.tbl_pts.setCellWidget(row, 0, cb_fn)
        self.tbl_pts.setCellWidget(row, 1, cb_rng)
        self.tbl_pts.setCellWidget(row, 2, txt_nom)
        self.tbl_pts.setCellWidget(row, 3, cb_u)
        self.tbl_pts.setCellWidget(row, 4, txt_pct)
        self.tbl_pts.setCellWidget(row, 5, txt_dig)
        self.tbl_pts.setCellWidget(row, 6, txt_res)
        self.tbl_pts.setCellWidget(row, 7, btn_del)

        def on_range_changed(rng_text):
            fn_t = cb_fn.currentText().strip()
            ranges_data = []
            for fname, r_list in self.inst_ranges_by_func.items():
                if fname.lower() == fn_t.lower() or fname.split()[0].lower() in fn_t.lower():
                    ranges_data = r_list
                    break
            for r_item in ranges_data:
                if r_item.get('range', '').strip().lower() == rng_text.strip().lower():
                    acc_pct = r_item.get('accuracy_pct', '')
                    m_pct = re.search(r'([0-9]+(?:\.[0-9]+)?)', acc_pct)
                    if m_pct: txt_pct.setText(m_pct.group(1))
                    acc_dig = r_item.get('accuracy_digits', '')
                    m_dig = re.search(r'([0-9]+)', acc_dig)
                    if m_dig: txt_dig.setText(m_dig.group(1))
                    res_str = r_item.get('resolution', '')
                    if '.' in res_str:
                        dec_part = res_str.split('.')[1]
                        m_d = re.match(r'([0-9]+)', dec_part)
                        if m_d: txt_res.setText(str(len(m_d.group(1))))
                    break
            self._sync_ref_points_data()

        cb_fn.currentTextChanged.connect(update_ranges_dropdown)
        cb_rng.currentTextChanged.connect(on_range_changed)
        for w in (txt_nom, txt_pct, txt_dig, txt_res): w.textChanged.connect(self._sync_ref_points_data)
        cb_u.currentTextChanged.connect(self._sync_ref_points_data)
        cb_fn.currentTextChanged.connect(self._sync_ref_points_data)

    def _add_ref_point_row(self):
        new_pt = {'id': f"pt_{os.urandom(3).hex()}", 'function': 'Tensión DC (Vdc)', 'nominal': 10.0, 'unit': 'V', 'range': '20 V', 'percent_tol': 0.05, 'digits_tol': 2, 'resolution': 4}
        self.block_data.setdefault('points', []).append(new_pt)
        self._insert_ref_point_row_ui(new_pt)
        self._adjust_pts_height()
        self.block_changed.emit()

    def _delete_ref_row(self, row: int):
        self.tbl_pts.removeRow(row)
        self._sync_ref_points_data()
        self._adjust_pts_height()

    def _sync_ref_points_data(self):
        pts = []
        for r in range(self.tbl_pts.rowCount()):
            w_fn = self.tbl_pts.cellWidget(r, 0)
            w_rng = self.tbl_pts.cellWidget(r, 1)
            w_nom = self.tbl_pts.cellWidget(r, 2)
            w_u = self.tbl_pts.cellWidget(r, 3)
            w_pct = self.tbl_pts.cellWidget(r, 4)
            w_dig = self.tbl_pts.cellWidget(r, 5)
            w_res = self.tbl_pts.cellWidget(r, 6)
            try: nom = float(w_nom.text()) if w_nom else 0.0
            except: nom = 0.0
            try: pct = float(w_pct.text()) if w_pct else 0.05
            except: pct = 0.05
            try: dig = int(w_dig.text()) if w_dig else 2
            except: dig = 2
            try: res = int(w_res.text()) if w_res else 4
            except: res = 4
            fn_val = w_fn.currentText().strip() if hasattr(w_fn, 'currentText') else (w_fn.text().strip() if w_fn else 'Medición')
            rng_val = w_rng.currentText().strip() if hasattr(w_rng, 'currentText') else (w_rng.text().strip() if w_rng else '')
            unit_val = w_u.currentText().strip() if hasattr(w_u, 'currentText') else 'V'
            pts.append({'id': f"pt_{r+1}_{os.urandom(2).hex()}", 'function': fn_val or 'Medición', 'nominal': nom, 'unit': unit_val, 'range': rng_val or 'Auto', 'percent_tol': pct, 'digits_tol': dig, 'resolution': res})
        self.block_data['points'] = pts
        self.block_changed.emit()

    def _import_calibrator_points(self):
        cal = self.cb_calib.currentData()
        if not cal:
            QMessageBox.information(self, "Calibrador", "Selecciona un calibrador para importar sus puntos patrón.")
            return

        pts = list(cal.get('reference_points', []))
        if not pts and cal.get('measurements'):
            seen = set()
            for m in cal.get('measurements', []):
                nom = m.get('nominal', '').strip()
                unit = m.get('unit', 'V').strip() or 'V'
                if nom and (nom, unit) not in seen:
                    seen.add((nom, unit))
                    try: nom_val = float(nom)
                    except: nom_val = 0.0
                    pts.append({'magnitude': m.get('notes') or f"Punto Patrón ({nom} {unit})", 'nominal': nom_val, 'unit': unit, 'tolerance': '0.05%'})

        if not pts:
            QMessageBox.warning(self, "Sin Puntos", f"El calibrador '{cal.get('name')}' no contiene puntos registrados.")
            return

        imported_count = 0
        for p in pts:
            nom_raw = p.get('nominal', 0.0)
            try: nom_val = float(nom_raw)
            except: nom_val = 0.0
            unit = str(p.get('unit', 'V')).strip() or 'V'
            cal_type = (cal.get('type') or '').lower()
            u_low = unit.lower()
            if 'v' in u_low or 'tensión' in cal_type or 'volt' in cal_type:
                fn_guess = "Tensión DC (Vdc)" if ('dc' in cal_type or 'tensión' in cal_type or 'v' in u_low) else "Tensión AC (Vac)"
            elif 'a' in u_low or 'corriente' in cal_type or 'amp' in cal_type:
                fn_guess = "Corriente DC (Adc)"
            elif 'Ω' in unit or 'ohm' in u_low or 'resistencia' in cal_type:
                fn_guess = "Resistencia (Ω)"
            elif 'f' in u_low or 'capaci' in cal_type:
                fn_guess = "Capacitancia (F)"
            elif 'hz' in u_low or 'frecuen' in cal_type:
                fn_guess = "Frecuencia (Hz)"
            elif '°c' in u_low or 'temperatura' in cal_type:
                fn_guess = "Temperatura (°C)"
            else:
                fn_guess = p.get('function') or "Tensión DC (Vdc)"

            matched_fn = fn_guess
            for spec_fn in self.inst_functions:
                if (fn_guess.split()[0].lower() in spec_fn.lower()) or (unit in spec_fn):
                    matched_fn = spec_fn
                    break

            matched_range = ""
            pct_tol = 0.05
            dig_tol = 1
            res_dec = 4
            ranges_for_fn = self.inst_ranges_by_func.get(matched_fn, [])
            if ranges_for_fn:
                best_range_obj = None
                for r_obj in ranges_for_fn:
                    r_str = r_obj.get('range', '')
                    m_r = re.search(r'([0-9]+(?:\.[0-9]+)?)', r_str)
                    if m_r:
                        r_num = float(m_r.group(1))
                        if r_num >= abs(nom_val):
                            best_range_obj = r_obj
                            break
                if not best_range_obj and ranges_for_fn: best_range_obj = ranges_for_fn[0]
                if best_range_obj:
                    matched_range = best_range_obj.get('range', '')
                    acc_pct = best_range_obj.get('accuracy_pct', '')
                    m_pct = re.search(r'([0-9]+(?:\.[0-9]+)?)', acc_pct)
                    if m_pct: pct_tol = float(m_pct.group(1))
                    acc_dig = best_range_obj.get('accuracy_digits', '')
                    m_dig = re.search(r'([0-9]+)', acc_dig)
                    if m_dig: dig_tol = int(m_dig.group(1))
                    res_str = best_range_obj.get('resolution', '')
                    if '.' in res_str:
                        dec_part = res_str.split('.')[1]
                        m_d = re.match(r'([0-9]+)', dec_part)
                        if m_d: res_dec = len(m_d.group(1))

            if not matched_range: matched_range = p.get('range') or f"{nom_val * 1.5:.1f} {unit}".replace('.0 ', ' ')

            new_p = {'id': f"pt_{os.urandom(3).hex()}", 'function': matched_fn, 'nominal': nom_val, 'unit': unit, 'range': matched_range, 'percent_tol': pct_tol, 'digits_tol': dig_tol, 'resolution': res_dec}
            self.block_data.setdefault('points', []).append(new_p)
            self._insert_ref_point_row_ui(new_p)
            imported_count += 1
        self._sync_ref_points_data()
        self._adjust_pts_height()
        QMessageBox.information(self, "Puntos Importados", f"Se importaron {imported_count} puntos patrón.")

    # --- Métodos para manual_measurements ---
    def _load_manual_points(self):
        pts = self.block_data.setdefault('points', [])
        self.tbl_manual.setRowCount(0)
        for p in pts:
            row = self.tbl_manual.rowCount()
            self.tbl_manual.insertRow(row)
            self.tbl_manual.setRowHeight(row, 34)
            txt_desc = QLineEdit(str(p.get('description', 'Medición')))
            txt_nom = QLineEdit(str(p.get('nominal', '5.00')))
            cb_u = QComboBox()
            cb_u.setEditable(True)
            cb_u.addItems(CALIBRATION_UNITS)
            cb_u.setEditText(str(p.get('unit', 'V')))
            txt_min = QLineEdit(str(p.get('min_val', '4.95')))
            txt_max = QLineEdit(str(p.get('max_val', '5.05')))
            for w in (txt_desc, txt_nom, txt_min, txt_max):
                w.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-size: 11px; padding: 2px 4px; border: 1px solid #B0BEC5; border-radius: 2px; }")
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #FFCDD2; color: #B71C1C; font-size: 10px;")
            btn_del.clicked.connect(lambda checked, r=row: self._delete_manual_row(r))
            self.tbl_manual.setCellWidget(row, 0, txt_desc)
            self.tbl_manual.setCellWidget(row, 1, txt_nom)
            self.tbl_manual.setCellWidget(row, 2, cb_u)
            self.tbl_manual.setCellWidget(row, 3, txt_min)
            self.tbl_manual.setCellWidget(row, 4, txt_max)
            self.tbl_manual.setCellWidget(row, 5, btn_del)
            def sync(): self._sync_manual_points_data()
            for w in (txt_desc, txt_nom, txt_min, txt_max): w.textChanged.connect(sync)
            cb_u.currentTextChanged.connect(sync)

    def _add_manual_point_row(self):
        self.block_data.setdefault('points', []).append({'description': 'Medición', 'nominal': 5.0, 'unit': 'V', 'min_val': 4.95, 'max_val': 5.05})
        self._load_manual_points()
        self.block_changed.emit()

    def _delete_manual_row(self, row: int):
        self.tbl_manual.removeRow(row)
        self._sync_manual_points_data()

    def _sync_manual_points_data(self):
        pts = []
        for r in range(self.tbl_manual.rowCount()):
            w_d = self.tbl_manual.cellWidget(r, 0)
            w_nom = self.tbl_manual.cellWidget(r, 1)
            w_u = self.tbl_manual.cellWidget(r, 2)
            w_min = self.tbl_manual.cellWidget(r, 3)
            w_max = self.tbl_manual.cellWidget(r, 4)
            pts.append({
                'id': f"m_{r+1}_{os.urandom(2).hex()}",
                'description': w_d.text().strip() if w_d else 'Medición',
                'nominal': float(w_nom.text()) if (w_nom and w_nom.text()) else 0.0,
                'unit': w_u.currentText().strip() if hasattr(w_u, 'currentText') else 'V',
                'min_val': float(w_min.text()) if (w_min and w_min.text()) else 0.0,
                'max_val': float(w_max.text()) if (w_max and w_max.text()) else 0.0
            })
        self.block_data['points'] = pts
        self.block_changed.emit()

    # --- Métodos para functional y special_functions ---
    def _load_functional_items(self):
        items = self.block_data.setdefault('items', [])
        self.tbl_func.setRowCount(0)
        for it in items:
            row = self.tbl_func.rowCount()
            self.tbl_func.insertRow(row)
            self.tbl_func.setRowHeight(row, 34)
            txt_n = QLineEdit(str(it.get('name', '')))
            txt_n.setPlaceholderText("Nombre de la prueba...")
            txt_d = QLineEdit(str(it.get('description', '')))
            txt_d.setPlaceholderText("Criterio de aceptación...")
            for w in (txt_n, txt_d):
                w.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-size: 11px; padding: 2px 4px; border: 1px solid #B0BEC5; border-radius: 2px; }")
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #FFCDD2; color: #B71C1C; font-size: 10px;")
            btn_del.clicked.connect(lambda checked, r=row: self._delete_functional_row(r))
            self.tbl_func.setCellWidget(row, 0, txt_n)
            self.tbl_func.setCellWidget(row, 1, txt_d)
            self.tbl_func.setCellWidget(row, 2, btn_del)
            txt_n.textChanged.connect(self._sync_functional_items)
            txt_d.textChanged.connect(self._sync_functional_items)

    def _add_functional_row(self):
        self.block_data.setdefault('items', []).append({'name': 'Prueba Operativa', 'description': 'Operación correcta sin ruidos ni anomalías'})
        self._load_functional_items()
        self.block_changed.emit()

    def _delete_functional_row(self, row: int):
        self.tbl_func.removeRow(row)
        self._sync_functional_items()

    def _sync_functional_items(self):
        items = []
        for r in range(self.tbl_func.rowCount()):
            w_n = self.tbl_func.cellWidget(r, 0)
            w_d = self.tbl_func.cellWidget(r, 1)
            items.append({'id': f"f_{r+1}_{os.urandom(2).hex()}", 'name': w_n.text().strip() if w_n else '', 'description': w_d.text().strip() if w_d else ''})
        self.block_data['items'] = items
        self.block_changed.emit()

    # --- Métodos para levels ---
    def _load_level_items(self):
        items = self.block_data.setdefault('items', [])
        self.tbl_levels.setRowCount(0)
        for it in items:
            row = self.tbl_levels.rowCount()
            self.tbl_levels.insertRow(row)
            self.tbl_levels.setRowHeight(row, 34)
            txt_n = QLineEdit(str(it.get('name', 'Ripple / Ruido')))
            txt_nom = QLineEdit(str(it.get('nominal', '0.0')))
            cb_u = QComboBox()
            cb_u.setEditable(True)
            cb_u.addItems(CALIBRATION_UNITS)
            cb_u.setEditText(str(it.get('unit', 'mV')))
            txt_max = QLineEdit(str(it.get('max_val', '10.0')))
            for w in (txt_n, txt_nom, txt_max):
                w.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-size: 11px; padding: 2px 4px; border: 1px solid #B0BEC5; border-radius: 2px; }")
            btn_del = QPushButton("Eliminar")
            btn_del.setStyleSheet("background-color: #FFCDD2; color: #B71C1C; font-size: 10px;")
            btn_del.clicked.connect(lambda checked, r=row: self._delete_level_row(r))
            self.tbl_levels.setCellWidget(row, 0, txt_n)
            self.tbl_levels.setCellWidget(row, 1, txt_nom)
            self.tbl_levels.setCellWidget(row, 2, cb_u)
            self.tbl_levels.setCellWidget(row, 3, txt_max)
            self.tbl_levels.setCellWidget(row, 4, btn_del)
            for w in (txt_n, txt_nom, txt_max): w.textChanged.connect(self._sync_level_items)
            cb_u.currentTextChanged.connect(self._sync_level_items)

    def _add_level_row(self):
        self.block_data.setdefault('items', []).append({'name': 'Ruido de Fondo (RMS)', 'nominal': 0.0, 'unit': 'mV', 'max_val': 5.0})
        self._load_level_items()
        self.block_changed.emit()

    def _delete_level_row(self, row: int):
        self.tbl_levels.removeRow(row)
        self._sync_level_items()

    def _sync_level_items(self):
        items = []
        for r in range(self.tbl_levels.rowCount()):
            w_n = self.tbl_levels.cellWidget(r, 0)
            w_nom = self.tbl_levels.cellWidget(r, 1)
            w_u = self.tbl_levels.cellWidget(r, 2)
            w_max = self.tbl_levels.cellWidget(r, 3)
            items.append({'id': f"lvl_{r+1}_{os.urandom(2).hex()}", 'name': w_n.text().strip() if w_n else '', 'nominal': float(w_nom.text()) if (w_nom and w_nom.text()) else 0.0, 'unit': w_u.currentText().strip() if hasattr(w_u, 'currentText') else 'mV', 'max_val': float(w_max.text()) if (w_max and w_max.text()) else 0.0})
        self.block_data['items'] = items
        self.block_changed.emit()


# --- 2.5 Editor de Estructura de Guía de Prueba (Modo Página Única) ---
class GuideStructureEditorWidget(QWidget):
    """Editor visual de bloques para definir la estructura de la guía de prueba del instrumento."""

    back_requested = pyqtSignal()

    def __init__(self, item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item = item or {}
        self.agenda_path = agenda_path
        self.structure = {'blocks': []}
        self.calibrators_list = []
        self.specs_data = {}
        self._load_data()
        self._setup_ui()

    def _load_data(self):
        if self.agenda_path and self.item:
            inst_dir = get_instrument_dir(self.agenda_path, self.item)
            struct_file = os.path.join(inst_dir, 'guia_estructura.json')
            if os.path.exists(struct_file):
                try:
                    with open(struct_file, 'r', encoding='utf-8') as f:
                        self.structure = json.load(f)
                except Exception:
                    self.structure = {'blocks': []}
            specs_file = os.path.join(inst_dir, 'specifications.json')
            if os.path.exists(specs_file):
                try:
                    with open(specs_file, 'r', encoding='utf-8') as f:
                        self.specs_data = json.load(f)
                except Exception:
                    self.specs_data = {}
            calib_path = os.path.join(self.agenda_path, 'laboratorio', 'calibradores.json')
            if os.path.exists(calib_path):
                cal_data = DataStore.load(calib_path)
                if cal_data: self.calibrators_list = cal_data.get('calibrators', [])

    def _setup_ui(self):
        self.setStyleSheet("""
            GuideStructureEditorWidget { background: transparent; }
            QLabel { color: #111111; }
            QTableWidget {
                background-color: #FFFFFF;
                color: #111111;
                gridline-color: #ECEFF1;
                border: 1px solid #CFD8DC;
                font-size: 11px;
                selection-background-color: #E3F2FD;
                selection-color: #0D47A1;
            }
            QTableWidget QLineEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QTableWidget QComboBox {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QHeaderView {
                background-color: #2B2D42;
                border: none;
            }
            QHeaderView::section {
                background-color: #2B2D42;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 6px;
                border: 1px solid #3D405B;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # 1. Barra Superior con Volver, Título y Guardar
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #1E1E2E; border: 1px solid #313244; border-radius: 6px; padding: 6px;")
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(10, 6, 10, 6)

        self.btn_back = QPushButton(" Volver")
        self.btn_back.setIcon(QIcon(os.path.join(icons_dir, 'left.svg')))
        self.btn_back.setStyleSheet("QPushButton { background-color: #313244; color: #CDD6F4; font-weight: bold; border: 1px solid #45475A; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #45475A; color: #FFFFFF; }")
        self.btn_back.clicked.connect(self.back_requested.emit)
        tb_layout.addWidget(self.btn_back)

        lbl_title = QLabel(f"Estructura de Guía de Prueba: <b>{self.item.get('name', 'Instrumento')}</b>")
        lbl_title.setStyleSheet("font-size: 13px; color: #FFFFFF; margin-left: 10px;")
        tb_layout.addWidget(lbl_title, 1)

        self.btn_save = QPushButton(" Guardar Estructura")
        self.btn_save.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
        self.btn_save.setStyleSheet("QPushButton { background-color: #2E7D32; color: #FFFFFF; font-weight: bold; padding: 6px 14px; border-radius: 4px; } QPushButton:hover { background-color: #1B5E20; }")
        self.btn_save.clicked.connect(self._save_structure)
        tb_layout.addWidget(self.btn_save)

        layout.addWidget(top_bar)

        # 2. Barra de Herramientas para Agregar Bloques
        add_bar = QFrame()
        add_bar.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CFD8DC; border-radius: 6px; padding: 8px;")
        ab_layout = QHBoxLayout(add_bar)
        ab_layout.setSpacing(8)

        lbl_add = QLabel("<b>Agregar Bloque:</b>")
        lbl_add.setStyleSheet("color: #37474F; font-size: 11px;")
        ab_layout.addWidget(lbl_add)

        btn_t = QPushButton("+ Texto / Instrucciones")
        btn_t.setStyleSheet("background-color: #ECEFF1; color: #37474F; font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 11px;")
        btn_t.clicked.connect(lambda: self._add_block('text'))
        ab_layout.addWidget(btn_t)

        btn_ref = QPushButton("+ Mediciones con Referencias")
        btn_ref.setStyleSheet("background-color: #E3F2FD; color: #0D47A1; font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 11px;")
        btn_ref.clicked.connect(lambda: self._add_block('ref_measurements'))
        ab_layout.addWidget(btn_ref)

        btn_man = QPushButton("+ Mediciones Manuales")
        btn_man.setStyleSheet("background-color: #EDE7F6; color: #4A148C; font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 11px;")
        btn_man.clicked.connect(lambda: self._add_block('manual_measurements'))
        ab_layout.addWidget(btn_man)

        btn_f = QPushButton("+ Pruebas Funcionales")
        btn_f.setStyleSheet("background-color: #FBE9E7; color: #BF360C; font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 11px;")
        btn_f.clicked.connect(lambda: self._add_block('functional'))
        ab_layout.addWidget(btn_f)

        btn_lvl = QPushButton("+ Niveles / Ruido")
        btn_lvl.setStyleSheet("background-color: #E0F2F1; color: #006064; font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 11px;")
        btn_lvl.clicked.connect(lambda: self._add_block('levels'))
        ab_layout.addWidget(btn_lvl)

        btn_img = QPushButton("+ Fotos / Capturas")
        btn_img.setStyleSheet("background-color: #ECEFF1; color: #263238; font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 11px;")
        btn_img.clicked.connect(lambda: self._add_block('images'))
        ab_layout.addWidget(btn_img)

        ab_layout.addStretch()
        layout.addWidget(add_bar)

        # 3. ScrollArea con el listado de bloques configurables
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.blocks_container = QWidget()
        self.blocks_container.setStyleSheet("background: transparent;")
        self.blocks_layout = QVBoxLayout(self.blocks_container)
        self.blocks_layout.setContentsMargins(0, 0, 0, 0)
        self.blocks_layout.setSpacing(12)

        self.scroll.setWidget(self.blocks_container)
        layout.addWidget(self.scroll, 1)

        self._render_blocks()

    def _render_blocks(self):
        while self.blocks_layout.count():
            c = self.blocks_layout.takeAt(0)
            if c and c.widget(): c.widget().deleteLater()
        blocks = self.structure.setdefault('blocks', [])
        for blk in blocks:
            card = GuideBlockCardWidget(blk, calibrators_list=self.calibrators_list, specs_data=self.specs_data, parent=self.blocks_container)
            card.move_up_requested.connect(self._move_block_up)
            card.move_down_requested.connect(self._move_block_down)
            card.delete_requested.connect(self._delete_block)
            card.duplicate_requested.connect(self._duplicate_block)
            self.blocks_layout.addWidget(card)
        self.blocks_layout.addStretch()

    def _add_block(self, block_type: str):
        b_id = f"blk_{os.urandom(3).hex()}"
        new_b = {'id': b_id, 'type': block_type}
        if block_type == 'text':
            new_b['title'] = '1. Información y Condiciones Ambientales'
            new_b['content'] = '<p>Verificar que la temperatura esté entre 20°C y 25°C.</p>'
        elif block_type == 'ref_measurements':
            new_b['title'] = 'Calibración y Pruebas con Referencia'
            new_b['calibrator_id'] = ''
            new_b['calibrator_name'] = ''
            new_b['points'] = []
        elif block_type == 'manual_measurements':
            new_b['title'] = 'Mediciones de Parámetros Específicos'
            new_b['points'] = []
        elif block_type == 'functional':
            new_b['title'] = 'Verificaciones Funcionales Básicas'
            new_b['items'] = []
        elif block_type == 'special_functions':
            new_b['title'] = 'Funciones Especiales y Modos'
            new_b['items'] = []
        elif block_type == 'levels':
            new_b['title'] = 'Medición de Niveles / Ruido'
            new_b['items'] = []
        elif block_type == 'images':
            new_b['title'] = 'Registro Fotográfico / Oscilogramas'
            new_b['instructions'] = 'Adjuntar capturas relevantes.'

        self.structure.setdefault('blocks', []).append(new_b)
        self._render_blocks()

    def _move_block_up(self, block_id: str):
        blocks = self.structure.setdefault('blocks', [])
        idx = next((i for i, b in enumerate(blocks) if b.get('id') == block_id), -1)
        if idx > 0:
            blocks[idx], blocks[idx - 1] = blocks[idx - 1], blocks[idx]
            self._render_blocks()

    def _move_block_down(self, block_id: str):
        blocks = self.structure.setdefault('blocks', [])
        idx = next((i for i, b in enumerate(blocks) if b.get('id') == block_id), -1)
        if idx >= 0 and idx < len(blocks) - 1:
            blocks[idx], blocks[idx + 1] = blocks[idx + 1], blocks[idx]
            self._render_blocks()

    def _delete_block(self, block_id: str):
        blocks = self.structure.setdefault('blocks', [])
        self.structure['blocks'] = [b for b in blocks if b.get('id') != block_id]
        self._render_blocks()

    def _duplicate_block(self, block_id: str):
        blocks = self.structure.setdefault('blocks', [])
        target = next((b for b in blocks if b.get('id') == block_id), None)
        if target:
            import copy
            clone = copy.deepcopy(target)
            clone['id'] = f"blk_{os.urandom(3).hex()}"
            clone['title'] = f"{clone.get('title', '')} (Copia)"
            idx = blocks.index(target)
            blocks.insert(idx + 1, clone)
            self._render_blocks()

    def _save_structure(self):
        if not self.agenda_path or not self.item: return
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        os.makedirs(inst_dir, exist_ok=True)
        struct_file = os.path.join(inst_dir, 'guia_estructura.json')
        try:
            with open(struct_file, 'w', encoding='utf-8') as f:
                json.dump(self.structure, f, indent=2, ensure_ascii=False)
            QMessageBox.information(self, "Estructura Guardada", "La estructura de la guía de prueba ha sido guardada exitosamente.")
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar la estructura: {e}")


class GuideRunnerWidget(QWidget):
    """Ejecutor / Llenado de guía de prueba en tiempo real (Modo Página Única)."""

    back_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, item: dict, agenda_path: str, test_run: dict, structure: dict, parent=None):
        super().__init__(parent)
        self.item = item or {}
        self.agenda_path = agenda_path
        self.test_run = test_run or {}
        self.structure = structure or {}
        self.read_only = (self.test_run.get('status') == 'Finalizada')
        self._inputs_map = {}
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            GuideRunnerWidget {
                background: transparent;
            }
            QLabel {
                color: #111111;
            }
            QLineEdit, QTextEdit, QPlainTextEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                selection-background-color: #BBDEFB;
                selection-color: #0D47A1;
            }
            QDateEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QComboBox {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QComboBox QAbstractItemView {
                background-color: #FFFFFF;
                color: #111111;
                selection-background-color: #BBDEFB;
                selection-color: #0D47A1;
            }
            QTableWidget {
                background-color: #FFFFFF;
                color: #111111;
                gridline-color: #ECEFF1;
                border: 1px solid #CFD8DC;
                font-size: 11px;
                selection-background-color: #E3F2FD;
                selection-color: #0D47A1;
            }
            QTableWidget QLineEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QTableWidget QComboBox {
                background-color: #FFFFFF;
                color: #111111;
                border: 1px solid #B0BEC5;
                border-radius: 3px;
                padding: 2px 6px;
            }
            QHeaderView::section {
                background-color: #2B2D42;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 4px;
                border: 1px solid #3D405B;
                min-height: 26px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # 1. Barra Superior con Estado, Correlativo y Acciones
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #1E1E2E; border: 1px solid #313244; border-radius: 6px; padding: 6px;")
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(10, 6, 10, 6)

        self.btn_back = QPushButton(" Volver")
        self.btn_back.setIcon(QIcon(os.path.join(icons_dir, 'left.svg')))
        self.btn_back.setStyleSheet("QPushButton { background-color: #313244; color: #CDD6F4; font-weight: bold; border: 1px solid #45475A; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #45475A; color: #FFFFFF; }")
        self.btn_back.clicked.connect(self.back_requested.emit)
        tb_layout.addWidget(self.btn_back)

        serial = self.test_run.get('serial', 'TES0000000')
        st = self.test_run.get('status', 'Borrador')
        st_color = "#2E7D32" if st == 'Finalizada' else "#F57C00"
        
        lbl_info = QLabel(f"Guía: <span style='color:#89B4FA; font-weight:bold;'>{serial}</span> | Instrumento: <b>{self.item.get('name')}</b>")
        lbl_info.setStyleSheet("font-size: 13px; color: #FFFFFF; margin-left: 10px;")
        tb_layout.addWidget(lbl_info, 1)

        lbl_st = QLabel(f" {st.upper()} ")
        lbl_st.setStyleSheet(f"background-color: {st_color}; color: #FFFFFF; font-weight: bold; font-size: 11px; border-radius: 4px; padding: 4px 8px;")
        tb_layout.addWidget(lbl_st)

        self.btn_pdf = QPushButton(" Exportar PDF")
        self.btn_pdf.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
        self.btn_pdf.setStyleSheet("QPushButton { background-color: #00838F; color: #FFFFFF; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #006064; }")
        self.btn_pdf.clicked.connect(self._export_pdf)
        tb_layout.addWidget(self.btn_pdf)

        if not self.read_only:
            self.btn_save_draft = QPushButton(" Guardar Borrador")
            self.btn_save_draft.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
            self.btn_save_draft.setStyleSheet("QPushButton { background-color: #1976D2; color: #FFFFFF; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #1565C0; }")
            self.btn_save_draft.clicked.connect(lambda: self._save(status='Borrador'))
            tb_layout.addWidget(self.btn_save_draft)

            self.btn_finalize = QPushButton(" Finalizar Guía")
            self.btn_finalize.setIcon(QIcon(os.path.join(icons_dir, 'check.svg')))
            self.btn_finalize.setStyleSheet("QPushButton { background-color: #2E7D32; color: #FFFFFF; font-weight: bold; padding: 6px 14px; border-radius: 4px; } QPushButton:hover { background-color: #1B5E20; }")
            self.btn_finalize.clicked.connect(self._finalize_guide)
            tb_layout.addWidget(self.btn_finalize)

        layout.addWidget(top_bar)

        # 2. Metadatos de la Ejecución (Fecha, Operador, Resumen)
        meta_card = QFrame()
        meta_card.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CFD8DC; border-radius: 6px; padding: 8px;")
        meta_layout = QHBoxLayout(meta_card)
        meta_layout.setSpacing(10)

        meta_layout.addWidget(QLabel("<b>Fecha Inicio:</b>"))
        self.dt_start = QDateEdit()
        self.dt_start.setCalendarPopup(True)
        self.dt_start.setDate(QDate.fromString(self.test_run.get('start_date', ''), Qt.DateFormat.ISODate) if self.test_run.get('start_date') else QDate.currentDate())
        self.dt_start.setEnabled(not self.read_only)
        meta_layout.addWidget(self.dt_start)

        meta_layout.addWidget(QLabel("<b>Técnico / Operador:</b>"))
        self.txt_operator = QLineEdit(self.test_run.get('operator', 'Víctor'))
        self.txt_operator.setPlaceholderText("Nombre del responsable...")
        self.txt_operator.setEnabled(not self.read_only)
        meta_layout.addWidget(self.txt_operator)

        meta_layout.addWidget(QLabel("<b>Resultado Global:</b>"))
        self.cb_result = QComboBox()
        self.cb_result.addItems(["En Progreso", "Aprobado", "Rechazado"])
        self.cb_result.setCurrentText(self.test_run.get('general_result', 'En Progreso'))
        self.cb_result.setEnabled(not self.read_only)
        meta_layout.addWidget(self.cb_result)

        meta_layout.addWidget(QLabel("<b>Resumen / Nota:</b>"))
        self.txt_summary = QLineEdit(self.test_run.get('summary', ''))
        self.txt_summary.setPlaceholderText("Observaciones generales...")
        self.txt_summary.setEnabled(not self.read_only)
        meta_layout.addWidget(self.txt_summary, 1)

        layout.addWidget(meta_card)

        # 3. ScrollArea con la ejecución de los bloques
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.runner_container = QWidget()
        self.runner_container.setStyleSheet("background: transparent;")
        self.runner_layout = QVBoxLayout(self.runner_container)
        self.runner_layout.setContentsMargins(0, 0, 0, 0)
        self.runner_layout.setSpacing(12)

        self.scroll.setWidget(self.runner_container)
        layout.addWidget(self.scroll, 1)

        self._render_runner_blocks()

    def _render_runner_blocks(self):
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        blocks = self.structure.get('blocks', [])
        blocks_data = self.test_run.setdefault('blocks_data', {})

        for blk in blocks:
            blk_id = blk.get('id', '')
            blk_type = blk.get('type', 'text')
            blk_title = blk.get('title', 'Sección de Prueba')
            b_data = blocks_data.setdefault(blk_id, {})

            card = QFrame()
            card.setStyleSheet("QFrame { background-color: #FFFFFF; border: 1px solid #CFD8DC; border-radius: 6px; padding: 12px; }")
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(10)

            lbl_t = QLabel(f"<b>{blk_title}</b>")
            lbl_t.setStyleSheet("font-size: 13px; color: #1565C0;")
            c_layout.addWidget(lbl_t)

            if blk_type == 'text':
                content = blk.get('content', '')
                lbl_c = QLabel(content)
                lbl_c.setWordWrap(True)
                lbl_c.setStyleSheet("color: #333333; font-size: 11px;")
                c_layout.addWidget(lbl_c)

            elif blk_type == 'ref_measurements':
                cal_name = blk.get('calibrator_name', 'Patrón de Calibración')
                lbl_cal = QLabel(f"<b>Patrón Referencia:</b> <span style='color:#0D47A1;'>{cal_name}</span>")
                lbl_cal.setStyleSheet("font-size: 12px; margin-bottom: 2px;")
                c_layout.addWidget(lbl_cal)

                tbl = QTableWidget()
                tbl.setColumnCount(7)
                tbl.setHorizontalHeaderLabels([
                    "Función / Escala del Instrumento", "Valor Patrón", "Límites Aceptados [Mín - Máx]", 
                    "Valor Medido", "Desviación", "Estado", "Notas"
                ])
                tbl.horizontalHeader().setFixedHeight(32)
                tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(0, 240)
                tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(1, 115)
                tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(2, 210)
                tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(3, 115)
                tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(4, 95)
                tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(5, 110)
                tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

                tbl.verticalHeader().setVisible(False)
                tbl.verticalHeader().setDefaultSectionSize(44)
                tbl.setStyleSheet("""
                    QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; gridline-color: #ECEFF1; font-size: 11px; }
                    QHeaderView { background-color: #2B2D42; border: none; }
                    QHeaderView::section { background-color: #2B2D42; color: #FFFFFF; font-weight: bold; font-size: 11px; padding: 4px 6px; border: 1px solid #3D405B; }
                """)

                points = blk.get('points', [])
                tbl.setRowCount(len(points))

                for r, pt in enumerate(points):
                    tbl.setRowHeight(r, 44)
                    pid = pt.get('id', f"pt_{r}")
                    p_res = b_data.setdefault(pid, {})

                    nom = float(pt.get('nominal', 0.0))
                    unit = pt.get('unit', 'V')
                    rng = str(pt.get('range', '')).strip()
                    fn = str(pt.get('function', 'Medición')).strip()
                    pct = float(pt.get('percent_tol', 0.05))
                    dig = int(pt.get('digits_tol', 2))
                    res = int(pt.get('resolution', 4))

                    tol_abs = (pct / 100.0 * abs(nom)) + (dig * (10 ** -res))
                    min_lim = nom - tol_abs
                    max_lim = nom + tol_abs

                    if rng:
                        lbl_fn = QLabel(f"<b>{fn}</b><br><span style='color:#1565C0; font-size:10px;'>Escala: <b>{rng}</b></span>")
                    else:
                        lbl_fn = QLabel(f"<b>{fn}</b>")
                    lbl_fn.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_fn.setStyleSheet("QLabel { background: transparent; color: #111111; padding-left: 6px; }")

                    lbl_pat = QLabel(f"<b>{nom}</b> {unit}")
                    lbl_pat.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_pat.setStyleSheet("QLabel { background: transparent; color: #111111; font-size: 11px; padding-left: 6px; }")

                    lbl_lim = QLabel(f"[{min_lim:.{res}f} a {max_lim:.{res}f}] {unit}")
                    lbl_lim.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_lim.setStyleSheet("QLabel { background: transparent; color: #455A64; font-weight: bold; font-size: 11px; padding-left: 4px; }")

                    txt_med = QLineEdit(str(p_res.get('measured', '')))
                    txt_med.setPlaceholderText("Medido...")
                    txt_med.setEnabled(not self.read_only)
                    txt_med.setFixedHeight(28)
                    txt_med.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-weight: bold; font-size: 11px; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    lbl_err = QLabel(f"{p_res.get('error', '-'):+.4f}" if isinstance(p_res.get('error'), (int, float)) else "-")
                    lbl_err.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_err.setStyleSheet("font-size: 11px; font-weight: 500;")

                    lbl_st = QLabel(p_res.get('status', 'No Evaluado'))
                    lbl_st.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_st.setFixedHeight(24)
                    self._style_status_badge(lbl_st, p_res.get('status'))

                    txt_note = QLineEdit(p_res.get('notes', ''))
                    txt_note.setPlaceholderText("Obs...")
                    txt_note.setEnabled(not self.read_only)
                    txt_note.setFixedHeight(28)
                    txt_note.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-size: 11px; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    tbl.setCellWidget(r, 0, lbl_fn)
                    tbl.setCellWidget(r, 1, lbl_pat)
                    tbl.setCellWidget(r, 2, lbl_lim)
                    tbl.setCellWidget(r, 3, txt_med)
                    tbl.setCellWidget(r, 4, lbl_err)
                    tbl.setCellWidget(r, 5, lbl_st)
                    tbl.setCellWidget(r, 6, txt_note)

                    def make_eval(p_res_ref, txt_m_w, lbl_e_w, lbl_s_w, n_val, mi_l, ma_l, txt_nt):
                        def do_eval():
                            val_str = txt_m_w.text().strip()
                            if not val_str:
                                p_res_ref.update({'measured': '', 'error': '', 'status': 'No Evaluado', 'notes': txt_nt.text().strip()})
                                lbl_e_w.setText("-")
                                lbl_s_w.setText("No Evaluado")
                                self._style_status_badge(lbl_s_w, "No Evaluado")
                                return
                            try:
                                m_val = float(val_str)
                                err = m_val - n_val
                                st = "Pasa" if (mi_l <= m_val <= ma_l) else "Falla"
                                p_res_ref.update({'measured': m_val, 'error': err, 'min_val': mi_l, 'max_val': ma_l, 'status': st, 'notes': txt_nt.text().strip()})
                                lbl_e_w.setText(f"{err:+.4f}")
                                lbl_s_w.setText(st)
                                self._style_status_badge(lbl_s_w, st)
                            except ValueError: pass
                        return do_eval

                    eval_fn = make_eval(p_res, txt_med, lbl_err, lbl_st, nom, min_lim, max_lim, txt_note)
                    txt_med.textChanged.connect(eval_fn)
                    txt_note.textChanged.connect(eval_fn)

                hdr_h = 32
                row_h = 44
                tot_h = hdr_h + (len(points) * row_h) + 12
                tbl.setFixedHeight(max(tot_h, 80))
                c_layout.addWidget(tbl)

            elif blk_type == 'manual_measurements':
                tbl = QTableWidget()
                tbl.setColumnCount(6)
                tbl.setHorizontalHeaderLabels([
                    "Parámetro / Descripción", "Nominal", "Límites [Mín - Máx]", "Valor Medido", "Estado", "Notas"
                ])
                tbl.horizontalHeader().setFixedHeight(32)
                tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(0, 220)
                tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(1, 110)
                tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(2, 190)
                tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(3, 115)
                tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(4, 110)
                tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

                tbl.verticalHeader().setVisible(False)
                tbl.verticalHeader().setDefaultSectionSize(42)
                tbl.setStyleSheet("""
                    QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                    QHeaderView { background-color: #4A148C; border: none; }
                    QHeaderView::section { background-color: #4A148C; color: #FFFFFF; font-weight: bold; font-size: 11px; padding: 4px 6px; border: 1px solid #3D405B; }
                """)

                points = blk.get('points', [])
                tbl.setRowCount(len(points))

                for r, pt in enumerate(points):
                    tbl.setRowHeight(r, 42)
                    pid = pt.get('id', f"m_{r}")
                    p_res = b_data.setdefault(pid, {})

                    nom = float(pt.get('nominal', 0.0))
                    unit = pt.get('unit', 'V')
                    desc = pt.get('description', 'Medición')
                    min_lim = float(pt.get('min_val', 0.0))
                    max_lim = float(pt.get('max_val', 0.0))

                    lbl_d = QLabel(f"<b>{desc}</b>")
                    lbl_d.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_d.setStyleSheet("QLabel { background: transparent; color: #111111; padding-left: 6px; font-size: 11px; }")

                    lbl_nom = QLabel(f"{nom} {unit}")
                    lbl_nom.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_nom.setStyleSheet("QLabel { background: transparent; color: #111111; padding-left: 6px; font-size: 11px; }")

                    lbl_lim = QLabel(f"[{min_lim} a {max_lim}] {unit}")
                    lbl_lim.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_lim.setStyleSheet("QLabel { background: transparent; color: #455A64; font-weight: bold; padding-left: 4px; font-size: 11px; }")

                    txt_med = QLineEdit(str(p_res.get('measured', '')))
                    txt_med.setPlaceholderText("Medido...")
                    txt_med.setEnabled(not self.read_only)
                    txt_med.setFixedHeight(28)
                    txt_med.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-weight: bold; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    lbl_st = QLabel(p_res.get('status', 'No Evaluado'))
                    lbl_st.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl_st.setFixedHeight(24)
                    self._style_status_badge(lbl_st, p_res.get('status'))

                    txt_note = QLineEdit(p_res.get('notes', ''))
                    txt_note.setPlaceholderText("Obs...")
                    txt_note.setEnabled(not self.read_only)
                    txt_note.setFixedHeight(28)
                    txt_note.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    tbl.setCellWidget(r, 0, lbl_d)
                    tbl.setCellWidget(r, 1, lbl_nom)
                    tbl.setCellWidget(r, 2, lbl_lim)
                    tbl.setCellWidget(r, 3, txt_med)
                    tbl.setCellWidget(r, 4, lbl_st)
                    tbl.setCellWidget(r, 5, txt_note)

                    def make_manual_eval(p_ref, txt_m_w, lbl_s_w, mi_l, ma_l, txt_nt):
                        def do_eval():
                            val_str = txt_m_w.text().strip()
                            if not val_str:
                                p_ref.update({'measured': '', 'status': 'No Evaluado', 'notes': txt_nt.text().strip()})
                                lbl_s_w.setText("No Evaluado")
                                self._style_status_badge(lbl_s_w, "No Evaluado")
                                return
                            try:
                                m_val = float(val_str)
                                st = "Pasa" if (mi_l <= m_val <= ma_l) else "Falla"
                                p_ref.update({'measured': m_val, 'min_val': mi_l, 'max_val': ma_l, 'status': st, 'notes': txt_nt.text().strip()})
                                lbl_s_w.setText(st)
                                self._style_status_badge(lbl_s_w, st)
                            except ValueError: pass
                        return do_eval

                    m_eval = make_manual_eval(p_res, txt_med, lbl_st, min_lim, max_lim, txt_note)
                    txt_med.textChanged.connect(m_eval)
                    txt_note.textChanged.connect(m_eval)

                hdr_h = 32
                row_h = 42
                tot_h = hdr_h + (len(points) * row_h) + 12
                tbl.setFixedHeight(max(tot_h, 80))
                c_layout.addWidget(tbl)

            elif blk_type in ('functional', 'special_functions'):
                tbl = QTableWidget()
                tbl.setColumnCount(4)
                tbl.setHorizontalHeaderLabels(["Ítem / Función a Probar", "Criterio de Aceptación", "Evaluación", "Notas"])
                tbl.horizontalHeader().setFixedHeight(32)
                tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(0, 220)
                tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
                tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(2, 140)
                tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(3, 180)

                tbl.verticalHeader().setVisible(False)
                tbl.verticalHeader().setDefaultSectionSize(42)
                tbl.setStyleSheet("""
                    QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                    QHeaderView { background-color: #BF360C; border: none; }
                    QHeaderView::section { background-color: #BF360C; color: #FFFFFF; font-weight: bold; font-size: 11px; padding: 4px 6px; border: 1px solid #3D405B; }
                """)

                items = blk.get('items', [])
                tbl.setRowCount(len(items))

                for r, it in enumerate(items):
                    tbl.setRowHeight(r, 42)
                    iid = it.get('id', f"f_{r}")
                    i_res = b_data.setdefault(iid, {})

                    lbl_n = QLabel(f"<b>{it.get('name', '')}</b>")
                    lbl_n.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_n.setStyleSheet("QLabel { background: transparent; color: #111111; padding-left: 6px; font-size: 11px; }")

                    lbl_d = QLabel(it.get('description', ''))
                    lbl_d.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_d.setWordWrap(True)
                    lbl_d.setStyleSheet("QLabel { background: transparent; padding-left: 6px; color: #455A64; font-size: 11px; }")

                    cb_st = QComboBox()
                    cb_st.addItems(["No Evaluado", "Conforme", "No Conforme", "No Aplica"])
                    cb_st.setCurrentText(i_res.get('status', 'No Evaluado'))
                    cb_st.setEnabled(not self.read_only)
                    cb_st.setFixedHeight(28)
                    cb_st.setStyleSheet("QComboBox { background-color: #FFFFFF; color: #111111; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; } QComboBox QAbstractItemView { background-color: #FFFFFF; color: #111111; }")

                    txt_nt = QLineEdit(i_res.get('notes', ''))
                    txt_nt.setPlaceholderText("Observaciones...")
                    txt_nt.setEnabled(not self.read_only)
                    txt_nt.setFixedHeight(28)
                    txt_nt.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    tbl.setCellWidget(r, 0, lbl_n)
                    tbl.setCellWidget(r, 1, lbl_d)
                    tbl.setCellWidget(r, 2, cb_st)
                    tbl.setCellWidget(r, 3, txt_nt)

                    def make_func_sync(i_res_ref, cb_w, txt_w):
                        def do_sync():
                            i_res_ref['status'] = cb_w.currentText()
                            i_res_ref['notes'] = txt_w.text().strip()
                        return do_sync

                    sync_fn = make_func_sync(i_res, cb_st, txt_nt)
                    cb_st.currentTextChanged.connect(sync_fn)
                    txt_nt.textChanged.connect(sync_fn)

                hdr_h = 32
                row_h = 42
                tot_h = hdr_h + (len(items) * row_h) + 12
                tbl.setFixedHeight(max(tot_h, 80))
                c_layout.addWidget(tbl)

            elif blk_type == 'levels':
                tbl = QTableWidget()
                tbl.setColumnCount(5)
                tbl.setHorizontalHeaderLabels(["Parámetro / Prueba", "Nominal", "Límite Máximo", "Valor Medido", "Notas"])
                tbl.horizontalHeader().setFixedHeight(32)
                tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(0, 220)
                tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(1, 110)
                tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(2, 130)
                tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
                tbl.horizontalHeader().resizeSection(3, 115)
                tbl.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

                tbl.verticalHeader().setVisible(False)
                tbl.verticalHeader().setDefaultSectionSize(42)
                tbl.setStyleSheet("""
                    QTableWidget { background-color: #FFFFFF; border: 1px solid #CFD8DC; font-size: 11px; }
                    QHeaderView { background-color: #006064; border: none; }
                    QHeaderView::section { background-color: #006064; color: #FFFFFF; font-weight: bold; font-size: 11px; padding: 4px 6px; border: 1px solid #3D405B; }
                """)

                items = blk.get('items', [])
                tbl.setRowCount(len(items))

                for r, it in enumerate(items):
                    tbl.setRowHeight(r, 42)
                    iid = it.get('id', f"lvl_{r}")
                    i_res = b_data.setdefault(iid, {})

                    lbl_n = QLabel(f"<b>{it.get('name', '')}</b>")
                    lbl_n.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_n.setStyleSheet("QLabel { background: transparent; color: #111111; padding-left: 6px; font-size: 11px; }")

                    unit = it.get('unit', 'mV')
                    lbl_nom = QLabel(f"{it.get('nominal', 0.0)} {unit}")
                    lbl_nom.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_nom.setStyleSheet("QLabel { background: transparent; color: #111111; padding-left: 6px; font-size: 11px; }")

                    lbl_max = QLabel(f"≤ {it.get('max_val', 0.0)} {unit}")
                    lbl_max.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                    lbl_max.setStyleSheet("QLabel { background: transparent; padding-left: 6px; font-weight: bold; color: #006064; font-size: 11px; }")

                    txt_med = QLineEdit(str(i_res.get('measured', '')))
                    txt_med.setPlaceholderText("Medido...")
                    txt_med.setEnabled(not self.read_only)
                    txt_med.setFixedHeight(28)
                    txt_med.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; font-weight: bold; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    txt_nt = QLineEdit(i_res.get('notes', ''))
                    txt_nt.setPlaceholderText("Notas...")
                    txt_nt.setEnabled(not self.read_only)
                    txt_nt.setFixedHeight(28)
                    txt_nt.setStyleSheet("QLineEdit { background-color: #FFFFFF; color: #111111; padding: 2px 6px; border: 1px solid #B0BEC5; border-radius: 3px; }")

                    tbl.setCellWidget(r, 0, lbl_n)
                    tbl.setCellWidget(r, 1, lbl_nom)
                    tbl.setCellWidget(r, 2, lbl_max)
                    tbl.setCellWidget(r, 3, txt_med)
                    tbl.setCellWidget(r, 4, txt_nt)

                    def make_lvl_sync(i_res_ref, txt_m_w, txt_n_w):
                        def do_sync():
                            i_res_ref['measured'] = txt_m_w.text().strip()
                            i_res_ref['notes'] = txt_n_w.text().strip()
                        return do_sync

                    lvl_sync = make_lvl_sync(i_res, txt_med, txt_nt)
                    txt_med.textChanged.connect(lvl_sync)
                    txt_nt.textChanged.connect(lvl_sync)

                hdr_h = 32
                row_h = 42
                tot_h = hdr_h + (len(items) * row_h) + 12
                tbl.setFixedHeight(max(tot_h, 80))
                c_layout.addWidget(tbl)

            elif blk_type == 'images':
                imgs = b_data.setdefault('images', [])
                img_container = QWidget()
                img_layout = QVBoxLayout(img_container)

                btn_add_img = QPushButton(" Adjuntar Imagen / Captura")
                btn_add_img.setIcon(QIcon(os.path.join(icons_dir, 'image_file.svg')))
                btn_add_img.setStyleSheet("QPushButton { background-color: #455A64; color: white; font-weight: bold; border-radius: 4px; padding: 5px 10px; font-size: 11px; }")
                btn_add_img.setEnabled(not self.read_only)
                
                gallery_layout = QHBoxLayout()
                gallery_layout.setSpacing(10)

                def render_gallery():
                    while gallery_layout.count():
                        c = gallery_layout.takeAt(0)
                        if c and c.widget(): c.widget().deleteLater()
                    
                    for idx, im in enumerate(imgs):
                        thumb_card = QFrame()
                        thumb_card.setStyleSheet("background-color: #F5F5F5; border: 1px solid #B0BEC5; border-radius: 4px; padding: 4px;")
                        tc_layout = QVBoxLayout(thumb_card)
                        
                        im_rel = im.get('relative_path', '')
                        im_full = os.path.join(self.agenda_path, im_rel) if self.agenda_path and not os.path.isabs(im_rel) else im_rel
                        lbl_th = QLabel()
                        lbl_th.setFixedSize(120, 90)
                        lbl_th.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        if os.path.exists(im_full):
                            pix = load_image_pixmap(im_full)
                            if not pix.isNull():
                                lbl_th.setPixmap(pix.scaled(120, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        tc_layout.addWidget(lbl_th)

                        txt_cap = QLineEdit(im.get('caption', ''))
                        txt_cap.setPlaceholderText("Pie de foto...")
                        txt_cap.setEnabled(not self.read_only)
                        txt_cap.textChanged.connect(lambda t, i=im: i.update({'caption': t}))
                        tc_layout.addWidget(txt_cap)

                        if not self.read_only:
                            btn_del_im = QPushButton(" Eliminar")
                            btn_del_im.setIcon(QIcon(os.path.join(icons_dir, 'trash_empty.svg')))
                            btn_del_im.setStyleSheet("background-color: #FFCDD2; color: #B71C1C; font-size: 10px;")
                            btn_del_im.clicked.connect(lambda ch, i_idx=idx: (imgs.pop(i_idx), render_gallery()))
                            tc_layout.addWidget(btn_del_im)

                        gallery_layout.addWidget(thumb_card)
                    gallery_layout.addStretch()

                def pick_image():
                    path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen / Captura", "", IMAGE_FILE_FILTER)
                    if path and self.agenda_path:
                        inst_dir = get_instrument_dir(self.agenda_path, self.item)
                        fname = f"capture_{os.urandom(3).hex()}{os.path.splitext(path)[1]}"
                        dest = os.path.join(inst_dir, fname)
                        shutil.copy2(path, dest)
                        rel = os.path.relpath(dest, self.agenda_path)
                        imgs.append({'filename': fname, 'relative_path': rel, 'caption': 'Captura de prueba'})
                        render_gallery()

                btn_add_img.clicked.connect(pick_image)
                img_layout.addWidget(btn_add_img, 0, Qt.AlignmentFlag.AlignLeft)
                img_layout.addLayout(gallery_layout)
                render_gallery()

                c_layout.addWidget(img_container)

            self.runner_layout.addWidget(card)

        self.runner_layout.addStretch()

    def _style_status_badge(self, lbl: QLabel, status: str):
        if status == 'Pasa' or status == 'Conforme' or status == 'Aprobado':
            lbl.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; font-weight: bold; border-radius: 3px; padding: 2px 6px;")
        elif status == 'Falla' or status == 'No Conforme' or status == 'Rechazado':
            lbl.setStyleSheet("background-color: #FFEBEE; color: #C62828; font-weight: bold; border-radius: 3px; padding: 2px 6px;")
        else:
            lbl.setStyleSheet("background-color: #ECEFF1; color: #546E7A; font-weight: bold; border-radius: 3px; padding: 2px 6px;")

    def _save(self, status: str = None) -> bool:
        if not self.agenda_path or not self.item: return False
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        file_json = os.path.join(inst_dir, 'guias_pruebas.json')

        if status:
            self.test_run['status'] = status
        self.test_run['start_date'] = self.dt_start.date().toString(Qt.DateFormat.ISODate)
        self.test_run['operator'] = self.txt_operator.text().strip()
        self.test_run['general_result'] = self.cb_result.currentText()
        self.test_run['summary'] = self.txt_summary.text().strip()

        # Cargar o crear lista
        data = {'tests': []}
        if os.path.exists(file_json):
            try:
                with open(file_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                data = {'tests': []}

        # Actualizar o insertar
        tests = data.setdefault('tests', [])
        t_id = self.test_run.get('id')
        found = False
        for i, t in enumerate(tests):
            if t.get('id') == t_id:
                tests[i] = self.test_run
                found = True
                break
        if not found:
            tests.append(self.test_run)

        try:
            with open(file_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.saved.emit()
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la prueba: {e}")
            return False

    def _finalize_guide(self):
        reply = QMessageBox.question(
            self, "Finalizar Guía de Prueba",
            "¿Confirmas que deseas finalizar y sellar esta guía de prueba?\nUna vez finalizada, quedará registrada como documento oficial y no podrá modificarse.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.test_run['end_date'] = QDate.currentDate().toString(Qt.DateFormat.ISODate)
            if self._save(status='Finalizada'):
                QMessageBox.information(self, "Guía Finalizada", "La guía ha sido completada y finalizada con éxito.")
                self.back_requested.emit()

    def _export_pdf(self):
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        serial = self.test_run.get('serial', 'TES0000')
        default_name = f"Guia_Prueba_{serial}_{self.item.get('name', 'Instrumento')}.pdf"
        default_path = os.path.join(inst_dir, default_name)

        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar Guía a PDF", default_path, "Archivos PDF (*.pdf)")
        if filepath:
            try:
                generate_test_guide_pdf(filepath, self.test_run, self.structure, self.item, self.agenda_path)
                QMessageBox.information(self, "PDF Generado", f"El informe PDF oficial fue generado exitosamente:\n{filepath}")
                open_local_file(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error al generar PDF", f"No se pudo crear el PDF: {e}")


# --- 2.6 Vista Rediseñada de Calibración en la Página Derecha ---
class InstrumentCalibrationView(QWidget):
    """Página de Calibración con Botones de Estructura, Pruebas y Tabla Histórica."""

    open_structure_requested = pyqtSignal(dict, str)
    open_runner_requested = pyqtSignal(dict, str, dict, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.agenda_path = None
        self.tests_list = []
        self.structure = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # 1. Barra Superior con Botones Principales (Estructura y Pruebas)
        action_card = QFrame()
        action_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 8px; }")
        ac_layout = QHBoxLayout(action_card)
        ac_layout.setContentsMargins(10, 6, 10, 6)
        ac_layout.setSpacing(10)

        self.btn_structure = QPushButton(" Estructura")
        self.btn_structure.setIcon(QIcon(os.path.join(icons_dir, 'new_project.svg')))
        self.btn_structure.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_structure.setStyleSheet("""
            QPushButton {
                background-color: #1565C0;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0D47A1; }
        """)
        self.btn_structure.clicked.connect(self._on_structure_clicked)
        ac_layout.addWidget(self.btn_structure)

        self.btn_run_test = QPushButton(" Pruebas")
        self.btn_run_test.setIcon(QIcon(os.path.join(icons_dir, 'tasks.svg')))
        self.btn_run_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_run_test.setStyleSheet("""
            QPushButton {
                background-color: #2E7D32;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 6px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1B5E20; }
        """)
        self.btn_run_test.clicked.connect(self._on_new_test_clicked)
        ac_layout.addWidget(self.btn_run_test)

        lbl_desc = QLabel("Guías de prueba estructuradas y calibraciones oficiales.")
        lbl_desc.setStyleSheet("color: #555555; font-size: 11px; font-style: italic; margin-left: 8px;")
        ac_layout.addWidget(lbl_desc, 1)

        layout.addWidget(action_card)

        # 2. Tabla Histórica de Guías Realizadas / En Ejecución
        lbl_tbl_title = QLabel("Historial de Guías de Prueba y Calibraciones:")
        lbl_tbl_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #222222;")
        layout.addWidget(lbl_tbl_title)

        self.tbl_guides = QTableWidget()
        self.tbl_guides.setColumnCount(7)
        self.tbl_guides.setHorizontalHeaderLabels([
            "Fecha", "Número", "Descripción / Resumen", "Resultado", "Estado", "PDF", "Acciones"
        ])
        self.tbl_guides.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tbl_guides.horizontalHeader().resizeSection(0, 95)
        self.tbl_guides.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tbl_guides.horizontalHeader().resizeSection(1, 110)
        self.tbl_guides.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tbl_guides.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tbl_guides.horizontalHeader().resizeSection(3, 100)
        self.tbl_guides.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.tbl_guides.horizontalHeader().resizeSection(4, 95)
        self.tbl_guides.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.tbl_guides.horizontalHeader().resizeSection(5, 50)
        self.tbl_guides.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.tbl_guides.horizontalHeader().resizeSection(6, 130)

        self.tbl_guides.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #CCCCCC;
                color: #111111;
                gridline-color: #E0E0E0;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #2B2D42;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 11px;
                padding: 4px;
                border: 1px solid #3D405B;
            }
        """)
        self.tbl_guides.cellDoubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self.tbl_guides, 1)

    def set_data(self, item: dict, agenda_path: str):
        self.item = item
        self.agenda_path = agenda_path
        self._load_guides()

    def _load_guides(self):
        self.tbl_guides.setRowCount(0)
        self.tests_list = []
        self.structure = {}
        if not self.item or not self.agenda_path: return

        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        struct_file = os.path.join(inst_dir, 'guia_estructura.json')
        if os.path.exists(struct_file):
            try:
                with open(struct_file, 'r', encoding='utf-8') as f:
                    self.structure = json.load(f)
            except Exception:
                self.structure = {}

        tests_file = os.path.join(inst_dir, 'guias_pruebas.json')
        if os.path.exists(tests_file):
            try:
                with open(tests_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.tests_list = data.get('tests', [])
            except Exception:
                self.tests_list = []

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        for r, t in enumerate(self.tests_list):
            self.tbl_guides.insertRow(r)

            # Fecha
            lbl_date = QLabel(t.get('start_date', '-'))
            lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Número
            lbl_num = QLabel(f"<b>{t.get('serial', '-')}</b>")
            lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_num.setStyleSheet("color: #0D47A1;")

            # Resumen
            lbl_sum = QLabel(t.get('summary', 'Guía de calibración y pruebas'))

            # Resultado
            res_str = t.get('general_result', 'En Progreso')
            lbl_res = QLabel(res_str)
            lbl_res.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if res_str == 'Aprobado':
                lbl_res.setStyleSheet("color: #2E7D32; font-weight: bold;")
            elif res_str == 'Rechazado':
                lbl_res.setStyleSheet("color: #C62828; font-weight: bold;")
            else:
                lbl_res.setStyleSheet("color: #E65100; font-weight: bold;")

            # Estado (Borrador / Finalizada)
            st = t.get('status', 'Borrador')
            lbl_st = QLabel(f" {st} ")
            lbl_st.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if st == 'Finalizada':
                lbl_st.setStyleSheet("background-color: #E8F5E9; color: #2E7D32; font-weight: bold; border-radius: 3px; padding: 2px;")
            else:
                lbl_st.setStyleSheet("background-color: #FFF3E0; color: #E65100; font-weight: bold; border-radius: 3px; padding: 2px;")

            # Icono PDF
            btn_pdf = QPushButton()
            btn_pdf.setIcon(QIcon(os.path.join(icons_dir, 'document.svg')))
            btn_pdf.setToolTip("Generar / Abrir PDF Oficial")
            btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_pdf.setStyleSheet("QPushButton { border: none; background: transparent; padding: 2px; } QPushButton:hover { background-color: #E0F2FE; border-radius: 3px; }")
            btn_pdf.clicked.connect(lambda checked, test=t: self._on_export_pdf_clicked(test))

            # Acciones (Abrir / Eliminar)
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            btn_open = QPushButton("Abrir" if st == 'Borrador' else "Ver")
            btn_open.setStyleSheet("QPushButton { background-color: #1976D2; color: white; font-weight: bold; font-size: 10px; border-radius: 3px; padding: 2px 6px; } QPushButton:hover { background-color: #1565C0; }")
            btn_open.clicked.connect(lambda checked, test=t: self._open_runner(test))
            act_layout.addWidget(btn_open)

            btn_del = QPushButton()
            btn_del.setIcon(QIcon(os.path.join(icons_dir, 'trash_empty.svg')))
            btn_del.setToolTip("Eliminar registro")
            btn_del.setStyleSheet("QPushButton { background-color: #FFEBEE; color: #C62828; font-size: 10px; border-radius: 3px; padding: 2px 4px; } QPushButton:hover { background-color: #FFCDD2; }")
            btn_del.clicked.connect(lambda checked, test=t: self._delete_test(test))
            act_layout.addWidget(btn_del)

            self.tbl_guides.setCellWidget(r, 0, lbl_date)
            self.tbl_guides.setCellWidget(r, 1, lbl_num)
            self.tbl_guides.setCellWidget(r, 2, lbl_sum)
            self.tbl_guides.setCellWidget(r, 3, lbl_res)
            self.tbl_guides.setCellWidget(r, 4, lbl_st)
            self.tbl_guides.setCellWidget(r, 5, btn_pdf)
            self.tbl_guides.setCellWidget(r, 6, act_widget)

    def _on_structure_clicked(self):
        if not self.item or not self.agenda_path: return
        self.open_structure_requested.emit(self.item, self.agenda_path)

    def _on_new_test_clicked(self):
        if not self.item or not self.agenda_path: return

        # Verificar si hay estructura
        if not self.structure or not self.structure.get('blocks'):
            reply = QMessageBox.question(
                self, "Estructura Requerida",
                f"El instrumento '{self.item.get('name')}' aún no tiene una estructura de guía de pruebas configurada.\n\n¿Deseas abrir el editor de estructura ahora para diseñarla?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._on_structure_clicked()
            return

        # Generar número correlativo con prefijo TES
        cm = CorrelativosManager(self.agenda_path)
        cm.add_or_update_type("Guía de Prueba", "TES")
        key, count, serial_str = cm.get_next_serial_info("Guía de Prueba")
        cm.commit_serial("Guía de Prueba", key, count)

        # Crear nuevo registro de prueba
        new_test = {
            'id': f"test_{os.urandom(4).hex()}",
            'serial': serial_str,
            'start_date': QDate.currentDate().toString(Qt.DateFormat.ISODate),
            'end_date': '',
            'operator': 'Víctor',
            'status': 'Borrador',
            'general_result': 'En Progreso',
            'summary': f"Calibración y Pruebas {serial_str}",
            'blocks_data': {}
        }

        # Guardar en archivo y abrir ejecutor
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        tests_file = os.path.join(inst_dir, 'guias_pruebas.json')
        data = {'tests': []}
        if os.path.exists(tests_file):
            try:
                with open(tests_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception: pass
        data.setdefault('tests', []).append(new_test)
        with open(tests_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._open_runner(new_test)

    def _on_row_double_clicked(self, row: int, col: int):
        if 0 <= row < len(self.tests_list):
            self._open_runner(self.tests_list[row])

    def _open_runner(self, test: dict):
        self.open_runner_requested.emit(self.item, self.agenda_path, test, self.structure)

    def _on_export_pdf_clicked(self, test: dict):
        inst_dir = get_instrument_dir(self.agenda_path, self.item)
        serial = test.get('serial', 'TES0000')
        default_name = f"Guia_Prueba_{serial}_{self.item.get('name', 'Instrumento')}.pdf"
        default_path = os.path.join(inst_dir, default_name)

        try:
            generate_test_guide_pdf(default_path, test, self.structure, self.item, self.agenda_path)
            QMessageBox.information(self, "PDF Generado", f"El informe PDF fue generado:\n{default_path}")
            open_local_file(default_path)
        except Exception as e:
            QMessageBox.critical(self, "Error al generar PDF", f"No se pudo crear el PDF: {e}")

    def _delete_test(self, test: dict):
        reply = QMessageBox.question(
            self, "Eliminar Guía",
            f"¿Deseas eliminar la guía '{test.get('serial')}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            inst_dir = get_instrument_dir(self.agenda_path, self.item)
            tests_file = os.path.join(inst_dir, 'guias_pruebas.json')
            if os.path.exists(tests_file):
                try:
                    with open(tests_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    tests = data.get('tests', [])
                    data['tests'] = [t for t in tests if t.get('id') != test.get('id')]
                    with open(tests_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    self._load_guides()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo eliminar el registro: {e}")


# =============================================================================
# 3. CONTENEDOR PRINCIPAL DE LA PÁGINA DERECHA EN MODO REGISTROS
# =============================================================================

class InstrumentRecordsContainer(QWidget):
    """Contenedor de la página derecha que aloja las sub-vistas del modo registros."""

    item_updated = pyqtSignal(dict)
    single_page_requested = pyqtSignal(bool)
    open_structure_editor_requested = pyqtSignal(dict, str)
    open_guide_runner_requested = pyqtSignal(dict, str, dict, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.item = None
        self.agenda_path = None
        self.lists = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 15, 25, 15)
        layout.setSpacing(10)

        # Cabecera de la página derecha
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)

        self.lbl_title = QLabel("Registro del Instrumento")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_title, 1)

        layout.addWidget(self.hdr_frame)

        # Stack con las 6 vistas
        self.stack = QStackedWidget()

        self.view_ficha = InstrumentFichaView()
        self.view_specs = InstrumentSpecificationsView()
        self.view_doc = InstrumentDocView()
        self.view_desc = InstrumentDescriptionView()
        self.view_chk = InstrumentCheckListView()
        self.view_calib = InstrumentCalibrationView()

        self.view_chk.item_updated.connect(self.item_updated.emit)
        self.view_specs.single_page_requested.connect(self.single_page_requested.emit)
        self.view_calib.open_structure_requested.connect(self.open_structure_editor_requested.emit)
        self.view_calib.open_runner_requested.connect(self.open_guide_runner_requested.emit)

        self.stack.addWidget(self.view_ficha)   # 0: Ficha
        self.stack.addWidget(self.view_specs)   # 1: Especificaciones
        self.stack.addWidget(self.view_doc)     # 2: Documentación
        self.stack.addWidget(self.view_desc)    # 3: Descripción (HTML)
        self.stack.addWidget(self.view_chk)     # 4: Check List
        self.stack.addWidget(self.view_calib)   # 5: Calibración

        layout.addWidget(self.stack, 1)

    def set_data(self, item: dict, agenda_path: str, lists: dict):
        self.item = item
        self.agenda_path = agenda_path
        self.lists = lists or {}

        if item:
            self.lbl_title.setText(f"Registro: {item.get('name', 'Instrumento')}")
            self.view_ficha.set_data(item)
            self.view_specs.set_data(item, agenda_path)
            self.view_doc.set_data(item, agenda_path)
            self.view_desc.set_data(item, agenda_path)
            self.view_chk.set_data(item, agenda_path, lists)
            self.view_calib.set_data(item, agenda_path)
        else:
            self.lbl_title.setText("Registro del Instrumento")

    def show_section(self, section_id: str):
        sec_map = {
            'ficha': (0, "Ficha del Instrumento"),
            'especificaciones': (1, "Especificaciones Técnicas y Rangos"),
            'documentacion': (2, "Documentación del Instrumento"),
            'descripcion': (3, "Descripción Técnica (HTML)"),
            'checklist': (4, "Sistema de Check List"),
            'calibracion': (5, "Guías de Prueba y Calibración")
        }
        if section_id in sec_map:
            idx, title = sec_map[section_id]
            self.stack.setCurrentIndex(idx)
            if self.item:
                self.lbl_title.setText(f"{title} - {self.item.get('name', '')}")
            else:
                self.lbl_title.setText(title)
