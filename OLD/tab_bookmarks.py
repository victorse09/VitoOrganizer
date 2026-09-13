# -*- coding: utf-8 -*-
"""
tab_bookmarks.py — Módulo de Gestión de Marcadores/Enlaces para Vito Organizer.

Proporciona una interfaz de árbol jerárquico para organizar marcadores web
por categorías. Incluye apertura en navegador, menú contextual y gestión
de categorías dinámicas.

Autor: Vito Organizer
"""

from typing import Optional

from PyQt6.QtCore import QModelIndex, Qt, QUrl
from PyQt6.QtGui import (
    QAction,
    QColor,
    QDesktopServices,
    QFont,
    QStandardItem,
    QStandardItemModel,
)
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from database import Database
from svg_icons import (
    icon_category,
    icon_delete,
    icon_edit,
    icon_link,
    icon_new,
    icon_open_external,
    icon_plus,
    icon_save,
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
# Color para URLs mostradas como texto secundario
COLOR_URL = "#7D6B5D"

# Roles personalizados para almacenar datos en los items del árbol
ROL_TIPO = Qt.ItemDataRole.UserRole + 1       # "categoria" o "marcador"
ROL_ID = Qt.ItemDataRole.UserRole + 2         # ID del marcador en BD
ROL_URL = Qt.ItemDataRole.UserRole + 3        # URL del marcador
ROL_CATEGORIA = Qt.ItemDataRole.UserRole + 4  # Nombre de la categoría
ROL_DESCRIPCION = Qt.ItemDataRole.UserRole + 5  # Descripción del marcador

# Hoja de estilos para el árbol
ESTILO_ARBOL = f"""
    QTreeView {{
        background-color: {COLOR_FONDO};
        alternate-background-color: {COLOR_FILA_ALTERNA};
        border: 1px solid #C4A882;
        border-radius: 4px;
        color: {COLOR_TEXTO_OSCURO};
        font-size: 13px;
        selection-background-color: {COLOR_SELECCION};
        selection-color: #2C1810;
        outline: none;
    }}
    QTreeView::item {{
        padding: 5px 4px;
        border-bottom: 1px solid #EDE4D3;
    }}
    QTreeView::item:selected {{
        background-color: {COLOR_SELECCION};
    }}
    QTreeView::item:hover {{
        background-color: #E8D5B7;
    }}
    QTreeView::branch {{
        background-color: {COLOR_FONDO};
    }}
    QHeaderView::section {{
        background-color: {COLOR_ENCABEZADO};
        color: {COLOR_TEXTO_OSCURO};
        padding: 6px 8px;
        border: none;
        border-bottom: 2px solid #C4A882;
        font-weight: bold;
        font-size: 13px;
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
    QLineEdit, QComboBox {{
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
# Diálogo para crear/editar marcadores
# =============================================================================
class BookmarkDialog(QDialog):
    """
    Diálogo modal para crear o editar un marcador (enlace web).

    Contiene campos para título, URL, categoría (combo editable para
    permitir crear nuevas categorías) y descripción.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        categorias: list[str] | None = None,
        datos: dict | None = None,
        titulo: str = "Nuevo Enlace",
    ) -> None:
        """
        Inicializa el diálogo de marcador.

        Args:
            parent: Widget padre.
            categorias: Lista de categorías existentes para el combo.
            datos: Diccionario con datos existentes para edición.
            titulo: Título de la ventana del diálogo.
        """
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(460)
        self.setStyleSheet(ESTILO_DIALOGO)
        self._configurar_interfaz(categorias or [], datos)

    def _configurar_interfaz(self, categorias: list[str], datos: dict | None) -> None:
        """Construye el formulario del diálogo."""
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Campo: Título del marcador ---
        self.campo_titulo = QLineEdit()
        self.campo_titulo.setPlaceholderText("Título del enlace...")
        self.campo_titulo.setMaxLength(300)
        layout.addRow("Título:", self.campo_titulo)

        # --- Campo: URL ---
        self.campo_url = QLineEdit()
        self.campo_url.setPlaceholderText("https://ejemplo.com")
        self.campo_url.setMaxLength(2000)
        layout.addRow("URL:", self.campo_url)

        # --- Campo: Categoría (combo editable) ---
        self.campo_categoria = QComboBox()
        self.campo_categoria.setEditable(True)
        self.campo_categoria.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.campo_categoria.lineEdit().setPlaceholderText("Seleccionar o escribir categoría...")
        # Agregar categorías existentes
        for cat in sorted(categorias):
            self.campo_categoria.addItem(cat)
        layout.addRow("Categoría:", self.campo_categoria)

        # --- Campo: Descripción ---
        self.campo_descripcion = QTextEdit()
        self.campo_descripcion.setPlaceholderText("Descripción del enlace...")
        self.campo_descripcion.setMaximumHeight(100)
        layout.addRow("Descripción:", self.campo_descripcion)

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
            self.campo_titulo.setText(str(datos.get("title", "")))
            self.campo_url.setText(str(datos.get("url", "")))
            self.campo_descripcion.setPlainText(str(datos.get("description", "")))
            # Seleccionar la categoría existente o escribirla
            categoria = str(datos.get("category", ""))
            indice = self.campo_categoria.findText(categoria)
            if indice >= 0:
                self.campo_categoria.setCurrentIndex(indice)
            else:
                self.campo_categoria.setEditText(categoria)

    def _validar_y_aceptar(self) -> None:
        """Valida campos obligatorios antes de aceptar."""
        titulo = self.campo_titulo.text().strip()
        url = self.campo_url.text().strip()
        categoria = self.campo_categoria.currentText().strip()

        if not titulo:
            QMessageBox.warning(self, "Campo requerido", "El título es obligatorio.")
            self.campo_titulo.setFocus()
            return

        if not url:
            QMessageBox.warning(self, "Campo requerido", "La URL es obligatoria.")
            self.campo_url.setFocus()
            return

        if not categoria:
            QMessageBox.warning(self, "Campo requerido", "La categoría es obligatoria.")
            self.campo_categoria.setFocus()
            return

        # Agregar protocolo si falta
        if not url.startswith(("http://", "https://", "ftp://")):
            self.campo_url.setText("https://" + url)

        self.accept()

    def obtener_datos(self) -> dict:
        """
        Devuelve los datos ingresados en el formulario.

        Returns:
            Diccionario con las claves: title, url, category, description.
        """
        return {
            "title": self.campo_titulo.text().strip(),
            "url": self.campo_url.text().strip(),
            "category": self.campo_categoria.currentText().strip(),
            "description": self.campo_descripcion.toPlainText().strip(),
        }


