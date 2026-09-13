# =============================================================================
# Vito Organizer v2.2 - Plugin Base
# Clase base abstracta para todos los plugins de sección
# =============================================================================

from abc import ABCMeta, abstractmethod
from typing import List, Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QWidget


class PluginBaseMeta(type(QObject), ABCMeta):
    pass


import os

IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.avif', '.svg')
IMAGE_FILE_FILTER = "Imágenes (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.avif *.svg);;Todos los Archivos (*.*)"


def load_image_pixmap(file_path: str):
    """Carga una imagen en un QPixmap soportando PNG, JPG, JPEG, BMP, GIF, WEBP, SVG y AVIF.
    Para AVIF o formatos especiales utiliza decodificadores auxiliares (Pillow, ffmpeg o ImageMagick)
    de forma completamente transparente.
    """
    if not file_path or not os.path.exists(file_path):
        from PyQt6.QtGui import QPixmap
        return QPixmap()

    from PyQt6.QtGui import QPixmap, QImage

    # 1. Intento nativo con Qt6
    pix = QPixmap(file_path)
    if not pix.isNull():
        return pix

    # 2. Intento con Pillow / pillow_heif si está instalado
    try:
        from PIL import Image
        import io
        img = Image.open(file_path)
        img = img.convert("RGBA")
        bio = io.BytesIO()
        img.save(bio, format="PNG")
        qimg = QImage.fromData(bio.getvalue())
        if not qimg.isNull():
            return QPixmap.fromImage(qimg)
    except Exception:
        pass

    # 3. Intento con ffmpeg (soporta AVIF nativamente en Linux)
    try:
        import subprocess
        p = subprocess.run(['ffmpeg', '-i', file_path, '-f', 'image2pipe', '-vcodec', 'png', '-'],
                           capture_output=True, timeout=5)
        if p.returncode == 0 and len(p.stdout) > 0:
            qimg = QImage.fromData(p.stdout)
            if not qimg.isNull():
                return QPixmap.fromImage(qimg)
    except Exception:
        pass

    # 4. Intento con ImageMagick (convert)
    try:
        import subprocess
        p = subprocess.run(['convert', file_path, 'png:-'], capture_output=True, timeout=5)
        if p.returncode == 0 and len(p.stdout) > 0:
            qimg = QImage.fromData(p.stdout)
            if not qimg.isNull():
                return QPixmap.fromImage(qimg)
    except Exception:
        pass

    return QPixmap()


def load_image_qimage(file_path: str):
    """Carga una imagen en un QImage con soporte extendido para AVIF."""
    pix = load_image_pixmap(file_path)
    if not pix.isNull():
        return pix.toImage()
    from PyQt6.QtGui import QImage
    return QImage()


def open_local_file(full_path: str):
    """Abre un archivo local usando el programa predeterminado del sistema.
    En Linux, redirige la salida estándar y de error para evitar ensuciar
    la terminal con advertencias de bibliotecas externas (e.g., GLib, GTK).
    """
    if not full_path or not os.path.exists(full_path):
        return

    import sys
    from PyQt6.QtGui import QDesktopServices
    from PyQt6.QtCore import QUrl

    if sys.platform.startswith('linux'):
        try:
            import subprocess
            subprocess.Popen(['xdg-open', full_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))
    else:
        QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))


