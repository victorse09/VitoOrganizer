# -*- coding: utf-8 -*-
"""
Vito Organizer — Componentes de Vistas Calendario Divididas
Implementa las vistas Diaria, Semanal/Agenda, Mensual y Semestral en el formato
esqueumórfico de doble página (Página Izquierda y Página Derecha).
"""

import calendar
from datetime import date, datetime, timedelta
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QFrame,
    QGridLayout, QScrollArea, QCheckBox, QSizePolicy, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QTime, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush, QIcon

# Colores y constantes compartidas
COLOR_FONDO_PAPEL = "#ffffff"
COLOR_LINEA_GRILLA = "#e0e0e0"
COLOR_LINEA_MARGEN = "#ff9999"
COLOR_CABECERA_DIA = "#4A3728"
COLOR_TEXTO_NORMAL = "#2C1810"
COLOR_SELECCION = "#ede0cc"


# ═══════════════════════════════════════════════════════════
# VISTA DIARIA (DAILY VIEW)
# ═══════════════════════════════════════════════════════════

class DailyLeftWidget(QWidget):
    """
    Página izquierda de la vista diaria: Horario de 8:00 a 22:00
    """
    crear_evento = pyqtSignal(date, int)  # fecha, hora
    editar_evento = pyqtSignal(dict)      # datos del evento

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.fecha_actual = date.today()
        self._setup_ui()

    def _setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(10, 10, 10, 10)
        self.layout_principal.setSpacing(5)

        # Encabezado del día
        self.lbl_cabecera = QLabel()
        self.lbl_cabecera.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.lbl_cabecera.setStyleSheet("color: #4A3728; padding-bottom: 5px;")
        self.lbl_cabecera.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout_principal.addWidget(self.lbl_cabecera)

        # Área de scroll para el horario
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        self.widget_grid = QWidget()
        self.widget_grid.setStyleSheet("background: transparent;")
        self.grid_layout = QVBoxLayout(self.widget_grid)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(0)

        # Crear filas horarias
        self.filas_horarias = {}
        for hora in range(8, 23):
            fila = QFrame()
            fila.setFrameShape(QFrame.Shape.StyledPanel)
            fila.setStyleSheet(f"border-bottom: 1px solid {COLOR_LINEA_GRILLA}; min-height: 45px;")
            
            fila_layout = QHBoxLayout(fila)
            fila_layout.setContentsMargins(5, 2, 5, 2)
            
            # Etiqueta de hora
            lbl_hora = QLabel(f"{hora:02d}:00")
            lbl_hora.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl_hora.setStyleSheet("color: #8B7D6B; min-width: 50px; border: none;")
            fila_layout.addWidget(lbl_hora)
            
            # Contenedor para eventos de esta hora
            contenedor_eventos = QWidget()
            contenedor_eventos.setStyleSheet("border: none; background: transparent;")
            layout_evt = QHBoxLayout(contenedor_eventos)
            layout_evt.setContentsMargins(0, 0, 0, 0)
            layout_evt.setSpacing(4)
            fila_layout.addWidget(contenedor_eventos, 1)

            # Doble clic para añadir evento en esta hora
            fila.mouseDoubleClickEvent = lambda e, h=hora: self.crear_evento.emit(self.fecha_actual, h)

            self.grid_layout.addWidget(fila)
            self.filas_horarias[hora] = (contenedor_eventos, layout_evt)

        scroll.setWidget(self.widget_grid)
        self.layout_principal.addWidget(scroll, 1)

    def establecer_fecha(self, fecha: date):
        self.fecha_actual = fecha
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        nombre_dia = dias_semana[fecha.weekday()]
        nombre_mes = meses[fecha.month]
        self.lbl_cabecera.setText(f"{nombre_dia}, {fecha.day} de {nombre_mes} de {fecha.year}")
        self.actualizar_eventos()

    def actualizar_eventos(self):
        # Limpiar contenedores
        for hora in self.filas_horarias:
            contenedor, layout_evt = self.filas_horarias[hora]
            while layout_evt.count():
                child = layout_evt.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

        # Consultar eventos del día
        fecha_str = self.fecha_actual.isoformat()
        eventos = self.db.obtener_eventos_por_fecha(fecha_str)

        for evt in eventos:
            try:
                # Extraer hora de inicio
                dt_str = evt["start_datetime"]
                # Formato esperado: YYYY-MM-DD HH:MM
                hora_str = dt_str.split(" ")[1]
                hora_val = int(hora_str.split(":")[0])
            except Exception:
                continue

            if hora_val in self.filas_horarias:
                _, layout_evt = self.filas_horarias[hora_val]
                
                # Crear botón de evento tipo post-it
                btn_evt = QPushButton(evt["title"])
                color = evt.get("color", "#3498DB")
                btn_evt.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color};
                        color: #ffffff;
                        border: 1px solid {QColor(color).darker(120).name()};
                        border-radius: 3px;
                        font-size: 11px;
                        padding: 3px 6px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: {QColor(color).lighter(115).name()};
                    }}
                """)
                # Al hacer clic editar evento
                btn_evt.clicked.connect(lambda checked, ev=evt: self.editar_evento.emit(ev))
                layout_evt.addWidget(btn_evt)


class DailyRightWidget(QWidget):
    """
    Página derecha de la vista diaria: Tareas, Llamadas, Notas Diarias
    """
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.fecha_actual = date.today()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── SECCIÓN TAREAS ──
        box_tareas = QFrame()
        box_tareas.setStyleSheet(f"border: 1px solid {COLOR_LINEA_GRILLA}; background-color: #fcfbf9; border-radius: 4px;")
        layout_tareas = QVBoxLayout(box_tareas)
        layout_tareas.setContentsMargins(6, 6, 6, 6)
        
        lbl_tareas = QLabel("✔ TAREAS DEL DÍA")
        lbl_tareas.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_tareas.setStyleSheet("color: #4A3728; border: none;")
        layout_tareas.addWidget(lbl_tareas)

        self.input_tarea = QLineEdit()
        self.input_tarea.setPlaceholderText("Añadir tarea... (Enter)")
        self.input_tarea.setStyleSheet("background: white; border: 1px solid #c0c0c0; border-radius: 2px; padding: 3px;")
        self.input_tarea.returnPressed.connect(self._agregar_tarea)
        layout_tareas.addWidget(self.input_tarea)

        self.list_tareas = QListWidget()
        self.list_tareas.setStyleSheet("border: none; background: transparent;")
        self.list_tareas.itemChanged.connect(self._estado_tarea_cambiado)
        self.list_tareas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_tareas.customContextMenuRequested.connect(self._menu_contextual_tareas)
        layout_tareas.addWidget(self.list_tareas, 1)

        layout.addWidget(box_tareas, 3)

        # ── SECCIÓN LLAMADAS ──
        box_llamadas = QFrame()
        box_llamadas.setStyleSheet(f"border: 1px solid {COLOR_LINEA_GRILLA}; background-color: #fcfbf9; border-radius: 4px;")
        layout_llamadas = QVBoxLayout(box_llamadas)
        layout_llamadas.setContentsMargins(6, 6, 6, 6)
        
        lbl_llamadas = QLabel("☎ LLAMADAS PENDIENTES")
        lbl_llamadas.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_llamadas.setStyleSheet("color: #4A3728; border: none;")
        layout_llamadas.addWidget(lbl_llamadas)

        self.input_llamada = QLineEdit()
        self.input_llamada.setPlaceholderText("Nombre - Teléfono... (Enter)")
        self.input_llamada.setStyleSheet("background: white; border: 1px solid #c0c0c0; border-radius: 2px; padding: 3px;")
        self.input_llamada.returnPressed.connect(self._agregar_llamada)
        layout_llamadas.addWidget(self.input_llamada)

        self.list_llamadas = QListWidget()
        self.list_llamadas.setStyleSheet("border: none; background: transparent;")
        self.list_llamadas.itemChanged.connect(self._estado_llamada_cambiado)
        self.list_llamadas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list_llamadas.customContextMenuRequested.connect(self._menu_contextual_llamadas)
        layout_llamadas.addWidget(self.list_llamadas, 1)

        layout.addWidget(box_llamadas, 3)

        # ── SECCIÓN NOTAS DIARIAS ──
        box_notas = QFrame()
        box_notas.setStyleSheet(f"border: 1px solid {COLOR_LINEA_GRILLA}; background-color: #fcfbf9; border-radius: 4px;")
        layout_notas = QVBoxLayout(box_notas)
        layout_notas.setContentsMargins(6, 6, 6, 6)
        
        lbl_notas = QLabel("✍ NOTAS DIARIAS")
        lbl_notas.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_notas.setStyleSheet("color: #4A3728; border: none;")
        layout_notas.addWidget(lbl_notas)

        self.editor_notas = QTextEdit()
        self.editor_notas.setPlaceholderText("Escribe apuntes o eventos del día aquí...")
        self.editor_notas.setStyleSheet("background: white; border: 1px solid #c0c0c0; border-radius: 2px; padding: 5px;")
        self.editor_notas.textChanged.connect(self._guardar_notas_diarias)
        layout_notas.addWidget(self.editor_notas, 1)

        layout.addWidget(box_notas, 4)

    def establecer_fecha(self, fecha: date):
        self.fecha_actual = fecha
        self.actualizar_datos()

    def actualizar_datos(self):
        # 1. Cargar Tareas
        self.list_tareas.blockSignals(True)
        self.list_tareas.clear()
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM daily_tasks WHERE task_date = ?", (self.fecha_actual.isoformat(),))
        for row in cursor.fetchall():
            item = QListWidgetItem(row["title"])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if row["done"] else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.list_tareas.addItem(item)
        self.list_tareas.blockSignals(False)

        # 2. Cargar Llamadas
        self.list_llamadas.blockSignals(True)
        self.list_llamadas.clear()
        cursor.execute("SELECT * FROM daily_calls WHERE call_date = ?", (self.fecha_actual.isoformat(),))
        for row in cursor.fetchall():
            label_text = f"{row['contact']}  ({row['phone']})" if row['phone'] else row['contact']
            item = QListWidgetItem(label_text)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if row["done"] else Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.list_llamadas.addItem(item)
        self.list_llamadas.blockSignals(False)

        # 3. Cargar Notas Diarias
        self.editor_notas.blockSignals(True)
        cursor.execute("SELECT content FROM daily_notes WHERE note_date = ?", (self.fecha_actual.isoformat(),))
        row = cursor.fetchone()
        self.editor_notas.setPlainText(row["content"] if row else "")
        self.editor_notas.blockSignals(False)

    def _agregar_tarea(self):
        texto = self.input_tarea.text().strip()
        if not texto: return
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO daily_tasks (title, done, task_date) VALUES (?, 0, ?)",
                       (texto, self.fecha_actual.isoformat()))
        self.db.conn.commit()
        self.input_tarea.clear()
        self.actualizar_datos()

    def _estado_tarea_cambiado(self, item):
        done = 1 if item.checkState() == Qt.CheckState.Checked else 0
        task_id = item.data(Qt.ItemDataRole.UserRole)
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE daily_tasks SET done = ? WHERE id = ?", (done, task_id))
        self.db.conn.commit()

    def _menu_contextual_tareas(self, pos):
        item = self.list_tareas.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        action_delete = menu.addAction("Eliminar Tarea")
        action = menu.exec(self.list_tareas.mapToGlobal(pos))
        if action == action_delete:
            task_id = item.data(Qt.ItemDataRole.UserRole)
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM daily_tasks WHERE id = ?", (task_id,))
            self.db.conn.commit()
            self.actualizar_datos()

    def _agregar_llamada(self):
        texto = self.input_llamada.text().strip()
        if not texto: return
        
        # Analizar "Nombre - Teléfono"
        contacto = texto
        telefono = ""
        if "-" in texto:
            partes = texto.split("-")
            contacto = partes[0].strip()
            telefono = partes[1].strip()
            
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO daily_calls (contact, phone, done, call_date) VALUES (?, ?, 0, ?)",
                       (contacto, telefono, self.fecha_actual.isoformat()))
        self.db.conn.commit()
        self.input_llamada.clear()
        self.actualizar_datos()

    def _estado_llamada_cambiado(self, item):
        done = 1 if item.checkState() == Qt.CheckState.Checked else 0
        call_id = item.data(Qt.ItemDataRole.UserRole)
        cursor = self.db.conn.cursor()
        cursor.execute("UPDATE daily_calls SET done = ? WHERE id = ?", (done, call_id))
        self.db.conn.commit()

    def _menu_contextual_llamadas(self, pos):
        item = self.list_llamadas.itemAt(pos)
        if not item: return
        menu = QMenu(self)
        action_delete = menu.addAction("Eliminar Llamada")
        action = menu.exec(self.list_llamadas.mapToGlobal(pos))
        if action == action_delete:
            call_id = item.data(Qt.ItemDataRole.UserRole)
            cursor = self.db.conn.cursor()
            cursor.execute("DELETE FROM daily_calls WHERE id = ?", (call_id,))
            self.db.conn.commit()
            self.actualizar_datos()

    def _guardar_notas_diarias(self):
        contenido = self.editor_notas.toPlainText()
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO daily_notes (note_date, content) VALUES (?, ?)",
                       (self.fecha_actual.isoformat(), contenido))
        self.db.conn.commit()


# ═══════════════════════════════════════════════════════════
# VISTA SEMANAL / AGENDA (WEEKLY VIEW)
# ═══════════════════════════════════════════════════════════

class DayBox(QFrame):
    """
    Sub-widget para mostrar un día en la vista semanal split.
    """
    crear_evento = pyqtSignal(date)
    editar_evento = pyqtSignal(dict)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.fecha = date.today()
        self.setStyleSheet(f"border-bottom: 1px solid {COLOR_LINEA_GRILLA}; background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(3)

        # Encabezado del día: "Lunes 22"
        self.lbl_dia = QLabel()
        self.lbl_dia.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lbl_dia.setStyleSheet("color: #4A3728; border: none;")
        layout.addWidget(self.lbl_dia)

        # Contenedor horizontal para eventos
        self.evt_layout = QHBoxLayout()
        self.evt_layout.setContentsMargins(0, 0, 0, 0)
        self.evt_layout.setSpacing(4)
        layout.addLayout(self.evt_layout)

        # Doble clic en el fondo añade evento
        self.mouseDoubleClickEvent = lambda e: self.crear_evento.emit(self.fecha)

    def establecer_fecha(self, fecha: date):
        self.fecha = fecha
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        hoy = date.today()
        style = "color: #ff3b30; border: none;" if fecha == hoy else "color: #4A3728; border: none;"
        self.lbl_dia.setText(f"{dias[fecha.weekday()]} {fecha.day}")
        self.lbl_dia.setStyleSheet(style)
        self.actualizar_eventos()

    def actualizar_eventos(self):
        while self.evt_layout.count():
            child = self.evt_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        eventos = self.db.obtener_eventos_por_fecha(self.fecha.isoformat())
        for evt in eventos:
            btn_evt = QPushButton(evt["title"])
            color = evt.get("color", "#3498DB")
            btn_evt.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: #ffffff;
                    border: 1px solid {QColor(color).darker(110).name()};
                    border-radius: 3px;
                    font-size: 11px;
                    padding: 2px 5px;
                    text-align: left;
                }}
            """)
            btn_evt.clicked.connect(lambda checked, ev=evt: self.editar_evento.emit(ev))
            self.evt_layout.addWidget(btn_evt)


