# =============================================================================
# Vito Organizer v2.2 - Settings Dialog
# Diálogo de configuración con pestañas
# =============================================================================

import os
import json
import urllib.request
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QComboBox, QCheckBox, QPushButton, QColorDialog,
    QSpinBox, QDoubleSpinBox, QSlider, QTextEdit, QRadioButton, QGroupBox, QFormLayout, QDialogButtonBox,
    QFrame, QLineEdit, QFileDialog, QListWidget, QListWidgetItem, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)

from config.settings import Settings, AppearanceSettings
from graphics.page_styles import PageStyles
from graphics.ring_binder import RingBinder


class PagePreview(QWidget):
    """Widget de vista previa de la apariencia de la página."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 200)
        self.setMaximumHeight(250)
        self._page_style = 'lined'
        self._page_color = '#FFFDD0'
        self._binding_type = 'rings'
        self._line_color = '#B0C4DE'
        self._show_margin = True
        self._line_spacing = 24

    def update_preview(self, page_style: str, page_color: str,
                       binding_type: str, line_color: str,
                       show_margin: bool, line_spacing: int):
        """Actualiza los parámetros de la vista previa."""
        self._page_style = page_style
        self._page_color = page_color
        self._binding_type = binding_type
        self._line_color = line_color
        self._show_margin = show_margin
        self._line_spacing = line_spacing
        self.update()

    def paintEvent(self, event):
        """Dibuja la vista previa."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect())

        # Fondo
        painter.fillRect(rect, QColor('#1e1e2e'))

        # Página izquierda
        page_margin = 10
        binder_w = RingBinder.get_binder_width(self._binding_type)
        page_w = (rect.width() - binder_w - page_margin * 2) / 2
        page_h = rect.height() - page_margin * 2

        left_rect = QRectF(page_margin, page_margin, page_w, page_h)
        right_rect = QRectF(page_margin + page_w + binder_w, page_margin, page_w, page_h)
        binder_rect = QRectF(page_margin + page_w, page_margin, binder_w, page_h)

        # Dibujar páginas
        for page_rect in [left_rect, right_rect]:
            painter.setPen(QPen(QColor('#C0C0C0'), 0.5))
            painter.setBrush(QBrush(QColor(self._page_color)))
            painter.drawRoundedRect(page_rect, 3, 3)

            style_kwargs = {}
            if self._page_style == 'lined':
                style_kwargs = {
                    'line_color': self._line_color,
                    'margin_color': '#E88888',
                    'show_margin': self._show_margin and page_rect == left_rect,
                    'line_spacing': self._line_spacing,
                    'header_height': 25,
                }
            elif self._page_style == 'grid':
                style_kwargs = {
                    'line_color': self._line_color,
                    'line_spacing': self._line_spacing,
                    'header_height': 25,
                }
            elif self._page_style == 'dots':
                style_kwargs = {
                    'dot_color': self._line_color,
                    'dot_spacing': self._line_spacing,
                    'header_height': 25,
                }

            PageStyles.draw(self._page_style, painter, page_rect, **style_kwargs)

        # Dibujar encuadernación
        RingBinder.draw(self._binding_type, painter, binder_rect)

        painter.end()


