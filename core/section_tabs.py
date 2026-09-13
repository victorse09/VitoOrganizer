# =============================================================================
# Vito Organizer v2.2 - Section Tabs
# Pestañas/solapas de sección tipo agenda de papel (estilo Lotus Organizer)
# =============================================================================

import math
from enum import Enum
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QSize
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QFontMetrics,
    QLinearGradient, QPainterPath, QMouseEvent
)
from PyQt6.QtWidgets import QWidget

from typing import List, Tuple, Optional


class Side(Enum):
    LEFT = 1
    RIGHT = 2


class SectionTab:
    """Representa una pestaña individual de sección."""

    def __init__(self, plugin_id: str, name: str, color: str, order: int):
        self.plugin_id = plugin_id
        self.name = name
        self.color = color
        self.order = order
        self.rect: Optional[QRectF] = None  # Se calcula al dibujar


class SectionTabs(QWidget):
    """Widget que dibuja las pestañas/solapas de sección tipo agenda de papel.

    Comportamiento fiel a Lotus Organizer:
    - Las pestañas se muestran en los bordes derecho e izquierdo
    - La sección activa tiene su pestaña en el lado donde se seleccionó
    - Las secciones antes de la activa van al borde izquierdo
    - Las secciones después van al borde derecho
    """

    section_changed = pyqtSignal(str)  # Emite el plugin_id seleccionado

    # Dimensiones de las pestañas
    TAB_WIDTH = 26
    TAB_HEIGHT = 100
    TAB_SPACING = 2
    TAB_CORNER_RADIUS = 6

    def __init__(self, side: Side = Side.RIGHT, parent=None):
        super().__init__(parent)
        self.side = side
        self._tabs: List[SectionTab] = []
        self._active_id: Optional[str] = None
        self._required_columns = 1
        self.setMinimumWidth(self.TAB_WIDTH)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_tabs(self, tabs_data: List[Tuple[str, str, str, int]]):
        """Establece las pestañas."""
        self._tabs = [
            SectionTab(pid, name, color, order)
            for pid, name, color, order in tabs_data
        ]
        self._update_required_columns()
        self.update()

    def set_active(self, plugin_id: str):
        """Establece la pestaña activa."""
        self._active_id = plugin_id
        self.update()

    def get_active_id(self) -> Optional[str]:
        """Retorna el ID de la pestaña activa."""
        return self._active_id

    def sizeHint(self) -> QSize:
        return QSize(self.TAB_WIDTH * self._required_columns, 400)

    def minimumSizeHint(self) -> QSize:
        return QSize(self.TAB_WIDTH * self._required_columns, 200)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_required_columns()

    def _update_required_columns(self):
        h = self.height()
        if h < 50:
            return
        top_margin = 15
        available_height = max(1, h - top_margin * 2)
        total_tabs = len(self._tabs)
        if total_tabs == 0:
            return
            
        max_per_col = max(1, int(available_height / (self.TAB_HEIGHT + self.TAB_SPACING)))
        cols = math.ceil(total_tabs / max_per_col)
        
        if self._required_columns != cols:
            self._required_columns = cols
            self.setMinimumWidth(self.TAB_WIDTH * cols)
            self.updateGeometry()

    def paintEvent(self, event):
        """Dibuja las pestañas."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        if not self._tabs:
            return

        # Calcular posiciones
        self._calculate_tab_positions()

        # Las pestañas de la derecha representan páginas más profundas hacia atrás,
        # así que físicamente la pestaña con índice menor (más arriba/primero) está en la página SUPERIOR.
        # Por lo tanto, debemos dibujar de abajo hacia arriba (reverse) en la derecha,
        # y de arriba hacia abajo en la izquierda, para que el solapamiento 3D sea correcto.
        draw_list = list(self._tabs)
        if self.side == Side.RIGHT:
            draw_list.reverse()

        # Dibujar pestañas inactivas
        for tab in draw_list:
            if tab.plugin_id != self._active_id:
                self._draw_tab(painter, tab, is_active=False)

        # Dibujar la pestaña activa encima
        for tab in self._tabs:
            if tab.plugin_id == self._active_id:
                self._draw_tab(painter, tab, is_active=True)
                break

        painter.end()

    def _calculate_tab_positions(self):
        """Calcula las posiciones de cada pestaña escalonadas si no caben."""
        h = self.height()
        top_margin = 15
        bottom_margin = 15
        available_height = h - top_margin - bottom_margin
        total_tabs = len(self._tabs)

        if total_tabs == 0:
            return

        cols = self._required_columns
        
        y_step = self.TAB_HEIGHT + self.TAB_SPACING
        if cols > 1 and total_tabs > 1:
            # Escalonadas: comprimir para que quepan en la altura disponible
            y_step = (available_height - self.TAB_HEIGHT) / (total_tabs - 1)

        for i, tab in enumerate(self._tabs):
            if self.side == Side.RIGHT:
                # Anclar el bloque de pestañas a la parte inferior
                total_stack_height = (total_tabs - 1) * y_step + self.TAB_HEIGHT
                start_y = h - bottom_margin - total_stack_height
                # Evitar que suba más allá del margen superior si la altura es muy pequeña
                start_y = max(top_margin, start_y)
                y = start_y + i * y_step
            else:
                y = top_margin + i * y_step
                
            col_idx = i % cols
            
            # El ancho real de la pestaña depende de su columna.
            # Las de la columna 1 (segunda) son más anchas para que sobresalgan por debajo de la columna 0.
            tab_w = self.TAB_WIDTH * (col_idx + 1)
            
            if self.side == Side.RIGHT:
                x = 0
            else:
                x = self.width() - tab_w
                
            tab.rect = QRectF(x, y, tab_w, self.TAB_HEIGHT)

    def _draw_tab(self, painter: QPainter, tab: SectionTab, is_active: bool):
        """Dibuja una pestaña individual con aspecto de pestaña física de agenda."""
        if tab.rect is None:
            return

        rect = tab.rect
        color = QColor(tab.color)
        r = self.TAB_CORNER_RADIUS

        path = QPainterPath()
        if self.side == Side.RIGHT:
            # --- Build tab shape: left edge straight (connects to book), right side rounded ---
            path.moveTo(rect.left(), rect.top())                          # Top-left corner (straight)
            path.lineTo(rect.right() - r, rect.top())                    # Top edge to curve start
            path.arcTo(rect.right() - 2 * r, rect.top(),                 # Top-right rounded corner
                       2 * r, 2 * r, 90, -90)
            path.lineTo(rect.right(), rect.bottom() - r)                 # Right edge down
            path.arcTo(rect.right() - 2 * r, rect.bottom() - 2 * r,     # Bottom-right rounded corner
                       2 * r, 2 * r, 0, -90)
            path.lineTo(rect.left(), rect.bottom())                      # Bottom edge back (straight)
            path.closeSubpath()                                           # Close left edge (straight)
        else:
            # --- Left side: right edge straight, left side rounded ---
            path.moveTo(rect.right(), rect.top())                        # Top-right corner (straight)
            path.lineTo(rect.left() + r, rect.top())                     # Top edge to curve start
            path.arcTo(rect.left(), rect.top(),                          # Top-left rounded corner
                       2 * r, 2 * r, 90, 90)
            path.lineTo(rect.left(), rect.bottom() - r)                  # Left edge down
            path.arcTo(rect.left(), rect.bottom() - 2 * r,               # Bottom-left rounded corner
                       2 * r, 2 * r, 180, 90)
            path.lineTo(rect.right(), rect.bottom())                     # Bottom edge back (straight)
            path.closeSubpath()

        # Build border path (excluding the straight edge so it merges with the page)
        border_path = QPainterPath()
        if self.side == Side.RIGHT:
            border_path.moveTo(rect.left(), rect.top())
            border_path.lineTo(rect.right() - r, rect.top())
            border_path.arcTo(rect.right() - 2 * r, rect.top(),
                              2 * r, 2 * r, 90, -90)
            border_path.lineTo(rect.right(), rect.bottom() - r)
            border_path.arcTo(rect.right() - 2 * r, rect.bottom() - 2 * r,
                              2 * r, 2 * r, 0, -90)
            border_path.lineTo(rect.left(), rect.bottom())
        else:
            border_path.moveTo(rect.right(), rect.top())
            border_path.lineTo(rect.left() + r, rect.top())
            border_path.arcTo(rect.left(), rect.top(),
                              2 * r, 2 * r, 90, 90)
            border_path.lineTo(rect.left(), rect.bottom() - r)
            border_path.arcTo(rect.left(), rect.bottom() - 2 * r,
                              2 * r, 2 * r, 180, 90)
            border_path.lineTo(rect.right(), rect.bottom())

        if is_active:
            # === ACTIVE TAB: protruding, bright, beveled 3D ===
            shadow_path = QPainterPath(path)
            shadow_path.translate(1.5 if self.side == Side.RIGHT else -1.5, 2.0)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 70))
            painter.drawPath(shadow_path)

            gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
            gradient.setColorAt(0.0, QColor(255, 255, 255, 60))
            gradient.setColorAt(0.08, color.lighter(140))
            gradient.setColorAt(0.45, color.lighter(115))
            gradient.setColorAt(0.55, color)
            gradient.setColorAt(0.92, color.darker(115))
            gradient.setColorAt(1.0, QColor(0, 0, 0, 40))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawPath(path)

            painter.setPen(QPen(color.darker(160), 0.8))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(border_path)

            highlight_pen = QPen(QColor(255, 255, 255, 100), 1.2)
            painter.setPen(highlight_pen)
            if self.side == Side.RIGHT:
                painter.drawLine(
                    QPointF(rect.left() + 1, rect.top() + 1.0),
                    QPointF(rect.right() - r, rect.top() + 1.0)
                )
            else:
                painter.drawLine(
                    QPointF(rect.left() + r, rect.top() + 1.0),
                    QPointF(rect.right() - 1, rect.top() + 1.0)
                )

            text_color = QColor(255, 255, 255, 255)
            font_size = 10

        else:
            # === INACTIVE TAB: recessed, desaturated, tucked behind ===
            darker = color.darker(160)
            h_val, s_val, v_val, a_val = darker.getHsv()
            darker.setHsv(h_val, max(0, s_val - 40), max(0, v_val - 15), a_val)

            gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
            gradient.setColorAt(0.0, darker.lighter(115))
            gradient.setColorAt(0.5, darker)
            gradient.setColorAt(1.0, darker.darker(115))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawPath(path)
            
            painter.setPen(QPen(darker.darker(140), 0.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(border_path)

            inner_shadow_pen = QPen(QColor(0, 0, 0, 50), 1.0)
            painter.setPen(inner_shadow_pen)
            
            if self.side == Side.RIGHT:
                painter.drawLine(
                    QPointF(rect.left() + 1, rect.top() + 2),
                    QPointF(rect.right() - r, rect.top() + 2)
                )
                painter.drawLine(
                    QPointF(rect.right() - 2, rect.top() + r),
                    QPointF(rect.right() - 2, rect.bottom() - r)
                )
            else:
                painter.drawLine(
                    QPointF(rect.left() + r, rect.top() + 2),
                    QPointF(rect.right() - 1, rect.top() + 2)
                )
                painter.drawLine(
                    QPointF(rect.left() + 2, rect.top() + r),
                    QPointF(rect.left() + 2, rect.bottom() - r)
                )

            text_color = QColor(255, 255, 255, 220)
            font_size = 9

        # --- Draw vertical text ---
        painter.save()
        painter.setPen(text_color)

        font = QFont("Segoe UI", font_size)
        if font_size == 10:  # Fallback if Segoe UI not found
            font.setStyleHint(QFont.StyleHint.SansSerif)
        font.setBold(is_active)
        painter.setFont(font)

        # Centrar el texto SÓLO en la porción visible de la pestaña (la que sobresale)
        if self.side == Side.RIGHT:
            visible_rect = QRectF(rect.right() - self.TAB_WIDTH, rect.top(), self.TAB_WIDTH, self.TAB_HEIGHT)
        else:
            visible_rect = QRectF(rect.left(), rect.top(), self.TAB_WIDTH, self.TAB_HEIGHT)

        center = visible_rect.center()
        painter.translate(center.x(), center.y())
        
        if self.side == Side.RIGHT:
            painter.rotate(90)
        else:
            painter.rotate(-90)

        text_rect = QRectF(
            -visible_rect.height() / 2, -visible_rect.width() / 2,
            visible_rect.height(), visible_rect.width()
        )
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, tab.name)
        painter.restore()

    def mousePressEvent(self, event: QMouseEvent):
        """Maneja el click en una pestaña."""
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.position()
        # Verificar clics de arriba hacia abajo visualmente (reverso del dibujo para right)
        # Para clics, queremos verificar desde la capa superior hacia la inferior.
        # Active tab siempre está encima:
        if self._active_id:
            for tab in self._tabs:
                if tab.plugin_id == self._active_id and tab.rect and tab.rect.contains(pos):
                    return # Clic en la misma pestaña activa

        # Inactive tabs:
        # En la derecha, tab 0 tapa a tab 1, así que debemos chequear tab 0 primero.
        # Iterar en el mismo orden que dibujamos al revés.
        check_list = list(self._tabs)
        if self.side == Side.LEFT:
            check_list.reverse() # En left, tab 1 tapa a tab 0
            
        for tab in check_list:
            if tab.plugin_id != self._active_id and tab.rect and tab.rect.contains(pos):
                self._active_id = tab.plugin_id
                self.section_changed.emit(tab.plugin_id)
                self.update()
                break