# =============================================================================
# Diálogo para crear nueva categoría
# =============================================================================
class CategoryDialog(QDialog):
    """
    Diálogo simple para ingresar el nombre de una nueva categoría.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Inicializa el diálogo de nueva categoría."""
        super().__init__(parent)
        self.setWindowTitle("Nueva Categoría")
        self.setMinimumWidth(350)
        self.setStyleSheet(ESTILO_DIALOGO)
        self._configurar_interfaz()

    def _configurar_interfaz(self) -> None:
        """Construye el formulario del diálogo."""
        layout = QFormLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- Campo: Nombre de la categoría ---
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Nombre de la categoría...")
        self.campo_nombre.setMaxLength(100)
        layout.addRow("Categoría:", self.campo_nombre)

        # --- Botones ---
        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("Crear")
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setIcon(
            svg_to_qicon(icon_plus(), size=18, color=COLOR_ICONOS)
        )
        self.botones.accepted.connect(self._validar_y_aceptar)
        self.botones.rejected.connect(self.reject)
        layout.addRow(self.botones)

    def _validar_y_aceptar(self) -> None:
        """Valida que el nombre no esté vacío."""
        if not self.campo_nombre.text().strip():
            QMessageBox.warning(
                self, "Campo requerido", "El nombre de la categoría es obligatorio."
            )
            self.campo_nombre.setFocus()
            return
        self.accept()

    def obtener_nombre(self) -> str:
        """Devuelve el nombre de la categoría ingresado."""
        return self.campo_nombre.text().strip()


