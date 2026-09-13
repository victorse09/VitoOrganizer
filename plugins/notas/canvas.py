# =============================================================================
# Vito Organizer v2.2 - Handwriting Canvas Widget
# Lienzo interactivo para notas a mano alzada
# =============================================================================

import base64
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QImage
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel, QFrame


class HandwritingCanvasWidget(QWidget):
    """Widget de dibujo a mano alzada para notas manuscritas o bocetos."""
    
    canvas_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.drawing = False
        self.last_point = QPoint()
        self.pen_color = QColor("#111111")
        self.pen_width = 3
        
        self.image = QImage(600, 500, QImage.Format.Format_ARGB32)
        self.image.fill(QColor("#FFFFFF"))
        
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(6)

        # Barra de herramientas de dibujo
        toolbar = QFrame()
        toolbar.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.7); border: 1px solid #D0C070; border-radius: 6px; }")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(8)

        tb_layout.addWidget(QLabel("<b style='color:#333333; font-size:11px;'>Color:</b>"))
        
        self.color_combo = QComboBox()
        self.colors = [
            ("Negro", "#111111"),
            ("Azul", "#1e88e5"),
            ("Rojo", "#e53935"),
            ("Verde", "#43a047"),
            ("Morado", "#8e24aa"),
            ("Naranja", "#fb8c00")
        ]
        for name, hex_val in self.colors:
            self.color_combo.addItem(name, hex_val)
        self.color_combo.currentIndexChanged.connect(self._on_color_changed)
        tb_layout.addWidget(self.color_combo)

        tb_layout.addWidget(QLabel("<b style='color:#333333; font-size:11px;'>Grosor:</b>"))
        self.width_combo = QComboBox()
        self.width_combo.addItems(["Fino (2px)", "Medio (4px)", "Grueso (6px)", "Marcador (10px)"])
        self.width_combo.setCurrentIndex(1)
        self.width_combo.currentIndexChanged.connect(self._on_width_changed)
        tb_layout.addWidget(self.width_combo)

        tb_layout.addStretch()

        btn_clear = QPushButton("Limpiar")
        btn_clear.setStyleSheet("QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; border-radius: 4px; padding: 4px 8px; } QPushButton:hover { background-color: #e78284; }")
        btn_clear.clicked.connect(self.clear_canvas)
        tb_layout.addWidget(btn_clear)

        main_layout.addWidget(toolbar)

        # Área del lienzo
        self.canvas_frame = QFrame()
        self.canvas_frame.setStyleSheet("QFrame { background-color: #FFFFFF; border: 2px dashed #B0A890; border-radius: 8px; }")
        c_layout = QVBoxLayout(self.canvas_frame)
        c_layout.setContentsMargins(0, 0, 0, 0)
        
        main_layout.addWidget(self.canvas_frame, 1)

    def _on_color_changed(self, index):
        hex_val = self.color_combo.currentData()
        if hex_val:
            self.pen_color = QColor(hex_val)

    def _on_width_changed(self, index):
        widths = [2, 4, 6, 10]
        if 0 <= index < len(widths):
            self.pen_width = widths[index]

    def clear_canvas(self):
        self.image.fill(QColor("#FFFFFF"))
        self.update()
        self.canvas_changed.emit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            pos = self.mapToGlobal(event.pos())
            canvas_pos = self.canvas_frame.mapFromGlobal(pos)
            self.last_point = canvas_pos

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing:
            pos = self.mapToGlobal(event.pos())
            canvas_pos = self.canvas_frame.mapFromGlobal(pos)
            self._draw_line_to(canvas_pos)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            pos = self.mapToGlobal(event.pos())
            canvas_pos = self.canvas_frame.mapFromGlobal(pos)
            self._draw_line_to(canvas_pos)
            self.drawing = False

    def _draw_line_to(self, end_point):
        painter = QPainter(self.image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(self.pen_color, self.pen_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.drawLine(self.last_point, end_point)
        self.last_point = QPoint(end_point)
        self.update()
        self.canvas_changed.emit()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        canvas_rect = self.canvas_frame.geometry()
        painter.drawImage(canvas_rect, self.image)

    def get_image_base64(self) -> str:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        self.image.save(buffer, "PNG")
        encoded = base64.b64encode(buffer.data().data()).decode('utf-8')
        return encoded

    def load_image_base64(self, base64_str: str):
        if not base64_str:
            self.clear_canvas()
            return
        try:
            raw = base64.b64decode(base64_str)
            img = QImage()
            img.loadFromData(raw, "PNG")
            if not img.isNull():
                self.image = img.scaled(600, 500, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.update()
        except Exception as e:
            print(f"Error cargando imagen base64: {e}")
