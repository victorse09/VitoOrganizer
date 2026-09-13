# =============================================================================
# Vito Organizer v2.2 - Sidebar
# Barra lateral ajustable con contenido dinámico por sección
# Estilo visual: Lotus Organizer (cubierta de cuero texturizado)
# =============================================================================

from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPaintEvent
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QStackedWidget, QFrame, QScrollArea
)

from core.trash_widget import TrashWidget
from graphics.textures import Textures


class Sidebar(QWidget):
    """Barra lateral ajustable con contenido dinámico.

    El contenido se actualiza según la sección activa.
    Siempre muestra la papelera en la parte inferior.
    
    Estilo Lotus Organizer: cubierta de cuero verde-azulado texturizado
    con borde cosido decorativo.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('sidebar')
        self.setMinimumWidth(160)
        self.setMaximumWidth(350)
        self._sidebar_color = '#1b4332'

        self._setup_ui()

    def set_sidebar_color(self, color: str):
        """Establece el color base de la textura de la barra lateral."""
        self._sidebar_color = color
        self.update()

    def set_trash_style(self, style: str):
        """Establece el estilo visual de la papelera."""
        self._trash.set_trash_style(style)

    def _setup_ui(self):
        """Configura la interfaz del sidebar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(0)

        # Área de contenido dinámico (scrollable)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)

        # Stack para alternar contenido de cada sección
        self._content_stack = QStackedWidget()
        self._content_stack.setObjectName('sidebarContent')
        self._scroll_area.setWidget(self._content_stack)

        # Papelera (siempre visible abajo)
        self._trash = TrashWidget()

        layout.addWidget(self._scroll_area, 1)
        layout.addWidget(self._trash)

    def paintEvent(self, event: QPaintEvent):
        """Dibuja la textura de cuero de fondo tipo Lotus Organizer."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        rect = QRectF(self.rect())
        
        # Dibujar textura de cuero/tela con el color seleccionado
        Textures.draw_sidebar_texture(painter, rect, base_color=self._sidebar_color)
        
        # Borde derecho con efecto de profundidad (borde del libro)
        edge_width = 4
        from PyQt6.QtGui import QLinearGradient, QColor, QBrush
        edge_rect = QRectF(rect.right() - edge_width, rect.top(), edge_width, rect.height())
        edge_grad = QLinearGradient(edge_rect.left(), 0, edge_rect.right(), 0)
        edge_grad.setColorAt(0.0, QColor(0, 0, 0, 40))
        edge_grad.setColorAt(0.5, QColor(0, 0, 0, 60))
        edge_grad.setColorAt(1.0, QColor(0, 0, 0, 30))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(edge_grad))
        painter.drawRect(edge_rect)
        
        painter.end()

    @property
    def trash_widget(self) -> TrashWidget:
        """Retorna el widget de papelera."""
        return self._trash

    def add_section_widget(self, plugin_id: str, widget: QWidget):
        """Agrega un widget de sección al stack.

        Args:
            plugin_id: ID del plugin.
            widget: Widget de sidebar del plugin.
        """
        widget.setObjectName(f'sidebar_{plugin_id}')
        self._content_stack.addWidget(widget)

    def show_section(self, plugin_id: str):
        """Muestra el widget de la sección indicada."""
        for i in range(self._content_stack.count()):
            widget = self._content_stack.widget(i)
            if widget.objectName() == f'sidebar_{plugin_id}':
                self._content_stack.setCurrentIndex(i)
                break

    def get_current_section_widget(self) -> QWidget:
        """Retorna el widget de sección actualmente visible."""
        return self._content_stack.currentWidget()
