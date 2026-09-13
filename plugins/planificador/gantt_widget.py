# =============================================================================
# Vito Organizer v2.2 - Authentic Gantt Chart Engine (Panoramic Split)
# Motor gráfico de Diagrama de Gantt con soporte para vista Panorámica Continua
# =============================================================================

from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, QRectF, pyqtSignal, QDate
from PyQt6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame


class GanttWidget(QWidget):
    """Widget de cronograma visual tipo Carta / Diagrama de Gantt."""
    
    stage_clicked = pyqtSignal(dict)

    def __init__(self, side: str = 'full', parent=None):
        super().__init__(parent)
        self.project = None
        self.stages = []
        self.side = side # 'full', 'left', 'right'
        self.setMinimumHeight(420)
        self.setStyleSheet("background: transparent;")

    def set_data(self, project: dict, stages: list):
        self.project = project
        self.stages = stages
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = QRectF(self.rect())
        
        # 1. Fondo de la hoja estilo libreta
        painter.setPen(QPen(QColor("#D0C070"), 1.5))
        painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
        painter.drawRoundedRect(rect, 8, 8)

        if not self.project or not self.stages:
            painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            painter.setPen(QColor("#666666"))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "📋 Selecciona un proyecto con etapas para visualizar el Diagrama de Gantt.")
            return

        # Dimensiones generales
        header_h1 = 24  # Cabecera de Semanas
        header_h2 = 20  # Cabecera de Días (L M X J V S D)
        header_total_h = header_h1 + header_h2
        legend_h = 36 if self.side in ('full', 'right') else 0   # Leyenda inferior en lado derecho o full
        
        left_margin = 10
        top_margin = 10
        right_margin = 10
        bottom_margin = 10
        
        left_col_w = 150 if self.side in ('full', 'left') else 0  # Columna de etapas solo en lado izquierdo o full
        right_badge_w = 40 if self.side in ('full', 'right') else 0 # Insignias a la derecha
        
        grid_x = rect.left() + left_margin + left_col_w
        grid_w = rect.width() - left_margin - right_margin - left_col_w - right_badge_w
        grid_y = rect.top() + top_margin + header_total_h
        grid_h = rect.height() - top_margin - bottom_margin - header_total_h - legend_h

        # 2. Dibujar Cabecera del Grid (Semanas y Días)
        hdr_rect_top = QRectF(grid_x, rect.top() + top_margin, grid_w, header_h1)
        hdr_rect_bot = QRectF(grid_x, rect.top() + top_margin + header_h1, grid_w, header_h2)
        
        painter.setPen(QPen(QColor("#B0A890"), 1))
        painter.setBrush(QBrush(QColor("#EAE6D0")))
        painter.drawRect(hdr_rect_top)
        painter.setBrush(QBrush(QColor("#F5F2E0")))
        painter.drawRect(hdr_rect_bot)

        # Columna de Etapas (Esquina Izquierda)
        if left_col_w > 0:
            corner_rect = QRectF(rect.left() + left_margin, rect.top() + top_margin, left_col_w, header_total_h)
            painter.setBrush(QBrush(QColor("#DCD6BA")))
            painter.drawRect(corner_rect)
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            painter.setPen(QColor("#111111"))
            painter.drawText(corner_rect, Qt.AlignmentFlag.AlignCenter, "Actividad / Etapa")

        # Determinación de rango de semanas según 'side'
        if self.side == 'left':
            weeks = [("Semana 1", 0), ("Semana 2", 4)]
            num_cols = 8
            start_global_col = 0
        elif self.side == 'right':
            weeks = [("Semana 3", 0), ("Semana 4", 4)]
            num_cols = 8
            start_global_col = 8
        else:
            weeks = [("Semana 1", 0), ("Semana 2", 4), ("Semana 3", 8), ("Semana 4", 12)]
            num_cols = 16
            start_global_col = 0

        col_w = grid_w / num_cols

        # Dibujar Semanas
        for w_name, w_col_offset in weeks:
            w_rect = QRectF(grid_x + (w_col_offset * col_w), rect.top() + top_margin, col_w * 4, header_h1)
            painter.setPen(QPen(QColor("#B0A890"), 1))
            painter.drawRect(w_rect)
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor("#333333"))
            painter.drawText(w_rect, Qt.AlignmentFlag.AlignCenter, w_name)

        # Dibujar Días y Franjas verticales de Fines de Semana
        day_initials = ["L", "M", "X", "J", "V", "S", "D"]
        for c in range(num_cols):
            global_c = start_global_col + c
            cx = grid_x + (c * col_w)
            d_initial = day_initials[global_c % 7]
            is_weekend = (global_c % 7) in (5, 6)
            
            d_rect = QRectF(cx, rect.top() + top_margin + header_h1, col_w, header_h2)
            painter.setPen(QPen(QColor("#C0B8A0"), 1))
            painter.setBrush(QBrush(QColor("#E8E2CB") if is_weekend else QColor("#F5F2E0")))
            painter.drawRect(d_rect)
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold if not is_weekend else QFont.Weight.Normal))
            painter.setPen(QColor("#D32F2F" if is_weekend else "#222222"))
            painter.drawText(d_rect, Qt.AlignmentFlag.AlignCenter, d_initial)

            col_bg_rect = QRectF(cx, grid_y, col_w, grid_h)
            if is_weekend:
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(QColor(230, 230, 230, 160)))
                painter.drawRect(col_bg_rect)
            
            painter.setPen(QPen(QColor("#E0E0E0"), 1, Qt.PenStyle.DotLine if not is_weekend else Qt.PenStyle.SolidLine))
            painter.drawLine(int(cx), int(grid_y), int(cx), int(grid_y + grid_h))

        # 3. Dibujar Filas y Barras de Gantt Continuas
        num_stages = len(self.stages)
        row_h = grid_h / max(1, min(10, num_stages))
        colors = ["#1e88e5", "#00897b", "#8e24aa", "#f57c00", "#43a047", "#d81b60", "#3949ab"]

        total_global_cols = 16

        for i, st in enumerate(self.stages):
            if i >= 10: break
            ry = grid_y + (i * row_h)

            painter.setPen(QPen(QColor("#E0D8C0"), 1))
            painter.drawLine(int(rect.left() + left_margin), int(ry + row_h), int(rect.right() - right_margin), int(ry + row_h))

            if left_col_w > 0:
                lbl_rect = QRectF(rect.left() + left_margin + 5, ry, left_col_w - 10, row_h)
                painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                painter.setPen(QColor("#222222"))
                painter.drawText(lbl_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, st.get('name', f'Etapa {i+1}'))

            # Posición global de la barra en la escala de 16 columnas
            g_start = (i * 2.2) % (total_global_cols - 4)
            g_span = max(3.0, (i % 3 + 4))
            g_end = g_start + g_span

            # Verificar si la barra se solapa con el rango visual de este widget
            v_start = max(start_global_col, g_start)
            v_end = min(start_global_col + num_cols, g_end)

            if v_start < v_end:
                b_x = grid_x + ((v_start - start_global_col) * col_w) + 1
                b_w = ((v_end - v_start) * col_w) - 2
                b_h = min(22.0, row_h - 8.0)
                b_y = ry + (row_h - b_h) / 2.0
                bar_rect = QRectF(b_x, b_y, b_w, b_h)

                st_color = QColor(colors[i % len(colors)])
                painter.setPen(QPen(st_color.darker(120), 1.5))
                painter.setBrush(QBrush(st_color))
                painter.drawRoundedRect(bar_rect, 4, 4)

                # Detalle esquina roja si inicia en esta página
                if g_start >= start_global_col and g_start < start_global_col + num_cols:
                    accent_path = QRectF(bar_rect.left(), bar_rect.top(), 6, 6)
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor("#D32F2F")))
                    painter.drawRect(accent_path)

                pct = max(0, min(100, st.get('progress', 0)))
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.setPen(QColor("#FFFFFF"))
                painter.drawText(bar_rect, Qt.AlignmentFlag.AlignCenter, f"{pct}%")

            # Badge de recurso a la derecha
            if right_badge_w > 0:
                badge_x = rect.right() - right_margin - right_badge_w + 8
                badge_rect = QRectF(badge_x, ry + (row_h - 22)/2, 22, 22)
                painter.setPen(QPen(QColor("#FFA726"), 1.5))
                painter.setBrush(QBrush(QColor("#FFE0B2")))
                painter.drawEllipse(badge_rect)
                painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                painter.setPen(QColor("#E65100"))
                painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, f"E{i+1}")

        # 4. Leyenda de Colores Inferior
        if legend_h > 0:
            leg_y = rect.bottom() - bottom_margin - legend_h + 4
            leg_rect = QRectF(rect.left() + left_margin, leg_y, rect.width() - left_margin - right_margin, legend_h - 4)
            painter.setPen(QPen(QColor("#B0A890"), 1))
            painter.setBrush(QBrush(QColor("#F5F2E0")))
            painter.drawRoundedRect(leg_rect, 4, 4)

            leg_items = [("En Planificación", "#1e88e5"), ("En Progreso", "#00897b"), ("En Revisión", "#8e24aa"), ("Completado", "#43a047")]
            item_w = leg_rect.width() / len(leg_items)
            for idx, (l_text, l_color) in enumerate(leg_items):
                ix = leg_rect.left() + (idx * item_w)
                box_r = QRectF(ix + 10, leg_y + 8, 14, 14)
                painter.setPen(QPen(QColor(l_color).darker(120), 1))
                painter.setBrush(QBrush(QColor(l_color)))
                painter.drawRect(box_r)

                txt_r = QRectF(ix + 30, leg_y, item_w - 32, legend_h - 4)
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.setPen(QColor("#333333"))
                painter.drawText(txt_r, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, l_text)
