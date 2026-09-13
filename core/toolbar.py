# =============================================================================
# Vito Organizer v2.2 - Toolbar
# Barra de herramientas con iconos SVG
# =============================================================================

import os
from PyQt6.QtCore import pyqtSignal, QSize
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QToolBar


class AppToolBar(QToolBar):
    """Barra de herramientas principal de Vito Organizer."""

    # Señales
    action_toggle_sidebar = pyqtSignal()
    action_save = pyqtSignal()
    action_refresh = pyqtSignal()
    action_sync = pyqtSignal()
    action_copy = pyqtSignal()
    action_cut = pyqtSignal()
    action_paste = pyqtSignal()
    action_trash = pyqtSignal()
    action_export_pdf = pyqtSignal()
    action_ai_assistant = pyqtSignal()
    action_calculator = pyqtSignal()
    action_unit_converter = pyqtSignal()
    action_prev_page = pyqtSignal()
    action_next_page = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__("Herramientas", parent)
        self.setMovable(False)
        self.setIconSize(QSize(22, 22))

        self._icons_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'resources', 'icons'
        )

        self._build_toolbar()

    def _get_icon(self, name: str) -> QIcon:
        """Carga un icono SVG."""
        path = os.path.join(self._icons_dir, name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()

    def _build_toolbar(self):
        """Construye los botones de la barra de herramientas."""

        # Botón Toggle Sidebar (cuadrado mitad blanco/negro)
        toggle_action = QAction(
            self._get_icon('sidebar_toggle.svg'),
            "Mostrar/Ocultar barra lateral", self)
        toggle_action.setToolTip("Mostrar/Ocultar barra lateral")
        toggle_action.setCheckable(True)
        toggle_action.setChecked(True)
        toggle_action.triggered.connect(self.action_toggle_sidebar.emit)
        self.addAction(toggle_action)
        self._toggle_action = toggle_action

        self.addSeparator()

        # Botón Guardar (diskette)
        save_action = QAction(
            self._get_icon('save.svg'),
            "Guardar", self)
        save_action.setToolTip("Guardar agenda (Ctrl+S)")
        save_action.triggered.connect(self.action_save.emit)
        self.addAction(save_action)

        # Botón Refrescar (actualizar en caliente)
        refresh_action = QAction(
            self._get_icon('history.svg'),
            "Recargar", self)
        refresh_action.setToolTip("Recargar y actualizar agenda")
        refresh_action.triggered.connect(self.action_refresh.emit)
        self.addAction(refresh_action)

        # Botón Sincronizar Red
        sync_action = QAction(
            self._get_icon('sync.svg'),
            "Sincronizar Red", self)
        sync_action.setToolTip("Sincronizar datos entre cliente y servidor (Red Local)")
        sync_action.triggered.connect(self.action_sync.emit)
        self.addAction(sync_action)

        self.addSeparator()

        # Botón Copiar
        copy_action = QAction(
            self._get_icon('copy.svg'),
            "Copiar", self)
        copy_action.setToolTip("Copiar (Ctrl+C)")
        copy_action.triggered.connect(self.action_copy.emit)
        self.addAction(copy_action)

        # Botón Cortar
        cut_action = QAction(
            self._get_icon('cut.svg'),
            "Cortar", self)
        cut_action.setToolTip("Cortar (Ctrl+X)")
        cut_action.triggered.connect(self.action_cut.emit)
        self.addAction(cut_action)

        # Botón Pegar
        paste_action = QAction(
            self._get_icon('paste.svg'),
            "Pegar", self)
        paste_action.setToolTip("Pegar (Ctrl+V)")
        paste_action.triggered.connect(self.action_paste.emit)
        self.addAction(paste_action)

        self.addSeparator()

        # Botón Papelera
        trash_action = QAction(
            self._get_icon('trash_empty.svg'),
            "Papelera", self)
        trash_action.setToolTip("Abrir Papelera de Reciclaje")
        trash_action.triggered.connect(self.action_trash.emit)
        self.addAction(trash_action)

        self.addSeparator()

        # Botón Generar PDF
        pdf_action = QAction(
            self._get_icon('document.svg'),
            "Generar PDF", self)
        pdf_action.setToolTip("Generar documento PDF de la sección activa")
        pdf_action.setEnabled(False)
        pdf_action.triggered.connect(self.action_export_pdf.emit)
        self.addAction(pdf_action)
        self._pdf_action = pdf_action

        # Botón Asistente de IA
        ai_action = QAction(
            self._get_icon('component.svg'),
            "Asistente IA", self)
        ai_action.setToolTip("Abrir Asistente de Inteligencia Artificial (IA Local & Agente)")
        ai_action.triggered.connect(self.action_ai_assistant.emit)
        self.addAction(ai_action)

        # Botón Calculadora
        calc_action = QAction(
            self._get_icon('calculator.svg'),
            "Calculadora", self)
        calc_action.setToolTip("Abrir Calculadora Flotante (Ctrl+K)")
        calc_action.triggered.connect(self.action_calculator.emit)
        self.addAction(calc_action)

        # Botón Conversor de Unidades
        units_action = QAction(
            self._get_icon('ruler.svg'),
            "Unidades", self)
        units_action.setToolTip("Abrir Conversor de Unidades (Ctrl+U)")
        units_action.triggered.connect(self.action_unit_converter.emit)
        self.addAction(units_action)

        self.addSeparator()

        # --- Sistema de Navegación de Páginas ---
        from PyQt6.QtWidgets import QPushButton, QLabel, QWidget, QHBoxLayout
        nav_widget = QWidget(self)
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(4, 0, 4, 0)
        nav_layout.setSpacing(6)

        self.btn_prev_page = QPushButton()
        self.btn_prev_page.setIcon(self._get_icon('left.svg'))
        self.btn_prev_page.setIconSize(QSize(14, 14))
        self.btn_prev_page.setFixedSize(26, 24)
        self.btn_prev_page.setToolTip("Página anterior")
        self.btn_prev_page.setStyleSheet("""
            QPushButton { border: 1px solid #45475a; border-radius: 4px; background: rgba(255, 255, 255, 0.08); color: #cdd6f4; }
            QPushButton:hover:enabled { background: rgba(255, 255, 255, 0.2); }
            QPushButton:disabled { border-color: #313244; background: transparent; }
        """)
        self.btn_prev_page.clicked.connect(self.action_prev_page.emit)

        self.lbl_page = QLabel("1 de 1")
        self.lbl_page.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 12px; padding: 0 4px;")

        self.btn_next_page = QPushButton()
        self.btn_next_page.setIcon(self._get_icon('right.svg'))
        self.btn_next_page.setIconSize(QSize(14, 14))
        self.btn_next_page.setFixedSize(26, 24)
        self.btn_next_page.setToolTip("Página siguiente")
        self.btn_next_page.setStyleSheet("""
            QPushButton { border: 1px solid #45475a; border-radius: 4px; background: rgba(255, 255, 255, 0.08); color: #cdd6f4; }
            QPushButton:hover:enabled { background: rgba(255, 255, 255, 0.2); }
            QPushButton:disabled { border-color: #313244; background: transparent; }
        """)
        self.btn_next_page.clicked.connect(self.action_next_page.emit)

        nav_layout.addWidget(self.btn_prev_page)
        nav_layout.addWidget(self.lbl_page)
        nav_layout.addWidget(self.btn_next_page)

        self.addWidget(nav_widget)

    def set_sidebar_checked(self, checked: bool):
        """Actualiza el estado del botón toggle sidebar."""
        self._toggle_action.setChecked(checked)

    def update_pagination(self, current_page: int, total_pages: int):
        """Actualiza el contador de páginas y el estado de los botones de navegación."""
        self.lbl_page.setText(f"{current_page} de {total_pages}")
        self.btn_prev_page.setEnabled(current_page > 1)
        self.btn_next_page.setEnabled(current_page < total_pages)

    def set_pdf_export_enabled(self, enabled: bool):
        """Habilita o deshabilita el botón de exportación a PDF."""
        self._pdf_action.setEnabled(enabled)
