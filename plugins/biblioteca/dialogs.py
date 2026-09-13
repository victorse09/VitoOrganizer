# =============================================================================
# Vito Organizer v2.2 - Biblioteca Dialogs
# Diálogos para gestión y asignación múltiple de documentos e imágenes
# =============================================================================

import os
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtWidgets import (
    QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QTextEdit, QPushButton, QComboBox, QCheckBox, QFileDialog,
    QFormLayout, QScrollArea, QFrame, QMessageBox
)


class DocumentDialog(QDialog):
    """Diálogo para agregar o editar un documento/imagen en la Biblioteca."""
    def __init__(self, item_to_edit: dict = None, lab_data: dict = None, parent=None):
        super().__init__(parent)
        self.item_to_edit = item_to_edit
        self.lab_data = lab_data or {} # {'components': [...], 'instruments': [...], 'tools': [...], 'supplies': [...]}
        self.item_data = None
        self.selected_file_path = None
        self.is_delete = False
        self.checkboxes = [] # List of (item_id, QCheckBox)

        self.setWindowTitle("Editar Documento / Imagen" if item_to_edit else "Subir Documento / Imagen a Biblioteca")
        self.setMinimumWidth(480)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ej: Resistencia 1/4W, Multímetro Fluke 117, Flux NC-559...")
        if self.item_to_edit: self.name_input.setText(self.item_to_edit.get('name', ''))
        form.addRow("Título / Nombre:", self.name_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "Imágenes",
            "Manuales",
            "Datasheets",
            "Libros",
            "Revistas",
            "Información Técnica",
            "Hojas de Seguridad",
            "Software / Firmware / Drivers",
            "Otros Documentos"
        ])
        if self.item_to_edit:
            edit_t = self.item_to_edit.get('type', '')
            # Normalizar para compatibilidad
            clean_t = edit_t.replace("🖼️ ", "").replace("📖 ", "").replace("⚡ ", "").replace("🧪 ", "").replace("📁 ", "").replace("📄 ", "").replace("💻 ", "")
            idx = self.type_combo.findText(clean_t)
            if idx < 0 and clean_t == 'Software':
                idx = self.type_combo.findText("Software / Firmware / Drivers")
            if idx >= 0: self.type_combo.setCurrentIndex(idx)
        form.addRow("Tipo de Archivo:", self.type_combo)

        # Seleccionar archivo físico
        file_layout = QHBoxLayout()
        self.lbl_file_path = QLineEdit()
        self.lbl_file_path.setReadOnly(True)
        self.lbl_file_path.setPlaceholderText("Selecciona un archivo del equipo...")
        if self.item_to_edit:
            self.lbl_file_path.setText(self.item_to_edit.get('filename', ''))

        btn_browse = QPushButton("Examinar...")
        btn_browse.clicked.connect(self._browse_file)
        file_layout.addWidget(self.lbl_file_path, 1)
        file_layout.addWidget(btn_browse)
        form.addRow("Archivo Físico:", file_layout)

        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "Componentes Electrónicos",
            "Instrumentos de Laboratorio",
            "Herramientas de Taller",
            "Insumos y Materiales",
            "Análisis y Pruebas",
            "Desarrollo y Proyectos"
        ])
        if self.item_to_edit:
            cat_map = {'components': 0, 'instruments': 1, 'tools': 2, 'supplies': 3, 'analysis': 4, 'projects': 5}
            c_idx = cat_map.get(self.item_to_edit.get('target_category', 'components'), 0)
            self.category_combo.setCurrentIndex(c_idx)
        self.category_combo.currentIndexChanged.connect(self._populate_elements)
        form.addRow("Categoría Destino:", self.category_combo)

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Descripción o notas del archivo...")
        self.desc_input.setMaximumHeight(60)
        if self.item_to_edit: self.desc_input.setText(self.item_to_edit.get('description', ''))
        form.addRow("Descripción:", self.desc_input)

        layout.addLayout(form)

        # Lista de Elementos asignables con Checkboxes
        lbl_assign = QLabel("<b>Asignar a Elementos (Marcar casillas):</b>")
        lbl_assign.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        layout.addWidget(lbl_assign)

        scroll_elements = QScrollArea()
        scroll_elements.setWidgetResizable(True)
        scroll_elements.setMaximumHeight(160)
        scroll_elements.setStyleSheet("QScrollArea { border: 1px solid #2d314e; background-color: #1e1e2e; border-radius: 4px; } QScrollArea QWidget { background-color: transparent; }")

        self.elements_container = QWidget()
        self.elements_layout = QVBoxLayout(self.elements_container)
        self.elements_layout.setContentsMargins(8, 8, 8, 8)
        self.elements_layout.setSpacing(4)
        scroll_elements.setWidget(self.elements_container)
        layout.addWidget(scroll_elements)

        self._populate_elements()

        btn_layout = QHBoxLayout()
        if self.item_to_edit:
            btn_delete = QPushButton("Eliminar de Biblioteca")
            btn_delete.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
            btn_delete.clicked.connect(self._delete)
            btn_layout.addWidget(btn_delete)

        btn_layout.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar en Biblioteca")
        btn_save.setObjectName("primaryButton")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save)

        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Seleccionar Archivo para Biblioteca", 
            "", 
            "Todos los Archivos (*.*);;Software, Firmware y Drivers (*.exe *.bin *.hex *.iso *.zip *.tar *.gz *.7z *.rar *.deb *.appimage *.py *.ino *.elf *.rom *.fw *.inf *.sys *.dll);;Documentos PDF (*.pdf);;Imágenes (*.png *.jpg *.jpeg *.gif *.webp *.avif *.bmp)"
        )
        if file_path:
            self.selected_file_path = file_path
            self.lbl_file_path.setText(os.path.basename(file_path))
            if not self.name_input.text():
                self.name_input.setText(os.path.splitext(os.path.basename(file_path))[0])

    def _populate_elements(self):
        while self.elements_layout.count():
            child = self.elements_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        
        self.checkboxes.clear()
        
        cat_index = self.category_combo.currentIndex()
        cat_keys = ['components', 'instruments', 'tools', 'supplies', 'analysis', 'projects']
        active_key = cat_keys[cat_index] if cat_index < len(cat_keys) else 'components'
        
        items_list = self.lab_data.get(active_key, [])
        assigned_ids = self.item_to_edit.get('assigned_element_ids', []) if self.item_to_edit else []

        if not items_list:
            lbl_none = QLabel("No hay elementos registrados en esta categoría.")
            lbl_none.setStyleSheet("color: #89b4fa; font-style: italic;")
            self.elements_layout.addWidget(lbl_none)
        else:
            for item in items_list:
                item_id = item.get('id') or item.get('name')
                detail_str = item.get('category', item.get('brand', item.get('type', 'Elemento')))
                chk = QCheckBox(f"{item.get('name')} ({detail_str})")
                chk.setStyleSheet("color: #cdd6f4; font-weight: bold;")
                if item_id in assigned_ids or item.get('name') in assigned_ids:
                    chk.setChecked(True)
                self.checkboxes.append((item_id, chk))
                self.elements_layout.addWidget(chk)
        
        self.elements_layout.addStretch()

    def _delete(self):
        self.is_delete = True
        self.accept()

    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            self.name_input.setFocus()
            return

        if not self.item_to_edit and not self.selected_file_path:
            QMessageBox.warning(self, "Archivo requerido", "Por favor selecciona un archivo físico del equipo.")
            return

        cat_keys = ['components', 'instruments', 'tools', 'supplies', 'analysis', 'projects']
        target_category = cat_keys[self.category_combo.currentIndex()] if self.category_combo.currentIndex() < len(cat_keys) else 'components'

        assigned_element_ids = [item_id for item_id, chk in self.checkboxes if chk.isChecked()]

        self.item_data = {
            'id': self.item_to_edit.get('id') if self.item_to_edit else f"doc_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'name': name,
            'type': self.type_combo.currentText(),
            'target_category': target_category,
            'description': self.desc_input.toPlainText().strip(),
            'assigned_element_ids': assigned_element_ids,
            'filename': self.item_to_edit.get('filename', '') if self.item_to_edit else '',
            'relative_path': self.item_to_edit.get('relative_path', '') if self.item_to_edit else ''
        }
        self.accept()


