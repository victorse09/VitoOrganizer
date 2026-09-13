# =============================================================================
# Vito Organizer v2.2 - Biblioteca: Creador y Editor de Documentos Doki (.doki)
# Formato contenedor propio (ZIP: metadata.json + content.html + content.xml + images/)
# Soporte de Alineación, Formato de Página (Carta, Oficio, A4, A3, A5), Salto de Página
# Exportación nativa a PDF, EPUB, OpenDocument (.odt) y XML
# =============================================================================

import os
import re
import json
import zipfile
import shutil
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QTime, QSize, QByteArray, QMarginsF
from PyQt6.QtGui import (
    QFont, QColor, QIcon, QPixmap, QPainter, QTextCharFormat, QTextBlockFormat,
    QTextCursor, QTextListFormat, QTextTableFormat, QTextLength, QImage,
    QDesktopServices, QClipboard, QGuiApplication, QPageSize, QPageLayout
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit,
    QLineEdit, QComboBox, QSplitter, QMessageBox, QFileDialog, QFrame,
    QDialog, QInputDialog, QColorDialog, QSpinBox, QScrollArea, QToolButton,
    QMenu, QTabWidget, QApplication, QButtonGroup
)
from PyQt6.QtPrintSupport import QPrinter

from plugins.biblioteca.doc_translator import get_themed_svg_icon
from tools.math_renderer import FormulaDialog, latex_to_base64_img_tag, convert_math_to_rendered_html


# =============================================================================
# 1. GESTOR DE ARCHIVOS Y EXPORTACIONES DOKI (DokiManager)
# =============================================================================

class DokiManager:
    """
    Gestiona la creación, lectura, empaquetado y exportación de archivos .doki
    (Contenedores ZIP con metadata.json, content.html, content.xml e images/).
    """

    @classmethod
    def get_doki_dir(cls, agenda_path: str) -> str:
        doki_dir = os.path.join(agenda_path, 'biblioteca', 'doki')
        os.makedirs(doki_dir, exist_ok=True)
        os.makedirs(os.path.join(doki_dir, 'exports'), exist_ok=True)
        return doki_dir

    @classmethod
    def create_empty_doki(cls, agenda_path: str, title: str, author: str = "", description: str = "",
                          page_format: str = "Carta", orientation: str = "portrait", margin: str = "normal") -> dict:
        doki_dir = cls.get_doki_dir(agenda_path)
        doc_id = f"doki_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}"
        clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title).lower()
        filename = f"{doc_id}_{clean_title}.doki"
        full_path = os.path.join(doki_dir, filename)

        metadata = {
            "id": doc_id,
            "title": title,
            "author": author or "Usuario",
            "created_at": QDate.currentDate().toString("yyyy-MM-dd"),
            "updated_at": QDate.currentDate().toString("yyyy-MM-dd"),
            "description": description,
            "filename": filename,
            "relative_path": f"biblioteca/doki/{filename}",
            "tags": ["doki", "documento"],
            "version": "1.0",
            "page_format": page_format,
            "orientation": orientation,
            "margin": margin,
            "exports": {}
        }

        initial_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #222; margin: 20px; }}
