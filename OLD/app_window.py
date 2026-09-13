# -*- coding: utf-8 -*-
"""
Vito Organizer — Ventana Principal (Estilo Lotus Original)
Recrea la distribución icónica de Lotus Organizer:
- Panel "SmartCenter" izquierdo sobre el cuero (Almanaque).
- Página izquierda (con pestañas a la izquierda).
- Anillas de metal centrales.
- Página derecha (con pestañas a la derecha).
- Barra de menús clásica estilo Windows 95.
"""

import os
import shutil
from datetime import date, datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QSizePolicy, QStatusBar, QFrame,
    QCalendarWidget, QPushButton, QSpacerItem,
    QDialog, QListWidget, QListWidgetItem, QMessageBox,
    QCheckBox, QSpinBox, QTextBrowser, QMenuBar, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QRectF, QPointF, QSize, QPoint, QTimer
from PyQt6.QtGui import QFont, QIcon, QPainter, QPen, QBrush, QColor, QLinearGradient, QPolygonF, QPainterPath

from database import Database
from ui_builder import (
    RingSpineWidget, PaperPageWidget, LeatherBackground,
    TabButton, TAB_COLORS, crear_estilo_global, crear_estilo_toolbar_papel
)
from svg_icons import (
    svg_to_qicon, icon_agenda, icon_calendar, icon_delete,
    icon_edit, icon_folder, icon_link, icon_settings, icon_today, icon_week, icon_new
)
from tab_calendar import TabCalendar
from tab_notes import TabNotes
from tab_inventory import TabInventory
from tab_instruments import TabInstruments
from tab_bookmarks import TabBookmarks


# ═══════════════════════════════════════════════════════════
# WIDGET DE PAPELERA ESQUEUMÓRFICA (DRAWN WITH QPAINTER)
# ═══════════════════════════════════════════════════════════

