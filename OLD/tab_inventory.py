# -*- coding: utf-8 -*-
"""
tab_inventory.py — Módulo de Inventario de Componentes para Vito Organizer.

Proporciona una interfaz CRUD completa para gestionar componentes electrónicos
u otros elementos de inventario. Incluye búsqueda en tiempo real, tabla ordenable
y diálogos de creación/edición con validación.

Autor: Vito Organizer
"""

from typing import Any, Optional

from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    QVariant,
)
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QTextEdit,
    QToolBar,
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

# Hoja de estilos para la tabla y la barra de búsqueda
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
    QToolBar {{
        background-color: {COLOR_FONDO};
        border: none;
        spacing: 6px;
        padding: 4px;
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
    QLineEdit, QSpinBox {{
        background-color: white;
        border: 1px solid #C4A882;
        border-radius: 4px;
        padding: 5px 8px;
        font-size: 13px;
        color: {COLOR_TEXTO_OSCURO};
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
# Modelo de datos para la tabla de componentes
# =============================================================================
class ComponentModel(QAbstractTableModel):
    """
    Modelo personalizado para la tabla de componentes.
    
    Gestiona los datos del inventario proporcionando acceso por filas/columnas,
    ordenamiento y formato de visualización.
    """

    # Nombres de las columnas en español
    COLUMNAS = ["ID", "Componente", "Cantidad", "Ubicación", "Descripción"]
    # Claves correspondientes en el diccionario de datos
    CLAVES = ["id", "name", "quantity", "location", "description"]

    def __init__(self, datos: list[dict] | None = None, parent=None) -> None:
        """Inicializa el modelo con los datos proporcionados."""
        super().__init__(parent)
        self._datos: list[dict] = datos or []

    # ---- Métodos obligatorios de QAbstractTableModel ----

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Devuelve el número de filas (componentes)."""
        return len(self._datos)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Devuelve el número de columnas."""
        return len(self.COLUMNAS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """
        Devuelve el dato correspondiente a la celda y rol indicados.
        
        Soporta roles de visualización, alineación, color de fondo y fuente.
        """
        if not index.isValid() or not (0 <= index.row() < len(self._datos)):
            return QVariant()

        componente = self._datos[index.row()]
        clave = self.CLAVES[index.column()]
        valor = componente.get(clave, "")

        if role == Qt.ItemDataRole.DisplayRole:
            return str(valor)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Centrar la columna de cantidad
            if clave == "quantity":
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.ForegroundRole:
            return QColor(COLOR_TEXTO_OSCURO)

        elif role == Qt.ItemDataRole.FontRole:
            fuente = QFont()
            fuente.setPointSize(10)
            # Nombre del componente en negrita
            if clave == "name":
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

    def obtener_componente(self, fila: int) -> dict | None:
        """Devuelve el diccionario del componente en la fila indicada."""
        if 0 <= fila < len(self._datos):
            return self._datos[fila]
        return None


# =============================================================================
# Diálogo para crear/editar componentes
# =============================================================================
class ComponentDialog(QDialog):
    """
    Diálogo modal para crear o editar un componente del inventario.
    
    Contiene campos para nombre, cantidad, ubicación y descripción,
    con validación básica antes de aceptar.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        datos: dict | None = None,
        titulo: str = "Nuevo Componente",
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
        self.setMinimumWidth(420)
        self.setStyleSheet(ESTILO_DIALOGO)
        self._configurar_interfaz(datos)

    def _configurar_interfaz(self, datos: dict | None) -> None:
        """Construye el formulario del diálogo."""
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Campo: Nombre del componente ---
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Nombre del componente...")
        self.campo_nombre.setMaxLength(200)
        layout.addRow("Componente:", self.campo_nombre)

        # --- Campo: Cantidad ---
        self.campo_cantidad = QSpinBox()
        self.campo_cantidad.setRange(0, 99999)
        self.campo_cantidad.setValue(0)
        layout.addRow("Cantidad:", self.campo_cantidad)

        # --- Campo: Ubicación ---
        self.campo_ubicacion = QLineEdit()
        self.campo_ubicacion.setPlaceholderText("Ej: Estante A-3, Cajón 5...")
        self.campo_ubicacion.setMaxLength(200)
        layout.addRow("Ubicación:", self.campo_ubicacion)

        # --- Campo: Descripción ---
        self.campo_descripcion = QTextEdit()
        self.campo_descripcion.setPlaceholderText("Descripción detallada del componente...")
        self.campo_descripcion.setMaximumHeight(120)
        layout.addRow("Descripción:", self.campo_descripcion)

        # --- Botones de acción ---
        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("Guardar")
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        # Asignar icono de guardar al botón OK
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setIcon(
            svg_to_qicon(icon_save(), size=18, color=COLOR_ICONOS)
        )
        self.botones.accepted.connect(self._validar_y_aceptar)
        self.botones.rejected.connect(self.reject)
        layout.addRow(self.botones)

        # --- Pre-cargar datos si estamos editando ---
        if datos:
            self.campo_nombre.setText(str(datos.get("name", "")))
            self.campo_cantidad.setValue(int(datos.get("quantity", 0)))
            self.campo_ubicacion.setText(str(datos.get("location", "")))
            self.campo_descripcion.setPlainText(str(datos.get("description", "")))

    def _validar_y_aceptar(self) -> None:
        """Valida que los campos obligatorios estén completos antes de aceptar."""
        nombre = self.campo_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(
                self,
                "Campo requerido",
                "El nombre del componente es obligatorio.",
            )
            self.campo_nombre.setFocus()
            return
        self.accept()

    def obtener_datos(self) -> dict:
        """
        Devuelve los datos ingresados en el formulario.

        Returns:
            Diccionario con las claves: name, quantity, location, description.
        """
        return {
            "name": self.campo_nombre.text().strip(),
            "quantity": self.campo_cantidad.value(),
            "location": self.campo_ubicacion.text().strip(),
            "description": self.campo_descripcion.toPlainText().strip(),
        }


# =============================================================================
# Widget principal de la pestaña de Inventario
# =============================================================================
class TabInventory(QWidget):
    """
    Pestaña principal de Inventario de Componentes.

    Proporciona una interfaz completa para buscar, crear, editar y eliminar
    componentes del inventario, con tabla ordenable y búsqueda en tiempo real.
    """

    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        """
        Inicializa la pestaña de inventario.

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
        # Fondo papel/crema
        self.setStyleSheet(f"QWidget {{ background-color: {COLOR_FONDO}; }}")

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(12, 12, 12, 12)
        layout_principal.setSpacing(8)

        # --- Barra de herramientas ---
        self._crear_toolbar(layout_principal)

        # --- Barra de búsqueda ---
        self._crear_barra_busqueda(layout_principal)

        # --- Tabla de componentes ---
        self._crear_tabla(layout_principal)

    def _crear_toolbar(self, layout: QVBoxLayout) -> None:
        """Crea la barra de herramientas con botones de acción."""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        # Contenedor con estilo para la toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(ESTILO_TOOLBAR)

        # Botón: Nuevo componente
        self.btn_nuevo = QPushButton("  Nuevo")
        self.btn_nuevo.setIcon(svg_to_qicon(icon_new(), size=20, color=COLOR_ICONOS))
        self.btn_nuevo.clicked.connect(self._nuevo_componente)
        self.btn_nuevo.setToolTip("Agregar un nuevo componente al inventario")
        toolbar_layout.addWidget(self.btn_nuevo)

        # Botón: Editar componente seleccionado
        self.btn_editar = QPushButton("  Editar")
        self.btn_editar.setIcon(svg_to_qicon(icon_edit(), size=20, color=COLOR_ICONOS))
        self.btn_editar.clicked.connect(self._editar_componente)
        self.btn_editar.setToolTip("Editar el componente seleccionado")
        toolbar_layout.addWidget(self.btn_editar)

        # Botón: Eliminar componente seleccionado
        self.btn_eliminar = QPushButton("  Eliminar")
        self.btn_eliminar.setIcon(svg_to_qicon(icon_delete(), size=20, color=COLOR_ICONOS))
        self.btn_eliminar.clicked.connect(self._eliminar_componente)
        self.btn_eliminar.setToolTip("Eliminar el componente seleccionado")
        toolbar_layout.addWidget(self.btn_eliminar)

        # Espaciador para empujar botones a la izquierda
        toolbar_layout.addStretch()

        toolbar_widget.setLayout(toolbar_layout)
        layout.addWidget(toolbar_widget)

    def _crear_barra_busqueda(self, layout: QVBoxLayout) -> None:
        """Crea la barra de búsqueda con filtrado en tiempo real."""
        contenedor_busqueda = QHBoxLayout()
        contenedor_busqueda.setSpacing(8)

        # Icono de búsqueda como etiqueta
        lbl_icono = QLabel()
        lbl_icono.setPixmap(
            svg_to_qicon(icon_search(), size=20, color=COLOR_ICONOS).pixmap(20, 20)
        )
        lbl_icono.setFixedSize(24, 24)
        contenedor_busqueda.addWidget(lbl_icono)

        # Campo de texto de búsqueda
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Buscar componentes...")
        self.campo_busqueda.setClearButtonEnabled(True)
        self.campo_busqueda.setStyleSheet(ESTILO_BUSQUEDA)
        # Conectar la búsqueda en tiempo real
        self.campo_busqueda.textChanged.connect(self._filtrar_componentes)
        contenedor_busqueda.addWidget(self.campo_busqueda)

        layout.addLayout(contenedor_busqueda)

    def _crear_tabla(self, layout: QVBoxLayout) -> None:
        """Crea la tabla de componentes con modelo y proxy de ordenamiento."""
        # Modelo de datos
        self.modelo = ComponentModel()

        # Proxy para permitir ordenamiento por columnas
        self.proxy_modelo = QSortFilterProxyModel()
        self.proxy_modelo.setSourceModel(self.modelo)
        self.proxy_modelo.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        # Filtrar en todas las columnas visibles
        self.proxy_modelo.setFilterKeyColumn(-1)

        # Vista de tabla
        self.tabla = QTableView()
        self.tabla.setModel(self.proxy_modelo)
        self.tabla.setStyleSheet(ESTILO_TABLA)

        # Configuración visual de la tabla
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
        header.setStretchLastSection(True)  # Descripción ocupa el espacio restante
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Componente
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Cantidad
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Ubicación
        # Anchos iniciales razonables
        self.tabla.setColumnWidth(1, 200)
        self.tabla.setColumnWidth(3, 160)

        # Doble clic para editar
        self.tabla.doubleClicked.connect(self._editar_componente)

        layout.addWidget(self.tabla)

    # =========================================================================
    # Operaciones CRUD
    # =========================================================================

    def _cargar_datos(self) -> None:
        """Carga todos los componentes desde la base de datos al modelo."""
        componentes = self.db.obtener_componentes()
        self.modelo.actualizar_datos(componentes)

    def _filtrar_componentes(self, texto: str) -> None:
        """
        Filtra los componentes mostrados según el texto de búsqueda.
        
        Si el texto está vacío, muestra todos los componentes.
        Utiliza el método de búsqueda de la base de datos para resultados precisos.
        """
        if texto.strip():
            # Usar búsqueda de la base de datos para resultados más precisos
            resultados = self.db.buscar_componentes(texto.strip())
            self.modelo.actualizar_datos(resultados)
        else:
            self._cargar_datos()

    def _obtener_componente_seleccionado(self) -> dict | None:
        """
        Obtiene el componente actualmente seleccionado en la tabla.

        Returns:
            Diccionario del componente o None si no hay selección.
        """
        indices = self.tabla.selectionModel().selectedRows()
        if not indices:
            QMessageBox.information(
                self,
                "Sin selección",
                "Seleccione un componente de la tabla primero.",
            )
            return None

        # Mapear del proxy al modelo fuente
        indice_fuente = self.proxy_modelo.mapToSource(indices[0])
        return self.modelo.obtener_componente(indice_fuente.row())

    def _nuevo_componente(self) -> None:
        """Abre el diálogo para crear un nuevo componente."""
        dialogo = ComponentDialog(self, titulo="Nuevo Componente")
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.crear_componente(
                name=datos["name"],
                quantity=datos["quantity"],
                location=datos["location"],
                description=datos["description"],
            )
            # Recargar datos para reflejar el nuevo componente
            self._cargar_datos()
            # Limpiar búsqueda para mostrar todos los resultados
            self.campo_busqueda.clear()

    def _editar_componente(self) -> None:
        """Abre el diálogo para editar el componente seleccionado."""
        componente = self._obtener_componente_seleccionado()
        if componente is None:
            return

        dialogo = ComponentDialog(
            self, datos=componente, titulo="Editar Componente"
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.actualizar_componente(
                comp_id=componente["id"],
                name=datos["name"],
                quantity=datos["quantity"],
                location=datos["location"],
                description=datos["description"],
            )
            # Recargar datos para reflejar los cambios
            self._cargar_datos()

    def _eliminar_componente(self) -> None:
        """Solicita confirmación y elimina el componente seleccionado."""
        componente = self._obtener_componente_seleccionado()
        if componente is None:
            return

        # Diálogo de confirmación antes de eliminar
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el componente?\n\n"
            f"  Componente: {componente.get('name', '')}\n"
            f"  Ubicación: {componente.get('location', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.db.eliminar_componente(componente["id"])
            # Recargar datos para reflejar la eliminación
            self._cargar_datos()
