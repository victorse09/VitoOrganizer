# =============================================================================
# Vito Organizer v2.2 - Notas Dialogs
# Diálogos para creación/edición de notas, cuadernos y enlaces
# =============================================================================

import os
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QComboBox, QFormLayout, QMessageBox, QColorDialog
)


class NoteDialog(QDialog):
    """Diálogo para crear una nueva nota o editar sus propiedades básicas."""
    def __init__(self, notebooks: list, selected_notebook_id: str = None, note_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.notebooks = notebooks
        self.note_to_edit = note_to_edit
        self.note_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Propiedades de Nota" if note_to_edit else "Nueva Nota")
        self.setMinimumWidth(420)
        self._setup_ui(selected_notebook_id)

    def _setup_ui(self, selected_notebook_id):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Título de la nota...")
        if self.note_to_edit:
            self.title_input.setText(self.note_to_edit.get('title', ''))
        form.addRow("Título:", self.title_input)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Combo para seleccionar Cuaderno / Lista
        self.notebook_combo = QComboBox()
        self.notebook_combo.addItem(QIcon(os.path.join(icons_dir, 'open_folder.svg')), "General (Sin Cuaderno)", None)
        
        selected_idx = 0
        for i, nb in enumerate(self.notebooks):
            self.notebook_combo.addItem(QIcon(os.path.join(icons_dir, 'manual.svg')), f"{nb.get('title')}", nb.get('id'))
            if self.note_to_edit and self.note_to_edit.get('notebook_id') == nb.get('id'):
                selected_idx = i + 1
            elif not self.note_to_edit and selected_notebook_id == nb.get('id'):
                selected_idx = i + 1
                
        self.notebook_combo.setCurrentIndex(selected_idx)
        form.addRow("Cuaderno / Grupo:", self.notebook_combo)

        # Tipo de Nota (Solo elegible al crear)
        self.type_combo = QComboBox()
        types = [
            ("Texto Plano", "text", "document.svg"),
            ("Documento Markdown", "markdown", "manual.svg"),
            ("Lista de Enlaces Web", "links", "link.svg"),
            ("Nota Gráfica (Imagen)", "image", "image_file.svg"),
            ("Nota a Mano Alzada", "handwriting", "pencil.svg")
        ]
        for label, val, icon_name in types:
            self.type_combo.addItem(QIcon(os.path.join(icons_dir, icon_name)), label, val)

        if self.note_to_edit:
            curr_type = self.note_to_edit.get('type', 'text')
            idx = self.type_combo.findData(curr_type)
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
            self.type_combo.setEnabled(False) # No cambiar tipo una vez creada
        form.addRow("Tipo de Nota:", self.type_combo)

        self.category_input = QLineEdit()
        self.category_input.setPlaceholderText("Ej: Ideas, Proyecto X, General...")
        if self.note_to_edit:
            self.category_input.setText(self.note_to_edit.get('category', ''))
        form.addRow("Categoría / Etiqueta:", self.category_input)

        layout.addLayout(form)

        # Botones
        btn_layout = QHBoxLayout()
        if self.note_to_edit:
            btn_delete = QPushButton("Eliminar Nota")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
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

        nb_id = self.notebook_combo.currentData()
        n_type = self.type_combo.currentData()
        now_str = QDate.currentDate().toString("dd/MM/yyyy")

        if self.note_to_edit:
            self.note_data = dict(self.note_to_edit)
            self.note_data['title'] = title
            self.note_data['notebook_id'] = nb_id
            self.note_data['category'] = self.category_input.text().strip()
            self.note_data['updated_at'] = now_str
        else:
            self.note_data = {
                'id': f"note_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
                'title': title,
                'notebook_id': nb_id,
                'type': n_type,
                'category': self.category_input.text().strip(),
                'created_at': now_str,
                'updated_at': now_str,
                'content': "" if n_type in ('text', 'markdown', 'image', 'handwriting') else []
            }
        self.accept()


class NotebookDialog(QDialog):
    """Diálogo para crear o editar un Cuaderno / Grupo de notas."""
    def __init__(self, notebook_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.notebook_to_edit = notebook_to_edit
        self.notebook_data = None
        self.is_delete = False
        self.selected_color = notebook_to_edit.get('color', '#4682B4') if notebook_to_edit else '#4682B4'

        self.setWindowTitle("Editar Cuaderno" if notebook_to_edit else "Nuevo Cuaderno")
        self.setMinimumWidth(360)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ej: Trabajo, Personal, Investigaciones...")
        if self.notebook_to_edit:
            self.title_input.setText(self.notebook_to_edit.get('title', ''))
        form.addRow("Nombre del Cuaderno:", self.title_input)

        # Selector de Color
        color_layout = QHBoxLayout()
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(40, 24)
        self._update_color_btn()
        self.btn_color.clicked.connect(self._pick_color)
        color_layout.addWidget(self.btn_color)
        color_layout.addStretch()
        form.addRow("Color distintivo:", color_layout)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.notebook_to_edit:
            btn_delete = QPushButton("Eliminar Cuaderno")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Cuaderno")
        btn_save.setObjectName("primaryButton")
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _update_color_btn(self):
        self.btn_color.setStyleSheet(f"background-color: {self.selected_color}; border: 1px solid #ffffff; border-radius: 4px;")

    def _pick_color(self):
        color = QColorDialog.getColor(initial=Qt.GlobalColor.blue, parent=self)
        if color.isValid():
            self.selected_color = color.name()
            self._update_color_btn()

    def _delete(self):
        self.is_delete = True
        self.accept()

    def _save(self):
        title = self.title_input.text().strip()
        if not title:
            self.title_input.setFocus()
            return

        self.notebook_data = {
            'id': self.notebook_to_edit.get('id') if self.notebook_to_edit else f"nb_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'title': title,
            'color': self.selected_color
        }
        self.accept()


class LinkDialog(QDialog):
    """Diálogo para agregar o editar un enlace web dentro de una nota de tipo Enlaces."""
    def __init__(self, link_to_edit: dict = None, categories: list = None, parent=None):
        super().__init__(parent)
        self.link_to_edit = link_to_edit
        self.categories = categories or []
        self.link_data = None
        self.is_delete = False

        self.setWindowTitle("Editar Enlace Web" if link_to_edit else "Nuevo Enlace Web")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Ej: Documentación PyQt6, GitHub Repo...")
        if self.link_to_edit:
            self.title_input.setText(self.link_to_edit.get('title', ''))
        form.addRow("Título del Enlace:", self.title_input)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://...")
        if self.link_to_edit:
            self.url_input.setText(self.link_to_edit.get('url', ''))
        form.addRow("URL:", self.url_input)

        self.cat_combo = QComboBox()
        self.cat_combo.setEditable(True)
        self.cat_combo.addItem("General")
        for c in self.categories:
            if c != "General" and self.cat_combo.findText(c) < 0:
                self.cat_combo.addItem(c)
        if self.link_to_edit:
            self.cat_combo.setEditText(self.link_to_edit.get('category', 'General'))
        form.addRow("Categoría:", self.cat_combo)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Descripción breve opcional...")
        if self.link_to_edit:
            self.desc_input.setText(self.link_to_edit.get('description', ''))
        form.addRow("Descripción:", self.desc_input)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        if self.link_to_edit:
            btn_delete = QPushButton("Eliminar Enlace")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar Enlace")
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
        url = self.url_input.text().strip()
        if not title:
            self.title_input.setFocus()
            return
        if not url:
            self.url_input.setFocus()
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        self.link_data = {
            'id': self.link_to_edit.get('id') if self.link_to_edit else f"link_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'title': title,
            'url': url,
            'category': self.cat_combo.currentText().strip() or "General",
            'description': self.desc_input.text().strip()
        }
        self.accept()


class NoteSettingsDialog(QDialog):
    """Diálogo de configuración del plugin de Notas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuración de Notas")
        self.setMinimumWidth(350)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl_info = QLabel("<b>Gestor de Notas VitoOrganizer v2.3</b><br>Configuración general de visualización y edición.")
        lbl_info.setStyleSheet("color: #333333; font-size: 12px;")
        layout.addWidget(lbl_info)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
