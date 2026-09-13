# =============================================================================
# Vito Organizer v2.2 - Menu Bar
# Barra de menú de la aplicación
# =============================================================================

import os
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import QMenuBar, QMenu


class AppMenuBar(QMenuBar):
    """Barra de menú principal de Vito Organizer."""

    # Señales para acciones
    # Archivo
    action_new = pyqtSignal()
    action_open = pyqtSignal()
    action_save = pyqtSignal()
    action_save_as = pyqtSignal()
    action_close = pyqtSignal()

    # Editar
    action_cut = pyqtSignal()
    action_copy = pyqtSignal()
    action_paste = pyqtSignal()
    action_export_pdf = pyqtSignal()
    action_unit_converter = pyqtSignal()
    action_calculator = pyqtSignal()
    action_ai_assistant = pyqtSignal()

    # Sección
    action_section = pyqtSignal(str)  # Emite el plugin_id

    # Opciones
    action_settings = pyqtSignal()
    action_trash = pyqtSignal()
    action_connectivity = pyqtSignal()
    action_correlativos = pyqtSignal()

    # Ayuda
    action_instructions = pyqtSignal()
    action_information = pyqtSignal()
    action_version = pyqtSignal()
    action_license = pyqtSignal()
    action_about = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._section_actions = {}
        self._icons_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'resources', 'icons'
        )
        self._build_menus()

    def _get_icon(self, name: str) -> QIcon:
        """Carga un icono SVG."""
        path = os.path.join(self._icons_dir, name)
        if os.path.exists(path):
            return QIcon(path)
        return QIcon()

    def _build_menus(self):
        """Construye todos los menús."""
        self._build_file_menu()
        self._build_edit_menu()
        self._build_section_menu()
        self._build_utilities_menu()
        self._build_options_menu()
        self._build_help_menu()

    def _build_file_menu(self):
        """Menú Archivo."""
        menu = self.addMenu("&Archivo")

        new_action = QAction(self._get_icon('new_file.svg'), "&Nuevo", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.setStatusTip("Crear nueva agenda")
        new_action.triggered.connect(self.action_new.emit)
        menu.addAction(new_action)

        open_action = QAction(self._get_icon('open_folder.svg'), "&Abrir", self)
        open_action.setShortcut(QKeySequence("Ctrl+O"))
        open_action.setStatusTip("Abrir agenda existente")
        open_action.triggered.connect(self.action_open.emit)
        menu.addAction(open_action)

        menu.addSeparator()

        save_action = QAction(self._get_icon('save.svg'), "&Guardar", self)
        save_action.setShortcut(QKeySequence("Ctrl+S"))
        save_action.setStatusTip("Guardar agenda")
        save_action.triggered.connect(self.action_save.emit)
        menu.addAction(save_action)
        self._save_action = save_action

        save_as_action = QAction(self._get_icon('save_as.svg'), "Guardar &Como...", self)
        save_as_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_action.setStatusTip("Guardar agenda en otra ubicación")
        save_as_action.triggered.connect(self.action_save_as.emit)
        menu.addAction(save_as_action)

        menu.addSeparator()

        close_action = QAction(self._get_icon('close.svg'), "&Cerrar", self)
        close_action.setShortcut(QKeySequence("Ctrl+W"))
        close_action.setStatusTip("Cerrar agenda actual")
        close_action.triggered.connect(self.action_close.emit)
        menu.addAction(close_action)

    def _build_edit_menu(self):
        """Menú Editar."""
        menu = self.addMenu("&Editar")

        cut_action = QAction(self._get_icon('cut.svg'), "Cor&tar", self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        cut_action.setStatusTip("Cortar selección")
        cut_action.triggered.connect(self.action_cut.emit)
        menu.addAction(cut_action)

        copy_action = QAction(self._get_icon('copy.svg'), "&Copiar", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        copy_action.setStatusTip("Copiar selección")
        copy_action.triggered.connect(self.action_copy.emit)
        menu.addAction(copy_action)

        paste_action = QAction(self._get_icon('paste.svg'), "&Pegar", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        paste_action.setStatusTip("Pegar del portapapeles")
        paste_action.triggered.connect(self.action_paste.emit)
        menu.addAction(paste_action)

        menu.addSeparator()

        pdf_action = QAction(self._get_icon('document.svg'), "&Generar PDF...", self)
        pdf_action.setShortcut(QKeySequence("Ctrl+P"))
        pdf_action.setStatusTip("Generar documento PDF de la sección actual")
        pdf_action.setEnabled(False)
        pdf_action.triggered.connect(self.action_export_pdf.emit)
        menu.addAction(pdf_action)
        self._pdf_action = pdf_action

    def _build_utilities_menu(self):
        """Menú Utilidades."""
        menu = self.addMenu("&Utilidades")

        units_action = QAction(self._get_icon('ruler.svg'), "&Unidades...", self)
        units_action.setShortcut(QKeySequence("Ctrl+U"))
        units_action.setStatusTip("Abrir conversor de unidades de medida")
        units_action.triggered.connect(self.action_unit_converter.emit)
        menu.addAction(units_action)

        calc_action = QAction(self._get_icon('calculator.svg'), "Ca&lculadora...", self)
        calc_action.setShortcut(QKeySequence("Ctrl+K"))
        calc_action.setStatusTip("Abrir calculadora (básica, científica, electrónica)")
        calc_action.triggered.connect(self.action_calculator.emit)
        menu.addAction(calc_action)

        ai_action = QAction(self._get_icon('component.svg'), "Asistente de &IA...", self)
        ai_action.setShortcut(QKeySequence("Ctrl+Shift+I"))
        ai_action.setStatusTip("Abrir Asistente de Inteligencia Artificial (IA Local & Agente)")
        ai_action.triggered.connect(self.action_ai_assistant.emit)
        menu.addAction(ai_action)

    def _build_section_menu(self):
        """Menú Sección."""
        self._section_menu = self.addMenu("&Sección")
        # Se poblará dinámicamente cuando se carguen los plugins

    def populate_sections(self, sections: list):
        """Puebla el menú de secciones con los plugins cargados.

        Args:
            sections: Lista de (plugin_id, name, icon_name)
        """
        self._section_menu.clear()
        self._section_actions.clear()

        for plugin_id, name, icon_name in sections:
            action = QAction(self._get_icon(icon_name), name, self)
            action.setStatusTip(f"Ir a la sección {name}")
            action.triggered.connect(
                lambda checked, pid=plugin_id: self.action_section.emit(pid))
            self._section_menu.addAction(action)
            self._section_actions[plugin_id] = action

    def _build_options_menu(self):
        """Menú Opciones."""
        menu = self.addMenu("&Opciones")

        settings_action = QAction(
            self._get_icon('settings.svg'), "&Configuración", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.setStatusTip("Abrir configuración")
        settings_action.triggered.connect(self.action_settings.emit)
        menu.addAction(settings_action)

        trash_action = QAction(
            self._get_icon('trash_empty.svg'), "&Papelera", self)
        trash_action.setStatusTip("Abrir papelera de reciclaje")
        trash_action.triggered.connect(self.action_trash.emit)
        menu.addAction(trash_action)

        connectivity_action = QAction(
            self._get_icon('globe.svg'), "Conectividad de &Red...", self)
        connectivity_action.setStatusTip("Herramientas de sincronización local y de red")
        connectivity_action.triggered.connect(self.action_connectivity.emit)
        menu.addAction(connectivity_action)

        correlativos_action = QAction(
            self._get_icon('edit.svg'), "Control de &Correlativos...", self)
        correlativos_action.setStatusTip("Administrar secuencias de documentos (Check Lists, Facturas, etc.)")
        correlativos_action.triggered.connect(self.action_correlativos.emit)
        menu.addAction(correlativos_action)

    def _build_help_menu(self):
        """Menú Ayuda."""
        menu = self.addMenu("A&yuda")

        instructions_action = QAction(self._get_icon('manual.svg'), "&Instrucciones", self)
        instructions_action.setShortcut(QKeySequence("F1"))
        instructions_action.setStatusTip("Ver instrucciones de uso")
        instructions_action.triggered.connect(self.action_instructions.emit)
        menu.addAction(instructions_action)

        information_action = QAction(self._get_icon('document.svg'), "I&nformación Técnica y Documentación...", self)
        information_action.setStatusTip("Ver documentación técnica, formato .doki y guías Markdown")
        information_action.triggered.connect(self.action_information.emit)
        menu.addAction(information_action)

        menu.addSeparator()

        version_action = QAction(self._get_icon('history.svg'), "&Versión", self)
        version_action.setStatusTip("Información de versión")
        version_action.triggered.connect(self.action_version.emit)
        menu.addAction(version_action)

        license_action = QAction(self._get_icon('safety.svg'), "&Licencia", self)
        license_action.setStatusTip("Ver la licencia del software")
        license_action.triggered.connect(self.action_license.emit)
        menu.addAction(license_action)

        about_action = QAction(self._get_icon('vito_organizer_icon.svg'), "&Acerca de...", self)
        about_action.setStatusTip("Acerca de Vito Organizer")
        about_action.triggered.connect(self.action_about.emit)
        menu.addAction(about_action)

    def set_pdf_export_enabled(self, enabled: bool):
        """Habilita o deshabilita la acción de exportar a PDF en el menú Editar."""
        if hasattr(self, '_pdf_action'):
            self._pdf_action.setEnabled(enabled)