class WeekLeftWidget(QWidget):
    """
    Página izquierda de la vista semanal: Lunes, Martes, Miércoles
    """
    crear_evento = pyqtSignal(date)
    editar_evento = pyqtSignal(dict)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.lunes = date.today()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.dia_boxes = []
        for i in range(3): # Lunes, Martes, Miércoles
            box = DayBox(self.db)
            box.crear_evento.connect(self.crear_evento.emit)
            box.editar_evento.connect(self.editar_evento.emit)
            layout.addWidget(box)
            self.dia_boxes.append(box)

    def establecer_lunes(self, lunes: date):
        self.lunes = lunes
        for i, box in enumerate(self.dia_boxes):
            box.establecer_fecha(lunes + timedelta(days=i))


class WeekRightWidget(QWidget):
    """
    Página derecha de la vista semanal: Jueves, Viernes, Sábado, Domingo
    """
    crear_evento = pyqtSignal(date)
    editar_evento = pyqtSignal(dict)

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.lunes = date.today()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(0)

        self.dia_boxes = []
        for i in range(3, 7): # Jueves, Viernes, Sábado, Domingo
            box = DayBox(self.db)
            box.crear_evento.connect(self.crear_evento.emit)
            box.editar_evento.connect(self.editar_evento.emit)
            layout.addWidget(box)
            self.dia_boxes.append(box)

    def establecer_lunes(self, lunes: date):
        self.lunes = lunes
        for i, box in enumerate(self.dia_boxes):
            box.establecer_fecha(lunes + timedelta(days=i + 3))


