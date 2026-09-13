# -*- coding: utf-8 -*-
"""
tab_instruments.py — Módulo de Control de Instrumentos para Vito Organizer.

Proporciona una interfaz CRUD completa para gestionar instrumentos de medición
y laboratorio. Incluye tabla con estados coloreados, formulario con selector
de fecha de calibración y combo de estados predefinidos.

Autor: Vito Organizer
"""

from typing import Any, Optional

from PyQt6.QtCore import (
    QAbstractTableModel,
    QDate,
    QModelIndex,
    QSortFilterProxyModel,
    QVariant,
    Qt,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database import Database
from svg_icons import (
    icon_delete,
    icon_edit,
    icon_new,
    icon_save,
    icon_search,
    svg_to_qicon,
)

# =============================================================================
# Constantes de estilo
# =============================================================================

# Color de fondo papel/crema
COLOR_FONDO = "#FDF5E6"
# Fila alterna más oscura
COLOR_FILA_ALTERNA = "#F5ECD7"
# Encabezado de tabla
COLOR_ENCABEZADO = "#E8D5B7"
# Color de selección
COLOR_SELECCION = "#D4A574"
# Color de texto oscuro marrón
COLOR_TEXTO_OSCURO = "#4A3728"
# Color de iconos
COLOR_ICONOS = "#4A3728"

# Colores para los estados de instrumentos
COLORES_ESTADO = {
    "Operativo": "#27AE60",           # Verde — funcionando correctamente
    "En reparación": "#E74C3C",       # Rojo — fuera de servicio
    "Pendiente calibración": "#E67E22",  # Naranja — requiere atención
    "Retirado": "#95A5A6",            # Gris — dado de baja
}

# Estados disponibles para el combo
ESTADOS_INSTRUMENTO = [
    "Operativo",
    "En reparación",
    "Pendiente calibración",
    "Retirado",
]

# Hoja de estilos para la tabla
ESTILO_TABLA = f"""
    QTableView {{
        background-color: {COLOR_FONDO};
        alternate-background-color: {COLOR_FILA_ALTERNA};
        border: 1px solid #C4A882;
        border-radius: 4px;
        gridline-color: #D5C4A1;
        color: {COLOR_TEXTO_OSCURO};
        font-size: 13px;
        selection-background-color: {COLOR_SELECCION};
        selection-color: #2C1810;
    }}
    QHeaderView::section {{
        background-color: {COLOR_ENCABEZADO};
        color: {COLOR_TEXTO_OSCURO};
        padding: 6px 8px;
        border: none;
        border-bottom: 2px solid #C4A882;
        border-right: 1px solid #D5C4A1;
        font-weight: bold;
        font-size: 13px;
    }}
    QTableView::item {{
        padding: 4px 8px;
    }}
"""

ESTILO_BUSQUEDA = f"""
    QLineEdit {{
        background-color: {COLOR_FONDO};
        border: 1px solid #C4A882;
        border-radius: 6px;
        padding: 6px 10px 6px 30px;
        font-size: 13px;
        color: {COLOR_TEXTO_OSCURO};
    }}
    QLineEdit:focus {{
        border: 2px solid {COLOR_SELECCION};
    }}
"""

ESTILO_TOOLBAR = f"""
    QWidget {{
        background-color: {COLOR_FONDO};
    }}
    QPushButton {{
        background-color: {COLOR_ENCABEZADO};
        color: {COLOR_TEXTO_OSCURO};
        border: 1px solid #C4A882;
        border-radius: 5px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: bold;
    }}
    QPushButton:hover {{
        background-color: {COLOR_SELECCION};
    }}
    QPushButton:pressed {{
        background-color: #C49A6C;
    }}
"""

ESTILO_DIALOGO = f"""
    QDialog {{
        background-color: {COLOR_FONDO};
    }}
    QLabel {{
        color: {COLOR_TEXTO_OSCURO};
        font-size: 13px;
    }}
    QLineEdit, QDateEdit, QComboBox {{
        background-color: white;
        border: 1px solid #C4A882;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 13px;
        color: {COLOR_TEXTO_OSCURO};
    }}
    QComboBox::drop-down {{
        border-left: 1px solid #C4A882;
        width: 24px;
    }}
    QTextEdit {{
        background-color: white;
        border: 1px solid #C4A882;
        border-radius: 4px;
        padding: 4px;
        font-size: 13px;
        color: {COLOR_TEXTO_OSCURO};
    }}
    QDialogButtonBox QPushButton {{
        background-color: {COLOR_ENCABEZADO};
        color: {COLOR_TEXTO_OSCURO};
        border: 1px solid #C4A882;
        border-radius: 5px;
        padding: 6px 20px;
        font-size: 12px;
        font-weight: bold;
        min-width: 80px;
    }}
    QDialogButtonBox QPushButton:hover {{
        background-color: {COLOR_SELECCION};
    }}
"""


# =============================================================================
# Modelo de datos para la tabla de instrumentos
# =============================================================================
class InstrumentModel(QAbstractTableModel):
    """
    Modelo personalizado para la tabla de instrumentos.

    Gestiona los datos de instrumentos proporcionando acceso por filas/columnas,
    ordenamiento y formato de visualización con estados coloreados.
    """

    # Nombres de las columnas en español
    COLUMNAS = ["ID", "Instrumento", "Modelo", "Última Calibración", "Estado", "Notas"]
    # Claves correspondientes en el diccionario de datos
    CLAVES = ["id", "name", "model", "last_calibration", "status", "notes"]

    def __init__(self, datos: list[dict] | None = None, parent=None) -> None:
        """Inicializa el modelo con los datos proporcionados."""
        super().__init__(parent)
        self._datos: list[dict] = datos or []

    # ---- Métodos obligatorios de QAbstractTableModel ----

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Devuelve el número de filas (instrumentos)."""
        return len(self._datos)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Devuelve el número de columnas."""
        return len(self.COLUMNAS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Devuelve el dato correspondiente a la celda y rol indicados.

        La columna de estado muestra texto coloreado según el valor:
        - Operativo: verde
        - En reparación: rojo
        - Pendiente calibración: naranja
        - Retirado: gris
        """
        if not index.isValid() or not (0 <= index.row() < len(self._datos)):
            return QVariant()

        instrumento = self._datos[index.row()]
        clave = self.CLAVES[index.column()]
        valor = instrumento.get(clave, "")

        if role == Qt.ItemDataRole.DisplayRole:
            return str(valor) if valor is not None else ""

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Centrar las columnas de fecha y estado
            if clave in ("last_calibration", "status"):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ForegroundRole:
            # Color especial para la columna de estado
            if clave == "status":
                color_estado = COLORES_ESTADO.get(str(valor), COLOR_TEXTO_OSCURO)
                return QColor(color_estado)
            return QColor(COLOR_TEXTO_OSCURO)

        elif role == Qt.ItemDataRole.FontRole:
            fuente = QFont()
            fuente.setPointSize(10)
            # Nombre del instrumento en negrita
            if clave == "name":
                fuente.setBold(True)
            # Estado también en negrita para mejor visibilidad del color
            if clave == "status":
                fuente.setBold(True)
            return fuente

        return QVariant()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        """Devuelve los encabezados de columna."""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.COLUMNAS[section]
        return QVariant()

    # ---- Métodos para actualizar datos ----

    def actualizar_datos(self, datos: list[dict]) -> None:
        """Reemplaza todos los datos del modelo y notifica a las vistas."""
        self.beginResetModel()
        self._datos = datos
        self.endResetModel()

    def obtener_instrumento(self, fila: int) -> dict | None:
        """Devuelve el diccionario del instrumento en la fila indicada."""
        if 0 <= fila < len(self._datos):
            return self._datos[fila]
        return None


# =============================================================================
# Diálogo para crear/editar instrumentos
# =============================================================================
class InstrumentDialog(QDialog):
    """
    Diálogo modal para crear o editar un instrumento.

    Contiene campos para nombre, modelo, fecha de última calibración,
    estado (con combo predefinido) y notas adicionales.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        datos: dict | None = None,
        titulo: str = "Nuevo Instrumento",
    ) -> None:
        """
        Inicializa el diálogo.

        Args:
            parent: Widget padre.
            datos: Diccionario con datos existentes para edición (o None para nuevo).
            titulo: Título de la ventana del diálogo.
        """
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(440)
        self.setStyleSheet(ESTILO_DIALOGO)
        self._configurar_interfaz(datos)

    def _configurar_interfaz(self, datos: dict | None) -> None:
        """Construye el formulario del diálogo."""
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Campo: Nombre del instrumento ---
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Nombre del instrumento...")
        self.campo_nombre.setMaxLength(200)
        layout.addRow("Instrumento:", self.campo_nombre)

        # --- Campo: Modelo ---
        self.campo_modelo = QLineEdit()
        self.campo_modelo.setPlaceholderText("Modelo o referencia...")
        self.campo_modelo.setMaxLength(200)
        layout.addRow("Modelo:", self.campo_modelo)

        # --- Campo: Última calibración (selector de fecha) ---
        self.campo_calibracion = QDateEdit()
        self.campo_calibracion.setCalendarPopup(True)
        self.campo_calibracion.setDisplayFormat("yyyy-MM-dd")
        self.campo_calibracion.setDate(QDate.currentDate())
        layout.addRow("Última Calibración:", self.campo_calibracion)

        # --- Campo: Estado (combo con opciones predefinidas) ---
        self.campo_estado = QComboBox()
        self.campo_estado.addItems(ESTADOS_INSTRUMENTO)
        layout.addRow("Estado:", self.campo_estado)

        # --- Campo: Notas adicionales ---
        self.campo_notas = QTextEdit()
        self.campo_notas.setPlaceholderText("Notas o comentarios adicionales...")
        self.campo_notas.setMaximumHeight(120)
        layout.addRow("Notas:", self.campo_notas)

        # --- Botones de acción ---
        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("Guardar")
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setIcon(
            svg_to_qicon(icon_save(), size=18, color=COLOR_ICONOS)
        )
        self.botones.accepted.connect(self._validar_y_aceptar)
        self.botones.rejected.connect(self.reject)
        layout.addRow(self.botones)

        # --- Pre-cargar datos si estamos editando ---
        if datos:
            self.campo_nombre.setText(str(datos.get("name", "")))
            self.campo_modelo.setText(str(datos.get("model", "")))

            # Parsear la fecha de calibración
            fecha_str = str(datos.get("last_calibration", ""))
            fecha = QDate.fromString(fecha_str, "yyyy-MM-dd")
            if fecha.isValid():
                self.campo_calibracion.setDate(fecha)

            # Seleccionar el estado actual en el combo
            estado = str(datos.get("status", ""))
            indice_estado = self.campo_estado.findText(estado)
            if indice_estado >= 0:
                self.campo_estado.setCurrentIndex(indice_estado)

            self.campo_notas.setPlainText(str(datos.get("notes", "")))

    def _validar_y_aceptar(self) -> None:
        """Valida que los campos obligatorios estén completos antes de aceptar."""
        nombre = self.campo_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(
                self,
                "Campo requerido",
                "El nombre del instrumento es obligatorio.",
            )
            self.campo_nombre.setFocus()
            return
        self.accept()

    def obtener_datos(self) -> dict:
        """
        Devuelve los datos ingresados en el formulario.

        Returns:
            Diccionario con las claves: name, model, last_calibration, status, notes.
        """
        return {
            "name": self.campo_nombre.text().strip(),
            "model": self.campo_modelo.text().strip(),
            "last_calibration": self.campo_calibracion.date().toString("yyyy-MM-dd"),
            "status": self.campo_estado.currentText(),
            "notes": self.campo_notas.toPlainText().strip(),
        }


# =============================================================================
# Widget principal de la pestaña de Instrumentos
# =============================================================================
class TabInstruments(QWidget):
    """
    Pestaña principal de Control de Instrumentos.

    Proporciona una interfaz completa para gestionar instrumentos de medición,
    incluyendo seguimiento de calibración y estado operativo.
    """

    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        """
        Inicializa la pestaña de instrumentos.

        Args:
            db: Instancia de la clase Database para operaciones CRUD.
            parent: Widget padre opcional.
        """
        super().__init__(parent)
        self.db = db
        self._configurar_interfaz()
        self._cargar_datos()

    def _configurar_interfaz(self) -> None:
        """Construye toda la interfaz de la pestaña."""
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_FONDO}; }}")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(12, 12, 12, 12)
        layout_principal.setSpacing(8)

        # --- Barra de herramientas ---
        self._crear_toolbar(layout_principal)

        # --- Barra de búsqueda ---
        self._crear_barra_busqueda(layout_principal)

        # --- Tabla de instrumentos ---
        self._crear_tabla(layout_principal)

    def _crear_toolbar(self, layout: QVBoxLayout) -> None:
        """Crea la barra de herramientas con botones de acción."""
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(ESTILO_TOOLBAR)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        # Botón: Nuevo instrumento
        self.btn_nuevo = QPushButton("  Nuevo")
        self.btn_nuevo.setIcon(svg_to_qicon(icon_new(), size=20, color=COLOR_ICONOS))
        self.btn_nuevo.clicked.connect(self._nuevo_instrumento)
        self.btn_nuevo.setToolTip("Registrar un nuevo instrumento")
        toolbar_layout.addWidget(self.btn_nuevo)

        # Botón: Editar instrumento seleccionado
        self.btn_editar = QPushButton("  Editar")
        self.btn_editar.setIcon(svg_to_qicon(icon_edit(), size=20, color=COLOR_ICONOS))
        self.btn_editar.clicked.connect(self._editar_instrumento)
        self.btn_editar.setToolTip("Editar el instrumento seleccionado")
        toolbar_layout.addWidget(self.btn_editar)

        # Botón: Eliminar instrumento seleccionado
        self.btn_eliminar = QPushButton("  Eliminar")
        self.btn_eliminar.setIcon(svg_to_qicon(icon_delete(), size=20, color=COLOR_ICONOS))
        self.btn_eliminar.clicked.connect(self._eliminar_instrumento)
        self.btn_eliminar.setToolTip("Eliminar el instrumento seleccionado")
        toolbar_layout.addWidget(self.btn_eliminar)

        # Espaciador
        toolbar_layout.addStretch()

        toolbar_widget.setLayout(toolbar_layout)
        layout.addWidget(toolbar_widget)

    def _crear_barra_busqueda(self, layout: QVBoxLayout) -> None:
        """Crea la barra de búsqueda con filtrado en tiempo real."""
        contenedor_busqueda = QHBoxLayout()
        contenedor_busqueda.setSpacing(8)

        # Icono de búsqueda
        lbl_icono = QLabel()
        lbl_icono.setPixmap(
            svg_to_qicon(icon_search(), size=20, color=COLOR_ICONOS).pixmap(20, 20)
        )
        lbl_icono.setFixedSize(24, 24)
        contenedor_busqueda.addWidget(lbl_icono)

        # Campo de texto de búsqueda
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Buscar instrumentos...")
        self.campo_busqueda.setClearButtonEnabled(True)
        self.campo_busqueda.setStyleSheet(ESTILO_BUSQUEDA)
        self.campo_busqueda.textChanged.connect(self._filtrar_instrumentos)
        contenedor_busqueda.addWidget(self.campo_busqueda)

        layout.addLayout(contenedor_busqueda)

    def _crear_tabla(self, layout: QVBoxLayout) -> None:
        """Crea la tabla de instrumentos con modelo y proxy de ordenamiento."""
        # Modelo de datos
        self.modelo = InstrumentModel()

        # Proxy para ordenamiento
        self.proxy_modelo = QSortFilterProxyModel()
        self.proxy_modelo.setSourceModel(self.modelo)
        self.proxy_modelo.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_modelo.setFilterKeyColumn(-1)

        # Vista de tabla
        self.tabla = QTableView()
        self.tabla.setModel(self.proxy_modelo)
        self.tabla.setStyleSheet(ESTILO_TABLA)

        # Configuración visual
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.tabla.setSortingEnabled(True)
        self.tabla.setShowGrid(False)
        self.tabla.verticalHeader().setVisible(False)

        # Ocultar la columna ID (columna 0)
        self.tabla.setColumnHidden(0, True)

        # Ajustar anchos de columna
        header = self.tabla.horizontalHeader()
        header.setStretchLastSection(True)  # Notas ocupa el espacio restante
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Instrumento
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Modelo
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Calibración
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Estado
        self.tabla.setColumnWidth(1, 180)
        self.tabla.setColumnWidth(2, 140)

        # Doble clic para editar
        self.tabla.doubleClicked.connect(self._editar_instrumento)

        layout.addWidget(self.tabla)

    # =========================================================================
    # Operaciones CRUD
    # =========================================================================

    def _cargar_datos(self) -> None:
        """Carga todos los instrumentos desde la base de datos al modelo."""
        instrumentos = self.db.obtener_instrumentos()
        self.modelo.actualizar_datos(instrumentos)

    def _filtrar_instrumentos(self, texto: str) -> None:
        """
        Filtra los instrumentos mostrados según el texto de búsqueda.

        Utiliza el QSortFilterProxyModel para filtrado local en tiempo real.
        """
        self.proxy_modelo.setFilterFixedString(texto)

    def _obtener_instrumento_seleccionado(self) -> dict | None:
        """
        Obtiene el instrumento actualmente seleccionado en la tabla.

        Returns:
            Diccionario del instrumento o None si no hay selección.
        """
        indices = self.tabla.selectionModel().selectedRows()
        if not indices:
            QMessageBox.information(
                self,
                "Sin selección",
                "Seleccione un instrumento de la tabla primero.",
            )
            return None

        # Mapear del proxy al modelo fuente
        indice_fuente = self.proxy_modelo.mapToSource(indices[0])
        return self.modelo.obtener_instrumento(indice_fuente.row())

    def _nuevo_instrumento(self) -> None:
        """Abre el diálogo para crear un nuevo instrumento."""
        dialogo = InstrumentDialog(self, titulo="Nuevo Instrumento")
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.crear_instrumento(
                name=datos["name"],
                model=datos["model"],
                last_calibration=datos["last_calibration"],
                status=datos["status"],
                notes=datos["notes"],
            )
            self._cargar_datos()
            self.campo_busqueda.clear()

    def _editar_instrumento(self) -> None:
        """Abre el diálogo para editar el instrumento seleccionado."""
        instrumento = self._obtener_instrumento_seleccionado()
        if instrumento is None:
            return

        dialogo = InstrumentDialog(
            self, datos=instrumento, titulo="Editar Instrumento"
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.actualizar_instrumento(
                inst_id=instrumento["id"],
                name=datos["name"],
                model=datos["model"],
                last_calibration=datos["last_calibration"],
                status=datos["status"],
                notes=datos["notes"],
            )
            self._cargar_datos()

    def _eliminar_instrumento(self) -> None:
        """Solicita confirmación y elimina el instrumento seleccionado."""
        instrumento = self._obtener_instrumento_seleccionado()
        if instrumento is None:
            return

        # Diálogo de confirmación
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el instrumento?\n\n"
            f"  Instrumento: {instrumento.get('name', '')}\n"
            f"  Modelo: {instrumento.get('model', '')}\n"
            f"  Estado: {instrumento.get('status', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.db.eliminar_instrumento(instrumento["id"])
            self._cargar_datos()
