# =============================================================================
# Vito Organizer v2.2 - Laboratorio Dialogs
# Diálogos para componentes electrónicos, instrumentos y herramientas
# =============================================================================

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFormLayout, QMessageBox, QDateEdit, QTabWidget, QWidget, 
    QListWidget, QInputDialog, QListWidgetItem
)
import os

def ask_spanish_confirmation(parent, title: str, text: str) -> bool:
    """Muestra un mensaje de confirmación con botones en español ('Sí' y 'No')."""
    msg = QMessageBox(parent)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setIcon(QMessageBox.Icon.Question)
    btn_yes = msg.addButton("Sí", QMessageBox.ButtonRole.YesRole)
    btn_no = msg.addButton("No", QMessageBox.ButtonRole.NoRole)
    msg.setDefaultButton(btn_no)
    msg.exec()
    return msg.clickedButton() == btn_yes


class ComponentDialog(QDialog):
    """Diálogo para crear o editar un componente electrónico."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Componente Electrónico" if item_to_edit else "Nuevo Componente Electrónico")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Resistencia 10k 1/4W, ATmega328P, NE555...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre / Valor:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('component_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo:", self.type_combo)

        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.lists.get('component_categories', []))
        if self.item_to_edit:
            self.category_combo.setCurrentText(self.item_to_edit.get('category', ''))
        else:
            self.category_combo.setCurrentText('')
        form.addRow("Categoría / Encapsulado:", self.category_combo)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Cajón 3A, Caja Transparente #2, Estante B...")
        if self.item_to_edit: self.location_input.setText(self.item_to_edit.get('storage_location', ''))
        form.addRow("Lugar de Almacenado:", self.location_input)

        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        if self.item_to_edit: 
            self.stock_spin.setValue(self.item_to_edit.get('stock_quantity', 0))
        else: 
            self.stock_spin.setValue(0)
        self.stock_spin.setEnabled(False)
        self.stock_spin.setToolTip("El stock se gestiona exclusivamente desde el módulo Bodega.")
        form.addRow("Cantidad en Stock:", self.stock_spin)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 999999)
        if self.item_to_edit: self.min_stock_spin.setValue(self.item_to_edit.get('min_stock_quantity', 0))
        else: self.min_stock_spin.setValue(0)
        form.addRow("Stock Mínimo (Reposición):", self.min_stock_spin)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 99999999.0)
        self.cost_spin.setDecimals(2)
        if self.item_to_edit: self.cost_spin.setValue(self.item_to_edit.get('cost_value', 0.0))
        else: self.cost_spin.setValue(0.0)
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        self.cost_spin.setSuffix(f" {currency}")
        form.addRow("Costo Unitario:", self.cost_spin)

        self.tested_check = QCheckBox("Componente probado / testeado funcionalmente")
        if self.item_to_edit: self.tested_check.setChecked(self.item_to_edit.get('tested', True))
        else: self.tested_check.setChecked(True)
        form.addRow("Estado de Prueba:", self.tested_check)

        self.condition_combo = QComboBox()
        self.condition_combo.addItems(self.lists.get('component_conditions', []))
        if self.item_to_edit:
            idx = self.condition_combo.findText(self.item_to_edit.get('condition', 'Nuevo (Sin uso)'))
            if idx >= 0: self.condition_combo.setCurrentIndex(idx)
        form.addRow("Condición Física:", self.condition_combo)

        self.datasheet_input = QLineEdit()
        self.datasheet_input.setPlaceholderText("https://... o ruta a PDF de Datasheet")
        if self.item_to_edit: self.datasheet_input.setText(self.item_to_edit.get('datasheet', ''))
        form.addRow("Datasheet (URL/Ruta):", self.datasheet_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Componente")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Componente")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"comp_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'category': self.category_combo.currentText().strip(),
            'storage_location': self.location_input.text().strip(),
            'stock_quantity': self.stock_spin.value(),
            'min_stock_quantity': self.min_stock_spin.value(),
            'cost_value': self.cost_spin.value(),
            'tested': self.tested_check.isChecked(),
            'condition': self.condition_combo.currentText(),
            'datasheet': self.datasheet_input.text().strip(),
            'movements': self.item_to_edit.get('movements', []) if self.item_to_edit else []
        }
        self.accept()


class InstrumentDialog(QDialog):
    """Diálogo para crear o editar un instrumento de laboratorio."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Instrumento de Lab" if item_to_edit else "Nuevo Instrumento de Lab")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Osciloscopio Digital 100MHz, Multímetro True RMS...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre Instrumento:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('instrument_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Instrumento:", self.type_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(self.lists.get('instrument_statuses', []))
        if self.item_to_edit:
            idx = self.status_combo.findText(self.item_to_edit.get('status', 'Operativo'))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        form.addRow("Estado Operativo:", self.status_combo)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Ej: Rigol, Fluke, Tektronix, Korad, Yihua...")
        if self.item_to_edit: self.brand_input.setText(self.item_to_edit.get('brand', ''))
        form.addRow("Marca:", self.brand_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Ej: DS1054Z, 87V, KA3005D...")
        if self.item_to_edit: self.model_input.setText(self.item_to_edit.get('model', ''))
        form.addRow("Modelo:", self.model_input)

        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Número de serie...")
        if self.item_to_edit: self.serial_input.setText(self.item_to_edit.get('serial_number', ''))
        form.addRow("Nº de Serie:", self.serial_input)

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("https://... o ruta a PDF de Manual de usuario")
        if self.item_to_edit: self.manual_input.setText(self.item_to_edit.get('manual', ''))
        form.addRow("Manual (URL/Ruta):", self.manual_input)

        self.supplies_input = QLineEdit()
        self.supplies_input.setPlaceholderText("Ej: Puntas de prueba 10X, fusibles 500mA, boquillas...")
        if self.item_to_edit: self.supplies_input.setText(self.item_to_edit.get('supplies', ''))
        form.addRow("Insumos / Accesorios:", self.supplies_input)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripción, notas o rango de operación...")
        self.desc_input.setMaximumHeight(70)
        if self.item_to_edit: self.desc_input.setText(self.item_to_edit.get('description', ''))
        form.addRow("Descripción:", self.desc_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Instrumento")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Instrumento")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"inst_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'status': self.status_combo.currentText(),
            'brand': self.brand_input.text().strip(),
            'model': self.model_input.text().strip(),
            'serial_number': self.serial_input.text().strip(),
            'manual': self.manual_input.text().strip(),
            'supplies': self.supplies_input.text().strip(),
            'description': self.desc_input.toPlainText().strip(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else []
        }
        self.accept()


class ToolDialog(QDialog):
    """Diálogo para crear o editar una herramienta de taller."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Herramienta de Taller" if item_to_edit else "Nueva Herramienta de Taller")
        self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Juego Destornilladores Precisión, Alicate Corte Limpio...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre Herramienta:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('tool_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo:", self.type_combo)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Ej: Wiha, Stanley, Pro'sKit, Bosch...")
        if self.item_to_edit: self.brand_input.setText(self.item_to_edit.get('brand', ''))
        form.addRow("Marca:", self.brand_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Modelo o especificación...")
        if self.item_to_edit: self.model_input.setText(self.item_to_edit.get('model', ''))
        form.addRow("Modelo / Medida:", self.model_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(self.lists.get('tool_statuses', []))
        if self.item_to_edit:
            idx = self.status_combo.findText(self.item_to_edit.get('status', 'Excelente'))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        form.addRow("Estado Operativo:", self.status_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Herramienta")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Herramienta")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"tool_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'brand': self.brand_input.text().strip(),
            'model': self.model_input.text().strip(),
            'status': self.status_combo.currentText(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else []
        }
        self.accept()


class CalibrationLogDialog(QDialog):
    """Diálogo para registrar una prueba, calibración o chequeo."""
    def __init__(self, lists: dict = None, parent=None):
        super().__init__(parent)
        self.lists = lists or {}
        self.log_data = None
        self.setWindowTitle("Registrar Calibración / Chequeo")
        self.setMinimumWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Fecha:", self.date_edit)

        self.result_combo = QComboBox()
        results = self.lists.get('calibration_results', [
            "Calibrado / Operativo Ok", 
            "Calibrado con Desviación", 
            "Mantenimiento Realizado", 
            "Falla / Requiere Reparación"
        ])
        self.result_combo.addItems(results)
        form.addRow("Resultado / Estado:", self.result_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas del ajuste, patrón utilizado o detalles de la revisión...")
        self.notes_input.setMaximumHeight(80)
        form.addRow("Detalles / Notas:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Registro")
        btn_save.setObjectName("primaryButton")
        btn_save.setStyleSheet("background-color: #ff5722; color: #ffffff; border: none; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _save(self):
        self.log_data = {
            'date': self.date_edit.date().toString("dd/MM/yyyy"),
            'result': self.result_combo.currentText(),
            'notes': self.notes_input.toPlainText().strip()
        }
        self.accept()


class SupplyDialog(QDialog):
    """Diálogo para crear o editar un insumo de laboratorio/taller."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Insumo de Lab" if item_to_edit else "Nuevo Insumo de Lab")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Flux Líquido NC-559, Pasta Térmica MX-4, Alcohol Isopropílico...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre Insumo:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('supply_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Insumo:", self.type_combo)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Ej: Amtech, Arctic, Mechanic, Kester...")
        if self.item_to_edit: self.brand_input.setText(self.item_to_edit.get('brand', ''))
        form.addRow("Marca:", self.brand_input)

        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Ej: NC-559-ASM, MX-4, 99.9%...")
        if self.item_to_edit: self.model_input.setText(self.item_to_edit.get('model', ''))
        form.addRow("Modelo / Especif.:", self.model_input)

        self.container_input = QLineEdit()
        self.container_input.setPlaceholderText("Ej: Jeringa 10cc, Pote 50g, Frasco 500ml, Rollos...")
        if self.item_to_edit: self.container_input.setText(self.item_to_edit.get('container', ''))
        form.addRow("Envase / Presentación:", self.container_input)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Armario Químicos, Estante 2, Cajón C...")
        if self.item_to_edit: self.location_input.setText(self.item_to_edit.get('storage_location', ''))
        form.addRow("Lugar Almacenado:", self.location_input)

        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        if self.item_to_edit: 
            self.stock_spin.setValue(self.item_to_edit.get('stock_quantity', 0))
        else: 
            self.stock_spin.setValue(0)
        self.stock_spin.setEnabled(False)
        self.stock_spin.setToolTip("El stock se gestiona exclusivamente desde el módulo Bodega.")
        form.addRow("Cantidad Stock:", self.stock_spin)

        self.min_stock_spin = QSpinBox()
        self.min_stock_spin.setRange(0, 999999)
        if self.item_to_edit: self.min_stock_spin.setValue(self.item_to_edit.get('min_stock_quantity', 0))
        else: self.min_stock_spin.setValue(0)
        form.addRow("Stock Mínimo (Reposición):", self.min_stock_spin)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 99999999.0)
        self.cost_spin.setDecimals(2)
        if self.item_to_edit: self.cost_spin.setValue(self.item_to_edit.get('cost_value', 0.0))
        else: self.cost_spin.setValue(0.0)
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        self.cost_spin.setSuffix(f" {currency}")
        form.addRow("Costo Unitario:", self.cost_spin)

        self.unit_combo = QComboBox()
        self.unit_combo.addItems(self.lists.get('supply_units', []))
        if self.item_to_edit:
            idx = self.unit_combo.findText(self.item_to_edit.get('unit', 'unidades'))
            if idx >= 0: self.unit_combo.setCurrentIndex(idx)
        form.addRow("Unidad de Medida:", self.unit_combo)

        self.msds_input = QLineEdit()
        self.msds_input.setPlaceholderText("https://... o ruta a PDF de Hoja de Seguridad (MSDS)")
        if self.item_to_edit: self.msds_input.setText(self.item_to_edit.get('msds', ''))
        form.addRow("Hoja Seguridad (MSDS):", self.msds_input)

        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText("https://... o ruta a PDF de Ficha Técnica / Manual")
        if self.item_to_edit: self.manual_input.setText(self.item_to_edit.get('manual', ''))
        form.addRow("Datasheet / Ficha:", self.manual_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Insumo")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Insumo")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"sup_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'brand': self.brand_input.text().strip(),
            'model': self.model_input.text().strip(),
            'container': self.container_input.text().strip(),
            'storage_location': self.location_input.text().strip(),
            'stock_quantity': self.stock_spin.value(),
            'min_stock_quantity': self.min_stock_spin.value(),
            'cost_value': self.cost_spin.value(),
            'unit': self.unit_combo.currentText(),
            'msds': self.msds_input.text().strip(),
            'manual': self.manual_input.text().strip(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else [],
            'movements': self.item_to_edit.get('movements', []) if self.item_to_edit else []
        }
        self.accept()


class CalibratorDialog(QDialog):
    """Diálogo para crear o editar un dispositivo de calibración o calibrador patrón."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Calibrador / Referencia" if item_to_edit else "Nuevo Calibrador / Dispositivo de Calibración")
        self.setMinimumWidth(460)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Fluke 732B, Placa Ref. Voltaje/Corriente v1, Ref. Resistencia 10k...")
        if self.item_to_edit:
            self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre del Calibrador:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.setEditable(True)
        default_types = [
            "Placa Referencia",
            "Referencia de tensión",
            "Referencia de Corriente",
            "Referencia pasiva",
            "Otro"
        ]
        types_list = self.lists.get('calibrator_types', default_types)
        self.type_combo.addItems(types_list)
        if self.item_to_edit:
            self.type_combo.setCurrentText(self.item_to_edit.get('type', ''))
        form.addRow("Tipo de Dispositivo:", self.type_combo)

        self.origin_combo = QComboBox()
        self.origin_combo.addItems(["Comparada", "Fabricada"])
        if self.item_to_edit:
            idx = self.origin_combo.findText(self.item_to_edit.get('origin', 'Comparada'))
            if idx >= 0:
                self.origin_combo.setCurrentIndex(idx)
        form.addRow("Origen / Clasificación:", self.origin_combo)

        self.date_calib = QDateEdit()
        self.date_calib.setCalendarPopup(True)
        if self.item_to_edit and self.item_to_edit.get('last_calibration_date'):
            self.date_calib.setDate(QDate.fromString(self.item_to_edit.get('last_calibration_date'), Qt.DateFormat.ISODate))
        else:
            self.date_calib.setDate(QDate.currentDate())
        form.addRow("Última Calibración:", self.date_calib)

        self.comments_input = QTextEdit()
        self.comments_input.setPlaceholderText("Notas, especificaciones, condiciones ambientales, trazabilidad...")
        self.comments_input.setMaximumHeight(90)
        if self.item_to_edit:
            self.comments_input.setPlainText(self.item_to_edit.get('comments', ''))
        form.addRow("Comentarios:", self.comments_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Calibrador")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Calibrador")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"calib_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText().strip(),
            'origin': self.origin_combo.currentText(),
            'last_calibration_date': self.date_calib.date().toString(Qt.DateFormat.ISODate),
            'comments': self.comments_input.toPlainText().strip(),
            'measurements': self.item_to_edit.get('measurements', []) if self.item_to_edit else [],
            'reference_points': self.item_to_edit.get('reference_points', []) if self.item_to_edit else []
        }
        self.accept()


class LabSettingsDialog(QDialog):
    """Diálogo de configuración del Laboratorio con soporte para edición de listas."""
    def __init__(self, lists: dict = None, plugin_data: dict = None, parent=None):
        super().__init__(parent)
        self.lists = lists or {}
        self.plugin_data = plugin_data or {}
        self.setWindowTitle("Configuración de Laboratorio")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.list_map = {
            "Componentes: Tipo": "component_types",
            "Componentes: Categoría/Encapsulado": "component_categories",
            "Componentes: Condición Física": "component_conditions",
            "Herramientas: Tipo": "tool_types",
            "Herramientas: Estado Operativo": "tool_statuses",
            "Insumos: Tipo": "supply_types",
            "Insumos: Unidad de Medida": "supply_units",
            "Instrumentos: Tipo de Instrumento": "instrument_types",
            "Instrumentos: Estado Operativo": "instrument_statuses",
            "Calibradores: Tipo de Referencia": "calibrator_types",
            "Chequeos: Resultado / Estado": "calibration_results",
            "Análisis y Pruebas: Categorías": "analysis_categories",
            "Desarrollo y Proyectos: Categorías": "project_categories"
        }
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Tab Widget
        self.tabs = QTabWidget()
        
        # Tab 1: Info / General
        tab_info = QWidget()
        info_layout = QVBoxLayout(tab_info)
        info_layout.setSpacing(14)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_logo = QLabel("<h2>🔬 Laboratorio y Taller</h2>")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(lbl_logo)
        
        lbl_info = QLabel(
            "<b>Gestor de Laboratorio y Taller VitoOrganizer v2.3</b><br><br>"
            "Este módulo te permite llevar un control riguroso de inventario:<br>"
            "• Componentes electrónicos y sus encapsulados.<br>"
            "• Instrumentos de precisión con registro de calibraciones.<br>"
            "• Herramientas de taller y su estado de conservación.<br>"
            "• Insumos y materiales con hojas de seguridad MSDS.<br><br>"
            "Usa la pestaña <b>Listas</b> para personalizar las opciones de los menús desplegables."
        )
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet("color: #cdd6f4; font-size: 13px;")
        info_layout.addWidget(lbl_info)
        
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
        current_sort = self.plugin_data.get('sort_order', 'alpha_asc')
        self.sort_combo.setCurrentIndex(sort_map.get(current_sort, 0))
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        
        sort_layout.addWidget(self.sort_combo)
        sort_layout.addStretch()
        info_layout.addLayout(sort_layout)
        
        info_layout.addStretch()
        
        self.tabs.addTab(tab_info, "General")

        # Tab 2: Listas
        tab_lists = QWidget()
        lists_layout = QVBoxLayout(tab_lists)
        lists_layout.setSpacing(10)
        lists_layout.setContentsMargins(15, 15, 15, 15)

        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Lista a modificar:"))
        self.list_selector = QComboBox()
        self.list_selector.addItems(list(self.list_map.keys()))
        self.list_selector.currentIndexChanged.connect(self._on_list_changed)
        selector_layout.addWidget(self.list_selector, 1)
        lists_layout.addLayout(selector_layout)

        self.items_list = QListWidget()
        self.items_list.setStyleSheet("QListWidget { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #2d314e; border-radius: 4px; padding: 4px; }")
        lists_layout.addWidget(self.items_list, 1)

        # Botones de acción para las listas
        act_btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("Agregar...")
        self.btn_add.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; min-height: 28px; border-radius: 4px; } QPushButton:hover { background-color: #94e28f; }")
        self.btn_add.clicked.connect(self._add_item)
        act_btn_layout.addWidget(self.btn_add)

        self.btn_edit = QPushButton("Editar...")
        self.btn_edit.setStyleSheet("QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; min-height: 28px; border-radius: 4px; } QPushButton:hover { background-color: #74c7ec; }")
        self.btn_edit.clicked.connect(self._edit_item)
        act_btn_layout.addWidget(self.btn_edit)

        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.setStyleSheet("QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; min-height: 28px; border-radius: 4px; } QPushButton:hover { background-color: #e78284; }")
        self.btn_delete.clicked.connect(self._delete_item)
        act_btn_layout.addWidget(self.btn_delete)

        lists_layout.addLayout(act_btn_layout)
        
        self.tabs.addTab(tab_lists, "Listas")

        layout.addWidget(self.tabs, 1)

        # Botón de Aceptar del Diálogo
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        # Cargar lista inicial
        self._on_list_changed()

    def _on_sort_changed(self):
        sort_map_rev = {0: 'alpha_asc', 1: 'alpha_desc', 2: 'date_asc', 3: 'date_desc'}
        self.plugin_data['sort_order'] = sort_map_rev.get(self.sort_combo.currentIndex(), 'alpha_asc')

    def _on_list_changed(self):
        self.items_list.clear()
        display_name = self.list_selector.currentText()
        list_key = self.list_map.get(display_name)
        if list_key and list_key in self.lists:
            for item in self.lists[list_key]:
                self.items_list.addItem(item)

    def _add_item(self):
        display_name = self.list_selector.currentText()
        list_key = self.list_map.get(display_name)
        if not list_key: return

        text, ok = QInputDialog.getText(self, "Agregar Elemento", f"Nuevo elemento para '{display_name}':")
        if ok and text.strip():
            new_val = text.strip()
            if new_val not in self.lists[list_key]:
                self.lists[list_key].append(new_val)
                self._on_list_changed()
            else:
                QMessageBox.warning(self, "Elemento duplicado", "El elemento ya existe en la lista.")

    def _edit_item(self):
        curr_row = self.items_list.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un elemento para editar.")
            return

        display_name = self.list_selector.currentText()
        list_key = self.list_map.get(display_name)
        if not list_key: return

        old_val = self.lists[list_key][curr_row]
        text, ok = QInputDialog.getText(self, "Editar Elemento", f"Editar elemento de '{display_name}':", text=old_val)
        if ok and text.strip():
            new_val = text.strip()
            if new_val == old_val: return
            
            if new_val in self.lists[list_key]:
                QMessageBox.warning(self, "Elemento duplicado", "El nuevo nombre ya existe en la lista.")
                return

            # Actualizar en la lista de opciones
            self.lists[list_key][curr_row] = new_val
            
            # Actualizar referencias en el inventario actual
            self._update_inventory_references(list_key, old_val, new_val)
            self._on_list_changed()

    def _delete_item(self):
        curr_row = self.items_list.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Atención", "Selecciona un elemento para eliminar.")
            return

        display_name = self.list_selector.currentText()
        list_key = self.list_map.get(display_name)
        if not list_key: return

        val_to_delete = self.lists[list_key][curr_row]

        # Verificar uso en inventario
        usages = self._get_usage_list(list_key, val_to_delete)
        if usages:
            # Mostrar elementos en uso
            msg = (
                f"El elemento '{val_to_delete}' está en uso en los siguientes registros del taller:\n\n"
                + "\n".join(f"• {u}" for u in usages)
                + "\n\n¿Estás seguro de que deseas eliminarlo de las opciones de selección?"
            )
            ret = QMessageBox.question(
                self, 
                "Confirmar Eliminación", 
                msg, 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if ret != QMessageBox.StandardButton.Yes:
                return

        # Proceder con la eliminación
        self.lists[list_key].pop(curr_row)
        self._on_list_changed()

    def _get_usage_list(self, list_key, value):
        used_by = []
        if list_key == 'component_types':
            for item in self.plugin_data.get('components', []):
                if item.get('type') == value:
                    used_by.append(f"Componente: {item.get('name')}")
        elif list_key == 'component_categories':
            for item in self.plugin_data.get('components', []):
                if item.get('category') == value:
                    used_by.append(f"Componente: {item.get('name')}")
        elif list_key == 'component_conditions':
            for item in self.plugin_data.get('components', []):
                if item.get('condition') == value:
                    used_by.append(f"Componente: {item.get('name')}")
        elif list_key == 'tool_types':
            for item in self.plugin_data.get('tools', []):
                if item.get('type') == value:
                    used_by.append(f"Herramienta: {item.get('name')}")
        elif list_key == 'tool_statuses':
            for item in self.plugin_data.get('tools', []):
                if item.get('status') == value:
                    used_by.append(f"Herramienta: {item.get('name')}")
        elif list_key == 'supply_types':
            for item in self.plugin_data.get('supplies', []):
                if item.get('type') == value:
                    used_by.append(f"Insumo: {item.get('name')}")
        elif list_key == 'supply_units':
            for item in self.plugin_data.get('supplies', []):
                if item.get('unit') == value:
                    used_by.append(f"Insumo: {item.get('name')}")
        elif list_key == 'instrument_types':
            for item in self.plugin_data.get('instruments', []):
                if item.get('type') == value:
                    used_by.append(f"Instrumento: {item.get('name')}")
        elif list_key == 'instrument_statuses':
            for item in self.plugin_data.get('instruments', []):
                if item.get('status') == value:
                    used_by.append(f"Instrumento: {item.get('name')}")
        elif list_key == 'analysis_categories':
            for item in self.plugin_data.get('analysis', []):
                if item.get('category') == value:
                    used_by.append(f"Análisis: {item.get('name')}")
        return used_by

    def _update_inventory_references(self, list_key, old_value, new_value):
        """Actualiza el valor en todos los elementos del inventario que lo usan."""
        updated_count = 0
        if list_key == 'component_types':
            for item in self.plugin_data.get('components', []):
                if item.get('type') == old_value:
                    item['type'] = new_value
                    updated_count += 1
        elif list_key == 'component_categories':
            for item in self.plugin_data.get('components', []):
                if item.get('category') == old_value:
                    item['category'] = new_value
                    updated_count += 1
        elif list_key == 'component_conditions':
            for item in self.plugin_data.get('components', []):
                if item.get('condition') == old_value:
                    item['condition'] = new_value
                    updated_count += 1
        elif list_key == 'tool_types':
            for item in self.plugin_data.get('tools', []):
                if item.get('type') == old_value:
                    item['type'] = new_value
                    updated_count += 1
        elif list_key == 'tool_statuses':
            for item in self.plugin_data.get('tools', []):
                if item.get('status') == old_value:
                    item['status'] = new_value
                    updated_count += 1
        elif list_key == 'supply_types':
            for item in self.plugin_data.get('supplies', []):
                if item.get('type') == old_value:
                    item['type'] = new_value
                    updated_count += 1
        elif list_key == 'supply_units':
            for item in self.plugin_data.get('supplies', []):
                if item.get('unit') == old_value:
                    item['unit'] = new_value
                    updated_count += 1
        elif list_key == 'instrument_types':
            for item in self.plugin_data.get('instruments', []):
                if item.get('type') == old_value:
                    item['type'] = new_value
                    updated_count += 1
        elif list_key == 'instrument_statuses':
            for item in self.plugin_data.get('instruments', []):
                if item.get('status') == old_value:
                    item['status'] = new_value
                    updated_count += 1
        elif list_key == 'analysis_categories':
            for item in self.plugin_data.get('analysis', []):
                if item.get('category') == old_value:
                    item['category'] = new_value
                    updated_count += 1
                    
        if updated_count > 0:
            QMessageBox.information(
                self, 
                "Referencias Actualizadas", 
                f"Se han actualizado {updated_count} registros del inventario que usaban este valor."
            )


class CheckListEditDialog(QDialog):
    """Diálogo para crear o editar una lista de chequeo (Checklist) con asignación múltiple."""
    def __init__(self, item_to_edit: dict = None, plugin_data: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.plugin_data = plugin_data or {}
        self.item_data = None
        
        self.setWindowTitle("Editar Lista de Chequeo" if item_to_edit else "Nueva Lista de Chequeo")
        self.setMinimumWidth(500)
        self.setMinimumHeight(450)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Inspección de alicates, Rutina de fuentes...")
        form.addRow("Nombre de Checklist:", self.name_input)

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Componentes", "Instrumentos", "Herramientas", "Insumos"
        ])
        self.category_combo.currentIndexChanged.connect(self._on_category_changed)
        form.addRow("Categoría:", self.category_combo)

        # Usar un QListWidget para asignación múltiple
        self.elements_list = QListWidget()
        self.elements_list.setStyleSheet("""
            QListWidget { background-color: #1e1e2e; color: #f5f5f5; border: 1px solid #45475a; border-radius: 6px; padding: 4px; }
            QListWidget::item { padding: 4px 6px; }
        """)
        self.elements_list.setMaximumHeight(130)
        form.addRow("Elementos Asignados:", self.elements_list)

        # Editor de ítems del checklist
        self.items_text = QTextEdit()
        self.items_text.setPlaceholderText(
            "[Grupo 1: Inspección Visual]\n"
            "Verificar que la carcasa no tenga trizaduras\n"
            "Comprobar estado de las puntas de prueba\n\n"
            "[Grupo 2: Funcionalidad]\n"
            "Encender y verificar voltaje de batería\n"
            "Probar continuidad con zumbador"
        )
        form.addRow("Grupos e Ítems:\n(Escriba un grupo entre corchetes [ ]\ny los ítems debajo, uno por línea)", self.items_text)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Checklist")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _on_category_changed(self):
        self.elements_list.clear()
        category_name = self.category_combo.currentText()
        key_map = {
            "Componentes": "components",
            "Instrumentos": "instruments",
            "Herramientas": "tools",
            "Insumos": "supplies"
        }
        key = key_map.get(category_name, "components")
        elements = self.plugin_data.get(key, [])
        
        assigned = []
        if self.item_to_edit:
            assigned = self.item_to_edit.get('assigned_element_ids', [])
            if not assigned and self.item_to_edit.get('assigned_element_id'):
                assigned = [self.item_to_edit.get('assigned_element_id')]

        for el in elements:
            el_name = el.get('name', 'Sin nombre')
            el_id = el.get('id')
            
            item = QListWidgetItem(el_name)
            item.setData(Qt.ItemDataRole.UserRole, el_id)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            if el_id in assigned:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
                
            self.elements_list.addItem(item)

    def _load_values(self):
        if self.item_to_edit:
            self.name_input.setText(self.item_to_edit.get('name', ''))
            
            key_map_rev = {
                "components": "Componentes",
                "instruments": "Instrumentos",
                "tools": "Herramientas",
                "supplies": "Insumos"
            }
            cat_val = key_map_rev.get(self.item_to_edit.get('category', ''), "Componentes")
            idx = self.category_combo.findText(cat_val)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            
            self._on_category_changed()

            # Reconstruir texto
            text = ""
            for g in self.item_to_edit.get('groups', []):
                text += f"[{g.get('name', '')}]\n"
                for item in g.get('items', []):
                    text += f"{item}\n"
                text += "\n"
            self.items_text.setText(text.strip())
        else:
            self._on_category_changed()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        el_ids = []
        for i in range(self.elements_list.count()):
            item = self.elements_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                el_ids.append(item.data(Qt.ItemDataRole.UserRole))

        if not el_ids:
            QMessageBox.warning(self, "Atención", "Debe seleccionar al menos un elemento para asignar el checklist.")
            return

        text_content = self.items_text.toPlainText()
        groups = []
        current_group = None

        for line in text_content.split('\n'):
            line = line.strip()
            if not line:
                continue
            if line.startswith('[') and line.endswith(']'):
                current_group = {
                    'name': line[1:-1].strip(),
                    'items': []
                }
                groups.append(current_group)
            else:
                if current_group is None:
                    current_group = {
                        'name': 'General',
                        'items': []
                    }
                    groups.append(current_group)
                current_group['items'].append(line)

        if not groups or not any(g['items'] for g in groups):
            QMessageBox.warning(self, "Atención", "Debe ingresar al menos un ítem de chequeo.")
            return

        category_map = {
            "Componentes": "components",
            "Instrumentos": "instruments",
            "Herramientas": "tools",
            "Insumos": "supplies"
        }

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"chk_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'category': category_map.get(self.category_combo.currentText(), "components"),
            'assigned_element_ids': el_ids,
            'assigned_element_id': el_ids[0], # Retrocompatibilidad
            'groups': groups
        }
        self.accept()


class CheckListManagerDialog(QDialog):
    """Diálogo para administrar las listas de chequeo."""
    def __init__(self, plugin_data: dict = None, parent=None):
        super().__init__(parent)
        self.plugin_data = plugin_data or {}
        self.checklists = self.plugin_data.setdefault('checklists', [])
        
        self.setWindowTitle("Administrar Listas de Chequeo")
        self.setMinimumWidth(550)
        self.setMinimumHeight(400)
        self._setup_ui()
        self._load_checklists()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel("<b>Listas de Chequeo Definidas</b>")
        title.setStyleSheet("font-size: 13px; color: #f9e2af;")
        layout.addWidget(title)

        h_layout = QHBoxLayout()

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1e1e2e; color: #f5f5f5; border: 1px solid #45475a; border-radius: 6px; padding: 6px; }
            QListWidget::item { padding: 8px 10px; border-bottom: 1px solid #313244; }
            QListWidget::item:selected { background-color: #45475a; color: #f9e2af; border-radius: 4px; }
        """)
        h_layout.addWidget(self.list_widget, 1)

        btn_box = QVBoxLayout()
        btn_box.setSpacing(8)

        self.btn_new = QPushButton("Nueva Lista")
        self.btn_new.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #a6e3a1; color: #11111b; } QPushButton:hover { background-color: #94e28f; }")
        self.btn_new.clicked.connect(self._new_checklist)
        
        self.btn_edit = QPushButton("Editar...")
        self.btn_edit.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #89b4fa; color: #11111b; } QPushButton:hover { background-color: #74c7ec; }")
        self.btn_edit.clicked.connect(self._edit_checklist)
        
        self.btn_delete = QPushButton("Eliminar")
        self.btn_delete.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #f38ba8; color: #11111b; } QPushButton:hover { background-color: #e78284; }")
        self.btn_delete.clicked.connect(self._delete_checklist)

        btn_box.addWidget(self.btn_new)
        btn_box.addWidget(self.btn_edit)
        btn_box.addWidget(self.btn_delete)
        btn_box.addStretch()
        h_layout.addLayout(btn_box)

        layout.addLayout(h_layout)

        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setFixedWidth(100)
        btn_ok.clicked.connect(self.accept)
        layout.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignRight)

    def _load_checklists(self):
        self.list_widget.clear()
        
        category_labels = {
            "components": "Componentes",
            "instruments": "Instrumentos",
            "tools": "Herramientas",
            "supplies": "Insumos"
        }

        for chk in self.checklists:
            cat = chk.get('category', '')
            el_ids = chk.get('assigned_element_ids', [])
            if not el_ids and chk.get('assigned_element_id'):
                el_ids = [chk.get('assigned_element_id')]
            
            el_names = []
            elements = self.plugin_data.get(cat, [])
            for el in elements:
                if el.get('id') in el_ids:
                    el_names.append(el.get('name', 'Sin nombre'))
            
            if len(el_names) == 0:
                el_display = "Ninguno"
            elif len(el_names) <= 3:
                el_display = ", ".join(el_names)
            else:
                el_display = f"{len(el_names)} elementos"

            cat_label = category_labels.get(cat, cat)
            display_text = f"{chk.get('name')}  [{cat_label}: {el_display}]"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, chk.get('id'))
            self.list_widget.addItem(item)

    def _new_checklist(self):
        dlg = CheckListEditDialog(plugin_data=self.plugin_data, parent=self)
        if dlg.exec() and dlg.item_data:
            self.checklists.append(dlg.item_data)
            self._load_checklists()

    def _edit_checklist(self):
        curr_row = self.list_widget.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un checklist para editar.")
            return

        chk_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        chk_item = None
        for c in self.checklists:
            if c.get('id') == chk_id:
                chk_item = c
                break

        if chk_item:
            dlg = CheckListEditDialog(item_to_edit=chk_item, plugin_data=self.plugin_data, parent=self)
            if dlg.exec() and dlg.item_data:
                idx = self.checklists.index(chk_item)
                self.checklists[idx] = dlg.item_data
                self._load_checklists()

    def _delete_checklist(self):
        curr_row = self.list_widget.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Atención", "Seleccione un checklist para eliminar.")
            return

        chk_id = self.list_widget.currentItem().data(Qt.ItemDataRole.UserRole)
        chk_item = None
        for c in self.checklists:
            if c.get('id') == chk_id:
                chk_item = c
                break

        ret = QMessageBox.question(
            self, "Confirmar Eliminación",
            "¿Está seguro de que desea eliminar esta lista de chequeo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if ret == QMessageBox.StandardButton.Yes:
            if chk_item in self.checklists:
                self.checklists.remove(chk_item)
            self._load_checklists()


class CheckListEventDialog(QDialog):
    """Diálogo para registrar una prueba/mantenimiento completando una lista de chequeo."""
    def __init__(self, checklist: dict, agenda_path: str = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.checklist = checklist
        self.agenda_path = agenda_path
        self.lists = lists or {}
        self.log_data = None
        
        self.setWindowTitle(f"Chequeo: {checklist.get('name')}")
        self.setMinimumWidth(480)
        self.setMinimumHeight(550)
        self._setup_ui()
        self._update_serial_number()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.dateChanged.connect(self._update_serial_number)
        form.addRow("Fecha:", self.date_edit)

        self.serial_label = QLabel("——")
        self.serial_label.setStyleSheet("font-weight: bold; color: #f9e2af; font-size: 13px;")
        form.addRow("Número de Chequeo:", self.serial_label)

        self.result_combo = QComboBox()
        results = self.lists.get('calibration_results', [
            "Calibrado / Operativo Ok", 
            "Calibrado con Desviación", 
            "Mantenimiento Realizado", 
            "Falla / Requiere Reparación"
        ])
        self.result_combo.addItems(results)
        form.addRow("Resultado / Estado:", self.result_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Detalles adicionales del mantenimiento...")
        self.notes_input.setMaximumHeight(60)
        form.addRow("Notas:", self.notes_input)

        layout.addLayout(form)

        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 4px; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        self.checkbox_map = {}

        for g in self.checklist.get('groups', []):
            g_name = g.get('name', 'General')
            g_label = QLabel(f"<b>{g_name}</b>")
            g_label.setStyleSheet("color: #a6e3a1; font-size: 12px; margin-top: 5px;")
            scroll_layout.addWidget(g_label)

            for item_text in g.get('items', []):
                cb = QCheckBox(item_text)
                cb.setStyleSheet("QCheckBox { color: #cdd6f4; }")
                scroll_layout.addWidget(cb)
                
                key = f"{g_name}_{item_text}"
                self.checkbox_map[key] = cb

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Registro")
        btn_save.setObjectName("primaryButton")
        btn_save.setStyleSheet("background-color: #2e7d32; color: #ffffff; border: none; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _get_next_serial_info(self):
        from core.correlativos_manager import CorrelativosManager
        manager = CorrelativosManager(self.agenda_path)
        yymm, count, serial_str = manager.get_next_serial_info("Check List", self.date_edit.date())
        return yymm, count, serial_str

    def _update_serial_number(self):
        _, _, serial_str = self._get_next_serial_info()
        self.serial_label.setText(serial_str)

    def _save(self):
        yymm, count, serial_str = self._get_next_serial_info()
        
        from core.correlativos_manager import CorrelativosManager
        manager = CorrelativosManager(self.agenda_path)
        manager.commit_serial("Check List", yymm, count)

        answers = {}
        for key, cb in self.checkbox_map.items():
            answers[key] = cb.isChecked()

        self.log_data = {
            'date': self.date_edit.date().toString("dd/MM/yyyy"),
            'result': self.result_combo.currentText(),
            'notes': self.notes_input.toPlainText().strip(),
            'check_number': serial_str,
            'checklist_id': self.checklist.get('id'),
            'checklist_answers': answers
        }
        self.accept()


class CheckListViewDialog(QDialog):
    """Diálogo para ver una lista de chequeo completada de forma de sólo lectura."""
    def __init__(self, log_entry: dict, checklist_def: dict, item: dict = None, agenda_path: str = None, parent=None):
        super().__init__(parent)
        self.log_entry = log_entry
        self.checklist_def = checklist_def
        self.item = item or {}
        self.agenda_path = agenda_path
        
        self.setWindowTitle(f"Chequeo Completado: {self.log_entry.get('check_number', '——')}")
        self.setMinimumWidth(480)
        self.setMinimumHeight(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        
        lbl_date = QLabel(self.log_entry.get('date', '——'))
        form.addRow("Fecha del Chequeo:", lbl_date)

        lbl_serial = QLabel(self.log_entry.get('check_number', '——'))
        lbl_serial.setStyleSheet("font-weight: bold; color: #f9e2af;")
        form.addRow("Número de Chequeo:", lbl_serial)

        lbl_result = QLabel(self.log_entry.get('result', '——'))
        form.addRow("Resultado / Estado:", lbl_result)

        lbl_notes = QLabel(self.log_entry.get('notes', '——'))
        lbl_notes.setWordWrap(True)
        form.addRow("Notas:", lbl_notes)

        layout.addLayout(form)

        from PyQt6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 4px; }")

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        answers = self.log_entry.get('checklist_answers', {})

        if self.checklist_def:
            for g in self.checklist_def.get('groups', []):
                g_name = g.get('name', 'General')
                g_label = QLabel(f"<b>{g_name}</b>")
                g_label.setStyleSheet("color: #a6e3a1; font-size: 12px; margin-top: 5px;")
                scroll_layout.addWidget(g_label)

                for item_text in g.get('items', []):
                    cb = QCheckBox(item_text)
                    cb.setEnabled(False)
                    cb.setStyleSheet("QCheckBox { color: #cdd6f4; }")
                    
                    key = f"{g_name}_{item_text}"
                    is_checked = answers.get(key, False)
                    cb.setChecked(is_checked)
                    
                    scroll_layout.addWidget(cb)
        else:
            lbl_warning = QLabel("<i>Definición de lista de chequeo original no encontrada. Respuestas:</i>")
            lbl_warning.setStyleSheet("color: #f38ba8;")
            scroll_layout.addWidget(lbl_warning)
            
            for key, val in answers.items():
                parts = key.split('_', 1)
                item_label = parts[1] if len(parts) > 1 else key
                cb = QCheckBox(item_label)
                cb.setEnabled(False)
                cb.setChecked(val)
                cb.setStyleSheet("QCheckBox { color: #cdd6f4; }")
                scroll_layout.addWidget(cb)

        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        btn_layout = QHBoxLayout()
        
        btn_pdf = QPushButton(" Descargar PDF")
        btn_pdf.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'document.svg')))
        btn_pdf.setStyleSheet("background-color: #f38ba8; color: #111111; border: none; font-weight: bold; padding: 6px 14px; border-radius: 6px;")
        btn_pdf.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_pdf.clicked.connect(self._export_pdf)
        btn_layout.addWidget(btn_pdf, alignment=Qt.AlignmentFlag.AlignLeft)
        
        btn_layout.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("primaryButton")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

        layout.addLayout(btn_layout)

    def _export_pdf(self):
        from plugins.laboratorio.pdf_export import generate_checklist_pdf
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte en PDF",
            f"Informe_{self.log_entry.get('check_number', 'CHK')}.pdf",
            "PDF Files (*.pdf)"
        )
        if filepath:
            try:
                generate_checklist_pdf(filepath, self.log_entry, self.checklist_def, self.item, self.agenda_path)
                QMessageBox.information(self, "PDF Generado", f"El informe fue guardado exitosamente en:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error al generar PDF", f"Ocurrió un error al crear el archivo PDF:\n{str(e)}")


