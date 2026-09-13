# =============================================================================
# Vito Organizer v2.2 - Main Entry Point
# Punto de entrada de la aplicación
# =============================================================================

import sys

from core.app import VitoOrganizerApp
from core.main_window import MainWindow

def main():
    """Punto de entrada principal."""
    app = VitoOrganizerApp(sys.argv)
    
    window = MainWindow(app)
    
    # El estado de maximizado/tamaño se maneja dentro de MainWindow 
    # restaurando el state guardado, o showMaximized si es la primera vez.
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
