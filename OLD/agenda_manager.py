# -*- coding: utf-8 -*-
"""
Vito Organizer — Gestor de Agendas
Maneja la creación, listado y apertura de agendas múltiples.
Cada agenda es una subcarpeta independiente con su propia base de datos y notas.
"""

import os
import re
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QMessageBox,
    QWidget, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor

from svg_icons import svg_to_qicon, icon_new, icon_folder, icon_agenda


# ─────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────

# Directorio base para todas las agendas
BASE_DIR = os.path.join(os.path.expanduser("~"), ".local", "share", "VitoOrganizer")


class AgendaManager:
    """
    Gestiona las operaciones del sistema de archivos para las agendas.
    Crea directorios, lista agendas existentes, valida estructura.
    """

    def __init__(self):
        """Inicializa el gestor y crea el directorio base si no existe."""
        os.makedirs(BASE_DIR, exist_ok=True)

    @staticmethod
    def obtener_directorio_base() -> str:
        """Devuelve la ruta del directorio base de agendas."""
        return BASE_DIR

    def listar_agendas(self) -> list[dict]:
        """
        Lista todas las agendas existentes.
        
        Returns:
            Lista de diccionarios con 'nombre' y 'ruta' de cada agenda.
        """
        agendas = []
        if not os.path.exists(BASE_DIR):
            return agendas

        for nombre in sorted(os.listdir(BASE_DIR)):
            ruta = os.path.join(BASE_DIR, nombre)
            if os.path.isdir(ruta):
                # Verificar que tiene la estructura correcta
                db_path = os.path.join(ruta, "database.sqlite")
                notas_path = os.path.join(ruta, "notas_md")
                if os.path.exists(db_path) or os.path.exists(notas_path):
                    agendas.append({
                        "nombre": nombre,
                        "ruta": ruta,
                        "db_path": db_path,
                        "notas_dir": notas_path
                    })
        return agendas

    def crear_agenda(self, nombre: str) -> dict:
        """
        Crea una nueva agenda con su estructura de directorios.
        
        Args:
            nombre: Nombre de la agenda (se sanitiza para el sistema de archivos).
        
        Returns:
            Diccionario con 'nombre', 'ruta', 'db_path', 'notas_dir'.
        
        Raises:
            ValueError: Si el nombre es inválido o ya existe.
        """
        # Sanitizar nombre para el sistema de archivos
        nombre_limpio = self._sanitizar_nombre(nombre)
        if not nombre_limpio:
            raise ValueError("El nombre de la agenda no es válido.")

        ruta = os.path.join(BASE_DIR, nombre_limpio)
        if os.path.exists(ruta):
            raise ValueError(f"Ya existe una agenda llamada '{nombre_limpio}'.")

        # Crear estructura de directorios
        os.makedirs(ruta, exist_ok=True)
        notas_dir = os.path.join(ruta, "notas_md")
        os.makedirs(notas_dir, exist_ok=True)

        db_path = os.path.join(ruta, "database.sqlite")

        return {
            "nombre": nombre_limpio,
            "ruta": ruta,
            "db_path": db_path,
            "notas_dir": notas_dir
        }

    def eliminar_agenda(self, nombre: str) -> bool:
        """
        Elimina una agenda y todos sus datos.
        
        Args:
            nombre: Nombre de la agenda a eliminar.
        
        Returns:
            True si se eliminó correctamente.
        """
        import shutil
        ruta = os.path.join(BASE_DIR, nombre)
        if os.path.exists(ruta) and os.path.isdir(ruta):
            shutil.rmtree(ruta)
            return True
        return False

    @staticmethod
    def _sanitizar_nombre(nombre: str) -> str:
        """
        Sanitiza un nombre para uso como nombre de directorio.
        Reemplaza espacios por guiones bajos y elimina caracteres especiales.
        """
        # Reemplazar espacios por guiones bajos
        nombre = nombre.strip().replace(" ", "_")
        # Eliminar caracteres no alfanuméricos (excepto guión bajo y guión)
        nombre = re.sub(r'[^\w\-]', '', nombre)
        # Limitar longitud
        return nombre[:50]


# ─────────────────────────────────────────────────────────
# DIÁLOGO SELECTOR DE AGENDA
# ─────────────────────────────────────────────────────────