# ═══════════════════════════════════════════════════════════
# VISTA MENSUAL (MONTHLY VIEW) SPLIT
# ═══════════════════════════════════════════════════════════

class MonthGridCell(QFrame):
    """
    Celda individual de la grilla mensual.
    """
    dia_clic = pyqtSignal(date)
    dia_doble_clic = pyqtSignal(date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fecha = None
        self.activo = False
        self.hoy = False
        self.eventos = []
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"border: 1px solid {COLOR_LINEA_GRILLA}; background-color: #ffffff;")

    def establecer_datos(self, fecha: date, activo: bool, es_hoy: bool, eventos: list):
        self.fecha = fecha
        self.activo = activo
        self.hoy = es_hoy
        self.eventos = eventos
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if not self.fecha:
            return

        w, h = self.width(), self.height()

        # Fondo
        if not self.activo:
            painter.fillRect(self.rect(), QColor("#f4f0e6")) # Mes vecino
        else:
            painter.fillRect(self.rect(), QColor("#ffffff"))

        # Borde de Hoy
        if self.hoy:
            painter.setPen(QPen(QColor("#E74C3C"), 2))
            painter.drawRect(1, 1, w - 2, h - 2)

        # Dibujar número de día
        painter.setPen(QColor(COLOR_TEXTO_NORMAL) if self.activo else QColor("#b0a090"))
        font = QFont("Arial", 11)
        if self.hoy: font.setBold(True)
        painter.setFont(font)
        painter.drawText(5, 17, str(self.fecha.day))

        # Eventos (dibujar círculos pequeños de color)
        if self.eventos:
            cx = 8
            cy = h - 12
            for i, evt in enumerate(self.eventos[:5]): # Máximo 5 puntos
                color = QColor(evt.get("color", "#3498DB"))
                painter.setBrush(QBrush(color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(cx, cy, 6, 6)
                cx += 8

        painter.end()

    def mousePressEvent(self, event):
        if self.fecha:
            self.dia_clic.emit(self.fecha)

    def mouseDoubleClickEvent(self, event):
        if self.fecha:
            self.dia_doble_clic.emit(self.fecha)


class MonthPageWidget(QWidget):
    """
    Base para las páginas izquierda y derecha de la vista mensual.
    """
    dia_clic = pyqtSignal(date)
    dia_doble_clic = pyqtSignal(date)

    def __init__(self, db, side="left", parent=None):
        super().__init__(parent)
        self.db = db
        self.side = side # "left" (Lun-Mié) o "right" (Jue-Dom)
        self.anio = date.today().year
        self.mes = date.today().month
        self.columnas = [0, 1, 2] if side == "left" else [3, 4, 5, 6]
        self._setup_ui()

    def _setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(5, 5, 5, 5)
        self.layout_principal.setSpacing(2)

        # Fila de días de la semana
        self.layout_dias_semana = QHBoxLayout()
        self.layout_dias_semana.setSpacing(2)
        
        nombres_dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        cols_mostrar = nombres_dias[:3] if self.side == "left" else nombres_dias[3:]
        
        for d in cols_mostrar:
            lbl = QLabel(d)
            lbl.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #8B7D6B; background: transparent; padding: 3px;")
            self.layout_dias_semana.addWidget(lbl)
            
        self.layout_principal.addLayout(self.layout_dias_semana)

        # Grilla de celdas
        self.grid = QGridLayout()
        self.grid.setSpacing(2)
        self.layout_principal.addLayout(self.grid, 1)

        self.celdas = {}
        for row in range(6):
            for col_idx, col in enumerate(self.columnas):
                celda = MonthGridCell()
                celda.dia_clic.connect(self.dia_clic.emit)
                celda.dia_doble_clic.connect(self.dia_doble_clic.emit)
                self.grid.addWidget(celda, row, col_idx)
                self.celdas[(row, col)] = celda

    def establecer_mes(self, anio: int, mes: int):
        self.anio = anio
        self.mes = mes
        self.actualizar_grilla()

    def actualizar_grilla(self):
        # Obtener calendario mensual
        cal_obj = calendar.Calendar(firstweekday=0) # Lunes = 0
        semanas = cal_obj.monthdatescalendar(self.anio, self.mes)
        
        # Si tiene menos de 6 semanas, agregar de relleno para mantener proporciones clásicas
        while len(semanas) < 6:
            semanas.append([semanas[-1][-1] + timedelta(days=i) for i in range(1, 8)])

        # Consultar eventos del mes
        eventos = self.db.obtener_eventos_por_mes(self.anio, self.mes)
        eventos_por_dia = {}
        for evt in eventos:
            try:
                # Obtener la fecha del evento
                f_str = evt["start_datetime"].split(" ")[0]
                eventos_por_dia.setdefault(f_str, []).append(evt)
            except Exception:
                continue

        hoy = date.today()

        for row in range(6):
            for col in self.columnas:
                celda = self.celdas.get((row, col))
                if not celda: continue
                
                fecha = semanas[row][col]
                es_activo = (fecha.month == self.mes)
                es_hoy = (fecha == hoy)
                evts_dia = eventos_por_dia.get(fecha.isoformat(), [])
                
                celda.establecer_datos(fecha, es_activo, es_hoy, evts_dia)


# ═══════════════════════════════════════════════════════════
# VISTA SEMESTRAL (SEMIANNUAL VIEW)
# ═══════════════════════════════════════════════════════════

class MiniMonthWidget(QFrame):
    """
    Calendario mensual en miniatura.
    """
    dia_seleccionado = pyqtSignal(date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"border: 1px solid {COLOR_LINEA_GRILLA}; background-color: #ffffff; border-radius: 3px;")
        self.anio = date.today().year
        self.mes = date.today().month
        self._setup_ui()

    def _setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(4, 4, 4, 4)
        self.layout_principal.setSpacing(2)

        # Encabezado (Nombre de Mes y Año)
        self.lbl_titulo = QLabel()
        self.lbl_titulo.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_titulo.setStyleSheet("color: #4A3728; border: none; padding-bottom: 2px;")
        self.layout_principal.addWidget(self.lbl_titulo)

        # Grilla de días
        self.grid = QGridLayout()
        self.grid.setSpacing(1)
        self.layout_principal.addLayout(self.grid, 1)

    def establecer_mes(self, anio: int, mes: int):
        self.anio = anio
        self.mes = mes

        # Limpiar grilla anterior
        while self.grid.count():
            child = self.grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Título
        meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.lbl_titulo.setText(f"{meses[mes]} {anio}")

        # Cabecera de días
        cabeceras = ["L", "M", "X", "J", "V", "S", "D"]
        for col, c in enumerate(cabeceras):
            lbl_c = QLabel(c)
            lbl_c.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            lbl_c.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_c.setStyleSheet("color: #8B7D6B; border: none;")
            self.grid.addWidget(lbl_c, 0, col)

        # Calendario
        cal_obj = calendar.Calendar(firstweekday=0)
        semanas = cal_obj.monthdatescalendar(anio, mes)
        
        for row_idx, semana in enumerate(semanas):
            for col_idx, fecha in enumerate(semana):
                # Solo mostrar días que pertenecen al mes
                if fecha.month != mes:
                    # Celda vacía
                    lbl_vacio = QLabel("")
                    lbl_vacio.setStyleSheet("border: none;")
                    self.grid.addWidget(lbl_vacio, row_idx + 1, col_idx)
                    continue

                btn_dia = QPushButton(str(fecha.day))
                btn_dia.setFlat(True)
                btn_dia.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_dia.setFont(QFont("Arial", 8))
                
                # Resaltar hoy
                if fecha == date.today():
                    btn_dia.setStyleSheet("color: white; background-color: #E74C3C; border-radius: 8px; border: none; font-weight: bold;")
                else:
                    btn_dia.setStyleSheet("color: #2C1810; border: none;")

                btn_dia.clicked.connect(lambda checked, f=fecha: self.dia_seleccionado.emit(f))
                self.grid.addWidget(btn_dia, row_idx + 1, col_idx)


class SemiannualLeftWidget(QWidget):
    """
    Página izquierda de la vista semestral: Muestra meses N, N+1, N+2
    """
    dia_seleccionado = pyqtSignal(date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.anio = date.today().year
        self.mes = date.today().month
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.minis = []
        for i in range(3):
            mini = MiniMonthWidget()
            mini.dia_seleccionado.connect(self.dia_seleccionado.emit)
            layout.addWidget(mini)
            self.minis.append(mini)

    def establecer_fecha_base(self, anio: int, mes: int):
        self.anio = anio
        self.mes = mes

        # Calcular los 3 meses
        for i, mini in enumerate(self.minis):
            m_anio = anio
            m_mes = mes + i
            if m_mes > 12:
                m_mes -= 12
                m_anio += 1
            mini.establecer_mes(m_anio, m_mes)


class SemiannualRightWidget(QWidget):
    """
    Página derecha de la vista semestral: Muestra meses N+3, N+4, N+5
    """
    dia_seleccionado = pyqtSignal(date)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.anio = date.today().year
        self.mes = date.today().month
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.minis = []
        for i in range(3):
            mini = MiniMonthWidget()
            mini.dia_seleccionado.connect(self.dia_seleccionado.emit)
            layout.addWidget(mini)
            self.minis.append(mini)

    def establecer_fecha_base(self, anio: int, mes: int):
        self.anio = anio
        self.mes = mes

        # Calcular los 3 meses posteriores
        for i, mini in enumerate(self.minis):
            m_anio = anio
            m_mes = mes + i + 3
            if m_mes > 12:
                m_mes -= 12
                m_anio += 1
            mini.establecer_mes(m_anio, m_mes)
