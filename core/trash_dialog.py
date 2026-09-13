# =============================================================================
# Vito Organizer v2.2 - Trash Dialog
# Ventana para gestionar elementos en la papelera de reciclaje
# =============================================================================

import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QListWidget, QListWidgetItem, QFrame, QMessageBox, QWidget
)


class TrashDialog(QDialog):
    """Diálogo para ver, restaurar y vaciar elementos de la papelera."""

    def __init__(self, plugin_manager, main_window=None):
        super().__init__(main_window)
        self.setWindowTitle("Papelera de Reciclaje")
        self.setMinimumSize(500, 400)
        self.plugin_manager = plugin_manager
        self.main_window = main_window

        self._setup_ui()
        self._load_trash_items()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title bar with custom styled TrashButton and label
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        from core.trash_widget import TrashButton
        self.title_icon = TrashButton(self)
        self.title_icon.setFixedSize(24, 24)
        
        # Determine trash style and if we have items
        if self.main_window and hasattr(self.main_window, 'settings'):
            self.title_icon.trash_style = getattr(self.main_window.settings.appearance, 'trash_style', 'classic_recycling')
        self.title_icon.has_items = self.plugin_manager.any_plugin_has_trash()
        self.title_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title_icon.setStyleSheet("background: transparent; border: none;")

        title_label = QLabel("Elementos en la Papelera")
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #f9e2af;")

        title_layout.addWidget(self.title_icon)
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #313244;
                padding: 8px;
            }
        """)
        layout.addWidget(self.list_widget)

        # Bottom Bar Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_empty = QPushButton("Vaciar Papelera")
        self.btn_empty.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 6px 12px;")
        self.btn_empty.clicked.connect(self._empty_trash)
        btn_layout.addWidget(self.btn_empty)

        btn_layout.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _load_trash_items(self):
        self.list_widget.clear()
        all_trash = []

        for plugin in self.plugin_manager.get_plugins():
            trash_items = plugin.get_trash_items()
            for idx, item in enumerate(trash_items):
                all_trash.append((plugin, idx, item))

        has_items = len(all_trash) > 0
        if hasattr(self, 'title_icon'):
            self.title_icon.has_items = has_items
            self.title_icon.update()

        if not all_trash:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            label = QLabel("La papelera está vacía")
            label.setStyleSheet("color: #a6adc8; font-style: italic;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item_layout.addWidget(label)
            
            list_item = QListWidgetItem(self.list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(list_item, item_widget)
            self.btn_empty.setEnabled(False)
            return

        self.btn_empty.setEnabled(True)

        for plugin, idx, item in all_trash:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 6, 8, 6)
            item_layout.setSpacing(10)

            title = item.get('title') or item.get('name') or 'Elemento borrado'
            date_str = item.get('date', '')
            info_text = f"<b>[{plugin.get_name()}]</b> {title}"
            if date_str:
                info_text += f" <span style='color: #a6adc8;'>({date_str})</span>"

            lbl_info = QLabel(info_text)
            lbl_info.setStyleSheet("color: #cdd6f4; font-size: 13px;")
            item_layout.addWidget(lbl_info, 1)

            # Botón Restaurar
            btn_restore = QPushButton("Restaurar")
            btn_restore.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_restore.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; min-height: 28px; padding: 4px 14px; border-radius: 4px; } QPushButton:hover { background-color: #94e28f; }")
            btn_restore.clicked.connect(lambda checked, p=plugin, i=idx: self._restore_item(p, i))
            item_layout.addWidget(btn_restore)

            # Botón Eliminar para siempre
            btn_delete = QPushButton("Borrar para siempre")
            btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_delete.setStyleSheet("QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; min-height: 28px; padding: 4px 14px; border-radius: 4px; } QPushButton:hover { background-color: #e78284; }")
            btn_delete.clicked.connect(lambda checked, p=plugin, i=idx: self._delete_permanently(p, i))
            item_layout.addWidget(btn_delete)

            list_item = QListWidgetItem(self.list_widget)
            from PyQt6.QtCore import QSize
            list_item.setSizeHint(QSize(0, 60))
            self.list_widget.setItemWidget(list_item, item_widget)

    def _restore_item(self, plugin, index):
        if hasattr(plugin, 'restore_item'):
            plugin.restore_item(index)
        else:
            plugin.restore_from_trash(index)
            
        if self.main_window:
            self.main_window.agenda_manager.is_modified = True
            has_trash = self.plugin_manager.any_plugin_has_trash()
            self.main_window.sidebar.trash_widget.set_has_items(has_trash)
            
        self._load_trash_items()

    def _delete_permanently(self, plugin, index):
        reply = QMessageBox.question(
            self, "Eliminar para siempre",
            "¿Estás seguro de que deseas eliminar este elemento para siempre?\nEsta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if 0 <= index < len(plugin._trash):
                plugin._trash.pop(index)
                if self.main_window:
                    self.main_window.agenda_manager.is_modified = True
                    has_trash = self.plugin_manager.any_plugin_has_trash()
                    self.main_window.sidebar.trash_widget.set_has_items(has_trash)
            self._load_trash_items()

    def _empty_trash(self):
        reply = QMessageBox.question(
            self, "Vaciar Papelera",
            "¿Estás seguro de que deseas vaciar toda la papelera?\nTodos los elementos se eliminarán para siempre.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for plugin in self.plugin_manager.get_plugins():
                plugin.empty_trash()
            if self.main_window:
                self.main_window.agenda_manager.is_modified = True
                has_trash = self.plugin_manager.any_plugin_has_trash()
                self.main_window.sidebar.trash_widget.set_has_items(has_trash)
            self._load_trash_items()
