# =============================================================================
# Vito Organizer v2.2 - Calendar Sidebar
# Barra lateral para la sección de calendario
# =============================================================================

import os
from datetime import datetime
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QCalendarWidget, QPushButton, 
    QLabel, QHBoxLayout, QButtonGroup
)

class ClickableLabel(QLabel):
    """Label cliqueable para volver al día de hoy."""
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class CalendarSidebar(QWidget):
    """Widget de barra lateral para el Calendario."""
    
    date_changed = pyqtSignal(QDate)
    view_changed = pyqtSignal(str) # 'day', 'week', 'month', 'semester', 'year'
    add_event_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _get_icon(self, name: str) -> QIcon:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return QIcon(os.path.join(base_dir, 'resources', 'icons', name))

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(12)

        # 1. Mini Calendario de navegación
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.clicked.connect(self.date_changed.emit)
        layout.addWidget(self.calendar)

        # 2. Display de fecha actual grande (Fija en HOY, cliqueable para volver a hoy)
        self.date_display = ClickableLabel()
        self.date_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.date_display.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date_display.setToolTip("Volver al día de hoy")
        self.date_display.setStyleSheet("""
            QLabel {
                background-color: #313244;
                border-radius: 6px;
                padding: 10px;
                color: #cdd6f4;
            }
            QLabel:hover {
                background-color: #45475a;
            }
        """)
        self._update_date_display(QDate.currentDate())
        self.date_display.clicked.connect(self._go_to_today)
        layout.addWidget(self.date_display)

        # 3. Botón Agregar Evento
        self.btn_add_event = QPushButton("Nuevo Evento")
        self.btn_add_event.setIcon(self._get_icon('add_event.svg'))
        self.btn_add_event.setObjectName("primaryButton")
        self.btn_add_event.clicked.connect(self.add_event_clicked.emit)
        layout.addWidget(self.btn_add_event)

        # 4. Botones de vista
        views_layout = QVBoxLayout()
        views_layout.setSpacing(4)
        
        self.view_group = QButtonGroup(self)
        
        views = [
            ('day', 'Día a la vista', 'day_view.svg'),
            ('week', 'Semana a la vista', 'week_view.svg'),
            ('month', 'Mes a la vista', 'month_view.svg'),
            ('semester', 'Semestre a la vista', 'semester_view.svg'),
            ('year', 'Año a la vista', 'year_view.svg')
        ]
        
        for i, (vid, name, icon) in enumerate(views):
            btn = QPushButton(name)
            btn.setIcon(self._get_icon(icon))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding-left: 10px; border: none; background: transparent; }
                QPushButton:checked { background-color: #313244; font-weight: bold; }
                QPushButton:hover:!checked { background-color: #45475a; }
            """)
            btn.clicked.connect(lambda checked, v=vid: self.view_changed.emit(v))
            self.view_group.addButton(btn, i)
            views_layout.addWidget(btn)
            
            if vid == 'day':
                btn.setChecked(True)
                
        layout.addLayout(views_layout)
        layout.addStretch()

        # 5. Botón de engranaje inferior izquierdo para configuración del calendario
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(self._get_icon('settings.svg'))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Calendario")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: #45475a; }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def set_active_view(self, vid: str):
        views = ['day', 'week', 'month', 'semester', 'year']
        if vid in views:
            idx = views.index(vid)
            btn = self.view_group.button(idx)
            if btn:
                btn.setChecked(True)

    def _update_date_display(self, date: QDate):
        """Actualiza el display grande de fecha."""
        d = date.toPyDate()
        # Nombres en español (simple aproximación)
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        text = f"<div style='font-size: 24px; font-weight: bold; color: #f9e2af;'>{d.day}</div>"
        text += f"<div style='font-size: 14px;'>{dias[d.weekday()]}</div>"
        text += f"<div style='font-size: 12px; color: #a6adc8;'>{meses[d.month-1]} {d.year}</div>"
        
        self.date_display.setText(text)
        
    def _go_to_today(self):
        """Vuelve la navegación al día de hoy."""
        today = QDate.currentDate()
        self.calendar.setSelectedDate(today)
        self.date_changed.emit(today)

    def get_selected_date(self) -> QDate:
        return self.calendar.selectedDate()