class PluginBase(QObject, metaclass=PluginBaseMeta):
    """Clase base abstracta para todos los plugins de sección de la agenda.

    Cada plugin representa una sección de la agenda (Portada, Calendario,
    Cumpleaños, Tareas, Notas, Planificador) y proporciona:
    - Widget para la barra lateral (sidebar)
    - Contenido para la página izquierda y derecha de la agenda
    - Gestión de datos propios (carga, guardado, papelera)
    """

    page_changed = pyqtSignal(int, int) # (current_page, total_pages)
    single_page_requested = pyqtSignal(bool) # True = activate single page mode, False = restore normal
    status_message_requested = pyqtSignal(str)
    pdf_export_state_changed = pyqtSignal(bool) # Emits True/False when PDF export availability changes

    def __init__(self):
        super().__init__()
        self._agenda_path: Optional[str] = None
        self._data: Dict[str, Any] = {}
        self._trash: List[Dict[str, Any]] = []
        self._is_active: bool = False

    @property
    def _is_modified(self) -> bool:
        return getattr(self, '_is_modified_internal', False)

    @_is_modified.setter
    def _is_modified(self, value: bool):
        self._is_modified_internal = value
        if value:
            path = self.get_agenda_path()
            if path:
                try:
                    self.save_data(path)
                    self.status_message_requested.emit(f"✓ {self.get_name()}: Cambios auto-guardados correctamente")
                except Exception as e:
                    print(f"Error en auto-guardado del plugin {self.get_id()}: {e}")
                    self.status_message_requested.emit(f"❌ Error al auto-guardar datos de {self.get_name()}")

    # ---- Propiedades abstractas (obligatorias) ----

    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre de la sección (e.g., 'Calendario')."""
        ...

    @abstractmethod
    def get_id(self) -> str:
        """Retorna el identificador único del plugin (e.g., 'calendario')."""
        ...

    @abstractmethod
    def get_icon(self) -> str:
        """Retorna el nombre del archivo de icono SVG (e.g., 'calendar.svg')."""
        ...

    @abstractmethod
    def get_tab_color(self) -> str:
        """Retorna el color hex de la pestaña de esta sección."""
        ...

    @abstractmethod
    def get_order(self) -> int:
        """Retorna el orden de la sección en las pestañas (0 = primera)."""
        ...

    # ---- Widgets abstractos (obligatorios) ----

    @abstractmethod
    def create_sidebar_widget(self) -> QWidget:
        """Crea y retorna el widget para mostrar en la barra lateral.

        Este widget se muestra cuando la sección está activa.
        Debe incluir controles específicos de la sección.
        """
        ...

    @abstractmethod
    def create_left_page(self) -> QWidget:
        """Crea y retorna el widget de contenido para la página izquierda."""
        ...

    @abstractmethod
    def create_right_page(self) -> QWidget:
        """Crea y retorna el widget de contenido para la página derecha."""
        ...

    # ---- Ciclo de vida ----

    def on_activate(self):
        """Se llama cuando la sección se activa (el usuario la selecciona)."""
        self._is_active = True

    def on_deactivate(self):
        """Se llama cuando la sección se desactiva."""
        self._is_active = False

    def is_active(self) -> bool:
        """Retorna si la sección está activa actualmente."""
        return self._is_active

    # ---- Exportación a PDF ----

    def supports_pdf_export(self) -> bool:
        """Retorna True si la sección o vista actual permite exportar a PDF."""
        return False

    def export_pdf(self, parent_widget=None):
        """Ejecuta la exportación a PDF para la sección actual."""
        pass

    # ---- Paginación y Navegación de Sección ----

    def get_total_pages(self) -> int:
        """Retorna el número total de páginas (o pliegos) de la sección."""
        return 1

    def get_current_page(self) -> int:
        """Retorna la página (o pliego) actual (1-indexed)."""
        return 1

    def go_to_page(self, page_num: int):
        """Navega a la página especificada."""
        pass

    # ---- Gestión de datos ----

    def set_agenda_path(self, path: str):
        """Establece la ruta de la agenda actual."""
        self._agenda_path = path

    def get_agenda_path(self) -> Optional[str]:
        """Retorna la ruta de la agenda actual."""
        return self._agenda_path

    @abstractmethod
    def load_data(self, agenda_path: str):
        """Carga los datos del plugin desde la carpeta de la agenda.

        Args:
            agenda_path: Ruta a la carpeta de la agenda.
        """
        ...

    @abstractmethod
    def save_data(self, agenda_path: str):
        """Guarda los datos del plugin en la carpeta de la agenda.

        Args:
            agenda_path: Ruta a la carpeta de la agenda.
        """
        ...

    def clear_data(self):
        """Limpia todos los datos del plugin (para nueva agenda o cerrar)."""
        self._data = {}
        self._trash = []

    # ---- Papelera ----

    def get_trash_items(self) -> List[Dict[str, Any]]:
        """Retorna los items en la papelera de esta sección."""
        return self._trash

    def has_trash(self) -> bool:
        """Retorna True si hay items en la papelera."""
        return len(self._trash) > 0

    def move_to_trash(self, item: Dict[str, Any]):
        """Mueve un item a la papelera."""
        item['_deleted_at'] = self._get_timestamp()
        self._trash.append(item)

    def restore_from_trash(self, item_index: int) -> Optional[Dict[str, Any]]:
        """Restaura un item de la papelera por su índice."""
        if 0 <= item_index < len(self._trash):
            item = self._trash.pop(item_index)
            item.pop('_deleted_at', None)
            return item
        return None

    def empty_trash(self):
        """Vacía la papelera permanentemente."""
        self._trash.clear()

    def trash_count(self) -> int:
        """Retorna la cantidad de items en la papelera."""
        return len(self._trash)

    # ---- Utilidades ----

    @staticmethod
    def _get_timestamp() -> str:
        """Retorna timestamp actual en formato ISO."""
        from datetime import datetime
        return datetime.now().isoformat()

    @staticmethod
    def _generate_id() -> str:
        """Genera un ID único."""
        import uuid
        return str(uuid.uuid4())

    def open_local_file(self, full_path: str):
        """Abre un archivo local usando el programa predeterminado del sistema."""
        open_local_file(full_path)

    def __repr__(self) -> str:
        return f"<Plugin: {self.get_name()} ({self.get_id()})>"
