# -*- coding: utf-8 -*-
"""
Vito Organizer — Punto de Entrada
Aplicación de agenda personal esqueumórfica inspirada en Lotus Organizer.

Tecnologías: Python 3, PyQt6, SQLite3
Autor: Generado con Vito Organizer Builder
"""

import sys
import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from agenda_manager import AgendaSelectorDialog
from app_window import MainWindow
from ui_builder import crear_estilo_global, crear_estilo_toolbar_papel


def main():
    """Función principal de la aplicación."""
    # ── Crear aplicación Qt ──
    app = QApplication(sys.argv)
    app.setApplicationName("Vito Organizer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VitoOrganizer")

    # ── Fuente global ──
    fuente = QFont("Segoe UI", 11)
    fuente.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(fuente)

    # ── Estilo global QSS ──
    app.setStyleSheet(crear_estilo_global() + crear_estilo_toolbar_papel())

    # ── Diálogo selector de agenda ──
    selector = AgendaSelectorDialog()
    resultado = selector.exec()

    if resultado != AgendaSelectorDialog.DialogCode.Accepted:
        # Usuario canceló: salir de la aplicación
        sys.exit(0)

    agenda_data = selector.agenda_seleccionada
    if not agenda_data:
        sys.exit(0)

    # ── Crear y mostrar la ventana principal ──
    ventana = MainWindow(agenda_data)
    ventana.showMaximized()

    # ── Ejecutar el bucle de eventos ──
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
