# =============================================================================
# Vito Organizer v2.2 - Agenda View
# Vista central de libro abierto (dos páginas + encuadernación + pestañas)
# =============================================================================

from PyQt6.QtCore import Qt, QRectF, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPaintEvent, QResizeEvent, QRadialGradient
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QScrollArea, QFrame, QSizePolicy
)

from graphics.agenda_renderer import AgendaRenderer
from core.section_tabs import SectionTabs, Side
from config.settings import AppearanceSettings


class AgendaPageContainer(QWidget):
    """Contenedor para el contenido de una página de la agenda.

    Dibuja el fondo de la página y contiene el widget del plugin.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('agendaContainer')
        self.setStyleSheet('background: transparent;')
        self._content_widget: QWidget = None
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Expanding)

    def set_content(self, widget: QWidget):
        """Establece el widget de contenido de la página."""
        # Remover widget anterior
        if self._content_widget:
            self._layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)

        self._content_widget = widget
        if widget:
            widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self._layout.addWidget(widget)

    def clear_content(self):
        """Limpia el contenido de la página."""
        if self._content_widget:
            self._layout.removeWidget(self._content_widget)
            self._content_widget.setParent(None)
            self._content_widget = None


class AgendaView(QWidget):
    """Vista central que muestra el libro abierto con dos páginas,
    encuadernación y pestañas de sección.

    Emula la vista de Lotus Organizer: una agenda de papel abierta.
    """

    section_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('agendaView')
        self._appearance = AppearanceSettings()
        self._current_page = 1
        self._total_pages = 1
        self._single_page_mode = False

        # Contenedores de páginas
        self._left_page = AgendaPageContainer()
        self._right_page = AgendaPageContainer()

        # Pestañas de sección izquierda y derecha
        self._left_tabs = SectionTabs(side=Side.LEFT)
        self._right_tabs = SectionTabs(side=Side.RIGHT)
        
        self._left_tabs.section_changed.connect(self.section_changed.emit)
        self._right_tabs.section_changed.connect(self.section_changed.emit)
        
        self._all_tabs_data = []

        self._setup_layout()

    def _setup_layout(self):
        """Configura el layout del widget."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Use negative spacing so tabs overlap the paper edges perfectly, eliminating gaps
        overlap = AgendaRenderer.PAGE_MARGIN + 1
        layout.setSpacing(-overlap)

        # Contenedor central (las páginas se dibujan en paintEvent)
        self._book_area = QWidget()
        self._book_area.setObjectName('transparentPage')
        self._book_area.setStyleSheet('background: transparent;')
        self._book_area.setMinimumSize(400, 300)

        # Layout interno del libro con las dos páginas
        self._book_layout = QHBoxLayout(self._book_area)
        # Margins adjusted for tighter fit since tabs now overlap
        self._book_layout.setContentsMargins(0, 15, 0, 15)
        self._book_layout.setSpacing(60)  # Espacio para la encuadernación (wider binder)
        self._book_layout.addWidget(self._left_page, 1)
        self._book_layout.addWidget(self._right_page, 1)

        # Agregar componentes al layout general: [LeftTabs] [BookArea] [RightTabs]
        layout.addWidget(self._left_tabs)
        layout.addWidget(self._book_area, 1)
        layout.addWidget(self._right_tabs)

    def set_appearance(self, appearance: AppearanceSettings):
        """Actualiza la configuración de apariencia."""
        self._appearance = appearance
        self.update()

    def set_single_page_mode(self, enabled: bool):
        """Activa o desactiva el modo de página única sin encuadernación.

        En este modo, la página derecha se oculta, el spacing de la
        encuadernación desaparece y se renderiza una sola hoja grande.
        Cualquier plugin puede solicitar este modo vía la señal
        single_page_requested de PluginBase.
        """
        if self._single_page_mode == enabled:
            return
        self._single_page_mode = enabled
        if enabled:
            self._right_page.hide()
            self._book_layout.setSpacing(0)
        else:
            self._right_page.show()
            self._book_layout.setSpacing(60)
            self._left_page.updateGeometry()
            self._right_page.updateGeometry()
            self._book_layout.invalidate()
            self._book_layout.activate()
        self.update()

    def set_pagination(self, current_page: int, total_pages: int):
        """Establece la paginación de la sección activa para renderizar los números de página."""
        self._current_page = current_page
        self._total_pages = total_pages
        self.update()

    def set_tabs(self, tabs_data):
        """Establece todas las pestañas de sección y las distribuye."""
        self._all_tabs_data = list(tabs_data)
        
        # Intentar mantener la activa actual o usar la primera por defecto
        current = self._left_tabs.get_active_id() or self._right_tabs.get_active_id()
        if not current and self._all_tabs_data:
            current = self._all_tabs_data[0][0]
            
        if current:
            self.set_active_section(current)

    def set_active_section(self, plugin_id: str):
        """Establece la sección activa y distribuye las pestañas a izquierda/derecha."""
        if not self._all_tabs_data:
            return
            
        active_index = 0
        for i, tab in enumerate(self._all_tabs_data):
            if tab[0] == plugin_id:
                active_index = i
                break
                
        # Split tabs
        left_tabs = self._all_tabs_data[:active_index + 1]
        right_tabs = self._all_tabs_data[active_index + 1:]
        
        self._left_tabs.set_tabs(left_tabs)
        self._right_tabs.set_tabs(right_tabs)
        
        self._left_tabs.set_active(plugin_id)
        self._right_tabs.set_active("")

    def set_left_content(self, widget: QWidget):
        """Establece el contenido de la página izquierda."""
        self._left_page.set_content(widget)

    def set_right_content(self, widget: QWidget):
        """Establece el contenido de la página derecha."""
        self._right_page.set_content(widget)

    def clear_pages(self):
        """Limpia el contenido de ambas páginas."""
        self._left_page.clear_content()
        self._right_page.clear_content()

    def paintEvent(self, event: QPaintEvent):
        """Dibuja el fondo del libro abierto."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Fondo verde fieltro (escritorio)
        from graphics.textures import Textures
        Textures.draw_green_felt_texture(painter, QRectF(self.rect()))

        book_rect = QRectF(self._book_area.geometry())

        if self._single_page_mode:
            # Modo página única sin encuadernación
            AgendaRenderer.draw_single_page(
                painter, book_rect,
                page_color=self._appearance.page_color,
                page_style=self._appearance.page_style,
                line_color=self._appearance.line_color,
                margin_color=self._appearance.margin_color,
                show_margin=False,
                line_spacing=self._appearance.line_spacing
            )
        else:
            # Modo normal: libro abierto con dos páginas y encuadernación
            left_num = (self._current_page - 1) * 2 + 1
            right_num = (self._current_page - 1) * 2 + 2
            AgendaRenderer.draw_open_book(
                painter, book_rect,
                page_color=self._appearance.page_color,
                page_style=self._appearance.page_style,
                binding_type=self._appearance.binding_type,
                ring_color=self._appearance.ring_color,
                line_color=self._appearance.line_color,
                margin_color=self._appearance.margin_color,
                show_margin=self._appearance.show_margin,
                line_spacing=self._appearance.line_spacing,
                left_page_num=left_num,
                right_page_num=right_num
            )

        painter.end()
