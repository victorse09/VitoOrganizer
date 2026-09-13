# =============================================================================
# Vito Organizer v2.2 - Ring Binder
# Renderizado de encuadernación: anillas, espiral, clip, sin encuadernación
# =============================================================================

from PyQt6.QtCore import QRectF, QPointF, Qt
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient,
    QRadialGradient, QPainterPath
)


class RingBinder:
    """Renderiza los diferentes tipos de encuadernación entre las páginas."""

    RING_COUNT = 7          # Número de anillas
    RING_RADIUS = 16        # Radio de cada anilla (increased from 14)
    BINDER_WIDTH = 50       # Ancho de la zona central de encuadernación (increased from 40)

    @classmethod
    def draw(cls, binding_type: str, painter: QPainter, rect: QRectF,
             ring_color: str = '#B0B0B0'):
        """Dibuja la encuadernación según el tipo seleccionado."""
        binders = {
            'rings': cls.draw_rings,
            'spiral': cls.draw_spiral,
            'clip': cls.draw_clip,
            'none': cls.draw_none,
        }
        draw_func = binders.get(binding_type, cls.draw_rings)
        draw_func(painter, rect, ring_color)

    @classmethod
    def draw_rings(cls, painter: QPainter, rect: QRectF,
                   ring_color: str = '#B0B0B0'):
        """Dibuja anillas metálicas circulares tipo Lotus Organizer."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        center_x = rect.center().x()
        total_height = rect.height() - 80  # Margen arriba y abajo
        spacing = total_height / (cls.RING_COUNT + 1)

        # Fondo de la zona de encuadernación (lomo)
        spine_rect = QRectF(
            center_x - cls.BINDER_WIDTH / 2,
            rect.top(),
            cls.BINDER_WIDTH,
            rect.height()
        )

        # --- Dark leather/hard material spine gradient ---
        spine_grad = QLinearGradient(spine_rect.left(), 0, spine_rect.right(), 0)
        spine_grad.setColorAt(0.0, QColor('#3a2a1a'))   # Dark brown edge
        spine_grad.setColorAt(0.15, QColor('#4a3a2a'))   # Slightly lighter
        spine_grad.setColorAt(0.35, QColor('#5a4a38'))   # Leather mid-tone
        spine_grad.setColorAt(0.50, QColor('#625040'))   # Center highlight
        spine_grad.setColorAt(0.65, QColor('#5a4a38'))   # Symmetric
        spine_grad.setColorAt(0.85, QColor('#4a3a2a'))
        spine_grad.setColorAt(1.0, QColor('#3a2a1a'))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(spine_grad))
        painter.drawRect(spine_rect)

        # --- Vertical texture lines on the spine ---
        import random
        random.seed(99)
        texture_pen = QPen(QColor(0, 0, 0, 20), 0.5)
        painter.setPen(texture_pen)
        x = spine_rect.left() + 3
        while x < spine_rect.right() - 3:
            # Slightly irregular vertical lines for leather grain
            y_offset = random.random() * 4
            painter.drawLine(
                int(x), int(spine_rect.top() + y_offset),
                int(x), int(spine_rect.bottom() - y_offset)
            )
            x += 2 + random.random() * 1.5

        # Subtle horizontal grain marks
        grain_pen = QPen(QColor(255, 255, 255, 8), 0.3)
        painter.setPen(grain_pen)
        y = spine_rect.top() + 5
        while y < spine_rect.bottom() - 5:
            painter.drawLine(
                int(spine_rect.left() + 4), int(y),
                int(spine_rect.right() - 4), int(y)
            )
            y += 3 + random.random() * 2

        # --- Edge shadows on spine borders ---
        shadow_pen = QPen(QColor(0, 0, 0, 60), 1.5)
        painter.setPen(shadow_pen)
        painter.drawLine(
            int(spine_rect.left()), int(rect.top()),
            int(spine_rect.left()), int(rect.bottom())
        )
        painter.drawLine(
            int(spine_rect.right()), int(rect.top()),
            int(spine_rect.right()), int(rect.bottom())
        )

        # Inner highlight on left edge of spine
        highlight_pen = QPen(QColor(255, 255, 255, 20), 1)
        painter.setPen(highlight_pen)
        painter.drawLine(
            int(spine_rect.left() + 2), int(rect.top()),
            int(spine_rect.left() + 2), int(rect.bottom())
        )

        # Dibujar cada anilla
        for i in range(cls.RING_COUNT):
            y = rect.top() + 40 + spacing * (i + 1)
            cls._draw_single_ring(painter, center_x, y, cls.RING_RADIUS, ring_color)

        painter.restore()

    @classmethod
    def _draw_single_ring(cls, painter: QPainter, cx: float, cy: float,
                          radius: int, ring_color: str):
        """Dibuja una anilla individual (alargada y plana) con efecto metálico 3D."""
        rx = radius + 12  # Más ancha para alcanzar los agujeros
        ry = radius - 8   # Más plana verticalmente

        # --- Drop shadow for ring ---
        shadow_color = QColor(0, 0, 0, 90)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(shadow_color))
        painter.drawEllipse(QPointF(cx + 1, cy + 3), rx, ry)

        # --- Anilla exterior con gradiente metálico ---
        ring_grad = QRadialGradient(cx, cy - ry/2, rx * 1.5)
        base_color = QColor(ring_color)
        ring_grad.setColorAt(0.0, base_color.lighter(180))
        ring_grad.setColorAt(0.2, base_color.lighter(140))
        ring_grad.setColorAt(0.5, base_color)
        ring_grad.setColorAt(0.8, base_color.darker(140))
        ring_grad.setColorAt(1.0, base_color.darker(180))

        # Thicker ring (pen width 5)
        pen = QPen(QBrush(ring_grad), 5.5)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), rx, ry)

        # --- Primary metallic highlight arc (upper part) ---
        highlight = QPen(QColor(255, 255, 255, 140), 2.0)
        painter.setPen(highlight)
        path1 = QPainterPath()
        path1.arcMoveTo(cx - rx + 2, cy - ry + 2, (rx - 2) * 2, (ry - 2) * 2, 160)
        path1.arcTo(cx - rx + 2, cy - ry + 2, (rx - 2) * 2, (ry - 2) * 2, 160, 60)
        painter.drawPath(path1)

        # --- Dark contour on bottom for 3D depth ---
        dark_edge = QPen(QColor(0, 0, 0, 80), 1.5)
        painter.setPen(dark_edge)
        path3 = QPainterPath()
        path3.arcMoveTo(cx - rx, cy - ry, rx * 2, ry * 2, -30)
        path3.arcTo(cx - rx, cy - ry, rx * 2, ry * 2, -30, -120)
        painter.drawPath(path3)

    @classmethod
    def draw_spiral(cls, painter: QPainter, rect: QRectF,
                    ring_color: str = '#B0B0B0'):
        """Dibuja encuadernación de espiral continua."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        center_x = rect.center().x()
        spiral_width = 20
        coil_height = 16
        num_coils = int((rect.height() - 60) / coil_height)

        # --- Fondo del lomo con tonos cuero oscuro ---
        spine_rect = QRectF(
            center_x - spiral_width / 2 - 5,
            rect.top(),
            spiral_width + 10,
            rect.height()
        )
        spine_grad = QLinearGradient(spine_rect.left(), 0, spine_rect.right(), 0)
        spine_grad.setColorAt(0.0, QColor('#3a2a1a'))
        spine_grad.setColorAt(0.3, QColor('#4a3a2a'))
        spine_grad.setColorAt(0.5, QColor('#554838'))
        spine_grad.setColorAt(0.7, QColor('#4a3a2a'))
        spine_grad.setColorAt(1.0, QColor('#3a2a1a'))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(spine_grad))
        painter.drawRect(spine_rect)

        # Dibujar espiral (diseño 3D y más realista)
        base_color = QColor(ring_color)
        shadow_pen = QPen(QColor(0, 0, 0, 70), 3.5)
        shadow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        main_pen = QPen(base_color, 2.5)
        main_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        dark_pen = QPen(base_color.darker(150), 3.0)
        dark_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        
        highlight_pen = QPen(QColor(255, 255, 255, 180), 1.0)
        
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for i in range(num_coils):
            y = rect.top() + 30 + i * coil_height
            
            # Sombra base
            path = QPainterPath()
            path.moveTo(center_x - spiral_width / 2 + 1, y + 2)
            path.cubicTo(
                center_x - spiral_width / 2 + 1, y + coil_height * 0.5 + 2,
                center_x + spiral_width / 2 + 1, y + coil_height * 0.5 + 2,
                center_x + spiral_width / 2 + 1, y + coil_height + 2
            )
            painter.setPen(shadow_pen)
            painter.drawPath(path)
            
            # Lazo oscuro para volumen
            path = QPainterPath()
            path.moveTo(center_x - spiral_width / 2, y)
            path.cubicTo(
                center_x - spiral_width / 2, y + coil_height * 0.5,
                center_x + spiral_width / 2, y + coil_height * 0.5,
                center_x + spiral_width / 2, y + coil_height
            )
            painter.setPen(dark_pen)
            painter.drawPath(path)
            
            # Línea principal
            painter.setPen(main_pen)
            painter.drawPath(path)

            # Highlight
            path_hl = QPainterPath()
            path_hl.moveTo(center_x - spiral_width / 4, y + coil_height * 0.15)
            path_hl.cubicTo(
                center_x, y + coil_height * 0.35,
                center_x + spiral_width / 4, y + coil_height * 0.35,
                center_x + spiral_width / 3, y + coil_height * 0.7
            )
            painter.setPen(highlight_pen)
            painter.drawPath(path_hl)

        painter.restore()

    @classmethod
    def draw_clip(cls, painter: QPainter, rect: QRectF,
                  ring_color: str = '#B0B0B0'):
        """Dibuja encuadernación tipo clip/acoplamiento."""
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        center_x = rect.center().x()
        clip_width = 30
        clip_height = 50
        num_clips = 5
        total_height = rect.height() - 80
        spacing = total_height / (num_clips + 1)

        # --- Fondo del lomo con tonos cuero oscuro ---
        spine_rect = QRectF(
            center_x - 8,
            rect.top(),
            16,
            rect.height()
        )
        spine_grad = QLinearGradient(spine_rect.left(), 0, spine_rect.right(), 0)
        spine_grad.setColorAt(0.0, QColor('#3a2a1a'))
        spine_grad.setColorAt(0.5, QColor('#4a3a2a'))
        spine_grad.setColorAt(1.0, QColor('#3a2a1a'))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(spine_grad))
        painter.drawRect(spine_rect)

        for i in range(num_clips):
            y = rect.top() + 40 + spacing * (i + 1) - clip_height / 2
            cls._draw_single_clip(painter, center_x, y, clip_width, clip_height, ring_color)

        painter.restore()

    @classmethod
    def _draw_single_clip(cls, painter: QPainter, cx: float, cy: float,
                          width: int, height: int, color: str):
        """Dibuja un clip individual."""
        clip_color = QColor(color)

        # Cuerpo del clip
        path = QPainterPath()
        path.moveTo(cx - width / 2, cy)
        path.lineTo(cx - width / 2, cy + height - 10)
        path.arcTo(cx - width / 2, cy + height - 20, width, 20, 180, 180)
        path.lineTo(cx + width / 2, cy + 10)
        path.arcTo(cx - width / 2 + 5, cy, width - 10, 20, 0, 180)
        path.lineTo(cx - width / 2 + 5, cy + height - 15)

        pen = QPen(clip_color, 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)

        # Highlight
        highlight = QPen(QColor(255, 255, 255, 60), 1)
        painter.setPen(highlight)
        painter.drawLine(int(cx - width / 2 + 1), int(cy + 5),
                         int(cx - width / 2 + 1), int(cy + height - 15))

    @classmethod
    def draw_none(cls, painter: QPainter, rect: QRectF,
                  ring_color: str = '#B0B0B0'):
        """Sin encuadernación - solo una línea divisoria sutil."""
        painter.save()
        center_x = rect.center().x()

        # Línea divisoria sutil
        pen = QPen(QColor(0, 0, 0, 30), 1)
        painter.setPen(pen)
        painter.drawLine(
            int(center_x), int(rect.top() + 10),
            int(center_x), int(rect.bottom() - 10)
        )

        # Sombra central sutil
        for i in range(5):
            alpha = 20 - i * 4
            if alpha <= 0:
                break
            shadow_pen = QPen(QColor(0, 0, 0, alpha), 1)
            painter.setPen(shadow_pen)
            painter.drawLine(
                int(center_x - i), int(rect.top() + 10),
                int(center_x - i), int(rect.bottom() - 10)
            )
            painter.drawLine(
                int(center_x + i), int(rect.top() + 10),
                int(center_x + i), int(rect.bottom() - 10)
            )

        painter.restore()

    @classmethod
    def get_binder_width(cls, binding_type: str) -> int:
        """Retorna el ancho de la zona de encuadernación."""
        widths = {
            'rings': cls.BINDER_WIDTH,
            'spiral': 30,
            'clip': 30,
            'none': 6,
        }
        return widths.get(binding_type, cls.BINDER_WIDTH)
