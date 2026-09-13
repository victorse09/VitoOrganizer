# =============================================================================
# Vito Organizer v2.2 - Main Window
# Ventana principal de la aplicación
# =============================================================================

import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QSplitter, QVBoxLayout, QWidget, QMessageBox, QFileDialog, QInputDialog
)
from PyQt6.QtGui import QIcon

from config.settings import Settings
from core.menu_bar import AppMenuBar
from core.toolbar import AppToolBar
from core.sidebar import Sidebar
from core.agenda_view import AgendaView
from core.status_bar import AppStatusBar
from config.settings_dialog import SettingsDialog
from core.correlativos_manager import CorrelativosManager
from core.correlativos_dialog import CorrelativosDialog
from plugins.plugin_manager import PluginManager
from data.agenda_manager import AgendaManager


class MainWindow(QMainWindow):
    """Ventana principal de Vito Organizer."""

    def __init__(self, app_instance):
        super().__init__()
        self.app = app_instance
        self.setWindowTitle("Vito Organizer")
        self.setMinimumSize(800, 600)
        
        icon_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'resources', 'icons', 'vito_organizer_icon.svg'
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Gestores
        self.settings = Settings.load()
        self.plugin_manager = PluginManager()
        self.agenda_manager = AgendaManager()

        self._setup_ui()
        self._connect_signals()
        self._update_connectivity_status()

        # Inicialización
        self.plugin_manager.discover_and_load()
        self._populate_plugins()
        
        # Aplicar configuración de apariencia inicial
        self.agenda_view.set_appearance(self.settings.appearance)
        self.sidebar.set_sidebar_color(getattr(self.settings.appearance, 'sidebar_color', '#1b4332'))
        self.sidebar.set_trash_style(getattr(self.settings.appearance, 'trash_style', 'classic_recycling'))

        # Abrir última agenda si existe
        if self.settings.general.last_agenda_path and \
           os.path.exists(self.settings.general.last_agenda_path):
            self._open_agenda(self.settings.general.last_agenda_path)
        else:
            self._update_title()

        # Restaurar estado de la ventana si existe
        if self.settings.general.window_state:
            self.restoreGeometry(self.settings.general.window_state)
        else:
            self.showMaximized()

    def showEvent(self, event):
        super().showEvent(event)
        if not hasattr(self, '_splitter_shown'):
            self._splitter_shown = True
            sw = self.settings.general.sidebar_width or 200
            total_w = self.width() if self.width() > 0 else 1000
            self.splitter.setSizes([sw, max(100, total_w - sw)])

    def _setup_ui(self):
        """Configura la interfaz principal."""
        # Menú
        self.menu_bar = AppMenuBar(self)
        self.setMenuBar(self.menu_bar)

        # Toolbar
        self.toolbar = AppToolBar(self)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)

        # Status Bar
        self.status_bar = AppStatusBar(self)
        self.setStatusBar(self.status_bar)

        # Widget central (Splitter)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(self.splitter)

        # Sidebar
        self.sidebar = Sidebar()
        self.splitter.addWidget(self.sidebar)

        # Vista de agenda (libro abierto)
        self.agenda_view = AgendaView()
        self.splitter.addWidget(self.agenda_view)

        # Configurar factores de estiramiento (sidebar fijo, agenda estirable)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)

        # Proporciones iniciales del splitter
        sw = self.settings.general.sidebar_width or 200
        self.splitter.setSizes([sw, 800])
        
        # Estado inicial del sidebar
        if not self.settings.general.sidebar_visible:
            self.sidebar.hide()
            self.toolbar.set_sidebar_checked(False)

    def _connect_signals(self):
        """Conecta las señales de los componentes."""
        # Toolbar
        self.toolbar.action_toggle_sidebar.connect(self._toggle_sidebar)
        self.toolbar.action_save.connect(self._save_agenda)
        self.toolbar.action_trash.connect(self._show_trash)
        self.toolbar.action_export_pdf.connect(self._on_export_pdf)
        self.toolbar.action_ai_assistant.connect(self._show_ai_assistant)
        self.toolbar.action_calculator.connect(self._show_calculator)
        self.toolbar.action_unit_converter.connect(self._show_unit_converter)
        self.toolbar.action_prev_page.connect(self._on_prev_page)
        self.toolbar.action_next_page.connect(self._on_next_page)
        self.toolbar.action_refresh.connect(self._reload_agenda)
        self.toolbar.action_sync.connect(self._sync_network_data)

        # Splitter & Sidebar Trash
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        self.sidebar.trash_widget.trash_clicked.connect(self._show_trash)

        # Menú - Archivo
        self.menu_bar.action_new.connect(self._new_agenda)
        self.menu_bar.action_open.connect(self._browse_open_agenda)
        self.menu_bar.action_save.connect(self._save_agenda)
        self.menu_bar.action_save_as.connect(self._save_as_agenda)
        self.menu_bar.action_close.connect(self.close)

        # Menú - Sección
        self.menu_bar.action_section.connect(self._change_section)

        # Menú - Opciones
        self.menu_bar.action_settings.connect(self._show_settings)
        self.menu_bar.action_trash.connect(self._show_trash)
        self.menu_bar.action_connectivity.connect(self._show_connectivity)
        self.menu_bar.action_correlativos.connect(self._show_correlativos)

        # Menú - Editar (Herramientas)
        self.menu_bar.action_export_pdf.connect(self._on_export_pdf)
        self.menu_bar.action_unit_converter.connect(self._show_unit_converter)
        self.menu_bar.action_calculator.connect(self._show_calculator)
        self.menu_bar.action_ai_assistant.connect(self._show_ai_assistant)

        # Menú - Ayuda
        self.menu_bar.action_instructions.connect(self._show_instructions)
        self.menu_bar.action_information.connect(self._show_information)
        self.menu_bar.action_version.connect(self._show_version)
        self.menu_bar.action_license.connect(self._show_license)
        self.menu_bar.action_about.connect(self._show_about)

        # Vista de agenda
        self.agenda_view.section_changed.connect(self._change_section)

    def _populate_plugins(self):
        """Prepara la interfaz con los plugins cargados."""
        if self.settings.general.tab_order:
            self.plugin_manager.sort_plugins(self.settings.general.tab_order)
            
        plugins = self.plugin_manager.get_plugins()
        
        # Pestañas
        tabs_data = []
        menu_sections = []
        
        hidden_ids = set(getattr(self.settings.general, 'hidden_sections', []))
        custom_names = getattr(self.settings.general, 'custom_tab_names', {})
        
        for p in plugins:
            if hasattr(p, 'set_plugin_manager'):
                p.set_plugin_manager(self.plugin_manager)

            # Sidebar widget
            self.sidebar.add_section_widget(p.get_id(), p.create_sidebar_widget())
            if hasattr(p, 'trash_changed'):
                p.trash_changed.connect(self._update_trash_status)
            if hasattr(p, 'events_changed'):
                p.events_changed.connect(self._on_plugin_events_changed)
            if hasattr(p, 'page_changed'):
                p.page_changed.connect(lambda c, t: self._update_pagination_ui())
            if hasattr(p, 'single_page_requested'):
                p.single_page_requested.connect(self.agenda_view.set_single_page_mode)
            if hasattr(p, 'status_message_requested'):
                p.status_message_requested.connect(self._show_temporary_status)
            if hasattr(p, 'pdf_export_state_changed'):
                p.pdf_export_state_changed.connect(self._update_pdf_export_ui)

            if p.get_id() in hidden_ids:
                continue

            p_name = custom_names.get(p.get_id()) or p.get_name()
            tabs_data.append((p.get_id(), p_name, p.get_tab_color(), p.get_order()))
            menu_sections.append((p.get_id(), p_name, p.get_icon()))

        self.agenda_view.set_tabs(tabs_data)
        self.menu_bar.populate_sections(menu_sections)

        # Activar última sección guardada al iniciar (siempre que esté visible)
        target_section = self.settings.general.last_section
        visible_plugins = [p for p in plugins if p.get_id() not in hidden_ids]

        if target_section in hidden_ids or not self.plugin_manager.get_plugin_by_id(target_section):
            target_section = visible_plugins[0].get_id() if visible_plugins else (plugins[0].get_id() if plugins else None)

        if target_section:
            self._change_section(target_section)

    def _update_trash_status(self):
        has_trash = self.plugin_manager.any_plugin_has_trash()
        self.sidebar.trash_widget.set_has_items(has_trash)

    def _on_plugin_events_changed(self):
        cal_p = self.plugin_manager.get_plugin_by_id('calendario')
        if cal_p and hasattr(cal_p, '_update_all_views_events'):
            cal_p._update_all_views_events()

    def _on_prev_page(self):
        plugin = self.plugin_manager.get_active_plugin()
        if plugin:
            curr = plugin.get_current_page()
            if curr > 1:
                plugin.go_to_page(curr - 1)
                self._update_pagination_ui()

    def _on_next_page(self):
        plugin = self.plugin_manager.get_active_plugin()
        if plugin:
            curr = plugin.get_current_page()
            total = plugin.get_total_pages()
            if curr < total:
                plugin.go_to_page(curr + 1)
                self._update_pagination_ui()

    def _update_pagination_ui(self):
        plugin = self.plugin_manager.get_active_plugin()
        if plugin:
            curr = plugin.get_current_page()
            total = plugin.get_total_pages()
            self.toolbar.update_pagination(curr, total)
            self.agenda_view.set_pagination(curr, total)

    def _update_pdf_export_ui(self, enabled: bool = None):
        plugin = self.plugin_manager.get_active_plugin()
        if enabled is None:
            enabled = plugin.supports_pdf_export() if plugin else False
        self.toolbar.set_pdf_export_enabled(enabled)
        self.menu_bar.set_pdf_export_enabled(enabled)

    def _on_export_pdf(self):
        plugin = self.plugin_manager.get_active_plugin()
        if plugin and plugin.supports_pdf_export():
            if not hasattr(self, 'correlativos_manager') or not self.correlativos_manager:
                if self.agenda_manager.is_open:
                    self.correlativos_manager = CorrelativosManager(self.agenda_manager.current_path)
            if hasattr(plugin, 'set_correlativos_manager'):
                plugin.set_correlativos_manager(getattr(self, 'correlativos_manager', None))
            plugin.export_pdf(self)

    def _change_section(self, plugin_id: str):
        """Cambia la sección activa."""
        plugin = self.plugin_manager.activate_plugin(plugin_id)
        if not plugin:
            return

        # Resetear modo página única al cambiar de sección
        self.agenda_view.set_single_page_mode(False)

        # Actualizar UI
        self.sidebar.show_section(plugin_id)
        self.agenda_view.set_active_section(plugin_id)
        
        # Actualizar páginas de la agenda
        self.agenda_view.set_left_content(plugin.create_left_page())
        self.agenda_view.set_right_content(plugin.create_right_page())
        
        custom_names = getattr(self.settings.general, 'custom_tab_names', {})
        disp_name = custom_names.get(plugin.get_id()) or plugin.get_name()
        self.status_bar.set_section(disp_name)
        
        # Guardar última sección
        self.settings.general.last_section = plugin_id
        self.settings.save()
        
        self._update_pagination_ui()
        self._update_pdf_export_ui()

    def _on_splitter_moved(self, pos, index):
        if self.sidebar.isVisible():
            sizes = self.splitter.sizes()
            if sizes and sizes[0] > 0:
                self.settings.general.sidebar_width = sizes[0]
                self.settings.save()

    def _toggle_sidebar(self):
        """Muestra u oculta la barra lateral."""
        visible = not self.sidebar.isVisible()
        if visible:
            self.sidebar.show()
            w = self.settings.general.sidebar_width or 200
            total_w = self.splitter.width()
            self.splitter.setSizes([w, max(100, total_w - w)])
        else:
            sizes = self.splitter.sizes()
            if sizes and sizes[0] > 0:
                self.settings.general.sidebar_width = sizes[0]
            self.sidebar.hide()
            
        self.settings.general.sidebar_visible = visible
        self.settings.save()

    # ---- Operaciones de Agenda ----

    def _update_title(self):
        """Actualiza el título de la ventana."""
        title = "Vito Organizer - "
        if self.agenda_manager.is_open:
            title += f"[{self.agenda_manager.name}]"
        else:
            title += "[Sin título]"
        self.setWindowTitle(title)
        
        self.status_bar.set_agenda(self.agenda_manager.name if self.agenda_manager.is_open else "Ninguna")

    def _new_agenda(self):
        """Crea una nueva agenda."""
        name, ok = QInputDialog.getText(self, "Nueva Agenda", "Nombre de la Agenda:")
        if ok and name:
            parent_dir = QFileDialog.getExistingDirectory(
                self, "Seleccionar ubicación",
                self.settings.general.default_agenda_dir,
                QFileDialog.Option.ShowDirsOnly
            )
            if parent_dir:
                path = os.path.join(parent_dir, name)
                if self.agenda_manager.create(name, path):
                    self._open_agenda(path)

    def _browse_open_agenda(self):
        """Abre un diálogo para seleccionar agenda."""
        path = QFileDialog.getExistingDirectory(
            self, "Abrir Agenda",
            self.settings.general.default_agenda_dir
        )
        if path:
            if AgendaManager.is_valid_agenda(path):
                self._open_agenda(path)
            else:
                QMessageBox.warning(self, "Error", "La carpeta seleccionada no es una agenda válida.")

    def _open_agenda(self, path: str):
        """Abre una agenda específica."""
        if self.agenda_manager.open(path):
            self._update_title()
            
            # Aplicar apariencia guardada
            appearance_dict = self.agenda_manager.get_appearance()
            for key, value in appearance_dict.items():
                if hasattr(self.settings.appearance, key):
                    setattr(self.settings.appearance, key, value)
            self.agenda_view.set_appearance(self.settings.appearance)
            self.sidebar.set_sidebar_color(getattr(self.settings.appearance, 'sidebar_color', '#1b4332'))
            self.sidebar.set_trash_style(getattr(self.settings.appearance, 'trash_style', 'classic_recycling'))
            
            # Cargar datos a los plugins
            self.plugin_manager.load_all_data(path)
            self._on_plugin_events_changed()
            
            # Cargar correlativos globales
            self.correlativos_manager = CorrelativosManager(path)
            
            # Actualizar settings
            self.settings.general.last_agenda_path = path
            self.settings.save()
            
            # Actualizar papelera
            has_trash = self.plugin_manager.any_plugin_has_trash()
            self.sidebar.trash_widget.set_has_items(has_trash)

    def _save_agenda(self):
        """Guarda la agenda actual."""
        if not self.agenda_manager.is_open:
            self._save_as_agenda()
            return

        # Guardar apariencia
        self.agenda_manager.set_appearance(self.settings.appearance.__dict__)
        
        # Guardar metadata
        self.agenda_manager.save()
        
        # Guardar datos de plugins
        self.plugin_manager.save_all_data(self.agenda_manager.current_path)
        
        # Guardar ancho de sidebar y settings
        sizes = self.splitter.sizes()
        if self.sidebar.isVisible() and sizes and sizes[0] > 0:
            self.settings.general.sidebar_width = sizes[0]
        self.settings.save()
        
        self.status_bar.set_status("Agenda guardada", 3000)

    def _save_as_agenda(self):
        """Guarda la agenda con nuevo nombre."""
        path = QFileDialog.getSaveFileName(
            self, "Guardar Agenda Como", 
            self.settings.general.default_agenda_dir,
            "Carpetas (*)"
        )[0]
        
        if path:
            if self.agenda_manager.save_as(path):
                self._open_agenda(path)

    def _show_settings(self):
        """Muestra el diálogo de configuración."""
        dialog = SettingsDialog(self.settings, self.plugin_manager, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()

    def _on_settings_changed(self, new_settings: Settings):
        """Aplica la nueva configuración."""
        self.settings = new_settings
        self.agenda_view.set_appearance(self.settings.appearance)
        self.sidebar.set_sidebar_color(getattr(self.settings.appearance, 'sidebar_color', '#1b4332'))
        self.sidebar.set_trash_style(getattr(self.settings.appearance, 'trash_style', 'classic_recycling'))
        
        # Reordenar y filtrar pestañas
        if self.settings.general.tab_order:
            self.plugin_manager.sort_plugins(self.settings.general.tab_order)
            
        plugins = self.plugin_manager.get_plugins()
        hidden_ids = set(getattr(self.settings.general, 'hidden_sections', []))
        custom_names = getattr(self.settings.general, 'custom_tab_names', {})
        
        tabs_data = []
        menu_sections = []
        for p in plugins:
            if p.get_id() in hidden_ids:
                continue
            disp_name = custom_names.get(p.get_id()) or p.get_name()
            tabs_data.append((p.get_id(), disp_name, p.get_tab_color(), p.get_order()))
            menu_sections.append((p.get_id(), disp_name, p.get_icon()))

        self.agenda_view.set_tabs(tabs_data)
        self.menu_bar.populate_sections(menu_sections)

        # Si la sección activa actual fue ocultada/deshabilitada, activar la primera visible
        active_p = self.plugin_manager.get_active_plugin()
        if active_p and active_p.get_id() in hidden_ids:
            visible_plugins = [p for p in plugins if p.get_id() not in hidden_ids]
            if visible_plugins:
                self._change_section(visible_plugins[0].get_id())
        elif active_p:
            disp_name = custom_names.get(active_p.get_id()) or active_p.get_name()
            self.status_bar.set_section(disp_name)

        if self.agenda_manager.is_open:
            self.agenda_manager.set_appearance(self.settings.appearance.__dict__)
            self.agenda_manager.is_modified = True

    def _show_trash(self):
        """Muestra el diálogo de gestión de la papelera."""
        from core.trash_dialog import TrashDialog
        dlg = TrashDialog(self.plugin_manager, self)
        dlg.exec()

    def _show_instructions(self):
        """Muestra el diálogo de instrucciones."""
        from core.help_dialogs import InstructionsDialog
        dlg = InstructionsDialog(self)
        dlg.exec()

    def _show_information(self):
        """Muestra el diálogo de información técnica y documentación Markdown."""
        from core.help_dialogs import InformationDialog
        dlg = InformationDialog(self)
        dlg.exec()

    def _show_version(self):
        """Muestra el diálogo de historial de versiones."""
        from core.help_dialogs import VersionDialog
        dlg = VersionDialog(self)
        dlg.exec()

    def _show_license(self):
        """Muestra el diálogo de licencia."""
        from core.help_dialogs import LicenseDialog
        dlg = LicenseDialog(self)
        dlg.exec()

    def _show_about(self):
        """Muestra el diálogo Acerca de."""
        from core.help_dialogs import AboutDialog
        dlg = AboutDialog(self)
        dlg.exec()

    @property
    def agenda_path(self):
        return self.agenda_manager.current_path if self.agenda_manager.is_open else ""

    def _show_connectivity(self):
        """Muestra el diálogo de conectividad y sincronización."""
        from core.connectivity import ConnectivityDialog
        dialog = ConnectivityDialog(self)
        dialog.exec()

    def _sync_network_data(self):
        """Ejecuta la sincronización de red entre cliente y servidor o abre el panel de conectividad."""
        if not self.agenda_manager.is_open:
            QMessageBox.warning(self, "Agenda Requerida", "Debe abrir una agenda previamente para sincronizar datos.")
            return

        from PyQt6.QtCore import QSettings
        from core.connectivity import ConnectivityDialog, SyncWorkerThread

        qsettings = QSettings("Vitokin", "VitoOrganizerConnectivity")
        ip = qsettings.value("cli_ip", "").strip()
        port_str = qsettings.value("cli_port", "8080").strip()
        password = qsettings.value("cli_pass", "")
        client_name = qsettings.value("cli_name", "").strip()

        # Si hay parámetros de cliente configurados, lanzar la sincronización directa en segundo plano
        if ip and port_str and password and client_name:
            if hasattr(self, '_sync_worker') and self._sync_worker and self._sync_worker.isRunning():
                QMessageBox.information(self, "Sincronización en curso", "Ya hay un proceso de sincronización en ejecución.")
                return

            self.statusBar().showMessage("Sincronizando datos de red con el servidor...", 5000)
            self._sync_worker = SyncWorkerThread('bidirectional', ip, int(port_str), password, client_name, self.agenda_path)

            def _on_sync_finished(success, message):
                if success:
                    self._reload_agenda()
                    QMessageBox.information(self, "Sincronización Completada", f"¡Sincronización exitosa!\n\n{message}")
                else:
                    QMessageBox.critical(self, "Error en Sincronización", f"Fallo al sincronizar:\n\n{message}")

            self._sync_worker.finished_sync.connect(_on_sync_finished)
            self._sync_worker.start()
        else:
            # Si no hay datos guardados, abrir el diálogo para configurar
            dialog = ConnectivityDialog(self)
            dialog.exec()

    def _show_correlativos(self):
        """Muestra el gestor global de correlativos."""
        if not self.agenda_manager.is_open:
            QMessageBox.information(self, "Agenda no abierta", "Debe abrir una agenda primero para gestionar correlativos.")
            return
        
        # Ensure it exists (should exist if agenda is open)
        if not hasattr(self, 'correlativos_manager') or not self.correlativos_manager:
            self.correlativos_manager = CorrelativosManager(self.agenda_manager.current_path)
            
        dialog = CorrelativosDialog(self.correlativos_manager, self)
        dialog.exec()

    def _reload_agenda(self):
        """Vuelve a cargar los datos de la agenda actual tras una sincronización."""
        if self.agenda_path and os.path.exists(self.agenda_path):
            self.plugin_manager.load_all_data(self.agenda_path)
            self._on_plugin_events_changed()
            self._update_trash_status()
            
            # Recargar la sección de la página actual para actualizar la visualización
            if hasattr(self, 'current_section'):
                self._change_section(self.current_section)

    def _update_connectivity_status(self):
        """Actualiza el indicador de estado de red en la barra de estado."""
        if hasattr(self, 'server_thread') and self.server_thread and self.server_thread.is_running:
            self.status_bar.set_connectivity_mode('server', f"{self.server_thread.port}")
        elif getattr(self, 'client_connected', False):
            self.status_bar.set_connectivity_mode('client', getattr(self, 'client_server_ip', ''))
        else:
            self.status_bar.set_connectivity_mode('local')

    def _show_unit_converter(self):
        """Muestra la herramienta de conversor de unidades como ventana flotante."""
        if hasattr(self, '_unit_converter_dialog') and self._unit_converter_dialog is not None:
            if self._unit_converter_dialog.isHidden():
                self._unit_converter_dialog.show()
            self._unit_converter_dialog.raise_()
            self._unit_converter_dialog.activateWindow()
            return
        from tools.unit_converter import UnitConverterDialog
        self._unit_converter_dialog = UnitConverterDialog(self)
        self._unit_converter_dialog.destroyed.connect(
            lambda: setattr(self, '_unit_converter_dialog', None))
        self._unit_converter_dialog.show()

    def _show_calculator(self):
        """Muestra la calculadora como ventana flotante."""
        if hasattr(self, '_calculator_dialog') and self._calculator_dialog is not None:
            if self._calculator_dialog.isHidden():
                self._calculator_dialog.show()
            self._calculator_dialog.raise_()
            self._calculator_dialog.activateWindow()
            return
        from tools.calculator import CalculatorDialog
        self._calculator_dialog = CalculatorDialog(self)
        self._calculator_dialog.destroyed.connect(
            lambda: setattr(self, '_calculator_dialog', None))
        self._calculator_dialog.show()

    def _show_ai_assistant(self):
        """Muestra el Asistente de IA como ventana flotante."""
        if hasattr(self, '_ai_assistant_dialog') and self._ai_assistant_dialog is not None:
            if self._ai_assistant_dialog.isHidden():
                self._ai_assistant_dialog.show()
            self._ai_assistant_dialog.raise_()
            self._ai_assistant_dialog.activateWindow()
            return
        from tools.ai_assistant import AIAssistantDialog
        self._ai_assistant_dialog = AIAssistantDialog(main_window=self, parent=self)
        self._ai_assistant_dialog.destroyed.connect(
            lambda: setattr(self, '_ai_assistant_dialog', None))
        self._ai_assistant_dialog.show()

    def _show_temporary_status(self, message: str):
        """Muestra una confirmación temporal en la barra de estado."""
        self.status_bar.set_status(message, 3000)

    def closeEvent(self, event):
        """Maneja el cierre de la ventana."""
        # Detener servidor de red si estuviera corriendo
        if hasattr(self, 'server_thread') and self.server_thread:
            try:
                self.server_thread.stop()
            except:
                pass

        # Guardar estado de la ventana
        self.settings.general.window_state = self.saveGeometry()
        if self.sidebar.isVisible():
            sizes = self.splitter.sizes()
            if sizes and sizes[0] > 0:
                self.settings.general.sidebar_width = sizes[0]
        self.settings.save()
        
        # Limpiar plugins
        self.plugin_manager.clear_all_data()
        
        event.accept()
