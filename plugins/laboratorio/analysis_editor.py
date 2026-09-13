import os
import shutil
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QSize
from PyQt6.QtGui import QIcon, QPixmap, QDesktopServices, QTextCursor, QTextCharFormat, QFont, QTextListFormat, QColor
from plugins.plugin_base import open_local_file, load_image_pixmap, IMAGE_EXTENSIONS, IMAGE_FILE_FILTER
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QFileDialog, QMessageBox, QFrame, QToolBar, QColorDialog, QDialog
)
from tools.math_renderer import MathRichTextEdit, FormulaDialog

class CalculationEditorWidget(QWidget):
    """
    Widget de pantalla completa (single_page) para editar un Cálculo de Análisis.
    Soporta: Texto plano, Imagen, Markdown (Texto Enriquecido).
    """
    
    close_requested = pyqtSignal() # Emitido cuando el usuario presiona "Volver"
    saved = pyqtSignal() # Emitido al guardar

    def __init__(self, calculation: dict, analysis_item: dict, agenda_path: str, sub_folder: str = 'analisis', parent=None):
        super().__init__(parent)
        self.calculation = calculation
        self.analysis_item = analysis_item
        self.agenda_path = agenda_path
        self.sub_folder = sub_folder
        
        self.calc_type = calculation.get('type', 'Texto')
        self.calc_id = calculation.get('id', 'unknown')
        
        item_name = analysis_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        # Ruta de almacenamiento de assets según el módulo (analisis o desarrollo)
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', self.sub_folder, safe_name, self.calc_id)
        
        # Migración de archivos de proyecto que fueron guardados por error en laboratorio/analisis/
        if self.sub_folder == 'desarrollo':
            misplaced_dir = os.path.join(self.agenda_path, 'laboratorio', 'analisis', safe_name, self.calc_id)
            if os.path.exists(misplaced_dir) and not os.path.exists(self.storage_dir):
                os.makedirs(os.path.dirname(self.storage_dir), exist_ok=True)
                try: shutil.move(misplaced_dir, self.storage_dir)
                except Exception as e: print(f"Error moving misplaced project dir: {e}")

        # Migración de rutas antiguas (si existían carpetas con id o data/)
        old_id_dir = os.path.join(self.agenda_path, 'laboratorio', self.sub_folder, analysis_item.get('id', ''), self.calc_id)
        old_data_dir = os.path.join(self.agenda_path, 'data', 'laboratorio', self.sub_folder, analysis_item.get('id', ''), self.calc_id)
        
        if not os.path.exists(self.storage_dir):
            if os.path.exists(old_id_dir):
                os.makedirs(os.path.dirname(self.storage_dir), exist_ok=True)
                try: shutil.move(old_id_dir, self.storage_dir)
                except Exception: pass
            elif os.path.exists(old_data_dir):
                os.makedirs(os.path.dirname(self.storage_dir), exist_ok=True)
                try: shutil.move(old_data_dir, self.storage_dir)
                except Exception: pass

        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(15)

        # Barra superior con título y botones
        top_bar = QHBoxLayout()
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        
        self.btn_back = QPushButton(" Volver")
        icon_back = os.path.join(icons_dir, 'left.svg')
        if os.path.exists(icon_back):
            self.btn_back.setIcon(QIcon(icon_back))
            self.btn_back.setIconSize(QSize(14, 14))
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Análisis y Pruebas: <b>{self.calculation.get('name', 'Sin nombre')}</b> ({self.calc_type})")
        title_lbl.setStyleSheet("font-size: 16px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setIcon(QIcon(os.path.join(icons_dir, 'save.svg')))
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Contenedor principal de edición
        self.editor_container = QFrame()
        self.editor_container.setStyleSheet("QFrame { background-color: rgba(255, 255, 255, 0.85); border: 1px solid #CCC; border-radius: 8px; }")
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(20, 20, 20, 20)
        editor_layout.setSpacing(10)

        if self.calc_type == 'Texto':
            self.text_editor = QTextEdit()
            self.text_editor.setStyleSheet("QTextEdit { background: transparent; border: none; font-size: 14px; color: #111; }")
            self.text_editor.setPlaceholderText("Escribe el texto de tu análisis aquí...")
            editor_layout.addWidget(self.text_editor)
            
        elif self.calc_type == 'Imagen':
            img_layout = QVBoxLayout()
            self.img_preview = QLabel("No hay imagen cargada")
            self.img_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.img_preview.setStyleSheet("QLabel { background-color: #EEE; border: 1px dashed #AAA; border-radius: 4px; color: #777; }")
            self.img_preview.setMinimumHeight(300)
            img_layout.addWidget(self.img_preview, 1)
            
            btn_upload = QPushButton(" Cargar / Cambiar Imagen")
            icon_upload = os.path.join(icons_dir, 'image_file.svg')
            if os.path.exists(icon_upload):
                btn_upload.setIcon(QIcon(icon_upload))
                btn_upload.setIconSize(QSize(16, 16))
            btn_upload.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #1976D2; color: white; }")
            btn_upload.clicked.connect(self._upload_image)
            img_layout.addWidget(btn_upload, alignment=Qt.AlignmentFlag.AlignCenter)
            
            editor_layout.addLayout(img_layout)
            self.current_image_path = None
            
        elif self.calc_type in ('Markdown (MD)', 'Texto Enriquecido', 'Texto Enriquecido (RTF)', 'Documento'):
            # Barra de herramientas RTF enriquecida
            toolbar_layout = QHBoxLayout()
            toolbar_layout.setSpacing(5)
            
            btn_style = "color: #111111; background-color: #E0E0E0; border: 1px solid #999999; padding: 4px 8px; border-radius: 4px; font-size: 12px;"
            btn_hover = "QPushButton:hover { background-color: #CCCCCC; }"
            
            btn_bold = QPushButton("B")
            icon_bold = os.path.join(icons_dir, 'bold_dark.svg')
            if os.path.exists(icon_bold):
                btn_bold.setIcon(QIcon(icon_bold))
                btn_bold.setIconSize(QSize(14, 14))
                btn_bold.setText("")
            btn_bold.setToolTip("Texto en Negrita")
            btn_bold.setStyleSheet(f"QPushButton {{ font-weight: bold; {btn_style} }} {btn_hover}")
            btn_bold.clicked.connect(lambda: self._set_format('bold'))
            toolbar_layout.addWidget(btn_bold)
            
            btn_italic = QPushButton("I")
            icon_italic = os.path.join(icons_dir, 'italic_dark.svg')
            if os.path.exists(icon_italic):
                btn_italic.setIcon(QIcon(icon_italic))
                btn_italic.setIconSize(QSize(14, 14))
                btn_italic.setText("")
            btn_italic.setToolTip("Texto en Cursiva")
            btn_italic.setStyleSheet(f"QPushButton {{ font-style: italic; {btn_style} }} {btn_hover}")
            btn_italic.clicked.connect(lambda: self._set_format('italic'))
            toolbar_layout.addWidget(btn_italic)
            
            btn_ul = QPushButton(" Lista")
            icon_ul = os.path.join(icons_dir, 'tasks_dark.svg')
            if os.path.exists(icon_ul):
                btn_ul.setIcon(QIcon(icon_ul))
                btn_ul.setIconSize(QSize(14, 14))
            btn_ul.setToolTip("Insertar Lista")
            btn_ul.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_ul.clicked.connect(self._insert_list)
            toolbar_layout.addWidget(btn_ul)

            btn_color = QPushButton(" Color")
            icon_color = os.path.join(icons_dir, 'pencil_dark.svg')
            if os.path.exists(icon_color):
                btn_color.setIcon(QIcon(icon_color))
                btn_color.setIconSize(QSize(14, 14))
            btn_color.setToolTip("Cambiar color de texto")
            btn_color.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_color.clicked.connect(self._change_text_color)
            toolbar_layout.addWidget(btn_color)

            btn_insert_img = QPushButton(" Imagen")
            icon_img = os.path.join(icons_dir, 'image_file_dark.svg')
            if os.path.exists(icon_img):
                btn_insert_img.setIcon(QIcon(icon_img))
                btn_insert_img.setIconSize(QSize(14, 14))
            btn_insert_img.setToolTip("Insertar imagen en documento")
            btn_insert_img.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_insert_img.clicked.connect(self._insert_image_in_doc)
            toolbar_layout.addWidget(btn_insert_img)

            btn_table = QPushButton(" Tabla")
            icon_table = os.path.join(icons_dir, 'table_dark.svg')
            if os.path.exists(icon_table):
                btn_table.setIcon(QIcon(icon_table))
                btn_table.setIconSize(QSize(14, 14))
            btn_table.setToolTip("Insertar Tabla")
            btn_table.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_table.clicked.connect(self._insert_table)
            toolbar_layout.addWidget(btn_table)

            btn_code = QPushButton(" Código")
            icon_code = os.path.join(icons_dir, 'software_dark.svg')
            if os.path.exists(icon_code):
                btn_code.setIcon(QIcon(icon_code))
                btn_code.setIconSize(QSize(14, 14))
            btn_code.setToolTip("Insertar bloque de Código")
            btn_code.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_code.clicked.connect(self._insert_code_block)
            toolbar_layout.addWidget(btn_code)

            btn_formula = QPushButton(" Fórmula")
            icon_formula = os.path.join(icons_dir, 'ruler_dark.svg')
            if os.path.exists(icon_formula):
                btn_formula.setIcon(QIcon(icon_formula))
                btn_formula.setIconSize(QSize(14, 14))
            btn_formula.setToolTip("Insertar o editar fórmula matemática (LaTeX)")
            btn_formula.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_formula.clicked.connect(self._insert_formula_dialog)
            toolbar_layout.addWidget(btn_formula)

            btn_render_math = QPushButton(" Convertir LaTeX")
            icon_sync = os.path.join(icons_dir, 'sync.svg')
            if os.path.exists(icon_sync):
                btn_render_math.setIcon(QIcon(icon_sync))
                btn_render_math.setIconSize(QSize(14, 14))
            btn_render_math.setToolTip("Convertir fórmulas LaTeX ($$...$$ o $...$) en el documento a gráficos")
            btn_render_math.setStyleSheet(f"QPushButton {{ {btn_style} }} {btn_hover}")
            btn_render_math.clicked.connect(self._render_all_math)
            toolbar_layout.addWidget(btn_render_math)
            
            toolbar_layout.addStretch()
            editor_layout.addLayout(toolbar_layout)
            
            self.rich_editor = MathRichTextEdit()
            self.rich_editor.setStyleSheet("QTextEdit { background: transparent; border: 1px solid #CCC; font-size: 14px; color: #111; }")
            self.rich_editor.setPlaceholderText("Escribe tu documento en texto enriquecido...")
            editor_layout.addWidget(self.rich_editor)

        layout.addWidget(self.editor_container, 1)

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _load_content(self):
        if not os.path.exists(self.storage_dir):
            return
            
        if self.calc_type == 'Texto':
            file_path = os.path.join(self.storage_dir, 'content.txt')
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        self.text_editor.setPlainText(f.read())
                except Exception as e:
                    print(f"Error loading text: {e}")
                    
        elif self.calc_type == 'Imagen':
            # Find first image
            for f in os.listdir(self.storage_dir):
                if f.lower().endswith(IMAGE_EXTENSIONS):
                    self.current_image_path = os.path.join(self.storage_dir, f)
                    self._update_image_preview()
                    break
                    
        elif self.calc_type in ('Markdown (MD)', 'Texto Enriquecido', 'Texto Enriquecido (RTF)', 'Documento'):
            file_html = os.path.join(self.storage_dir, 'content.html')
            file_xml = os.path.join(self.storage_dir, 'content.xml')
            file_md = os.path.join(self.storage_dir, 'content.md')
            
            if os.path.exists(file_html):
                try:
                    with open(file_html, 'r', encoding='utf-8') as f:
                        self.rich_editor.setHtml(f.read())
                except Exception as e:
                    print(f"Error loading html: {e}")
            elif os.path.exists(file_xml):
                try:
                    with open(file_xml, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if '<document>' in content:
                            content = content.split('<document>', 1)[1].rsplit('</document>', 1)[0]
                        self.rich_editor.setHtml(content)
                except Exception as e:
                    print(f"Error loading xml: {e}")
            elif os.path.exists(file_md):
                try:
                    with open(file_md, 'r', encoding='utf-8') as f:
                        self.rich_editor.setMarkdown(f.read())
                except Exception as e:
                    print(f"Error loading md: {e}")

    def _save_content(self):
        self._ensure_storage_dir()
        
        try:
            if self.calc_type == 'Texto':
                file_path = os.path.join(self.storage_dir, 'content.txt')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.text_editor.toPlainText())
                    
            elif self.calc_type == 'Imagen':
                # Already saved when uploaded
                pass
                
            elif self.calc_type in ('Markdown (MD)', 'Texto Enriquecido', 'Texto Enriquecido (RTF)', 'Documento'):
                file_html = os.path.join(self.storage_dir, 'content.html')
                file_xml = os.path.join(self.storage_dir, 'content.xml')
                file_md = os.path.join(self.storage_dir, 'content.md')
                
                html_data = self.rich_editor.toHtml()
                
                # 1. Guardar archivo HTML primario para fidelidad 100% de procesador de texto (colores, fuentes, tablas, imágenes, bloques)
                with open(file_html, 'w', encoding='utf-8') as f:
                    f.write(html_data)
                    
                # 2. Guardar archivo XML para compatibilidad
                with open(file_xml, 'w', encoding='utf-8') as f:
                    f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<document>\n{html_data}\n</document>')
                    
                # 3. Guardar copia Markdown .md
                try:
                    with open(file_md, 'w', encoding='utf-8') as f:
                        f.write(self.rich_editor.toMarkdown())
                except Exception:
                    pass
                    
            QMessageBox.information(self, "Éxito", "Cálculo guardado correctamente.")
            self.saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el contenido:\n{str(e)}")

    def _upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Imagen", "", IMAGE_FILE_FILTER)
        if file_path:
            self._ensure_storage_dir()
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.storage_dir, filename)
            
            try:
                # Remove old images if any
                for f in os.listdir(self.storage_dir):
                    if f.lower().endswith(IMAGE_EXTENSIONS):
                        os.remove(os.path.join(self.storage_dir, f))
                
                shutil.copy2(file_path, dest_path)
                self.current_image_path = dest_path
                self._update_image_preview()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al copiar la imagen:\n{str(e)}")

    def _update_image_preview(self):
        if self.current_image_path and os.path.exists(self.current_image_path):
            pixmap = load_image_pixmap(self.current_image_path)
            # Scale to fit label roughly
            scaled_pixmap = pixmap.scaled(self.img_preview.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.img_preview.setPixmap(scaled_pixmap)
            self.img_preview.setText("")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.calc_type == 'Imagen' and hasattr(self, 'current_image_path'):
            self._update_image_preview()

    # Formatos de Texto Enriquecido
    def _set_format(self, fmt):
        if not hasattr(self, 'rich_editor'): return
        cursor = self.rich_editor.textCursor()
        format = QTextCharFormat()
        if fmt == 'bold':
            format.setFontWeight(QFont.Weight.Bold if cursor.charFormat().fontWeight() != QFont.Weight.Bold else QFont.Weight.Normal)
        elif fmt == 'italic':
            format.setFontItalic(not cursor.charFormat().fontItalic())
        cursor.mergeCharFormat(format)
        self.rich_editor.setTextCursor(cursor)

    def _insert_list(self):
        if not hasattr(self, 'rich_editor'): return
        cursor = self.rich_editor.textCursor()
        cursor.insertList(cursor.currentList().format() if cursor.currentList() else QTextListFormat.Style.ListDisc)

    def _change_text_color(self):
        if not hasattr(self, 'rich_editor'): return
        color = QColorDialog.getColor(Qt.GlobalColor.black, self, "Seleccionar color de texto")
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            cursor = self.rich_editor.textCursor()
            cursor.mergeCharFormat(fmt)
            self.rich_editor.setTextCursor(cursor)

    def _insert_image_in_doc(self):
        if not hasattr(self, 'rich_editor'): return
        file_path, _ = QFileDialog.getOpenFileName(self, "Insertar Imagen en Documento", "", IMAGE_FILE_FILTER)
        if file_path:
            self._ensure_storage_dir()
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.storage_dir, filename)
            try:
                shutil.copy2(file_path, dest_path)
                cursor = self.rich_editor.textCursor()
                cursor.insertHtml(f'<br><img src="{dest_path}" style="max-width: 100%; border-radius: 4px; margin: 8px 0;"><br>')
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al insertar la imagen:\n{str(e)}")

    def _insert_table(self):
        if not hasattr(self, 'rich_editor'): return
        table_html = """
        <br>
        <table border="1" cellspacing="0" cellpadding="6" style="border-collapse: collapse; border: 1px solid #888888; width: 90%; margin: 10px 0;">
          <tr style="background-color: #E0E0E0; font-weight: bold;">
            <td style="border: 1px solid #888888;"><b>Columna 1</b></td>
            <td style="border: 1px solid #888888;"><b>Columna 2</b></td>
            <td style="border: 1px solid #888888;"><b>Columna 3</b></td>
          </tr>
          <tr>
            <td style="border: 1px solid #888888;">Dato A1</td>
            <td style="border: 1px solid #888888;">Dato B1</td>
            <td style="border: 1px solid #888888;">Dato C1</td>
          </tr>
          <tr>
            <td style="border: 1px solid #888888;">Dato A2</td>
            <td style="border: 1px solid #888888;">Dato B2</td>
            <td style="border: 1px solid #888888;">Dato C2</td>
          </tr>
        </table>
        <br>
        """
        cursor = self.rich_editor.textCursor()
        cursor.insertHtml(table_html)

    def _insert_code_block(self):
        if not hasattr(self, 'rich_editor'): return
        code_html = """
        <br>
        <table width="100%" cellspacing="0" cellpadding="12" style="background-color: #36393e; color: #a6e3a1; border-radius: 6px; border: none; margin: 10px 0;">
          <tr>
            <td style="background-color: #36393e; color: #a6e3a1; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px; border-radius: 6px; border: none;">
              <p style="margin:0px; color:#a6e3a1;"><span style="color:#a6e3a1; font-family:'Consolas', 'Courier New', monospace;"># Escribe tu código aquí...</span></p>
              <p style="margin:0px; color:#a6e3a1;"><span style="color:#a6e3a1; font-family:'Consolas', 'Courier New', monospace;">class Ejemplo:</span></p>
              <p style="margin:0px; color:#a6e3a1;"><span style="color:#a6e3a1; font-family:'Consolas', 'Courier New', monospace;">&nbsp;&nbsp;&nbsp;&nbsp;def __init__(self):</span></p>
              <p style="margin:0px; color:#a6e3a1;"><span style="color:#a6e3a1; font-family:'Consolas', 'Courier New', monospace;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;pass</span></p>
            </td>
          </tr>
        </table>
        <br>
        """
        cursor = self.rich_editor.textCursor()
        cursor.insertHtml(code_html)
        
        # Aplicar formato de texto al cursor para que todo lo que se escriba continúe en verde pastel y monoespaciado
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#a6e3a1"))
        fmt.setFontFamilies(["Consolas", "Courier New", "monospace"])
        cursor.mergeCharFormat(fmt)
        self.rich_editor.setTextCursor(cursor)

    def _insert_formula_dialog(self):
        if not hasattr(self, 'rich_editor'): return
        cursor = self.rich_editor.textCursor()
        selected_text = cursor.selectedText().strip()
        dlg = FormulaDialog(self, initial_latex=selected_text)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            tag = dlg.get_formula_html()
            if tag:
                cursor.insertHtml(tag)

    def _render_all_math(self):
        if not hasattr(self, 'rich_editor'): return
        converted = self.rich_editor.render_all_unrendered_formulas()
        if converted:
            QMessageBox.information(self, "Fórmulas", "Se han convertido las fórmulas matemáticas encontradas en el documento a gráficos.")
        else:
            QMessageBox.information(self, "Fórmulas", "No se encontraron fórmulas LaTeX ($$...$$ o $...$) pendientes de renderizar.")

