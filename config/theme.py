# =============================================================================
# Vito Organizer v2.2 - Theme Manager
# Gestión del tema clásico retro y paleta de colores (Lotus Organizer style)
# =============================================================================

import os
from PyQt6.QtGui import QPalette, QColor, QFont
from PyQt6.QtWidgets import QApplication


class Theme:
    """Gestiona el tema visual de la aplicación."""

    # --- Paleta de colores (Catppuccin Macchiato) ---
    COLORS = {
        # Base (Macchiato)
        'base': '#24273a',
        'mantle': '#1e2030',
        'crust': '#181825',
        'surface0': '#363a4f',
        'surface1': '#494d64',
        'surface2': '#5b6078',

        # Texto
        'text': '#cad3f5',
        'subtext1': '#b8c0e0',
        'subtext0': '#a5adcb',
        'overlay2': '#939ab7',
        'overlay1': '#8087a2',
        'overlay0': '#6e738d',

        # Acentos (Macchiato)
        'blue': '#8aadf4',
        'lavender': '#b7bdf8',
        'sapphire': '#7dc4e4',
        'sky': '#91d7e3',
        'teal': '#8bd5ca',
        'green': '#a6da95',
        'yellow': '#eed49f',
        'peach': '#f5a97f',
        'maroon': '#ee99a0',
        'red': '#ed8796',
        'mauve': '#c6a0f6',
        'pink': '#f5bde6',
        'flamingo': '#f0c6c6',
        'rosewater': '#f4dbd6',

        # Colores de pestañas de sección (vivid)
        'tab_portada': '#8aadf4',
        'tab_calendario': '#eed49f',
        'tab_cumpleanos': '#f5bde6',
        'tab_tareas': '#a6da95',
        'tab_notas': '#c6a0f6',
        'tab_planificador': '#f5a97f',

        # Colores de página de agenda
        'page_cream': '#FFFDD0',
        'page_white': '#FFFFF0',
        'page_yellow': '#FFFFE0',
        'page_green': '#F0FFF0',
        'page_line': '#B0C4DE',
        'page_margin': '#E88888',
        'page_grid': '#C8D8E8',
    }

    # --- Colores de prioridad ---
    PRIORITY_COLORS = {
        'high': '#ed8796',
        'medium': '#eed49f',
        'low': '#a6da95',
    }

    @classmethod
    def get_qss_path(cls) -> str:
        """Retorna la ruta al archivo QSS del tema oscuro."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, 'resources', 'styles', 'dark_theme.qss')

    @classmethod
    def load_stylesheet(cls) -> str:
        """Carga y retorna el stylesheet QSS."""
        qss_path = cls.get_qss_path()
        try:
            with open(qss_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"[Theme] Warning: QSS file not found at {qss_path}")
            return ""

    @classmethod
    def apply(cls, app: QApplication):
        """Aplica el tema oscuro Catppuccin Macchiato a la aplicación."""
        # Cargar stylesheet
        stylesheet = cls.load_stylesheet()
        app.setStyleSheet(stylesheet)

        # Configurar paleta oscura
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(cls.hex('base')))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(cls.hex('text')))
        palette.setColor(QPalette.ColorRole.Base, QColor(cls.hex('mantle')))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(cls.hex('crust')))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(cls.hex('surface0')))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(cls.hex('text')))
        palette.setColor(QPalette.ColorRole.Text, QColor(cls.hex('text')))
        palette.setColor(QPalette.ColorRole.Button, QColor(cls.hex('surface0')))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(cls.hex('text')))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(cls.hex('red')))
        palette.setColor(QPalette.ColorRole.Link, QColor(cls.hex('blue')))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(cls.hex('blue')))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(cls.hex('base')))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(cls.hex('overlay0')))

        # Sombras y bordes
        palette.setColor(QPalette.ColorRole.Light, QColor(cls.hex('surface2')))
        palette.setColor(QPalette.ColorRole.Midlight, QColor(cls.hex('surface1')))
        palette.setColor(QPalette.ColorRole.Dark, QColor(cls.hex('crust')))
        palette.setColor(QPalette.ColorRole.Mid, QColor(cls.hex('surface0')))
        palette.setColor(QPalette.ColorRole.Shadow, QColor('#000000'))

        app.setPalette(palette)

        # Configurar fuente (classic feel)
        font = QFont("Segoe UI", 10)
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        app.setFont(font)

    @classmethod
    def color(cls, name: str) -> QColor:
        """Retorna un QColor por nombre."""
        hex_color = cls.COLORS.get(name, '#FFFFFF')
        return QColor(hex_color)

    @classmethod
    def hex(cls, name: str) -> str:
        """Retorna el código hex de un color por nombre."""
        return cls.COLORS.get(name, '#FFFFFF')
