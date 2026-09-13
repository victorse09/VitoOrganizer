# =============================================================================
# Vito Organizer v2.2 - Trash Widget
# Widget de papelera personalizable con múltiples diseños 3D y vectoriales
# =============================================================================

import os
from PyQt6.QtCore import Qt, QSize, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QLinearGradient, QPainterPath, QFont
)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton


class TrashButton(QPushButton):
    """Botón personalizado que dibuja 5 estilos diferentes de papelera."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.has_items = False
        self.trash_style = 'classic_recycling'  # 'classic_recycling', 'metallic_mesh', 'green_dumpster', 'purple_flat', 'black_grid'

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        if width != 64 or height != 64:
            scale_factor = min(width / 64.0, height / 64.0)
            painter.scale(scale_factor, scale_factor)
            cx = 32.0
            cy = 32.0
        else:
            rect = self.rect()
            cx = rect.center().x()
            cy = rect.center().y()

        if self.trash_style == 'metallic_mesh':
            self._draw_metallic_mesh(painter, cx, cy)
        elif self.trash_style == 'green_dumpster':
            self._draw_green_dumpster(painter, cx, cy)
        elif self.trash_style == 'purple_flat':
            self._draw_purple_flat(painter, cx, cy)
        elif self.trash_style == 'black_grid':
            self._draw_black_grid(painter, cx, cy)
        elif self.trash_style == 'silver_metal_can':
            self._draw_silver_metal_can(painter, cx, cy)
        elif self.trash_style == 'white_plastic_bin':
            self._draw_white_plastic_bin(painter, cx, cy)
        elif self.trash_style == 'blue_plastic_bin':
            self._draw_blue_plastic_bin(painter, cx, cy)
        else:
            self._draw_classic_recycling(painter, cx, cy)

    # -------------------------------------------------------------------------
    # Estilo 1: Reciclaje Clásica (Blanca con flechas azules - Lotus / Win)
    # -------------------------------------------------------------------------
    def _draw_classic_recycling(self, painter: QPainter, cx: float, cy: float):
        w, h = 30, 36
        y_top = cy - h/2 + 2
        y_bot = cy + h/2 - 2

        # Cuerpo del bote blanco/gris metálico claro
        body = QPainterPath()
        body.moveTo(cx - w/2, y_top + 4)
        body.lineTo(cx + w/2, y_top + 4)
        body.lineTo(cx + w/2 - 2, y_bot - 2)
        body.quadTo(cx, y_bot + 4, cx - w/2 + 2, y_bot - 2)
        body.closeSubpath()

        grad = QLinearGradient(cx - w/2, 0, cx + w/2, 0)
        grad.setColorAt(0.0, QColor('#d8dcd8'))
        grad.setColorAt(0.3, QColor('#ffffff'))
        grad.setColorAt(0.7, QColor('#e0e4e0'))
        grad.setColorAt(1.0, QColor('#b5bab5'))

        painter.setPen(QPen(QColor('#757a75'), 1))
        painter.setBrush(QBrush(grad))
        painter.drawPath(body)

        # Simbolo de reciclaje azul en el centro
        painter.setPen(QPen(QColor('#0088cc'), 2))
        painter.drawArc(int(cx - 7), int(cy - 2), 14, 12, 30 * 16, 300 * 16)

        # Apertura superior / Aro
        rim = QRectF(cx - w/2 - 1, y_top, w + 2, 8)
        rim_grad = QLinearGradient(rim.left(), 0, rim.right(), 0)
        rim_grad.setColorAt(0, QColor('#b0b5b0'))
        rim_grad.setColorAt(0.5, QColor('#ffffff'))
        rim_grad.setColorAt(1, QColor('#909590'))
        painter.setPen(QPen(QColor('#656a65'), 1))
        painter.setBrush(QBrush(rim_grad))
        painter.drawEllipse(rim)

        # Interior oscuro
        inner = QRectF(cx - w/2 + 1, y_top + 1, w - 2, 6)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor('#4a504a')))
        painter.drawEllipse(inner)

        # Hojas de papel saliendo si está llena
        if self.has_items:
            painter.setPen(QPen(QColor('#b0b0b0'), 1))
            painter.setBrush(QBrush(QColor('#ffffff')))
            
            # Documento 1
            doc1 = QPainterPath()
            doc1.moveTo(cx - 8, y_top + 2)
            doc1.lineTo(cx - 6, y_top - 12)
            doc1.lineTo(cx + 2, y_top - 14)
            doc1.lineTo(cx + 4, y_top + 2)
            painter.drawPath(doc1)

            # Documento 2 doblado
            doc2 = QPainterPath()
            doc2.moveTo(cx - 2, y_top + 2)
            doc2.lineTo(cx, y_top - 15)
            doc2.lineTo(cx + 10, y_top - 11)
            doc2.lineTo(cx + 7, y_top + 2)
            painter.drawPath(doc2)

    # -------------------------------------------------------------------------
    # Estilo 2: Cesta Metálica Negra (Malla)
    # -------------------------------------------------------------------------
    def _draw_metallic_mesh(self, painter: QPainter, cx: float, cy: float):
        w, h = 32, 36
        y_top = cy - h/2 + 2
        y_bot = cy + h/2 - 2

        # Dibujar papeles dentro si está llena
        if self.has_items:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#e0e0e0')))
            painter.drawEllipse(int(cx - 10), int(y_top - 8), 20, 16)
            painter.setBrush(QBrush(QColor('#ffffff')))
            painter.drawEllipse(int(cx - 6), int(y_top - 12), 14, 12)

        # Cuerpo malla
        body = QPainterPath()
        body.moveTo(cx - w/2, y_top + 3)
        body.lineTo(cx + w/2, y_top + 3)
        body.lineTo(cx + w/2 - 1, y_bot - 3)
        body.lineTo(cx - w/2 + 1, y_bot - 3)
        body.closeSubpath()

        painter.setPen(QPen(QColor('#111111'), 1.5))
        painter.setBrush(QBrush(QColor(15, 15, 15, 200)))
        painter.drawPath(body)

        # Malla en diagonal (rejilla metálica)
        painter.setPen(QPen(QColor('#555555'), 0.8))
        for x in range(int(cx - w/2), int(cx + w/2), 4):
            painter.drawLine(x, int(y_top + 4), x + 6, int(y_bot - 3))
            painter.drawLine(x, int(y_top + 4), x - 6, int(y_bot - 3))

        # Aro superior e inferior metálico negro
        painter.setPen(QPen(QColor('#222222'), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(cx - w/2 - 1, y_top - 1, w + 2, 6))
        painter.drawEllipse(QRectF(cx - w/2 + 1, y_bot - 4, w - 2, 5))

    # -------------------------------------------------------------------------
    # Estilo 3: Contenedor Verde de Reciclaje
    # -------------------------------------------------------------------------
    def _draw_green_dumpster(self, painter: QPainter, cx: float, cy: float):
        w, h = 38, 30
        y_top = cy - h/2 + 4
        y_bot = cy + h/2 - 6

        # Basura sobresaliendo si está llena
        if self.has_items:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#d4a373'))) # Cartón
            painter.drawRect(int(cx - 12), int(y_top - 10), 12, 10)
            painter.setBrush(QBrush(QColor('#52b788'))) # Botella verde
            painter.drawRoundedRect(int(cx), int(y_top - 12), 6, 12, 2, 2)
            painter.setBrush(QBrush(QColor('#e9ecef'))) # Papeles
            painter.drawEllipse(int(cx + 5), int(y_top - 8), 10, 8)

        # Ruedas abajo
        painter.setPen(QPen(QColor('#111111'), 1))
        painter.setBrush(QBrush(QColor('#333333')))
        painter.drawEllipse(int(cx - 14), int(y_bot), 8, 8)
        painter.drawEllipse(int(cx + 6), int(y_bot), 8, 8)

        # Cuerpo del contenedor verde
        body = QPainterPath()
        body.moveTo(cx - w/2 + 2, y_top + 4)
        body.lineTo(cx + w/2 - 2, y_top + 4)
        body.lineTo(cx + w/2 - 5, y_bot + 2)
        body.lineTo(cx - w/2 + 5, y_bot + 2)
        body.closeSubpath()

        grad = QLinearGradient(cx - w/2, 0, cx + w/2, 0)
        grad.setColorAt(0, QColor('#2d6a4f'))
        grad.setColorAt(0.4, QColor('#52b788'))
        grad.setColorAt(1, QColor('#1b4332'))

        painter.setPen(QPen(QColor('#1b4332'), 1.5))
        painter.setBrush(QBrush(grad))
        painter.drawPath(body)

        # Borde / Tapa superior verde
        painter.setBrush(QBrush(QColor('#40916c')))
        painter.drawRoundedRect(QRectF(cx - w/2, y_top, w, 6), 2, 2)

        # Símbolo blanco de reciclaje en el frente
        painter.setPen(QPen(QColor('#ffffff'), 2))
        painter.drawArc(int(cx - 5), int(cy - 2), 10, 10, 0, 360 * 16)

    # -------------------------------------------------------------------------
    # Estilo 4: Balde Morado Moderno
    # -------------------------------------------------------------------------
    def _draw_purple_flat(self, painter: QPainter, cx: float, cy: float):
        w, h = 32, 34
        y_top = cy - h/2 + 2
        y_bot = cy + h/2 - 2

        # Papeles de colores saliendo si está llena
        if self.has_items:
            painter.setPen(Qt.PenStyle.NoPen)
            # Papel rosa / coral
            p1 = QPainterPath()
            p1.moveTo(cx - 6, y_top)
            p1.lineTo(cx - 10, y_top - 10)
            p1.lineTo(cx + 2, y_top - 6)
            p1.closeSubpath()
            painter.setBrush(QBrush(QColor('#ff8a75')))
            painter.drawPath(p1)

            # Papel salmón
            p2 = QPainterPath()
            p2.moveTo(cx - 2, y_top)
            p2.lineTo(cx + 4, y_top - 12)
            p2.lineTo(cx + 11, y_top - 5)
            p2.closeSubpath()
            painter.setBrush(QBrush(QColor('#ffb3ba')))
            painter.drawPath(p2)

        # Cuerpo balde morado
        body = QPainterPath()
        body.moveTo(cx - w/2, y_top + 3)
        body.lineTo(cx + w/2, y_top + 3)
        body.lineTo(cx + w/2 - 4, y_bot)
        body.lineTo(cx - w/2 + 4, y_bot)
        body.closeSubpath()

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor('#b197fc')))
        painter.drawPath(body)

        # Aro superior grueso morado oscuro
        painter.setBrush(QBrush(QColor('#7952b3')))
        painter.drawRoundedRect(QRectF(cx - w/2 - 1, y_top - 1, w + 2, 6), 3, 3)

    # -------------------------------------------------------------------------
    # Estilo 5: Cesta Rejilla Cuadrada Negra
    # -------------------------------------------------------------------------
    def _draw_black_grid(self, painter: QPainter, cx: float, cy: float):
        w, h = 32, 36
        y_top = cy - h/2 + 2
        y_bot = cy + h/2 - 2

        # Contenido bolsas de papel arrugado si está llena
        if self.has_items:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#d4a373')))
            painter.drawEllipse(int(cx - 10), int(y_top - 10), 20, 18)

        # Rejilla exterior negra gruesa
        painter.setPen(QPen(QColor('#111111'), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Contorno trapezoidal
        painter.drawLine(int(cx - w/2), int(y_top), int(cx + w/2), int(y_top))
        painter.drawLine(int(cx + w/2), int(y_top), int(cx + w/2 - 3), int(y_bot))
        painter.drawLine(int(cx + w/2 - 3), int(y_bot), int(cx - w/2 + 3), int(y_bot))
        painter.drawLine(int(cx - w/2 + 3), int(y_bot), int(cx - w/2), int(y_top))

        # Líneas verticales cuadradas
        for i in range(1, 4):
            t = i / 4.0
            x_top = (cx - w/2) + w * t
            x_bot = (cx - w/2 + 3) + (w - 6) * t
            painter.drawLine(int(x_top), int(y_top), int(x_bot), int(y_bot))

        # Líneas horizontales cuadradas
        for i in range(1, 5):
            t = i / 5.0
            y = y_top + (y_bot - y_top) * t
            x_left = (cx - w/2) + 3 * t
            x_right = (cx + w/2) - 3 * t
            painter.drawLine(int(x_left), int(y), int(x_right), int(y))

    def _draw_silver_metal_can(self, painter: QPainter, cx: float, cy: float):
        w, h = 32, 40
        y_top = cy - h/2 + 4
        y_bot = cy + h/2 - 2

        if self.has_items:
            # Draw floppy disk
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor('#333333')))
            painter.drawRect(int(cx - 10), int(y_top - 15), 18, 18)
            painter.setBrush(QBrush(QColor('#ffffff')))
            painter.drawRect(int(cx - 6), int(y_top - 15), 10, 8)
            # Draw yellow folder
            painter.setBrush(QBrush(QColor('#f4d03f')))
            painter.drawRect(int(cx - 4), int(y_top - 12), 16, 14)
            # Draw pencil
            painter.setPen(QPen(QColor('#f39c12'), 2))
            painter.drawLine(int(cx + 8), int(y_top), int(cx + 12), int(y_top - 16))

        # Can body
        painter.setPen(QPen(QColor('#888888'), 1))
        grad = QLinearGradient(cx - w/2, 0, cx + w/2, 0)
        grad.setColorAt(0, QColor('#d0d0d0'))
        grad.setColorAt(0.3, QColor('#ffffff'))
        grad.setColorAt(0.7, QColor('#c0c0c0'))
        grad.setColorAt(1, QColor('#a0a0a0'))
        painter.setBrush(QBrush(grad))
        
        # Draw cylinder
        body = QPainterPath()
        body.moveTo(cx - w/2, y_top)
        body.lineTo(cx - w/2, y_bot)
        body.quadTo(cx, y_bot + 4, cx + w/2, y_bot)
        body.lineTo(cx + w/2, y_top)
        body.quadTo(cx, y_top + 4, cx - w/2, y_top)
        painter.drawPath(body)

        # Vertical stripes
        painter.setPen(QPen(QColor('#a0a0a0'), 1))
        for i in range(1, 5):
            x = cx - w/2 + i * (w/5)
            painter.drawLine(int(x), int(y_top + 2), int(x), int(y_bot + 2))

        # 3D Embossed recycling logo
        painter.setPen(QPen(QColor('#f0f0f0'), 1))
        painter.drawArc(int(cx - 8), int(cy - 4), 16, 12, 30 * 16, 300 * 16)
        painter.setPen(QPen(QColor('#888888'), 1))
        painter.drawArc(int(cx - 7), int(cy - 3), 16, 12, 30 * 16, 300 * 16)

        # Top opening
        painter.setPen(QPen(QColor('#777777'), 1))
        painter.setBrush(QBrush(QColor('#e0e0e0')))
        painter.drawEllipse(int(cx - w/2), int(y_top - 4), int(w), 8)

    def _draw_white_plastic_bin(self, painter: QPainter, cx: float, cy: float):
        w, h = 34, 34
        y_top = cy - h/2 + 2
        y_bot = cy + h/2 - 2

        if self.has_items:
            # Crumpled white paper
            painter.setPen(QPen(QColor('#dddddd'), 1))
            painter.setBrush(QBrush(QColor('#ffffff')))
            for dx, dy, s in [(-8, -12, 16), (2, -14, 14), (-4, -6, 12)]:
                painter.drawEllipse(int(cx + dx), int(y_top + dy), s, s)

        # Semi-transparent white square bin
        painter.setPen(QPen(QColor('#cccccc'), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255, 220)))
        body = QPainterPath()
        body.moveTo(cx - w/2 - 2, y_top)
        body.lineTo(cx + w/2 + 2, y_top)
        body.lineTo(cx + w/2 - 2, y_bot)
        body.lineTo(cx - w/2 + 2, y_bot)
        body.closeSubpath()
        painter.drawPath(body)

        # Blue 3-arrow logo
        painter.setPen(QPen(QColor('#2196F3'), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(int(cx - 8), int(cy - 6), 16, 16, 0, 90 * 16)
        painter.drawArc(int(cx - 8), int(cy - 6), 16, 16, 120 * 16, 90 * 16)
        painter.drawArc(int(cx - 8), int(cy - 6), 16, 16, 240 * 16, 90 * 16)

    def _draw_blue_plastic_bin(self, painter: QPainter, cx: float, cy: float):
        w, h = 36, 38
        y_top = cy - h/2 + 4
        y_bot = cy + h/2 - 2

        if self.has_items:
            # Box and can and smell
            painter.setPen(QPen(QColor('#8b5a2b'), 1))
            painter.setBrush(QBrush(QColor('#cd853f')))
            painter.drawRect(int(cx - 12), int(y_top - 12), 14, 14) # box
            painter.setPen(QPen(QColor('#666666'), 1))
            painter.setBrush(QBrush(QColor('#aaaaaa')))
            painter.drawEllipse(int(cx + 2), int(y_top - 14), 10, 16) # can
            # Smell waves
            painter.setPen(QPen(QColor('#8fbc8f'), 2, Qt.PenStyle.DashLine))
            painter.drawLine(int(cx - 8), int(y_top - 18), int(cx - 4), int(y_top - 24))
            painter.drawLine(int(cx + 6), int(y_top - 20), int(cx + 10), int(y_top - 26))

        # Blue bucket
        painter.setPen(QPen(QColor('#0d47a1'), 1))
        grad = QLinearGradient(cx - w/2, 0, cx + w/2, 0)
        grad.setColorAt(0, QColor('#1976d2'))
        grad.setColorAt(0.5, QColor('#42a5f5'))
        grad.setColorAt(1, QColor('#1565c0'))
        painter.setBrush(QBrush(grad))
        
        body = QPainterPath()
        body.moveTo(cx - w/2 - 4, y_top)
        body.lineTo(cx + w/2 + 4, y_top)
        body.lineTo(cx + w/2 - 2, y_bot)
        body.quadTo(cx, y_bot + 4, cx - w/2 + 2, y_bot)
        body.closeSubpath()
        painter.drawPath(body)
        
        # White circular arrows
        painter.setPen(QPen(QColor('#ffffff'), 2))
        painter.drawArc(int(cx - 7), int(cy - 4), 14, 12, 45 * 16, 270 * 16)
        # small arrow head
        painter.setBrush(QBrush(QColor('#ffffff')))
        painter.setPen(Qt.PenStyle.NoPen)
        arrow = QPainterPath()
        arrow.moveTo(cx + 4, cy - 4)
        arrow.lineTo(cx + 10, cy - 1)
        arrow.lineTo(cx + 8, cy - 8)
        arrow.closeSubpath()
        painter.drawPath(arrow)

        # Top rim
        painter.setPen(QPen(QColor('#0b3c8a'), 1))
        painter.setBrush(QBrush(QColor('#1e88e5')))
        painter.drawEllipse(int(cx - w/2 - 4), int(y_top - 4), int(w + 8), 8)


class TrashWidget(QWidget):
    """Widget de papelera personalizable estilo Lotus Organizer."""

    trash_clicked = pyqtSignal()
    trash_emptied = pyqtSignal()
    item_restored = pyqtSignal(str, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._has_items = False
        self._setup_ui()

    def _setup_ui(self):
        """Configura la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Botón con icono de papelera
        self._trash_btn = TrashButton()
        self._trash_btn.setFixedSize(64, 64)
        self._trash_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._trash_btn.setToolTip("Abrir Papelera")
        self._trash_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 8px;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self._trash_btn.clicked.connect(self._on_click)

        layout.addWidget(self._trash_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self._update_icon()

    def set_trash_style(self, style: str):
        """Establece el estilo visual de la papelera."""
        self._trash_btn.trash_style = style
        self._trash_btn.update()

    def _update_icon(self):
        """Actualiza el icono según el estado de la papelera."""
        self._trash_btn.has_items = self._has_items
        self._trash_btn.update()

    def set_has_items(self, has_items: bool):
        """Establece si la papelera tiene items."""
        if self._has_items != has_items:
            self._has_items = has_items
            self._update_icon()

    def _on_click(self):
        """Maneja el click en la papelera."""
        self.trash_clicked.emit()
