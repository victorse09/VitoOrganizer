# =============================================================================
# Vito Organizer v2.2 - Cumpleaños, Aniversarios y Feriados Plugin
# =============================================================================

import os
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, QRect, QRectF, pyqtSignal, QDate
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
)

from plugins.plugin_base import PluginBase
from data.data_store import DataStore
from plugins.cumpleanos.dialogs import (
    BirthdayDialog, AnniversaryDialog, HolidayDialog, CumpleanosSettingsDialog
)


class HalfYearView(QWidget):
    """Vista de medio año (3 meses por página) para Cumpleaños y Feriados."""
    
    edit_event_requested = pyqtSignal(dict)

    def __init__(self, months, parent=None):
        super().__init__(parent)
        self.months = months # List of tuples: [(month_num, "Month Name"), ...]
        self.events: List[dict] = []
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self._drawn_events = []

    def set_months(self, months):
        self.months = months
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        self._drawn_events.clear()
        
        if not self.months:
            return
            
        block_height = height / 3.0
        
        for i, (month_num, month_name) in enumerate(self.months):
            y_offset = int(i * block_height)
            margin_side = 30
            
            # --- 1. Cabecera del Mes ---
            header_height = 30
            header_rect = QRect(margin_side, y_offset, width - 2 * margin_side, header_height)
            
            # Efecto biselado 3D
            painter.fillRect(header_rect, QColor("#FFFFFF"))
            painter.setPen(QPen(QColor("#FFFFFF"), 2))
            painter.drawLine(header_rect.topLeft(), header_rect.topRight())
            painter.drawLine(header_rect.topLeft(), header_rect.bottomLeft())
            painter.setPen(QPen(QColor("#A0A0A0"), 2))
            painter.drawLine(header_rect.bottomLeft(), header_rect.bottomRight())
            painter.drawLine(header_rect.topRight(), header_rect.bottomRight())
            
            # Texto del mes
            painter.setPen(QPen(QColor("#000000")))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(12)
            painter.setFont(font)
            text_rect = header_rect.adjusted(10, 0, 0, 0)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, month_name)
            
            # --- 2. Área de contenido y líneas ---
            content_rect = QRect(margin_side, y_offset + header_height, width - 2 * margin_side, int(block_height) - header_height)
            
            # Línea de margen roja
            margin_x = margin_side + 40
            painter.setPen(QPen(QColor("#FF9999"), 1))
            painter.drawLine(margin_x, content_rect.top(), margin_x, content_rect.bottom())
            
            # Líneas horizontales tipo cuaderno
            line_spacing = 22
            painter.setPen(QPen(QColor("#D0D0C0"), 1))
            num_lines = content_rect.height() // line_spacing
            for j in range(1, num_lines + 1):
                line_y = content_rect.top() + j * line_spacing
                painter.drawLine(margin_side, line_y, width - margin_side, line_y)

            # --- 3. Filtrar y dibujar eventos del mes ---
            month_events = []
            for ev in self.events:
                d_str = ev.get('date', '')
                try:
                    parts = d_str.split('-')
                    if len(parts) >= 3 and int(parts[1]) == month_num:
                        month_events.append((int(parts[2]), ev))
                except (ValueError, IndexError):
                    continue

            month_events.sort(key=lambda x: x[0]) # Ordenar por día del mes

            line_idx = 1
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            icons_dir = os.path.join(base_dir, 'resources', 'icons')
            icon_bday = QIcon(os.path.join(icons_dir, 'birthday.svg'))
            icon_anniv = QIcon(os.path.join(icons_dir, 'anniversary.svg'))
            icon_holiday = QIcon(os.path.join(icons_dir, 'holiday.svg'))

            font_ev = QFont("Arial", 9)
            painter.setFont(font_ev)

            for day_num, ev in month_events:
                if line_idx > num_lines:
                    break
                
                line_y = content_rect.top() + line_idx * line_spacing
                ev_rect = QRectF(margin_x + 6, line_y - 18, width - margin_x - margin_side - 12, 18)
                self._drawn_events.append((ev_rect, ev))

                ev_type = ev.get('type', 'birthday')
                name = ev.get('name', '')

                if ev_type == 'birthday':
                    painter.setPen(QPen(QColor("#D81B60"))) # Pink/Magenta
                    age_str = f" ({ev['age']} años)" if ev.get('age') else ""
                    text = f"{day_num} {name}{age_str}"
                    icon = icon_bday
                elif ev_type == 'anniversary':
                    painter.setPen(QPen(QColor("#8E44AD"))) # Purple
                    motive_str = f" - {ev['motive']}" if ev.get('motive') else ""
                    text = f"{day_num} {name}{motive_str}"
                    icon = icon_anniv
                else: # holiday
                    painter.setPen(QPen(QColor("#D32F2F"))) # Red
                    text = f"{day_num} {name}"
                    icon = icon_holiday

                # Draw SVG Icon
                icon_size = 14
                icon_rect = QRectF(
                    ev_rect.left(),
                    ev_rect.top() + (ev_rect.height() - icon_size) / 2.0,
                    icon_size,
                    icon_size
                )
                icon.paint(painter, icon_rect.toRect())

                # Draw text shifted to the right of the icon
                text_rect = ev_rect.adjusted(icon_size + 6, 0, 0, 0)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
                line_idx += 1

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            for ev_rect, ev in self._drawn_events:
                if ev_rect.contains(pos):
                    self.edit_event_requested.emit(ev)
                    return
        super().mouseDoubleClickEvent(event)


