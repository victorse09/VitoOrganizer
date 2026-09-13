# -*- coding: utf-8 -*-
"""
Vito Organizer — Constructor de la Interfaz Esqueumórfica (Estilo Lotus Original)
Crea la interfaz principal simulando una agenda física abierta con:
- Fondo de cuero verde oscuro con textura y biselado
- Páginas de papel cuadradas con agujeros perforados
- 6 anillas metálicas centrales
- Pestañas laterales estilo cartulina adheridas al papel
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy,
    QLabel, QPushButton
)
from PyQt6.QtCore import Qt, QRect, QRectF, QPointF, QSize, QPoint, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QLinearGradient,
    QRadialGradient, QFont, QPainterPath, QPolygonF
)
import random


# ─────────────────────────────────────────────────────────
# COLORES Y CONSTANTES DE DISEÑO (Estilo Clásico)
# ─────────────────────────────────────────────────────────

CUERO_BASE = "#3c4f4b"    # Verde grisáceo oscuro
CUERO_CLARO = "#4d605c"
CUERO_OSCURO = "#2b3b38"
PAPEL_FONDO = "#ffffff"   # Blanco/crema muy claro
PAPEL_SOMBRE = "#e8e8e8"
LINEA_PAPEL_H = "#e0e0e0" # Líneas horizontales
LINEA_PAPEL_V = "#ff9999" # Margen rojo
ANILLA_PLATA = "#dcdcdc"
ANILLA_OSCURA = "#707070"

# Colores de pestañas clásicos
TAB_COLORS = {
    "red": "#e33030",
    "green": "#1e8c45",
    "blue": "#2b5da8",
    "yellow": "#e8cc1c",
    "purple": "#8e388e",
    "brown": "#8c562b"
}


class TabButton(QWidget):
    """
    Pestaña personalizada adherida al lateral de la agenda.
    Se dibuja como un trapecio con QPainter y emite una señal al hacer clic.
    """
    clicked = pyqtSignal(str)

    def __init__(self, id_str: str, text: str, color_hex: str, side: str = "right", parent=None):
        super().__init__(parent)
        self.id_str = id_str
        self.text = text
        self.color_hex = color_hex
        self.side = side  # "left" o "right"
        self.is_selected = False
        
        self.setFixedSize(30, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        path = QPainterPath()

        if self.side == "right":
            path.moveTo(0, 0)
            path.lineTo(w - 5, 5)
            path.lineTo(w - 5, h - 5)
            path.lineTo(0, h)
            path.closeSubpath()
        else:
            path.moveTo(w, 0)
            path.lineTo(5, 5)
            path.lineTo(5, h - 5)
            path.lineTo(w, h)
            path.closeSubpath()

        # Color base con ligero gradiente
        base_color = QColor(self.color_hex)
        grad = QLinearGradient(0, 0, w, 0)
        
        if self.is_selected:
            grad.setColorAt(0, base_color.lighter(110))
            grad.setColorAt(1, base_color.lighter(130))
        else:
            grad.setColorAt(0, base_color.darker(110))
            grad.setColorAt(1, base_color)

        painter.fillPath(path, QBrush(grad))
        
        # Borde
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1))
        painter.drawPath(path)

        # Texto vertical
        painter.setPen(QColor("#ffffff") if base_color.lightness() < 150 else QColor("#000000"))
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        # Rotar texto
        painter.translate(w/2, h/2)
        if self.side == "right":
            painter.rotate(90)
        else:
            painter.rotate(-90)
            
        painter.drawText(QRect(-h//2, -w//2, h, w), Qt.AlignmentFlag.AlignCenter, self.text)
        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.id_str)


class PaperPageWidget(QWidget):
    """
    Página de la agenda con agujeros perforados, líneas de libreta, y sombras.
    Soporta pestañas en su borde exterior.
    """

    def __init__(self, side: str = "left", parent=None):
        super().__init__(parent)
        self.side = side
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumWidth(300)

        # Contenedor para el módulo interno
        self._layout = QVBoxLayout(self)
        
        # Márgenes: Dejar espacio para las pestañas y los agujeros
        if side == "left":
            self._layout.setContentsMargins(40, 20, 25, 20)
        else:
            self._layout.setContentsMargins(25, 20, 40, 20)
            
        self._layout.setSpacing(0)
        
        self.tabs = []

    def set_content(self, widget: QWidget):
        # Limpiar contenido anterior
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        if widget:
            self._layout.addWidget(widget)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        
        # Espacio para pestañas
        tab_space = 30
        
        if self.side == "left":
            rect_papel = QRectF(tab_space, 10, w - tab_space, h - 20)
        else:
            rect_papel = QRectF(0, 10, w - tab_space, h - 20)

        # Sombra del bloque de papel
        shadow_rect = rect_papel.translated(2 if self.side == "right" else -2, 3)
        painter.fillRect(shadow_rect, QColor(0, 0, 0, 40))

        # Dibujar papel
        painter.fillRect(rect_papel, QColor(PAPEL_FONDO))
        
        # Líneas de la libreta
        painter.setPen(QPen(QColor(LINEA_PAPEL_H), 1))
        for y in range(40, int(h - 20), 25):
            painter.drawLine(int(rect_papel.left()), y, int(rect_papel.right()), y)

        # Línea de margen rojo
        painter.setPen(QPen(QColor(LINEA_PAPEL_V), 1.5))
        if self.side == "left":
            painter.drawLine(int(rect_papel.left() + 30), 10, int(rect_papel.left() + 30), int(h - 10))
        else:
            painter.drawLine(int(rect_papel.left() + 20), 10, int(rect_papel.left() + 20), int(h - 10))

        # Dibujar agujeros perforados en el borde interior
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.setBrush(QBrush(QColor(CUERO_BASE))) # Hueco transparente que muestra el cuero
        
        num_anillas = 6
        spacing = (h - 20) / (num_anillas + 1)
        radio_agujero = 6
        
        for i in range(num_anillas):
            cy = 10 + spacing * (i + 1)
            if self.side == "left":
                cx = w - 10
            else:
                cx = 10
            painter.drawEllipse(QPointF(cx, cy), radio_agujero, radio_agujero)

        # Gradiente en el borde interior para simular la doblez de las hojas
        if self.side == "left":
            grad = QLinearGradient(w - 20, 0, w, 0)
            grad.setColorAt(0, QColor(0,0,0,0))
            grad.setColorAt(1, QColor(0,0,0,30))
            painter.fillRect(QRectF(w - 20, 10, 20, h - 20), grad)
        else:
            grad = QLinearGradient(0, 0, 20, 0)
            grad.setColorAt(0, QColor(0,0,0,30))
            grad.setColorAt(1, QColor(0,0,0,0))
            painter.fillRect(QRectF(0, 10, 20, h - 20), grad)

        painter.end()


class RingSpineWidget(QWidget):
    """
    Anillas metálicas centrales (Exactamente 6).
    Se superponen sobre el cuero y las hojas de papel.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(40)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        num_anillas = 6
        spacing = (h - 20) / (num_anillas + 1)
        
        # Sombra del lomo central (grieta oscura)
        spine_grad = QLinearGradient(0, 0, w, 0)
        spine_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
        spine_grad.setColorAt(0.4, QColor(0, 0, 0, 80))
        spine_grad.setColorAt(0.6, QColor(0, 0, 0, 80))
        spine_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        painter.fillRect(0, 0, w, h, spine_grad)

        anilla_alto = 24
        anilla_ancho = 32

        for i in range(num_anillas):
            cy = 10 + spacing * (i + 1)
            cx = w / 2

            # Sombra de la anilla proyectada en el papel
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 50))
            painter.drawRect(QRectF(cx - anilla_ancho/2 + 2, cy - anilla_alto/2 + 3, anilla_ancho, anilla_alto))

            # Gradiente metálico
            ring_grad = QLinearGradient(cx - anilla_ancho/2, cy - anilla_alto/2, cx + anilla_ancho/2, cy + anilla_alto/2)
            ring_grad.setColorAt(0.0, QColor("#e0e0e0"))
            ring_grad.setColorAt(0.3, QColor("#a0a0a0"))
            ring_grad.setColorAt(0.5, QColor("#f5f5f5"))
            ring_grad.setColorAt(0.7, QColor("#808080"))
            ring_grad.setColorAt(1.0, QColor("#404040"))

            painter.setPen(QPen(QColor("#303030"), 1))
            painter.setBrush(ring_grad)
            
            # Forma de la anilla (rectángulo redondeado simulando el arco)
            rect = QRectF(cx - anilla_ancho/2, cy - anilla_alto/2, anilla_ancho, anilla_alto)
            painter.drawRoundedRect(rect, 8, 8)
            
            # Hueco interior de la anilla
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(0,0,0, 60), 2))
            painter.drawRoundedRect(QRectF(cx - anilla_ancho/2 + 4, cy - anilla_alto/2 + 4, anilla_ancho - 8, anilla_alto - 8), 4, 4)

        painter.end()


