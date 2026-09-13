# =============================================================================
# Vito Organizer v2.2 - Textures
# Texturas para cubiertas y fondos decorativos
# =============================================================================

from PyQt6.QtCore import QRectF, QRect, Qt
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QPixmap, QRadialGradient
)


class Textures:
    """Genera texturas decorativas para la interfaz."""

    @staticmethod
    def draw_leather_texture(painter: QPainter, rect: QRectF,
                             base_color: str = '#2C3E50'):
        """Dibuja una textura de cuero para portada/sidebar."""
        painter.save()

        color = QColor(base_color)

        # --- Deeper gradient with more color stops ---
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, color.lighter(115))
        gradient.setColorAt(0.15, color.lighter(108))
        gradient.setColorAt(0.3, color)
        gradient.setColorAt(0.5, color.darker(103))
        gradient.setColorAt(0.7, color.darker(108))
        gradient.setColorAt(0.85, color.darker(112))
        gradient.setColorAt(1.0, color.darker(120))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(rect)

        # --- Subtle noise/grain effect (dark speckles) ---
        import random
        random.seed(42)

        grain_dark = QColor(0, 0, 0, 18)
        grain_light = QColor(255, 255, 255, 12)
        painter.setPen(Qt.PenStyle.NoPen)

        num_grains = int(rect.width() * rect.height() / 80)
        for _ in range(num_grains):
            x = rect.left() + random.random() * rect.width()
            y = rect.top() + random.random() * rect.height()
            size = random.random() * 1.2 + 0.3
            grain_c = grain_dark if random.random() < 0.6 else grain_light
            painter.setBrush(QBrush(grain_c))
            painter.drawEllipse(int(x), int(y), int(size), int(size))

        # --- More visible dot pattern (pore texture) ---
        dot_color = QColor(color.lighter(112))
        dot_color.setAlpha(45)  # Increased alpha (~40-50)
        painter.setBrush(QBrush(dot_color))

        for _ in range(int(rect.width() * rect.height() / 150)):
            x = rect.left() + random.random() * rect.width()
            y = rect.top() + random.random() * rect.height()
            size = random.random() * 2.0 + 0.5
            painter.drawEllipse(int(x), int(y), int(size), int(size))

        # --- Stitching border with contrasting color ---
        stitch_color = QColor(color.lighter(145))
        stitch_color.setAlpha(160)
        stitch_pen = QPen(stitch_color)
        stitch_pen.setWidth(1)
        stitch_pen.setDashPattern([6, 4])  # Larger dashes for visibility
        painter.setPen(stitch_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        margin = 8
        painter.drawRect(QRectF(
            rect.left() + margin, rect.top() + margin,
            rect.width() - margin * 2, rect.height() - margin * 2
        ))

        # Second inner stitch line for depth
        inner_stitch = QColor(0, 0, 0, 35)
        inner_pen = QPen(inner_stitch)
        inner_pen.setWidth(1)
        inner_pen.setDashPattern([6, 4])
        painter.setPen(inner_pen)
        painter.drawRect(QRectF(
            rect.left() + margin + 1.5, rect.top() + margin + 1.5,
            rect.width() - (margin + 1.5) * 2, rect.height() - (margin + 1.5) * 2
        ))

        painter.restore()

    @staticmethod
    def draw_sidebar_texture(painter: QPainter, rect: QRectF,
                             base_color: str = '#1a6b5a'):
        """Dibuja textura tipo tela/cuero verde oscuro para la sidebar (estilo Lotus)."""
        painter.save()

        color = QColor(base_color)

        # --- Stronger gradient with highlight in the center ---
        gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
        gradient.setColorAt(0.0, color.lighter(112))
        gradient.setColorAt(0.2, color.lighter(106))
        gradient.setColorAt(0.45, color.lighter(110))  # Center highlight
        gradient.setColorAt(0.55, color.lighter(108))
        gradient.setColorAt(0.8, color.darker(105))
        gradient.setColorAt(1.0, color.darker(115))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(rect)

        # --- Crosshatch texture (fabric/leather weave) ---
        line_color = QColor(color.lighter(110))
        line_color.setAlpha(32)  # Increased alpha (~30-35)
        pen = QPen(line_color, 0.5)
        painter.setPen(pen)

        spacing = 4
        x = rect.left()
        while x < rect.right():
            painter.drawLine(int(x), int(rect.top()), int(x), int(rect.bottom()))
            x += spacing

        y = rect.top()
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), int(y), int(rect.right()), int(y))
            y += spacing

        # --- Additional diagonal crosshatch for richer fabric feel ---
        diag_color = QColor(0, 0, 0, 12)
        diag_pen = QPen(diag_color, 0.3)
        painter.setPen(diag_pen)
        spacing_diag = 8
        x = rect.left() - rect.height()
        while x < rect.right():
            painter.drawLine(int(x), int(rect.bottom()),
                             int(x + rect.height()), int(rect.top()))
            x += spacing_diag

        # --- Embossed border/edge effect ---
        # Light inner edge (top & left)
        emboss_light = QColor(255, 255, 255, 25)
        emboss_pen_light = QPen(emboss_light, 1.5)
        painter.setPen(emboss_pen_light)
        painter.drawLine(int(rect.left() + 3), int(rect.top() + 3),
                         int(rect.right() - 3), int(rect.top() + 3))
        painter.drawLine(int(rect.left() + 3), int(rect.top() + 3),
                         int(rect.left() + 3), int(rect.bottom() - 3))

        # Dark inner edge (bottom & right)
        emboss_dark = QColor(0, 0, 0, 35)
        emboss_pen_dark = QPen(emboss_dark, 1.5)
        painter.setPen(emboss_pen_dark)
        painter.drawLine(int(rect.left() + 3), int(rect.bottom() - 3),
                         int(rect.right() - 3), int(rect.bottom() - 3))
        painter.drawLine(int(rect.right() - 3), int(rect.top() + 3),
                         int(rect.right() - 3), int(rect.bottom() - 3))

        # --- Vertical gradient band on the right side (cover edge) ---
        band_width = 10
        band_rect = QRectF(
            rect.right() - band_width, rect.top(),
            band_width, rect.height()
        )
        band_grad = QLinearGradient(band_rect.left(), 0, band_rect.right(), 0)
        band_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        band_grad.setColorAt(0.3, QColor(0, 0, 0, 30))
        band_grad.setColorAt(0.6, QColor(0, 0, 0, 50))
        band_grad.setColorAt(0.85, QColor(0, 0, 0, 35))
        band_grad.setColorAt(1.0, QColor(0, 0, 0, 55))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(band_grad))
        painter.drawRect(band_rect)

        painter.restore()

    @staticmethod
    def draw_green_felt_texture(painter: QPainter, rect: QRectF):
        """Dibuja textura de fieltro verde (tapete de escritorio) para el fondo."""
        painter.save()
        
        # Base dark green color
        base_color = QColor('#1e4235')
        
        # Subtle radial gradient to make the center slightly brighter (where the book is)
        center = rect.center()
        radius = max(rect.width(), rect.height())
        gradient = QRadialGradient(center, radius)
        gradient.setColorAt(0.0, base_color.lighter(110))
        gradient.setColorAt(1.0, base_color.darker(120))
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(rect)
        
        # Noise/Felt texture
        import random
        random.seed(84)
        
        num_grains = int(rect.width() * rect.height() / 150)
        
        # Draw light speckles
        painter.setBrush(QBrush(QColor(255, 255, 255, 15)))
        for _ in range(num_grains // 2):
            x = rect.left() + random.random() * rect.width()
            y = rect.top() + random.random() * rect.height()
            size = random.random() * 1.5 + 0.5
            painter.drawEllipse(int(x), int(y), int(size), int(size))
            
        # Draw dark speckles
        painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
        for _ in range(num_grains):
            x = rect.left() + random.random() * rect.width()
            y = rect.top() + random.random() * rect.height()
            size = random.random() * 1.5 + 0.5
            painter.drawEllipse(int(x), int(y), int(size), int(size))
            
        painter.restore()

    @staticmethod
    def draw_page_shadow(painter: QPainter, rect: QRectF, side: str = 'right'):
        """Dibuja sombra en el borde de una página para dar profundidad."""
        painter.save()

        shadow_width = 12  # Increased from 8

        if side == 'right':
            shadow_rect = QRectF(
                rect.right() - shadow_width, rect.top(),
                shadow_width, rect.height()
            )
            gradient = QLinearGradient(shadow_rect.left(), 0, shadow_rect.right(), 0)
            gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
            gradient.setColorAt(0.5, QColor(0, 0, 0, 15))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 40))  # +10 alpha
        elif side == 'left':
            shadow_rect = QRectF(
                rect.left(), rect.top(),
                shadow_width, rect.height()
            )
            gradient = QLinearGradient(shadow_rect.left(), 0, shadow_rect.right(), 0)
            gradient.setColorAt(0.0, QColor(0, 0, 0, 40))  # +10 alpha
            gradient.setColorAt(0.5, QColor(0, 0, 0, 15))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 0))
        elif side == 'bottom':
            shadow_rect = QRectF(
                rect.left(), rect.bottom() - shadow_width,
                rect.width(), shadow_width
            )
            gradient = QLinearGradient(0, shadow_rect.top(), 0, shadow_rect.bottom())
            gradient.setColorAt(0.0, QColor(0, 0, 0, 0))
            gradient.setColorAt(0.5, QColor(0, 0, 0, 10))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 30))  # +10 alpha
        else:
            painter.restore()
            return

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(shadow_rect)

        painter.restore()

    @staticmethod
    def draw_page_edge(painter: QPainter, rect: QRectF, side: str = 'right', cover_rect: QRectF = None):
        """Dibuja el efecto de borde de múltiples páginas apiladas (grosor del libro)."""
        painter.save()

        if cover_rect is None:
            max_width = 15
        else:
            if side == 'right':
                max_width = int(cover_rect.right() - rect.right() - 4)
            else:
                max_width = int(rect.left() - cover_rect.left() - 4)
                
        if max_width < 1:
            max_width = 15

        # --- Gradiente para el volumen de las páginas apiladas ---
        if side == 'right':
            grad = QLinearGradient(rect.right(), 0, rect.right() + max_width, 0)
            # De color claro (pegado a la página) a más oscuro (borde)
            grad.setColorAt(0.0, QColor(240, 235, 215))
            grad.setColorAt(0.4, QColor(225, 215, 195))
            grad.setColorAt(0.8, QColor(190, 180, 160))
            grad.setColorAt(1.0, QColor(160, 150, 130))
        else:
            grad = QLinearGradient(rect.left(), 0, rect.left() - max_width, 0)
            grad.setColorAt(0.0, QColor(240, 235, 215))
            grad.setColorAt(0.4, QColor(225, 215, 195))
            grad.setColorAt(0.8, QColor(190, 180, 160))
            grad.setColorAt(1.0, QColor(160, 150, 130))

        # --- Polígono para el efecto de perspectiva/curvatura ---
        from PyQt6.QtGui import QPainterPath
        path = QPainterPath()
        slope = 0.2  # Curvatura superior/inferior

        if side == 'right':
            path.moveTo(rect.right(), rect.top() + 4)
            path.lineTo(rect.right() + max_width, rect.top() + 4 + max_width * slope)
            path.lineTo(rect.right() + max_width, rect.bottom() - 4 - max_width * slope)
            path.lineTo(rect.right(), rect.bottom() - 4)
            path.closeSubpath()
        else:
            path.moveTo(rect.left(), rect.top() + 4)
            path.lineTo(rect.left() - max_width, rect.top() + 4 + max_width * slope)
            path.lineTo(rect.left() - max_width, rect.bottom() - 4 - max_width * slope)
            path.lineTo(rect.left(), rect.bottom() - 4)
            path.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # --- Líneas sutiles simulando hojas individuales ---
        pen_dark = QPen(QColor(0, 0, 0, 30), 0.5)
        painter.setPen(pen_dark)
        
        spacing = 2.5
        i = spacing
        while i < max_width:
            if side == 'right':
                x = rect.right() + i
            else:
                x = rect.left() - i
                
            painter.drawLine(
                int(x), int(rect.top() + 4 + i * slope),
                int(x), int(rect.bottom() - 4 - i * slope)
            )
            i += spacing

        # Línea de sombra final pegada al cuero
        final_x = rect.right() + max_width if side == 'right' else rect.left() - max_width
        painter.setPen(QPen(QColor(0, 0, 0, 80), 1.0))
        painter.drawLine(
            int(final_x), int(rect.top() + 4 + max_width * slope),
            int(final_x), int(rect.bottom() - 4 - max_width * slope)
        )

        painter.restore()
