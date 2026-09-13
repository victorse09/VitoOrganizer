# =============================================================================
# Vito Organizer v2.2 - Bodega Dialogs
# Diálogos para registro de movimientos de inventario (ingresos y egresos)
# =============================================================================

import os
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QFormLayout, QMessageBox, QDateEdit, QCheckBox
)

class MovementDialog(QDialog):
    """Diálogo para registrar ingresos y retiros de stock."""
    
    def __init__(self, item_name: str, current_stock: int, is_egreso: bool = False, current_cost: float = 0.0, parent=None):
        super().__init__(parent)
        self.item_name = item_name
        self.current_stock = current_stock
        self.is_egreso = is_egreso
        self.current_cost = current_cost
        self.movement_data = None

        self.setWindowTitle("Registrar Egreso / Retiro" if is_egreso else "Registrar Ingreso de Stock")
        self.setMinimumWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Cabecera con nombre del ítem
        lbl_info = QLabel(f"Elemento: <b style='color: #FFFFFF;'>{self.item_name}</b><br>Stock Actual: <b style='color: #FFFFFF;'>{self.current_stock}</b>")
        lbl_info.setStyleSheet("color: #E0E0E0; font-size: 13px; background: rgba(255,255,255,0.06); padding: 8px; border-radius: 4px;")
        layout.addWidget(lbl_info)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha:", self.date_edit)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Ingreso de Stock", "Egreso / Retiro de Stock"])
        self.type_combo.setCurrentIndex(1 if self.is_egreso else 0)
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Tipo de Operación:", self.type_combo)

        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 999999)
        self.qty_spin.setValue(1)
        form.addRow("Cantidad:", self.qty_spin)

        self.cost_label = QLabel("Costo Unitario:")
        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 99999999.0)
        self.cost_spin.setDecimals(2)
        self.cost_spin.setValue(self.current_cost)
        
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        self.cost_spin.setSuffix(f" {currency}")
        form.addRow(self.cost_label, self.cost_spin)

        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Ej: Consumo de proyecto, compra proveedor, calibración...")
        form.addRow("Notas / Motivo:", self.notes_input)

        self._on_type_changed(self.type_combo.currentIndex())

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Registrar")
        btn_save.setObjectName("primaryButton")
        btn_save.setStyleSheet("background-color: #ff5722; color: #ffffff; border: none; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _save(self):
        qty = self.qty_spin.value()
        notes = self.notes_input.text().strip()
        op_type = "egreso" if self.type_combo.currentIndex() == 1 else "ingreso"

        if op_type == "egreso" and qty > self.current_stock:
            QMessageBox.warning(
                self, "Stock Insuficiente",
                f"No puedes retirar {qty} unidades. El stock actual es de {self.current_stock}."
            )
            return

        self.movement_data = {
            'date': self.date_edit.date().toString("dd/MM/yyyy"),
            'type': op_type,
            'quantity': qty,
            'notes': notes if notes else ("Retiro de inventario" if op_type == "egreso" else "Ingreso de inventario"),
            'cost_value': self.cost_spin.value() if op_type == "ingreso" else 0.0
        }
        self.accept()

    def _on_type_changed(self, index):
        is_ingreso = (index == 0)
        self.cost_label.setVisible(is_ingreso)
        self.cost_spin.setVisible(is_ingreso)


class BodegaPDFExportDialog(QDialog):
    """Diálogo de opciones de exportación a PDF para Bodega."""

    def __init__(self, current_view: str = 'stock', locations_list: list = None, parent=None):
        super().__init__(parent)
        self.current_view = current_view
        self.locations_list = locations_list or []
        self.export_config = None

        view_titles = {
            'stock': "Generar PDF - Vista de Stock",
            'saldos': "Generar PDF - Vista de Saldos y Ubicaciones",
            'costos': "Generar PDF - Valoración y Costos",
            'consolidado': "Generar PDF - Resumen Consolidado"
        }
        self.setWindowTitle(view_titles.get(current_view, "Generar Reporte PDF de Bodega"))
        self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl_header = QLabel("Seleccione los criterios de filtrado para el documento PDF:")
        lbl_header.setStyleSheet("color: #E0E0E0; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_header)

        form = QFormLayout()

        # 1. Tipo de elemento
        self.type_combo = QComboBox()
        self.type_combo.addItem("Todos (Componentes e Insumos)", "all")
        self.type_combo.addItem("Solo Componentes", "components")
        self.type_combo.addItem("Solo Insumos", "supplies")
        form.addRow("Incluir Elementos:", self.type_combo)

        # 2. Filtro de Stock
        self.stock_combo = QComboBox()
        self.stock_combo.addItem("Todos los elementos", "all")
        self.stock_combo.addItem("Bajo stock (≤ Stock Mínimo)", "low_stock")
        self.stock_combo.addItem("Stock mínimo (Exacto)", "min_stock")
        self.stock_combo.addItem("Sin stock (= 0)", "no_stock")
        self.stock_combo.addItem("Mucho stock (> 2x Mínimo)", "high_stock")
        form.addRow("Filtro de Stock:", self.stock_combo)

        # 3. Vista Saldos: Ubicación
        if self.current_view == 'saldos':
            self.loc_combo = QComboBox()
            self.loc_combo.addItem("Todas las ubicaciones", "all")
            for loc in self.locations_list:
                if loc and loc != 'No definido':
                    self.loc_combo.addItem(f"📍 {loc}", loc)
            form.addRow("Ubicación:", self.loc_combo)

            self.chk_group_loc = QCheckBox("Agrupar componentes e insumos por ubicación")
            self.chk_group_loc.setChecked(True)
            self.chk_group_loc.setStyleSheet("QCheckBox { color: #E0E0E0; font-weight: bold; }")
            form.addRow("", self.chk_group_loc)

        # 4. Vista Costos: Nivel de costo
        if self.current_view == 'costos':
            self.cost_combo = QComboBox()
            self.cost_combo.addItem("Todos los costos", "all")
            self.cost_combo.addItem("Sin costo (Valor = $0)", "no_cost")
            self.cost_combo.addItem("Costos bajos (≤ $10.000)", "low_cost")
            self.cost_combo.addItem("Costos altos (> $10.000)", "high_cost")
            form.addRow("Rango de Costo:", self.cost_combo)

        layout.addLayout(form)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_export = QPushButton("Generar PDF")
        btn_export.setStyleSheet("background-color: #ff5722; color: #ffffff; border: none; font-weight: bold; padding: 6px 16px; border-radius: 6px;")
        btn_export.clicked.connect(self._on_export)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_export)
        layout.addLayout(btn_layout)

    def _on_export(self):
        self.export_config = {
            'element_type': self.type_combo.currentData(),
            'stock_filter': self.stock_combo.currentData(),
            'location': self.loc_combo.currentData() if self.current_view == 'saldos' else 'all',
            'group_by_location': self.chk_group_loc.isChecked() if self.current_view == 'saldos' else False,
            'cost_filter': self.cost_combo.currentData() if self.current_view == 'costos' else 'all'
        }
        self.accept()


class BodegaSettingsDialog(QDialog):
    """Diálogo de configuración de la Bodega."""
    def __init__(self, plugin_data: dict = None, parent=None):
        super().__init__(parent)
        self.plugin_data = plugin_data or {}
        self.setWindowTitle("Configuración de Bodega")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl = QLabel("<b>Gestor de Bodega y Stock VitoOrganizer v2.3</b><br>Configuración de ordenación de inventario y saldos.")
        lbl.setStyleSheet("color: #333333; font-size: 12px;")
        layout.addWidget(lbl)

        # Opciones de visualización
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Orden de elementos por defecto:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Alfabético (A-Z)",
            "Alfabético (Z-A)",
            "Fecha de Ingreso (Más antiguos primero)",
            "Fecha de Ingreso (Más recientes primero)"
        ])
        
        sort_map = {'alpha_asc': 0, 'alpha_desc': 1, 'date_asc': 2, 'date_desc': 3}
        current_sort = self.plugin_data.get('bodega_sort_order', 'alpha_asc')
        self.sort_combo.setCurrentIndex(sort_map.get(current_sort, 0))
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        
        sort_layout.addWidget(self.sort_combo)
        layout.addLayout(sort_layout)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _on_sort_changed(self):
        sort_map_rev = {0: 'alpha_asc', 1: 'alpha_desc', 2: 'date_asc', 3: 'date_desc'}
        self.plugin_data['bodega_sort_order'] = sort_map_rev.get(self.sort_combo.currentIndex(), 'alpha_asc')


