# =============================================================================
# Vito Organizer v2.2 - Page Styles
# Estilos de fondo de página de agenda (líneas, cuadrícula, puntos, liso)
# Estilo visual: Lotus Organizer (papel crema con líneas tenues)
# =============================================================================

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QPainter, QColor, QPen


class PageStyles:
    """Renderiza los diferentes estilos de fondo de página de agenda."""

    @staticmethod
    def draw_lined(painter: QPainter, rect: QRectF,
                   line_color: str = '#C8C4A0',
                   margin_color: str = '#CC6666',
                   show_margin: bool = True,
                   line_spacing: int = 24,
                   header_height: int = 40):
        """Dibuja página con líneas horizontales (tipo libreta rayada).
        
        Estilo Lotus Organizer: líneas tenues color mostaza/arena sobre
        papel crema, con margen rojo suave.
        """
        # Líneas principales - tenues y cálidas
        line_col = QColor(line_color)
        line_col.setAlpha(100)
        pen = QPen(line_col, 0.6)
        painter.setPen(pen)

        # Líneas horizontales desde el header hacia abajo
        y = rect.top() + header_height
        while y < rect.bottom() - 5:
            painter.drawLine(
                int(rect.left() + 5), int(y),
                int(rect.right() - 5), int(y)
            )
            y += line_spacing

        # Sub-líneas intermedias más tenues (marca de :30 minutos)
        sub_line_col = QColor(line_color)
        sub_line_col.setAlpha(40)
        sub_pen = QPen(sub_line_col, 0.3)
        painter.setPen(sub_pen)

        y = rect.top() + header_height + line_spacing / 2
        while y < rect.bottom() - 5:
            painter.drawLine(
                int(rect.left() + 15), int(y),
                int(rect.right() - 15), int(y)
            )
            y += line_spacing

        # Línea de margen vertical (roja suave)
        if show_margin:
            margin_x = rect.left() + 60
            margin_col = QColor(margin_color)
            margin_col.setAlpha(120)
            pen_margin = QPen(margin_col, 0.8)
            painter.setPen(pen_margin)
            painter.drawLine(
                int(margin_x), int(rect.top() + header_height - 10),
                int(margin_x), int(rect.bottom() - 5)
            )

    @staticmethod
    def draw_grid(painter: QPainter, rect: QRectF,
                  line_color: str = '#C8C4A0',
                  line_spacing: int = 20,
                  header_height: int = 40):
        """Dibuja página cuadriculada."""
        line_col = QColor(line_color)
        line_col.setAlpha(70)
        pen = QPen(line_col, 0.3)
        painter.setPen(pen)

        # Líneas horizontales
        y = rect.top() + header_height
        while y < rect.bottom() - 5:
            painter.drawLine(
                int(rect.left() + 5), int(y),
                int(rect.right() - 5), int(y)
            )
            y += line_spacing

        # Líneas verticales
        x = rect.left() + 5
        while x < rect.right() - 5:
            painter.drawLine(
                int(x), int(rect.top() + header_height),
                int(x), int(rect.bottom() - 5)
            )
            x += line_spacing

    @staticmethod
    def draw_dots(painter: QPainter, rect: QRectF,
                  dot_color: str = '#B0A880',
                  dot_spacing: int = 20,
                  header_height: int = 40):
        """Dibuja página con patrón de puntos (dot grid)."""
        color = QColor(dot_color)
        color.setAlpha(90)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)

        y = rect.top() + header_height
        while y < rect.bottom() - 5:
            x = rect.left() + 10
            while x < rect.right() - 5:
                painter.drawEllipse(int(x) - 1, int(y) - 1, 2, 2)
                x += dot_spacing
            y += dot_spacing

    @staticmethod
    def draw_plain(painter: QPainter, rect: QRectF, **kwargs):
        """Página lisa sin líneas ni cuadrícula."""
        # No se dibuja nada adicional
        pass

    @classmethod
    def draw(cls, style: str, painter: QPainter, rect: QRectF, **kwargs):
        """Dibuja el estilo de página según el nombre."""
        styles = {
            'lined': cls.draw_lined,
            'grid': cls.draw_grid,
            'dots': cls.draw_dots,
            'plain': cls.draw_plain,
        }
        draw_func = styles.get(style, cls.draw_lined)
        draw_func(painter, rect, **kwargs)