class SettingsDialog(QDialog):
    """Diálogo de configuración con pestañas de Apariencia y General."""

    settings_changed = pyqtSignal(object)  # Emite Settings actualizado

    def __init__(self, settings: Settings, plugin_manager=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración")
        self.setMinimumSize(550, 520)
        self._settings = settings
        self._plugin_manager = plugin_manager
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        """Configura la interfaz."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_appearance_tab(), "Apariencia")
        self._tabs.addTab(self._create_general_tab(), "General")
        self._tabs.addTab(self._create_sections_tab(), "📋 Secciones y Pestañas")
        self._tabs.addTab(self._create_backup_tab(), "Respaldos")
        self._tabs.addTab(self._create_ai_tab(), "🤖 IA (Inteligencia Artificial)")
        layout.addWidget(self._tabs)

        # Botones
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._on_apply)
        layout.addWidget(buttons)

    def _create_appearance_tab(self) -> QWidget:
        """Crea la pestaña de apariencia."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # --- Estilo de página ---
        style_group = QGroupBox("Estilo de Página")
        style_layout = QFormLayout(style_group)

        self._page_style_combo = QComboBox()
        self._page_style_combo.addItems([
            "Líneas", "Cuadriculada", "Lisa", "Puntos"
        ])
        self._page_style_combo.currentIndexChanged.connect(self._update_preview)
        style_layout.addRow("Tipo:", self._page_style_combo)

        # Color de página
        self._page_color_btn = QPushButton()
        self._page_color_btn.setFixedSize(80, 30)
        self._page_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._page_color_btn.clicked.connect(self._pick_page_color)
        self._page_color = '#FFFDD0'
        style_layout.addRow("Color de página:", self._page_color_btn)

        # Color de líneas
        self._line_color_btn = QPushButton()
        self._line_color_btn.setFixedSize(80, 30)
        self._line_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._line_color_btn.clicked.connect(self._pick_line_color)
        self._line_color = '#B0C4DE'
        style_layout.addRow("Color de líneas:", self._line_color_btn)

        # Color de barra lateral
        self._sidebar_color_btn = QPushButton()
        self._sidebar_color_btn.setFixedSize(80, 30)
        self._sidebar_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._sidebar_color_btn.clicked.connect(self._pick_sidebar_color)
        self._sidebar_color = '#1b4332'
        style_layout.addRow("Color barra lateral:", self._sidebar_color_btn)

        # Margen
        self._show_margin_check = QCheckBox("Mostrar línea de margen")
        self._show_margin_check.stateChanged.connect(self._update_preview)
        style_layout.addRow(self._show_margin_check)

        # Espaciado
        self._line_spacing_spin = QSpinBox()
        self._line_spacing_spin.setRange(12, 40)
        self._line_spacing_spin.setSuffix(" px")
        self._line_spacing_spin.valueChanged.connect(self._update_preview)
        style_layout.addRow("Espaciado:", self._line_spacing_spin)

        # Diseño de papelera
        self._trash_style_combo = QComboBox()
        self._trash_style_combo.addItems([
            "Reciclaje Clásica (Blanca con Flechas Azules)",
            "Cesta Metálica Negra (Malla)",
            "Contenedor Verde de Reciclaje",
            "Balde Morado Moderno",
            "Cesta Rejilla Cuadrada Negra",
            "Lote Metálico Plateado (con Disquete y Lápiz)",
            "Papelera Plástica Cuadrada Blanca",
            "Bote Azul con Flechas Circulares"
        ])
        style_layout.addRow("Diseño papelera:", self._trash_style_combo)

        layout.addWidget(style_group)

        # --- Encuadernación ---
        binding_group = QGroupBox("Encuadernación")
        binding_layout = QFormLayout(binding_group)

        self._binding_combo = QComboBox()
        self._binding_combo.addItems([
            "Anillas", "Espiral", "Clip", "Sin encuadernación"
        ])
        self._binding_combo.currentIndexChanged.connect(self._update_preview)
        binding_layout.addRow("Tipo:", self._binding_combo)

        layout.addWidget(binding_group)

        # --- Vista previa ---
        preview_group = QGroupBox("Vista Previa")
        preview_layout = QVBoxLayout(preview_group)
        self._preview = PagePreview()
        preview_layout.addWidget(self._preview)
        layout.addWidget(preview_group)

        return tab

    def _create_general_tab(self) -> QWidget:
        """Crea la pestaña general."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # Directorio por defecto
        dir_group = QGroupBox("Directorio de Agendas")
        dir_layout = QHBoxLayout(dir_group)
        self._default_dir_edit = QLineEdit()
        self._default_dir_edit.setPlaceholderText("Directorio por defecto...")
        dir_browse_btn = QPushButton("Examinar")
        dir_browse_btn.clicked.connect(self._browse_default_dir)
        dir_layout.addWidget(self._default_dir_edit, 1)
        dir_layout.addWidget(dir_browse_btn)
        layout.addWidget(dir_group)

        # Configuración de Moneda / Unidad de Costo
        currency_group = QGroupBox("Configuración de Moneda y Costos")
        currency_layout = QFormLayout(currency_group)
        self._currency_combo = QComboBox()
        self._currency_combo.addItems([
            "CLP ($ Peso Chileno)",
            "USD ($ Dólar estadounidense)",
            "EUR (€ Euro)"
        ])
        currency_layout.addRow("Moneda Predeterminada:", self._currency_combo)
        layout.addWidget(currency_group)

        # Logotipo personalizado
        logo_group = QGroupBox("Logotipo de la Aplicación")
        logo_layout = QHBoxLayout(logo_group)
        self._logo_path_edit = QLineEdit()
        self._logo_path_edit.setPlaceholderText("Ruta del logotipo (.png, .jpg, .svg)...")
        self._logo_path_edit.setReadOnly(True)
        self._logo_path_edit.setStyleSheet("QLineEdit { background: #1e1e2e; color: #f5f5f5; border: 1px solid #45475a; border-radius: 4px; padding: 4px; }")
        
        btn_browse_logo = QPushButton("Examinar")
        btn_browse_logo.setStyleSheet("QPushButton { font-weight: bold; background-color: #313244; color: #ffffff; border: 1px solid #45475a; padding: 5px 10px; border-radius: 4px; } QPushButton:hover { background-color: #45475a; }")
        btn_browse_logo.clicked.connect(self._browse_logo)
        
        btn_clear_logo = QPushButton("Limpiar")
        btn_clear_logo.setStyleSheet("QPushButton { font-weight: bold; background-color: #313244; color: #ffffff; border: 1px solid #45475a; padding: 5px 10px; border-radius: 4px; } QPushButton:hover { background-color: #45475a; }")
        btn_clear_logo.clicked.connect(self._clear_logo)

        logo_layout.addWidget(self._logo_path_edit, 1)
        logo_layout.addWidget(btn_browse_logo)
        logo_layout.addWidget(btn_clear_logo)
        layout.addWidget(logo_group)

        layout.addStretch()
        return tab

    def _create_sections_tab(self) -> QWidget:
        """Crea la pestaña de gestión de secciones y pestañas (visibilidad, nombres y orden)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        group = QGroupBox("Visibilidad, Nombres y Orden de Secciones")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(10)

        lbl_desc = QLabel(
            "Marca las casillas en la columna 'Visible' para activar u ocultar secciones en la agenda.\n"
            "Puedes editar directamente la columna 'Nombre en Pestaña' para personalizar el título mostrado en la solapa."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #a6adc8; font-size: 12px;")
        g_layout.addWidget(lbl_desc)

        main_box = QHBoxLayout()

        # Tabla de Secciones
        self._sections_table = QTableWidget()
        self._sections_table.setColumnCount(4)
        self._sections_table.setHorizontalHeaderLabels(["Visible", "Ícono", "Nombre en Pestaña", "Sección Original"])
        self._sections_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._sections_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._sections_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._sections_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._sections_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._sections_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._sections_table.setStyleSheet("""
            QTableWidget { background-color: #1e1e2e; color: #f5f5f5; border: 1px solid #45475a; border-radius: 6px; gridline-color: #313244; }
            QHeaderView::section { background-color: #313244; color: #cdd6f4; font-weight: bold; padding: 6px; border: none; }
            QTableWidget::item { padding: 4px; }
            QTableWidget::item:selected { background-color: #45475a; color: #f9e2af; }
        """)

        main_box.addWidget(self._sections_table, 1)

        # Botones de orden y acciones
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')

        btn_box = QVBoxLayout()
        btn_box.setSpacing(8)

        self.btn_section_up = QPushButton(" Subir")
        self.btn_section_up.setIcon(QIcon(os.path.join(icons_dir, 'up.svg')))
        self.btn_section_down = QPushButton(" Bajar")
        self.btn_section_down.setIcon(QIcon(os.path.join(icons_dir, 'down.svg')))
        
        btn_reset_names = QPushButton(" Restablecer")
        btn_reset_names.setIcon(QIcon(os.path.join(icons_dir, 'sync.svg')))
        btn_reset_names.setToolTip("Restablecer nombres originales de las pestañas")

        btn_select_all = QPushButton(" Mostrar Todas")
        btn_select_all.setIcon(QIcon(os.path.join(icons_dir, 'check.svg')))
        btn_select_all.setToolTip("Marcar todas las secciones como visibles")

        btn_style = """
            QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 5px; background-color: #313244; color: #ffffff; border: 1px solid #45475a; font-size: 11px; }
            QPushButton:hover { background-color: #45475a; color: #f9e2af; }
        """
        self.btn_section_up.setStyleSheet(btn_style)
        self.btn_section_down.setStyleSheet(btn_style)
        btn_reset_names.setStyleSheet(btn_style)
        btn_select_all.setStyleSheet(btn_style)

        self.btn_section_up.clicked.connect(self._move_table_row_up)
        self.btn_section_down.clicked.connect(self._move_table_row_down)
        btn_reset_names.clicked.connect(self._reset_section_names)
        btn_select_all.clicked.connect(self._select_all_sections)

        btn_box.addWidget(self.btn_section_up)
        btn_box.addWidget(self.btn_section_down)
        btn_box.addWidget(btn_reset_names)
        btn_box.addWidget(btn_select_all)
        btn_box.addStretch()

        main_box.addLayout(btn_box)
        g_layout.addLayout(main_box)
        layout.addWidget(group)

        return tab

    def _move_table_row_up(self):
        row = self._sections_table.currentRow()
        if row > 0:
            self._swap_table_rows(row, row - 1)
            self._sections_table.setCurrentCell(row - 1, 3)

    def _move_table_row_down(self):
        row = self._sections_table.currentRow()
        if row >= 0 and row < self._sections_table.rowCount() - 1:
            self._swap_table_rows(row, row + 1)
            self._sections_table.setCurrentCell(row + 1, 3)

    def _swap_table_rows(self, r1: int, r2: int):
        w1 = self._sections_table.cellWidget(r1, 0)
        w2 = self._sections_table.cellWidget(r2, 0)
        chk1_val = w1.findChild(QCheckBox).isChecked() if w1 else True
        chk2_val = w2.findChild(QCheckBox).isChecked() if w2 else True

        n1 = self._sections_table.cellWidget(r1, 2)
        n2 = self._sections_table.cellWidget(r2, 2)
        name1_txt = n1.text() if n1 else ""
        name2_txt = n2.text() if n2 else ""

        item1 = self._sections_table.takeItem(r1, 3)
        item2 = self._sections_table.takeItem(r2, 3)

        lbl1 = self._sections_table.cellWidget(r1, 1).findChild(QLabel) if self._sections_table.cellWidget(r1, 1) else None
        lbl2 = self._sections_table.cellWidget(r2, 1).findChild(QLabel) if self._sections_table.cellWidget(r2, 1) else None
        pm1 = lbl1.pixmap() if lbl1 else None
        pm2 = lbl2.pixmap() if lbl2 else None

        if w1: w1.findChild(QCheckBox).setChecked(chk2_val)
        if n1: n1.setText(name2_txt)
        if item2: self._sections_table.setItem(r1, 3, item2)
        if pm2 and lbl1: lbl1.setPixmap(pm2)

        if w2: w2.findChild(QCheckBox).setChecked(chk1_val)
        if n2: n2.setText(name1_txt)
        if item1: self._sections_table.setItem(r2, 3, item1)
        if pm1 and lbl2: lbl2.setPixmap(pm1)

    def _reset_section_names(self):
        for row in range(self._sections_table.rowCount()):
            orig_item = self._sections_table.item(row, 3)
            if orig_item:
                orig_name = orig_item.data(Qt.ItemDataRole.UserRole + 1)
                name_widget = self._sections_table.cellWidget(row, 2)
                if isinstance(name_widget, QLineEdit):
                    name_widget.setText(orig_name)

    def _select_all_sections(self):
        for row in range(self._sections_table.rowCount()):
            chk_container = self._sections_table.cellWidget(row, 0)
            if chk_container:
                chk = chk_container.findChild(QCheckBox)
                if chk:
                    chk.setChecked(True)

    def _load_values(self):
        """Carga los valores actuales de la configuración."""
        app = self._settings.appearance

        # Estilo de página
        style_map = {'lined': 0, 'grid': 1, 'plain': 2, 'dots': 3}
        self._page_style_combo.setCurrentIndex(style_map.get(app.page_style, 0))

        # Colores
        self._page_color = app.page_color
        self._update_color_button(self._page_color_btn, self._page_color)
        self._line_color = app.line_color
        self._update_color_button(self._line_color_btn, self._line_color)
        self._sidebar_color = getattr(app, 'sidebar_color', '#1b4332')
        self._update_color_button(self._sidebar_color_btn, self._sidebar_color)

        # Margen
        self._show_margin_check.setChecked(app.show_margin)

        # Espaciado
        self._line_spacing_spin.setValue(app.line_spacing)

        # Diseño de Papelera
        trash_map = {'classic_recycling': 0, 'metallic_mesh': 1, 'green_dumpster': 2, 'purple_flat': 3, 'black_grid': 4, 'silver_metal_can': 5, 'white_plastic_bin': 6, 'blue_plastic_bin': 7}
        self._trash_style_combo.setCurrentIndex(trash_map.get(getattr(app, 'trash_style', 'classic_recycling'), 0))

        # Encuadernación
        binding_map = {'rings': 0, 'spiral': 1, 'clip': 2, 'none': 3}
        self._binding_combo.setCurrentIndex(binding_map.get(app.binding_type, 0))

        # General
        self._default_dir_edit.setText(self._settings.general.default_agenda_dir)

        # Moneda
        currency_val = getattr(self._settings.general, 'cost_currency', 'CLP')
        currency_map = {'CLP': 0, 'USD': 1, 'EUR': 2}
        self._currency_combo.setCurrentIndex(currency_map.get(currency_val, 0))

        # Logotipo
        self._logo_path_edit.setText(getattr(self._settings.general, 'logo_path', ''))

        # Población de Tabla de Secciones y Pestañas
        self._sections_table.setRowCount(0)
        if self._plugin_manager:
            if self._settings.general.tab_order:
                self._plugin_manager.sort_plugins(self._settings.general.tab_order)
            plugins = self._plugin_manager.get_plugins()
            hidden_ids = set(getattr(self._settings.general, 'hidden_sections', []))
            custom_names = getattr(self._settings.general, 'custom_tab_names', {})
            icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')

            for row, p in enumerate(plugins):
                self._sections_table.insertRow(row)

                # Col 0: Visible (Checkbox)
                chk = QCheckBox()
                chk.setChecked(p.get_id() not in hidden_ids)
                chk_container = QWidget()
                chk_layout = QHBoxLayout(chk_container)
                chk_layout.addWidget(chk)
                chk_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                chk_layout.setContentsMargins(0, 0, 0, 0)
                self._sections_table.setCellWidget(row, 0, chk_container)

                # Col 1: Ícono
                icon_lbl = QLabel()
                if hasattr(p, 'get_icon') and p.get_icon():
                    icon_path = os.path.join(icons_dir, p.get_icon())
                    if os.path.exists(icon_path):
                        icon_lbl.setPixmap(QIcon(icon_path).pixmap(20, 20))
                icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._sections_table.setCellWidget(row, 1, icon_lbl)

                # Col 2: Nombre en Pestaña (QLineEdit)
                name_edit = QLineEdit()
                curr_name = custom_names.get(p.get_id(), p.get_name())
                name_edit.setText(curr_name)
                name_edit.setStyleSheet("QLineEdit { background: #181825; color: #f9e2af; border: 1px solid #45475a; border-radius: 4px; padding: 4px 6px; font-weight: bold; }")
                self._sections_table.setCellWidget(row, 2, name_edit)

                # Col 3: Sección Original
                orig_item = QTableWidgetItem(f"{p.get_name()} ({p.get_id()})")
                orig_item.setFlags(orig_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                orig_item.setData(Qt.ItemDataRole.UserRole, p.get_id())
                orig_item.setData(Qt.ItemDataRole.UserRole + 1, p.get_name())
                self._sections_table.setItem(row, 3, orig_item)

        # Respaldos
        self._backup_dir_edit.setText(self._settings.backup.backup_dir)
        self._backup_name_edit.setText(self._settings.backup.filename_prefix)
        
        fmt_val = self._settings.backup.compression_format.upper()
        fmt_map = {"ZIP": 0, "RAR": 1, "7ZIP": 2, "ARJ": 3}
        self._compression_combo.setCurrentIndex(fmt_map.get(fmt_val, 0))

        self._split_volumes_check.setChecked(self._settings.backup.split_volumes)
        self._volume_size_spin.setValue(self._settings.backup.volume_size)
        self._toggle_volume_inputs(self._settings.backup.split_volumes)

        # Configuración IA
        ai = getattr(self._settings, 'ai', None)
        if ai:
            provider_map = {'lm_studio': 0, 'ollama': 1, 'custom_openai': 2}
            self._ai_provider_combo.setCurrentIndex(provider_map.get(ai.provider, 0))
            self._ai_lm_studio_url.setText(ai.lm_studio_url)
            self._ai_ollama_url.setText(ai.ollama_url)
            self._ai_custom_url.setText(ai.custom_url)
            self._ai_api_key.setText(ai.api_key)
            if ai.selected_model and self._ai_model_combo.findText(ai.selected_model) < 0:
                self._ai_model_combo.addItem(ai.selected_model)
            self._ai_model_combo.setCurrentText(ai.selected_model)
            self._ai_temp_spin.setValue(ai.temperature)
            self._ai_max_tokens_spin.setValue(ai.max_tokens)
            self._ai_system_prompt.setText(ai.system_prompt)
            self._ai_enable_agent.setChecked(ai.enable_agent)

        self._update_preview()

    def _update_color_button(self, button: QPushButton, color: str):
        """Actualiza el estilo de un botón de color."""
        button.setStyleSheet(
            f"QPushButton {{ background-color: {color}; border: 1px solid #45475a; "
            f"border-radius: 4px; }}"
        )

    def _pick_page_color(self):
        """Abre selector de color para la página."""
        color = QColorDialog.getColor(QColor(self._page_color), self,
                                      "Color de página")
        if color.isValid():
            self._page_color = color.name()
            self._update_color_button(self._page_color_btn, self._page_color)
            self._update_preview()

    def _pick_line_color(self):
        """Abre selector de color para las líneas."""
        color = QColorDialog.getColor(QColor(self._line_color), self,
                                      "Color de líneas")
        if color.isValid():
            self._line_color = color.name()
            self._update_color_button(self._line_color_btn, self._line_color)
            self._update_preview()

    def _pick_sidebar_color(self):
        """Abre selector de color para la barra lateral."""
        color = QColorDialog.getColor(QColor(self._sidebar_color), self,
                                      "Color de barra lateral")
        if color.isValid():
            self._sidebar_color = color.name()
            self._update_color_button(self._sidebar_color_btn, self._sidebar_color)
            self._update_preview()

    def _browse_default_dir(self):
        """Abre selector de directorio."""
        path = QFileDialog.getExistingDirectory(
            self, "Directorio por defecto", self._default_dir_edit.text())
        if path:
            self._default_dir_edit.setText(path)

    def _browse_logo(self):
        """Abre selector de imagen para el logotipo."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Logotipo Personalizado", "", 
            "Imágenes (*.png *.jpg *.jpeg *.svg)"
        )
        if path:
            # Obtener la ruta de la agenda activa desde MainWindow
            agenda_path = ""
            if self.parent() and hasattr(self.parent(), 'agenda_path'):
                agenda_path = self.parent().agenda_path

            if agenda_path:
                import shutil
                portada_dir = os.path.join(agenda_path, 'portada')
                os.makedirs(portada_dir, exist_ok=True)
                ext = os.path.splitext(path)[1]
                dest_name = f"custom_logo{ext}"
                dest_path = os.path.join(portada_dir, dest_name)
                try:
                    shutil.copy2(path, dest_path)
                    self._logo_path_edit.setText(dest_path)
                except Exception as e:
                    print(f"[Settings] Error al copiar el logotipo a la carpeta de portada: {e}")
                    self._logo_path_edit.setText(path)
            else:
                self._logo_path_edit.setText(path)

    def _clear_logo(self):
        """Limpia el logotipo seleccionado."""
        self._logo_path_edit.clear()

    def _update_preview(self):
        """Actualiza la vista previa."""
        style_map = {0: 'lined', 1: 'grid', 2: 'plain', 3: 'dots'}
        binding_map = {0: 'rings', 1: 'spiral', 2: 'clip', 3: 'none'}

        self._preview.update_preview(
            page_style=style_map.get(self._page_style_combo.currentIndex(), 'lined'),
            page_color=self._page_color,
            binding_type=binding_map.get(self._binding_combo.currentIndex(), 'rings'),
            line_color=self._line_color,
            show_margin=self._show_margin_check.isChecked(),
            line_spacing=self._line_spacing_spin.value(),
        )



    def _create_backup_tab(self) -> QWidget:
        """Crea la pestaña de respaldos."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # --- GRUPO CREACIÓN DE RESPALDO ---
        backup_group = QGroupBox("Crear Copia de Seguridad (Respaldo)")
        backup_layout = QFormLayout(backup_group)
        backup_layout.setSpacing(8)

        # Destino
        dest_row = QHBoxLayout()
        self._backup_dir_edit = QLineEdit()
        self._backup_dir_edit.setPlaceholderText("Seleccione carpeta de destino...")
        btn_browse_backup = QPushButton("Examinar")
        btn_browse_backup.clicked.connect(self._browse_backup_dir)
        dest_row.addWidget(self._backup_dir_edit, 1)
        dest_row.addWidget(btn_browse_backup)
        backup_layout.addRow("Directorio Destino:", dest_row)

        # Nombre del archivo
        self._backup_name_edit = QLineEdit()
        self._backup_name_edit.setPlaceholderText("Nombre del archivo de respaldo...")
        backup_layout.addRow("Nombre del Archivo:", self._backup_name_edit)

        # Formato de compresión
        self._compression_combo = QComboBox()
        self._compression_combo.addItems(["ZIP", "RAR", "7ZIP", "ARJ"])
        backup_layout.addRow("Formato de Compresión:", self._compression_combo)

        # Volumen check y tamaño
        vol_row = QHBoxLayout()
        self._split_volumes_check = QCheckBox("Dividir en volúmenes (Multivolumen)")
        self._split_volumes_check.toggled.connect(self._toggle_volume_inputs)
        
        self._volume_size_spin = QSpinBox()
        self._volume_size_spin.setRange(1, 4096)
        self._volume_size_spin.setValue(10)
        self._volume_size_spin.setSuffix(" MB")
        self._volume_size_label = QLabel("Tamaño:")
        
        vol_row.addWidget(self._split_volumes_check)
        vol_row.addWidget(self._volume_size_label)
        vol_row.addWidget(self._volume_size_spin)
        backup_layout.addRow("Opciones de Volumen:", vol_row)

        # Botón Crear
        btn_layout = QHBoxLayout()
        self._btn_run_backup = QPushButton("Crear Respaldo Ahora")
        self._btn_run_backup.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #a6e3a1;
                color: #11111b;
                border: 1px solid #45475a;
                padding: 6px 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #94e2d5;
            }
        """)
        self._btn_run_backup.clicked.connect(self._perform_backup)
        btn_layout.addWidget(self._btn_run_backup)
        btn_layout.addStretch()
        backup_layout.addRow("", btn_layout)

        layout.addWidget(backup_group)

        # --- GRUPO RESTAURACIÓN DE RESPALDO ---
        restore_group = QGroupBox("Restaurar Copia de Seguridad (Restauración)")
        restore_layout = QFormLayout(restore_group)
        restore_layout.setSpacing(8)

        # Archivo de respaldo a restaurar
        restore_row = QHBoxLayout()
        self._restore_file_edit = QLineEdit()
        self._restore_file_edit.setPlaceholderText("Seleccione archivo de respaldo (.zip, .rar, .7z, .arj)...")
        btn_browse_restore = QPushButton("Examinar")
        btn_browse_restore.clicked.connect(self._browse_restore_file)
        restore_row.addWidget(self._restore_file_edit, 1)
        restore_row.addWidget(btn_browse_restore)
        restore_layout.addRow("Archivo de Respaldo:", restore_row)

        # Botón Restaurar
        btn_restore_layout = QHBoxLayout()
        self._btn_run_restore = QPushButton("Restaurar Respaldo Ahora")
        self._btn_run_restore.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                background-color: #f38ba8;
                color: #11111b;
                border: 1px solid #45475a;
                padding: 6px 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f9e2af;
            }
        """)
        self._btn_run_restore.clicked.connect(self._perform_restore)
        btn_restore_layout.addWidget(self._btn_run_restore)
        btn_restore_layout.addStretch()
        restore_layout.addRow("", btn_restore_layout)

        layout.addWidget(restore_group)

        layout.addStretch()
        return tab

    def _browse_backup_dir(self):
        """Abre selector de directorio para guardar el respaldo."""
        path = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio de Respaldo", self._backup_dir_edit.text())
        if path:
            self._backup_dir_edit.setText(path)

    def _toggle_volume_inputs(self, checked):
        """Habilita o deshabilita los inputs del tamaño de volumen."""
        self._volume_size_spin.setEnabled(checked)
        self._volume_size_label.setEnabled(checked)

    def _perform_backup(self):
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import shutil

        # 1. Obtener ruta de la agenda activa
        agenda_path = ""
        if self.parent() and hasattr(self.parent(), 'agenda_path'):
            agenda_path = self.parent().agenda_path

        if not agenda_path or not os.path.exists(agenda_path):
            QMessageBox.warning(self, "Error de Respaldo", 
                                "No hay ninguna agenda abierta actualmente. Abra una agenda antes de realizar el respaldo.")
            return

        # 2. Validar destino
        dest_dir = self._backup_dir_edit.text().strip()
        if not dest_dir:
            QMessageBox.warning(self, "Error de Respaldo", 
                                "Por favor, seleccione un directorio de destino para guardar el respaldo.")
            return
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except Exception as e:
                QMessageBox.warning(self, "Error de Respaldo", 
                                    f"No se pudo crear el directorio de destino:\n{e}")
                return

        # 3. Validar nombre del archivo
        filename = self._backup_name_edit.text().strip()
        if not filename:
            filename = "respaldo_agenda"

        fmt = self._compression_combo.currentText().upper()
        split = self._split_volumes_check.isChecked()
        vol_size = self._volume_size_spin.value()

        # Determinar la extensión
        ext_map = {"ZIP": ".zip", "RAR": ".rar", "7ZIP": ".7z", "ARJ": ".arj"}
        ext = ext_map.get(fmt, ".zip")

        dest_file = os.path.join(dest_dir, filename + ext)
        parent_dir = os.path.dirname(agenda_path)
        folder_name = os.path.basename(agenda_path)

        success = False
        error_msg = ""

        try:
            # Caso 1: ZIP nativo sin división
            if fmt == "ZIP" and not split:
                import zipfile
                with zipfile.ZipFile(dest_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(agenda_path):
                        for file in files:
                            abs_path = os.path.join(root, file)
                            rel_path = os.path.relpath(abs_path, parent_dir)
                            zipf.write(abs_path, rel_path)
                success = True

            # Caso 2: ZIP con volúmenes usando 7z
            elif fmt == "ZIP" and split:
                if shutil.which("7z"):
                    cmd = ["7z", "a", f"-v{vol_size}m", dest_file, folder_name]
                    res = subprocess.run(cmd, cwd=parent_dir, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "Se requiere el comando '7z' para dividir archivos ZIP en volúmenes. Instale 'p7zip-full'."

            # Caso 3: 7ZIP
            elif fmt == "7ZIP":
                tool = "7z" if shutil.which("7z") else ("7za" if shutil.which("7za") else None)
                if tool:
                    cmd = [tool, "a"]
                    if split:
                        cmd.append(f"-v{vol_size}m")
                    cmd.extend([dest_file, folder_name])
                    res = subprocess.run(cmd, cwd=parent_dir, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "No se encontró el comando '7z' o '7za' en el sistema. Instale 'p7zip-full'."

            # Caso 4: RAR
            elif fmt == "RAR":
                if shutil.which("rar"):
                    cmd = ["rar", "a"]
                    if split:
                        cmd.append(f"-v{vol_size}m")
                    cmd.extend([dest_file, folder_name])
                    res = subprocess.run(cmd, cwd=parent_dir, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "No se encontró el comando 'rar' en el sistema. Por favor instale el paquete 'rar'."

            # Caso 5: ARJ
            elif fmt == "ARJ":
                if shutil.which("arj"):
                    cmd = ["arj", "a"]
                    if split:
                        cmd.append(f"-v{vol_size * 1024}")
                    cmd.extend([dest_file, folder_name])
                    res = subprocess.run(cmd, cwd=parent_dir, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "No se encontró el comando 'arj' en el sistema. Por favor instale el paquete 'arj'."

        except Exception as e:
            error_msg = str(e)

        if success:
            QMessageBox.information(self, "Respaldo Completado", 
                                    f"El respaldo de la agenda se ha realizado exitosamente en:\n{dest_dir}")
        else:
            QMessageBox.critical(self, "Error de Respaldo", 
                                 f"No se pudo completar el respaldo.\n\nDetalles:\n{error_msg}")

    def _browse_restore_file(self):
        """Abre selector de archivos para elegir el respaldo a restaurar."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Archivo de Respaldo", "", 
            "Archivos de Respaldo (*.zip *.rar *.7z *.arj *.001 *.part1.rar)"
        )
        if path:
            self._restore_file_edit.setText(path)

    def _perform_restore(self):
        from PyQt6.QtWidgets import QMessageBox
        import subprocess
        import shutil

        # 1. Obtener ruta de la agenda activa
        agenda_path = ""
        if self.parent() and hasattr(self.parent(), 'agenda_path'):
            agenda_path = self.parent().agenda_path

        if not agenda_path or not os.path.exists(agenda_path):
            QMessageBox.warning(self, "Error de Restauración", 
                                "No hay ninguna agenda abierta actualmente. Abra una agenda antes de realizar la restauración.")
            return

        # 2. Validar archivo de origen
        backup_file = self._restore_file_edit.text().strip()
        if not backup_file or not os.path.exists(backup_file):
            QMessageBox.warning(self, "Error de Restauración", 
                                "Por favor, seleccione un archivo de respaldo válido.")
            return

        # 3. Confirmar con el usuario
        reply = QMessageBox.question(
            self, "Confirmar Restauración",
            "¡ADVERTENCIA! Esta acción cerrará la agenda actual y reemplazará todos sus archivos con los datos del respaldo.\n\n¿Está seguro de que desea continuar?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        parent_dir = os.path.dirname(agenda_path)
        
        # Determinar el formato real
        real_fmt = "ZIP"
        if ".zip" in backup_file.lower():
            real_fmt = "ZIP"
        elif ".rar" in backup_file.lower():
            real_fmt = "RAR"
        elif ".7z" in backup_file.lower() or ".7zip" in backup_file.lower():
            real_fmt = "7ZIP"
        elif ".arj" in backup_file.lower():
            real_fmt = "ARJ"

        success = False
        error_msg = ""

        try:
            # Caso 1: ZIP nativo (si no es split)
            if real_fmt == "ZIP" and not backup_file.lower().endswith((".001", ".part1.rar")):
                import zipfile
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    zipf.extractall(parent_dir)
                success = True

            # Caso 2: 7ZIP o ZIP split usando 7z
            elif real_fmt == "7ZIP" or (real_fmt == "ZIP" and backup_file.lower().endswith(".001")):
                tool = "7z" if shutil.which("7z") else ("7za" if shutil.which("7za") else None)
                if tool:
                    # 7z extrae automáticamente archivos divididos si apuntas al primer volumen .001
                    cmd = [tool, "x", "-y", f"-o{parent_dir}", backup_file]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "No se encontró el comando '7z' o '7za' en el sistema para extraer el archivo. Por favor instale 'p7zip-full'."

            # Caso 3: RAR usando unrar o 7z
            elif real_fmt == "RAR":
                tool = "unrar" if shutil.which("unrar") else ("rar" if shutil.which("rar") else ("7z" if shutil.which("7z") else None))
                if tool:
                    if "7z" in tool:
                        cmd = [tool, "x", "-y", f"-o{parent_dir}", backup_file]
                    else:
                        cmd = [tool, "x", "-y", backup_file, parent_dir + "/"]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "No se encontró un descompresor compatible con RAR ('unrar', 'rar' o '7z'). Instale uno de ellos."

            # Caso 4: ARJ
            elif real_fmt == "ARJ":
                if shutil.which("arj"):
                    cmd = ["arj", "x", "-y", backup_file, parent_dir + "/"]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    if res.returncode == 0:
                        success = True
                    else:
                        error_msg = res.stderr
                else:
                    error_msg = "No se encontró el comando 'arj' para descomprimir. Por favor instale el paquete 'arj'."

        except Exception as e:
            error_msg = str(e)

        if success:
            # Recargar la agenda en MainWindow
            if self.parent() and hasattr(self.parent(), '_open_agenda'):
                try:
                    self.parent()._open_agenda(agenda_path)
                except Exception as ex:
                    print(f"[Restore] Error al recargar la agenda: {ex}")
            QMessageBox.information(self, "Restauración Completada", 
                                    "La agenda ha sido restaurada con éxito y recargada en la aplicación.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error de Restauración", 
                                 f"No se pudo completar la restauración.\n\nDetalles:\n{error_msg}")

    def _get_current_settings(self) -> Settings:
        """Obtiene la configuración actual del diálogo."""
        style_map = {0: 'lined', 1: 'grid', 2: 'plain', 3: 'dots'}
        binding_map = {0: 'rings', 1: 'spiral', 2: 'clip', 3: 'none'}
        trash_map = {0: 'classic_recycling', 1: 'metallic_mesh', 2: 'green_dumpster', 3: 'purple_flat', 4: 'black_grid', 5: 'silver_metal_can', 6: 'white_plastic_bin', 7: 'blue_plastic_bin'}

        self._settings.appearance.page_style = style_map.get(
            self._page_style_combo.currentIndex(), 'lined')
        self._settings.appearance.page_color = self._page_color
        self._settings.appearance.line_color = self._line_color
        self._settings.appearance.sidebar_color = self._sidebar_color
        self._settings.appearance.trash_style = trash_map.get(
            self._trash_style_combo.currentIndex(), 'classic_recycling')
        self._settings.appearance.binding_type = binding_map.get(
            self._binding_combo.currentIndex(), 'rings')
        self._settings.appearance.show_margin = self._show_margin_check.isChecked()
        self._settings.appearance.line_spacing = self._line_spacing_spin.value()

        self._settings.general.default_agenda_dir = self._default_dir_edit.text()

        currency_map_rev = {0: 'CLP', 1: 'USD', 2: 'EUR'}
        self._settings.general.cost_currency = currency_map_rev.get(self._currency_combo.currentIndex(), 'CLP')
        
        self._settings.general.logo_path = self._logo_path_edit.text()

        # Extraer configuración de Secciones y Pestañas
        new_order = []
        new_hidden_sections = []
        new_custom_tab_names = {}

        for row in range(self._sections_table.rowCount()):
            orig_item = self._sections_table.item(row, 3)
            if not orig_item:
                continue
            plugin_id = orig_item.data(Qt.ItemDataRole.UserRole)
            orig_name = orig_item.data(Qt.ItemDataRole.UserRole + 1)
            
            new_order.append(plugin_id)
            
            # Checkbox de visibilidad
            chk_container = self._sections_table.cellWidget(row, 0)
            if chk_container:
                chk = chk_container.findChild(QCheckBox)
                if chk and not chk.isChecked():
                    new_hidden_sections.append(plugin_id)

            # Nombre personalizado
            name_widget = self._sections_table.cellWidget(row, 2)
            if isinstance(name_widget, QLineEdit):
                custom_name = name_widget.text().strip()
                if custom_name and custom_name != orig_name:
                    new_custom_tab_names[plugin_id] = custom_name

        self._settings.general.tab_order = new_order
        self._settings.general.hidden_sections = new_hidden_sections
        self._settings.general.custom_tab_names = new_custom_tab_names

        # Respaldos
        self._settings.backup.backup_dir = self._backup_dir_edit.text()
        self._settings.backup.filename_prefix = self._backup_name_edit.text()
        
        fmt_map_rev = {0: "ZIP", 1: "RAR", 2: "7ZIP", 3: "ARJ"}
        self._settings.backup.compression_format = fmt_map_rev.get(self._compression_combo.currentIndex(), "ZIP")
        
        self._settings.backup.split_volumes = self._split_volumes_check.isChecked()
        self._settings.backup.volume_size = self._volume_size_spin.value()

        # IA
        provider_map_rev = {0: 'lm_studio', 1: 'ollama', 2: 'custom_openai'}
        if not hasattr(self._settings, 'ai') or self._settings.ai is None:
            from config.settings import AISettings
            self._settings.ai = AISettings()
        self._settings.ai.provider = provider_map_rev.get(self._ai_provider_combo.currentIndex(), 'lm_studio')
        self._settings.ai.lm_studio_url = self._ai_lm_studio_url.text().strip()
        self._settings.ai.ollama_url = self._ai_ollama_url.text().strip()
        self._settings.ai.custom_url = self._ai_custom_url.text().strip()
        self._settings.ai.api_key = self._ai_api_key.text().strip()
        self._settings.ai.selected_model = self._ai_model_combo.currentText().strip()
        self._settings.ai.temperature = self._ai_temp_spin.value()
        self._settings.ai.max_tokens = self._ai_max_tokens_spin.value()
        self._settings.ai.system_prompt = self._ai_system_prompt.toPlainText().strip()
        self._settings.ai.enable_agent = self._ai_enable_agent.isChecked()

        return self._settings

    def _create_ai_tab(self) -> QWidget:
        """Crea la pestaña de configuración para Inteligencia Artificial Local (LM Studio / Ollama)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # --- SERVIDOR / PROVEEDOR IA ---
        provider_group = QGroupBox("Servidor e Integración de IA Local")
        p_form = QFormLayout(provider_group)
        p_form.setSpacing(8)

        self._ai_provider_combo = QComboBox()
        self._ai_provider_combo.addItems([
            "LM Studio (API Local OpenAI-Compatible)",
            "Ollama (API Nativa / Endpoint Local)",
            "Servidor Personalizado (OpenAI Compatible)"
        ])
        p_form.addRow("Proveedor de IA:", self._ai_provider_combo)

        self._ai_lm_studio_url = QLineEdit()
        self._ai_lm_studio_url.setPlaceholderText("http://localhost:1234/v1")
        p_form.addRow("URL LM Studio:", self._ai_lm_studio_url)

        self._ai_ollama_url = QLineEdit()
        self._ai_ollama_url.setPlaceholderText("http://localhost:11434")
        p_form.addRow("URL Ollama:", self._ai_ollama_url)

        self._ai_custom_url = QLineEdit()
        self._ai_custom_url.setPlaceholderText("http://localhost:8000/v1")
        p_form.addRow("URL Custom:", self._ai_custom_url)

        self._ai_api_key = QLineEdit()
        self._ai_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self._ai_api_key.setPlaceholderText("lm-studio (opcional para modelos locales)")
        p_form.addRow("Clave API / Token:", self._ai_api_key)

        layout.addWidget(provider_group)

        # --- SELECTOR DE MODELO ---
        model_group = QGroupBox("Selección y Detección de Modelos")
        m_layout = QHBoxLayout(model_group)

        self._ai_model_combo = QComboBox()
        self._ai_model_combo.setEditable(True)
        self._ai_model_combo.addItems([
            "qwen2.5-coder-7b-instruct",
            "llama3.2",
            "deepseek-r1-distill-qwen-7b",
            "mistral-7b-instruct",
            "phi-4"
        ])
        m_layout.addWidget(self._ai_model_combo, 1)

        btn_fetch_models = QPushButton("🔍 Buscar Modelos")
        btn_fetch_models.setStyleSheet("QPushButton { font-weight: bold; padding: 5px 10px; background: #89b4fa; color: #111; border-radius: 4px; }")
        btn_fetch_models.clicked.connect(self._fetch_ai_models)
        m_layout.addWidget(btn_fetch_models)

        btn_test_conn = QPushButton("⚡ Probar Conexión")
        btn_test_conn.setStyleSheet("QPushButton { font-weight: bold; padding: 5px 10px; background: #a6e3a1; color: #111; border-radius: 4px; }")
        btn_test_conn.clicked.connect(self._test_ai_connection)
        m_layout.addWidget(btn_test_conn)

        layout.addWidget(model_group)

        # --- PARÁMETROS DEL MODELO Y AGENTE ---
        params_group = QGroupBox("Parámetros del Modelo y Modo Agente")
        params_form = QFormLayout(params_group)
        params_form.setSpacing(8)

        self._ai_temp_spin = QDoubleSpinBox()
        self._ai_temp_spin.setRange(0.0, 2.0)
        self._ai_temp_spin.setSingleStep(0.1)
        self._ai_temp_spin.setValue(0.7)
        params_form.addRow("Temperatura (Creatividad):", self._ai_temp_spin)

        self._ai_max_tokens_spin = QSpinBox()
        self._ai_max_tokens_spin.setRange(128, 32768)
        self._ai_max_tokens_spin.setValue(2048)
        params_form.addRow("Máx Tokens (Respuesta):", self._ai_max_tokens_spin)

        self._ai_system_prompt = QTextEdit()
        self._ai_system_prompt.setMaximumHeight(70)
        self._ai_system_prompt.setPlaceholderText("Instrucciones iniciales del sistema...")
        params_form.addRow("Prompt del Sistema:", self._ai_system_prompt)

        self._ai_enable_agent = QCheckBox("Activar Capacidad de Agente (Inspección y herramientas de la agenda)")
        self._ai_enable_agent.setChecked(True)
        params_form.addRow("Modo Agente:", self._ai_enable_agent)

        layout.addWidget(params_group)
        layout.addStretch()
        return tab

    def _get_active_ai_endpoint(self) -> tuple[str, str]:
        """Retorna (endpoint_url, provider_type) según el proveedor seleccionado."""
        p_idx = self._ai_provider_combo.currentIndex()
        if p_idx == 0:
            url = self._ai_lm_studio_url.text().strip() or "http://localhost:1234/v1"
            return url.rstrip('/'), "openai"
        elif p_idx == 1:
            url = self._ai_ollama_url.text().strip() or "http://localhost:11434"
            return url.rstrip('/'), "ollama"
        else:
            url = self._ai_custom_url.text().strip() or "http://localhost:8000/v1"
            return url.rstrip('/'), "openai"

    def _fetch_ai_models(self):
        """Consulta el servidor local para listar los modelos instalados."""
        base_url, ptype = self._get_active_ai_endpoint()
        try:
            if ptype == "ollama":
                target_url = f"{base_url}/api/tags"
            else:
                target_url = f"{base_url}/models"

            req = urllib.request.Request(target_url, headers={'User-Agent': 'VitoOrganizer/2.9'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = []
                if ptype == "ollama":
                    for m in data.get('models', []): models.append(m.get('name'))
                else:
                    for m in data.get('data', []): models.append(m.get('id'))

                if models:
                    self._ai_model_combo.clear()
                    self._ai_model_combo.addItems(models)
                    QMessageBox.information(self, "Modelos Encontrados", f"Se detectaron {len(models)} modelo(s) en el servidor IA:\n" + ", ".join(models[:5]))
                else:
                    QMessageBox.warning(self, "Aviso", "Conexión lograda pero no se reportaron modelos instalados.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión", f"No se pudo consultar el servidor de IA ({base_url}).\nAsegúrate de que LM Studio u Ollama estén ejecutándose.\n\nDetalle:\n{str(e)}")

    def _test_ai_connection(self):
        """Envía una prueba de conexión rápida al servidor de IA."""
        base_url, ptype = self._get_active_ai_endpoint()
        model_name = self._ai_model_combo.currentText().strip() or "default"
        try:
            if ptype == "ollama":
                target_url = f"{base_url}/api/generate"
                payload = json.dumps({"model": model_name, "prompt": "Responde OK", "stream": False}).encode('utf-8')
            else:
                target_url = f"{base_url}/chat/completions"
                payload = json.dumps({
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Hola, responde únicamente 'OK'"}],
                    "max_tokens": 10
                }).encode('utf-8')

            req = urllib.request.Request(target_url, data=payload, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {self._ai_api_key.text()}'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                QMessageBox.information(self, "Conexión Éxitos", f"¡Conexión con el servidor IA exitosa!\n\nProveedor: {self._ai_provider_combo.currentText()}\nModelo: {model_name}\nURL: {base_url}")
        except Exception as e:
            QMessageBox.critical(self, "Fallo de Prueba", f"Error al probar la conexión con el servidor IA:\n\n{str(e)}")

    def _on_apply(self):
        """Aplica los cambios sin cerrar."""
        settings = self._get_current_settings()
        self.settings_changed.emit(settings)

    def _on_accept(self):
        """Acepta y cierra."""
        self._on_apply()
        self.accept()

