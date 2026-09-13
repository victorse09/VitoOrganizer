# =============================================================================
# Vito Organizer v2.2 - Tareas Dialogs
# =============================================================================

import os
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QDateEdit, QComboBox, QCheckBox,
    QFormLayout, QMessageBox
)


class TaskDialog(QDialog):
    """Diálogo para crear o editar una tarea."""
    def __init__(self, lists: list, selected_list_id: str = None, task_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.lists = lists
        self.task_to_edit = task_to_edit
        self.task_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Tarea" if task_to_edit else "Nueva Tarea")
        self.setMinimumWidth(400)
        self._setup_ui(selected_list_id)

    def _setup_ui(self, selected_list_id):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la tarea...")
        if self.task_to_edit:
            self.title_input.setText(self.task_to_edit.get('title', ''))
        form.addRow("Tarea:", self.title_input)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Combo para seleccionar lista a la que pertenece
        self.list_combo = QComboBox()
        self.list_combo.addItem(QIcon(os.path.join(icons_dir, 'pushpin.svg')), "Ninguna (Tarea Suelta)", None)
        
        selected_idx = 0
        for i, l in enumerate(self.lists):
            self.list_combo.addItem(QIcon(os.path.join(icons_dir, 'open_folder.svg')), f"{l.get('title')}", l.get('id'))
            if self.task_to_edit and self.task_to_edit.get('list_id') == l.get('id'):
                selected_idx = i + 1
            elif not self.task_to_edit and selected_list_id == l.get('id'):
                selected_idx = i + 1
                
        self.list_combo.setCurrentIndex(selected_idx)
        form.addRow("Lista / Proyecto:", self.list_combo)

        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Baja", "Media", "Alta"])
        if self.task_to_edit:
            prio = self.task_to_edit.get('priority', 'Media')
            idx = self.priority_combo.findText(prio)
            if idx >= 0: self.priority_combo.setCurrentIndex(idx)
        else:
            self.priority_combo.setCurrentIndex(1) # Media por defecto
        form.addRow("Prioridad:", self.priority_combo)

        self.has_date_check = QCheckBox("Con fecha límite")
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        
        has_due = True
        if self.task_to_edit:
            has_due = self.task_to_edit.get('has_due_date', bool(self.task_to_edit.get('due_date')))
            if self.task_to_edit.get('due_date'):
                self.date_edit.setDate(QDate.fromString(self.task_to_edit.get('due_date'), "yyyy-MM-dd"))
            else:
                self.date_edit.setDate(QDate.currentDate())
        else:
            self.date_edit.setDate(QDate.currentDate())
            
        self.has_date_check.setChecked(has_due)
        self.date_edit.setEnabled(has_due)
        self.has_date_check.toggled.connect(self.date_edit.setEnabled)
        
        date_box = QHBoxLayout()
        date_box.addWidget(self.has_date_check)
        date_box.addWidget(self.date_edit, 1)
        form.addRow("Fecha límite:", date_box)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripción detallada o notas...")
        self.desc_input.setMaximumHeight(80)
        if self.task_to_edit:
            self.desc_input.setText(self.task_to_edit.get('description', ''))
        form.addRow("Descripción:", self.desc_input)

        layout.addLayout(form)

        # Botones
        btn_layout = QHBoxLayout()
        if self.task_to_edit:
            btn_delete = QPushButton("Eliminar Tarea")
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
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setFocus()
            return

        list_id = self.list_combo.currentData()
        has_due = self.has_date_check.isChecked()
        self.task_data = {
            'id': self.task_to_edit.get('id') if self.task_to_edit else f"task_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'list_id': list_id,
            'title': title,
            'description': self.desc_input.toPlainText().strip(),
            'priority': self.priority_combo.currentText(),
            'has_due_date': has_due,
            'due_date': self.date_edit.date().toString("yyyy-MM-dd") if has_due else "",
            'completed': self.task_to_edit.get('completed', False) if self.task_to_edit else False,
            'completed_date': self.task_to_edit.get('completed_date', '') if self.task_to_edit else ''
        }
        self.accept()


class TaskListDialog(QDialog):
    """Diálogo para crear o editar una Lista de Tareas."""
    def __init__(self, list_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.list_to_edit = list_to_edit
        self.list_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Lista de Tareas" if list_to_edit else "Nueva Lista de Tareas")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ej: Compras del Supermercado, Proyecto X...")
        if self.list_to_edit:
            self.title_input.setText(self.list_to_edit.get('title', ''))
        form.addRow("Nombre de la Lista:", self.title_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.list_to_edit:
            btn_delete = QPushButton("Eliminar Lista")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Lista")
        btn_save.setObjectName("primaryButton")
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

        self.list_data = {
            'id': self.list_to_edit.get('id') if self.list_to_edit else f"list_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'title': title,
            'collapsed': self.list_to_edit.get('collapsed', False) if self.list_to_edit else False
        }
        self.accept()


class TaskSettingsDialog(QDialog):
    """Diálogo de configuración del plugin de Tareas."""
    def __init__(self, stats_in_sidebar: bool = False, parent=None):
        super().__init__(parent)
        self.stats_in_sidebar = stats_in_sidebar
        self.setWindowTitle("Configuración de Tareas")
        self.setMinimumWidth(380)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.stats_combo = QComboBox()
        self.stats_combo.addItem(QIcon(os.path.join(icons_dir, 'chart.svg')), "Página Derecha (Estadísticas)", False)
        self.stats_combo.addItem(QIcon(os.path.join(icons_dir, 'sidebar_toggle.svg')), "Barra Lateral (Libera Página Derecha)", True)
        self.stats_combo.setCurrentIndex(1 if self.stats_in_sidebar else 0)
        form.addRow("Ubicación de Estadísticas:", self.stats_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Configuración")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _save(self):
        self.stats_in_sidebar = self.stats_combo.currentData()
        self.accept()