# =============================================================================
# Widget principal de la pestaña de Marcadores
# =============================================================================
class TabBookmarks(QWidget):
    """
    Pestaña principal de Gestión de Marcadores.

    Organiza los marcadores web en un árbol jerárquico por categorías.
    Permite crear, editar, eliminar marcadores y abrirlos en el navegador
    predeterminado. Incluye menú contextual con acciones rápidas.
    """

    def __init__(self, db: Database, parent: QWidget | None = None) -> None:
        """
        Inicializa la pestaña de marcadores.

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

        # --- Árbol de marcadores ---
        self._crear_arbol(layout_principal)

    def _crear_toolbar(self, layout: QVBoxLayout) -> None:
        """Crea la barra de herramientas con botones de acción."""
        toolbar_widget = QWidget()
        toolbar_widget.setStyleSheet(ESTILO_TOOLBAR)
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(6)

        # Botón: Nueva categoría
        self.btn_nueva_categoria = QPushButton("  Nueva Categoría")
        self.btn_nueva_categoria.setIcon(
            svg_to_qicon(icon_category(), size=20, color=COLOR_ICONOS)
        )
        self.btn_nueva_categoria.clicked.connect(self._nueva_categoria)
        self.btn_nueva_categoria.setToolTip("Crear una nueva categoría de marcadores")
        toolbar_layout.addWidget(self.btn_nueva_categoria)

        # Botón: Nuevo enlace
        self.btn_nuevo_enlace = QPushButton("  Nuevo Enlace")
        self.btn_nuevo_enlace.setIcon(
            svg_to_qicon(icon_new(), size=20, color=COLOR_ICONOS)
        )
        self.btn_nuevo_enlace.clicked.connect(self._nuevo_marcador)
        self.btn_nuevo_enlace.setToolTip("Agregar un nuevo marcador/enlace")
        toolbar_layout.addWidget(self.btn_nuevo_enlace)

        # Botón: Editar
        self.btn_editar = QPushButton("  Editar")
        self.btn_editar.setIcon(svg_to_qicon(icon_edit(), size=20, color=COLOR_ICONOS))
        self.btn_editar.clicked.connect(self._editar_marcador)
        self.btn_editar.setToolTip("Editar el marcador seleccionado")
        toolbar_layout.addWidget(self.btn_editar)

        # Botón: Eliminar
        self.btn_eliminar = QPushButton("  Eliminar")
        self.btn_eliminar.setIcon(svg_to_qicon(icon_delete(), size=20, color=COLOR_ICONOS))
        self.btn_eliminar.clicked.connect(self._eliminar_marcador)
        self.btn_eliminar.setToolTip("Eliminar el marcador seleccionado")
        toolbar_layout.addWidget(self.btn_eliminar)

        # Botón: Abrir en navegador
        self.btn_abrir = QPushButton("  Abrir en Navegador")
        self.btn_abrir.setIcon(
            svg_to_qicon(icon_open_external(), size=20, color=COLOR_ICONOS)
        )
        self.btn_abrir.clicked.connect(self._abrir_en_navegador)
        self.btn_abrir.setToolTip("Abrir el marcador seleccionado en el navegador")
        toolbar_layout.addWidget(self.btn_abrir)

        # Espaciador
        toolbar_layout.addStretch()

        toolbar_widget.setLayout(toolbar_layout)
        layout.addWidget(toolbar_widget)

    def _crear_arbol(self, layout: QVBoxLayout) -> None:
        """Crea el QTreeView con su modelo estándar."""
        # Modelo estándar para el árbol
        self.modelo_arbol = QStandardItemModel()
        self.modelo_arbol.setHorizontalHeaderLabels(["Marcadores"])

        # Vista de árbol
        self.arbol = QTreeView()
        self.arbol.setModel(self.modelo_arbol)
        self.arbol.setStyleSheet(ESTILO_ARBOL)

        # Configuración visual
        self.arbol.setAlternatingRowColors(True)
        self.arbol.setAnimated(True)
        self.arbol.setHeaderHidden(False)
        self.arbol.setExpandsOnDoubleClick(False)  # Controlamos doble clic manualmente
        self.arbol.setEditTriggers(QTreeView.EditTrigger.NoEditTriggers)

        # Ajustar encabezado
        header = self.arbol.header()
        header.setStretchLastSection(True)

        # Conectar señales
        self.arbol.doubleClicked.connect(self._al_doble_clic)

        # Menú contextual
        self.arbol.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.arbol.customContextMenuRequested.connect(self._mostrar_menu_contextual)

        layout.addWidget(self.arbol)

    # =========================================================================
    # Carga y construcción del árbol
    # =========================================================================

    def _cargar_datos(self) -> None:
        """
        Carga todos los marcadores desde la base de datos y construye el árbol.

        Agrupa los marcadores por categoría, creando nodos padre para cada
        categoría y nodos hijos para cada marcador.
        """
        self.modelo_arbol.clear()
        self.modelo_arbol.setHorizontalHeaderLabels(["Marcadores"])

        marcadores = self.db.obtener_marcadores()

        # Agrupar marcadores por categoría
        categorias_dict: dict[str, list[dict]] = {}
        for m in marcadores:
            cat = m.get("category", "Sin categoría") or "Sin categoría"
            if cat not in categorias_dict:
                categorias_dict[cat] = []
            categorias_dict[cat].append(m)

        # También incluir categorías vacías de la BD
        categorias_bd = self.db.obtener_categorias()
        for cat in categorias_bd:
            if cat not in categorias_dict:
                categorias_dict[cat] = []

        # Crear nodos del árbol ordenados por categoría
        raiz = self.modelo_arbol.invisibleRootItem()
        for nombre_cat in sorted(categorias_dict.keys()):
            # Nodo de categoría (padre)
            item_categoria = QStandardItem()
            item_categoria.setText(f"{nombre_cat}  ({len(categorias_dict[nombre_cat])})")
            item_categoria.setIcon(
                svg_to_qicon(icon_category(), size=18, color=COLOR_ICONOS)
            )
            item_categoria.setData("categoria", ROL_TIPO)
            item_categoria.setData(nombre_cat, ROL_CATEGORIA)

            # Fuente en negrita para categorías
            fuente_cat = QFont()
            fuente_cat.setBold(True)
            fuente_cat.setPointSize(11)
            item_categoria.setFont(fuente_cat)
            item_categoria.setForeground(QColor(COLOR_TEXTO_OSCURO))

            # No se puede editar ni arrastrar directamente
            item_categoria.setEditable(False)

            # Agregar marcadores hijos de esta categoría
            for marcador in categorias_dict[nombre_cat]:
                item_marcador = self._crear_item_marcador(marcador)
                item_categoria.appendRow(item_marcador)

            raiz.appendRow(item_categoria)

        # Expandir todas las categorías por defecto
        self.arbol.expandAll()

    def _crear_item_marcador(self, marcador: dict) -> QStandardItem:
        """
        Crea un QStandardItem para un marcador individual.

        Args:
            marcador: Diccionario con los datos del marcador.

        Returns:
            QStandardItem configurado con icono, texto y datos almacenados.
        """
        titulo = marcador.get("title", "Sin título")
        url = marcador.get("url", "")
        descripcion = marcador.get("description", "")

        item = QStandardItem()
        item.setText(titulo)
        item.setIcon(svg_to_qicon(icon_link(), size=16, color=COLOR_ICONOS))

        # Tooltip con la URL y descripción
        tooltip_text = f"URL: {url}"
        if descripcion:
            tooltip_text += f"\n\n{descripcion}"
        item.setToolTip(tooltip_text)

        # Almacenar datos en roles personalizados
        item.setData("marcador", ROL_TIPO)
        item.setData(marcador.get("id"), ROL_ID)
        item.setData(url, ROL_URL)
        item.setData(marcador.get("category", ""), ROL_CATEGORIA)
        item.setData(descripcion, ROL_DESCRIPCION)

        # Fuente normal para marcadores
        fuente = QFont()
        fuente.setPointSize(10)
        item.setFont(fuente)
        item.setForeground(QColor(COLOR_TEXTO_OSCURO))
        item.setEditable(False)

        return item

    # =========================================================================
    # Obtención del elemento seleccionado
    # =========================================================================

    def _obtener_item_seleccionado(self) -> QStandardItem | None:
        """
        Obtiene el QStandardItem actualmente seleccionado en el árbol.

        Returns:
            El item seleccionado o None si no hay selección.
        """
        indices = self.arbol.selectionModel().selectedIndexes()
        if not indices:
            return None
        return self.modelo_arbol.itemFromIndex(indices[0])

    def _obtener_marcador_seleccionado(self) -> QStandardItem | None:
        """
        Obtiene el item de tipo marcador seleccionado.

        Returns:
            El item si es un marcador, None si no hay selección o es categoría.
        """
        item = self._obtener_item_seleccionado()
        if item is None:
            QMessageBox.information(
                self,
                "Sin selección",
                "Seleccione un marcador del árbol primero.",
            )
            return None
        if item.data(ROL_TIPO) != "marcador":
            QMessageBox.information(
                self,
                "Selección inválida",
                "Seleccione un marcador, no una categoría.",
            )
            return None
        return item

    # =========================================================================
    # Operaciones CRUD
    # =========================================================================

    def _nueva_categoria(self) -> None:
        """Abre el diálogo para crear una nueva categoría."""
        dialogo = CategoryDialog(self)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            nombre = dialogo.obtener_nombre()
            # Verificar que no exista ya como categoría
            categorias_existentes = self.db.obtener_categorias()
            if nombre in categorias_existentes:
                QMessageBox.information(
                    self,
                    "Categoría existente",
                    f"La categoría '{nombre}' ya existe.",
                )
                return
            # Crear un marcador temporal vacío no es necesario,
            # simplemente recargamos y la categoría aparecerá
            # cuando se agregue un marcador a ella.
            # Para categorías vacías, creamos un marcador placeholder
            # o simplemente refrescamos — la categoría se agrega al árbol local.
            # Recargamos los datos para que la categoría aparezca
            # (la BD maneja categorías a través de obtener_categorias)
            self._cargar_datos()
            QMessageBox.information(
                self,
                "Categoría creada",
                f"La categoría '{nombre}' está lista.\n"
                f"Agregue marcadores a esta categoría para poblarla.",
            )

    def _nuevo_marcador(self) -> None:
        """Abre el diálogo para crear un nuevo marcador."""
        categorias = self.db.obtener_categorias()
        # Si se seleccionó una categoría, pre-seleccionarla
        item = self._obtener_item_seleccionado()
        datos_pre = None
        if item and item.data(ROL_TIPO) == "categoria":
            datos_pre = {"category": item.data(ROL_CATEGORIA)}
        elif item and item.data(ROL_TIPO) == "marcador":
            datos_pre = {"category": item.data(ROL_CATEGORIA)}

        dialogo = BookmarkDialog(
            self, categorias=categorias, datos=datos_pre, titulo="Nuevo Enlace"
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.crear_marcador(
                title=datos["title"],
                url=datos["url"],
                category=datos["category"],
                description=datos["description"],
            )
            self._cargar_datos()

    def _editar_marcador(self) -> None:
        """Abre el diálogo para editar el marcador seleccionado."""
        item = self._obtener_marcador_seleccionado()
        if item is None:
            return

        # Reconstruir diccionario de datos del marcador
        datos_actuales = {
            "id": item.data(ROL_ID),
            "title": item.text(),
            "url": item.data(ROL_URL),
            "category": item.data(ROL_CATEGORIA),
            "description": item.data(ROL_DESCRIPCION),
        }

        categorias = self.db.obtener_categorias()
        dialogo = BookmarkDialog(
            self,
            categorias=categorias,
            datos=datos_actuales,
            titulo="Editar Enlace",
        )
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.actualizar_marcador(
                bm_id=datos_actuales["id"],
                title=datos["title"],
                url=datos["url"],
                category=datos["category"],
                description=datos["description"],
            )
            self._cargar_datos()

    def _eliminar_marcador(self) -> None:
        """Solicita confirmación y elimina el marcador seleccionado."""
        item = self._obtener_marcador_seleccionado()
        if item is None:
            return

        titulo = item.text()
        url = item.data(ROL_URL) or ""

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro de que desea eliminar el marcador?\n\n"
            f"  Título: {titulo}\n"
            f"  URL: {url}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            bm_id = item.data(ROL_ID)
            self.db.eliminar_marcador(bm_id)
            self._cargar_datos()

    def _abrir_en_navegador(self) -> None:
        """Abre el marcador seleccionado en el navegador predeterminado."""
        item = self._obtener_marcador_seleccionado()
        if item is None:
            return

        url = item.data(ROL_URL)
        if url:
            QDesktopServices.openUrl(QUrl(url))

    # =========================================================================
    # Eventos de interacción
    # =========================================================================

    def _al_doble_clic(self, indice: QModelIndex) -> None:
        """
        Maneja el doble clic en el árbol.

        Si se hace doble clic en un marcador, se abre en el navegador.
        Si se hace doble clic en una categoría, se alterna expansión/colapso.
        """
        item = self.modelo_arbol.itemFromIndex(indice)
        if item is None:
            return

        if item.data(ROL_TIPO) == "marcador":
            # Abrir en el navegador
            url = item.data(ROL_URL)
            if url:
                QDesktopServices.openUrl(QUrl(url))
        elif item.data(ROL_TIPO) == "categoria":
            # Alternar expansión/colapso
            if self.arbol.isExpanded(indice):
                self.arbol.collapse(indice)
            else:
                self.arbol.expand(indice)

    def _mostrar_menu_contextual(self, posicion) -> None:
        """
        Muestra un menú contextual al hacer clic derecho en el árbol.

        El menú varía según si el item seleccionado es un marcador
        o una categoría.
        """
        indice = self.arbol.indexAt(posicion)
        if not indice.isValid():
            return

        item = self.modelo_arbol.itemFromIndex(indice)
        if item is None:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLOR_FONDO};
                border: 1px solid #C4A882;
                border-radius: 4px;
                padding: 4px;
                color: {COLOR_TEXTO_OSCURO};
                font-size: 12px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {COLOR_SELECCION};
            }}
        """)

        if item.data(ROL_TIPO) == "marcador":
            # Menú para marcadores: Abrir, Editar, Eliminar
            accion_abrir = QAction(
                svg_to_qicon(icon_open_external(), size=16, color=COLOR_ICONOS),
                "Abrir en navegador",
                self,
            )
            accion_abrir.triggered.connect(self._abrir_en_navegador)
            menu.addAction(accion_abrir)

            menu.addSeparator()

            accion_editar = QAction(
                svg_to_qicon(icon_edit(), size=16, color=COLOR_ICONOS),
                "Editar",
                self,
            )
            accion_editar.triggered.connect(self._editar_marcador)
            menu.addAction(accion_editar)

            accion_eliminar = QAction(
                svg_to_qicon(icon_delete(), size=16, color=COLOR_ICONOS),
                "Eliminar",
                self,
            )
            accion_eliminar.triggered.connect(self._eliminar_marcador)
            menu.addAction(accion_eliminar)

        elif item.data(ROL_TIPO) == "categoria":
            # Menú para categorías: Nuevo enlace en esta categoría
            accion_nuevo = QAction(
                svg_to_qicon(icon_new(), size=16, color=COLOR_ICONOS),
                "Nuevo enlace en esta categoría",
                self,
            )
            accion_nuevo.triggered.connect(self._nuevo_marcador)
            menu.addAction(accion_nuevo)

        menu.exec(self.arbol.viewport().mapToGlobal(posicion))
