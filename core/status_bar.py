# =============================================================================
# Vito Organizer v2.2 - Status Bar
# Barra de estado de la aplicación
# =============================================================================

from PyQt6.QtWidgets import QStatusBar, QLabel
from PyQt6.QtCore import Qt
from core.version import APP_VERSION


class AppStatusBar(QStatusBar):
    """Barra de estado de Vito Organizer."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Label de sección activa
        self._section_label = QLabel("Sección: ---")
        self._section_label.setStyleSheet("QLabel { color: #a6adc8; padding: 0 8px; }")
        self.addWidget(self._section_label)

        # Label de agenda
        self._agenda_label = QLabel("")
        self._agenda_label.setStyleSheet("QLabel { color: #a6adc8; padding: 0 8px; }")
        self.addWidget(self._agenda_label, 1)

        # Label de conectividad (derecha)
        self._connectivity_label = QLabel("Red: Local (Independiente)")
        self._connectivity_label.setStyleSheet("QLabel { color: #a6adc8; padding: 0 8px; }")
        self.addPermanentWidget(self._connectivity_label)

        # Label de estado (derecha)
        self._status_label = QLabel("Listo")
        self._status_label.setStyleSheet("QLabel { color: #6c7086; padding: 0 8px; }")
        self.addPermanentWidget(self._status_label)

        # Label de versión (derecha)
        self._version_label = QLabel(f"v{APP_VERSION}")
        self._version_label.setStyleSheet("QLabel { color: #585b70; padding: 0 8px; }")
        self.addPermanentWidget(self._version_label)

    def set_section(self, name: str):
        """Actualiza la sección activa mostrada."""
        self._section_label.setText(f"Sección: {name}")

    def set_agenda(self, name: str):
        """Actualiza el nombre de la agenda mostrada."""
        self._agenda_label.setText(f"Agenda: {name}")

    def set_connectivity_mode(self, mode: str, detail: str = ""):
        """Establece el indicador de conectividad de red.
        
        mode: 'local', 'server', 'client'
        """
        if mode == 'local':
            self._connectivity_label.setText("Red: Local (Independiente)")
            self._connectivity_label.setStyleSheet("QLabel { color: #a6adc8; padding: 0 8px; }")
        elif mode == 'server':
            self._connectivity_label.setText(f"Red: Servidor (Activo: {detail})" if detail else "Red: Servidor (Activo)")
            self._connectivity_label.setStyleSheet("QLabel { color: #eed49f; padding: 0 8px; font-weight: bold; }")
        elif mode == 'client':
            self._connectivity_label.setText(f"Red: Cliente (Sinc. con {detail})" if detail else "Red: Cliente (Sincronizado)")
            self._connectivity_label.setStyleSheet("QLabel { color: #89b4fa; padding: 0 8px; font-weight: bold; }")

    def set_status(self, text: str, timeout: int = 0):
        """Muestra un mensaje de estado temporal."""
        if timeout > 0:
            self.showMessage(text, timeout)
        else:
            self._status_label.setText(text)

    def set_modified(self, modified: bool):
        """Indica si hay cambios sin guardar."""
        if modified:
            self._status_label.setText("● Modificado")
            self._status_label.setStyleSheet(
                "QLabel { color: #f9e2af; padding: 0 8px; }")
        else:
            self._status_label.setText("Listo")
            self._status_label.setStyleSheet(
                "QLabel { color: #6c7086; padding: 0 8px; }")