class TrashBinWidget(QWidget):
    """
    Widget esqueumórfico para la papelera de reciclaje.
    Dibuja un tacho de basura metálico clásico con QPainter.
    Tiene estados: vacío o lleno de papeles arrugados.
    """
    clicked = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.is_empty = True
        self.setFixedSize(120, 100)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actualizar_estado()

    def actualizar_estado(self):
        try:
            self.is_empty = (self.db.recuento_papelera() == 0)
        except Exception:
            self.is_empty = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # Dibujar etiqueta "Papelera" arriba
        painter.setPen(QColor("#000000"))
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.drawText(QRect(0, 0, w, 15), Qt.AlignmentFlag.AlignCenter, "Papelera")

        # Centro del tacho
        cx = w / 2
        
        # Si NO está vacía, dibujar papeles sobresaliendo
        if not self.is_empty:
            painter.setPen(QPen(QColor("#808080"), 1))
            painter.setBrush(QBrush(QColor("#ffffff")))
            # Papel 1
            p1 = QPolygonF([QPointF(cx - 15, 30), QPointF(cx - 5, 20), QPointF(cx + 5, 25), QPointF(cx - 5, 35)])
            painter.drawPolygon(p1)
            # Papel 2
            p2 = QPolygonF([QPointF(cx - 2, 28), QPointF(cx + 10, 18), QPointF(cx + 18, 25), QPointF(cx + 8, 33)])
            painter.drawPolygon(p2)
            # Papel arrugado 3
            painter.drawEllipse(QPointF(cx, 26), 8, 6)

        # Gradiente metálico para el cuerpo del tacho
        body_grad = QLinearGradient(cx - 25, 35, cx + 25, 35)
        body_grad.setColorAt(0.0, QColor("#8a8a8a"))
        body_grad.setColorAt(0.3, QColor("#d1d1d1"))
        body_grad.setColorAt(0.5, QColor("#f0f0f0"))
        body_grad.setColorAt(0.8, QColor("#a3a3a3"))
        body_grad.setColorAt(1.0, QColor("#616161"))

        # Dibujar cuerpo (unir las elipses superior e inferior)
        path = QPainterPath()
        path.moveTo(cx - 24, 35)
        path.lineTo(cx - 18, 85)
        path.arcTo(cx - 18, 79, 36, 12, 180, 180)
        path.lineTo(cx + 24, 35)
        path.arcTo(cx - 24, 27, 48, 16, 0, -180)
        
        painter.setPen(QPen(QColor("#545454"), 1.5))
        painter.setBrush(body_grad)
        painter.drawPath(path)

        # Borde de la boca del tacho (elipse superior completa)
        painter.setBrush(QBrush(QColor("#3d3d3d"))) # Interior oscuro
        painter.drawEllipse(QRectF(cx - 24, 27, 48, 16))
        
        # Si NO está vacía, redibujar la parte inferior de los papeles
        if not self.is_empty:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QRectF(cx - 15, 30, 30, 8))

        # Rejilla / Costillas
        painter.setPen(QPen(QColor("#545454"), 1, Qt.PenStyle.SolidLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(int(cx - 20), 38, int(cx - 15), 82)
        painter.drawLine(int(cx - 10), 41, int(cx - 8), 84)
        painter.drawLine(int(cx), 42, int(cx), 85)
        painter.drawLine(int(cx + 10), 41, int(cx + 8), 84)
        painter.drawLine(int(cx + 20), 38, int(cx + 15), 82)
        
        # Borde metálico exterior superior
        painter.setPen(QPen(QColor("#a8a8a8"), 1.5))
        painter.drawEllipse(QRectF(cx - 24, 27, 48, 16))

        painter.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ═══════════════════════════════════════════════════════════
# DIÁLOGO DE PAPELERA DE RECICLAJE
# ═══════════════════════════════════════════════════════════

class TrashDialog(QDialog):
    """
    Diálogo de la Papelera de Reciclaje.
    Lista elementos borrados y permite restaurar o vaciar.
    """
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Papelera de Reciclaje")
        self.setMinimumSize(450, 400)
        self._setup_ui()
        self.actualizar_lista()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        lbl_desc = QLabel("Elementos eliminados temporalmente:")
        lbl_desc.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_desc.setStyleSheet("color: #4A3728;")
        layout.addWidget(lbl_desc)

        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Arial", 10))
        layout.addWidget(self.list_widget, 1)

        # Botones
        btn_layout = QHBoxLayout()
        
        self.btn_restaurar = QPushButton("Restaurar")
        self.btn_restaurar.clicked.connect(self._restaurar_item)
        btn_layout.addWidget(self.btn_restaurar)

        self.btn_vaciar = QPushButton("Vaciar Papelera")
        self.btn_vaciar.setStyleSheet("color: #c0392b; font-weight: bold;")
        self.btn_vaciar.clicked.connect(self._vaciar_papelera)
        btn_layout.addWidget(self.btn_vaciar)

        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_cerrar)

        layout.addLayout(btn_layout)

    def actualizar_lista(self):
        self.list_widget.clear()
        items = self.db.obtener_items_papelera()
        
        if not items:
            item = QListWidgetItem("La papelera está vacía.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setForeground(QColor("#808080"))
            self.list_widget.addItem(item)
            self.btn_restaurar.setEnabled(False)
            self.btn_vaciar.setEnabled(False)
            return

        self.btn_restaurar.setEnabled(True)
        self.btn_vaciar.setEnabled(True)

        tablas_amigables = {
            "events": "Calendario",
            "notes": "Notas",
            "components": "Inventario",
            "instruments": "Instrumentos",
            "bookmarks": "Enlaces"
        }

        for row in items:
            orig = row["item_type"]
            origen = tablas_amigables.get(orig, orig.capitalize())
            texto = f"[{origen}]  {row['title']}"
            item = QListWidgetItem(texto)
            item.setData(Qt.ItemDataRole.UserRole, row["id"])
            self.list_widget.addItem(item)

    def _restaurar_item(self):
        selected_item = self.list_widget.currentItem()
        if not selected_item: return
        
        trash_id = selected_item.data(Qt.ItemDataRole.UserRole)
        if not trash_id: return

        if self.db.restaurar_item_papelera(trash_id):
            QMessageBox.information(self, "Restaurado", "El elemento ha sido restaurado con éxito.")
            self.actualizar_lista()
            if self.parent() and hasattr(self.parent(), "actualizar_vista_actual"):
                self.parent().actualizar_vista_actual()
        else:
            QMessageBox.warning(self, "Error", "No se pudo restaurar el elemento.")

    def _vaciar_papelera(self):
        resp = QMessageBox.question(
            self, "Vaciar Papelera",
            "¿Estás seguro de vaciar la papelera permanentemente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if resp == QMessageBox.StandardButton.Yes:
            self.db.vaciar_papelera()
            self.actualizar_lista()
            if self.parent() and hasattr(self.parent(), "actualizar_vista_actual"):
                self.parent().actualizar_vista_actual()


# ═══════════════════════════════════════════════════════════
# WIDGET DE PORTADA
# ═══════════════════════════════════════════════════════════

class PortadaWidget(QWidget):
    """
    Sección de Portada que se muestra al inicio o al seleccionar Portada en el menú.
    """
    def __init__(self, agenda_data, db, parent=None):
        super().__init__(parent)
        self.agenda_nombre = agenda_data["nombre"]
        self.agenda_ruta = agenda_data["ruta"]
        self.db = db

        # Panel Izquierdo
        self.panel_izquierdo = QWidget()
        layout_izq = QVBoxLayout(self.panel_izquierdo)
        layout_izq.setContentsMargins(30, 40, 30, 40)
        layout_izq.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_titulo = QLabel("VITO\nORGANIZER")
        lbl_titulo.setFont(QFont("Georgia", 32, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #4A3728; line-height: 1.1;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(lbl_titulo)

        lbl_sub = QLabel("Agenda Personal esqueumórfica")
        lbl_sub.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_sub.setStyleSheet("color: #8B7D6B;")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(lbl_sub)

        layout_izq.addSpacing(25)

        lbl_logo = QLabel()
        lbl_logo.setPixmap(svg_to_qicon(icon_agenda(), size=96, color="#4A3728").pixmap(96, 96))
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(lbl_logo)

        layout_izq.addSpacing(25)

        lbl_version = QLabel("Versión 1.0 (v.1.0)")
        lbl_version.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_version.setStyleSheet("color: #8b5e3c;")
        lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(lbl_version)

        # Panel Derecho
        self.panel_derecho = QWidget()
        layout_der = QVBoxLayout(self.panel_derecho)
        layout_der.setContentsMargins(30, 40, 30, 40)
        layout_der.setSpacing(15)

        lbl_agenda_title = QLabel("DETALLES DE LA AGENDA")
        lbl_agenda_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_agenda_title.setStyleSheet("color: #4A3728; border-bottom: 2px solid #4A3728; padding-bottom: 5px;")
        layout_der.addWidget(lbl_agenda_title)

        self.lbl_detalles = QLabel()
        self.lbl_detalles.setFont(QFont("Arial", 11))
        self.lbl_detalles.setStyleSheet("color: #2C1810;")
        self.lbl_detalles.setWordWrap(True)
        layout_der.addWidget(self.lbl_detalles)

        layout_der.addStretch()

        lbl_tip = QLabel("💡 Navegación:\nUse el menú Sección superior o las pestañas laterales del cuaderno para navegar entre las secciones.")
        lbl_tip.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_tip.setStyleSheet("color: #8B7D6B; background-color: #f7f0e3; border: 1px solid #d4c5a9; border-radius: 4px; padding: 10px;")
        lbl_tip.setWordWrap(True)
        layout_der.addWidget(lbl_tip)

        self.actualizar_datos()

    def actualizar_datos(self):
        cursor = self.db.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM events")
        cant_eventos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM notes")
        cant_notas = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM components")
        cant_componentes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM instruments")
        cant_instrumentos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM bookmarks")
        cant_enlaces = cursor.fetchone()[0]

        detalles_text = (
            f"<b>Agenda Activa:</b> {self.agenda_nombre}<br/>"
            f"<b>Ruta de carpeta:</b> {self.agenda_ruta}<br/><br/>"
            f"<b>Estadísticas de uso:</b><br/>"
            f"• Anotaciones en Calendario: {cant_eventos}<br/>"
            f"• Hojas de Notas: {cant_notas}<br/>"
            f"• Elementos en Inventario: {cant_componentes}<br/>"
            f"• Instrumentos registrados: {cant_instrumentos}<br/>"
            f"• Enlaces almacenados: {cant_enlaces}<br/>"
        )
        self.lbl_detalles.setText(detalles_text)


# ═══════════════════════════════════════════════════════════
# DIÁLOGO DE OPCIONES
# ═══════════════════════════════════════════════════════════

class OptionsDialog(QDialog):
    """
    Ventana de opciones con pestañas para General (autoguardado) y Respaldo.
    """
    def __init__(self, agenda_data, db, parent=None):
        super().__init__(parent)
        self.agenda_data = agenda_data
        self.db = db
        self.setWindowTitle("Opciones del Sistema")
        self.setMinimumSize(420, 320)
        self._setup_ui()
        self._cargar_valores()

    def _setup_ui(self):
        from PyQt6.QtWidgets import QTabWidget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #808080;
                background-color: #d4d0c8;
            }
            QTabBar::tab {
                background: #d4d0c8;
                border: 1px solid #808080;
                border-bottom: none;
                padding: 6px 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #ffffff;
            }
        """)

        # General
        tab_general = QWidget()
        layout_gen = QVBoxLayout(tab_general)
        layout_gen.setContentsMargins(15, 15, 15, 15)
        layout_gen.setSpacing(15)

        self.chk_autosave = QCheckBox("Habilitar autoguardado de notas")
        self.chk_autosave.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.chk_autosave.stateChanged.connect(self._al_cambiar_autosave)
        layout_gen.addWidget(self.chk_autosave)

        layout_tiempo = QHBoxLayout()
        lbl_tiempo = QLabel("Tiempo de autoguardado (minutos):")
        self.spin_tiempo = QSpinBox()
        self.spin_tiempo.setRange(1, 60)
        layout_tiempo.addWidget(lbl_tiempo)
        layout_tiempo.addWidget(self.spin_tiempo)
        layout_gen.addLayout(layout_tiempo)

        layout_gen.addStretch()
        self.tabs.addTab(tab_general, "General")

        # Respaldo
        tab_respaldo = QWidget()
        layout_resp = QVBoxLayout(tab_respaldo)
        layout_resp.setContentsMargins(15, 15, 15, 15)
        layout_resp.setSpacing(15)

        lbl_resp_desc = QLabel(
            "Crea un archivo ZIP con todos los archivos de la agenda activa "
            "(base de datos SQLite y notas Markdown) para respaldar tus datos."
        )
        lbl_resp_desc.setFont(QFont("Arial", 10))
        lbl_resp_desc.setWordWrap(True)
        layout_resp.addWidget(lbl_resp_desc)

        self.btn_crear_respaldo = QPushButton("Crear Copia de Seguridad (.zip)")
        self.btn_crear_respaldo.setStyleSheet("padding: 8px; font-weight: bold;")
        self.btn_crear_respaldo.clicked.connect(self._crear_respaldo)
        layout_resp.addWidget(self.btn_crear_respaldo)

        layout_resp.addStretch()
        self.tabs.addTab(tab_respaldo, "Respaldo")

        layout.addWidget(self.tabs, 1)

        # Botones
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.btn_guardar = QPushButton("Aceptar")
        self.btn_guardar.clicked.connect(self._guardar_valores)
        btn_box.addWidget(self.btn_guardar)

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancelar)

        layout.addLayout(btn_box)

    def _al_cambiar_autosave(self, state):
        self.spin_tiempo.setEnabled(self.chk_autosave.isChecked())

    def _cargar_valores(self):
        enabled = self.db.obtener_config("autosave_enabled", "false")
        interval = self.db.obtener_config("autosave_interval", "5")
        self.chk_autosave.setChecked(enabled == "true")
        self.spin_tiempo.setValue(int(interval))
        self.spin_tiempo.setEnabled(enabled == "true")

    def _guardar_valores(self):
        enabled_str = "true" if self.chk_autosave.isChecked() else "false"
        interval_str = str(self.spin_tiempo.value())
        self.db.guardar_config("autosave_enabled", enabled_str)
        self.db.guardar_config("autosave_interval", interval_str)
        if self.parent() and hasattr(self.parent(), "configurar_timer_autosave"):
            self.parent().configurar_timer_autosave()
        self.accept()

    def _crear_respaldo(self):
        from PyQt6.QtWidgets import QFileDialog
        sug_nombre = f"Backup_VitoOrganizer_{self.agenda_data['nombre']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        destino, _ = QFileDialog.getSaveFileName(self, "Exportar Copia de Seguridad", sug_nombre, "Archivos ZIP (*.zip)")
        if not destino: return

        origen = self.agenda_data["ruta"]
        try:
            base_dest = destino
            if base_dest.lower().endswith(".zip"):
                base_dest = base_dest[:-4]
            shutil.make_archive(base_dest, 'zip', origen)
            QMessageBox.information(self, "Respaldo Éxito", f"Copia de seguridad guardada con éxito:\n{destino}")
        except Exception as e:
            QMessageBox.critical(self, "Error de Respaldo", f"No se pudo crear la copia:\n{e}")


# ═══════════════════════════════════════════════════════════
# SMARTCENTER (BARRA LATERAL IZQUIERDA DINÁMICA)
# ═══════════════════════════════════════════════════════════

class SmartCenterWidget(QWidget):
    """
    Panel lateral clásico de Lotus Organizer que muestra widgets completos
    en Calendario y oculta todo excepto la papelera en las demás secciones.
    """
    cambio_vista_calendario = pyqtSignal(str)
    evento_nuevo = pyqtSignal()
    papelera_clicked = pyqtSignal()

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setFixedWidth(200)
        self._setup_ui()

    def _setup_ui(self):
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(10, 20, 10, 20)
        self.layout_principal.setSpacing(10)

        # ── CONTENEDOR ESPECÍFICO DE CALENDARIO ──
        self.calendar_container = QWidget()
        self.calendar_container.setStyleSheet("background: transparent; border: none;")
        layout_cal_widgets = QVBoxLayout(self.calendar_container)
        layout_cal_widgets.setContentsMargins(0, 0, 0, 0)
        layout_cal_widgets.setSpacing(12)

        # Almanaque (Mini Calendario)
        self.cal = QCalendarWidget()
        self.cal.setGridVisible(True)
        self.cal.setStyleSheet("""
            QCalendarWidget QWidget { alternate-background-color: #d4d0c8; }
            QCalendarWidget QAbstractItemView:enabled { font-size: 10px; }
            QCalendarWidget QToolButton { color: black; }
        """)
        layout_cal_widgets.addWidget(self.cal)

        # Selector de Vistas de Calendario
        lbl_vistas = QLabel("Vistas del Calendario:")
        lbl_vistas.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        lbl_vistas.setStyleSheet("color: #4A3728;")
        layout_cal_widgets.addWidget(lbl_vistas)

        vistas_layout = QHBoxLayout()
        vistas_layout.setSpacing(2)
        
        self.btn_v_diaria = QPushButton("Día")
        self.btn_v_diaria.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.btn_v_diaria.clicked.connect(lambda: self.cambio_vista_calendario.emit("diaria"))
        vistas_layout.addWidget(self.btn_v_diaria)

        self.btn_v_semanal = QPushButton("Sem")
        self.btn_v_semanal.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.btn_v_semanal.clicked.connect(lambda: self.cambio_vista_calendario.emit("semanal"))
        vistas_layout.addWidget(self.btn_v_semanal)

        self.btn_v_mensual = QPushButton("Mes")
        self.btn_v_mensual.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.btn_v_mensual.clicked.connect(lambda: self.cambio_vista_calendario.emit("mensual"))
        vistas_layout.addWidget(self.btn_v_mensual)

        self.btn_v_sem = QPushButton("6M")
        self.btn_v_sem.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.btn_v_sem.clicked.connect(lambda: self.cambio_vista_calendario.emit("semestral"))
        vistas_layout.addWidget(self.btn_v_sem)

        layout_cal_widgets.addLayout(vistas_layout)

        # Botones de utilidad
        btn_eventos = QPushButton(" Eventos")
        btn_eventos.setIcon(svg_to_qicon(icon_calendar(), size=20, color="#000000"))
        btn_eventos.setStyleSheet("text-align: left; padding: 5px; font-weight: bold;")
        btn_eventos.clicked.connect(self.evento_nuevo.emit)
        
        btn_correo = QPushButton(" Correo")
        btn_correo.setIcon(svg_to_qicon(icon_folder(), size=20, color="#000000"))
        btn_correo.setStyleSheet("text-align: left; padding: 5px;")
        btn_correo.clicked.connect(self._no_implementado)
        
        btn_portapapeles = QPushButton(" Portapapeles")
        btn_portapapeles.setIcon(svg_to_qicon(icon_settings(), size=20, color="#000000"))
        btn_portapapeles.setStyleSheet("text-align: left; padding: 5px;")
        btn_portapapeles.clicked.connect(self._no_implementado)

        layout_cal_widgets.addWidget(btn_eventos)
        layout_cal_widgets.addWidget(btn_correo)
        layout_cal_widgets.addWidget(btn_portapapeles)

        self.layout_principal.addWidget(self.calendar_container)

        # Espaciador para empujar la papelera abajo
        self.spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout_principal.addItem(self.spacer)

        # Papelera Esqueumórfica
        self.trash_bin = TrashBinWidget(self.db)
        self.trash_bin.clicked.connect(self.papelera_clicked.emit)
        self.layout_principal.addWidget(self.trash_bin, 0, Qt.AlignmentFlag.AlignCenter)

    def set_active_section(self, section_id: str):
        """Muestra u oculta widgets según la sección activa."""
        # Mantenemos el almanaque siempre visible
        self.calendar_container.show()

    def _no_implementado(self):
        QMessageBox.information(self, "Lotus Organizer", "Servicio no disponible o fuera de línea (Simulación clásica).")


# ═══════════════════════════════════════════════════════════
# VENTANA PRINCIPAL DE VITO ORGANIZER
# ═══════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """
    Ventana principal de la réplica esqueumórfica Vito Organizer.
    """

    def __init__(self, agenda_data: dict, parent=None):
        super().__init__(parent)
        self.agenda_data = agenda_data
        self.agenda_nombre = agenda_data["nombre"]
        self.db = Database(agenda_data["db_path"])
        self.notas_dir = agenda_data["notas_dir"]

        self.setWindowTitle(f"Vito Organizer - [{self.agenda_nombre}]")
        self.setMinimumSize(900, 600)

        # Icono de la ventana
        from svg_icons import svg_to_qicon, icon_agenda
        self.setWindowIcon(svg_to_qicon(icon_agenda(), size=64, color="#2b5da8"))

        self._setup_modules()
        self._setup_ui()
        self._setup_menubar()
        self._setup_toolbar()
        self._setup_statusbar()
        
        # Temporizador de Autoguardado
        self.timer_autosave = QTimer(self)
        self.timer_autosave.timeout.connect(self._guardar_automatico)
        self.configurar_timer_autosave()

        # Iniciar en Portada
        self._cambiar_modulo("portada")

    def _setup_modules(self):
        self.modulos = {
            "calendario": TabCalendar(self.db),
            "notas": TabNotes(self.db, self.notas_dir),
            "inventario": TabInventory(self.db),
            "instrumentos": TabInstruments(self.db),
            "enlaces": TabBookmarks(self.db),
            "portada": PortadaWidget(self.agenda_data, self.db)
        }

    def _setup_ui(self):
        central = LeatherBackground()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # ── Panel Izquierdo (SmartCenter) ──
        self.smart_center = SmartCenterWidget(self.db)
        self.smart_center.cambio_vista_calendario.connect(self._cambiar_vista_calendario)
        self.smart_center.evento_nuevo.connect(self._crear_evento_calendario)
        self.smart_center.papelera_clicked.connect(self._mostrar_papelera)
        main_layout.addWidget(self.smart_center)

        # ── Contenedor de la Agenda Física ──
        agenda_layout = QHBoxLayout()
        agenda_layout.setSpacing(0)
        
        # Página Izquierda + Pestañas Izquierdas
        left_page_container = QWidget()
        left_page_layout = QHBoxLayout(left_page_container)
        left_page_layout.setContentsMargins(0, 0, 0, 0)
        left_page_layout.setSpacing(0)
        
        self.tabs_izq = QVBoxLayout()
        self.tabs_izq.setContentsMargins(0, 40, 0, 0)
        self.tabs_izq.setSpacing(2)
        self.tabs_izq.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self._crear_pestana("Calendario", "calendario", TAB_COLORS["red"], "left", self.tabs_izq)
        self._crear_pestana("Inventario", "inventario", TAB_COLORS["green"], "left", self.tabs_izq)
        
        left_page_layout.addLayout(self.tabs_izq)
        self.pagina_izquierda = PaperPageWidget(side="left")
        left_page_layout.addWidget(self.pagina_izquierda, stretch=1)
        
        agenda_layout.addWidget(left_page_container, stretch=1)

        # Anillas centrales
        self.anillas = RingSpineWidget()
        agenda_layout.addWidget(self.anillas)

        # Página Derecha + Pestañas Derechas
        right_page_container = QWidget()
        right_page_layout = QHBoxLayout(right_page_container)
        right_page_layout.setContentsMargins(0, 0, 0, 0)
        right_page_layout.setSpacing(0)
        
        self.pagina_derecha = PaperPageWidget(side="right")
        right_page_layout.addWidget(self.pagina_derecha, stretch=1)
        
        self.tabs_der = QVBoxLayout()
        self.tabs_der.setContentsMargins(0, 40, 0, 0)
        self.tabs_der.setSpacing(2)
        self.tabs_der.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self._crear_pestana("Notas", "notas", TAB_COLORS["yellow"], "right", self.tabs_der)
        self._crear_pestana("Instrumentos", "instrumentos", TAB_COLORS["blue"], "right", self.tabs_der)
        self._crear_pestana("Enlaces", "enlaces", TAB_COLORS["purple"], "right", self.tabs_der)
        
        right_page_layout.addLayout(self.tabs_der)
        agenda_layout.addWidget(right_page_container, stretch=1)

        main_layout.addLayout(agenda_layout)
        
        # Almacenar botones de pestañas
        self.all_tab_buttons = []
        for i in range(self.tabs_izq.count()):
            widget = self.tabs_izq.itemAt(i).widget()
            if isinstance(widget, TabButton): self.all_tab_buttons.append(widget)
        for i in range(self.tabs_der.count()):
            widget = self.tabs_der.itemAt(i).widget()
            if isinstance(widget, TabButton): self.all_tab_buttons.append(widget)

    def _crear_pestana(self, text, id_str, color, side, layout):
        btn = TabButton(id_str, text, color, side)
        btn.clicked.connect(self._cambiar_modulo)
        layout.addWidget(btn)

    def _setup_menubar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #d4d0c8;
                color: #000000;
                border-bottom: 2px outset #ffffff;
            }
            QMenuBar::item {
                background: transparent;
                padding: 4px 10px;
                margin: 2px 0;
            }
            QMenuBar::item:selected {
                background: #000080;
                color: #ffffff;
            }
            QMenu {
                background-color: #d4d0c8;
                border: 2px outset #ffffff;
                color: #000000;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #000080;
                color: #ffffff;
            }
        """)

        # Archivo
        menu_archivo = menubar.addMenu("Archivo")
        accion_abrir = menu_archivo.addAction("Abrir Agenda...")
        accion_abrir.triggered.connect(self._abrir_selector_agendas)
        menu_archivo.addSeparator()
        accion_salir = menu_archivo.addAction("Salir")
        accion_salir.triggered.connect(self.close)

        # Edición
        menu_edicion = menubar.addMenu("Edición")
        accion_opciones = menu_edicion.addAction("Opciones...")
        accion_opciones.triggered.connect(self._abrir_opciones)

        # Sección
        menu_seccion = menubar.addMenu("Sección")
        
        accion_portada = menu_seccion.addAction("Portada")
        accion_portada.triggered.connect(lambda: self._cambiar_modulo("portada"))
        
        accion_cal = menu_seccion.addAction("Calendario")
        accion_cal.triggered.connect(lambda: self._cambiar_modulo("calendario"))
        
        accion_notas = menu_seccion.addAction("Notas")
        accion_notas.triggered.connect(lambda: self._cambiar_modulo("notas"))
        
        accion_inv = menu_seccion.addAction("Inventario")
        accion_inv.triggered.connect(lambda: self._cambiar_modulo("inventario"))
        
        accion_inst = menu_seccion.addAction("Instrumentos")
        accion_inst.triggered.connect(lambda: self._cambiar_modulo("instrumentos"))
        
        accion_enlaces = menu_seccion.addAction("Enlaces")
        accion_enlaces.triggered.connect(lambda: self._cambiar_modulo("enlaces"))

        # Ayuda
        menu_ayuda = menubar.addMenu("Ayuda")
        accion_acerca = menu_ayuda.addAction("Acerca de...")
        accion_acerca.triggered.connect(self._abrir_acerca_de)
        accion_historicos = menu_ayuda.addAction("Históricos...")
        accion_historicos.triggered.connect(self._abrir_historicos)

    def _setup_toolbar(self):
        from PyQt6.QtWidgets import QToolBar
        from svg_icons import svg_to_qicon, icon_new, icon_edit, icon_delete, icon_calendar, icon_folder
        toolbar = QToolBar("Barra Principal")
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #d4d0c8;
                border-bottom: 2px outset #ffffff;
                spacing: 5px;
            }
            QToolButton {
                background: transparent;
                border: 1px solid transparent;
                padding: 4px;
            }
            QToolButton:hover {
                border: 1px outset #ffffff;
                background-color: #e4e0d8;
            }
        """)
        self.addToolBar(toolbar)

        c = "#404040"
        accion_nuevo = toolbar.addAction(svg_to_qicon(icon_new(), size=24, color=c), "Nuevo Evento/Item")
        accion_nuevo.triggered.connect(self._accion_nuevo_global)
        
        toolbar.addSeparator()
        
        accion_cal_dia = toolbar.addAction(svg_to_qicon(icon_calendar(), size=24, color=c), "Día")
        accion_cal_dia.triggered.connect(lambda: self._cambiar_vista_calendario("diaria"))
        
        accion_cal_sem = toolbar.addAction(svg_to_qicon(icon_calendar(), size=24, color=c), "Semana")
        accion_cal_sem.triggered.connect(lambda: self._cambiar_vista_calendario("semanal"))
        
        accion_cal_mes = toolbar.addAction(svg_to_qicon(icon_calendar(), size=24, color=c), "Mes")
        accion_cal_mes.triggered.connect(lambda: self._cambiar_vista_calendario("mensual"))

    def _setup_statusbar(self):
        status = QStatusBar()
        status.setStyleSheet("background: #d4d0c8; color: #000; border-top: 1px solid #808080;")
        self.setStatusBar(status)

    def _cambiar_modulo(self, modulo_id: str):
        """Enruta el contenido de los módulos a la agenda."""
        for btn in self.all_tab_buttons:
            btn.is_selected = (btn.id_str == modulo_id)
            btn.update()

        modulo = self.modulos.get(modulo_id)
        if not modulo: return

        self.smart_center.set_active_section(modulo_id)

        # Enrutamiento de Portada y Calendario (Doble página dividida)
        if modulo_id == "portada":
            self.pagina_izquierda.show()
            self.anillas.show()
            # Actualizar stats de la portada
            modulo.actualizar_datos()
            self.pagina_izquierda.set_content(modulo.panel_izquierdo)
            self.pagina_derecha.set_content(modulo.panel_derecho)
            # Deseleccionar pestañas
            for btn in self.all_tab_buttons:
                btn.is_selected = False
                btn.update()
        elif modulo_id == "calendario":
            self.pagina_izquierda.show()
            self.anillas.show()
            # Forzar actualización de datos en las vistas
            modulo.actualizar_vista()
            self.pagina_izquierda.set_content(modulo.panel_izquierdo)
            self.pagina_derecha.set_content(modulo.panel_derecho)
        elif hasattr(modulo, 'panel_izquierdo') and hasattr(modulo, 'panel_derecho'):
            self.pagina_izquierda.show()
            self.anillas.show()
            self.pagina_izquierda.set_content(modulo.panel_izquierdo)
            self.pagina_derecha.set_content(modulo.panel_derecho)
        else:
            self.pagina_izquierda.show()
            self.anillas.show()
            
            # Dejar la página izquierda en blanco como una agenda física
            lbl_blanco = QLabel("")
            self.pagina_izquierda.set_content(lbl_blanco)
            
            # Poner el contenido en la página derecha
            self.pagina_derecha.set_content(modulo)

        # Actualizar estado de la papelera
        self.smart_center.trash_bin.actualizar_estado()
        self.statusBar().showMessage(f" Agenda: {self.agenda_nombre} | Vista actual: {modulo_id.capitalize()}")

    def actualizar_vista_actual(self):
        """Refresca los datos del módulo activo (se llama tras restaurar/borrar)."""
        # Recargar stats de portada
        if "portada" in self.modulos:
            self.modulos["portada"].actualizar_datos()
        
        # Recargar calendario
        if "calendario" in self.modulos:
            self.modulos["calendario"].actualizar_vista()

        # Recargar notas si está seleccionado
        modulo_notas = self.modulos.get("notas")
        if modulo_notas and hasattr(modulo_notas, "_recargar_lista_notas"):
            modulo_notas._recargar_lista_notas(modulo_notas.input_busqueda.text())

        # Actualizar papelera
        self.smart_center.trash_bin.actualizar_estado()

    def _obtener_info_modulo(self, modulo_id: str) -> str:
        textos = {
            "calendario": "Calendario y Planner\n\nOrganiza tu tiempo.",
            "notas": "Bloc de Notas Markdown\n\nGestión de apuntes.",
            "inventario": "Inventario\n\nControl de componentes.",
            "instrumentos": "Instrumentos\n\nEstado del banco de trabajo.",
            "enlaces": "Enlaces\n\nMarcadores y referencias."
        }
        return textos.get(modulo_id, "")

    def _accion_nuevo_global(self):
        """Acción de nuevo global según el módulo actual."""
        # Se asume que el modulo activo tiene una acción de nuevo, por ahora abrimos evento
        self._crear_evento_calendario()

    # Slots de barra lateral de Calendario
    def _cambiar_vista_calendario(self, vista: str):
        if "calendario" in self.modulos:
            self.modulos["calendario"].set_vista(vista)

    def _crear_evento_calendario(self):
        if "calendario" in self.modulos:
            self.modulos["calendario"].crear_evento()

    # Slots de barra de herramientas superior e inferior
    def _mostrar_papelera(self):
        dialog = TrashDialog(self.db, self)
        dialog.exec()

    def _abrir_opciones(self):
        dialog = OptionsDialog(self.agenda_data, self.db, self)
        dialog.exec()

    def _abrir_selector_agendas(self):
        from agenda_manager import AgendaSelectorDialog
        self.close()
        selector = AgendaSelectorDialog()
        if selector.exec() == AgendaSelectorDialog.DialogCode.Accepted:
            agenda_data = selector.agenda_seleccionada
            if agenda_data:
                self.new_window = MainWindow(agenda_data)
                self.new_window.showMaximized()

    def _abrir_acerca_de(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Acerca de Vito Organizer")
        dialog.setFixedSize(380, 260)
        dialog.setStyleSheet("background-color: #d4d0c8; color: #000000;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        lbl_title = QLabel("Vito Organizer")
        lbl_title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #4a3728;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)
        
        lbl_ver = QLabel("Versión 1.0 (v.1.0)")
        lbl_ver.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_ver)
        
        lbl_desc = QLabel(
            "Una réplica moderna y esqueumórfica de la clásica agenda Lotus Organizer de los años 90.\n\n"
            "Desarrollado en Python utilizando PyQt6 y SQLite3 local."
        )
        lbl_desc.setFont(QFont("Arial", 10))
        lbl_desc.setWordWrap(True)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_desc)
        
        layout.addStretch()
        
        btn_ok = QPushButton("Aceptar")
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setFixedWidth(100)
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(btn_ok)
        btn_container.addStretch()
        layout.addLayout(btn_container)
        
        dialog.exec()

    def _abrir_historicos(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Historial de Cambios (Históricos)")
        dialog.setMinimumSize(520, 420)
        dialog.setStyleSheet("background-color: #d4d0c8; color: #000000;")
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_title = QLabel("Registro de Cambios por Versión")
        lbl_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: #4a3728;")
        layout.addWidget(lbl_title)
        
        browser = QTextBrowser()
        browser.setStyleSheet("background-color: #ffffff; color: #2C1810; border: 2px inset #808080;")
        
        # Leer changelog.md
        changelog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "changelog.md")
        contenido = ""
        if os.path.exists(changelog_path):
            try:
                with open(changelog_path, 'r', encoding='utf-8') as f:
                    contenido = f.read()
            except Exception:
                contenido = "No se pudo leer el archivo changelog.md"
        else:
            contenido = "Archivo changelog.md no encontrado."

        try:
            import markdown
            html = markdown.markdown(contenido)
            html_completo = f"""
            <html>
            <head>
            <style>
                body {{ font-family: 'Arial', sans-serif; font-size: 13px; line-height: 1.5; color: #2C1810; }}
                h1, h2, h3 {{ color: #4a3728; border-bottom: 1px solid #808080; padding-bottom: 3px; }}
                li {{ margin-bottom: 5px; }}
            </style>
            </head>
            <body>{html}</body>
            </html>
            """
            browser.setHtml(html_completo)
        except Exception:
            browser.setPlainText(contenido)
            
        layout.addWidget(browser, 1)
        
        btn_ok = QPushButton("Cerrar")
        btn_ok.clicked.connect(dialog.accept)
        btn_ok.setFixedWidth(100)
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        btn_container.addWidget(btn_ok)
        btn_container.addStretch()
        layout.addLayout(btn_container)
        
        dialog.exec()

    # Autoguardado
    def configurar_timer_autosave(self):
        enabled = self.db.obtener_config("autosave_enabled", "false")
        interval = self.db.obtener_config("autosave_interval", "5")
        if enabled == "true":
            self.timer_autosave.start(int(interval) * 60 * 1000)
        else:
            self.timer_autosave.stop()

    def _guardar_automatico(self):
        # Si el modulo Notas está cargado, forzar guardado si hay nota activa
        modulo_notas = self.modulos.get("notas")
        if modulo_notas and hasattr(modulo_notas, "_guardar_nota"):
            # Solo guardamos si el ID es válido
            if modulo_notas._nota_actual_id is not None:
                modulo_notas._guardar_nota()
                self.statusBar().showMessage("Guardado automático realizado con éxito.", 3000)

    def closeEvent(self, event):
        self.db.cerrar()
        event.accept()
