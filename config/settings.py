# =============================================================================
# Vito Organizer v2.2 - Settings
# Modelo de configuración de la aplicación
# =============================================================================

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class AppearanceSettings:
    """Configuración de apariencia de la agenda."""
    page_style: str = 'lined'          # 'lined', 'grid', 'plain', 'dots'
    page_color: str = '#FFFDD0'        # Color de fondo de las páginas
    binding_type: str = 'rings'        # 'rings', 'spiral', 'clip', 'none'
    ring_color: str = '#B0B0B0'        # Color de las anillas/espiral
    line_color: str = '#B0C4DE'        # Color de las líneas
    margin_color: str = '#E88888'      # Color del margen
    show_margin: bool = True           # Mostrar línea de margen
    line_spacing: int = 24             # Espaciado entre líneas en píxeles
    sidebar_color: str = '#1b4332'      # Color de fondo de la barra lateral
    trash_style: str = 'classic_recycling' # 'classic_recycling', 'metallic_mesh', 'green_dumpster', 'purple_flat', 'black_grid'


@dataclass
class GeneralSettings:
    """Configuración general de la aplicación."""
    last_agenda_path: str = ''         # Última agenda abierta
    sidebar_visible: bool = True       # Sidebar visible al inicio
    sidebar_width: int = 200           # Ancho de la sidebar
    language: str = 'es'               # Idioma (futuro)
    default_agenda_dir: str = ''       # Directorio por defecto para agendas
    last_section: str = 'portada'      # Última sección activa
    window_state: bytes = b''          # Estado de la ventana (geometría)
    tab_order: list = field(default_factory=list) # Orden personalizado de pestañas
    cost_currency: str = 'CLP'         # Unidad de costo predeterminada ('CLP', 'USD', 'EUR')
    logo_path: str = ''                # Ruta al logotipo personalizado de la aplicación
    hidden_sections: list = field(default_factory=list) # Lista de IDs de secciones deshabilitadas/ocultas
    custom_tab_names: dict = field(default_factory=dict) # Nombres personalizados de pestañas {plugin_id: custom_name}

@dataclass
class BackupSettings:
    """Configuración de respaldos de la agenda."""
    backup_dir: str = ''               # Ruta destino predeterminada para el respaldo
    filename_prefix: str = 'respaldo_agenda' # Nombre base del archivo
    compression_format: str = 'ZIP'    # 'ZIP', 'RAR', '7ZIP', 'ARJ'
    split_volumes: bool = False        # Activar división en volúmenes
    volume_size: int = 10              # Tamaño del volumen en MB


@dataclass
class AISettings:
    """Configuración para conexión a Inteligencia Artificial Local (LM Studio / Ollama)."""
    provider: str = 'lm_studio'          # 'lm_studio', 'ollama', 'custom_openai'
    lm_studio_url: str = 'http://localhost:1234/v1'
    ollama_url: str = 'http://localhost:11434'
    custom_url: str = 'http://localhost:8000/v1'
    api_key: str = 'lm-studio'           # Opcional / Token
    selected_model: str = 'qwen2.5-coder-7b-instruct'
    temperature: float = 0.7
    max_tokens: int = 2048
    system_prompt: str = 'Eres el asistente virtual de Vito Organizer. Ayudas al usuario en sus proyectos, laboratorio, componentes, código e inventario.'
    enable_agent: bool = True           # Capacidad de agente (acceso a herramientas de Vito Organizer)


@dataclass
class Settings:
    """Configuración completa de la aplicación."""
    appearance: AppearanceSettings = field(default_factory=AppearanceSettings)
    general: GeneralSettings = field(default_factory=GeneralSettings)
    backup: BackupSettings = field(default_factory=BackupSettings)
    ai: AISettings = field(default_factory=AISettings)

    _config_path: Optional[str] = field(default=None, repr=False)

    @classmethod
    def get_config_dir(cls) -> str:
        """Retorna el directorio de configuración de la aplicación."""
        config_dir = os.path.join(os.path.expanduser('~'), '.config', 'vito-organizer')
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    @classmethod
    def get_config_path(cls) -> str:
        """Retorna la ruta al archivo de configuración."""
        return os.path.join(cls.get_config_dir(), 'settings.json')

    @classmethod
    def load(cls) -> 'Settings':
        """Carga la configuración desde el archivo JSON."""
        config_path = cls.get_config_path()
        settings = cls()
        settings._config_path = config_path

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                if 'appearance' in data:
                    for key, value in data['appearance'].items():
                        if hasattr(settings.appearance, key):
                            setattr(settings.appearance, key, value)

                if 'general' in data:
                    for key, value in data['general'].items():
                        if hasattr(settings.general, key):
                            setattr(settings.general, key, value)

                if 'backup' in data:
                    for key, value in data['backup'].items():
                        if hasattr(settings.backup, key):
                            setattr(settings.backup, key, value)

                if 'ai' in data:
                    for key, value in data['ai'].items():
                        if hasattr(settings.ai, key):
                            setattr(settings.ai, key, value)

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"[Settings] Error cargando configuración: {e}")

        return settings

    def save(self):
        """Guarda la configuración en el archivo JSON."""
        config_path = self._config_path or self.get_config_path()
        data = {
            'appearance': asdict(self.appearance),
            'general': {
                k: v for k, v in asdict(self.general).items()
                if k != 'window_state'
            },
            'backup': asdict(self.backup),
            'ai': asdict(self.ai)
        }

        try:
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"[Settings] Error guardando configuración: {e}")
