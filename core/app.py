# =============================================================================
# Vito Organizer v2.2 - App Wrapper
# Wrapper para QApplication con configuración global
# =============================================================================

import sys
import signal
from PyQt6.QtWidgets import QApplication

from config.theme import Theme


class VitoOrganizerApp(QApplication):
    """Aplicación principal de Vito Organizer."""

    def __init__(self, argv):
        super().__init__(argv)
        
        self.setApplicationName("Vito Organizer")
        self.setApplicationVersion("2.0")
        
        # Permitir que Ctrl+C (SIGINT) cierre la aplicación en terminal
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        
        # Aplicar tema oscuro global
        Theme.apply(self)
