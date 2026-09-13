# =============================================================================
# Vito Organizer v2.11 - Retro Dialogs
# Diálogos para computadoras retro, medios, periféricos y modificaciones
# =============================================================================

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QFormLayout, QMessageBox, QDateEdit, QTabWidget, QWidget, 
    QListWidget, QInputDialog, QListWidgetItem, QScrollArea, QFileDialog
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


class ComputerDialog(QDialog):
    """Diálogo para crear o editar una computadora retro."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Equipo Retro" if item_to_edit else "Nuevo Equipo Retro")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Atari 800XL, Commodore 64...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre del Equipo:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('computer_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Plataforma / Arquitectura:", self.type_combo)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Ej: Atari, Commodore, Sinclair...")
        if self.item_to_edit: self.brand_input.setText(self.item_to_edit.get('brand', ''))
        form.addRow("Marca:", self.brand_input)

        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Número de Serie...")
        if self.item_to_edit: self.serial_input.setText(self.item_to_edit.get('serial_number', ''))
        form.addRow("Nº de Serie:", self.serial_input)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Vitrina 1, Caja Fuerte...")
        if self.item_to_edit: self.location_input.setText(self.item_to_edit.get('storage_location', ''))
        form.addRow("Lugar de Almacenado:", self.location_input)

        self.condition_combo = QComboBox()
        self.condition_combo.addItems(self.lists.get('conditions', []))
        if self.item_to_edit:
            idx = self.condition_combo.findText(self.item_to_edit.get('condition', ''))
            if idx >= 0: self.condition_combo.setCurrentIndex(idx)
        form.addRow("Condición Estética:", self.condition_combo)

        self.status_combo = QComboBox()
        self.status_combo.addItems(self.lists.get('statuses', []))
        if self.item_to_edit:
            idx = self.status_combo.findText(self.item_to_edit.get('status', ''))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        form.addRow("Estado Funcional:", self.status_combo)

        self.mods_input = QLineEdit()
        self.mods_input.setPlaceholderText("Ej: UAV Video, 1MB RAM, S-Video...")
        if self.item_to_edit: self.mods_input.setText(self.item_to_edit.get('modifications', ''))
        form.addRow("Modificaciones Instaladas:", self.mods_input)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 99999999.0)
        self.cost_spin.setDecimals(2)
        if self.item_to_edit: self.cost_spin.setValue(self.item_to_edit.get('cost_value', 0.0))
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        self.cost_spin.setSuffix(f" {currency}")
        form.addRow("Valor Estimado:", self.cost_spin)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionales, historia del equipo...")
        self.notes_input.setMaximumHeight(80)
        if self.item_to_edit: self.notes_input.setText(self.item_to_edit.get('notes', ''))
        form.addRow("Notas:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Equipo")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Equipo")
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
            'brand': self.brand_input.text().strip(),
            'serial_number': self.serial_input.text().strip(),
            'storage_location': self.location_input.text().strip(),
            'condition': self.condition_combo.currentText(),
            'status': self.status_combo.currentText(),
            'modifications': self.mods_input.text().strip(),
            'cost_value': self.cost_spin.value(),
            'notes': self.notes_input.toPlainText().strip(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else []
        }
        self.accept()


class MediaDialog(QDialog):
    """Diálogo para crear o editar medios de almacenamiento retro."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Medio Retro" if item_to_edit else "Nuevo Medio Retro")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Pac-Man, Montezuma's Revenge...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Título / Nombre:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('media_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Medio:", self.type_combo)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.lists.get('computer_types', []))
        if self.item_to_edit:
            idx = self.platform_combo.findText(self.item_to_edit.get('platform', ''))
            if idx >= 0: self.platform_combo.setCurrentIndex(idx)
        form.addRow("Plataforma Compatible:", self.platform_combo)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Estante Cartuchos...")
        if self.item_to_edit: self.location_input.setText(self.item_to_edit.get('storage_location', ''))
        form.addRow("Lugar de Almacenado:", self.location_input)

        self.condition_combo = QComboBox()
        self.condition_combo.addItems(self.lists.get('conditions', []))
        if self.item_to_edit:
            idx = self.condition_combo.findText(self.item_to_edit.get('condition', ''))
            if idx >= 0: self.condition_combo.setCurrentIndex(idx)
        form.addRow("Condición:", self.condition_combo)

        self.cost_spin = QDoubleSpinBox()
        self.cost_spin.setRange(0.0, 99999999.0)
        self.cost_spin.setDecimals(2)
        if self.item_to_edit: self.cost_spin.setValue(self.item_to_edit.get('cost_value', 0.0))
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        self.cost_spin.setSuffix(f" {currency}")
        form.addRow("Valor Estimado:", self.cost_spin)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas...")
        self.notes_input.setMaximumHeight(80)
        if self.item_to_edit: self.notes_input.setText(self.item_to_edit.get('notes', ''))
        form.addRow("Notas:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Medio")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Medio")
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
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"media_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'platform': self.platform_combo.currentText(),
            'storage_location': self.location_input.text().strip(),
            'condition': self.condition_combo.currentText(),
            'cost_value': self.cost_spin.value(),
            'notes': self.notes_input.toPlainText().strip(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else []
        }
        self.accept()


