# =============================================================================
# Vito Organizer v2.2 - Cumpleaños, Aniversarios y Feriados Dialogs
# =============================================================================

import json
import urllib.request
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QDateEdit, QSpinBox, QComboBox, 
    QGroupBox, QFormLayout, QMessageBox
)

class BirthdayDialog(QDialog):
    """Diálogo para agregar o editar un evento de Cumpleaños."""
    def __init__(self, selected_date: QDate = None, event_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.event_to_edit = event_to_edit
        self.event_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Cumpleaños" if event_to_edit else "Nuevo Cumpleaños")
        self.setMinimumWidth(380)
        self._setup_ui(selected_date or QDate.currentDate())

    def _setup_ui(self, initial_date):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        if self.event_to_edit:
            self.date_edit.setDate(QDate.fromString(self.event_to_edit.get('date'), "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(initial_date)
        form.addRow("Fecha:", self.date_edit)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del cumpleañero/a")
        if self.event_to_edit:
            self.name_input.setText(self.event_to_edit.get('name', ''))
        form.addRow("Nombre:", self.name_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionales...")
        self.notes_input.setMaximumHeight(70)
        if self.event_to_edit:
            self.notes_input.setText(self.event_to_edit.get('notes', ''))
        form.addRow("Nota:", self.notes_input)

        self.age_spin = QSpinBox()
        self.age_spin.setRange(0, 120)
        self.age_spin.setValue(self.event_to_edit.get('age', 0) if self.event_to_edit else 0)
        self.age_spin.setSuffix(" años")
        form.addRow("Edad:", self.age_spin)

        self.gift_input = QLineEdit()
        self.gift_input.setPlaceholderText("Idea de regalo...")
        if self.event_to_edit:
            self.gift_input.setText(self.event_to_edit.get('gift', ''))
        form.addRow("Regalo posible:", self.gift_input)

        layout.addLayout(form)

        # Botones
        btn_layout = QHBoxLayout()
        if self.event_to_edit:
            btn_delete = QPushButton("Eliminar")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        self.is_delete = True
        self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        self.event_data = {
            'type': 'birthday',
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'name': name,
            'notes': self.notes_input.toPlainText().strip(),
            'age': self.age_spin.value(),
            'gift': self.gift_input.text().strip()
        }
        self.accept()


class AnniversaryDialog(QDialog):
    """Diálogo para agregar o editar un evento de Aniversario."""
    def __init__(self, selected_date: QDate = None, event_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.event_to_edit = event_to_edit
        self.event_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Aniversario" if event_to_edit else "Nuevo Aniversario")
        self.setMinimumWidth(380)
        self._setup_ui(selected_date or QDate.currentDate())

    def _setup_ui(self, initial_date):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        if self.event_to_edit:
            self.date_edit.setDate(QDate.fromString(self.event_to_edit.get('date'), "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(initial_date)
        form.addRow("Fecha:", self.date_edit)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del aniversario (ej: Matrimonio, Empresa)")
        if self.event_to_edit:
            self.name_input.setText(self.event_to_edit.get('name', ''))
        form.addRow("Nombre:", self.name_input)

        self.motive_input = QLineEdit()
        self.motive_input.setPlaceholderText("Motivo del aniversario...")
        if self.event_to_edit:
            self.motive_input.setText(self.event_to_edit.get('motive', ''))
        form.addRow("Motivo:", self.motive_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Texto o comentario...")
        self.notes_input.setMaximumHeight(70)
        if self.event_to_edit:
            self.notes_input.setText(self.event_to_edit.get('notes', ''))
        form.addRow("Comentario:", self.notes_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.event_to_edit:
            btn_delete = QPushButton("Eliminar")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        self.is_delete = True
        self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        self.event_data = {
            'type': 'anniversary',
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'name': name,
            'motive': self.motive_input.text().strip(),
            'notes': self.notes_input.toPlainText().strip()
        }
        self.accept()


class HolidayDialog(QDialog):
    """Diálogo para agregar o editar un Feriado."""
    def __init__(self, selected_date: QDate = None, event_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.event_to_edit = event_to_edit
        self.event_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Feriado" if event_to_edit else "Nuevo Feriado")
        self.setMinimumWidth(380)
        self._setup_ui(selected_date or QDate.currentDate())

    def _setup_ui(self, initial_date):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        if self.event_to_edit:
            self.date_edit.setDate(QDate.fromString(self.event_to_edit.get('date'), "yyyy-MM-dd"))
        else:
            self.date_edit.setDate(initial_date)
        form.addRow("Fecha:", self.date_edit)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nombre del feriado")
        if self.event_to_edit:
            self.name_input.setText(self.event_to_edit.get('name', ''))
        form.addRow("Nombre Feriado:", self.name_input)

        self.motive_input = QLineEdit()
        self.motive_input.setPlaceholderText("Motivo / Conmemoración")
        if self.event_to_edit:
            self.motive_input.setText(self.event_to_edit.get('motive', ''))
        form.addRow("Motivo:", self.motive_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Civil", "Religioso"])
        if self.event_to_edit:
            htype = self.event_to_edit.get('holiday_type', 'Civil')
            idx = self.type_combo.findText(htype)
            if idx >= 0:
                self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo:", self.type_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.event_to_edit:
            btn_delete = QPushButton("Eliminar")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        self.is_delete = True
        self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return
        self.event_data = {
            'type': 'holiday',
            'date': self.date_edit.date().toString("yyyy-MM-dd"),
            'name': name,
            'motive': self.motive_input.text().strip(),
            'holiday_type': self.type_combo.currentText()
        }
        self.accept()


class CumpleanosSettingsDialog(QDialog):
    """Diálogo de configuración de la sección Cumpleaños (Importación de feriados)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Cumpleaños y Feriados")
        self.setMinimumWidth(420)
        self.imported_holidays = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        group = QGroupBox("Importación de Feriados de Chile")
        g_layout = QVBoxLayout(group)
        g_layout.setSpacing(10)

        desc = QLabel(
            "Puedes sincronizar la base de datos de feriados de Chile en línea "
            "desde el repositorio de GitHub:\nhttps://github.com/squirogar/FeriadosChile"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #a0a5c0; font-size: 12px;")
        g_layout.addWidget(desc)

        self.btn_import = QPushButton("Actualizar Feriados de Chile (GitHub)")
        self.btn_import.setObjectName("primaryButton")
        self.btn_import.clicked.connect(self._import_holidays)
        g_layout.addWidget(self.btn_import)

        self.lbl_status = QLabel("")
        self.lbl_status.setWordWrap(True)
        self.lbl_status.setStyleSheet("color: #a6da95; font-weight: bold;")
        g_layout.addWidget(self.lbl_status)

        layout.addWidget(group)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _import_holidays(self):
        self.lbl_status.setText("Conectando con GitHub...")
        self.lbl_status.setStyleSheet("color: #eed49f;")
        self.btn_import.setEnabled(False)
        
        # Intentar descargar feriados desde la API pública o JSON raw de GitHub
        urls = [
            "https://apis.digital.gob.cl/fl/feriados",
            "https://raw.githubusercontent.com/squirogar/FeriadosChile/main/feriados.json",
            "https://raw.githubusercontent.com/squirogar/FeriadosChile/master/feriados.json"
        ]
        
        fetched_events = []
        success = False
        
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        # Parse data depending on API format
                        if isinstance(data, list):
                            for item in data:
                                # digital.gob.cl format
                                date_str = item.get('fecha')
                                name_str = item.get('nombre')
                                htype = item.get('tipo', 'Civil')
                                if date_str and name_str:
                                    fetched_events.append({
                                        'type': 'holiday',
                                        'date': date_str,
                                        'name': name_str,
                                        'motive': item.get('comentarios', 'Feriado Oficial'),
                                        'holiday_type': 'Religioso' if 'religioso' in str(htype).lower() else 'Civil'
                                    })
                            if fetched_events:
                                success = True
                                break
            except Exception as e:
                continue

        # Fallback si falla la conexión a internet
        if not success or not fetched_events:
            year = QDate.currentDate().year()
            fetched_events = [
                {'type': 'holiday', 'date': f'{year}-01-01', 'name': 'Año Nuevo', 'motive': 'Feriado Civil', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-04-18', 'name': 'Viernes Santo', 'motive': 'Semana Santa', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-04-19', 'name': 'Sábado Santo', 'motive': 'Semana Santa', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-05-01', 'name': 'Día del Trabajo', 'motive': 'Feriado Internacional', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-05-21', 'name': 'Día de las Glorias Navales', 'motive': 'Combate Naval de Iquique', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-06-20', 'name': 'Día Nacional de los Pueblos Indígenas', 'motive': 'Solsticio de Invierno', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-06-29', 'name': 'San Pedro y San Pablo', 'motive': 'Feriado Religioso', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-07-16', 'name': 'Día de la Virgen del Carmen', 'motive': 'Patrona de Chile', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-08-15', 'name': 'Asunción de la Virgen', 'motive': 'Feriado Religioso', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-09-18', 'name': 'Día de la Independencia Nacional', 'motive': 'Fiestas Patrias', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-09-19', 'name': 'Día de las Glorias del Ejército', 'motive': 'Fiestas Patrias', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-10-12', 'name': 'Encuentro de Dos Mundos', 'motive': 'Día de la Raza', 'holiday_type': 'Civil'},
                {'type': 'holiday', 'date': f'{year}-10-31', 'name': 'Día de las Iglesias Evangélicas', 'motive': 'Feriado Religioso', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-11-01', 'name': 'Día de Todos los Santos', 'motive': 'Feriado Religioso', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-12-08', 'name': 'Inmaculada Concepción', 'motive': 'Feriado Religioso', 'holiday_type': 'Religioso'},
                {'type': 'holiday', 'date': f'{year}-12-25', 'name': 'Navidad', 'motive': 'Nacimiento de Jesús', 'holiday_type': 'Religioso'}
            ]
            self.lbl_status.setText(f"Se sincronizaron {len(fetched_events)} feriados locales de Chile.")
        else:
            self.lbl_status.setText(f"¡Éxito! Se importaron {len(fetched_events)} feriados desde GitHub.")

        self.lbl_status.setStyleSheet("color: #a6da95; font-weight: bold;")
        self.imported_holidays = fetched_events
        self.btn_import.setEnabled(True)
