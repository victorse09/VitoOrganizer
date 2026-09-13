# =============================================================================
# Vito Organizer v2.2 - Biblioteca: Visor Integrado de PDF y EPUB
# Visor con Marcadores, Extracción de Artículos, OCR, Traductor Técnico y Vistas
# =============================================================================

import os
import re
import fitz  # PyMuPDF
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint, QRect, QRectF, QDate, QTime, QTimer
from PyQt6.QtGui import (
    QPixmap, QImage, QIcon, QPainter, QColor, QPen, QBrush, QCursor, QFont,
    QKeySequence, QShortcut, QClipboard, QGuiApplication
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea,
    QFrame, QLineEdit, QComboBox, QSplitter, QListWidget, QListWidgetItem,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QDialog, QMessageBox,
    QFileDialog, QTextEdit, QSpinBox, QCheckBox, QToolButton, QMenu,
    QInputDialog, QProgressBar, QApplication, QButtonGroup
)

from plugins.plugin_base import open_local_file
from plugins.biblioteca.doc_translator import DocTranslateDialog, get_themed_svg_icon


class OCRResultDialog(QDialog):
    """Diálogo modal para visualizar, copiar y traducir el texto extraído / OCR."""
    def __init__(self, text: str, page_num: int, is_clip: bool = False, doc_context: dict = None, parent=None):
        super().__init__(parent)
        self.raw_text = text
        self.doc_context = doc_context or {}
        self.setWindowTitle(f"Reconocimiento de Texto / OCR — Página {page_num}" + (" (Selección)" if is_clip else ""))
        self.resize(580, 430)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E2E; color: #CDD6F4; }
            QLabel { color: #CDD6F4; font-size: 12px; }
            QTextEdit { background-color: #181825; color: #CDD6F4; border: 1px solid #313244; border-radius: 4px; font-family: monospace; font-size: 12px; padding: 8px; }
            QPushButton { background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; padding: 6px 14px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #45475A; color: #FFFFFF; }
            QPushButton#btnPrimary { background-color: #1E88E5; color: #FFFFFF; border: none; }
            QPushButton#btnPrimary:hover { background-color: #1565C0; }
            QPushButton#btnTranslate { background-color: #2E7D32; color: #FFFFFF; border: none; }
            QPushButton#btnTranslate:hover { background-color: #1B5E20; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        hdr = QLabel(f"<b>Texto Extraído / OCR (Página {page_num}):</b>")
        layout.addWidget(hdr)

        self.txt_edit = QTextEdit()
        self.txt_edit.setPlainText(text if text.strip() else "(No se detectó texto en el área seleccionada)")
        layout.addWidget(self.txt_edit, 1)

        # Estadísticas
        words = len(text.split())
        chars = len(text)
        lbl_stats = QLabel(f"Estadísticas: {words} palabras | {chars} caracteres")
        lbl_stats.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        layout.addWidget(lbl_stats)

        # Botones
        btn_layout = QHBoxLayout()
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        btn_copy = QPushButton(" Copiar al Portapapeles")
        btn_copy.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'copy.svg'), '#FFFFFF', 14))
        btn_copy.setObjectName("btnPrimary")
        btn_copy.clicked.connect(self._copy_text)
        btn_layout.addWidget(btn_copy)

        btn_translate = QPushButton(" Traducir al Español")
        btn_translate.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'globe.svg'), '#FFFFFF', 14))
        btn_translate.setObjectName("btnTranslate")
        btn_translate.clicked.connect(self._open_translator)
        btn_layout.addWidget(btn_translate)

        btn_send_doki = QPushButton(" 📝 Enviar a Doki...")
        btn_send_doki.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'new_note.svg'), '#FFFFFF', 14))
        btn_send_doki.setStyleSheet("QPushButton { background-color: #D84315; color: #FFFFFF; font-weight: bold; } QPushButton:hover { background-color: #E64A19; }")
        btn_send_doki.clicked.connect(self._send_to_doki)
        btn_layout.addWidget(btn_send_doki)

        btn_save = QPushButton(" Guardar como Archivo...")
        btn_save.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'save.svg'), '#CDD6F4', 14))
        btn_save.clicked.connect(self._save_file)
        btn_layout.addWidget(btn_save)

        btn_layout.addStretch()
        btn_close = QPushButton(" Cerrar")
        btn_close.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'close.svg'), '#CDD6F4', 14))
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _copy_text(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.txt_edit.toPlainText())
        QMessageBox.information(self, "Copiado", "Texto copiado al portapapeles.")

    def _open_translator(self):
        txt = self.txt_edit.toPlainText().strip()
        if not txt or txt == "(No se detectó texto en el área seleccionada)":
            QMessageBox.information(self, "Sin Texto", "No hay texto válido para traducir.")
            return
        dlg = DocTranslateDialog(source_text=txt, doc_context=self.doc_context, parent=self)
        dlg.exec()

    def _send_to_doki(self):
        text = self.txt_edit.toPlainText().strip()
        if not text or text == "(No se detectó texto en el área seleccionada)":
            QMessageBox.information(self, "Sin Texto", "No hay texto para enviar a un documento Doki.")
            return

        agenda_path = self.doc_context.get('agenda_path', '')
        if not agenda_path and hasattr(self.parent(), 'agenda_path'):
            agenda_path = getattr(self.parent(), 'agenda_path', '')

        if not agenda_path:
            QMessageBox.warning(self, "Agenda no disponible", "No se detectó una ruta de agenda activa para guardar documentos Doki.")
            return

        from plugins.biblioteca.doki_editor import DokiManager, NewDokiDialog
        doki_dir = DokiManager.get_doki_dir(agenda_path)
        doki_files = [f for f in os.listdir(doki_dir) if f.endswith('.doki')]

        options = ["➕ Crear Nuevo Documento Doki..."]
        file_map = {}
        for fn in doki_files:
            fp = os.path.join(doki_dir, fn)
            try:
                data = DokiManager.load_doki(fp)
                t = data.get('metadata', {}).get('title', fn)
                label = f"📄 {t} ({fn})"
                options.append(label)
                file_map[label] = fp
            except Exception:
                pass

        choice, ok = QInputDialog.getItem(self, "Enviar OCR a Documento Doki", "Selecciona el documento destino:", options, 0, False)
        if not ok or not choice: return

        if choice == "➕ Crear Nuevo Documento Doki...":
            dlg = NewDokiDialog(parent=self)
            if dlg.exec():
                d = dlg.get_data()
                meta = DokiManager.create_empty_doki(agenda_path, d['title'], d['author'], d['description'])
                full_p = os.path.join(agenda_path, meta['relative_path'])
                data = DokiManager.load_doki(full_p)
                cur_html = data.get('html', '')
                appended_html = cur_html + f"<br><h3>Texto Extraído (OCR)</h3><p>{text.replace(chr(10), '<br>')}</p>"
                DokiManager.save_doki(full_p, meta, appended_html, data.get('images', {}))
                QMessageBox.information(self, "Documento Creado", f"Se ha creado el documento Doki y se agregó el texto OCR:\n{meta['title']}")
        else:
            target_fp = file_map.get(choice)
            if target_fp and os.path.exists(target_fp):
                data = DokiManager.load_doki(target_fp)
                meta = data.get('metadata', {})
                cur_html = data.get('html', '')
                appended_html = cur_html + f"<br><h3>Texto Extraído (OCR)</h3><p>{text.replace(chr(10), '<br>')}</p>"
                DokiManager.save_doki(target_fp, meta, appended_html, data.get('images', {}))
                QMessageBox.information(self, "Texto Insertado", f"Texto insertado exitosamente en:\n{meta.get('title', choice)}")

    def _save_file(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Texto Reconocido", "texto_extraido.txt", "Archivos de Texto (*.txt)")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(self.txt_edit.toPlainText())
                QMessageBox.information(self, "Guardado", f"Archivo guardado exitosamente en:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {e}")


class CreateArticleDialog(QDialog):
    """Diálogo para seleccionar rango de páginas y exportar un nuevo artículo en PDF."""
    def __init__(self, total_pages: int, current_page: int, default_title: str = "", parent=None):
        super().__init__(parent)
        self.total_pages = total_pages
        self.setWindowTitle("Crear Artículo y Exportar como PDF")
        self.setMinimumWidth(440)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E2E; color: #CDD6F4; }
            QLabel { color: #CDD6F4; font-size: 12px; }
            QLineEdit, QTextEdit, QSpinBox { background-color: #181825; color: #CDD6F4; border: 1px solid #313244; border-radius: 4px; padding: 5px; font-size: 12px; }
            QPushButton { background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; padding: 6px 14px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #45475A; color: #FFFFFF; }
            QPushButton#btnPrimary { background-color: #2E7D32; color: #FFFFFF; border: none; }
            QPushButton#btnPrimary:hover { background-color: #1B5E20; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        layout.addWidget(QLabel("<b>Título del Artículo / Sección:</b>"))
        self.txt_title = QLineEdit(default_title)
        self.txt_title.setPlaceholderText("Ej: Artículo sobre Fuentes Conmutadas, Cap. 3...")
        layout.addWidget(self.txt_title)

        layout.addWidget(QLabel("<b>Rango de Páginas (de 1 a " + str(total_pages) + "):</b>"))
        page_layout = QHBoxLayout()
        page_layout.addWidget(QLabel("Desde página:"))
        self.spn_from = QSpinBox()
        self.spn_from.setRange(1, total_pages)
        self.spn_from.setValue(current_page)
        page_layout.addWidget(self.spn_from)

        page_layout.addWidget(QLabel("Hasta página:"))
        self.spn_to = QSpinBox()
        self.spn_to.setRange(1, total_pages)
        self.spn_to.setValue(min(current_page + 3, total_pages))
        page_layout.addWidget(self.spn_to)
        layout.addLayout(page_layout)

        layout.addWidget(QLabel("<b>Descripción o Notas (Opcional):</b>"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(70)
        self.txt_desc.setPlaceholderText("Breve resumen o contenido del artículo...")
        layout.addWidget(self.txt_desc)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        btn_cancel = QPushButton(" Cancelar")
        btn_cancel.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'close.svg'), '#CDD6F4', 14))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_create = QPushButton(" Crear y Exportar PDF")
        btn_create.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'new_file.svg'), '#FFFFFF', 14))
        btn_create.setObjectName("btnPrimary")
        btn_create.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(btn_create)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        title = self.txt_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Título Requerido", "Por favor ingresa un título para el artículo.")
            return
        if self.spn_from.value() > self.spn_to.value():
            QMessageBox.warning(self, "Rango Inválido", "La página inicial no puede ser mayor que la página final.")
            return
        self.accept()

    def get_article_data(self) -> dict:
        return {
            'id': f"art_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}",
            'title': self.txt_title.text().strip(),
            'description': self.txt_desc.toPlainText().strip(),
            'from_page': self.spn_from.value(),
            'to_page': self.spn_to.value(),
            'page_count': (self.spn_to.value() - self.spn_from.value() + 1),
            'date': QDate.currentDate().toString('yyyy-MM-dd')
        }