from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtCore import QByteArray
import re


def get_themed_svg_icon(icon_path: str, color_hex: str = "#0D47A1", size: int = 18) -> QIcon:
    """Carga un archivo SVG y colorea trazos/rellenos con color_hex."""
    if not os.path.exists(icon_path):
        return QIcon()
    try:
        from PyQt6.QtSvg import QSvgRenderer
        with open(icon_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'stroke="(?!none)[^"]+"', f'stroke="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'stroke:\s*(?!none)[^;"]+', f'stroke:{color_hex}', content, flags=re.IGNORECASE)
        content = re.sub(r'fill="(?!none)[^"]+"', f'fill="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'fill:\s*(?!none)[^;"]+', f'fill:{color_hex}', content, flags=re.IGNORECASE)

        renderer = QSvgRenderer(QByteArray(content.encode('utf-8')))
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return QIcon(pix)
    except Exception:
        return QIcon(icon_path)


class OpenDocChoiceDialog(QDialog):
    """Diálogo modal para preguntar si abrir con el visor integrado o con el del sistema."""
    def __init__(self, doc_name: str, parent=None):
        super().__init__(parent)
        self.choice = None # 'integrated' o 'system'
        self.remember = False
        self.setWindowTitle("Abrir Documento")
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E2E; color: #CDD6F4; }
            QLabel { color: #CDD6F4; font-size: 12px; }
            QPushButton { padding: 8px 14px; border-radius: 4px; font-weight: bold; font-size: 12px; }
            QCheckBox { color: #A6ADC8; font-size: 11px; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(18, 18, 18, 18)

        lbl = QLabel(f"¿Cómo deseas abrir el documento?<br><b>{doc_name}</b>")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        btn_box = QVBoxLayout()
        btn_box.setSpacing(8)
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        btn_viewer = QPushButton(" Abrir con Visor Integrado de VitoOrganizer")
        btn_viewer.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'manual.svg'), '#FFFFFF', 18))
        btn_viewer.setStyleSheet("background-color: #1E88E5; color: #FFFFFF; border: none; text-align: left; padding: 10px;")
        btn_viewer.clicked.connect(self._choose_integrated)
        btn_box.addWidget(btn_viewer)

        btn_sys = QPushButton(" Abrir con Visor Predeterminado del Sistema")
        btn_sys.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'open_folder.svg'), '#CDD6F4', 18))
        btn_sys.setStyleSheet("background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; text-align: left; padding: 10px;")
        btn_sys.clicked.connect(self._choose_system)
        btn_box.addWidget(btn_sys)
        layout.addLayout(btn_box)

        self.chk_remember = QCheckBox("Recordar mi elección para futuros documentos")
        layout.addWidget(self.chk_remember)

        btn_cancel = QPushButton(" Cancelar")
        btn_cancel.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'close.svg'), '#A6ADC8', 14))
        btn_cancel.setStyleSheet("background-color: transparent; color: #A6ADC8; border: none;")
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel, alignment=Qt.AlignmentFlag.AlignRight)

    def _choose_integrated(self):
        self.choice = 'integrated'
        self.remember = self.chk_remember.isChecked()
        self.accept()

    def _choose_system(self):
        self.choice = 'system'
        self.remember = self.chk_remember.isChecked()
        self.accept()


