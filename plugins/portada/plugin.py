# =============================================================================
# Vito Organizer v2.2 - Portada Plugin
# Sección de portada de la agenda
# =============================================================================

import os
import shutil
from typing import Dict, Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QFileDialog, QFrame, QHBoxLayout, QSizePolicy
)

from plugins.plugin_base import PluginBase, load_image_pixmap, IMAGE_EXTENSIONS, IMAGE_FILE_FILTER
from data.data_store import DataStore
from graphics.textures import Textures


class PortadaSidebar(QWidget):
    """Widget de la barra lateral para la Portada."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_path = ""
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Logotipo (si está configurado)
        self.lbl_logo = QLabel()
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setStyleSheet("background: transparent; border: none; padding-bottom: 5px;")
        self.lbl_logo.setVisible(False)
        layout.addWidget(self.lbl_logo)

        # Título
        title_label = QLabel("Información de Agenda")
        title_label.setStyleSheet("color: #E0E0E0; font-weight: bold; font-size: 14px; background: transparent;")
        layout.addWidget(title_label)

        # Nombre de agenda
        self.name_label = QLabel("Nombre: -")
        self.name_label.setStyleSheet("color: #D0D0D0; background: transparent;")
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)

        # Ruta
        self.path_label = QLabel("Ruta: -")
        self.path_label.setStyleSheet("color: #A0A0A0; font-size: 11px; background: transparent;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        # Tamaño en disco
        self.size_label = QLabel("Tamaño de agenda: -")
        self.size_label.setStyleSheet("color: #D0D0D0; background: transparent;")
        layout.addWidget(self.size_label)

        # Espacio disponible en disco
        self.free_label = QLabel("Espacio libre en disco: -")
        self.free_label.setStyleSheet("color: #D0D0D0; background: transparent;")
        layout.addWidget(self.free_label)

        # Botón para ver gráfico de contenido
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.btn_chart = QPushButton(" Ver Gráfico de Contenido")
        self.btn_chart.setIcon(QIcon(os.path.join(icons_dir, 'chart.svg')))
        self.btn_chart.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chart.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 12px;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.btn_chart.clicked.connect(self._on_show_chart)
        layout.addWidget(self.btn_chart)

        layout.addStretch()

    def _get_disk_info(self, path: str):
        if not path or path == "-":
            return "-", "-"
        
        # 1. Espacio que ocupa la agenda
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        total_size += os.path.getsize(fp)
            
            if total_size >= 1024 * 1024:
                agenda_space = f"{total_size / (1024 * 1024):.2f} MB"
            else:
                agenda_space = f"{total_size / 1024:.2f} KB"
        except Exception:
            agenda_space = "Error"

        # 2. Espacio disponible en la unidad
        try:
            total, used, free = shutil.disk_usage(path)
            if free >= 1024 * 1024 * 1024:
                free_space = f"{free / (1024 * 1024 * 1024):.2f} GB"
            else:
                free_space = f"{free / (1024 * 1024):.2f} MB"
        except Exception:
            free_space = "Error"

        return agenda_space, free_space

    def _on_show_chart(self):
        if not self.current_path or not os.path.exists(self.current_path) or self.current_path == "-":
            return
        
        agenda_path = self.current_path
        agenda_name = os.path.basename(agenda_path) or "Agenda"

        root_items = []
        total_size = 0
        total_files = 0
        total_folders = 0

        try:
            for entry in os.scandir(agenda_path):
                size = 0
                is_dir = False
                try:
                    if entry.is_dir(follow_symlinks=False):
                        is_dir = True
                        total_folders += 1
                        for root, dirs, files in os.walk(entry.path):
                            total_folders += len(dirs)
                            total_files += len(files)
                            for f in files:
                                try:
                                    size += os.path.getsize(os.path.join(root, f))
                                except (OSError, PermissionError):
                                    pass
                    elif entry.is_file(follow_symlinks=False):
                        total_files += 1
                        size = entry.stat().st_size
                    
                    total_size += size
                    root_items.append({'name': entry.name, 'size': size, 'is_dir': is_dir})
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            pass

        root_items.sort(key=lambda x: x['size'], reverse=True)

        item = {
            'name': f"Agenda: {agenda_name}",
            'storage_stats': {
                'total_bytes': total_size,
                'used_bytes': total_size,
                'free_bytes': 0,
                'total_files': total_files,
                'total_folders': total_folders,
                'root_items': root_items,
                'scanned_path': agenda_path,
                'include_files': True
            }
        }

        from plugins.respaldos.dialogs import DiskUsageChartDialog
        dlg = DiskUsageChartDialog(self, item=item)
        dlg.exec()

    def update_info(self, name: str, path: str):
        self.current_path = path
        self.name_label.setText(f"Nombre: {name}")
        self.path_label.setText(f"Ruta: {path}")
        agenda_space, free_space = self._get_disk_info(path)
        self.size_label.setText(f"Tamaño de agenda: {agenda_space}")
        self.free_label.setText(f"Espacio libre en disco: {free_space}")
        self.btn_chart.setEnabled(bool(path and path != "-" and os.path.exists(path)))

        # Cargar logotipo desde la configuración general o desde la carpeta de la agenda
        from config.settings import Settings
        settings = Settings.load()
        logo_path = getattr(settings.general, 'logo_path', '')

        # Buscar en la carpeta de portada de la agenda si logo_path no está configurado o no existe en este equipo
        if not logo_path or not os.path.exists(logo_path):
            if path and os.path.exists(path):
                portada_dir = os.path.join(path, 'portada')
                if os.path.exists(portada_dir):
                    for f in os.listdir(portada_dir):
                        if f.startswith('custom_logo') and f.lower().endswith(IMAGE_EXTENSIONS):
                            potential = os.path.join(portada_dir, f)
                            if os.path.exists(potential):
                                logo_path = potential
                                settings.general.logo_path = logo_path
                                try:
                                    settings.save()
                                except Exception:
                                    pass
                                break

        if logo_path and os.path.exists(logo_path):
            pixmap = load_image_pixmap(logo_path)
            if not pixmap.isNull():
                scaled = pixmap.scaled(150, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.lbl_logo.setPixmap(scaled)
                self.lbl_logo.setVisible(True)
            else:
                self.lbl_logo.setVisible(False)
        else:
            self.lbl_logo.setVisible(False)


class ResizableImageLabel(QLabel):
    """QLabel que escala su imagen automáticamente al cambiar de tamaño."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_pixmap = None
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def setPixmap(self, pixmap: QPixmap):
        self.original_pixmap = pixmap
        if pixmap and not pixmap.isNull():
            w = max(self.width(), 1)
            h = max(self.height(), 1)
            scaled = pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)
        else:
            super().setPixmap(pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.original_pixmap and not self.original_pixmap.isNull():
            w = max(self.width(), 1)
            h = max(self.height(), 1)
            scaled = self.original_pixmap.scaled(
                w, h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            super().setPixmap(scaled)

    def clear(self):
        self.original_pixmap = None
        super().clear()


class PortadaCoverWidget(QWidget):
    """Widget que representa la tapa frontal (página derecha)."""

    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName('transparentPage')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 60, 40, 60)
        layout.setSpacing(20)

        # Título (editable)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Título de la Agenda")
        font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        self.title_edit.setFont(font)
        self.title_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                border-bottom: 2px dashed #8B7355;
                color: #2a1a0a;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #336699;
            }
        """)
        self.title_edit.textChanged.connect(self._on_title_changed)
        layout.addWidget(self.title_edit)

        # Subtítulo (editable)
        self.subtitle_edit = QLineEdit()
        self.subtitle_edit.setPlaceholderText("Subtítulo o descripción corta")
        sub_font = QFont("Segoe UI", 14)
        sub_font.setItalic(True)
        self.subtitle_edit.setFont(sub_font)
        self.subtitle_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_edit.setStyleSheet(self.title_edit.styleSheet())
        self.subtitle_edit.textChanged.connect(self._on_subtitle_changed)
        layout.addWidget(self.subtitle_edit)

        layout.addStretch(1)

        # Imagen de portada
        self.image_label = ResizableImageLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumSize(200, 200)
        self.image_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #8B7355;
                border-radius: 8px;
                background-color: rgba(255, 255, 240, 0.5);
            }
        """)
        
        # Botón para cambiar imagen
        self.btn_change_image = QPushButton("Seleccionar Imagen...")
        self.btn_change_image.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_change_image.clicked.connect(self._select_image)

        img_layout = QVBoxLayout()
        img_layout.addWidget(self.image_label, 1)
        img_layout.addWidget(self.btn_change_image, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addLayout(img_layout, 3)

        layout.addStretch(2)

    def paintEvent(self, event):
        """Dibuja una textura de cuero para la portada."""
        from PyQt6.QtGui import QPainter, QPainterPath
        from PyQt6.QtCore import QRectF
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        
        # Redondear esquinas
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 8, 8)
        painter.setClipPath(path)
        
        Textures.draw_leather_texture(painter, QRectF(self.rect()), base_color="#34495e")

    def _on_title_changed(self, text):
        self.plugin.get_data()['title'] = text
        self.plugin.mark_modified()

    def _on_subtitle_changed(self, text):
        self.plugin.get_data()['subtitle'] = text
        self.plugin.mark_modified()

    def _select_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Imagen de Portada", "", 
            IMAGE_FILE_FILTER
        )
        if path:
            agenda_path = self.plugin.get_agenda_path()
            if agenda_path:
                # Copiar imagen a la carpeta del plugin
                plugin_dir = os.path.join(agenda_path, 'portada')
                ext = os.path.splitext(path)[1]
                dest_name = f"cover_image{ext}"
                dest_path = os.path.join(plugin_dir, dest_name)
                
                shutil.copy2(path, dest_path)
                
                self.plugin.get_data()['image_file'] = dest_name
                self.plugin.mark_modified()
                self.plugin.save_data(agenda_path)
                self.load_image(dest_path)

    def load_image(self, image_path: str):
        if os.path.exists(image_path):
            pixmap = load_image_pixmap(image_path)
            self.image_label.setPixmap(pixmap)
            self.image_label.setStyleSheet("border: none; background: transparent;")
            self.btn_change_image.setText("Cambiar Imagen...")
        else:
            self.image_label.clear()
            self.image_label.setText("Sin Imagen")
            self.image_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #8B7355;
                    border-radius: 8px;
                    color: #2a1a0a;
                    background-color: rgba(255, 255, 240, 0.5);
                }
            """)
            self.btn_change_image.setText("Seleccionar Imagen...")

    def update_from_data(self, data: Dict[str, Any]):
        """Actualiza la UI desde los datos."""
        self.title_edit.blockSignals(True)
        self.subtitle_edit.blockSignals(True)
        self.title_edit.setText(data.get('title', 'Vito Organizer'))
        self.subtitle_edit.setText(data.get('subtitle', ''))
        self.title_edit.blockSignals(False)
        self.subtitle_edit.blockSignals(False)
        
        img_file = data.get('image_file', '')
        agenda_path = self.plugin.get_agenda_path()
        loaded = False

        if agenda_path:
            portada_dir = os.path.join(agenda_path, 'portada')
            if img_file:
                img_path = os.path.join(portada_dir, img_file)
                if os.path.exists(img_path):
                    self.load_image(img_path)
                    loaded = True

            if not loaded and os.path.exists(portada_dir):
                for f in os.listdir(portada_dir):
                    if f.startswith('cover_image') and f.lower().endswith(IMAGE_EXTENSIONS):
                        img_path = os.path.join(portada_dir, f)
                        self.load_image(img_path)
                        self.plugin.get_data()['image_file'] = f
                        loaded = True
                        break

        if not loaded:
            self.load_image('')


class PortadaPlugin(PluginBase):
    """Plugin para la sección de Portada."""

    def __init__(self):
        super().__init__()
        self._data = {
            'title': 'Vito Organizer',
            'subtitle': '',
            'image_file': ''
        }
        self._sidebar = PortadaSidebar()
        self._left_page = QWidget() # Vacía intencionalmente (contraportada)
        self._right_page = PortadaCoverWidget(self)
        self._is_modified = False

    def get_name(self) -> str:
        return "Portada"

    def get_id(self) -> str:
        return "portada"

    def get_icon(self) -> str:
        return "portada.svg"

    def get_tab_color(self) -> str:
        return "#8B8B8B"

    def get_order(self) -> int:
        return 0

    def create_sidebar_widget(self) -> QWidget:
        return self._sidebar

    def create_left_page(self) -> QWidget:
        return self._left_page

    def create_right_page(self) -> QWidget:
        return self._right_page

    def on_activate(self):
        super().on_activate()
        path = self.get_agenda_path()
        if path:
            name = os.path.basename(path)
            self._sidebar.update_info(name, path)

    def get_data(self) -> Dict[str, Any]:
        return self._data

    def mark_modified(self):
        self._is_modified = True

    def set_agenda_path(self, path: str):
        super().set_agenda_path(path)
        name = os.path.basename(path) if path else "-"
        self._sidebar.update_info(name, path or "-")

    def load_data(self, agenda_path: str):
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
        
        self._right_page.update_from_data(self._data)
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            DataStore.save(data_path, self._data)
            self._is_modified = False