class LeatherBackground(QWidget):
    """
    Fondo general de la aplicación.
    Textura de cuero con borde biselado estilo Windows 95/Lotus.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        # Pre-calcular puntos de ruido para la textura
        self.noise_points = []
        for _ in range(5000):
            self.noise_points.append((random.random(), random.random(), random.randint(0, 20)))

    def paintEvent(self, event):
        painter = QPainter(self)
        w, h = self.width(), self.height()

        # Relleno base
        painter.fillRect(0, 0, w, h, QColor(CUERO_BASE))
        
        # Textura (simulada con puntos translúcidos)
        painter.setPen(Qt.PenStyle.NoPen)
        for nx, ny, alpha in self.noise_points:
            painter.setBrush(QColor(0, 0, 0, alpha))
            painter.drawRect(int(nx * w), int(ny * h), 2, 2)

        # Marco exterior biselado (3D Bevel)
        painter.setPen(QPen(QColor(CUERO_CLARO), 4))
        painter.drawLine(0, 0, w, 0)
        painter.drawLine(0, 0, 0, h)
        
        painter.setPen(QPen(QColor(CUERO_OSCURO), 4))
        painter.drawLine(0, h, w, h)
        painter.drawLine(w, 0, w, h)
        
        # Costuras
        painter.setPen(QPen(QColor(0,0,0,100), 1, Qt.PenStyle.DashLine))
        painter.drawRect(8, 8, w - 16, h - 16)

        painter.end()


def crear_estilo_global() -> str:
    """
    QSS Clásico. Reemplaza los colores planos por el estilo de sistema.
    """
    return f"""
        QMainWindow {{
            background: {CUERO_BASE};
        }}
        QDialog {{
            background: #d4d0c8; /* Classic Win95 gray */
            color: #000000;
        }}
        QLabel {{
            color: #000000;
        }}
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {{
            background-color: #ffffff;
            color: #000000;
            border: 2px inset #808080;
            padding: 2px;
            font-family: "MS Sans Serif", Arial, sans-serif;
            font-size: 12px;
        }}
        QPushButton {{
            background-color: #d4d0c8;
            color: #000000;
            border: 2px outset #ffffff;
            border-bottom-color: #808080;
            border-right-color: #808080;
            padding: 4px 8px;
            font-family: "MS Sans Serif", Arial, sans-serif;
            font-size: 12px;
        }}
        QPushButton:pressed {{
            border: 2px inset #ffffff;
            border-top-color: #808080;
            border-left-color: #808080;
            padding-top: 5px;
            padding-left: 9px;
        }}
        QTableView, QListWidget, QTreeView {{
            background-color: #ffffff;
            color: #000000;
            border: 2px inset #808080;
            gridline-color: #c0c0c0;
            selection-background-color: #000080;
            selection-color: #ffffff;
            font-family: "MS Sans Serif", Arial, sans-serif;
            font-size: 12px;
        }}
        QHeaderView::section {{
            background-color: #d4d0c8;
            color: #000000;
            border: 1px outset #ffffff;
            border-bottom-color: #808080;
            border-right-color: #808080;
            padding: 4px;
        }}
        QComboBox {{
            background-color: #ffffff;
            color: #000000;
            border: 2px inset #808080;
            padding: 2px;
        }}
        QComboBox::drop-down {{
            background-color: #d4d0c8;
            border: 1px outset #ffffff;
            border-bottom-color: #808080;
            border-right-color: #808080;
            width: 16px;
        }}
    """

def crear_estilo_toolbar_papel() -> str:
    """
    QSS específico para toolbars que están sobre el papel.
    """
    return """
        QWidget#toolbar_papel {
            background: transparent;
            border-bottom: 1px solid #c0c0c0;
            padding: 2px;
        }
        QWidget#toolbar_papel QPushButton {
            background-color: transparent;
            border: 1px solid transparent;
            padding: 2px;
            min-width: 24px;
        }
        QWidget#toolbar_papel QPushButton:hover {
            border: 1px outset #ffffff;
            border-bottom-color: #808080;
            border-right-color: #808080;
        }
        QWidget#toolbar_papel QPushButton:pressed {
            border: 1px inset #ffffff;
            border-top-color: #808080;
            border-left-color: #808080;
        }
    """