class PeripheralDialog(QDialog):
    """Diálogo para crear o editar un periférico retro."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Periférico" if item_to_edit else "Nuevo Periférico")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: 1050 Disk Drive, SIO2SD...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre del Periférico:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('peripheral_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo:", self.type_combo)

        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.lists.get('computer_types', []))
        if self.item_to_edit:
            idx = self.platform_combo.findText(self.item_to_edit.get('platform', ''))
            if idx >= 0: self.platform_combo.setCurrentIndex(idx)
        form.addRow("Plataforma Compatible:", self.platform_combo)

        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText("Marca / Fabricante...")
        if self.item_to_edit: self.brand_input.setText(self.item_to_edit.get('brand', ''))
        form.addRow("Marca:", self.brand_input)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Caja 3...")
        if self.item_to_edit: self.location_input.setText(self.item_to_edit.get('storage_location', ''))
        form.addRow("Lugar de Almacenado:", self.location_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(self.lists.get('statuses', []))
        if self.item_to_edit:
            idx = self.status_combo.findText(self.item_to_edit.get('status', ''))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        form.addRow("Estado Funcional:", self.status_combo)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas...")
        self.notes_input.setMaximumHeight(80)
        if self.item_to_edit: self.notes_input.setText(self.item_to_edit.get('notes', ''))
        form.addRow("Notas:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Periférico")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Periférico")
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
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"periph_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'platform': self.platform_combo.currentText(),
            'brand': self.brand_input.text().strip(),
            'storage_location': self.location_input.text().strip(),
            'status': self.status_combo.currentText(),
            'notes': self.notes_input.toPlainText().strip(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else []
        }
        self.accept()

class ModificationDialog(QDialog):
    """Diálogo para crear o editar una modificación."""
    def __init__(self, item_to_edit: dict = None, lists: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lists = lists or {}
        self.item_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Modificación / Componente" if item_to_edit else "Nueva Modificación / Componente")
        self.setMinimumWidth(440)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Placa UAV Video, Sophia 2...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Nombre de la Mod:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(self.lists.get('modification_types', []))
        if self.item_to_edit:
            idx = self.type_combo.findText(self.item_to_edit.get('type', ''))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo:", self.type_combo)
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(self.lists.get('computer_types', []))
        if self.item_to_edit:
            idx = self.platform_combo.findText(self.item_to_edit.get('platform', ''))
            if idx >= 0: self.platform_combo.setCurrentIndex(idx)
        form.addRow("Para Plataforma:", self.platform_combo)

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Ej: Cajón Mods...")
        if self.item_to_edit: self.location_input.setText(self.item_to_edit.get('storage_location', ''))
        form.addRow("Lugar de Almacenado:", self.location_input)
        
        self.stock_spin = QSpinBox()
        self.stock_spin.setRange(0, 999999)
        if self.item_to_edit: self.stock_spin.setValue(self.item_to_edit.get('stock_quantity', 0))
        form.addRow("Cantidad en Stock:", self.stock_spin)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas de instalación, compatibilidad...")
        self.notes_input.setMaximumHeight(80)
        if self.item_to_edit: self.notes_input.setText(self.item_to_edit.get('notes', ''))
        form.addRow("Notas:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar Modificación")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Modificación")
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
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"mod_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'platform': self.platform_combo.currentText(),
            'storage_location': self.location_input.text().strip(),
            'stock_quantity': self.stock_spin.value(),
            'notes': self.notes_input.toPlainText().strip(),
            'history': self.item_to_edit.get('history', []) if self.item_to_edit else []
        }
        self.accept()

class RetroSettingsDialog(QDialog):
    """Diálogo de configuración de Retro con soporte para edición de listas."""
    def __init__(self, lists: dict = None, plugin_data: dict = None, parent=None):
        super().__init__(parent)
        self.lists = lists or {}
        self.plugin_data = plugin_data or {}
        self.setWindowTitle("Configuración Retro")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.list_map = {
            "Equipos: Tipo/Arquitectura": "computer_types",
            "Condiciones Estéticas": "conditions",
            "Estados Funcionales": "statuses",
            "Medios: Tipos": "media_types",
            "Periféricos: Tipos": "peripheral_types",
            "Modificaciones: Tipos": "modification_types"
        }
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.tabs = QTabWidget()
        
        tab_info = QWidget()
        info_layout = QVBoxLayout(tab_info)
        info_layout.setSpacing(14)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_logo = QLabel("<h2>🕹️ Inventario Retro</h2>")
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(lbl_logo)
        
        lbl_info = QLabel(
            "<b>Gestor de Computadoras Retro VitoOrganizer</b><br><br>"
            "Este módulo te permite gestionar tu colección:<br>"
            "• Equipos y computadoras retro.<br>"
            "• Medios (cartuchos, disquetes, casetes).<br>"
            "• Periféricos (clásicos y modernos).<br>"
            "• Modificaciones, repuestos y desarrollos.<br><br>"
            "Usa la pestaña <b>Listas</b> para personalizar las opciones."
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

        # Mostrar/Ocultar nombre de archivo
        self.chk_show_filename = QCheckBox("Mostrar nombre de archivo en la lista (ROMs/Biblioteca)")
        self.chk_show_filename.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        self.chk_show_filename.setChecked(self.plugin_data.get('show_filename', True))
        self.chk_show_filename.stateChanged.connect(self._on_show_filename_changed)
        info_layout.addWidget(self.chk_show_filename)
        
        info_layout.addStretch()
        
        self.tabs.addTab(tab_info, "General")

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

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

        self._on_list_changed()

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

    def _on_sort_changed(self):
        sort_map_rev = {0: 'alpha_asc', 1: 'alpha_desc', 2: 'date_asc', 3: 'date_desc'}
        self.plugin_data['sort_order'] = sort_map_rev.get(self.sort_combo.currentIndex(), 'alpha_asc')

    def _on_show_filename_changed(self, state):
        self.plugin_data['show_filename'] = (state == 2)


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

            self.lists[list_key][curr_row] = new_val
            
            # Simple reference update
            if list_key == 'computer_types':
                for item in self.plugin_data.get('computers', []):
                    if item.get('type') == old_val: item['type'] = new_val
                for item in self.plugin_data.get('media', []):
                    if item.get('platform') == old_val: item['platform'] = new_val
                for item in self.plugin_data.get('peripherals', []):
                    if item.get('platform') == old_val: item['platform'] = new_val
                for item in self.plugin_data.get('modifications', []):
                    if item.get('platform') == old_val: item['platform'] = new_val

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
        self.lists[list_key].pop(curr_row)
        self._on_list_changed()


class RetroDocumentDialog(QDialog):
    """Diálogo para agregar o editar un documento/imagen en la Biblioteca Retro."""
    def __init__(self, item_to_edit: dict = None, retro_data: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.retro_data = retro_data or {}
        self.item_data = None
        self.selected_file_path = None
        self.is_delete = False
        self.checkboxes = []

        self.setWindowTitle("Editar Documento / Imagen Retro" if item_to_edit else "Subir Documento / Imagen a Biblioteca Retro")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Manual de Servicio Atari 800XL, Diagrama SIO2SD...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Título / Nombre:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Imágenes",
            "Manuales",
            "Datasheets",
            "Diagramas y Esquemas",
            "ROMs y Archivos",
            "Otros Documentos"
        ])
        if self.item_to_edit:
            edit_t = self.item_to_edit.get('type', '')
            idx = self.type_combo.findText(edit_t)
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Archivo:", self.type_combo)

        # Seleccionar archivo físico
        file_layout = QHBoxLayout()
        self.lbl_file_path = QLineEdit()
        self.lbl_file_path.setReadOnly(True)
        self.lbl_file_path.setPlaceholderText("Selecciona un archivo del equipo...")
        if self.item_to_edit:
            self.lbl_file_path.setText(self.item_to_edit.get('filename', ''))

        btn_browse = QPushButton("Examinar...")
        btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(self.lbl_file_path, 1)
        file_layout.addWidget(btn_browse)
        form.addRow("Archivo Físico:", file_layout)

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Equipos y Computadoras",
            "Medios (Cartuchos/Discos)",
            "Periféricos y Expansiones",
            "Modificaciones y Repuestos",
            "Proyectos y Restauraciones"
        ])
        if self.item_to_edit:
            cat_map = {'computers': 0, 'media': 1, 'peripherals': 2, 'modifications': 3, 'projects': 4}
            c_idx = cat_map.get(self.item_to_edit.get('target_category', 'computers'), 0)
            self.category_combo.setCurrentIndex(c_idx)
        self.category_combo.currentIndexChanged.connect(self._populate_elements)
        form.addRow("Categoría Destino:", self.category_combo)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripción o notas del archivo retro...")
        self.desc_input.setMaximumHeight(65)
        if self.item_to_edit: self.desc_input.setText(self.item_to_edit.get('description', ''))
        form.addRow("Descripción:", self.desc_input)

        layout.addLayout(form)

        # Lista de Elementos asignables con Checkboxes
        lbl_assign = QLabel("<b>Asignar a Elementos (Marcar casillas):</b>")
        lbl_assign.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_assign)

        scroll_elements = QScrollArea()
        scroll_elements.setWidgetResizable(True)
        scroll_elements.setMaximumHeight(160)
        scroll_elements.setStyleSheet("QScrollArea { border: 1px solid #2d314e; background-color: #1e1e2e; border-radius: 4px; } QScrollArea QWidget { background-color: transparent; }")

        self.elements_container = QWidget()
        self.elements_layout = QVBoxLayout(self.elements_container)
        self.elements_layout.setContentsMargins(8, 8, 8, 8)
        self.elements_layout.setSpacing(4)
        scroll_elements.setWidget(self.elements_container)
        layout.addWidget(scroll_elements)

        self._populate_elements()

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar de Biblioteca")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Documento")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo para Biblioteca Retro", "", 
            "Todos los Archivos (*.*);;Imágenes (*.png *.jpg *.jpeg *.gif *.webp *.avif *.bmp);;Documentos PDF (*.pdf);;Archivos ROM/Binarios (*.rom *.bin *.atr *.xex *.cas *.d64)"
        )
        if file_path:
            self.selected_file_path = file_path
            self.lbl_file_path.setText(os.path.basename(file_path))
            if not self.name_input.text():
                self.name_input.setText(os.path.splitext(os.path.basename(file_path))[0])

    def _populate_elements(self):
        while self.elements_layout.count():
            child = self.elements_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        self.checkboxes.clear()
        
        cat_index = self.category_combo.currentIndex()
        cat_keys = ['computers', 'media', 'peripherals', 'modifications', 'projects']
        active_key = cat_keys[cat_index] if cat_index < len(cat_keys) else 'computers'
        
        items_list = self.retro_data.get(active_key, [])
        assigned_ids = self.item_to_edit.get('assigned_element_ids', []) if self.item_to_edit else []

        if not items_list:
            lbl_none = QLabel("No hay elementos registrados en esta categoría.")
            lbl_none.setStyleSheet("color: #89b4fa; font-style: italic;")
            self.elements_layout.addWidget(lbl_none)
        else:
            for item in items_list:
                item_id = item.get('id') or item.get('name')
                detail_str = item.get('brand', item.get('type', item.get('category', 'Retro')))
                chk = QCheckBox(f"{item.get('name')} ({detail_str})")
                chk.setStyleSheet("color: #cdd6f4; font-weight: bold;")
                if item_id in assigned_ids or item.get('name') in assigned_ids:
                    chk.setChecked(True)
                self.checkboxes.append((item_id, chk))
                self.elements_layout.addWidget(chk)
        
        self.elements_layout.addStretch()

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}' de la Biblioteca Retro?"):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        if not self.item_to_edit and not self.selected_file_path:
            QMessageBox.warning(self, "Archivo requerido", "Por favor selecciona un archivo físico del equipo.")
            return

        cat_keys = ['computers', 'media', 'peripherals', 'modifications', 'projects']
        target_category = cat_keys[self.category_combo.currentIndex()] if self.category_combo.currentIndex() < len(cat_keys) else 'computers'

        assigned_element_ids = [item_id for item_id, chk in self.checkboxes if chk.isChecked()]

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"doc_retro_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'target_category': target_category,
            'description': self.desc_input.toPlainText().strip(),
            'assigned_element_ids': assigned_element_ids,
            'filename': self.item_to_edit.get('filename', '') if self.item_to_edit else '',
            'relative_path': self.item_to_edit.get('relative_path', '') if self.item_to_edit else ''
        }
        self.accept()


class RetroRomDialog(QDialog):
    """Diálogo para agregar o editar una ROM / Imagen de Disco / Casete / Binario en Retro."""
    def __init__(self, item_to_edit: dict = None, retro_data: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.retro_data = retro_data or {}
        self.item_data = None
        self.selected_rom_path = None
        self.is_delete = False

        self.setWindowTitle("Editar ROM / Dump" if item_to_edit else "Agregar ROM / Imagen de Disco / Casete")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Montezuma's Revenge, River Raid, OS/A+ Atari 800...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Título / Software:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Imagen de Cartucho (ROM / BIN)",
            "Imagen de Disquete (ATR / D64 / ADF / IMG)",
            "Volcado de Casete (CAS / TAP)",
            "Ejecutable / Binario (XEX / COM)",
            "Imagen ISO / CD-ROM",
            "Otro"
        ])
        if self.item_to_edit:
            edit_t = self.item_to_edit.get('type', '')
            idx = self.type_combo.findText(edit_t)
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Volcado:", self.type_combo)

        self.platform_combo = QComboBox()
        platforms = self.retro_data.get('lists', {}).get('computer_types', [
            "Atari 8-bit", "Atari 16-bit", "Commodore 64", "Commodore Amiga",
            "ZX Spectrum", "MSX", "Amstrad CPC", "Apple II", "PC / MS-DOS", "Otro"
        ])
        self.platform_combo.addItems(platforms)
        if self.item_to_edit:
            edit_p = self.item_to_edit.get('platform', '')
            idx_p = self.platform_combo.findText(edit_p)
            if idx_p >= 0: self.platform_combo.setCurrentIndex(idx_p)
        form.addRow("Plataforma:", self.platform_combo)

        # Combo para asignar a un Medio Físico
        self.media_combo = QComboBox()
        self.media_combo.addItem("Ninguno / Software Digital", None)
        media_list = self.retro_data.get('media', [])
        for m in media_list:
            m_id = m.get('id') or m.get('name')
            self.media_combo.addItem(f"{m.get('name')} ({m.get('platform')})", m_id)

        if self.item_to_edit:
            curr_m_id = self.item_to_edit.get('assigned_media_id')
            if curr_m_id:
                for i in range(1, self.media_combo.count()):
                    if self.media_combo.itemData(i) == curr_m_id:
                        self.media_combo.setCurrentIndex(i)
                        break
        form.addRow("Asignar a Medio Físico:", self.media_combo)

        # Combo para asignar imagen desde la Biblioteca Retro
        self.image_combo = QComboBox()
        self.image_combo.addItem("Sin imagen / Por defecto", None)
        library_docs = self.retro_data.get('library', [])
        for doc in library_docs:
            d_type = doc.get('type', '')
            rel_p = doc.get('relative_path', '')
            if d_type == 'Imágenes' or rel_p.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.avif', '.gif')):
                self.image_combo.addItem(f"🖼️ {doc.get('name')} ({doc.get('filename')})", doc.get('relative_path'))

        if self.item_to_edit:
            curr_img_p = self.item_to_edit.get('image_relative_path')
            if curr_img_p:
                for i in range(1, self.image_combo.count()):
                    if self.image_combo.itemData(i) == curr_img_p:
                        self.image_combo.setCurrentIndex(i)
                        break
        form.addRow("Imagen de Carátula (Biblioteca):", self.image_combo)

        # Archivo físico de ROM / Dump
        file_layout = QHBoxLayout()
        self.lbl_file_path = QLineEdit()
        self.lbl_file_path.setReadOnly(True)
        self.lbl_file_path.setPlaceholderText("Selecciona archivo de ROM/Dump (.atr, .d64, .rom, .xex, .cas)...")
        if self.item_to_edit:
            self.lbl_file_path.setText(self.item_to_edit.get('filename', ''))

        btn_browse = QPushButton("Examinar...")
        btn_browse.clicked.connect(self._browse_rom_file)
        file_layout.addWidget(self.lbl_file_path, 1)
        file_layout.addWidget(btn_browse)
        form.addRow("Archivo ROM / Dump:", file_layout)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas, desarrollador, año de publicación, notas de emulación...")
        self.notes_input.setMaximumHeight(65)
        if self.item_to_edit: self.notes_input.setText(self.item_to_edit.get('notes', ''))
        form.addRow("Notas / Descripción:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar ROM")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar ROM")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _browse_rom_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo de ROM o Imagen de Disco", "", 
            "Todos los Archivos (*.*);;Imágenes de Disquete (*.atr *.d64 *.adf *.img);;Cartuchos y Binarios (*.rom *.bin *.xex *.com);;Casetes (*.cas *.tap);;Imágenes ISO (*.iso)"
        )
        if file_path:
            self.selected_rom_path = file_path
            self.lbl_file_path.setText(os.path.basename(file_path))
            if not self.name_input.text():
                self.name_input.setText(os.path.splitext(os.path.basename(file_path))[0])

    def _delete(self):
        if ask_spanish_confirmation(self, "Confirmar Eliminación", f"¿Estás seguro de que deseas eliminar '{self.item_to_edit.get('name')}' de la colección de ROMs?"):
            self.is_delete = True
            self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        if not self.item_to_edit and not self.selected_rom_path:
            QMessageBox.warning(self, "Archivo requerido", "Por favor selecciona un archivo físico de ROM / Dump.")
            return

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"rom_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'platform': self.platform_combo.currentText(),
            'assigned_media_id': self.media_combo.currentData(),
            'image_relative_path': self.image_combo.currentData(),
            'notes': self.notes_input.toPlainText().strip(),
            'filename': self.item_to_edit.get('filename', '') if self.item_to_edit else '',
            'relative_path': self.item_to_edit.get('relative_path', '') if self.item_to_edit else ''
        }
        self.accept()



