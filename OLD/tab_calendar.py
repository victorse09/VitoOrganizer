# -*- coding: utf-8 -*-
"""
Vito Organizer — Módulo de Calendario / Agenda
Proporciona vistas mensual y semanal con gestión completa de eventos.
Incluye diálogo de creación/edición y panel lateral de eventos del día.
"""

import calendar
from datetime import date, datetime, timedelta
from typing import Optional

from PyQt6.QtCore import (
    Qt, QDate, QTime, QRect, QRectF, QPoint, QSize, pyqtSignal
)
from PyQt6.QtGui import (
    QPainter, QColor, QFont, QFontMetrics, QPen, QBrush,
    QMouseEvent, QPaintEvent, QIcon, QAction, QPixmap
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDialog, QLineEdit, QTextEdit, QDateEdit, QTimeEdit,
    QComboBox, QDialogButtonBox, QFormLayout, QScrollArea,
    QSizePolicy, QListWidget, QListWidgetItem, QMenu,
    QMessageBox, QSpacerItem, QFrame, QGridLayout, QSplitter,
    QAbstractItemView, QStackedWidget
)

from database import Database
from svg_icons import (
    icon_new, icon_delete, icon_edit, icon_arrow_left,
    icon_arrow_right, icon_today, icon_week, icon_calendar,
    svg_to_qicon
)


# ═══════════════════════════════════════════════════════════
# CONSTANTES
# ═══════════════════════════════════════════════════════════

