# =============================================================================
# Vito Organizer v2.2 - Data Store
# Persistencia de datos en JSON
# =============================================================================

import json
import os
from typing import Any, Dict, Optional
from datetime import datetime


class DataStore:
    """Gestiona la persistencia de datos en archivos JSON."""

    @staticmethod
    def load(filepath: str) -> Dict[str, Any]:
        """Carga datos desde un archivo JSON.

        Args:
            filepath: Ruta al archivo JSON.

        Returns:
            Diccionario con los datos. Vacío si el archivo no existe.
        """
        if not os.path.exists(filepath):
            return {}

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[DataStore] Error leyendo {filepath}: {e}")
            # Intentar backup
            backup = filepath + '.bak'
            if os.path.exists(backup):
                try:
                    with open(backup, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception:
                    pass
            return {}

    @staticmethod
    def save(filepath: str, data: Dict[str, Any]):
        """Guarda datos en un archivo JSON.

        Crea un backup del archivo existente antes de sobreescribir.

        Args:
            filepath: Ruta al archivo JSON.
            data: Diccionario con los datos a guardar.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Crear backup si el archivo ya existe
        if os.path.exists(filepath):
            backup = filepath + '.bak'
            try:
                os.replace(filepath, backup)
            except OSError:
                pass

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        except OSError as e:
            print(f"[DataStore] Error guardando {filepath}: {e}")
            raise

    @staticmethod
    def ensure_dir(path: str):
        """Crea un directorio si no existe."""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def get_plugin_data_path(agenda_path: str, plugin_id: str) -> str:
        """Retorna la ruta al archivo de datos de un plugin.

        Args:
            agenda_path: Ruta a la carpeta de la agenda.
            plugin_id: ID del plugin (e.g., 'calendario').

        Returns:
            Ruta al archivo data.json del plugin.
        """
        plugin_dir = os.path.join(agenda_path, plugin_id)
        os.makedirs(plugin_dir, exist_ok=True)
        return os.path.join(plugin_dir, 'data.json')

    @staticmethod
    def get_trash_data_path(agenda_path: str) -> str:
        """Retorna la ruta al archivo de datos de la papelera global."""
        trash_dir = os.path.join(agenda_path, 'trash')
        os.makedirs(trash_dir, exist_ok=True)
        return os.path.join(trash_dir, 'data.json')