class CumpleanosSidebar(QWidget):
    """Barra lateral para la sección de Cumpleaños, Aniversarios y Feriados."""
    
    semester_changed = pyqtSignal(int)
    add_birthday_clicked = pyqtSignal()
    add_anniversary_clicked = pyqtSignal()
    add_holiday_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _get_icon(self, name: str) -> QIcon:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return QIcon(os.path.join(base_dir, 'resources', 'icons', name))

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        # 1. Selector de Semestres
        sem_layout = QVBoxLayout()
        sem_layout.setSpacing(4)
        
        self.btn_sem1 = QPushButton("Enero - Junio")
        self.btn_sem2 = QPushButton("Julio - Diciembre")
        
        for b in (self.btn_sem1, self.btn_sem2):
            b.setCheckable(True)
            b.setStyleSheet("""
                QPushButton { text-align: center; padding: 6px; border: 1px solid #45475a; border-radius: 4px; background: rgba(255, 255, 255, 0.05); color: #cdd6f4; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #f9e2af; border-color: #f9e2af; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)

        self.btn_sem1.setChecked(True)
        self.btn_sem1.clicked.connect(lambda: self._on_sem_clicked(1))
        self.btn_sem2.clicked.connect(lambda: self._on_sem_clicked(2))

        sem_layout.addWidget(self.btn_sem1)
        sem_layout.addWidget(self.btn_sem2)
        layout.addLayout(sem_layout)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        layout.addWidget(line)

        # 2. Botones de Acción para Añadir Eventos
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)

        btn_bday = QPushButton(" Cumpleaños")
        btn_bday.setIcon(self._get_icon('birthday.svg'))
        btn_anniv = QPushButton(" Aniversarios")
        btn_anniv.setIcon(self._get_icon('anniversary.svg'))
        btn_holiday = QPushButton(" Feriados")
        btn_holiday.setIcon(self._get_icon('holiday.svg'))

        btn_style = """
            QPushButton { text-align: left; padding: 8px 12px; border-radius: 6px; background-color: rgba(255, 255, 255, 0.08); color: #ffffff; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """
        btn_bday.setStyleSheet(btn_style)
        btn_anniv.setStyleSheet(btn_style)
        btn_holiday.setStyleSheet(btn_style)

        btn_bday.clicked.connect(self.add_birthday_clicked.emit)
        btn_anniv.clicked.connect(self.add_anniversary_clicked.emit)
        btn_holiday.clicked.connect(self.add_holiday_clicked.emit)

        actions_layout.addWidget(btn_bday)
        actions_layout.addWidget(btn_anniv)
        actions_layout.addWidget(btn_holiday)
        layout.addLayout(actions_layout)

        layout.addStretch()

        # 3. Botón de engranaje inferior izquierdo
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(self._get_icon('settings.svg'))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Cumpleaños y Feriados")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def _on_sem_clicked(self, sem):
        if sem == 1:
            self.btn_sem1.setChecked(True)
            self.btn_sem2.setChecked(False)
        else:
            self.btn_sem1.setChecked(False)
            self.btn_sem2.setChecked(True)
        self.semester_changed.emit(sem)


class CumpleanosPlugin(PluginBase):
    """Plugin para la sección de Cumpleaños, Aniversarios y Feriados."""
    
    trash_changed = pyqtSignal()
    events_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._data = {'events': [], '_trash': []}
        self._trash = []
        self._is_modified = False
        
        self.semester = 1
        
        # Sidebar
        self._sidebar = CumpleanosSidebar()
        self._sidebar.semester_changed.connect(self.set_semester)
        self._sidebar.add_birthday_clicked.connect(self._on_add_birthday)
        self._sidebar.add_anniversary_clicked.connect(self._on_add_anniversary)
        self._sidebar.add_holiday_clicked.connect(self._on_add_holiday)
        self._sidebar.settings_clicked.connect(self._on_settings)

        # Pages
        self.months_names = [
            (1, "Enero"), (2, "Febrero"), (3, "Marzo"),
            (4, "Abril"), (5, "Mayo"), (6, "Junio"),
            (7, "Julio"), (8, "Agosto"), (9, "Septiembre"),
            (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre")
        ]
        
        self._left_page = HalfYearView(self.months_names[0:3])
        self._right_page = HalfYearView(self.months_names[3:6])

        self._left_page.edit_event_requested.connect(self._on_edit_event)
        self._right_page.edit_event_requested.connect(self._on_edit_event)

    def set_semester(self, semester):
        self.semester = semester
        if semester == 1:
            self._left_page.set_months(self.months_names[0:3])
            self._right_page.set_months(self.months_names[3:6])
        else:
            self._left_page.set_months(self.months_names[6:9])
            self._right_page.set_months(self.months_names[9:12])
        self._update_views()
        self.page_changed.emit(self.semester, 2)

    def _update_views(self):
        events = self._data.get('events', [])
        self._left_page.set_events(events)
        self._right_page.set_events(events)
        self.events_changed.emit()

    def _on_add_birthday(self):
        dlg = BirthdayDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.event_data:
            self._data.setdefault('events', []).append(dlg.event_data)
            self._is_modified = True
            self._update_views()

    def _on_add_anniversary(self):
        dlg = AnniversaryDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.event_data:
            self._data.setdefault('events', []).append(dlg.event_data)
            self._is_modified = True
            self._update_views()

    def _on_add_holiday(self):
        dlg = HolidayDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.event_data:
            self._data.setdefault('events', []).append(dlg.event_data)
            self._is_modified = True
            self._update_views()

    def _on_edit_event(self, ev_dict: dict):
        ev_type = ev_dict.get('type', 'birthday')
        dlg = None
        if ev_type == 'birthday':
            dlg = BirthdayDialog(event_to_edit=ev_dict, parent=self._sidebar.window())
        elif ev_type == 'anniversary':
            dlg = AnniversaryDialog(event_to_edit=ev_dict, parent=self._sidebar.window())
        else:
            dlg = HolidayDialog(event_to_edit=ev_dict, parent=self._sidebar.window())

        if dlg.exec():
            events = self._data.get('events', [])
            if dlg.is_delete:
                if ev_dict in events:
                    events.remove(ev_dict)
                    self.move_to_trash(ev_dict)
                    self._is_modified = True
                    self._update_views()
                    self.trash_changed.emit()
            elif dlg.event_data:
                idx = events.index(ev_dict) if ev_dict in events else -1
                if idx >= 0:
                    events[idx] = dlg.event_data
                else:
                    events.append(dlg.event_data)
                self._is_modified = True
                self._update_views()

    def _on_settings(self):
        dlg = CumpleanosSettingsDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.imported_holidays:
            events = self._data.setdefault('events', [])
            # Evitar duplicados por fecha y nombre
            existing_keys = {(e.get('date'), e.get('name')) for e in events}
            added_count = 0
            for h in dlg.imported_holidays:
                key = (h.get('date'), h.get('name'))
                if key not in existing_keys:
                    events.append(h)
                    existing_keys.add(key)
                    added_count += 1
            if added_count > 0:
                self._is_modified = True
                self._update_views()

    # --- Métodos de Trash / Papelera ---
    def move_to_trash(self, item: dict):
        self._trash.append(item)

    def get_trash_items(self) -> list:
        return self._trash

    def restore_item(self, index: int):
        if 0 <= index < len(self._trash):
            item = self._trash.pop(index)
            self._data.setdefault('events', []).append(item)
            self._is_modified = True
            self._update_views()
            self.trash_changed.emit()

    def delete_permanently(self, index: int):
        if 0 <= index < len(self._trash):
            self._trash.pop(index)
            self._is_modified = True
            self.trash_changed.emit()

    def empty_trash(self):
        if self._trash:
            self._trash.clear()
            self._is_modified = True
            self.trash_changed.emit()

    def get_total_pages(self) -> int:
        return 2

    def get_current_page(self) -> int:
        return self.semester

    def go_to_page(self, page_num: int):
        if page_num in (1, 2):
            self._sidebar._on_sem_clicked(page_num)

    def get_name(self) -> str: return "Cumpleaños"
    def get_id(self) -> str: return "cumpleanos"
    def get_icon(self) -> str: return "birthday.svg"
    def get_tab_color(self) -> str: return "#FF69B4"
    def get_order(self) -> int: return 2

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

    def load_data(self, agenda_path: str):
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
            self._trash = loaded.get('_trash', [])
        self._update_views()
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            DataStore.save(data_path, self._data)
            self._is_modified = False