# Nombres en español
NOMBRES_MESES = [
    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

NOMBRES_DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

NOMBRES_DIAS_COMPLETOS = [
    "Lunes", "Martes", "Miércoles", "Jueves",
    "Viernes", "Sábado", "Domingo"
]

# Colores de la aplicación
COLOR_FONDO_PAPEL = "#FDF5E6"
COLOR_LINEA_GRILLA = "#D4C5A9"
COLOR_CABECERA_DIA = "#4A3728"
COLOR_TEXTO_NORMAL = "#2C1810"
COLOR_TEXTO_GRIS = "#B0A090"
COLOR_HOY = "#E74C3C"
COLOR_SELECCION = "#3498DB"
COLOR_ICONO = "#4A3728"

# Colores predefinidos para eventos
COLORES_EVENTOS = [
    ("#E74C3C", "Rojo"),
    ("#E67E22", "Naranja"),
    ("#F1C40F", "Amarillo"),
    ("#27AE60", "Verde"),
    ("#3498DB", "Azul"),
    ("#9B59B6", "Púrpura"),
    ("#1ABC9C", "Turquesa"),
    ("#34495E", "Gris oscuro"),
]

# Rango horario para vista semanal
HORA_INICIO = 8   # 08:00
HORA_FIN = 22     # 22:00

# Hoja de estilo global para el módulo
ESTILO_MODULO = """
    QWidget#tabCalendar {
        background-color: #FDF5E6;
    }
    QLabel {
        color: #2C1810;
        background: transparent;
    }
    QPushButton {
        background-color: #EDE0C8;
        color: #2C1810;
        border: 1px solid #C4B590;
        border-radius: 4px;
        padding: 5px 12px;
        font-size: 13px;
    }
    QPushButton:hover {
        background-color: #DDD0B0;
        border-color: #A09070;
    }
    QPushButton:pressed {
        background-color: #CCC0A0;
    }
    QPushButton:checked {
        background-color: #4A3728;
        color: #FDF5E6;
        border-color: #2C1810;
    }
    QListWidget {
        background-color: #FDF5E6;
        border: 1px solid #D4C5A9;
        border-radius: 4px;
        color: #2C1810;
        font-size: 13px;
        outline: none;
    }
    QListWidget::item {
        padding: 6px 8px;
        border-bottom: 1px solid #EDE0C8;
    }
    QListWidget::item:selected {
        background-color: #EDE0C8;
        color: #2C1810;
    }
    QListWidget::item:hover {
        background-color: #F5ECD4;
    }
    QScrollArea {
        background-color: #FDF5E6;
        border: none;
    }
    QFrame#panelEventos {
        background-color: #FDF5E6;
        border-left: 1px solid #D4C5A9;
    }
"""


# ═══════════════════════════════════════════════════════════
# DIÁLOGO DE EVENTO
# ═══════════════════════════════════════════════════════════

class EventDialog(QDialog):
    """
    Diálogo para crear o editar un evento.
    Campos: título, descripción, fecha/hora inicio, fecha/hora fin, color.
    """

    def __init__(
        self,
        parent: QWidget = None,
        evento: Optional[dict] = None,
        fecha_inicial: Optional[QDate] = None,
        hora_inicial: Optional[QTime] = None
    ):
        """
        Inicializa el diálogo de evento.

        Args:
            parent: Widget padre.
            evento: Diccionario del evento existente (None para nuevo).
            fecha_inicial: Fecha preseleccionada para eventos nuevos.
            hora_inicial: Hora preseleccionada para eventos nuevos.
        """
        super().__init__(parent)
        self.evento = evento
        self.setWindowTitle("Editar Evento" if evento else "Nuevo Evento")
        self.setMinimumWidth(420)
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLOR_FONDO_PAPEL};
            }}
            QLabel {{
                color: {COLOR_TEXTO_NORMAL};
                font-size: 13px;
            }}
            QLineEdit, QTextEdit, QDateEdit, QTimeEdit, QComboBox {{
                background-color: #FFFFFF;
                border: 1px solid {COLOR_LINEA_GRILLA};
                border-radius: 4px;
                padding: 4px 8px;
                color: {COLOR_TEXTO_NORMAL};
                font-size: 13px;
            }}
            QLineEdit:focus, QTextEdit:focus, QDateEdit:focus,
            QTimeEdit:focus, QComboBox:focus {{
                border-color: {COLOR_SELECCION};
            }}
            QPushButton {{
                background-color: #EDE0C8;
                color: {COLOR_TEXTO_NORMAL};
                border: 1px solid #C4B590;
                border-radius: 4px;
                padding: 6px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #DDD0B0;
            }}
        """)
        self._construir_ui(fecha_inicial, hora_inicial)
        if evento:
            self._cargar_evento(evento)

    def _construir_ui(
        self,
        fecha_inicial: Optional[QDate],
        hora_inicial: Optional[QTime]
    ):
        """Construye la interfaz del diálogo."""
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Título ──
        self.txt_titulo = QLineEdit()
        self.txt_titulo.setPlaceholderText("Título del evento")
        layout.addRow("Título:", self.txt_titulo)

        # ── Descripción ──
        self.txt_descripcion = QTextEdit()
        self.txt_descripcion.setPlaceholderText("Descripción (opcional)")
        self.txt_descripcion.setMaximumHeight(80)
        layout.addRow("Descripción:", self.txt_descripcion)

        # ── Fecha y hora de inicio ──
        contenedor_inicio = QHBoxLayout()
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        if fecha_inicial:
            self.fecha_inicio.setDate(fecha_inicial)
        else:
            self.fecha_inicio.setDate(QDate.currentDate())

        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setDisplayFormat("HH:mm")
        if hora_inicial:
            self.hora_inicio.setTime(hora_inicial)
        else:
            self.hora_inicio.setTime(QTime(9, 0))

        contenedor_inicio.addWidget(self.fecha_inicio)
        contenedor_inicio.addWidget(self.hora_inicio)
        layout.addRow("Inicio:", contenedor_inicio)

        # ── Fecha y hora de fin ──
        contenedor_fin = QHBoxLayout()
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDisplayFormat("dd/MM/yyyy")
        if fecha_inicial:
            self.fecha_fin.setDate(fecha_inicial)
        else:
            self.fecha_fin.setDate(QDate.currentDate())

        self.hora_fin = QTimeEdit()
        self.hora_fin.setDisplayFormat("HH:mm")
        if hora_inicial:
            # Por defecto, el evento dura 1 hora
            fin = hora_inicial.addSecs(3600)
            self.hora_fin.setTime(fin)
        else:
            self.hora_fin.setTime(QTime(10, 0))

        contenedor_fin.addWidget(self.fecha_fin)
        contenedor_fin.addWidget(self.hora_fin)
        layout.addRow("Fin:", contenedor_fin)

        # ── Color del evento ──
        self.combo_color = QComboBox()
        for color_hex, color_nombre in COLORES_EVENTOS:
            self.combo_color.addItem(color_nombre, color_hex)
            # Poner un ícono cuadrado de color
            idx = self.combo_color.count() - 1
            pixmap = QIcon(_crear_pixmap_color(color_hex))
            self.combo_color.setItemIcon(idx, pixmap)
        layout.addRow("Color:", self.combo_color)

        # ── Botones OK / Cancelar ──
        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(
            QDialogButtonBox.StandardButton.Ok
        ).setText("Guardar")
        self.botones.button(
            QDialogButtonBox.StandardButton.Cancel
        ).setText("Cancelar")
        self.botones.accepted.connect(self._validar_y_aceptar)
        self.botones.rejected.connect(self.reject)
        layout.addRow(self.botones)

    def _cargar_evento(self, evento: dict):
        """Carga los datos de un evento existente en los campos."""
        self.txt_titulo.setText(evento.get("title", ""))
        self.txt_descripcion.setPlainText(evento.get("description", ""))

        # Parsear fecha/hora de inicio
        inicio = _parsear_datetime(evento.get("start_datetime", ""))
        if inicio:
            self.fecha_inicio.setDate(
                QDate(inicio.year, inicio.month, inicio.day)
            )
            self.hora_inicio.setTime(
                QTime(inicio.hour, inicio.minute)
            )

        # Parsear fecha/hora de fin
        fin = _parsear_datetime(evento.get("end_datetime", ""))
        if fin:
            self.fecha_fin.setDate(
                QDate(fin.year, fin.month, fin.day)
            )
            self.hora_fin.setTime(
                QTime(fin.hour, fin.minute)
            )

        # Seleccionar color
        color_evento = evento.get("color", "#3498DB")
        for i in range(self.combo_color.count()):
            if self.combo_color.itemData(i) == color_evento:
                self.combo_color.setCurrentIndex(i)
                break

    def _validar_y_aceptar(self):
        """Valida los campos antes de aceptar."""
        if not self.txt_titulo.text().strip():
            QMessageBox.warning(
                self, "Campo requerido",
                "El título del evento es obligatorio."
            )
            self.txt_titulo.setFocus()
            return

        # Validar que la fecha/hora de fin sea posterior a la de inicio
        inicio_dt = self._obtener_datetime_inicio()
        fin_dt = self._obtener_datetime_fin()
        if fin_dt <= inicio_dt:
            QMessageBox.warning(
                self, "Fechas inválidas",
                "La fecha/hora de fin debe ser posterior a la de inicio."
            )
            return

        self.accept()

    def obtener_datos(self) -> dict:
        """Devuelve los datos del formulario como diccionario."""
        return {
            "title": self.txt_titulo.text().strip(),
            "description": self.txt_descripcion.toPlainText().strip(),
            "start_datetime": self._obtener_datetime_inicio().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "end_datetime": self._obtener_datetime_fin().strftime(
                "%Y-%m-%d %H:%M"
            ),
            "color": self.combo_color.currentData(),
        }

    def _obtener_datetime_inicio(self) -> datetime:
        """Construye un datetime a partir de los campos de inicio."""
        d = self.fecha_inicio.date()
        t = self.hora_inicio.time()
        return datetime(d.year(), d.month(), d.day(), t.hour(), t.minute())

    def _obtener_datetime_fin(self) -> datetime:
        """Construye un datetime a partir de los campos de fin."""
        d = self.fecha_fin.date()
        t = self.hora_fin.time()
        return datetime(d.year(), d.month(), d.day(), t.hour(), t.minute())


# ═══════════════════════════════════════════════════════════
# WIDGET DE GRILLA MENSUAL (pintado con QPainter)
# ═══════════════════════════════════════════════════════════

class MonthGridWidget(QWidget):
    """
    Widget personalizado que dibuja la grilla del calendario mensual.
    Usa QPainter para renderizar días, eventos y selección.
    """

    # Señales
    dia_seleccionado = pyqtSignal(date)       # Clic en un día
    dia_doble_clic = pyqtSignal(date)          # Doble clic en un día

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumSize(350, 300)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Estado del calendario
        self._anio: int = date.today().year
        self._mes: int = date.today().month
        self._dia_seleccionado: Optional[date] = date.today()
        self._eventos_mes: list[dict] = []
        self._dias_con_eventos: set[int] = set()

        # Caché de celdas para detección de clics
        self._celdas: list[tuple[QRect, Optional[date]]] = []

        self.setMouseTracking(True)

    def establecer_mes(self, anio: int, mes: int):
        """Cambia el mes/año mostrado y repinta."""
        self._anio = anio
        self._mes = mes
        self.update()

    def establecer_eventos(self, eventos: list[dict]):
        """Recibe la lista de eventos del mes y actualiza indicadores."""
        self._eventos_mes = eventos
        self._dias_con_eventos.clear()
        for ev in eventos:
            dt = _parsear_datetime(ev.get("start_datetime", ""))
            if dt and dt.month == self._mes and dt.year == self._anio:
                self._dias_con_eventos.add(dt.day)
        self.update()

    def establecer_seleccion(self, fecha: Optional[date]):
        """Establece el día seleccionado."""
        self._dia_seleccionado = fecha
        self.update()

    def paintEvent(self, event: QPaintEvent):
        """Dibuja la grilla completa del mes con QPainter."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Fondo papel
        painter.fillRect(self.rect(), QColor(COLOR_FONDO_PAPEL))

        # Dimensiones de la grilla
        alto_cabecera = 32
        ancho_celda = w / 7
        alto_celda = (h - alto_cabecera) / 6

        # ── Cabecera con nombres de días ──
        fuente_cabecera = QFont("Sans", 11, QFont.Weight.Bold)
        painter.setFont(fuente_cabecera)
        painter.setPen(QColor(COLOR_CABECERA_DIA))

        for i, nombre in enumerate(NOMBRES_DIAS):
            rect = QRectF(
                i * ancho_celda, 0, ancho_celda, alto_cabecera
            )
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, nombre)

        # Línea separadora bajo la cabecera
        painter.setPen(QPen(QColor(COLOR_LINEA_GRILLA), 1))
        painter.drawLine(
            QPoint(0, alto_cabecera),
            QPoint(w, alto_cabecera)
        )

        # ── Calcular días del mes ──
        cal = calendar.Calendar(firstweekday=0)  # Lunes = 0
        dias_mes = cal.monthdayscalendar(self._anio, self._mes)

        # Rellenar hasta 6 filas
        while len(dias_mes) < 6:
            dias_mes.append([0] * 7)

        hoy = date.today()
        self._celdas.clear()

        # Obtener días del mes anterior y siguiente para rellenar
        if self._mes == 1:
            mes_anterior = 12
            anio_anterior = self._anio - 1
        else:
            mes_anterior = self._mes - 1
            anio_anterior = self._anio

        if self._mes == 12:
            mes_siguiente = 1
            anio_siguiente = self._anio + 1
        else:
            mes_siguiente = self._mes + 1
            anio_siguiente = self._anio

        ultimo_dia_mes_anterior = calendar.monthrange(
            anio_anterior, mes_anterior
        )[1]

        # Fuentes para los números de día
        fuente_dia = QFont("Sans", 12)
        fuente_dia_negrita = QFont("Sans", 12, QFont.Weight.Bold)
        metrics = QFontMetrics(fuente_dia)

        # Contador para días del mes siguiente
        dia_siguiente = 0
        # Contador para días del mes anterior (se calcula desde la primera fila)
        ceros_primera_fila = dias_mes[0].count(0)

        for fila, semana in enumerate(dias_mes):
            for col, dia in enumerate(semana):
                x = col * ancho_celda
                y = alto_cabecera + fila * alto_celda
                rect_celda = QRect(
                    int(x), int(y), int(ancho_celda), int(alto_celda)
                )
                rect_f = QRectF(x, y, ancho_celda, alto_celda)

                # Determinar la fecha real de esta celda
                if dia == 0:
                    if fila == 0:
                        # Día del mes anterior
                        dia_real = (
                            ultimo_dia_mes_anterior - ceros_primera_fila
                            + col + 1
                        )
                        if col >= ceros_primera_fila:
                            dia_real = col - ceros_primera_fila + 1
                            fecha_celda = date(
                                self._anio, self._mes, dia_real
                            )
                        else:
                            fecha_celda = date(
                                anio_anterior, mes_anterior, dia_real
                            )
                    else:
                        # Día del mes siguiente
                        dia_siguiente += 1
                        dia_real = dia_siguiente
                        fecha_celda = date(
                            anio_siguiente, mes_siguiente, dia_real
                        )
                    es_otro_mes = True
                else:
                    dia_real = dia
                    fecha_celda = date(self._anio, self._mes, dia)
                    es_otro_mes = False

                self._celdas.append((rect_celda, fecha_celda))

                # ── Dibujar líneas de grilla sutiles ──
                painter.setPen(QPen(QColor(COLOR_LINEA_GRILLA), 0.5))
                painter.drawRect(rect_f)

                # ── Resaltar día de hoy ──
                es_hoy = (fecha_celda == hoy and not es_otro_mes)
                es_seleccionado = (
                    self._dia_seleccionado is not None
                    and fecha_celda == self._dia_seleccionado
                )

                # Área central para el número de día
                tamano_circulo = min(ancho_celda, alto_celda) * 0.45
                cx = x + ancho_celda / 2
                cy = y + alto_celda * 0.35

                if es_hoy:
                    # Círculo rojo para hoy
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor(COLOR_HOY)))
                    painter.drawEllipse(
                        QRectF(
                            cx - tamano_circulo / 2,
                            cy - tamano_circulo / 2,
                            tamano_circulo,
                            tamano_circulo
                        )
                    )
                    painter.setPen(QColor("#FFFFFF"))
                    painter.setFont(fuente_dia_negrita)
                elif es_seleccionado:
                    # Fondo azul claro para el día seleccionado
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QBrush(QColor(COLOR_SELECCION + "40")))
                    painter.drawEllipse(
                        QRectF(
                            cx - tamano_circulo / 2,
                            cy - tamano_circulo / 2,
                            tamano_circulo,
                            tamano_circulo
                        )
                    )
                    painter.setPen(QColor(COLOR_SELECCION))
                    painter.setFont(fuente_dia_negrita)
                elif es_otro_mes:
                    painter.setPen(QColor(COLOR_TEXTO_GRIS))
                    painter.setFont(fuente_dia)
                else:
                    painter.setPen(QColor(COLOR_TEXTO_NORMAL))
                    painter.setFont(fuente_dia)

                # Dibujar número de día
                texto_dia = str(dia_real)
                rect_texto = QRectF(
                    cx - tamano_circulo / 2,
                    cy - tamano_circulo / 2,
                    tamano_circulo,
                    tamano_circulo
                )
                painter.drawText(
                    rect_texto, Qt.AlignmentFlag.AlignCenter, texto_dia
                )

                # ── Puntos de colores para días con eventos ──
                if (not es_otro_mes and dia in self._dias_con_eventos):
                    colores_dia = self._obtener_colores_dia(dia)
                    punto_y = cy + tamano_circulo / 2 + 4
                    radio_punto = 3.0
                    total_puntos = min(len(colores_dia), 5)
                    ancho_total = total_puntos * (radio_punto * 2 + 2) - 2
                    punto_x_inicio = cx - ancho_total / 2 + radio_punto

                    painter.setPen(Qt.PenStyle.NoPen)
                    for idx in range(total_puntos):
                        color_punto = colores_dia[idx]
                        painter.setBrush(QBrush(QColor(color_punto)))
                        painter.drawEllipse(
                            QRectF(
                                punto_x_inicio
                                + idx * (radio_punto * 2 + 2)
                                - radio_punto,
                                punto_y - radio_punto,
                                radio_punto * 2,
                                radio_punto * 2
                            )
                        )

        painter.end()

    def _obtener_colores_dia(self, dia: int) -> list[str]:
        """Obtiene los colores únicos de eventos para un día específico."""
        colores = []
        for ev in self._eventos_mes:
            dt = _parsear_datetime(ev.get("start_datetime", ""))
            if dt and dt.day == dia:
                color = ev.get("color", "#3498DB")
                if color not in colores:
                    colores.append(color)
        return colores

    def mousePressEvent(self, event: QMouseEvent):
        """Maneja clic simple: seleccionar día."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            fecha = self._fecha_en_posicion(pos)
            if fecha:
                self._dia_seleccionado = fecha
                self.dia_seleccionado.emit(fecha)
                self.update()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Maneja doble clic: crear nuevo evento en ese día."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            fecha = self._fecha_en_posicion(pos)
            if fecha:
                self._dia_seleccionado = fecha
                self.dia_doble_clic.emit(fecha)
                self.update()

    def _fecha_en_posicion(self, pos: QPoint) -> Optional[date]:
        """Devuelve la fecha correspondiente a una posición del widget."""
        for rect, fecha in self._celdas:
            if fecha and rect.contains(pos):
                return fecha
        return None


# ═══════════════════════════════════════════════════════════
# WIDGET DE VISTA SEMANAL (pintado con QPainter)
# ═══════════════════════════════════════════════════════════

class WeekGridWidget(QWidget):
    """
    Widget personalizado que dibuja la vista semanal con franjas horarias.
    Muestra 7 columnas (Lun-Dom) × franjas desde HORA_INICIO a HORA_FIN.
    Los eventos se dibujan como bloques coloreados.
    """

    # Señales
    slot_clic = pyqtSignal(datetime)  # Clic en un slot vacío

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setMinimumSize(400, 600)
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Estado
        self._fecha_lunes: date = date.today()
        self._eventos_semana: list[dict] = []

        # Dimensiones fijas
        self._ancho_hora = 55       # Columna de la etiqueta de hora
        self._alto_cabecera = 48    # Cabecera con nombres de días
        self._alto_hora = 50        # Alto de cada franja horaria

        # Calcular alto total necesario
        self._num_horas = HORA_FIN - HORA_INICIO
        alto_total = (
            self._alto_cabecera + self._num_horas * self._alto_hora + 20
        )
        self.setMinimumHeight(alto_total)

        self.setMouseTracking(True)

    def establecer_semana(self, fecha_lunes: date):
        """Establece la semana a mostrar (a partir del lunes)."""
        self._fecha_lunes = fecha_lunes
        self.update()

    def establecer_eventos(self, eventos: list[dict]):
        """Recibe la lista de eventos de la semana."""
        self._eventos_semana = eventos
        self.update()

    def paintEvent(self, event: QPaintEvent):
        """Dibuja la grilla semanal con franjas horarias y eventos."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Fondo
        painter.fillRect(self.rect(), QColor(COLOR_FONDO_PAPEL))

        ancho_dia = (w - self._ancho_hora) / 7
        hoy = date.today()

        # ── Cabecera: nombres de días y fechas ──
        fuente_cabecera = QFont("Sans", 10, QFont.Weight.Bold)
        fuente_fecha = QFont("Sans", 9)
        painter.setFont(fuente_cabecera)

        for i in range(7):
            fecha_dia = self._fecha_lunes + timedelta(days=i)
            x = self._ancho_hora + i * ancho_dia
            rect_dia = QRectF(x, 0, ancho_dia, self._alto_cabecera)

            # Resaltar columna de hoy
            if fecha_dia == hoy:
                painter.fillRect(
                    QRectF(x, 0, ancho_dia, h),
                    QColor(COLOR_HOY + "10")
                )
                painter.setPen(QColor(COLOR_HOY))
            else:
                painter.setPen(QColor(COLOR_CABECERA_DIA))

            painter.setFont(fuente_cabecera)
            # Nombre del día
            rect_nombre = QRectF(
                x, 2, ancho_dia, self._alto_cabecera / 2
            )
            painter.drawText(
                rect_nombre, Qt.AlignmentFlag.AlignCenter,
                NOMBRES_DIAS[i]
            )

            # Fecha numérica
            painter.setFont(fuente_fecha)
            rect_num = QRectF(
                x, self._alto_cabecera / 2 - 2,
                ancho_dia, self._alto_cabecera / 2
            )
            painter.drawText(
                rect_num, Qt.AlignmentFlag.AlignCenter,
                str(fecha_dia.day)
            )

        # Línea bajo cabecera
        painter.setPen(QPen(QColor(COLOR_LINEA_GRILLA), 1))
        painter.drawLine(0, self._alto_cabecera, w, self._alto_cabecera)

        # ── Franjas horarias ──
        fuente_hora = QFont("Sans", 9)
        painter.setFont(fuente_hora)

        for hora_idx in range(self._num_horas + 1):
            hora = HORA_INICIO + hora_idx
            y = self._alto_cabecera + hora_idx * self._alto_hora

            # Etiqueta de hora
            painter.setPen(QColor(COLOR_TEXTO_GRIS))
            rect_hora = QRectF(0, y - 8, self._ancho_hora - 5, 16)
            painter.drawText(
                rect_hora, Qt.AlignmentFlag.AlignRight
                | Qt.AlignmentFlag.AlignVCenter,
                f"{hora:02d}:00"
            )

            # Línea horizontal
            painter.setPen(QPen(QColor(COLOR_LINEA_GRILLA), 0.5))
            painter.drawLine(
                int(self._ancho_hora), int(y), int(w), int(y)
            )

        # Líneas verticales entre columnas
        for i in range(8):
            x = self._ancho_hora + i * ancho_dia
            painter.setPen(QPen(QColor(COLOR_LINEA_GRILLA), 0.5))
            painter.drawLine(
                int(x), int(self._alto_cabecera), int(x), int(h)
            )

        # ── Dibujar eventos como bloques ──
        fuente_evento = QFont("Sans", 9)
        painter.setFont(fuente_evento)

        for ev in self._eventos_semana:
            self._dibujar_evento(painter, ev, ancho_dia)

        # ── Línea indicadora de hora actual ──
        if self._fecha_lunes <= hoy < self._fecha_lunes + timedelta(days=7):
            ahora = datetime.now()
            col_hoy = (hoy - self._fecha_lunes).days
            if HORA_INICIO <= ahora.hour < HORA_FIN:
                minutos_desde_inicio = (
                    (ahora.hour - HORA_INICIO) * 60 + ahora.minute
                )
                y_ahora = (
                    self._alto_cabecera
                    + minutos_desde_inicio * self._alto_hora / 60
                )
                x_col = self._ancho_hora + col_hoy * ancho_dia
                painter.setPen(QPen(QColor(COLOR_HOY), 2))
                painter.drawLine(
                    int(x_col), int(y_ahora),
                    int(x_col + ancho_dia), int(y_ahora)
                )
                # Pequeño círculo en el borde
                painter.setBrush(QBrush(QColor(COLOR_HOY)))
                painter.drawEllipse(
                    QRectF(x_col - 4, y_ahora - 4, 8, 8)
                )

        painter.end()

    def _dibujar_evento(
        self, painter: QPainter, evento: dict, ancho_dia: float
    ):
        """Dibuja un bloque de evento en la grilla semanal."""
        inicio = _parsear_datetime(evento.get("start_datetime", ""))
        fin = _parsear_datetime(evento.get("end_datetime", ""))
        if not inicio or not fin:
            return

        # Determinar columna (día de la semana)
        dia_offset = (inicio.date() - self._fecha_lunes).days
        if dia_offset < 0 or dia_offset >= 7:
            return

        # Limitar al rango horario visible
        hora_inicio_ev = max(inicio.hour + inicio.minute / 60.0, HORA_INICIO)
        hora_fin_ev = min(fin.hour + fin.minute / 60.0, HORA_FIN)
        if hora_fin_ev <= hora_inicio_ev:
            return

        # Calcular posición y tamaño del bloque
        x = self._ancho_hora + dia_offset * ancho_dia + 2
        y = (
            self._alto_cabecera
            + (hora_inicio_ev - HORA_INICIO) * self._alto_hora
        )
        alto = (hora_fin_ev - hora_inicio_ev) * self._alto_hora
        ancho = ancho_dia - 4

        color_ev = QColor(evento.get("color", "#3498DB"))

        # Fondo del bloque con transparencia
        color_fondo = QColor(color_ev)
        color_fondo.setAlpha(180)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color_fondo))
        painter.drawRoundedRect(QRectF(x, y, ancho, alto), 4, 4)

        # Borde izquierdo grueso
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color_ev))
        painter.drawRoundedRect(QRectF(x, y, 4, alto), 2, 2)

        # Texto del evento
        painter.setPen(QColor("#FFFFFF"))
        fuente_ev = QFont("Sans", 8, QFont.Weight.Bold)
        painter.setFont(fuente_ev)
        rect_texto = QRectF(x + 7, y + 2, ancho - 10, alto - 4)
        titulo = evento.get("title", "")
        painter.drawText(
            rect_texto,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            titulo
        )

        # Hora del evento (si hay espacio)
        if alto > 28:
            fuente_hora_ev = QFont("Sans", 7)
            painter.setFont(fuente_hora_ev)
            painter.setPen(QColor("#FFFFFFCC"))
            hora_texto = (
                f"{inicio.strftime('%H:%M')} - {fin.strftime('%H:%M')}"
            )
            rect_hora = QRectF(x + 7, y + 16, ancho - 10, 14)
            painter.drawText(
                rect_hora,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                hora_texto
            )

    def mousePressEvent(self, event: QMouseEvent):
        """Maneja clic en un slot para crear evento."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            dt = self._datetime_en_posicion(pos)
            if dt:
                self.slot_clic.emit(dt)

    def _datetime_en_posicion(self, pos: QPoint) -> Optional[datetime]:
        """Calcula el datetime correspondiente a una posición del widget."""
        x = pos.x()
        y = pos.y()

        if x < self._ancho_hora or y < self._alto_cabecera:
            return None

        ancho_dia = (self.width() - self._ancho_hora) / 7
        col = int((x - self._ancho_hora) / ancho_dia)
        if col < 0 or col >= 7:
            return None

        minutos_rel = (
            (y - self._alto_cabecera) / self._alto_hora * 60
        )
        hora = HORA_INICIO + int(minutos_rel / 60)
        minutos = int(minutos_rel) % 60
        # Redondear a 15 minutos
        minutos = (minutos // 15) * 15

        if hora < HORA_INICIO or hora >= HORA_FIN:
            return None

        fecha_dia = self._fecha_lunes + timedelta(days=col)
        return datetime(
            fecha_dia.year, fecha_dia.month, fecha_dia.day, hora, minutos
        )


# ═══════════════════════════════════════════════════════════
# PANEL DE EVENTOS DEL DÍA
# ═══════════════════════════════════════════════════════════

class PanelEventosDia(QFrame):
    """
    Panel lateral que muestra la lista de eventos del día seleccionado.
    Permite editar y eliminar eventos desde aquí.
    """

    # Señales
    evento_editar = pyqtSignal(dict)      # Solicitar edición de evento
    evento_eliminar = pyqtSignal(int)     # Solicitar eliminación por ID
    evento_nuevo = pyqtSignal()           # Solicitar nuevo evento

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("panelEventos")
        self.setMinimumWidth(240)
        self.setMaximumWidth(320)
        self._eventos: list[dict] = []
        self._construir_ui()

    def _construir_ui(self):
        """Construye la interfaz del panel de eventos."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ── Etiqueta del día seleccionado ──
        self.lbl_fecha = QLabel("Eventos del día")
        self.lbl_fecha.setFont(QFont("Sans", 12, QFont.Weight.Bold))
        self.lbl_fecha.setStyleSheet(f"color: {COLOR_CABECERA_DIA};")
        self.lbl_fecha.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_fecha)

        # ── Separador ──
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {COLOR_LINEA_GRILLA};")
        layout.addWidget(sep)

        # ── Lista de eventos ──
        self.lista_eventos = QListWidget()
        self.lista_eventos.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.lista_eventos.customContextMenuRequested.connect(
            self._mostrar_menu_contextual
        )
        self.lista_eventos.itemDoubleClicked.connect(
            self._editar_evento_seleccionado
        )
        self.lista_eventos.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        layout.addWidget(self.lista_eventos)

        # ── Mensaje cuando no hay eventos ──
        self.lbl_sin_eventos = QLabel("No hay eventos para este día")
        self.lbl_sin_eventos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_eventos.setStyleSheet(
            f"color: {COLOR_TEXTO_GRIS}; font-style: italic; padding: 20px;"
        )
        self.lbl_sin_eventos.setWordWrap(True)
        layout.addWidget(self.lbl_sin_eventos)

        # ── Botones de acción ──
        barra_botones = QHBoxLayout()

        self.btn_editar = QPushButton()
        self.btn_editar.setIcon(
            svg_to_qicon(icon_edit(), 20, COLOR_ICONO)
        )
        self.btn_editar.setToolTip("Editar evento seleccionado")
        self.btn_editar.setFixedSize(36, 36)
        self.btn_editar.clicked.connect(self._editar_evento_seleccionado)
        barra_botones.addWidget(self.btn_editar)

        self.btn_eliminar = QPushButton()
        self.btn_eliminar.setIcon(
            svg_to_qicon(icon_delete(), 20, COLOR_ICONO)
        )
        self.btn_eliminar.setToolTip("Eliminar evento seleccionado")
        self.btn_eliminar.setFixedSize(36, 36)
        self.btn_eliminar.clicked.connect(self._eliminar_evento_seleccionado)
        barra_botones.addWidget(self.btn_eliminar)

        barra_botones.addStretch()
        layout.addLayout(barra_botones)

    def actualizar_eventos(self, fecha: date, eventos: list[dict]):
        """Actualiza la lista con los eventos de una fecha dada."""
        self._eventos = eventos

        # Actualizar etiqueta de fecha
        nombre_dia = NOMBRES_DIAS_COMPLETOS[fecha.weekday()]
        nombre_mes = NOMBRES_MESES[fecha.month]
        self.lbl_fecha.setText(
            f"{nombre_dia} {fecha.day} de {nombre_mes}"
        )

        # Limpiar y rellenar la lista
        self.lista_eventos.clear()

        if not eventos:
            self.lista_eventos.hide()
            self.lbl_sin_eventos.show()
            self.btn_editar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            return

        self.lista_eventos.show()
        self.lbl_sin_eventos.hide()
        self.btn_editar.setEnabled(True)
        self.btn_eliminar.setEnabled(True)

        for ev in eventos:
            item = QListWidgetItem()
            # Formatear hora
            inicio = _parsear_datetime(ev.get("start_datetime", ""))
            fin = _parsear_datetime(ev.get("end_datetime", ""))
            hora_str = ""
            if inicio and fin:
                hora_str = (
                    f"{inicio.strftime('%H:%M')} - {fin.strftime('%H:%M')}"
                )

            titulo = ev.get("title", "Sin título")
            texto = f"{hora_str}\n{titulo}" if hora_str else titulo
            item.setText(texto)

            # Guardar datos completos en el item
            item.setData(Qt.ItemDataRole.UserRole, ev)

            # Indicador de color como ícono
            color_ev = ev.get("color", "#3498DB")
            item.setIcon(QIcon(_crear_pixmap_color(color_ev, 12)))

            self.lista_eventos.addItem(item)

    def _editar_evento_seleccionado(self, item=None):
        """Emite señal para editar el evento seleccionado."""
        if isinstance(item, QListWidgetItem):
            ev = item.data(Qt.ItemDataRole.UserRole)
        else:
            seleccion = self.lista_eventos.currentItem()
            if not seleccion:
                return
            ev = seleccion.data(Qt.ItemDataRole.UserRole)

        if ev:
            self.evento_editar.emit(ev)

    def _eliminar_evento_seleccionado(self):
        """Emite señal para eliminar el evento seleccionado."""
        seleccion = self.lista_eventos.currentItem()
        if not seleccion:
            return

        ev = seleccion.data(Qt.ItemDataRole.UserRole)
        if ev:
            self.evento_eliminar.emit(ev.get("id", 0))

    def _mostrar_menu_contextual(self, pos: QPoint):
        """Muestra menú contextual al hacer clic derecho en un evento."""
        item = self.lista_eventos.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {COLOR_FONDO_PAPEL};
                border: 1px solid {COLOR_LINEA_GRILLA};
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px;
                color: {COLOR_TEXTO_NORMAL};
            }}
            QMenu::item:selected {{
                background-color: #EDE0C8;
            }}
        """)

        accion_editar = menu.addAction(
            svg_to_qicon(icon_edit(), 16, COLOR_ICONO), "Editar evento"
        )
        accion_eliminar = menu.addAction(
            svg_to_qicon(icon_delete(), 16, COLOR_ICONO), "Eliminar evento"
        )

        accion = menu.exec(self.lista_eventos.mapToGlobal(pos))
        if accion == accion_editar:
            self._editar_evento_seleccionado(item)
        elif accion == accion_eliminar:
            ev = item.data(Qt.ItemDataRole.UserRole)
            if ev:
                self.evento_eliminar.emit(ev.get("id", 0))


# ═══════════════════════════════════════════════════════════
# CLASE PRINCIPAL: TabCalendar (Doble Página)
# ═══════════════════════════════════════════════════════════

from calendar_split_views import (
    DailyLeftWidget, DailyRightWidget,
    WeekLeftWidget, WeekRightWidget,
    MonthPageWidget,
    SemiannualLeftWidget, SemiannualRightWidget
)

class TabCalendar(QWidget):
    """
    Widget principal de Calendario/Agenda rediseñado para formato de doble página.
    Es compatible con el enrutador de páginas de app_window.py.
    """

    def __init__(self, db: Database, parent: QWidget = None):
        super().__init__(parent)
        self.db = db

        # Estado de la fecha activa
        self._dia_seleccionado = date.today()
        self._vista_actual = "semanal"  # "diaria", "semanal", "mensual", "semestral"

        # ── Contenedores Stacked para ambas páginas de la agenda ──
        self.panel_izquierdo = QStackedWidget()
        self.panel_derecho = QStackedWidget()

        self._construir_vistas()
        self.set_vista("semanal")

    def _construir_vistas(self):
        # 1. Vista Diaria (Índice 0)
        self.daily_left = DailyLeftWidget(self.db)
        self.daily_right = DailyRightWidget(self.db)
        self.panel_izquierdo.addWidget(self.daily_left)
        self.panel_derecho.addWidget(self.daily_right)

        self.daily_left.crear_evento.connect(self._al_crear_evento_fecha_hora)
        self.daily_left.editar_evento.connect(self._editar_evento)

        # 2. Vista Semanal/Agenda (Índice 1)
        self.week_left = WeekLeftWidget(self.db)
        self.week_right = WeekRightWidget(self.db)
        self.panel_izquierdo.addWidget(self.week_left)
        self.panel_derecho.addWidget(self.week_right)

        self.week_left.crear_evento.connect(self._al_crear_evento_fecha)
        self.week_left.editar_evento.connect(self._editar_evento)
        self.week_right.crear_evento.connect(self._al_crear_evento_fecha)
        self.week_right.editar_evento.connect(self._editar_evento)

        # 3. Vista Mensual (Índice 2)
        self.month_left = MonthPageWidget(self.db, side="left")
        self.month_right = MonthPageWidget(self.db, side="right")
        self.panel_izquierdo.addWidget(self.month_left)
        self.panel_derecho.addWidget(self.month_right)

        self.month_left.dia_clic.connect(self._al_seleccionar_dia)
        self.month_left.dia_doble_clic.connect(self._al_crear_evento_fecha)
        self.month_right.dia_clic.connect(self._al_seleccionar_dia)
        self.month_right.dia_doble_clic.connect(self._al_crear_evento_fecha)

        # 4. Vista Semestral (Índice 3)
        self.semiannual_left = SemiannualLeftWidget()
        self.semiannual_right = SemiannualRightWidget()
        self.panel_izquierdo.addWidget(self.semiannual_left)
        self.panel_derecho.addWidget(self.semiannual_right)

        self.semiannual_left.dia_seleccionado.connect(self._al_dia_seleccionado_semestral)
        self.semiannual_right.dia_seleccionado.connect(self._al_dia_seleccionado_semestral)

    def set_vista(self, vista: str):
        """Cambia el modo de vista actual."""
        self._vista_actual = vista
        mapping = {
            "diaria": 0,
            "semanal": 1,
            "mensual": 2,
            "semestral": 3
        }
        idx = mapping.get(vista, 1)
        self.panel_izquierdo.setCurrentIndex(idx)
        self.panel_derecho.setCurrentIndex(idx)
        self.actualizar_vista()

    def ir_anterior(self):
        """Retrocede en el tiempo según la vista activa."""
        if self._vista_actual == "diaria":
            self._dia_seleccionado -= timedelta(days=1)
        elif self._vista_actual == "semanal":
            self._dia_seleccionado -= timedelta(days=7)
        elif self._vista_actual == "mensual":
            # Retroceder un mes
            mes = self._dia_seleccionado.month - 1
            anio = self._dia_seleccionado.year
            if mes == 0:
                mes = 12
                anio -= 1
            dia = min(self._dia_seleccionado.day, calendar.monthrange(anio, mes)[1])
            self._dia_seleccionado = date(anio, mes, dia)
        elif self._vista_actual == "semestral":
            # Retroceder 6 meses
            mes = self._dia_seleccionado.month - 6
            anio = self._dia_seleccionado.year
            if mes <= 0:
                mes += 12
                anio -= 1
                if mes <= 0:
                    mes += 12
                    anio -= 1
            dia = min(self._dia_seleccionado.day, calendar.monthrange(anio, mes)[1])
            self._dia_seleccionado = date(anio, mes, dia)

        self.actualizar_vista()

    def ir_siguiente(self):
        """Avanza en el tiempo según la vista activa."""
        if self._vista_actual == "diaria":
            self._dia_seleccionado += timedelta(days=1)
        elif self._vista_actual == "semanal":
            self._dia_seleccionado += timedelta(days=7)
        elif self._vista_actual == "mensual":
            # Avanzar un mes
            mes = self._dia_seleccionado.month + 1
            anio = self._dia_seleccionado.year
            if mes == 13:
                mes = 1
                anio += 1
            dia = min(self._dia_seleccionado.day, calendar.monthrange(anio, mes)[1])
            self._dia_seleccionado = date(anio, mes, dia)
        elif self._vista_actual == "semestral":
            # Avanzar 6 meses
            mes = self._dia_seleccionado.month + 6
            anio = self._dia_seleccionado.year
            if mes > 12:
                mes -= 12
                anio += 1
                if mes > 12:
                    mes -= 12
                    anio += 1
            dia = min(self._dia_seleccionado.day, calendar.monthrange(anio, mes)[1])
            self._dia_seleccionado = date(anio, mes, dia)

        self.actualizar_vista()

    def ir_a_hoy(self):
        """Navega a la fecha actual."""
        self._dia_seleccionado = date.today()
        self.actualizar_vista()

    def crear_evento(self):
        """Abre el diálogo de creación para el día seleccionado."""
        self._al_crear_evento_fecha(self._dia_seleccionado)

    def actualizar_vista(self):
        """Refresca los datos en la vista seleccionada."""
        idx = self.panel_izquierdo.currentIndex()
        if idx == 0:
            self.daily_left.establecer_fecha(self._dia_seleccionado)
            self.daily_right.establecer_fecha(self._dia_seleccionado)
        elif idx == 1:
            lunes = self._obtener_lunes(self._dia_seleccionado)
            self.week_left.establecer_lunes(lunes)
            self.week_right.establecer_lunes(lunes)
        elif idx == 2:
            self.month_left.establecer_mes(self._dia_seleccionado.year, self._dia_seleccionado.month)
            self.month_right.establecer_mes(self._dia_seleccionado.year, self._dia_seleccionado.month)
        elif idx == 3:
            self.semiannual_left.establecer_fecha_base(self._dia_seleccionado.year, self._dia_seleccionado.month)
            self.semiannual_right.establecer_fecha_base(self._dia_seleccionado.year, self._dia_seleccionado.month)

    # ─────────────────────────────────────────────────────────
    # Manejo de Eventos y Callbacks
    # ─────────────────────────────────────────────────────────

    def _al_seleccionar_dia(self, fecha: date):
        self._dia_seleccionado = fecha
        self.actualizar_vista()

    def _al_dia_seleccionado_semestral(self, fecha: date):
        self._dia_seleccionado = fecha
        self.set_vista("diaria")

    def _al_crear_evento_fecha(self, fecha: date):
        fecha_q = QDate(fecha.year, fecha.month, fecha.day)
        dialogo = EventDialog(self, fecha_inicial=fecha_q)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.crear_evento(
                datos["title"],
                datos["description"],
                datos["start_datetime"],
                datos["end_datetime"],
                datos["color"]
            )
            self.actualizar_vista()

    def _al_crear_evento_fecha_hora(self, fecha: date, hora: int):
        fecha_q = QDate(fecha.year, fecha.month, fecha.day)
        hora_q = QTime(hora, 0)
        dialogo = EventDialog(self, fecha_inicial=fecha_q, hora_inicial=hora_q)
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.crear_evento(
                datos["title"],
                datos["description"],
                datos["start_datetime"],
                datos["end_datetime"],
                datos["color"]
            )
            self.actualizar_vista()

    def _editar_evento(self, evento: dict):
        """Abre el diálogo para editar un evento existente."""
        dialogo = EventDialog(self, evento=evento)

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            datos = dialogo.obtener_datos()
            self.db.actualizar_evento(
                evento["id"],
                datos["title"],
                datos["description"],
                datos["start_datetime"],
                datos["end_datetime"],
                datos["color"]
            )
            self.actualizar_vista()

    def _eliminar_evento(self, event_id: int):
        """Elimina un evento previa confirmación."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Está seguro de que desea eliminar este evento?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.db.eliminar_evento(event_id)
            self.actualizar_vista()

    # ─────────────────────────────────────────────────────────
    # Utilidades
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _obtener_lunes(fecha: date) -> date:
        """Devuelve el lunes de la semana que contiene la fecha dada."""
        return fecha - timedelta(days=fecha.weekday())


# ═══════════════════════════════════════════════════════════
# FUNCIONES AUXILIARES
# ═══════════════════════════════════════════════════════════

def _parsear_datetime(texto: str) -> Optional[datetime]:
    """
    Parsea una cadena de fecha/hora en los formatos usados por la BD.
    Soporta: 'YYYY-MM-DD HH:MM', 'YYYY-MM-DD HH:MM:SS',
             'YYYY-MM-DDTHH:MM', 'YYYY-MM-DDTHH:MM:SS'.
    """
    if not texto:
        return None

    formatos = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    return None


def _crear_pixmap_color(color_hex: str, size: int = 16) -> QIcon:
    """
    Crea un QIcon cuadrado relleno de un color sólido.
    Usado como indicador visual en combos y listas.

    Args:
        color_hex: Color en formato hexadecimal (ej: '#E74C3C').
        size: Tamaño del ícono en píxeles.

    Returns:
        QIcon con el cuadrado de color.
    """
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(color_hex)))
    painter.drawRoundedRect(QRectF(1, 1, size - 2, size - 2), 3, 3)
    painter.end()

    return QIcon(pixmap)