class LibrarySettingsDialog(QDialog):
    """Diálogo de configuración de la Biblioteca."""
    def __init__(self, plugin_data: dict = None, parent=None):
        super().__init__(parent)
        self.plugin_data = plugin_data or {}
        self.setWindowTitle("Configuración de Biblioteca")
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl = QLabel("<b>Gestor de Biblioteca y Documentación VitoOrganizer v2.3</b><br>Almacenamiento, lectura e indexación de libros, revistas y manuales.")
        lbl.setStyleSheet("color: #333333; font-size: 12px;")
        layout.addWidget(lbl)

        # 1. Comportamiento al abrir documentos
        open_box = QVBoxLayout()
        open_box.addWidget(QLabel("<b>Acción al abrir documentos PDF / EPUB:</b>"))
        self.open_action_combo = QComboBox()
        self.open_action_combo.addItems([
            "📖 Usar Visor Integrado de VitoOrganizer (Recomendado)",
            "🖥️ Usar Visor del Sistema Operativo",
            "❓ Preguntar siempre al abrir documento"
        ])
        open_action_map = {'integrated': 0, 'system': 1, 'ask': 2}
        cur_action = self.plugin_data.get('default_open_action', 'integrated')
        self.open_action_combo.setCurrentIndex(open_action_map.get(cur_action, 0))
        self.open_action_combo.currentIndexChanged.connect(self._on_open_action_changed)
        open_box.addWidget(self.open_action_combo)
        layout.addLayout(open_box)

        # 2. Opciones de visualización
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Orden de elementos por defecto:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            "Alfabético (A-Z)",
            "Alfabético (Z-A)",
            "Fecha de Ingreso (Más antiguos primero)",
            "Fecha de Ingreso (Más recientes primero)"
        ])
        
        sort_map = {'alpha_asc': 0, 'alpha_desc': 1, 'date_asc': 2, 'date_desc': 3}
        current_sort = self.plugin_data.get('sort_order', 'alpha_asc')
        self.sort_combo.setCurrentIndex(sort_map.get(current_sort, 0))
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        
        sort_layout.addWidget(self.sort_combo)
        layout.addLayout(sort_layout)

        # 3. Mostrar/Ocultar nombre de archivo
        self.chk_show_filename = QCheckBox("Mostrar nombre de archivo en la lista")
        self.chk_show_filename.setChecked(self.plugin_data.get('show_filename', True))
        self.chk_show_filename.stateChanged.connect(self._on_show_filename_changed)
        layout.addWidget(self.chk_show_filename)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Aceptar")
        btn_ok.setObjectName("primaryButton")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _on_open_action_changed(self):
        action_map_rev = {0: 'integrated', 1: 'system', 2: 'ask'}
        self.plugin_data['default_open_action'] = action_map_rev.get(self.open_action_combo.currentIndex(), 'integrated')

    def _on_sort_changed(self):
        sort_map_rev = {0: 'alpha_asc', 1: 'alpha_desc', 2: 'date_asc', 3: 'date_desc'}
        self.plugin_data['sort_order'] = sort_map_rev.get(self.sort_combo.currentIndex(), 'alpha_asc')

    def _on_show_filename_changed(self, state):
        self.plugin_data['show_filename'] = (state == 2)


