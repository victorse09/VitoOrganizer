# =============================================================================
# Vito Organizer v2.2 - Planificador Dialogs
# Diálogos para proyectos, etapas, recursos y configuración
# =============================================================================

from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QDateEdit, QComboBox, QSpinBox,
    QFormLayout, QMessageBox
)


class ProjectDialog(QDialog):
    """Diálogo para crear o editar un Proyecto."""
    def __init__(self, project_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.project_to_edit = project_to_edit
        self.project_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Proyecto" if project_to_edit else "Nuevo Proyecto")
        self.setMinimumWidth(420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Nombre del proyecto...")
        if self.project_to_edit:
            self.title_input.setText(self.project_to_edit.get('title', ''))
        form.addRow("Proyecto:", self.title_input)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["En Planificación", "En Progreso", "En Pausa", "Completado"])
        if self.project_to_edit:
            idx = self.status_combo.findText(self.project_to_edit.get('status', 'En Progreso'))
            if idx >= 0: self.status_combo.setCurrentIndex(idx)
        form.addRow("Estado:", self.status_combo)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("dd/MM/yyyy")
        if self.project_to_edit and self.project_to_edit.get('start_date'):
            self.start_date.setDate(QDate.fromString(self.project_to_edit.get('start_date'), "yyyy-MM-dd"))
        else:
            self.start_date.setDate(QDate.currentDate())
        form.addRow("Fecha Inicio:", self.start_date)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("dd/MM/yyyy")
        if self.project_to_edit and self.project_to_edit.get('end_date'):
            self.end_date.setDate(QDate.fromString(self.project_to_edit.get('end_date'), "yyyy-MM-dd"))
        else:
            self.end_date.setDate(QDate.currentDate().addMonths(1))
        form.addRow("Fecha Término:", self.end_date)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripción y objetivos del proyecto...")
        self.desc_input.setMaximumHeight(80)
        if self.project_to_edit:
            self.desc_input.setText(self.project_to_edit.get('description', ''))
        form.addRow("Descripción:", self.desc_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.project_to_edit:
            btn_delete = QPushButton("Eliminar Proyecto")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Proyecto")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _delete(self):
        self.is_delete = True
        self.accept()

    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setFocus()
            return

        self.project_data = {
            'id': self.project_to_edit.get('id') if self.project_to_edit else f"proj_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'title': title,
            'status': self.status_combo.currentText(),
            'start_date': self.start_date.date().toString("yyyy-MM-dd"),
            'end_date': self.end_date.date().toString("yyyy-MM-dd"),
            'description': self.desc_input.toPlainText().strip()
        }
        self.accept()


class StageDialog(QDialog):
    """Diálogo para crear o editar una Etapa / Fase de un proyecto."""
    def __init__(self, stage_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.stage_to_edit = stage_to_edit
        self.stage_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Etapa" if stage_to_edit else "Nueva Etapa / Fase")
        self.setMinimumWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Fase 1: Análisis y Diseño...")
        if self.stage_to_edit:
            self.name_input.setText(self.stage_to_edit.get('name', ''))
        form.addRow("Nombre Etapa:", self.name_input)

        self.progress_spin = QSpinBox()
        self.progress_spin.setRange(0, 100)
        self.progress_spin.setSuffix(" %")
        if self.stage_to_edit:
            self.progress_spin.setValue(self.stage_to_edit.get('progress', 0))
        form.addRow("Progreso:", self.progress_spin)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.stage_to_edit:
            btn_delete = QPushButton("Eliminar Etapa")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Etapa")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
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

        self.stage_data = {
            'id': self.stage_to_edit.get('id') if self.stage_to_edit else f"stage_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'progress': self.progress_spin.value()
        }
        self.accept()


class ResourceDialog(QDialog):
    """Diálogo para crear o editar un Recurso (Persona, Equipo, Material)."""
    def __init__(self, resource_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.resource_to_edit = resource_to_edit
        self.resource_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Recurso" if resource_to_edit else "Nuevo Recurso / Integrante")
        self.setMinimumWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Juan Pérez, Servidor AWS, Impresora 3D...")
        if self.resource_to_edit:
            self.name_input.setText(self.resource_to_edit.get('name', ''))
        form.addRow("Nombre:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Persona / Integrante", "Equipo / Servidor", "Material / Herramienta"])
        if self.resource_to_edit:
            idx = self.type_combo.findText(self.resource_to_edit.get('type', 'Persona / Integrante'))
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Recurso:", self.type_combo)

        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("Ej: Desarrollador, Diseñador, Infraestructura...")
        if self.resource_to_edit:
            self.role_input.setText(self.resource_to_edit.get('role', ''))
        form.addRow("Rol / Función:", self.role_input)

        self.details_input = QLineEdit()
        self.details_input.setPlaceholderText("Contacto, email o detalles...")
        if self.resource_to_edit:
            self.details_input.setText(self.resource_to_edit.get('details', ''))
        form.addRow("Contacto / Detalle:", self.details_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.resource_to_edit:
            btn_delete = QPushButton("Eliminar Recurso")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Recurso")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
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

        self.resource_data = {
            'id': self.resource_to_edit.get('id') if self.resource_to_edit else f"res_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'role': self.role_input.text().strip(),
            'details': self.details_input.text().strip()
        }
        self.accept()


class PlannerSettingsDialog(QDialog):
    """Diálogo de configuración del Planificador."""
    def __init__(self, panoramic_mode: str = 'dual_page', parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Planificador")
        self.setMinimumWidth(420)
        self._panoramic_mode = panoramic_mode
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl = QLabel("<b>Gestor de Proyectos y Carta Gantt VitoOrganizer v2.3</b><br>Configuración general de cronogramas y equipos.")
        lbl.setStyleSheet("font-size: 12px;")
        layout.addWidget(lbl)

        # Grupo: Modo Panorámico
        from PyQt6.QtWidgets import QGroupBox, QRadioButton
        group_box = QGroupBox("Modo Panorámico de la Carta Gantt")
        group_layout = QVBoxLayout(group_box)
        group_layout.setSpacing(10)

        lbl_desc = QLabel("Selecciona cómo se presenta la Carta Gantt al activar el modo panorámico:")
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("font-size: 11px; font-weight: normal;")
        group_layout.addWidget(lbl_desc)

        self.rb_dual = QRadioButton("Ambas páginas con encuadernación")
        self.rb_dual.setToolTip("El diagrama Gantt se extiende sobre las dos páginas del libro,\ncon la encuadernación visible en el centro.")
        self.rb_dual.setStyleSheet("padding: 4px;")

        self.rb_single = QRadioButton("Página única sin encuadernación")
        self.rb_single.setToolTip("El diagrama Gantt se muestra en una sola hoja amplia,\nsin encuadernación ni división central — similar al Lotus Organizer.")
        self.rb_single.setStyleSheet("padding: 4px;")

        if self._panoramic_mode == 'single_page':
            self.rb_single.setChecked(True)
        else:
            self.rb_dual.setChecked(True)

        group_layout.addWidget(self.rb_dual)
        group_layout.addWidget(self.rb_single)
        layout.addWidget(group_box)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_accept)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _on_accept(self):
        if self.rb_single.isChecked():
            self._panoramic_mode = 'single_page'
        else:
            self._panoramic_mode = 'dual_page'
        self.accept()

    @property
    def panoramic_mode(self) -> str:
        """Retorna el modo panorámico seleccionado: 'dual_page' o 'single_page'."""
        return self._panoramic_mode

