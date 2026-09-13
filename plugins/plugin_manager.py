# =============================================================================
# Vito Organizer v2.2 - Plugin Manager
# Carga dinámica y gestión de plugins de sección
# =============================================================================

import os
import json
import importlib
from typing import List, Optional, Dict

from plugins.plugin_base import PluginBase


class PluginManager:
    """Gestiona la carga dinámica y el ciclo de vida de los plugins."""

    def __init__(self):
        self._plugins: List[PluginBase] = []
        self._plugins_by_id: Dict[str, PluginBase] = {}
        self._active_plugin: Optional[PluginBase] = None
        self._plugins_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__))
        )

    def discover_and_load(self):
        """Descubre y carga todos los plugins disponibles."""
        self._plugins.clear()
        self._plugins_by_id.clear()

        # Buscar subcarpetas con plugin.json
        for entry in sorted(os.listdir(self._plugins_dir)):
            plugin_dir = os.path.join(self._plugins_dir, entry)
            if not os.path.isdir(plugin_dir):
                continue

            plugin_json_path = os.path.join(plugin_dir, 'plugin.json')
            if not os.path.exists(plugin_json_path):
                continue

            try:
                plugin = self._load_plugin(entry, plugin_json_path)
                if plugin:
                    self._plugins.append(plugin)
                    self._plugins_by_id[plugin.get_id()] = plugin
                    print(f"[PluginManager] Cargado: {plugin.get_name()} "
                          f"(orden: {plugin.get_order()})")
            except Exception as e:
                print(f"[PluginManager] Error cargando plugin '{entry}': {e}")

        # Ordenar por orden definido o personalizado
        self.sort_plugins()
        print(f"[PluginManager] {len(self._plugins)} plugins cargados")

    def sort_plugins(self, custom_order: list = None):
        """Ordena los plugins cargados según custom_order o su orden por defecto."""
        if custom_order:
            def get_sort_key(p: PluginBase):
                if p.get_id() in custom_order:
                    return (0, custom_order.index(p.get_id()))
                return (1, p.get_order())
            self._plugins.sort(key=get_sort_key)
        else:
            self._plugins.sort(key=lambda p: p.get_order())

    def _load_plugin(self, folder_name: str, json_path: str) -> Optional[PluginBase]:
        """Carga un plugin individual desde su carpeta."""
        with open(json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        module_name = config.get('module', 'plugin')
        class_name = config.get('class', '')

        if not class_name:
            print(f"[PluginManager] plugin.json sin 'class' en {json_path}")
            return None

        # Importar el módulo del plugin
        full_module = f"plugins.{folder_name}.{module_name}"
        module = importlib.import_module(full_module)

        # Obtener la clase del plugin
        plugin_class = getattr(module, class_name)

        # Verificar que hereda de PluginBase
        if not issubclass(plugin_class, PluginBase):
            print(f"[PluginManager] {class_name} no hereda de PluginBase")
            return None

        # Instanciar
        return plugin_class()

    # ---- Acceso a plugins ----

    def get_plugins(self) -> List[PluginBase]:
        """Retorna la lista ordenada de plugins."""
        return self._plugins

    def get_plugin_by_id(self, plugin_id: str) -> Optional[PluginBase]:
        """Retorna un plugin por su ID."""
        return self._plugins_by_id.get(plugin_id)

    def get_plugin_count(self) -> int:
        """Retorna la cantidad de plugins cargados."""
        return len(self._plugins)

    def get_plugin_ids(self) -> List[str]:
        """Retorna la lista de IDs de plugins."""
        return [p.get_id() for p in self._plugins]

    # ---- Sección activa ----

    def get_active_plugin(self) -> Optional[PluginBase]:
        """Retorna el plugin activo actual."""
        return self._active_plugin

    def activate_plugin(self, plugin_id: str) -> Optional[PluginBase]:
        """Activa un plugin por su ID, desactivando el actual."""
        plugin = self.get_plugin_by_id(plugin_id)
        if plugin is None:
            return None

        # Desactivar el actual
        if self._active_plugin and self._active_plugin != plugin:
            self._active_plugin.on_deactivate()

        # Activar el nuevo
        self._active_plugin = plugin
        plugin.on_activate()
        return plugin

    def activate_first(self) -> Optional[PluginBase]:
        """Activa el primer plugin (Portada)."""
        if self._plugins:
            return self.activate_plugin(self._plugins[0].get_id())
        return None

    # ---- Ciclo de vida de datos ----

    def load_all_data(self, agenda_path: str):
        """Carga los datos de todos los plugins desde la agenda."""
        for plugin in self._plugins:
            try:
                plugin.set_agenda_path(agenda_path)
                plugin.load_data(agenda_path)
            except Exception as e:
                print(f"[PluginManager] Error cargando datos de "
                      f"{plugin.get_name()}: {e}")

    def save_all_data(self, agenda_path: str):
        """Guarda los datos de todos los plugins en la agenda."""
        for plugin in self._plugins:
            try:
                plugin.save_data(agenda_path)
            except Exception as e:
                print(f"[PluginManager] Error guardando datos de "
                      f"{plugin.get_name()}: {e}")

    def clear_all_data(self):
        """Limpia los datos de todos los plugins."""
        for plugin in self._plugins:
            plugin.clear_data()

    # ---- Papelera global ----

    def any_plugin_has_trash(self) -> bool:
        """Retorna True si algún plugin tiene items en la papelera."""
        return any(p.has_trash() for p in self._plugins)

    def get_total_trash_count(self) -> int:
        """Retorna el total de items en todas las papeleras."""
        return sum(p.trash_count() for p in self._plugins)

    # ---- Navegación ----

    def get_plugin_index(self, plugin_id: str) -> int:
        """Retorna el índice del plugin en la lista."""
        for i, p in enumerate(self._plugins):
            if p.get_id() == plugin_id:
                return i
        return -1

    def get_next_plugin(self) -> Optional[PluginBase]:
        """Retorna el siguiente plugin en la lista."""
        if not self._active_plugin:
            return self.activate_first()

        idx = self.get_plugin_index(self._active_plugin.get_id())
        if idx < len(self._plugins) - 1:
            return self._plugins[idx + 1]
        return None

    def get_previous_plugin(self) -> Optional[PluginBase]:
        """Retorna el plugin anterior en la lista."""
        if not self._active_plugin:
            return None

        idx = self.get_plugin_index(self._active_plugin.get_id())
        if idx > 0:
            return self._plugins[idx - 1]
        return None
