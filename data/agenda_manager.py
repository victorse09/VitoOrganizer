# =============================================================================
# Vito Organizer v2.2 - Agenda Manager
# Gestión de agendas (crear, abrir, guardar, cerrar)
# =============================================================================

import os
import json
import shutil
from typing import Optional, Dict, Any
from datetime import datetime

from data.data_store import DataStore


class AgendaManager:
    """Gestiona el ciclo de vida de las agendas."""

    AGENDA_METADATA_FILE = 'agenda.json'
    PLUGIN_FOLDERS = ['portada', 'calendario', 'cumpleanos', 'tareas',
                      'notas', 'planificador', 'trash']

    def __init__(self):
        self._current_path: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
        self._is_modified: bool = False

    # ---- Propiedades ----

    @property
    def current_path(self) -> Optional[str]:
        """Ruta de la agenda actual."""
        return self._current_path

    @property
    def is_open(self) -> bool:
        """Indica si hay una agenda abierta."""
        return self._current_path is not None

    @property
    def is_modified(self) -> bool:
        """Indica si la agenda tiene cambios sin guardar."""
        return self._is_modified

    @is_modified.setter
    def is_modified(self, value: bool):
        self._is_modified = value

    @property
    def name(self) -> str:
        """Nombre de la agenda actual."""
        return self._metadata.get('name', 'Sin título')

    # ---- Operaciones de agenda ----

    def create(self, name: str, path: str) -> bool:
        """Crea una nueva agenda.

        Args:
            name: Nombre de la agenda.
            path: Ruta donde crear la carpeta de la agenda.

        Returns:
            True si se creó correctamente.
        """
        try:
            # Crear directorio principal
            os.makedirs(path, exist_ok=True)

            # Crear subdirectorios para cada plugin
            for folder in self.PLUGIN_FOLDERS:
                os.makedirs(os.path.join(path, folder), exist_ok=True)

            # Crear metadata
            self._metadata = {
                'name': name,
                'version': '2.0',
                'created_at': datetime.now().isoformat(),
                'modified_at': datetime.now().isoformat(),
                'appearance': {
                    'page_style': 'lined',
                    'page_color': '#FFFDD0',
                    'binding_type': 'rings',
                }
            }

            # Guardar metadata
            metadata_path = os.path.join(path, self.AGENDA_METADATA_FILE)
            DataStore.save(metadata_path, self._metadata)

            # Crear archivos data.json vacíos para cada plugin
            for folder in self.PLUGIN_FOLDERS:
                data_path = os.path.join(path, folder, 'data.json')
                if not os.path.exists(data_path):
                    DataStore.save(data_path, {})

            self._current_path = path
            self._is_modified = False

            print(f"[AgendaManager] Agenda creada: '{name}' en {path}")
            return True

        except OSError as e:
            print(f"[AgendaManager] Error creando agenda: {e}")
            return False

    def open(self, path: str) -> bool:
        """Abre una agenda existente.

        Args:
            path: Ruta a la carpeta de la agenda.

        Returns:
            True si se abrió correctamente.
        """
        metadata_path = os.path.join(path, self.AGENDA_METADATA_FILE)

        if not os.path.exists(metadata_path):
            print(f"[AgendaManager] No se encontró agenda en {path}")
            return False

        try:
            self._metadata = DataStore.load(metadata_path)
            self._current_path = path
            self._is_modified = False

            print(f"[AgendaManager] Agenda abierta: '{self.name}'")
            return True

        except Exception as e:
            print(f"[AgendaManager] Error abriendo agenda: {e}")
            return False

    def save(self) -> bool:
        """Guarda la agenda actual."""
        if not self._current_path:
            return False

        try:
            # Actualizar timestamp
            self._metadata['modified_at'] = datetime.now().isoformat()

            # Guardar metadata
            metadata_path = os.path.join(
                self._current_path, self.AGENDA_METADATA_FILE)
            DataStore.save(metadata_path, self._metadata)

            self._is_modified = False
            print(f"[AgendaManager] Agenda guardada: '{self.name}'")
            return True

        except Exception as e:
            print(f"[AgendaManager] Error guardando agenda: {e}")
            return False

    def save_as(self, new_path: str) -> bool:
        """Guarda la agenda en una nueva ubicación.

        Args:
            new_path: Nueva ruta para la agenda.

        Returns:
            True si se guardó correctamente.
        """
        if not self._current_path:
            return False

        try:
            # Copiar toda la carpeta
            if os.path.exists(new_path):
                shutil.rmtree(new_path)
            shutil.copytree(self._current_path, new_path)

            self._current_path = new_path
            return self.save()

        except Exception as e:
            print(f"[AgendaManager] Error en guardar como: {e}")
            return False

    def close(self):
        """Cierra la agenda actual."""
        if self._current_path:
            print(f"[AgendaManager] Agenda cerrada: '{self.name}'")
        self._current_path = None
        self._metadata = {}
        self._is_modified = False

    # ---- Metadata ----

    def get_metadata(self) -> Dict[str, Any]:
        """Retorna la metadata de la agenda."""
        return self._metadata.copy()

    def set_metadata(self, key: str, value: Any):
        """Establece un valor en la metadata."""
        self._metadata[key] = value
        self._is_modified = True

    def get_appearance(self) -> Dict[str, Any]:
        """Retorna la configuración de apariencia de la agenda."""
        return self._metadata.get('appearance', {
            'page_style': 'lined',
            'page_color': '#FFFDD0',
            'binding_type': 'rings',
        })

    def set_appearance(self, appearance: Dict[str, Any]):
        """Establece la configuración de apariencia."""
        self._metadata['appearance'] = appearance
        self._is_modified = True

    # ---- Validación ----

    @staticmethod
    def is_valid_agenda(path: str) -> bool:
        """Verifica si una ruta contiene una agenda válida."""
        return os.path.exists(os.path.join(path, AgendaManager.AGENDA_METADATA_FILE))
