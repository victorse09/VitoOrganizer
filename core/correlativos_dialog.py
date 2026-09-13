from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QLineEdit, QCheckBox, QFormLayout
)
from PyQt6.QtCore import Qt, QDate

class CorrelativosDialog(QDialog):
    """Diálogo para gestionar los tipos de correlativos globales."""
    
    def __init__(self, manager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle('Control de Correlativos')
        self.setMinimumSize(450, 400)
        
        self._build_ui()
        self._refresh_list()
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        hdr = QLabel("Lista Global de Documentos y Secuencias")
        hdr.setStyleSheet("font-weight: bold; font-size: 14px; color: #cdd6f4;")
        layout.addWidget(hdr)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton('Nuevo')
        self.btn_add.setObjectName('primaryButton')
        self.btn_edit = QPushButton('Editar')
        self.btn_edit.setObjectName('secondaryButton')
        self.btn_reset = QPushButton('Reiniciar')
        self.btn_reset.setObjectName('dangerButton')
        self.btn_del = QPushButton('Eliminar')
        self.btn_del.setObjectName('dangerButton')
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_reset)
        btn_layout.addWidget(self.btn_del)
        layout.addLayout(btn_layout)
        
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_reset.clicked.connect(self._on_reset)
        self.btn_del.clicked.connect(self._on_delete)
        
    def _refresh_list(self):
        self.list_widget.clear()
        for t in self.manager.get_types():
            info = self.manager.get_type_info(t)
            _, _, sample = self.manager.get_next_serial_info(t)
            
            prefix = info.get('prefix', '')
            
            text = f"{t}  |  Prefijo: '{prefix}'  |  Siguiente: {sample}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, t)
            self.list_widget.addItem(item)
            
    def _on_add(self):
        dlg = _CorrelativoEditDialog(parent=self)
        if dlg.exec():
            name = dlg.name_edit.text().strip()
            if name:
                self.manager.add_or_update_type(name, dlg.prefix_edit.text().strip())
                self._refresh_list()
                
    def _on_edit(self):
        current = self.list_widget.currentItem()
        if not current:
            QMessageBox.information(self, 'Selección', 'Seleccione un elemento.')
            return
            
        name = current.data(Qt.ItemDataRole.UserRole)
        info = self.manager.get_type_info(name)
        
        dlg = _CorrelativoEditDialog(name, info.get('prefix', ''), parent=self)
        if dlg.exec():
            new_name = dlg.name_edit.text().strip()
            if new_name and new_name != name:
                # Rename means add new and copy old counts, then delete old
                old_counts = self.manager.types[name]["counts"]
                self.manager.add_or_update_type(new_name, dlg.prefix_edit.text().strip())
                self.manager.types[new_name]["counts"] = old_counts
                self.manager.delete_type(name)
            else:
                self.manager.add_or_update_type(name, dlg.prefix_edit.text().strip())
            self._refresh_list()
            
    def _on_reset(self):
        current = self.list_widget.currentItem()
        if not current: return
        name = current.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(self, 'Reiniciar', f'¿Seguro que desea reiniciar el contador de "{name}" a cero?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.reset_counters(name)
            self._refresh_list()
            
    def _on_delete(self):
        current = self.list_widget.currentItem()
        if not current: return
        name = current.data(Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(self, 'Eliminar', f'¿Seguro que desea eliminar el control para "{name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.manager.delete_type(name)
            self._refresh_list()

class _CorrelativoEditDialog(QDialog):
    def __init__(self, name="", prefix="", parent=None):
        super().__init__(parent)
        self.setWindowTitle('Editar Tipo de Documento')
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit(name)
        form.addRow("Nombre Documento:", self.name_edit)
        
        self.prefix_edit = QLineEdit(prefix)
        self.prefix_edit.setPlaceholderText("Ej: CHK-, FAC-")
        form.addRow("Prefijo (opcional):", self.prefix_edit)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName('primaryButton')
        btn_save.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