class AnalysisDialog(QDialog):
    """Diálogo para crear o editar un Análisis y Pruebas."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False
        
        self.setWindowTitle("Editar Análisis y Pruebas" if item_to_edit else "Nuevo Análisis y Pruebas")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Pruebas de Disipadores, Test Lote A...")
        form.addRow("Nombre:", self.name_input)
        
        self.category_combo = QComboBox()
        categories = self.lists.get('analysis_categories', ["Otro"])
        self.category_combo.addItems(categories)
        form.addRow("Categoría:", self.category_combo)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Comentario o descripción del análisis...")
        self.comment_input.setMaximumHeight(80)
        form.addRow("Comentario:", self.comment_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Elemento")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _load_values(self):
        if self.item_to_edit:
            self.name_input.setText(self.item_to_edit.get('name', ''))
            cat = self.item_to_edit.get('category', '')
            idx = self.category_combo.findText(cat)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.comment_input.setText(self.item_to_edit.get('comment', ''))

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        cat = self.category_combo.currentText()
        
        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"ana_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'category': cat,
            'comment': self.comment_input.toPlainText().strip(),
            'calculations': self.item_to_edit.get('calculations', []) if self.item_to_edit else []
        }
        self.accept()


class CalculationDialog(QDialog):
    """Diálogo para agregar o editar un cálculo o documento a un análisis."""
    def __init__(self, item_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.item_data = None
        self.is_delete = False
        
        self.setWindowTitle("Editar Cálculo" if item_to_edit else "Nuevo Cálculo / Documento")
        self.setMinimumWidth(350)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Espectrometría, Resultado visual...")
        form.addRow("Nombre del Cálculo:", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Texto Enriquecido", "Texto", "Imagen", "Markdown (MD)"])
        form.addRow("Tipo:", self.type_combo)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Comentario breve...")
        self.comment_input.setMaximumHeight(60)
        form.addRow("Comentario:", self.comment_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Cálculo")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar el cálculo '{self.item_to_edit.get('name')}'?\nEl cálculo se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _load_values(self):
        if self.item_to_edit:
            self.name_input.setText(self.item_to_edit.get('name', ''))
            
            t = self.item_to_edit.get('type', 'Texto')
            idx = self.type_combo.findText(t)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.type_combo.setEnabled(False) # No permitir cambiar tipo una vez creado
            
            self.comment_input.setText(self.item_to_edit.get('comment', ''))

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"calc_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'comment': self.comment_input.toPlainText().strip()
        }
        self.accept()


class ProjectDialog(QDialog):
    """Diálogo para crear o editar un Proyecto de Desarrollo."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False
        
        self.setWindowTitle("Editar Proyecto / Desarrollo" if item_to_edit else "Nuevo Proyecto / Desarrollo")
        self.setMinimumWidth(400)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Sistema de Monitoreo IoT, Firmware PCB...")
        form.addRow("Nombre del Proyecto:", self.name_input)
        
        self.category_combo = QComboBox()
        categories = self.lists.get('project_categories', ["Hardware", "Software / Firmware", "Diseño PCB", "Mecánica / 3D", "Investigación", "Otro"])
        self.category_combo.addItems(categories)
        form.addRow("Categoría:", self.category_combo)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Objetivo, descripción o especificaciones del proyecto...")
        self.comment_input.setMaximumHeight(80)
        form.addRow("Comentario / Notas:", self.comment_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Proyecto")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar el proyecto '{self.item_to_edit.get('name')}'?\nEl proyecto se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _load_values(self):
        if self.item_to_edit:
            self.name_input.setText(self.item_to_edit.get('name', ''))
            cat = self.item_to_edit.get('category', '')
            idx = self.category_combo.findText(cat)
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)
            self.comment_input.setText(self.item_to_edit.get('comment', ''))

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        cat = self.category_combo.currentText()
        
        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"proj_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'category': cat,
            'comment': self.comment_input.toPlainText().strip(),
            'calculations': self.item_to_edit.get('calculations', []) if self.item_to_edit else []
        }
        self.accept()