class DocPageViewCanvas(QWidget):
    """Lienzo principal de renderizado de la página del documento con soporte de selección."""
    
    selection_made = pyqtSignal(QRect)
    double_clicked = pyqtSignal(QPoint)

    def __init__(self, page_index: int = 0, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.pixmap = None
        self.tool_mode = 'hand'  # 'hand', 'rect_select'
        self.selection_start = None
        self.selection_current = None
        self.selected_rect = None
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #2B2D42; border-radius: 4px;")

    def set_pixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap
        self.selected_rect = None
        self.selection_start = None
        self.selection_current = None
        if pixmap:
            self.setFixedSize(pixmap.size())
        self.update()

    def set_tool_mode(self, mode: str):
        self.tool_mode = mode
        self.selected_rect = None
        self.selection_start = None
        self.selection_current = None
        if mode == 'hand':
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif mode in ('text_select', 'rect_select'):
            self.setCursor(Qt.CursorShape.CrossCursor)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.tool_mode in ('text_select', 'rect_select'):
                self.selection_start = event.pos()
                self.selection_current = event.pos()
                self.selected_rect = None
                self.update()
            elif self.tool_mode == 'hand':
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.selection_start and self.tool_mode in ('text_select', 'rect_select'):
            self.selection_current = event.pos()
            self.selected_rect = QRect(self.selection_start, self.selection_current).normalized()
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.tool_mode in ('text_select', 'rect_select') and self.selected_rect:
                if self.selected_rect.width() > 5 and self.selected_rect.height() > 5:
                    self.selection_made.emit(self.selected_rect)
            elif self.tool_mode == 'hand':
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.selection_start = None
            self.selection_current = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(event.pos())
        super().mouseDoubleClickEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)

        # Dibujar cuadro de selección
        if self.selected_rect and not self.selected_rect.isNull():
            pen = QPen(QColor(30, 144, 255), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            brush = QBrush(QColor(30, 144, 255, 60))
            painter.setBrush(brush)
            painter.drawRect(self.selected_rect)


class DocViewerSinglePageWidget(QWidget):
    """Visor integrado de PDF y EPUB en Modo de Página Única con herramientas avanzadas."""

    back_requested = pyqtSignal()
    bookmarks_updated = pyqtSignal(list)
    articles_updated = pyqtSignal(list)

    def __init__(self, item: dict, agenda_path: str, initial_page: int = 1, parent=None):
        super().__init__(parent)
        self.item = item
        self.agenda_path = agenda_path
        self.current_page = max(1, initial_page)
        self.total_pages = 1
        self.zoom_level = 1.0
        self.rotation_angle = 0
        self.view_mode = 'single'  # 'single' o 'continuous'
        self.doc = None
        self.active_tool_mode = 'hand'
        self.continuous_canvases = []  # List of DocPageViewCanvas for continuous view
        self.icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        self.bookmarks = list(self.item.get('bookmarks', []))
        self.articles = list(self.item.get('articles', []))

        self.setStyleSheet("""
            QWidget { background-color: #1E1E2E; color: #CDD6F4; font-family: sans-serif; }
            QSplitter::handle { background-color: #313244; }
            QScrollArea { border: none; background-color: #181825; }
            QScrollBar:vertical, QScrollBar:horizontal { background: #181825; border: none; }
            QScrollBar::handle { background: #45475A; border-radius: 4px; }
            QScrollBar::handle:hover { background: #585B70; }
        """)

        self._setup_ui()
        self._load_document()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Barra de Herramientas Superior
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(44)
        self.toolbar.setStyleSheet("""
            QFrame { background-color: #181825; border-bottom: 1px solid #313244; }
            QPushButton { background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #45475A; color: #FFFFFF; }
            QPushButton:checked { background-color: #1E88E5; color: #FFFFFF; border-color: #1565C0; }
            QLineEdit, QComboBox { background-color: #1E1E2E; color: #CDD6F4; border: 1px solid #313244; border-radius: 4px; padding: 2px 6px; font-size: 11px; }
            QLabel { color: #CDD6F4; font-size: 11px; }
        """)
        tb_layout = QHBoxLayout(self.toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(5)

        # Botón Volver
        self.btn_back = QPushButton(" Volver a Biblioteca")
        self.btn_back.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'left.svg'), '#FFFFFF', 16))
        self.btn_back.setStyleSheet("QPushButton { background-color: #45475A; color: #FFFFFF; font-weight: bold; border-radius: 4px; padding: 4px 10px; } QPushButton:hover { background-color: #585B70; }")
        self.btn_back.clicked.connect(self.back_requested.emit)
        tb_layout.addWidget(self.btn_back)

        # Título del archivo / Tipo
        doc_type = self.item.get('type', 'Documento')
        self.lbl_doc_title = QLabel(f"<b>{self.item.get('name', 'Documento')}</b> <span style='color:#A6ADC8;'>({doc_type})</span>")
        self.lbl_doc_title.setMaximumWidth(220)
        tb_layout.addWidget(self.lbl_doc_title)

        tb_layout.addWidget(self._create_separator())

        # Navegación de páginas
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'left.svg'), '#CDD6F4', 14))
        self.btn_prev.setToolTip("Página Anterior (Flecha Izq)")
        self.btn_prev.setFixedSize(26, 26)
        self.btn_prev.clicked.connect(self._prev_page)
        tb_layout.addWidget(self.btn_prev)

        self.txt_page_num = QLineEdit(str(self.current_page))
        self.txt_page_num.setFixedWidth(38)
        self.txt_page_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.txt_page_num.returnPressed.connect(self._on_page_input)
        tb_layout.addWidget(self.txt_page_num)

        self.lbl_total_pages = QLabel(f"/ {self.total_pages}")
        tb_layout.addWidget(self.lbl_total_pages)

        self.btn_next = QPushButton()
        self.btn_next.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'right.svg'), '#CDD6F4', 14))
        self.btn_next.setToolTip("Página Siguiente (Flecha Der)")
        self.btn_next.setFixedSize(26, 26)
        self.btn_next.clicked.connect(self._next_page)
        tb_layout.addWidget(self.btn_next)

        tb_layout.addWidget(self._create_separator())

        # Modos de Visualización: Página a Página vs Vista Continua
        self.view_mode_group = QButtonGroup(self)
        self.btn_view_single = QPushButton(" Página")
        self.btn_view_single.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'document.svg'), '#CDD6F4', 13))
        self.btn_view_single.setCheckable(True)
        self.btn_view_single.setChecked(True)
        self.btn_view_single.setToolTip("Vista Página a Página individual")
        self.btn_view_single.clicked.connect(lambda: self._set_view_mode('single'))
        self.view_mode_group.addButton(self.btn_view_single)
        tb_layout.addWidget(self.btn_view_single)

        self.btn_view_continuous = QPushButton(" Continua")
        self.btn_view_continuous.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'document_dark.svg'), '#CDD6F4', 13))
        self.btn_view_continuous.setCheckable(True)
        self.btn_view_continuous.setToolTip("Vista de Flujo Continuo con desplazamiento vertical")
        self.btn_view_continuous.clicked.connect(lambda: self._set_view_mode('continuous'))
        self.view_mode_group.addButton(self.btn_view_continuous)
        tb_layout.addWidget(self.btn_view_continuous)

        tb_layout.addWidget(self._create_separator())

        # Zoom y Ajustes
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setToolTip("Reducir Zoom (Ctrl -)")
        self.btn_zoom_out.setFixedSize(24, 24)
        self.btn_zoom_out.clicked.connect(self._zoom_out)
        tb_layout.addWidget(self.btn_zoom_out)

        self.cb_zoom = QComboBox()
        self.cb_zoom.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "Ajustar Ancho", "Ajustar Alto"])
        self.cb_zoom.setCurrentText("100%")
        self.cb_zoom.setFixedWidth(90)
        self.cb_zoom.currentTextChanged.connect(self._on_zoom_combo_changed)
        tb_layout.addWidget(self.cb_zoom)

        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setToolTip("Aumentar Zoom (Ctrl +)")
        self.btn_zoom_in.setFixedSize(24, 24)
        self.btn_zoom_in.clicked.connect(self._zoom_in)
        tb_layout.addWidget(self.btn_zoom_in)

        # Botones directos de ajuste
        self.btn_fit_width = QPushButton()
        self.btn_fit_width.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'ruler.svg'), '#CDD6F4', 14))
        self.btn_fit_width.setToolTip("Ajustar al Ancho de la Pantalla")
        self.btn_fit_width.setFixedSize(26, 26)
        self.btn_fit_width.clicked.connect(self._fit_width)
        tb_layout.addWidget(self.btn_fit_width)

        self.btn_fit_height = QPushButton()
        self.btn_fit_height.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'panoramic.svg'), '#CDD6F4', 14))
        self.btn_fit_height.setToolTip("Ajustar a la Altura / Página Completa")
        self.btn_fit_height.setFixedSize(26, 26)
        self.btn_fit_height.clicked.connect(self._fit_height)
        tb_layout.addWidget(self.btn_fit_height)

        self.btn_rotate = QPushButton()
        self.btn_rotate.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'sync.svg'), '#CDD6F4', 14))
        self.btn_rotate.setToolTip("Rotar 90°")
        self.btn_rotate.setFixedSize(26, 26)
        self.btn_rotate.clicked.connect(self._rotate_page)
        tb_layout.addWidget(self.btn_rotate)

        tb_layout.addWidget(self._create_separator())

        # Modos de herramienta
        self.btn_mode_hand = QPushButton(" Mano")
        self.btn_mode_hand.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'panoramic.svg'), '#CDD6F4', 13))
        self.btn_mode_hand.setCheckable(True)
        self.btn_mode_hand.setChecked(True)
        self.btn_mode_hand.setToolTip("Modo Desplazamiento y Lectura")
        self.btn_mode_hand.clicked.connect(lambda: self._set_tool_mode('hand'))
        tb_layout.addWidget(self.btn_mode_hand)

        self.btn_mode_select = QPushButton(" Recortar / OCR")
        self.btn_mode_select.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'cut.svg'), '#CDD6F4', 13))
        self.btn_mode_select.setCheckable(True)
        self.btn_mode_select.setToolTip("Seleccionar área para Extraer Texto (OCR) o Imagen")
        self.btn_mode_select.clicked.connect(lambda: self._set_tool_mode('rect_select'))
        tb_layout.addWidget(self.btn_mode_select)

        tb_layout.addWidget(self._create_separator())

        # Acciones especiales: Marcador, OCR, Traductor, Artículo
        self.btn_bookmark = QPushButton(" Marcar")
        self.btn_bookmark.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'pushpin.svg'), '#FFFFFF', 13))
        self.btn_bookmark.setToolTip("Añadir o editar marcador en esta página")
        self.btn_bookmark.setStyleSheet("QPushButton { background-color: #2E7D32; color: #FFFFFF; font-weight: bold; } QPushButton:hover { background-color: #388E3C; }")
        self.btn_bookmark.clicked.connect(self._toggle_bookmark)
        tb_layout.addWidget(self.btn_bookmark)

        self.btn_ocr_page = QPushButton(" OCR")
        self.btn_ocr_page.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'search.svg'), '#CDD6F4', 13))
        self.btn_ocr_page.setToolTip("Reconocer y extraer todo el texto de la página actual")
        self.btn_ocr_page.clicked.connect(self._ocr_current_page)
        tb_layout.addWidget(self.btn_ocr_page)

        self.btn_translate = QPushButton(" Traducir")
        self.btn_translate.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'globe.svg'), '#FFFFFF', 14))
        self.btn_translate.setToolTip("Traducir texto técnico al español (IA Local / Online / Offline)")
        self.btn_translate.setStyleSheet("QPushButton { background-color: #1565C0; color: #FFFFFF; font-weight: bold; } QPushButton:hover { background-color: #0D47A1; }")
        self.btn_translate.clicked.connect(self._open_translator_dialog)
        tb_layout.addWidget(self.btn_translate)

        self.btn_create_article = QPushButton(" Artículo")
        self.btn_create_article.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'new_file.svg'), '#FFFFFF', 13))
        self.btn_create_article.setToolTip("Seleccionar rango de páginas y exportar como nuevo PDF")
        self.btn_create_article.setStyleSheet("QPushButton { background-color: #D84315; color: #FFFFFF; font-weight: bold; } QPushButton:hover { background-color: #E64A19; }")
        self.btn_create_article.clicked.connect(self._show_create_article_dialog)
        tb_layout.addWidget(self.btn_create_article)

        tb_layout.addStretch()

        # Botón para colapsar panel lateral
        self.btn_toggle_sidebar = QPushButton(" Panel Lateral")
        self.btn_toggle_sidebar.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'sidebar_toggle.svg'), '#CDD6F4', 13))
        self.btn_toggle_sidebar.setCheckable(True)
        self.btn_toggle_sidebar.setChecked(True)
        self.btn_toggle_sidebar.clicked.connect(self._toggle_sidebar)
        tb_layout.addWidget(self.btn_toggle_sidebar)

        main_layout.addWidget(self.toolbar)

        # 2. Splitter Principal (Panel Lateral + Visor)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #313244; width: 4px; }")

        # 2.1 Panel Lateral
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setMinimumWidth(220)
        self.sidebar_widget.setMaximumWidth(360)
        self.sidebar_widget.setStyleSheet("background-color: #181825; border-right: 1px solid #313244;")
        sb_layout = QVBoxLayout(self.sidebar_widget)
        sb_layout.setContentsMargins(6, 6, 6, 6)
        sb_layout.setSpacing(6)

        # Pestañas de panel lateral
        sb_tabs_layout = QHBoxLayout()
        self.btn_tab_thumbs = QPushButton(" Miniaturas")
        self.btn_tab_thumbs.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'image_file.svg'), '#CDD6F4', 13))
        self.btn_tab_thumbs.setCheckable(True)
        self.btn_tab_thumbs.setChecked(True)
        self.btn_tab_thumbs.clicked.connect(lambda: self._set_sidebar_tab(0))
        sb_tabs_layout.addWidget(self.btn_tab_thumbs)

        self.btn_tab_bookmarks = QPushButton(" Marcadores")
        self.btn_tab_bookmarks.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'pushpin.svg'), '#CDD6F4', 13))
        self.btn_tab_bookmarks.setCheckable(True)
        self.btn_tab_bookmarks.clicked.connect(lambda: self._set_sidebar_tab(1))
        sb_tabs_layout.addWidget(self.btn_tab_bookmarks)

        self.btn_tab_articles = QPushButton(" Artículos")
        self.btn_tab_articles.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'document.svg'), '#CDD6F4', 13))
        self.btn_tab_articles.setCheckable(True)
        self.btn_tab_articles.clicked.connect(lambda: self._set_sidebar_tab(2))
        sb_tabs_layout.addWidget(self.btn_tab_articles)
        sb_layout.addLayout(sb_tabs_layout)

        self.sidebar_stack = QStackedWidget()

        # Tab 0: Miniaturas
        self.list_thumbnails = QListWidget()
        self.list_thumbnails.setStyleSheet("""
            QListWidget { background-color: #1E1E2E; border: 1px solid #313244; border-radius: 4px; }
            QListWidget::item { padding: 6px; border-bottom: 1px solid #313244; color: #CDD6F4; font-weight: bold; }
            QListWidget::item:selected { background-color: #1E88E5; color: #FFFFFF; }
        """)
        self.list_thumbnails.itemClicked.connect(self._on_thumbnail_clicked)
        self.sidebar_stack.addWidget(self.list_thumbnails)

        # Tab 1: Marcadores
        self.list_bookmarks = QListWidget()
        self.list_bookmarks.setStyleSheet("""
            QListWidget { background-color: #1E1E2E; border: 1px solid #313244; border-radius: 4px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #313244; color: #CDD6F4; }
            QListWidget::item:selected { background-color: #2E7D32; color: #FFFFFF; }
        """)
        self.list_bookmarks.itemClicked.connect(self._on_bookmark_clicked)
        self.sidebar_stack.addWidget(self.list_bookmarks)

        # Tab 2: Artículos
        self.list_articles = QListWidget()
        self.list_articles.setStyleSheet("""
            QListWidget { background-color: #1E1E2E; border: 1px solid #313244; border-radius: 4px; }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #313244; color: #CDD6F4; }
            QListWidget::item:selected { background-color: #D84315; color: #FFFFFF; }
        """)
        self.list_articles.itemClicked.connect(self._on_article_clicked)
        self.sidebar_stack.addWidget(self.list_articles)

        sb_layout.addWidget(self.sidebar_stack, 1)
        self.splitter.addWidget(self.sidebar_widget)

        # 2.2 Área Principal de Lectura (Scroll Area)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll_position_changed)

        self.canvas_container = QWidget()
        self.canvas_layout = QVBoxLayout(self.canvas_container)
        self.canvas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.canvas_layout.setContentsMargins(20, 20, 20, 20)
        self.canvas_layout.setSpacing(16)

        # Canvas individual para modo single-page
        self.single_canvas = DocPageViewCanvas(page_index=0)
        self.single_canvas.selection_made.connect(lambda r: self._on_canvas_selection_made(r, self.current_page))
        self.canvas_layout.addWidget(self.single_canvas)

        self.scroll_area.setWidget(self.canvas_container)
        self.splitter.addWidget(self.scroll_area)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        main_layout.addWidget(self.splitter, 1)

    def _create_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("background-color: #313244; max-width: 1px; margin: 4px 2px;")
        return sep

    def _load_document(self):
        rel_path = self.item.get('relative_path', '')
        full_path = os.path.join(self.agenda_path, rel_path) if self.agenda_path and rel_path else ""

        if not os.path.exists(full_path):
            QMessageBox.critical(self, "Archivo no encontrado", f"No se pudo encontrar el archivo físico en:\n{full_path}")
            return

        try:
            self.doc = fitz.open(full_path)
            self.total_pages = max(1, len(self.doc))
            self.lbl_total_pages.setText(f"/ {self.total_pages}")
            self._render_view()
            self._populate_thumbnails()
            self._refresh_bookmarks_list()
            self._refresh_articles_list()
        except Exception as e:
            QMessageBox.critical(self, "Error al abrir documento", f"Error al procesar el archivo con el motor PDF/EPUB:\n{e}")

    # =========================================================================
    # RENDERIZADO Y MODOS DE VISTA
    # =========================================================================

    def _set_view_mode(self, mode: str):
        if self.view_mode == mode: return
        self.view_mode = mode
        self.btn_view_single.setChecked(mode == 'single')
        self.btn_view_continuous.setChecked(mode == 'continuous')
        self._render_view()

    def _render_view(self):
        if not self.doc or len(self.doc) == 0:
            return

        if self.view_mode == 'single':
            self._render_single_page()
        else:
            self._render_continuous_pages()

    def _render_single_page(self):
        # Limpiar lienzos continuos si existían
        while self.canvas_layout.count():
            item = self.canvas_layout.takeAt(0)
            if item.widget() and item.widget() != self.single_canvas:
                item.widget().deleteLater()

        self.continuous_canvases.clear()
        self.single_canvas.setVisible(True)
        self.canvas_layout.addWidget(self.single_canvas)

        p_idx = max(0, min(self.current_page - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        mat = fitz.Matrix(self.zoom_level * 2.0, self.zoom_level * 2.0).prerotate(self.rotation_angle)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        fmt = QImage.Format.Format_RGB888
        qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
        pixmap = QPixmap.fromImage(qimg)

        self.single_canvas.set_pixmap(pixmap)
        self.single_canvas.set_tool_mode(self.active_tool_mode)
        self.txt_page_num.setText(str(self.current_page))

        self._update_bookmark_button_state()
        if self.list_thumbnails.count() > p_idx:
            self.list_thumbnails.setCurrentRow(p_idx)

    def _render_continuous_pages(self):
        self.single_canvas.setVisible(False)
        while self.canvas_layout.count():
            item = self.canvas_layout.takeAt(0)
            if item.widget() and item.widget() != self.single_canvas:
                item.widget().deleteLater()

        self.continuous_canvases.clear()
        mat = fitz.Matrix(self.zoom_level * 2.0, self.zoom_level * 2.0).prerotate(self.rotation_angle)

        for i in range(len(self.doc)):
            page = self.doc[i]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)

            # Contenedor de página con badge
            p_box = QWidget()
            p_layout = QVBoxLayout(p_box)
            p_layout.setContentsMargins(0, 0, 0, 0)
            p_layout.setSpacing(4)
            p_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            lbl_badge = QLabel(f"Página {i+1}")
            lbl_badge.setStyleSheet("color: #A6ADC8; font-size: 11px; font-weight: bold; background: #1E1E2E; padding: 2px 8px; border-radius: 3px;")
            p_layout.addWidget(lbl_badge, alignment=Qt.AlignmentFlag.AlignCenter)

            canvas = DocPageViewCanvas(page_index=i)
            canvas.set_pixmap(pixmap)
            canvas.set_tool_mode(self.active_tool_mode)
            canvas.selection_made.connect(lambda r, p_num=(i+1): self._on_canvas_selection_made(r, p_num))
            p_layout.addWidget(canvas, alignment=Qt.AlignmentFlag.AlignCenter)

            self.continuous_canvases.append((p_box, canvas))
            self.canvas_layout.addWidget(p_box)

        self._update_bookmark_button_state()

    def _on_scroll_position_changed(self, value):
        """Actualiza el número de página actual en modo continuo según el scroll visible."""
        if self.view_mode != 'continuous' or not self.continuous_canvases:
            return

        viewport_mid_y = self.scroll_area.verticalScrollBar().value() + (self.scroll_area.viewport().height() // 2)

        for idx, (p_box, _) in enumerate(self.continuous_canvases):
            p_top = p_box.y()
            p_bot = p_top + p_box.height()
            if p_top <= viewport_mid_y <= p_bot:
                if self.current_page != idx + 1:
                    self.current_page = idx + 1
                    self.txt_page_num.setText(str(self.current_page))
                    self._update_bookmark_button_state()
                    if self.list_thumbnails.count() > idx:
                        self.list_thumbnails.setCurrentRow(idx)
                break

    def _scroll_to_page(self, page_num: int):
        if self.view_mode == 'continuous' and 1 <= page_num <= len(self.continuous_canvases):
            p_box, _ = self.continuous_canvases[page_num - 1]
            self.scroll_area.verticalScrollBar().setValue(p_box.y())
        else:
            self.current_page = page_num
            self._render_view()

    # =========================================================================
    # AJUSTES DE ZOOM Y PANTALLA
    # =========================================================================

    def _fit_width(self):
        """Ajusta el zoom para que el ancho de la página coincida con el ancho de pantalla disponible."""
        if not self.doc or len(self.doc) == 0: return
        p_idx = max(0, min(self.current_page - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        avail_w = self.scroll_area.viewport().width() - 50
        if avail_w > 100 and page.rect.width > 0:
            target_zoom = max(0.3, min(3.0, avail_w / (page.rect.width * 2.0)))
            self.zoom_level = target_zoom
            self.cb_zoom.setCurrentText(f"{int(self.zoom_level * 100)}%")
            self._render_view()

    def _fit_height(self):
        """Ajusta el zoom para que el alto de la página coincida con la altura disponible."""
        if not self.doc or len(self.doc) == 0: return
        p_idx = max(0, min(self.current_page - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        avail_h = self.scroll_area.viewport().height() - 50
        if avail_h > 100 and page.rect.height > 0:
            target_zoom = max(0.3, min(3.0, avail_h / (page.rect.height * 2.0)))
            self.zoom_level = target_zoom
            self.cb_zoom.setCurrentText(f"{int(self.zoom_level * 100)}%")
            self._render_view()

    def _zoom_in(self):
        self.zoom_level = min(3.0, self.zoom_level + 0.25)
        self.cb_zoom.setCurrentText(f"{int(self.zoom_level * 100)}%")
        self._render_view()

    def _zoom_out(self):
        self.zoom_level = max(0.25, self.zoom_level - 0.25)
        self.cb_zoom.setCurrentText(f"{int(self.zoom_level * 100)}%")
        self._render_view()

    def _rotate_page(self):
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self._render_view()

    def _on_zoom_combo_changed(self, text: str):
        if text.endswith('%'):
            try:
                val = int(text.replace('%', ''))
                self.zoom_level = val / 100.0
                self._render_view()
            except ValueError:
                pass
        elif text == "Ajustar Ancho":
            self._fit_width()
        elif text in ("Ajustar Alto", "Página Completa"):
            self._fit_height()

    def _set_tool_mode(self, mode: str):
        self.active_tool_mode = mode
        self.btn_mode_hand.setChecked(mode == 'hand')
        self.btn_mode_select.setChecked(mode == 'rect_select')
        self.single_canvas.set_tool_mode(mode)
        for _, c in self.continuous_canvases:
            c.set_tool_mode(mode)

    # =========================================================================
    # NAVEGACIÓN Y MINIATURAS
    # =========================================================================

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            if self.view_mode == 'continuous':
                self._scroll_to_page(self.current_page)
            else:
                self._render_view()

    def _next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            if self.view_mode == 'continuous':
                self._scroll_to_page(self.current_page)
            else:
                self._render_view()

    def _on_page_input(self):
        try:
            val = int(self.txt_page_num.text().strip())
            if 1 <= val <= self.total_pages:
                self.current_page = val
                if self.view_mode == 'continuous':
                    self._scroll_to_page(self.current_page)
                else:
                    self._render_view()
            else:
                self.txt_page_num.setText(str(self.current_page))
        except ValueError:
            self.txt_page_num.setText(str(self.current_page))

    def _populate_thumbnails(self):
        if not self.doc: return
        self.list_thumbnails.clear()
        for i in range(len(self.doc)):
            page = self.doc[i]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.25, 0.25), alpha=False)
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            thumb_pixmap = QPixmap.fromImage(qimg).scaled(70, 95, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            item = QListWidgetItem(QIcon(thumb_pixmap), f"Página {i+1}")
            item.setSizeHint(QSize(180, 100))
            self.list_thumbnails.addItem(item)

    def _on_thumbnail_clicked(self, item: QListWidgetItem):
        row = self.list_thumbnails.row(item)
        self.current_page = row + 1
        if self.view_mode == 'continuous':
            self._scroll_to_page(self.current_page)
        else:
            self._render_view()

    def _toggle_sidebar(self, checked: bool):
        self.sidebar_widget.setVisible(checked)

    def _set_sidebar_tab(self, index: int):
        self.sidebar_stack.setCurrentIndex(index)
        self.btn_tab_thumbs.setChecked(index == 0)
        self.btn_tab_bookmarks.setChecked(index == 1)
        self.btn_tab_articles.setChecked(index == 2)

    # =========================================================================
    # MARCADORES
    # =========================================================================

    def _update_bookmark_button_state(self):
        is_bookmarked = any(b.get('page') == self.current_page for b in self.bookmarks)
        if is_bookmarked:
            self.btn_bookmark.setText(" ⭐ Marcada")
            self.btn_bookmark.setStyleSheet("QPushButton { background-color: #F57F17; color: #FFFFFF; font-weight: bold; }")
        else:
            self.btn_bookmark.setText(" Marcar")
            self.btn_bookmark.setStyleSheet("QPushButton { background-color: #2E7D32; color: #FFFFFF; font-weight: bold; }")

    def _toggle_bookmark(self):
        existing_idx = next((i for i, b in enumerate(self.bookmarks) if b.get('page') == self.current_page), -1)
        if existing_idx >= 0:
            menu = QMenu(self)
            act_edit = menu.addAction("✏ Editar Nota del Marcador")
            act_del = menu.addAction("🗑 Eliminar Marcador")
            action = menu.exec(QCursor.pos())
            if action == act_del:
                self.bookmarks.pop(existing_idx)
                self._on_bookmarks_modified()
            elif action == act_edit:
                cur_note = self.bookmarks[existing_idx].get('title', '')
                note, ok = QInputDialog.getText(self, "Editar Marcador", f"Título o nota para la Página {self.current_page}:", text=cur_note)
                if ok:
                    self.bookmarks[existing_idx]['title'] = note.strip() or f"Página {self.current_page}"
                    self._on_bookmarks_modified()
        else:
            note, ok = QInputDialog.getText(self, "Añadir Marcador", f"Título o nota para la Página {self.current_page}:", text=f"Marcador Pág. {self.current_page}")
            if ok:
                bm = {
                    'page': self.current_page,
                    'title': note.strip() or f"Página {self.current_page}",
                    'date': QDate.currentDate().toString('yyyy-MM-dd')
                }
                self.bookmarks.append(bm)
                self.bookmarks.sort(key=lambda x: x.get('page', 0))
                self._on_bookmarks_modified()

    def _on_bookmarks_modified(self):
        self.item['bookmarks'] = self.bookmarks
        self._refresh_bookmarks_list()
        self._update_bookmark_button_state()
        self.bookmarks_updated.emit(self.bookmarks)

    def _refresh_bookmarks_list(self):
        self.list_bookmarks.clear()
        if not self.bookmarks:
            item = QListWidgetItem("No hay marcadores aún.\nUsa '📌 Marcar' para guardar páginas.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_bookmarks.addItem(item)
            return

        for bm in self.bookmarks:
            p = bm.get('page', 1)
            t = bm.get('title', f'Página {p}')
            d = bm.get('date', '')
            item = QListWidgetItem(f"⭐ Pág. {p}: {t}\n    Fecha: {d}")
            item.setData(Qt.ItemDataRole.UserRole, p)
            self.list_bookmarks.addItem(item)

    def _on_bookmark_clicked(self, item: QListWidgetItem):
        p = item.data(Qt.ItemDataRole.UserRole)
        if p:
            self.current_page = int(p)
            if self.view_mode == 'continuous':
                self._scroll_to_page(self.current_page)
            else:
                self._render_view()

    # =========================================================================
    # OCR, TRADUCCIÓN Y SELECCIÓN
    # =========================================================================

    def _on_canvas_selection_made(self, rect: QRect, page_num: int):
        if not self.doc: return
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        # Menú contextual
        menu = QMenu(self)
        act_ocr = menu.addAction("🔍 Reconocer Texto (OCR)")
        act_translate = menu.addAction("🌐 Traducir Selección al Español")
        act_send_doki = menu.addAction("📝 Enviar Texto Seleccionado a Doki...")
        act_copy_img = menu.addAction("📋 Copiar Imagen al Portapapeles")
        act_send_img_doki = menu.addAction("🖼 Enviar Recorte de Imagen a Doki...")
        act_save_img = menu.addAction("💾 Guardar Imagen...")
        menu.addSeparator()
        act_cancel = menu.addAction("Cancelar Selección")

        action = menu.exec(QCursor.pos())
        if action == act_ocr:
            self._ocr_selection(rect, page_num)
        elif action == act_translate:
            self._translate_selection(rect, page_num)
        elif action == act_send_doki:
            self._send_selection_to_doki(rect, page_num)
        elif action == act_copy_img:
            self._copy_image_crop(rect, page_num)
        elif action == act_send_img_doki:
            self._send_image_crop_to_doki(rect, page_num)
        elif action == act_save_img:
            self._save_image_crop(rect, page_num)

    def _ocr_current_page(self):
        if not self.doc: return
        p_idx = max(0, min(self.current_page - 1, len(self.doc) - 1))
        page = self.doc[p_idx]
        text = page.get_text("text")
        ctx = {'doc': self.doc, 'current_page': self.current_page, 'total_pages': self.total_pages}
        dlg = OCRResultDialog(text, self.current_page, is_clip=False, doc_context=ctx, parent=self)
        dlg.exec()

    def _ocr_selection(self, rect: QRect, page_num: int):
        if not self.doc: return
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        canvas = self.single_canvas if self.view_mode == 'single' else self.continuous_canvases[p_idx][1]
        if not canvas or not canvas.pixmap: return

        pix_w = canvas.pixmap.width()
        pix_h = canvas.pixmap.height()
        rx0 = (rect.x() / pix_w) * page.rect.width
        ry0 = (rect.y() / pix_h) * page.rect.height
        rx1 = ((rect.x() + rect.width()) / pix_w) * page.rect.width
        ry1 = ((rect.y() + rect.height()) / pix_h) * page.rect.height
        clip_rect = fitz.Rect(rx0, ry0, rx1, ry1)

        text = page.get_text("text", clip=clip_rect)
        ctx = {'doc': self.doc, 'current_page': page_num, 'total_pages': self.total_pages}
        dlg = OCRResultDialog(text, page_num, is_clip=True, doc_context=ctx, parent=self)
        dlg.exec()

    def _translate_selection(self, rect: QRect, page_num: int):
        if not self.doc: return
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        canvas = self.single_canvas if self.view_mode == 'single' else self.continuous_canvases[p_idx][1]
        if not canvas or not canvas.pixmap: return

        pix_w = canvas.pixmap.width()
        pix_h = canvas.pixmap.height()
        rx0 = (rect.x() / pix_w) * page.rect.width
        ry0 = (rect.y() / pix_h) * page.rect.height
        rx1 = ((rect.x() + rect.width()) / pix_w) * page.rect.width
        ry1 = ((rect.y() + rect.height()) / pix_h) * page.rect.height
        clip_rect = fitz.Rect(rx0, ry0, rx1, ry1)

        text = page.get_text("text", clip=clip_rect)
        ctx = {'doc': self.doc, 'current_page': page_num, 'total_pages': self.total_pages}
        dlg = DocTranslateDialog(source_text=text, doc_context=ctx, parent=self)
        dlg.exec()

    def _open_translator_dialog(self):
        if not self.doc: return
        p_idx = max(0, min(self.current_page - 1, len(self.doc) - 1))
        page = self.doc[p_idx]
        cur_text = page.get_text("text")
        ctx = {'doc': self.doc, 'current_page': self.current_page, 'total_pages': self.total_pages}
        dlg = DocTranslateDialog(source_text=cur_text, doc_context=ctx, parent=self)
        dlg.exec()

    def _copy_image_crop(self, rect: QRect, page_num: int):
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        canvas = self.single_canvas if self.view_mode == 'single' else self.continuous_canvases[p_idx][1]
        if not canvas or not canvas.pixmap: return
        crop = canvas.pixmap.copy(rect)
        QGuiApplication.clipboard().setPixmap(crop)
        QMessageBox.information(self, "Copiado", "Recorte de imagen copiado al portapapeles.")

    def _send_selection_to_doki(self, rect: QRect, page_num: int):
        if not self.doc: return
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        page = self.doc[p_idx]

        canvas = self.single_canvas if self.view_mode == 'single' else self.continuous_canvases[p_idx][1]
        if not canvas or not canvas.pixmap: return

        pix_w = canvas.pixmap.width()
        pix_h = canvas.pixmap.height()
        rx0 = (rect.x() / pix_w) * page.rect.width
        ry0 = (rect.y() / pix_h) * page.rect.height
        rx1 = ((rect.x() + rect.width()) / pix_w) * page.rect.width
        ry1 = ((rect.y() + rect.height()) / pix_h) * page.rect.height
        clip_rect = fitz.Rect(rx0, ry0, rx1, ry1)

        text = page.get_text("text", clip=clip_rect).strip()
        if not text:
            QMessageBox.information(self, "Sin Texto", "No se detectó texto en el área seleccionada.")
            return

        if not self.agenda_path:
            QMessageBox.warning(self, "Agenda no disponible", "No hay una ruta de agenda activa.")
            return

        from plugins.biblioteca.doki_editor import DokiManager, NewDokiDialog
        doki_dir = DokiManager.get_doki_dir(self.agenda_path)
        doki_files = [f for f in os.listdir(doki_dir) if f.endswith('.doki')]

        options = ["➕ Crear Nuevo Documento Doki..."]
        file_map = {}
        for fn in doki_files:
            fp = os.path.join(doki_dir, fn)
            try:
                data = DokiManager.load_doki(fp)
                t = data.get('metadata', {}).get('title', fn)
                label = f"📄 {t} ({fn})"
                options.append(label)
                file_map[label] = fp
            except Exception:
                pass

        choice, ok = QInputDialog.getItem(self, "Enviar Selección a Documento Doki", "Selecciona el documento destino:", options, 0, False)
        if not ok or not choice: return

        if choice == "➕ Crear Nuevo Documento Doki...":
            dlg = NewDokiDialog(parent=self)
            if dlg.exec():
                d = dlg.get_data()
                meta = DokiManager.create_empty_doki(self.agenda_path, d['title'], d['author'], d['description'])
                full_p = os.path.join(self.agenda_path, meta['relative_path'])
                data = DokiManager.load_doki(full_p)
                cur_html = data.get('html', '')
                appended_html = cur_html + f"<br><h3>Texto Extraído ({self.item.get('name', 'Doc')} - Pág. {page_num})</h3><p>{text.replace(chr(10), '<br>')}</p>"
                DokiManager.save_doki(full_p, meta, appended_html, data.get('images', {}))
                QMessageBox.information(self, "Documento Creado", f"Se ha creado el documento Doki y se agregó el texto seleccionado:\n{meta['title']}")
        else:
            target_fp = file_map.get(choice)
            if target_fp and os.path.exists(target_fp):
                data = DokiManager.load_doki(target_fp)
                meta = data.get('metadata', {})
                cur_html = data.get('html', '')
                appended_html = cur_html + f"<br><h3>Texto Extraído ({self.item.get('name', 'Doc')} - Pág. {page_num})</h3><p>{text.replace(chr(10), '<br>')}</p>"
                DokiManager.save_doki(target_fp, meta, appended_html, data.get('images', {}))
                QMessageBox.information(self, "Texto Insertado", f"Texto insertado exitosamente en:\n{meta.get('title', choice)}")

    def _send_image_crop_to_doki(self, rect: QRect, page_num: int):
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        canvas = self.single_canvas if self.view_mode == 'single' else self.continuous_canvases[p_idx][1]
        if not canvas or not canvas.pixmap: return
        crop = canvas.pixmap.copy(rect)

        if not self.agenda_path:
            QMessageBox.warning(self, "Agenda no disponible", "No hay una ruta de agenda activa.")
            return

        from plugins.biblioteca.doki_editor import DokiManager, NewDokiDialog
        doki_dir = DokiManager.get_doki_dir(self.agenda_path)
        doki_files = [f for f in os.listdir(doki_dir) if f.endswith('.doki')]

        options = ["➕ Crear Nuevo Documento Doki..."]
        file_map = {}
        for fn in doki_files:
            fp = os.path.join(doki_dir, fn)
            try:
                data = DokiManager.load_doki(fp)
                t = data.get('metadata', {}).get('title', fn)
                label = f"📄 {t} ({fn})"
                options.append(label)
                file_map[label] = fp
            except Exception:
                pass

        choice, ok = QInputDialog.getItem(self, "Enviar Imagen a Documento Doki", "Selecciona el documento destino:", options, 0, False)
        if not ok or not choice: return

        # Convertir crop a PNG bytes y base64
        from PyQt6.QtCore import QBuffer, QIODevice
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        crop.save(buf, "PNG")
        img_bytes = bytes(buf.data())
        import base64
        b64 = base64.b64encode(img_bytes).decode('utf-8')
        data_uri = f"data:image/png;base64,{b64}"
        img_name = f"img_{QTime.currentTime().toString('hhmmsszzz')}_crop_p{page_num}.png"

        if choice == "➕ Crear Nuevo Documento Doki...":
            dlg = NewDokiDialog(parent=self)
            if dlg.exec():
                d = dlg.get_data()
                meta = DokiManager.create_empty_doki(self.agenda_path, d['title'], d['author'], d['description'])
                full_p = os.path.join(self.agenda_path, meta['relative_path'])
                data = DokiManager.load_doki(full_p)
                cur_html = data.get('html', '')
                imgs = data.get('images', {})
                imgs[f"images/{img_name}"] = img_bytes
                appended_html = cur_html + f"<br><h3>Figura Recortada ({self.item.get('name', 'Doc')} - Pág. {page_num})</h3><p><img src='{data_uri}' style='max-width:600px; border:1px solid #999;'/></p>"
                DokiManager.save_doki(full_p, meta, appended_html, imgs)
                QMessageBox.information(self, "Documento Creado", f"Se ha creado el documento Doki y se adjuntó la imagen:\n{meta['title']}")
        else:
            target_fp = file_map.get(choice)
            if target_fp and os.path.exists(target_fp):
                data = DokiManager.load_doki(target_fp)
                meta = data.get('metadata', {})
                cur_html = data.get('html', '')
                imgs = data.get('images', {})
                imgs[f"images/{img_name}"] = img_bytes
                appended_html = cur_html + f"<br><h3>Figura Recortada ({self.item.get('name', 'Doc')} - Pág. {page_num})</h3><p><img src='{data_uri}' style='max-width:600px; border:1px solid #999;'/></p>"
                DokiManager.save_doki(target_fp, meta, appended_html, imgs)
                QMessageBox.information(self, "Imagen Insertada", f"Imagen insertada exitosamente en:\n{meta.get('title', choice)}")

    def _save_image_crop(self, rect: QRect, page_num: int):
        p_idx = max(0, min(page_num - 1, len(self.doc) - 1))
        canvas = self.single_canvas if self.view_mode == 'single' else self.continuous_canvases[p_idx][1]
        if not canvas or not canvas.pixmap: return
        crop = canvas.pixmap.copy(rect)
        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Imagen Recortada", f"recorte_p{page_num}.png", "Imágenes (*.png *.jpg)")
        if filepath:
            crop.save(filepath)
            QMessageBox.information(self, "Guardado", f"Imagen guardada exitosamente en:\n{filepath}")

    # =========================================================================
    # EXTRACCIÓN Y CREACIÓN DE ARTÍCULOS
    # =========================================================================

    def _show_create_article_dialog(self):
        if not self.doc: return
        default_t = f"Artículo de {self.item.get('name', 'Documento')} (Págs. {self.current_page}-{min(self.current_page+3, self.total_pages)})"
        dlg = CreateArticleDialog(self.total_pages, self.current_page, default_title=default_t, parent=self)
        if dlg.exec():
            art_data = dlg.get_article_data()
            self._export_article_pdf(art_data)

    def _export_article_pdf(self, art_data: dict):
        if not self.doc or not self.agenda_path: return
        try:
            art_dir = os.path.join(self.agenda_path, 'biblioteca', 'Articulos')
            os.makedirs(art_dir, exist_ok=True)

            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', art_data.get('title', 'articulo')).lower()
            filename = f"art_{art_data.get('from_page')}_{art_data.get('to_page')}_{clean_name}.pdf"
            dest_path = os.path.join(art_dir, filename)

            new_doc = fitz.open()
            from_p = art_data.get('from_page', 1) - 1
            to_p = art_data.get('to_page', 1) - 1
            new_doc.insert_pdf(self.doc, from_page=from_p, to_page=to_p)
            new_doc.save(dest_path)
            new_doc.close()

            art_data['filename'] = filename
            art_data['relative_path'] = f"biblioteca/Articulos/{filename}"

            self.articles.append(art_data)
            self.item['articles'] = self.articles
            self._refresh_articles_list()
            self.articles_updated.emit(self.articles)

            QMessageBox.information(
                self, "Artículo Creado",
                f"El artículo se ha extraído y guardado como PDF:\n\n• Título: {art_data['title']}\n• Páginas: {art_data['from_page']} a {art_data['to_page']}\n• Archivo: {filename}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al Exportar", f"No se pudo crear el archivo PDF del artículo:\n{e}")

    def _refresh_articles_list(self):
        self.list_articles.clear()
        if not self.articles:
            item = QListWidgetItem("No hay artículos creados aún.\nUsa '📑 Crear Artículo' para extraer secciones en PDF.")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list_articles.addItem(item)
            return

        for art in self.articles:
            t = art.get('title', 'Artículo')
            fp = art.get('from_page', 1)
            tp = art.get('to_page', 1)
            fn = art.get('filename', '')
            item = QListWidgetItem(f"📄 {t}\n    Páginas: {fp} a {tp} ({tp - fp + 1} págs.)")
            item.setData(Qt.ItemDataRole.UserRole, art)
            self.list_articles.addItem(item)

    def _on_article_clicked(self, item: QListWidgetItem):
        art = item.data(Qt.ItemDataRole.UserRole)
        if not art: return
        rel_p = art.get('relative_path', '')
        full_p = os.path.join(self.agenda_path, rel_p) if self.agenda_path and rel_p else ""
        if os.path.exists(full_p):
            menu = QMenu(self)
            act_open = menu.addAction("📖 Abrir Archivo PDF del Artículo")
            act_jump = menu.addAction(f"⏩ Saltar a Página {art.get('from_page', 1)} en este documento")
            act_del = menu.addAction("🗑 Eliminar Artículo")
            action = menu.exec(QCursor.pos())

            if action == act_open:
                open_local_file(full_p)
            elif action == act_jump:
                self.current_page = art.get('from_page', 1)
                if self.view_mode == 'continuous':
                    self._scroll_to_page(self.current_page)
                else:
                    self._render_view()
            elif action == act_del:
                if QMessageBox.question(self, "Eliminar Artículo", f"¿Deseas eliminar el registro del artículo '{art.get('title')}'?") == QMessageBox.StandardButton.Yes:
                    self.articles.remove(art)
                    self.item['articles'] = self.articles
                    self._refresh_articles_list()
                    self.articles_updated.emit(self.articles)
        else:
            self.current_page = art.get('from_page', 1)
            if self.view_mode == 'continuous':
                self._scroll_to_page(self.current_page)
            else:
                self._render_view()