h1 {{ color: #1565C0; border-bottom: 2px solid #1565C0; padding-bottom: 6px; }}
h2 {{ color: #2E7D32; margin-top: 20px; }}
p {{ margin: 8px 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
th, td {{ border: 1px solid #CCC; padding: 8px; text-align: left; }}
th {{ background-color: #ECEFF1; }}
img {{ max-width: 100%; height: auto; }}
.page-break-marker {{ page-break-after: always; break-after: page; border-top: 2px dashed #1E88E5; border-bottom: 2px dashed #1E88E5; margin: 25px 0; text-align: center; color: #1565C0; font-size: 11px; font-weight: bold; background: #E3F2FD; padding: 6px; }}
.author-box {{ font-style: italic; color: #666; margin-bottom: 16px; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="author-box">Autor: {author or 'Usuario'} | Fecha: {metadata['created_at']} | Formato: {page_format} ({orientation})</div>
<p>{description or 'Escribe aquí el contenido de tu documento...'}</p>
</body>
</html>"""

        initial_xml = cls.generate_xml_content(metadata, initial_html)

        with zipfile.ZipFile(full_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('metadata.json', json.dumps(metadata, indent=2, ensure_ascii=False))
            z.writestr('content.html', initial_html)
            z.writestr('content.xml', initial_xml)

        return metadata

    @classmethod
    def load_doki(cls, file_path: str) -> dict:
        """Carga un archivo .doki y devuelve {metadata, html, xml, images}."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        result = {'metadata': {}, 'html': '', 'xml': '', 'images': {}}
        with zipfile.ZipFile(file_path, 'r') as z:
            if 'metadata.json' in z.namelist():
                result['metadata'] = json.loads(z.read('metadata.json').decode('utf-8'))
            if 'content.html' in z.namelist():
                result['html'] = z.read('content.html').decode('utf-8')
            if 'content.xml' in z.namelist():
                result['xml'] = z.read('content.xml').decode('utf-8')
            for name in z.namelist():
                if name.startswith('images/') and len(name) > 7:
                    result['images'][name] = z.read(name)

        return result

    @classmethod
    def save_doki(cls, file_path: str, metadata: dict, html_content: str, images: dict = None) -> None:
        """Guarda y comprime los datos del documento en el contenedor .doki."""
        metadata['updated_at'] = QDate.currentDate().toString("yyyy-MM-dd")
        xml_content = cls.generate_xml_content(metadata, html_content)

        temp_path = file_path + ".tmp"
        with zipfile.ZipFile(temp_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr('metadata.json', json.dumps(metadata, indent=2, ensure_ascii=False))
            z.writestr('content.html', html_content)
            z.writestr('content.xml', xml_content)
            if images:
                for img_name, img_bytes in images.items():
                    z.writestr(img_name, img_bytes)

        if os.path.exists(file_path):
            os.remove(file_path)
        shutil.move(temp_path, file_path)

    @classmethod
    def generate_xml_content(cls, metadata: dict, html_content: str) -> str:
        """Genera una representación semántica en XML del documento."""
        clean_body = re.sub(r'<head.*?</head>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        clean_body = re.sub(r'<!DOCTYPE.*?>', '', clean_body, flags=re.IGNORECASE)
        clean_body = clean_body.replace('<html>', '').replace('</html>', '').replace('<body>', '').replace('</body>', '').strip()

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<doki-document version="1.0">
  <metadata>
    <id>{metadata.get('id', '')}</id>
    <title><![CDATA[{metadata.get('title', '')}]]></title>
    <author><![CDATA[{metadata.get('author', '')}]]></author>
    <created-at>{metadata.get('created_at', '')}</created-at>
    <updated-at>{metadata.get('updated_at', '')}</updated-at>
    <page-format>{metadata.get('page_format', 'Carta')}</page-format>
    <orientation>{metadata.get('orientation', 'portrait')}</orientation>
    <margin>{metadata.get('margin', 'normal')}</margin>
    <description><![CDATA[{metadata.get('description', '')}]]></description>
  </metadata>
  <content>
    <![CDATA[
{clean_body}
    ]]>
  </content>
</doki-document>"""
        return xml

    # =========================================================================
    # EXPORTADORES A FORMATOS ESTÁNDAR
    # =========================================================================

    @classmethod
    def export_to_pdf(cls, doki_data: dict, output_pdf_path: str) -> str:
        """Exporta el documento Doki a formato PDF estándar de alta resolución respetando formato de página y saltos."""
        from PyQt6.QtGui import QTextDocument
        meta = doki_data.get('metadata', {})
        page_fmt_name = meta.get('page_format', 'Carta')
        orient_name = meta.get('orientation', 'portrait')
        margin_name = meta.get('margin', 'normal')

        # Mapeo de tamaño de página
        size_map = {
            'carta': QPageSize.PageSizeId.Letter,
            'letter': QPageSize.PageSizeId.Letter,
            'oficio': QPageSize.PageSizeId.Legal,
            'legal': QPageSize.PageSizeId.Legal,
            'a4': QPageSize.PageSizeId.A4,
            'a3': QPageSize.PageSizeId.A3,
            'a5': QPageSize.PageSizeId.A5,
        }
        clean_fmt = page_fmt_name.lower().split()[0].replace('(', '').replace(')', '')
        q_page_size_id = size_map.get(clean_fmt, QPageSize.PageSizeId.Letter)

        # Mapeo de orientación
        q_orient = QPageLayout.Orientation.Landscape if orient_name.lower() in ('horizontal', 'landscape') else QPageLayout.Orientation.Portrait

        # Mapeo de márgenes (mm)
        margin_val = 20.0
        if margin_name.lower() in ('estrecho', 'narrow'):
            margin_val = 10.0
        elif margin_name.lower() in ('ancho', 'wide'):
            margin_val = 30.0

        q_margins = QMarginsF(margin_val, margin_val, margin_val, margin_val)
        page_layout = QPageLayout(QPageSize(q_page_size_id), q_orient, q_margins, QPageLayout.Unit.Millimeter)

        html_src = doki_data.get('html', '')
        # Normalizar marcadores de salto de página para QTextDocument
        html_src = re.sub(r'<p[^>]*>.*?--- SALTO DE PÁGINA ---.*?</p>', r'<p style="page-break-before: always;"></p>', html_src, flags=re.IGNORECASE)
        html_src = re.sub(r'<div[^>]*class="page-break-marker"[^>]*>.*?</div>', r'<p style="page-break-before: always;"></p>', html_src, flags=re.IGNORECASE)

        doc = QTextDocument()
        doc.setHtml(html_src)

        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setPageLayout(page_layout)
        printer.setOutputFileName(output_pdf_path)
        doc.print(printer)
        return output_pdf_path

    @classmethod
    def export_to_epub(cls, doki_data: dict, output_epub_path: str) -> str:
        """Exporta el documento Doki a formato EPUB estándar."""
        meta = doki_data.get('metadata', {})
        title = meta.get('title', 'Documento Doki')
        author = meta.get('author', 'Usuario')
        doc_id = meta.get('id', 'doki_epub')

        html_body = doki_data.get('html', '')
        body_m = re.search(r'<body.*?>(.*?)</body>', html_body, re.DOTALL | re.IGNORECASE)
        body_inner = body_m.group(1) if body_m else html_body

        xhtml_content = f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{title}</title>
  <style>
    body {{ font-family: sans-serif; line-height: 1.6; padding: 1em; color: #111; }}
    h1 {{ color: #1565C0; }}
    h2 {{ color: #2E7D32; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #999; padding: 6px; }}
    th {{ background: #eee; }}
    .page-break-marker {{ page-break-after: always; break-after: page; display: block; height: 1px; border-top: 1px dashed #ccc; margin: 20px 0; }}
  </style>
</head>
<body>
{body_inner}
</body>
</html>"""

        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

        content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:identifier id="BookID">{doc_id}</dc:identifier>
    <dc:language>es</dc:language>
  </metadata>
  <manifest>
    <item id="page1" href="content.xhtml" media-type="application/xhtml+xml"/>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="page1"/>
  </spine>
</package>"""

        toc_ncx = f"""<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="{doc_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{title}</text></docTitle>
  <navMap>
    <navPoint id="navPoint-1" playOrder="1">
      <navLabel><text>{title}</text></navLabel>
      <content src="content.xhtml"/>
    </navPoint>
  </navMap>
</ncx>"""

        with zipfile.ZipFile(output_epub_path, 'w') as z:
            z.writestr('mimetype', 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
            z.writestr('META-INF/container.xml', container_xml, compress_type=zipfile.ZIP_DEFLATED)
            z.writestr('OEBPS/content.opf', content_opf, compress_type=zipfile.ZIP_DEFLATED)
            z.writestr('OEBPS/toc.ncx', toc_ncx, compress_type=zipfile.ZIP_DEFLATED)
            z.writestr('OEBPS/content.xhtml', xhtml_content, compress_type=zipfile.ZIP_DEFLATED)

        return output_epub_path

    @classmethod
    def export_to_odt(cls, doki_data: dict, output_odt_path: str) -> str:
        """Exporta el documento Doki a formato OpenDocument Text (.odt)."""
        meta = doki_data.get('metadata', {})
        title = meta.get('title', 'Documento Doki')
        author = meta.get('author', 'Usuario')

        html_text = re.sub(r'<.*?>', ' ', doki_data.get('html', ''))
        clean_text = "\n".join([line.strip() for line in html_text.splitlines() if line.strip()])

        odt_paragraphs = ""
        for line in clean_text.splitlines():
            odt_paragraphs += f'<text:p text:style-name="Standard">{line}</text:p>\n'

        manifest_xml = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
</manifest:manifest>"""

        meta_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:dc="http://purl.org/dc/elements/1.1/" office:version="1.2">
  <office:meta>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
  </office:meta>
</office:document-meta>"""

        content_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">
  <office:body>
    <office:text>
      <text:h text:style-name="Heading_20_1" text:outline-level="1">{title}</text:h>
      {odt_paragraphs}
    </office:text>
  </office:body>
</office:document-content>"""

        with zipfile.ZipFile(output_odt_path, 'w') as z:
            z.writestr('mimetype', 'application/vnd.oasis.opendocument.text', compress_type=zipfile.ZIP_STORED)
            z.writestr('META-INF/manifest.xml', manifest_xml, compress_type=zipfile.ZIP_DEFLATED)
            z.writestr('meta.xml', meta_xml, compress_type=zipfile.ZIP_DEFLATED)
            z.writestr('content.xml', content_xml, compress_type=zipfile.ZIP_DEFLATED)

        return output_odt_path

    @classmethod
    def export_to_xml(cls, doki_data: dict, output_xml_path: str) -> str:
        """Exporta el documento Doki a archivo XML semántico independiente."""
        xml = doki_data.get('xml', '')
        if not xml:
            xml = cls.generate_xml_content(doki_data.get('metadata', {}), doki_data.get('html', ''))

        with open(output_xml_path, 'w', encoding='utf-8') as f:
            f.write(xml)
        return output_xml_path


# =============================================================================
# 2. DIÁLOGO DE CREACIÓN RÁPIDA DE DOCUMENTO DOKI (NewDokiDialog)
# =============================================================================

class NewDokiDialog(QDialog):
    """Diálogo para crear un nuevo documento Doki con formato de página inicial."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo Documento Doki (.doki)")
        self.setMinimumWidth(480)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E2E; color: #CDD6F4; font-family: sans-serif; }
            QLabel { color: #CDD6F4; font-size: 12px; }
            QLineEdit, QTextEdit, QComboBox { background-color: #181825; color: #CDD6F4; border: 1px solid #313244; border-radius: 4px; padding: 6px; font-size: 12px; }
            QPushButton { background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; padding: 6px 14px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #45475A; color: #FFFFFF; }
            QPushButton#btnCreate { background-color: #1E88E5; color: #FFFFFF; border: none; }
            QPushButton#btnCreate:hover { background-color: #1565C0; }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 18, 18, 18)

        layout.addWidget(QLabel("<b>Título del Documento:</b>"))
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("Ej: Guía de Diseño de Fuentes Conmutadas, Apuntes de Microcontroladores...")
        layout.addWidget(self.txt_title)

        layout.addWidget(QLabel("<b>Autor:</b>"))
        self.txt_author = QLineEdit()
        self.txt_author.setPlaceholderText("Nombre del autor o departamento...")
        layout.addWidget(self.txt_author)

        # Formato de Página y Orientación
        fmt_layout = QHBoxLayout()
        fmt_layout.setSpacing(8)

        f_box = QVBoxLayout()
        f_box.addWidget(QLabel("<b>Tamaño de Página:</b>"))
        self.cb_page_format = QComboBox()
        self.cb_page_format.addItems(["Carta (Predeterminado)", "Oficio", "A4", "A3", "A5"])
        self.cb_page_format.setCurrentText("Carta (Predeterminado)")
        f_box.addWidget(self.cb_page_format)
        fmt_layout.addLayout(f_box)

        o_box = QVBoxLayout()
        o_box.addWidget(QLabel("<b>Orientación:</b>"))
        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["Vertical (Portrait)", "Horizontal (Landscape)"])
        self.cb_orientation.setCurrentText("Vertical (Portrait)")
        o_box.addWidget(self.cb_orientation)
        fmt_layout.addLayout(o_box)

        layout.addLayout(fmt_layout)

        layout.addWidget(QLabel("<b>Descripción o Resumen:</b>"))
        self.txt_desc = QTextEdit()
        self.txt_desc.setMaximumHeight(70)
        self.txt_desc.setPlaceholderText("Breve descripción del contenido del documento...")
        layout.addWidget(self.txt_desc)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        btn_cancel = QPushButton(" Cancelar")
        btn_cancel.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'close.svg'), '#CDD6F4', 14))
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)

        btn_create = QPushButton(" Crear Documento")
        btn_create.setIcon(get_themed_svg_icon(os.path.join(icons_dir, 'new_file.svg'), '#FFFFFF', 14))
        btn_create.setObjectName("btnCreate")
        btn_create.clicked.connect(self._validate_and_accept)
        btn_layout.addWidget(btn_create)
        layout.addLayout(btn_layout)

    def _validate_and_accept(self):
        title = self.txt_title.text().strip()
        if not title:
            QMessageBox.warning(self, "Título Requerido", "Por favor ingresa un título para el documento.")
            return
        self.accept()

    def get_data(self) -> dict:
        clean_fmt = "Carta" if "Carta" in self.cb_page_format.currentText() else self.cb_page_format.currentText()
        clean_orient = "portrait" if "Vertical" in self.cb_orientation.currentText() else "landscape"
        return {
            'title': self.txt_title.text().strip(),
            'author': self.txt_author.text().strip() or "Usuario",
            'page_format': clean_fmt,
            'orientation': clean_orient,
            'description': self.txt_desc.toPlainText().strip()
        }


# =============================================================================
# 3. EDITOR DE DOCUMENTOS DOKI EN MODO DE PÁGINA ÚNICA (DokiDocumentEditorWidget)
# =============================================================================

class DokiDocumentEditorWidget(QWidget):
    """Editor completo de documentos Doki en Modo de Página Única con suite de texto enriquecido y exportaciones."""

    back_requested = pyqtSignal()
    document_saved = pyqtSignal(dict)

    def __init__(self, doki_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.doki_item = doki_item
        self.agenda_path = agenda_path
        self.doki_data = {}
        self.images_cache = {}
        self.icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        self.setStyleSheet("""
            QWidget { background-color: #1E1E2E; color: #CDD6F4; font-family: sans-serif; }
            QFrame#toolbarFrame { background-color: #181825; border-bottom: 1px solid #313244; }
            QPushButton { background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; border-radius: 4px; padding: 4px 8px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #45475A; color: #FFFFFF; }
            QPushButton:checked { background-color: #1E88E5; color: #FFFFFF; border-color: #1565C0; }
            QPushButton#btnSave { background-color: #2E7D32; color: #FFFFFF; border: none; }
            QPushButton#btnSave:hover { background-color: #1B5E20; }
            QPushButton#btnExport { background-color: #D84315; color: #FFFFFF; border: none; }
            QPushButton#btnExport:hover { background-color: #BF360C; }
            QPushButton#btnPageBreak { background-color: #0288D1; color: #FFFFFF; border: none; font-weight: bold; }
            QPushButton#btnPageBreak:hover { background-color: #0277BD; }
            QLineEdit, QComboBox { background-color: #1E1E2E; color: #CDD6F4; border: 1px solid #313244; border-radius: 4px; padding: 2px 6px; font-size: 11px; }
            QTextEdit#dokiTextEdit { background-color: #FFFFFF; color: #111111; border: 1px solid #B0BEC5; border-radius: 6px; font-size: 14px; padding: 30px; line-height: 1.5; selection-background-color: #90CAF9; }
        """)

        self._setup_ui()
        self._load_document_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Barra de Herramientas Superior
        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("toolbarFrame")
        tb_layout = QVBoxLayout(self.toolbar_frame)
        tb_layout.setContentsMargins(8, 6, 8, 6)
        tb_layout.setSpacing(5)

        # Fila 1: Volver, Título, Autor, Guardar y Exportar
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.btn_back = QPushButton(" Volver a Biblioteca")
        self.btn_back.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'left.svg'), '#FFFFFF', 16))
        self.btn_back.setStyleSheet("QPushButton { background-color: #45475A; color: #FFFFFF; font-weight: bold; border-radius: 4px; padding: 4px 10px; } QPushButton:hover { background-color: #585B70; }")
        self.btn_back.clicked.connect(self._on_back_clicked)
        row1.addWidget(self.btn_back)

        row1.addWidget(QLabel("<b>Título:</b>"))
        self.txt_title = QLineEdit(self.doki_item.get('name', 'Documento Doki'))
        self.txt_title.setMinimumWidth(220)
        row1.addWidget(self.txt_title)

        row1.addWidget(QLabel("<b>Autor:</b>"))
        self.txt_author = QLineEdit(self.doki_item.get('author', 'Usuario'))
        self.txt_author.setFixedWidth(130)
        row1.addWidget(self.txt_author)

        row1.addStretch()

        # Botón Guardar
        self.btn_save = QPushButton(" Guardar (.doki)")
        self.btn_save.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'save.svg'), '#FFFFFF', 14))
        self.btn_save.setObjectName("btnSave")
        self.btn_save.clicked.connect(self._save_document)
        row1.addWidget(self.btn_save)

        # Menú Exportar
        self.btn_export = QPushButton(" Exportar ▼")
        self.btn_export.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'new_file.svg'), '#FFFFFF', 14))
        self.btn_export.setObjectName("btnExport")
        export_menu = QMenu(self)
        export_menu.addAction("📄 Exportar a PDF", self._export_pdf)
        export_menu.addAction("📚 Exportar a EPUB", self._export_epub)
        export_menu.addAction("📑 Exportar a OpenDocument (.odt)", self._export_odt)
        export_menu.addAction("⚙️ Exportar a XML", self._export_xml)
        self.btn_export.setMenu(export_menu)
        row1.addWidget(self.btn_export)

        tb_layout.addLayout(row1)

        # Fila 2: Formato de Página, Orientación, Márgenes, Salto de Página y Alineación
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        # Formato de Página
        row2.addWidget(QLabel("<b>Hoja:</b>"))
        self.cb_page_format = QComboBox()
        self.cb_page_format.addItems(["Carta (Predeterminado)", "Oficio", "A4", "A3", "A5"])
        self.cb_page_format.setFixedWidth(145)
        self.cb_page_format.currentTextChanged.connect(self._on_page_settings_changed)
        row2.addWidget(self.cb_page_format)

        # Orientación
        self.cb_orientation = QComboBox()
        self.cb_orientation.addItems(["Vertical", "Horizontal"])
        self.cb_orientation.setFixedWidth(85)
        self.cb_orientation.currentTextChanged.connect(self._on_page_settings_changed)
        row2.addWidget(self.cb_orientation)

        # Márgenes
        self.cb_margins = QComboBox()
        self.cb_margins.addItems(["Margen Normal (20mm)", "Margen Estrecho (10mm)", "Margen Ancho (30mm)"])
        self.cb_margins.setFixedWidth(140)
        self.cb_margins.currentTextChanged.connect(self._on_page_settings_changed)
        row2.addWidget(self.cb_margins)

        row2.addWidget(self._create_separator())

        # Salto de Página
        self.btn_page_break = QPushButton(" 📄 Salto de Página")
        self.btn_page_break.setObjectName("btnPageBreak")
        self.btn_page_break.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'document.svg'), '#FFFFFF', 13))
        self.btn_page_break.setToolTip("Insertar Salto de Página formal para la vista y exportación a PDF")
        self.btn_page_break.clicked.connect(self._insert_page_break)
        row2.addWidget(self.btn_page_break)

        row2.addWidget(self._create_separator())

        # Alineación
        row2.addWidget(QLabel("<b>Alineación:</b>"))
        self.align_group = QButtonGroup(self)

        self.btn_align_left = QPushButton("⇤ Izquierda")
        self.btn_align_left.setToolTip("Alinear a la Izquierda")
        self.btn_align_left.clicked.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignLeft))
        row2.addWidget(self.btn_align_left)

        self.btn_align_center = QPushButton("≡ Centro")
        self.btn_align_center.setToolTip("Centrar Texto")
        self.btn_align_center.clicked.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignCenter))
        row2.addWidget(self.btn_align_center)

        self.btn_align_right = QPushButton("⇥ Derecha")
        self.btn_align_right.setToolTip("Alinear a la Derecha")
        self.btn_align_right.clicked.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignRight))
        row2.addWidget(self.btn_align_right)

        self.btn_align_justify = QPushButton("≣ Justificado")
        self.btn_align_justify.setToolTip("Justificar Texto")
        self.btn_align_justify.clicked.connect(lambda: self.editor.setAlignment(Qt.AlignmentFlag.AlignJustify))
        row2.addWidget(self.btn_align_justify)

        row2.addStretch()

        self.btn_paste_clip = QPushButton(" Pegar Portapapeles")
        self.btn_paste_clip.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'paste.svg'), '#CDD6F4', 12))
        self.btn_paste_clip.clicked.connect(self._paste_clipboard)
        row2.addWidget(self.btn_paste_clip)

        tb_layout.addLayout(row2)

        # Fila 3: Estilos de Fuente y Elementos Avanzados (Tablas, Imágenes, Fórmulas)
        row3 = QHBoxLayout()
        row3.setSpacing(4)

        # Negrita, Cursiva, Subrayado, Tachado
        self.btn_bold = QPushButton("B")
        self.btn_bold.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_bold.setFixedSize(26, 26)
        self.btn_bold.clicked.connect(self._toggle_bold)
        row3.addWidget(self.btn_bold)

        self.btn_italic = QPushButton("I")
        self.btn_italic.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal, italic=True))
        self.btn_italic.setFixedSize(26, 26)
        self.btn_italic.clicked.connect(self._toggle_italic)
        row3.addWidget(self.btn_italic)

        self.btn_underline = QPushButton("U")
        self.btn_underline.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_underline.setFixedSize(26, 26)
        self.btn_underline.clicked.connect(self._toggle_underline)
        row3.addWidget(self.btn_underline)

        row3.addWidget(self._create_separator())

        # Tamaño de Fuente
        self.cb_font_size = QComboBox()
        self.cb_font_size.addItems(["9 pt", "10 pt", "11 pt", "12 pt", "14 pt", "16 pt", "18 pt", "24 pt", "32 pt"])
        self.cb_font_size.setCurrentText("12 pt")
        self.cb_font_size.setFixedWidth(75)
        self.cb_font_size.currentTextChanged.connect(self._on_font_size_changed)
        row3.addWidget(self.cb_font_size)

        # Color de Texto y Resaltador
        self.btn_color = QPushButton(" Color")
        self.btn_color.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'pencil.svg'), '#CDD6F4', 12))
        self.btn_color.clicked.connect(self._choose_color)
        row3.addWidget(self.btn_color)

        self.btn_bg_color = QPushButton(" Resaltar")
        self.btn_bg_color.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'filter.svg'), '#CDD6F4', 12))
        self.btn_bg_color.clicked.connect(self._choose_bg_color)
        row3.addWidget(self.btn_bg_color)

        row3.addWidget(self._create_separator())

        # Listas
        self.btn_bullet = QPushButton("• Viñetas")
        self.btn_bullet.clicked.connect(self._insert_bullet_list)
        row3.addWidget(self.btn_bullet)

        self.btn_numbered = QPushButton("1. Numerada")
        self.btn_numbered.clicked.connect(self._insert_numbered_list)
        row3.addWidget(self.btn_numbered)

        row3.addWidget(self._create_separator())

        # Inserción de Elementos Avanzados
        self.btn_table = QPushButton(" Tabla")
        self.btn_table.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'table_dark.svg'), '#CDD6F4', 12))
        self.btn_table.clicked.connect(self._insert_table_dialog)
        row3.addWidget(self.btn_table)

        self.btn_image = QPushButton(" Imagen")
        self.btn_image.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'image_file.svg'), '#CDD6F4', 12))
        self.btn_image.clicked.connect(self._insert_image)
        row3.addWidget(self.btn_image)

        self.btn_formula = QPushButton(" Fórmula LaTeX")
        self.btn_formula.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'calculator.svg'), '#CDD6F4', 12))
        self.btn_formula.clicked.connect(self._insert_formula)
        row3.addWidget(self.btn_formula)

        row3.addStretch()

        tb_layout.addLayout(row3)
        main_layout.addWidget(self.toolbar_frame)

        # 2. Área Central del Editor de Texto (Hoja de Documento física con medidas y márgenes reales)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #181825; border: none; }")

        self.paper_container = QWidget()
        self.paper_container.setStyleSheet("background-color: #181825;")
        self.paper_layout = QVBoxLayout(self.paper_container)
        self.paper_layout.setContentsMargins(40, 30, 40, 30)
        self.paper_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.editor = QTextEdit()
        self.editor.setObjectName("dokiTextEdit")

        # Configurar paleta clara de hoja de papel física
        from PyQt6.QtGui import QPalette
        pal = self.editor.palette()
        pal.setColor(QPalette.ColorRole.Base, QColor("#FFFFFF"))
        pal.setColor(QPalette.ColorRole.Text, QColor("#111111"))
        pal.setColor(QPalette.ColorRole.Window, QColor("#FFFFFF"))
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#111111"))
        pal.setColor(QPalette.ColorRole.Highlight, QColor("#90CAF9"))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#000000"))
        self.editor.setPalette(pal)
        self.editor.viewport().setPalette(pal)

        self.editor.setStyleSheet("""
            QTextEdit#dokiTextEdit {
                background-color: #FFFFFF;
                color: #111111;
                border: 2px solid #90A4AE;
                border-radius: 4px;
                padding: 40px 45px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                selection-background-color: #90CAF9;
                selection-color: #000000;
            }
        """)

        self.editor.document().setDefaultStyleSheet("""
            body { background-color: #FFFFFF; color: #111111; font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; }
            h1 { color: #1565C0; border-bottom: 2px solid #1565C0; padding-bottom: 4px; }
            h2 { color: #2E7D32; margin-top: 16px; }
            h3 { color: #C2185B; margin-top: 12px; }
            p, span, div, li, td, th { color: #111111; }
            table { border-collapse: collapse; width: 100%; margin: 12px 0; }
            th, td { border: 1px solid #B0BEC5; padding: 6px 10px; }
            th { background-color: #ECEFF1; color: #111111; }
            .author-box { color: #555555; font-style: italic; margin-bottom: 14px; }
            .page-break-marker { color: #1565C0; font-weight: bold; background: #E3F2FD; }
        """)

        self.paper_layout.addWidget(self.editor, alignment=Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.paper_container)
        main_layout.addWidget(self.scroll_area, 1)

        self._update_paper_geometry()

    def _create_separator(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("background-color: #313244; max-width: 1px; margin: 2px 4px;")
        return sep

    def _load_document_data(self):
        rel_path = self.doki_item.get('relative_path', '')
        full_path = os.path.join(self.agenda_path, rel_path) if self.agenda_path and rel_path else ""

        if os.path.exists(full_path):
            try:
                self.doki_data = DokiManager.load_doki(full_path)
                meta = self.doki_data.get('metadata', {})
                self.txt_title.setText(meta.get('title', self.doki_item.get('name', '')))
                self.txt_author.setText(meta.get('author', 'Usuario'))

                # Cargar configuración de hoja
                pf = meta.get('page_format', 'Carta')
                if pf == 'Carta': self.cb_page_format.setCurrentText("Carta (Predeterminado)")
                elif pf in ("Oficio", "A4", "A3", "A5"): self.cb_page_format.setCurrentText(pf)

                ori = meta.get('orientation', 'portrait')
                self.cb_orientation.setCurrentText("Horizontal" if ori in ('horizontal', 'landscape') else "Vertical")

                marg = meta.get('margin', 'normal')
                if marg == 'narrow': self.cb_margins.setCurrentText("Margen Estrecho (10mm)")
                elif marg == 'wide': self.cb_margins.setCurrentText("Margen Ancho (30mm)")
                else: self.cb_margins.setCurrentText("Margen Normal (20mm)")

                self.editor.setHtml(self.doki_data.get('html', ''))
                self.images_cache = self.doki_data.get('images', {})
                self._update_paper_geometry()
            except Exception as e:
                QMessageBox.critical(self, "Error al cargar .doki", f"No se pudo leer el archivo doki:\n{e}")
        else:
            # Documento nuevo
            self.editor.setHtml(f"<h1>{self.txt_title.text()}</h1><p>Comienza a escribir tu documento técnico aquí...</p>")
            self._update_paper_geometry()

    def _on_page_settings_changed(self):
        self._update_paper_geometry()

    def _update_paper_geometry(self):
        """Ajusta las dimensiones de la hoja visual según el tamaño de página y orientación."""
        fmt_text = self.cb_page_format.currentText()
        is_landscape = self.cb_orientation.currentText() == "Horizontal"

        # Dimensiones base en pixeles proporcionales para visualización
        if "Carta" in fmt_text:
            w, h = (960, 750) if is_landscape else (750, 960)
        elif "Oficio" in fmt_text:
            w, h = (1080, 750) if is_landscape else (750, 1080)
        elif "A4" in fmt_text:
            w, h = (980, 700) if is_landscape else (700, 980)
        elif "A3" in fmt_text:
            w, h = (1200, 850) if is_landscape else (850, 1200)
        elif "A5" in fmt_text:
            w, h = (750, 530) if is_landscape else (530, 750)
        else:
            w, h = (750, 960)

        self.editor.setMinimumWidth(w)
        self.editor.setMaximumWidth(w)
        self.editor.setMinimumHeight(h)

    def _insert_page_break(self):
        """Inserta un salto de página formal en el documento."""
        cursor = self.editor.textCursor()
        cursor.insertHtml('<p style="page-break-before: always; border-top: 2px dashed #1E88E5; padding-top: 8px; margin-top: 20px; color: #1565C0; font-size: 11px; font-weight: bold; text-align: center;">--- SALTO DE PÁGINA ---</p><p><br></p>')
        self.editor.setTextCursor(cursor)

    def append_text_or_translation(self, text: str, heading: str = ""):
        """Permite insertar texto o traducciones directamente desde otros módulos."""
        cursor = self.editor.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        if heading:
            cursor.insertHtml(f"<h3>{heading}</h3>")
        cursor.insertHtml(f"<p>{text.replace(chr(10), '<br>')}</p><br>")
        self.editor.setTextCursor(cursor)

    # =========================================================================
    # ACCIONES DE FORMATO DE TEXTO
    # =========================================================================

    def _toggle_bold(self):
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Weight.Normal if self.editor.fontWeight() > QFont.Weight.Normal else QFont.Weight.Bold)
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_italic(self):
        fmt = QTextCharFormat()
        fmt.setFontItalic(not self.editor.fontItalic())
        self.editor.mergeCurrentCharFormat(fmt)

    def _toggle_underline(self):
        fmt = QTextCharFormat()
        fmt.setFontUnderline(not self.editor.fontUnderline())
        self.editor.mergeCurrentCharFormat(fmt)

    def _on_font_size_changed(self, text: str):
        try:
            sz = int(text.replace(' pt', ''))
            fmt = QTextCharFormat()
            fmt.setFontPointSize(sz)
            self.editor.mergeCurrentCharFormat(fmt)
        except ValueError:
            pass

    def _choose_color(self):
        col = QColorDialog.getColor(Qt.GlobalColor.black, self, "Seleccionar Color de Texto")
        if col.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(col)
            self.editor.mergeCurrentCharFormat(fmt)

    def _choose_bg_color(self):
        col = QColorDialog.getColor(QColor("#FFF9C4"), self, "Seleccionar Color de Resaltado")
        if col.isValid():
            fmt = QTextCharFormat()
            fmt.setBackground(col)
            self.editor.mergeCurrentCharFormat(fmt)

    def _insert_bullet_list(self):
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDisc)

    def _insert_numbered_list(self):
        cursor = self.editor.textCursor()
        cursor.insertList(QTextListFormat.Style.ListDecimal)

    def _insert_table_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Insertar Tabla")
        d_layout = QVBoxLayout(dlg)
        
        row_l = QHBoxLayout()
        row_l.addWidget(QLabel("Filas:"))
        spn_rows = QSpinBox()
        spn_rows.setRange(1, 50)
        spn_rows.setValue(3)
        row_l.addWidget(spn_rows)

        row_l.addWidget(QLabel("Columnas:"))
        spn_cols = QSpinBox()
        spn_cols.setRange(1, 20)
        spn_cols.setValue(3)
        row_l.addWidget(spn_cols)
        d_layout.addLayout(row_l)

        btn_box = QHBoxLayout()
        btn_ok = QPushButton("Insertar")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(dlg.reject)
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_ok)
        d_layout.addLayout(btn_box)

        if dlg.exec():
            rows = spn_rows.value()
            cols = spn_cols.value()
            cursor = self.editor.textCursor()
            table_fmt = QTextTableFormat()
            table_fmt.setBorder(1)
            table_fmt.setBorderStyle(QTextTableFormat.BorderStyle.BorderStyle_Solid)
            table_fmt.setCellPadding(6)
            table_fmt.setCellSpacing(0)
            cursor.insertTable(rows, cols, table_fmt)

    def _insert_image(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.webp *.avif *.svg)")
        if filepath:
            try:
                with open(filepath, 'rb') as f:
                    img_bytes = f.read()

                img_filename = f"img_{QTime.currentTime().toString('hhmmsszzz')}_{os.path.basename(filepath)}"
                self.images_cache[f"images/{img_filename}"] = img_bytes

                import base64
                ext = os.path.splitext(filepath)[1].lower().replace('.', '')
                if ext == 'jpg': ext = 'jpeg'
                b64 = base64.b64encode(img_bytes).decode('utf-8')
                data_uri = f"data:image/{ext};base64,{b64}"

                cursor = self.editor.textCursor()
                cursor.insertHtml(f'<img src="{data_uri}" style="max-width: 600px; border: 1px solid #CCC; margin: 8px 0;" /><br>')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen: {e}")

    def _insert_formula(self):
        dlg = FormulaDialog(parent=self)
        if dlg.exec():
            html_img = dlg.get_formula_html()
            if html_img:
                cursor = self.editor.textCursor()
                cursor.insertHtml(html_img)

    def _paste_clipboard(self):
        cb = QGuiApplication.clipboard()
        text = cb.text()
        if text:
            self.editor.insertPlainText(text)

    # =========================================================================
    # GUARDADO Y EXPORTACIONES
    # =========================================================================

    def _save_document(self) -> bool:
        if not self.agenda_path: return False
        try:
            doki_dir = DokiManager.get_doki_dir(self.agenda_path)
            rel_path = self.doki_item.get('relative_path', '')
            full_path = os.path.join(self.agenda_path, rel_path) if rel_path else ""

            if not full_path or not os.path.exists(os.path.dirname(full_path)):
                clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', self.txt_title.text().strip()).lower()
                doc_id = self.doki_item.get('id', f"doki_{QDate.currentDate().toString('yyyyMMdd')}_{QTime.currentTime().toString('hhmmsszzz')}")
                filename = f"{doc_id}_{clean_title}.doki"
                full_path = os.path.join(doki_dir, filename)
                self.doki_item['filename'] = filename
                self.doki_item['relative_path'] = f"biblioteca/doki/{filename}"

            meta = self.doki_data.get('metadata', {})
            meta['title'] = self.txt_title.text().strip()
            meta['author'] = self.txt_author.text().strip()
            meta['description'] = self.doki_item.get('description', '')

            # Guardar configuración de hoja
            fmt_text = self.cb_page_format.currentText()
            meta['page_format'] = "Carta" if "Carta" in fmt_text else fmt_text
            meta['orientation'] = "landscape" if self.cb_orientation.currentText() == "Horizontal" else "portrait"
            
            marg_text = self.cb_margins.currentText()
            if "Estrecho" in marg_text: meta['margin'] = "narrow"
            elif "Ancho" in marg_text: meta['margin'] = "wide"
            else: meta['margin'] = "normal"

            self.doki_item['name'] = meta['title']
            self.doki_item['author'] = meta['author']

            html_content = self.editor.toHtml()
            DokiManager.save_doki(full_path, meta, html_content, self.images_cache)

            self.doki_data['metadata'] = meta
            self.doki_data['html'] = html_content
            self.document_saved.emit(self.doki_item)

            QMessageBox.information(self, "Guardado", f"Documento Doki guardado exitosamente en:\n{full_path}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error al Guardar", f"No se pudo guardar el archivo .doki:\n{e}")
            return False

    def _export_pdf(self):
        if not self._save_document(): return
        exp_dir = os.path.join(self.agenda_path, 'biblioteca', 'doki', 'exports')
        os.makedirs(exp_dir, exist_ok=True)
        clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', self.txt_title.text().strip()).lower()
        default_fn = f"{clean_title}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar a PDF", os.path.join(exp_dir, default_fn), "Archivos PDF (*.pdf)")
        if filepath:
            try:
                DokiManager.export_to_pdf(self.doki_data, filepath)
                QMessageBox.information(self, "PDF Exportado", f"Documento exportado exitosamente como PDF:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar PDF", str(e))

    def _export_epub(self):
        if not self._save_document(): return
        exp_dir = os.path.join(self.agenda_path, 'biblioteca', 'doki', 'exports')
        os.makedirs(exp_dir, exist_ok=True)
        clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', self.txt_title.text().strip()).lower()
        default_fn = f"{clean_title}.epub"
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar a EPUB", os.path.join(exp_dir, default_fn), "Libros Digitales EPUB (*.epub)")
        if filepath:
            try:
                DokiManager.export_to_epub(self.doki_data, filepath)
                QMessageBox.information(self, "EPUB Exportado", f"Documento exportado exitosamente como EPUB:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar EPUB", str(e))

    def _export_odt(self):
        if not self._save_document(): return
        exp_dir = os.path.join(self.agenda_path, 'biblioteca', 'doki', 'exports')
        os.makedirs(exp_dir, exist_ok=True)
        clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', self.txt_title.text().strip()).lower()
        default_fn = f"{clean_title}.odt"
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar a OpenDocument Text (.odt)", os.path.join(exp_dir, default_fn), "OpenDocument Text (*.odt)")
        if filepath:
            try:
                DokiManager.export_to_odt(self.doki_data, filepath)
                QMessageBox.information(self, "OpenDocument Exportado", f"Documento exportado exitosamente como OpenDocument (.odt):\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar ODT", str(e))

    def _export_xml(self):
        if not self._save_document(): return
        exp_dir = os.path.join(self.agenda_path, 'biblioteca', 'doki', 'exports')
        os.makedirs(exp_dir, exist_ok=True)
        clean_title = re.sub(r'[^a-zA-Z0-9_-]', '_', self.txt_title.text().strip()).lower()
        default_fn = f"{clean_title}.xml"
        filepath, _ = QFileDialog.getSaveFileName(self, "Exportar a XML", os.path.join(exp_dir, default_fn), "Archivos XML (*.xml)")
        if filepath:
            try:
                DokiManager.export_to_xml(self.doki_data, filepath)
                QMessageBox.information(self, "XML Exportado", f"Documento exportado exitosamente como XML:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error al Exportar XML", str(e))

    def _on_back_clicked(self):
        self.back_requested.emit()
