import os
from typing import Dict, Any
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QPushButton, QDoubleSpinBox, QFormLayout, QFrame,
    QMessageBox, QListWidget, QInputDialog
)

class DiskDialog(QDialog):
    """Diálogo para agregar o editar un disco duro."""

    def __init__(self, parent=None, item: dict = None, categories: list = None, types: list = None):
        super().__init__(parent)
        self.item = item or {}
        self.categories = categories or ["General"]
        self.types = types or ["SATA 2.5\"", "SATA 3.5\"", "NVMe M.2", "SATA M.2", "IDE", "USB Externo", "Otro"]
        
        title = "Editar Disco / Medio" if item else "Nuevo Disco / Medio"
        self.setWindowTitle(title)
        self.resize(400, 380)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-weight: bold; }
            QLineEdit, QComboBox, QDoubleSpinBox { padding: 6px; border: 1px solid #45475a; border-radius: 4px; background: #313244; color: #cdd6f4; }
            QListView { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; }
            QPushButton { background-color: #89b4fa; color: #11111b; padding: 6px 12px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #74c7ec; }
            QPushButton#btnCancel { background-color: #f38ba8; }
            QPushButton#btnCancel:hover { background-color: #eba0ac; }
        """)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        form = QFormLayout()
        form.setSpacing(10)

        # Número de Disco
        self.txt_disk_num = QLineEdit(self.item.get('disk_number', ''))
        self.txt_disk_num.setPlaceholderText("Ej: HD028, DISCO-1...")
        form.addRow("Número de Disco:", self.txt_disk_num)

        # Nombre / Etiqueta
        self.txt_name = QLineEdit(self.item.get('name', ''))
        self.txt_name.setPlaceholderText("Ej: Respaldo 1, Disco Externo WD...")
        form.addRow("Etiqueta/Nombre:", self.txt_name)

        # Tipo (2.5, 3.5, NVMe, etc)
        self.cmb_type = QComboBox()
        self.cmb_type.setEditable(True)
        self.cmb_type.addItems(self.types)
        curr_type = self.item.get('type', '')
        if curr_type and curr_type not in self.types:
            self.cmb_type.addItem(curr_type)
        self.cmb_type.setCurrentText(curr_type if curr_type else self.types[0])
        form.addRow("Tipo / Formato:", self.cmb_type)

        # Tecnología (Mecánico, SSD)
        self.cmb_tech = QComboBox()
        self.cmb_tech.addItems(["Disco Mecánico (HDD)", "Estado Sólido (SSD)", "Pendrive / Flash", "CD/DVD/BluRay", "Otro"])
        self.cmb_tech.setCurrentText(self.item.get('tech', 'Disco Mecánico (HDD)'))
        form.addRow("Tecnología:", self.cmb_tech)

        # Categoría
        self.cmb_cat = QComboBox()
        self.cmb_cat.addItems(self.categories)
        curr_cat = self.item.get('category', '')
        if curr_cat and curr_cat not in self.categories:
            self.cmb_cat.addItem(curr_cat)
        self.cmb_cat.setCurrentText(curr_cat if curr_cat else (self.categories[0] if self.categories else ''))
        form.addRow("Categoría / Uso:", self.cmb_cat)

        # Capacidad (GB)
        self.spin_cap = QDoubleSpinBox()
        self.spin_cap.setRange(0, 100000)
        self.spin_cap.setDecimals(1)
        self.spin_cap.setSuffix(" GB")
        self.spin_cap.setValue(float(self.item.get('capacity_gb', 0)))
        form.addRow("Capacidad:", self.spin_cap)

        layout.addLayout(form)
        layout.addStretch()

        # Botones
        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Guardar")
        btn_save.clicked.connect(self.accept)
        
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def get_data(self) -> Dict[str, Any]:
        data = self.item.copy() if self.item else {}
        data['disk_number'] = self.txt_disk_num.text().strip()
        data['name'] = self.txt_name.text().strip()
        data['type'] = self.cmb_type.currentText()
        data['tech'] = self.cmb_tech.currentText()
        data['category'] = self.cmb_cat.currentText()
        data['capacity_gb'] = self.spin_cap.value()
        return data


class RespaldosSettingsDialog(QDialog):
    """Diálogo de configuración para las categorías de los Respaldos."""

    def __init__(self, parent=None, config: dict = None):
        super().__init__(parent)
        self.config = config or {}
        if 'categories' not in self.config:
            self.config['categories'] = ["Películas", "Series", "Anime", "Música", "Respaldos PCs", "Videos Descargados", "General"]
        if 'types' not in self.config:
            self.config['types'] = ["SATA 2.5\"", "SATA 3.5\"", "NVMe M.2", "SATA M.2", "IDE", "USB Externo", "Otro"]
            
        self.setWindowTitle("Configuración de Respaldos")
        self.resize(350, 500)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-weight: bold; }
            QListWidget { background: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 4px 8px; }
            QPushButton:hover { background-color: #45475a; }
            QPushButton#btnSave { background-color: #a6e3a1; color: #11111b; border: none; padding: 6px 12px; font-weight: bold; }
            QPushButton#btnSave:hover { background-color: #94e2d5; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        layout.addWidget(QLabel("Categorías de Discos:"))
        
        self.list_cat = QListWidget()
        for cat in self.config.get('categories', []):
            self.list_cat.addItem(cat)
        layout.addWidget(self.list_cat)
        
        btns_list = QHBoxLayout()
        btn_add = QPushButton("Añadir")
        btn_add.clicked.connect(self._add_cat)
        btn_rem = QPushButton("Eliminar")
        btn_rem.clicked.connect(self._rem_cat)
        
        btns_list.addWidget(btn_add)
        btns_list.addWidget(btn_rem)
        btns_list.addStretch()
        layout.addLayout(btns_list)
        
        layout.addWidget(QLabel("Tipos de Discos:"))
        
        self.list_type = QListWidget()
        for t in self.config.get('types', []):
            self.list_type.addItem(t)
        layout.addWidget(self.list_type)
        
        btns_list2 = QHBoxLayout()
        btn_add_type = QPushButton("Añadir")
        btn_add_type.clicked.connect(self._add_type)
        btn_rem_type = QPushButton("Eliminar")
        btn_rem_type.clicked.connect(self._rem_type)
        
        btns_list2.addWidget(btn_add_type)
        btns_list2.addWidget(btn_rem_type)
        btns_list2.addStretch()
        layout.addLayout(btns_list2)
        
        layout.addStretch()
        
        btn_save = QPushButton("Guardar Configuración")
        btn_save.setObjectName("btnSave")
        btn_save.clicked.connect(self.accept)
        layout.addWidget(btn_save, alignment=Qt.AlignmentFlag.AlignRight)

    def _add_cat(self):
        cat, ok = QInputDialog.getText(self, "Nueva Categoría", "Nombre de la categoría:")
        if ok and cat.strip():
            self.list_cat.addItem(cat.strip())

    def _rem_cat(self):
        item = self.list_cat.currentItem()
        if item:
            self.list_cat.takeItem(self.list_cat.row(item))

    def _add_type(self):
        typ, ok = QInputDialog.getText(self, "Nuevo Tipo", "Nombre del tipo (ej. IDE 3.5\"):")
        if ok and typ.strip():
            self.list_type.addItem(typ.strip())

    def _rem_type(self):
        item = self.list_type.currentItem()
        if item:
            self.list_type.takeItem(self.list_type.row(item))

    def get_config(self) -> dict:
        cats = [self.list_cat.item(i).text() for i in range(self.list_cat.count())]
        self.config['categories'] = cats
        types = [self.list_type.item(i).text() for i in range(self.list_type.count())]
        self.config['types'] = types
        return self.config


def format_size(bytes_val: float) -> str:
    """Formatea bytes a unidad legible (B, KB, MB, GB, TB)."""
    if bytes_val >= 1024**4:
        return f"{bytes_val / (1024**4):.2f} TB"
    elif bytes_val >= 1024**3:
        return f"{bytes_val / (1024**3):.2f} GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / (1024**2):.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{int(bytes_val)} B"


class PieChartWidget(QFrame):
    """Widget que dibuja un gráfico circular de anillo estilizado con QPainter."""

    def __init__(self, slices: list, parent=None):
        super().__init__(parent)
        self.slices = slices # [{'name': str, 'value': float, 'color': QColor, 'formatted': str, 'percent': float}]
        self.setMinimumSize(220, 220)
        self.setStyleSheet("background: transparent; border: none;")

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QBrush, QPen, QColor, QFont
        from PyQt6.QtCore import QRectF

        if not self.slices:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        size = min(rect.width(), rect.height()) - 20
        cx = rect.center().x()
        cy = rect.center().y()
        chart_rect = QRectF(cx - size / 2, cy - size / 2, size, size)

        total = sum(s['value'] for s in self.slices)
        if total <= 0:
            return

        start_angle = 90 * 16 # Iniciar en las 12 en punto
        for s in self.slices:
            span_angle = int((s['value'] / total) * 360 * 16)
            if span_angle == 0 and s['value'] > 0:
                span_angle = 1
            painter.setPen(QPen(QColor("#1e1e2e"), 1.5))
            painter.setBrush(QBrush(s['color']))
            painter.drawPie(chart_rect, start_angle, span_angle)
            start_angle += span_angle

        # Anillo interior (Donut)
        hole_size = size * 0.45
        hole_rect = QRectF(cx - hole_size / 2, cy - hole_size / 2, hole_size, hole_size)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#1e1e2e")))
        painter.drawEllipse(hole_rect)

        # Texto al centro
        painter.setPen(QColor("#cdd6f4"))
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(hole_rect, Qt.AlignmentFlag.AlignCenter, "Distribución\nde Espacio")


class DiskUsageChartDialog(QDialog):
    """Ventana emergente que muestra un gráfico circular del uso de espacio del disco."""

    def __init__(self, parent=None, item: dict = None):
        super().__init__(parent)
        self.item = item or {}
        self.setWindowTitle(f"Gráfico de Espacio - {self.item.get('name', 'Disco')}")
        self.resize(700, 460)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-weight: bold; }
            QTableWidget { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; gridline-color: #45475a; }
            QHeaderView::section { background-color: #181825; color: #cdd6f4; font-weight: bold; padding: 4px; border: 1px solid #45475a; }
            QPushButton { background-color: #89b4fa; color: #11111b; padding: 6px 16px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #74c7ec; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        from PyQt6.QtGui import QColor, QPixmap, QPainter, QIcon
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        stats = self.item.get('storage_stats', {})
        total_b = float(stats.get('total_bytes', 0))
        used_b = float(stats.get('used_bytes', 0))
        free_b = float(stats.get('free_bytes', 0))
        root_items = stats.get('root_items', [])

        # Cabecera informativa
        disk_num = self.item.get('disk_number', '')
        prefix = f"[{disk_num}] " if disk_num else ""
        lbl_title = QLabel(f"Resumen de Almacenamiento: {prefix}{self.item.get('name')}")
        lbl_title.setStyleSheet("font-size: 15px; color: #89b4fa;")
        layout.addWidget(lbl_title)

        # Preparar sectores
        palette = [
            QColor("#f38ba8"), QColor("#fab387"), QColor("#f9e2af"),
            QColor("#89b4fa"), QColor("#cba6f7"), QColor("#94e2d5"),
            QColor("#b4befe"), QColor("#eba0ac")
        ]

        slices = []
        # 1. Espacio libre
        if free_b > 0 and total_b > 0:
            slices.append({
                'name': 'Espacio Libre',
                'value': free_b,
                'color': QColor("#a6e3a1"),
                'formatted': format_size(free_b),
                'percent': (free_b / total_b) * 100.0,
                'is_free': True
            })

        # 2. Carpetas principales de la raíz
        top_items = root_items[:7]
        other_items = root_items[7:]
        sum_top_sizes = 0.0

        for i, it in enumerate(top_items):
            size = float(it.get('size', 0))
            sum_top_sizes += size
            color = palette[i % len(palette)]
            pct = (size / total_b * 100.0) if total_b > 0 else 0.0
            slices.append({
                'name': f"📁 {it.get('name')}" if it.get('is_dir', True) else f"📄 {it.get('name')}",
                'value': size,
                'color': color,
                'formatted': format_size(size),
                'percent': pct,
                'is_free': False
            })

        if other_items:
            other_size = sum(float(x.get('size', 0)) for x in other_items)
            sum_top_sizes += other_size
            pct = (other_size / total_b * 100.0) if total_b > 0 else 0.0
            slices.append({
                'name': f"Otras carpetas/archivos ({len(other_items)})",
                'value': other_size,
                'color': QColor("#6c7086"),
                'formatted': format_size(other_size),
                'percent': pct,
                'is_free': False
            })

        unaccounted = max(0.0, used_b - sum_top_sizes)
        if unaccounted > (1024 * 1024 * 50): # Más de 50MB no indexados/sistema
            pct = (unaccounted / total_b * 100.0) if total_b > 0 else 0.0
            slices.append({
                'name': "Sistema / Otros datos",
                'value': unaccounted,
                'color': QColor("#585b70"),
                'formatted': format_size(unaccounted),
                'percent': pct,
                'is_free': False
            })

        # Contenedor central (Gráfico a la izquierda, Tabla a la derecha)
        center_layout = QHBoxLayout()
        center_layout.setSpacing(15)

        chart_widget = PieChartWidget(slices)
        center_layout.addWidget(chart_widget, 1)

        # Tabla de desglose
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Elemento / Categoría", "Tamaño", "% Total"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.verticalHeader().setVisible(False)

        table.setRowCount(len(slices))
        for row, s in enumerate(slices):
            # Icono de color
            pix = QPixmap(12, 12)
            pix.fill(s['color'])
            icon = QIcon(pix)

            item_name = QTableWidgetItem(icon, s['name'])
            item_size = QTableWidgetItem(s['formatted'])
            item_pct = QTableWidgetItem(f"{s['percent']:.1f} %")

            item_size.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            item_pct.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            table.setItem(row, 0, item_name)
            table.setItem(row, 1, item_size)
            table.setItem(row, 2, item_pct)

        center_layout.addWidget(table, 2)
        layout.addLayout(center_layout, 1)

        # Barra inferior con totales y botón cerrar
        bottom_layout = QHBoxLayout()
        pct_used = (used_b / total_b * 100.0) if total_b > 0 else 0.0
        tot_files = stats.get('total_files', 0)
        files_str = f" | <b>Total Archivos:</b> {tot_files:,}".replace(',', '.') if tot_files > 0 else ""
        if free_b > 0:
            lbl_stats = QLabel(f"<b>Capacidad Total:</b> {format_size(total_b)} | <b>Usado:</b> {format_size(used_b)} ({pct_used:.1f}%) | <b>Libre:</b> {format_size(free_b)}{files_str}")
        else:
            lbl_stats = QLabel(f"<b>Tamaño Total:</b> {format_size(total_b)}{files_str}")
        lbl_stats.setStyleSheet("color: #a6adc8; font-size: 12px;")
        bottom_layout.addWidget(lbl_stats)

        bottom_layout.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)

        layout.addLayout(bottom_layout)