class ProjectCalculationDialog(QDialog):
    """Diálogo para agregar o editar un módulo/documento a un Proyecto de Desarrollo."""
    def __init__(self, item_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.item_data = None
        self.is_delete = False
        
        self.setWindowTitle("Editar Elemento de Proyecto" if item_to_edit else "Nuevo Elemento / Documento de Proyecto")
        self.setMinimumWidth(380)
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Arquitectura del Sistema, Código Firmware, Diagrama...")
        form.addRow("Nombre del Elemento:", self.name_input)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Texto Enriquecido",
            "Editor de Código",
            "Mapa Mental",
            "Diagrama de Flujo (Draw.io)",
            "Dibujo / Paint",
            "Visor 3D STL / G-Code",
            "Visor KiCad / Gerber",
            "Editor de Diagramas Esquemáticos",
            "Documentación Biblioteca",
            "Texto",
            "Imagen"
        ])
        form.addRow("Tipo de Herramienta:", self.type_combo)

        self.comment_input = QTextEdit()
        self.comment_input.setPlaceholderText("Comentario breve...")
        self.comment_input.setMaximumHeight(60)
        form.addRow("Comentario:", self.comment_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Elemento")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}'?\nEl elemento se moverá a la Papelera."):
            self.is_delete = True
            self.accept()

    def _load_values(self):
        if self.item_to_edit:
            self.name_input.setText(self.item_to_edit.get('name', ''))
            
            t = self.item_to_edit.get('type', 'Texto Enriquecido')
            idx = self.type_combo.findText(t)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
            self.type_combo.setEnabled(False) # No cambiar tipo una vez creado
            
            self.comment_input.setText(self.item_to_edit.get('comment', ''))

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"pcalc_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'comment': self.comment_input.toPlainText().strip()
        }
        self.accept()