class AgendaSelectorDialog(QDialog):
    """
    Diálogo de inicio que permite crear o seleccionar una agenda.
    Se muestra al arrancar la aplicación.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manager = AgendaManager()
        self.agenda_seleccionada = None  # Resultado: dict con datos de la agenda
        self._setup_ui()
        self._cargar_agendas()

    def _setup_ui(self):
        """Construye la interfaz del diálogo."""
        self.setWindowTitle("Vito Organizer — Seleccionar Agenda")
        self.setMinimumSize(520, 480)
        self.setModal(True)

        # ── Estilos del diálogo ──
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2C1810, stop:0.5 #1A0F0A, stop:1 #2C1810);
                color: #FDF5E6;
            }
            QLabel {
                color: #FDF5E6;
                background: transparent;
            }
            QLabel#titulo {
                font-size: 22px;
                font-weight: bold;
                color: #D4A574;
                padding: 10px;
            }
            QLabel#subtitulo {
                font-size: 13px;
                color: #A89080;
                padding: 0 10px 10px 10px;
            }
            QListWidget {
                background-color: #FDF5E6;
                color: #4A3728;
                border: 2px solid #8B7355;
                border-radius: 6px;
                font-size: 14px;
                padding: 5px;
                outline: none;
            }
            QListWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #E8D5B7;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #D4A574;
                color: #2C1810;
            }
            QListWidget::item:hover {
                background-color: #F0E0C8;
            }
            QLineEdit {
                background-color: #FDF5E6;
                color: #4A3728;
                border: 2px solid #8B7355;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #D4A574;
            }
            QPushButton {
                background-color: #8B7355;
                color: #FDF5E6;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #A0845C;
            }
            QPushButton:pressed {
                background-color: #6B5535;
            }
            QPushButton#btn_crear {
                background-color: #27AE60;
            }
            QPushButton#btn_crear:hover {
                background-color: #2ECC71;
            }
            QPushButton#btn_abrir {
                background-color: #3498DB;
            }
            QPushButton#btn_abrir:hover {
                background-color: #5DADE2;
            }
            QPushButton#btn_eliminar {
                background-color: #C0392B;
            }
            QPushButton#btn_eliminar:hover {
                background-color: #E74C3C;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(24, 20, 24, 20)

        # ── Título ──
        lbl_titulo = QLabel("Vito Organizer")
        lbl_titulo.setObjectName("titulo")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_titulo)

        lbl_subtitulo = QLabel("Selecciona una agenda existente o crea una nueva")
        lbl_subtitulo.setObjectName("subtitulo")
        lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_subtitulo)

        # ── Separador ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #8B7355; max-height: 1px;")
        layout.addWidget(sep)

        # ── Lista de agendas ──
        lbl_agendas = QLabel("Agendas existentes:")
        lbl_agendas.setStyleSheet("font-size: 13px; font-weight: bold; color: #D4A574;")
        layout.addWidget(lbl_agendas)

        self.lista_agendas = QListWidget()
        self.lista_agendas.setMinimumHeight(150)
        self.lista_agendas.doubleClicked.connect(self._abrir_agenda)
        layout.addWidget(self.lista_agendas)

        # ── Botones de acción para agendas existentes ──
        btn_layout_existentes = QHBoxLayout()

        self.btn_abrir = QPushButton("Abrir Agenda")
        self.btn_abrir.setObjectName("btn_abrir")
        self.btn_abrir.setIcon(svg_to_qicon(icon_folder(), color="#FDF5E6"))
        self.btn_abrir.clicked.connect(self._abrir_agenda)
        btn_layout_existentes.addWidget(self.btn_abrir)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setObjectName("btn_eliminar")
        self.btn_eliminar.clicked.connect(self._eliminar_agenda)
        btn_layout_existentes.addWidget(self.btn_eliminar)

        layout.addLayout(btn_layout_existentes)

        # ── Separador ──
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet("background-color: #8B7355; max-height: 1px;")
        layout.addWidget(sep2)

        # ── Crear nueva agenda ──
        lbl_nueva = QLabel("Crear nueva agenda:")
        lbl_nueva.setStyleSheet("font-size: 13px; font-weight: bold; color: #D4A574;")
        layout.addWidget(lbl_nueva)

        nueva_layout = QHBoxLayout()
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre de la nueva agenda...")
        self.input_nombre.returnPressed.connect(self._crear_agenda)
        nueva_layout.addWidget(self.input_nombre)

        self.btn_crear = QPushButton("Crear")
        self.btn_crear.setObjectName("btn_crear")
        self.btn_crear.setIcon(svg_to_qicon(icon_new(), color="#FDF5E6"))
        self.btn_crear.clicked.connect(self._crear_agenda)
        nueva_layout.addWidget(self.btn_crear)

        layout.addLayout(nueva_layout)

    def _cargar_agendas(self):
        """Carga la lista de agendas existentes en el QListWidget."""
        self.lista_agendas.clear()
        agendas = self.manager.listar_agendas()

        if not agendas:
            item = QListWidgetItem("No hay agendas creadas. ¡Crea tu primera agenda!")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#A89080"))
            self.lista_agendas.addItem(item)
            return

        for agenda in agendas:
            item = QListWidgetItem(svg_to_qicon(icon_agenda(), color="#8B7355"),
                                   agenda["nombre"])
            item.setData(Qt.ItemDataRole.UserRole, agenda)
            item.setSizeHint(QSize(0, 42))
            self.lista_agendas.addItem(item)

    def _abrir_agenda(self):
        """Abre la agenda seleccionada."""
        item = self.lista_agendas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecciona una agenda de la lista.")
            return

        agenda_data = item.data(Qt.ItemDataRole.UserRole)
        if not agenda_data:
            return

        self.agenda_seleccionada = agenda_data
        self.accept()

    def _crear_agenda(self):
        """Crea una nueva agenda y la abre."""
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(self, "Aviso", "Escribe un nombre para la nueva agenda.")
            return

        try:
            agenda_data = self.manager.crear_agenda(nombre)
            self.agenda_seleccionada = agenda_data
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def _eliminar_agenda(self):
        """Elimina la agenda seleccionada previa confirmación."""
        item = self.lista_agendas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecciona una agenda para eliminar.")
            return

        agenda_data = item.data(Qt.ItemDataRole.UserRole)
        if not agenda_data:
            return

        nombre = agenda_data["nombre"]
        respuesta = QMessageBox.question(
            self, "Confirmar eliminación",
            f"¿Estás seguro de eliminar la agenda '{nombre}'?\n\n"
            "Se borrarán TODOS los datos permanentemente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            if self.manager.eliminar_agenda(nombre):
                self._cargar_agendas()
                QMessageBox.information(self, "Eliminada", f"Agenda '{nombre}' eliminada.")
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar la agenda.")
