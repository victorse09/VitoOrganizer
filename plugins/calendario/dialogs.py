# =============================================================================
# Vito Organizer v2.2 - Calendar Dialogs
# Diálogos para crear eventos y configurar el calendario
# =============================================================================

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QDateEdit, QTimeEdit, QSpinBox, 
    QRadioButton, QButtonGroup, QGroupBox, QFormLayout
)


class NewEventDialog(QDialog):
    """Diálogo para crear o editar un evento en el calendario."""

    def __init__(self, selected_date: QDate, working_hours: dict, default_start_time: str = None, event_to_edit: dict = None, time_format: str = '24h', parent=None):
        super().__init__(parent)
        self.selected_date = selected_date
        self.working_hours = working_hours # {'start': '08:00', 'end': '17:00'}
        self.default_start_time = default_start_time
        self.event_to_edit = event_to_edit
        self.time_format = time_format
        self.event_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Evento" if event_to_edit else "Nuevo Evento")
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Selector de fecha
        form_layout = QFormLayout()
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        
        if self.event_to_edit:
            self.date_edit.setDate(QDate.fromString(self.event_to_edit.get('date'), "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(self.selected_date)
            
        form_layout.addRow("Fecha:", self.date_edit)

        # 2. Título y Contenido
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título del evento")
        if self.event_to_edit:
            self.title_input.setText(self.event_to_edit.get('title', ''))
        form_layout.addRow("Título:", self.title_input)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Descripción o notas del evento...")
        self.content_input.setMaximumHeight(80)
        if self.event_to_edit:
            self.content_input.setText(self.event_to_edit.get('content', ''))
        form_layout.addRow("Contenido:", self.content_input)

        layout.addLayout(form_layout)

        # 3. Modalidades de horario
        mode_groupbox = QGroupBox("Modalidad de Horario")
        mode_layout = QVBoxLayout(mode_groupbox)

        self.rb_inicio = QRadioButton("Inicio (Hora de inicio + Duración)")
        self.rb_periodo = QRadioButton("Periodo (Hora de inicio + Hora de término)")
        self.rb_all_day = QRadioButton("Todo el día (Jornada laboral completa)")

        mode_layout.addWidget(self.rb_inicio)
        mode_layout.addWidget(self.rb_periodo)
        mode_layout.addWidget(self.rb_all_day)

        self.mode_button_group = QButtonGroup(self)
        self.mode_button_group.addButton(self.rb_inicio, 1)
        self.mode_button_group.addButton(self.rb_periodo, 2)
        self.mode_button_group.addButton(self.rb_all_day, 3)
        self.mode_button_group.idClicked.connect(self._on_mode_changed)

        layout.addWidget(mode_groupbox)

        # 4. Controles de tiempo
        self.time_controls_box = QGroupBox("Horario")
        time_layout = QFormLayout(self.time_controls_box)

        time_display_fmt = "hh:mm ap" if self.time_format == '12h' else "HH:mm"

        # Start Time
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat(time_display_fmt)
        initial_start = self.working_hours.get('start', '08:00')
        if self.event_to_edit:
            initial_start = self.event_to_edit.get('start_time', initial_start)
        elif self.default_start_time:
            initial_start = self.default_start_time
            
        self.start_time_edit.setTime(QTime.fromString(initial_start, "HH:mm"))
        time_layout.addRow("Hora Inicio:", self.start_time_edit)

        # End Time
        self.end_time_edit = QTimeEdit()
        self.end_time_edit.setDisplayFormat(time_display_fmt)
        initial_end = self.working_hours.get('end', '17:00')
        if self.event_to_edit:
            initial_end = self.event_to_edit.get('end_time', initial_end)
        elif self.default_start_time:
            t = QTime.fromString(self.default_start_time, "HH:mm").addSecs(3600)
            initial_end = t.toString("HH:mm")
            
        self.end_time_edit.setTime(QTime.fromString(initial_end, "HH:mm"))
        time_layout.addRow("Hora Término:", self.end_time_edit)

        # Duration
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(5, 480)
        self.duration_spin.setValue(60)
        self.duration_spin.setSuffix(" min")
        time_layout.addRow("Duración:", self.duration_spin)

        layout.addWidget(self.time_controls_box)

        # Configurar modo inicial
        init_mode = 2
        if self.event_to_edit:
            init_mode = self.event_to_edit.get('mode_id', 2)
            if self.event_to_edit.get('all_day'):
                init_mode = 3
                
        if init_mode == 1:
            self.rb_inicio.setChecked(True)
        elif init_mode == 3:
            self.rb_all_day.setChecked(True)
        else:
            self.rb_periodo.setChecked(True)
            
        self._on_mode_changed(init_mode)

        # 5. Botones
        btn_layout = QHBoxLayout()
        
        if self.event_to_edit:
            btn_delete = QPushButton("Eliminar Evento")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold;")
            btn_delete.clicked.connect(self._delete_event)
            btn_layout.addWidget(btn_delete)
            
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Guardar Cambios" if self.event_to_edit else "Guardar Evento")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save_event)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete_event(self):
        self.is_delete = True
        self.accept()

    def _on_mode_changed(self, mode_id):
        if mode_id == 1: # Inicio (Hora inicio + duración)
            self.start_time_edit.setEnabled(True)
            self.end_time_edit.setEnabled(False)
            self.duration_spin.setEnabled(True)
        elif mode_id == 2: # Periodo (Hora inicio + término)
            self.start_time_edit.setEnabled(True)
            self.end_time_edit.setEnabled(True)
            self.duration_spin.setEnabled(False)
        elif mode_id == 3: # Todo el día
            self.start_time_edit.setEnabled(False)
            self.end_time_edit.setEnabled(False)
            self.duration_spin.setEnabled(False)

    def _save_event(self):
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setFocus()
            return

        mode_id = self.mode_button_group.checkedId()
        
        if mode_id == 3: # Todo el día
            start_str = self.working_hours.get('start', '08:00')
            end_str = self.working_hours.get('end', '17:00')
        elif mode_id == 1: # Inicio + Duración
            start_q = self.start_time_edit.time()
            start_str = start_q.toString("HH:mm")
            end_q = start_q.addSecs(self.duration_spin.value() * 60)
            end_str = end_q.toString("HH:mm")
        else: # Periodo
            start_str = self.start_time_edit.time().toString("HH:mm")
            end_str = self.end_time_edit.time().toString("HH:mm")

        self.event_data = {
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'title': title,
            'content': self.content_input.toPlainText().strip(),
            'mode_id': mode_id,
            'start_time': start_str,
            'end_time': end_str,
            'all_day': (mode_id == 3)
        }
        self.accept()


class CalendarSettingsDialog(QDialog):
    """Diálogo de configuración para ajustar la jornada laboral y formato de hora."""

    def __init__(self, current_working_hours: dict, current_time_format: str = '24h', current_day_right_mode: str = 'next_day', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Calendario")
        self.setMinimumWidth(350)
        self.working_hours = current_working_hours # {'start': '08:00', 'end': '17:00'}
        self.time_format = current_time_format # '24h' or '12h'
        self.day_right_mode = current_day_right_mode
        self.new_working_hours = None
        self.new_time_format = None
        self.new_day_right_mode = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 1. Jornada Laboral
        group_box = QGroupBox("Jornada Laboral")
        form = QFormLayout(group_box)

        time_display_fmt = "hh:mm ap" if self.time_format == '12h' else "HH:mm"

        self.start_edit = QTimeEdit()
        self.start_edit.setDisplayFormat(time_display_fmt)
        start_qtime = QTime.fromString(self.working_hours.get('start', '08:00'), "HH:mm")
        self.start_edit.setTime(start_qtime)
        form.addRow("Hora Inicio:", self.start_edit)

        self.end_edit = QTimeEdit()
        self.end_edit.setDisplayFormat(time_display_fmt)
        end_qtime = QTime.fromString(self.working_hours.get('end', '17:00'), "HH:mm")
        self.end_edit.setTime(end_qtime)
        form.addRow("Hora Término:", self.end_edit)

        layout.addWidget(group_box)

        # 2. Formato de Hora
        fmt_group = QGroupBox("Formato de Hora")
        fmt_layout = QVBoxLayout(fmt_group)

        self.rb_24h = QRadioButton("Formato 24 Horas (ej: 14:00)")
        self.rb_12h = QRadioButton("Formato 12 Horas AM/PM (ej: 02:00 PM)")

        if self.time_format == '12h':
            self.rb_12h.setChecked(True)
        else:
            self.rb_24h.setChecked(True)

        fmt_layout.addWidget(self.rb_24h)
        fmt_layout.addWidget(self.rb_12h)
        layout.addWidget(fmt_group)

        # 3. Vista página derecha (Día a la Vista)
        right_group = QGroupBox("Página derecha (Día a la Vista)")
        right_layout = QVBoxLayout(right_group)
        
        self.rb_next_day = QRadioButton("Día siguiente (Mostrar agenda del día de mañana)")
        self.rb_summary = QRadioButton("Resumen del día (Mostrar Tareas, Llamadas y Notas)")
        
        if self.day_right_mode == 'summary':
            self.rb_summary.setChecked(True)
        else:
            self.rb_next_day.setChecked(True)
            
        right_layout.addWidget(self.rb_next_day)
        right_layout.addWidget(self.rb_summary)
        layout.addWidget(right_group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _save(self):
        self.new_working_hours = {
            'start': self.start_edit.time().toString("HH:mm"),
            'end': self.end_edit.time().toString("HH:mm")
        }
        self.new_time_format = '12h' if self.rb_12h.isChecked() else '24h'
        self.new_day_right_mode = 'summary' if self.rb_summary.isChecked() else 'next_day'
        self.accept()
