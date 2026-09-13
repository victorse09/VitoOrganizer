# =============================================================================
# Vito Organizer v2.2 - Calendario Plugin
# Sección de Calendario
# =============================================================================

from typing import Dict, Any
from PyQt6.QtWidgets import QWidget, QStackedWidget
from PyQt6.QtCore import Qt, QDate, pyqtSignal

from plugins.plugin_base import PluginBase
from data.data_store import DataStore

from plugins.calendario.calendar_sidebar import CalendarSidebar
from plugins.calendario.views import (
    DayView, RightSideView, DayRightContainer,
    WeekLeftView, WeekRightView,
    MonthLeftView, MonthRightView,
    SemesterLeftView, SemesterRightView,
    YearLeftView, YearRightView
)


class CalendarioPlugin(PluginBase):
    """Plugin para la sección de Calendario."""
    
    trash_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._data = {
            'events': [],
            'working_hours': {'start': '08:00', 'end': '17:00'},
            'day_right_mode': 'next_day'
        }
        self._is_modified = False
        self._plugin_manager = None
        
        self._sidebar = CalendarSidebar()
        self._sidebar.date_changed.connect(self._on_date_changed)
        self._sidebar.view_changed.connect(self._on_view_changed)
        self._sidebar.add_event_clicked.connect(self._on_add_event)
        self._sidebar.settings_clicked.connect(self._on_settings)
        
        # Stacks de páginas
        self._left_stack = QStackedWidget()
        self._right_stack = QStackedWidget()
        self._left_stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._right_stack.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._left_stack.setStyleSheet('background: transparent;')
        self._right_stack.setStyleSheet('background: transparent;')
        
        # Instanciar todas las vistas
        day_left, day_right = DayView(), DayRightContainer()
        day_left.create_event_requested.connect(self._on_create_event_at_time)
        day_left.edit_event_requested.connect(self._on_edit_event)
        day_right.next_day_view.create_event_requested.connect(self._on_create_event_at_time)
        day_right.next_day_view.edit_event_requested.connect(self._on_edit_event)

        self._views = {
            'day': (day_left, day_right),
            'week': (WeekLeftView(), WeekRightView()),
            'month': (MonthLeftView(), MonthRightView()),
            'semester': (SemesterLeftView(), SemesterRightView()),
            'year': (YearLeftView(), YearRightView())
        }
        
        self._view_indices = {'day': 0, 'week': 1, 'month': 2, 'semester': 3, 'year': 4}
        
        for vid in ['day', 'week', 'month', 'semester', 'year']:
            left_v, right_v = self._views[vid]
            self._left_stack.addWidget(left_v)
            self._right_stack.addWidget(right_v)

        self._on_date_changed(QDate.currentDate())

    def get_name(self) -> str:
        return "Calendario"

    def get_id(self) -> str:
        return "calendario"

    def get_icon(self) -> str:
        return "calendar.svg"

    def get_tab_color(self) -> str:
        return "#DAA520"

    def get_order(self) -> int:
        return 1

    def create_sidebar_widget(self) -> QWidget:
        return self._sidebar

    def create_left_page(self) -> QWidget:
        return self._left_stack

    def create_right_page(self) -> QWidget:
        return self._right_stack

    def load_data(self, agenda_path: str):
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
            self._trash = loaded.get('_trash', [])
            
        self._update_all_views_events()
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            DataStore.save(data_path, self._data)
            self._is_modified = False

    def get_total_pages(self) -> int:
        return 5

    def get_current_page(self) -> int:
        return self._left_stack.currentIndex() + 1

    def go_to_page(self, page_num: int):
        views = ['day', 'week', 'month', 'semester', 'year']
        if 1 <= page_num <= len(views):
            v_id = views[page_num - 1]
            self._sidebar.set_active_view(v_id)
            self._on_view_changed(v_id)

    def restore_item(self, index: int):
        """Restaura un evento desde la papelera."""
        item = self.restore_from_trash(index)
        if item:
            self._data['events'].append(item)
            self._is_modified = True
            self._update_all_views_events()
            self.trash_changed.emit()

    def set_plugin_manager(self, pm):
        self._plugin_manager = pm

    def _get_combined_events(self):
        cal_events = list(self._data.get('events', []))
        if hasattr(self, '_plugin_manager') and self._plugin_manager:
            cump_p = self._plugin_manager.get_plugin_by_id('cumpleanos')
            if cump_p and hasattr(cump_p, '_data'):
                cump_events = cump_p._data.get('events', [])
                for ev in cump_events:
                    ev_type = ev.get('type', 'birthday')
                    name = ev.get('name', '')
                    title = f"🎂 {name}" if ev_type == 'birthday' else (f"💍 {name}" if ev_type == 'anniversary' else f"🚩 {name}")
                    cal_events.append({
                        'date': ev.get('date'),
                        'title': title,
                        'content': ev.get('notes') or ev.get('motive') or '',
                        'all_day': True,
                        'start_time': '00:00',
                        'end_time': '23:59',
                        'event_type': ev_type,
                        'original_event': ev
                    })
        return cal_events

    def _update_all_views_events(self):
        events = self._get_combined_events()
        time_format = self._data.get('time_format', '24h')
        day_right_mode = self._data.get('day_right_mode', 'next_day')
        
        for left_v, right_v in self._views.values():
            if hasattr(left_v, 'set_time_format'):
                left_v.set_time_format(time_format)
            if hasattr(right_v, 'set_time_format'):
                right_v.set_time_format(time_format)
            if hasattr(left_v, 'set_events'):
                left_v.set_events(events)
            if hasattr(right_v, 'set_events'):
                right_v.set_events(events)
            if hasattr(right_v, 'set_mode'):
                right_v.set_mode(day_right_mode)
            
    def _on_date_changed(self, date):
        for left_v, right_v in self._views.values():
            if hasattr(left_v, 'set_date'):
                left_v.set_date(date)
            if hasattr(right_v, 'set_date'):
                right_v.set_date(date)
        
    def _on_view_changed(self, view_id):
        idx = self._view_indices.get(view_id, 0)
        self._left_stack.setCurrentIndex(idx)
        self._right_stack.setCurrentIndex(idx)
        self.page_changed.emit(idx + 1, 5)

    def _on_add_event(self):
        """Muestra el diálogo para agregar un nuevo evento."""
        from plugins.calendario.dialogs import NewEventDialog
        selected_date = self._sidebar.get_selected_date()
        working_hours = self._data.get('working_hours', {'start': '08:00', 'end': '17:00'})
        time_format = self._data.get('time_format', '24h')
        
        dlg = NewEventDialog(selected_date, working_hours, time_format=time_format, parent=self._sidebar)
        if dlg.exec():
            event_data = dlg.event_data
            if event_data:
                self._data['events'].append(event_data)
                self._is_modified = True
                self._update_all_views_events()

    def _on_create_event_at_time(self, start_time: str):
        """Muestra el diálogo de nuevo evento pre-llenando la hora seleccionada."""
        from plugins.calendario.dialogs import NewEventDialog
        selected_date = self._sidebar.get_selected_date()
        working_hours = self._data.get('working_hours', {'start': '08:00', 'end': '17:00'})
        time_format = self._data.get('time_format', '24h')
        
        dlg = NewEventDialog(selected_date, working_hours, default_start_time=start_time, time_format=time_format, parent=self._sidebar)
        if dlg.exec():
            if dlg.event_data:
                self._data['events'].append(dlg.event_data)
                self._is_modified = True
                self._update_all_views_events()

    def _on_edit_event(self, ev_dict: dict):
        """Muestra el diálogo para editar o eliminar un evento existente."""
        from plugins.calendario.dialogs import NewEventDialog
        selected_date = self._sidebar.get_selected_date()
        working_hours = self._data.get('working_hours', {'start': '08:00', 'end': '17:00'})
        time_format = self._data.get('time_format', '24h')
        
        dlg = NewEventDialog(selected_date, working_hours, event_to_edit=ev_dict, time_format=time_format, parent=self._sidebar)
        if dlg.exec():
            if dlg.is_delete:
                if ev_dict in self._data['events']:
                    self._data['events'].remove(ev_dict)
                    self.move_to_trash(ev_dict)
                    self._is_modified = True
                    self._update_all_views_events()
                    self.trash_changed.emit()
            elif dlg.event_data:
                idx = self._data['events'].index(ev_dict) if ev_dict in self._data['events'] else -1
                if idx >= 0:
                    self._data['events'][idx] = dlg.event_data
                else:
                    self._data['events'].append(dlg.event_data)
                self._is_modified = True
                self._update_all_views_events()

    def _on_settings(self):
        """Muestra el diálogo de configuración de la jornada laboral y formato de hora."""
        from plugins.calendario.dialogs import CalendarSettingsDialog
        working_hours = self._data.get('working_hours', {'start': '08:00', 'end': '17:00'})
        time_format = self._data.get('time_format', '24h')
        day_right_mode = self._data.get('day_right_mode', 'next_day')
        
        dlg = CalendarSettingsDialog(working_hours, current_time_format=time_format, current_day_right_mode=day_right_mode, parent=self._sidebar)
        if dlg.exec():
            if dlg.new_working_hours:
                self._data['working_hours'] = dlg.new_working_hours
            if dlg.new_time_format:
                self._data['time_format'] = dlg.new_time_format
            if dlg.new_day_right_mode:
                self._data['day_right_mode'] = dlg.new_day_right_mode
            self._is_modified = True
            self._update_all_views_events()
