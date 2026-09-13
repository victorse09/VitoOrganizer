"""
math_renderer.py — Motor de renderizado de fórmulas matemáticas (LaTeX)
para Vito Organizer.

Permite convertir expresiones LaTeX ($...$, $$...$$, \\[...\\], \\(...\\), KaTeX, MathJax)
en imágenes PNG con fondo transparente e incrustarlas automáticamente en editores
de texto enriquecido (QTextEdit / MathRichTextEdit) como data-URI base64.
"""

import os
import io
import re
import html
import base64
try:
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False

from PyQt6.QtCore import Qt, QSize, QRectF, QBuffer, QIODevice
from PyQt6.QtGui import QIcon, QPixmap, QImage, QTextCursor, QFont, QPainter, QTextDocument
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QLineEdit, QPushButton, QRadioButton, QButtonGroup,
    QFrame, QGridLayout, QScrollArea, QWidget, QMessageBox
)

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')


# ──────────────────────────────────────────────────────────────────────────────
# 1. Utilidades de Limpieza y Renderizado LaTeX a PNG / Base64
# ──────────────────────────────────────────────────────────────────────────────

def clean_latex_string(latex: str) -> str:
    """Limpia y normaliza cadenas LaTeX para mathtext de matplotlib o renderizador Qt."""
    if not latex:
        return ""
    
    s = latex.strip()
    
    # Remover delimitadores externos si existen
    for prefix, suffix in [('$$', '$$'), (r'\[', r'\]'), ('$', '$'), (r'\(', r'\)')]:
        if s.startswith(prefix) and s.endswith(suffix) and len(s) >= len(prefix) + len(suffix):
            s = s[len(prefix):-len(suffix)].strip()
            break

    # Remover espacios no separables y caracteres invisibles
    s = s.replace('\u00a0', ' ').replace('\u202f', ' ').replace('\u200b', '').replace('\r', '')

    # Normalizar entornos comunes a formato compatible con mathtext
    s = re.sub(r'\\text\{([^}]+)\}', lambda m: f"\\mathrm{{{m.group(1)}}}", s)
    s = re.sub(r'\\operatorname\{([^}]+)\}', lambda m: f"\\mathrm{{{m.group(1)}}}", s)
    s = re.sub(r'\\begin\{(?:aligned|matrix|cases|split)\}', '', s)
    s = re.sub(r'\\end\{(?:aligned|matrix|cases|split)\}', '', s)
    
    # Reemplazar \\ de saltos de línea por espacio si es una sola línea
    if '\\\\' in s:
        s = s.replace('\\\\', ' ')

    return s.strip()


def _latex_to_qt_html(latex: str, font_size: int = 13, color: str = '#111111') -> str:
    """Convierte expresiones LaTeX a estructura HTML estilizada para renderizado Qt."""
    s = latex.strip()

    # Reemplazar fracciones anidadas o simples: \frac{num}{den}
    def repl_frac(m):
        num = m.group(1)
        den = m.group(2)
        return (
            f'<table style="display:inline-table; border-collapse:collapse; vertical-align:middle; '
            f'margin:0 3px; text-align:center;">'
            f'<tr><td style="border-bottom:1.5px solid {color}; padding:0 3px; font-size:{max(font_size-2, 10)}px; color:{color};">{num}</td></tr>'
            f'<tr><td style="padding:0 3px; font-size:{max(font_size-2, 10)}px; color:{color};">{den}</td></tr>'
            f'</table>'
        )

    # Procesar fracciones hasta que no queden más
    prev = ""
    while prev != s and r'\frac' in s:
        prev = s
        s = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', repl_frac, s)

    # Operadores y símbolos matemáticos
    symbol_map = {
        r'\times': ' × ', r'\cdot': ' · ', r'\approx': ' ≈ ', r'\pm': ' ± ',
        r'\mp': ' ∓ ', r'\div': ' ÷ ', r'\neq': ' ≠ ', r'\le': ' ≤ ', r'\ge': ' ≥ ',
        r'\leq': ' ≤ ', r'\geq': ' ≥ ', r'\infty': ' ∞ ', r'\Omega': 'Ω',
        r'\mu': 'µ', r'\pi': 'π', r'\Delta': 'Δ', r'\theta': 'θ', r'\alpha': 'α',
        r'\beta': 'β', r'\gamma': 'γ', r'\lambda': 'λ', r'\sigma': 'σ',
        r'\phi': 'ϕ', r'\omega': 'ω', r'\degree': '°', r'\circ': '°',
        r'\sum': '∑', r'\int': '∫', r'\partial': '∂', r'\nabla': '∇',
        r'\rightarrow': ' → ', r'\leftarrow': ' ← ', r'\to': ' → ',
        r'\quad': '&nbsp;&nbsp;', r'\qquad': '&nbsp;&nbsp;&nbsp;&nbsp;',
        r'\mathrm': '', r'\mathbf': '', r'\mathit': '',
    }
    for cmd, sym in symbol_map.items():
        s = s.replace(cmd, sym)

    # Raíces cuadradas: \sqrt[n]{x} y \sqrt{x}
    s = re.sub(r'\\sqrt\[([^\]]+)\]\{([^}]+)\}', r'<sup>\1</sup>√(\2)', s)
    s = re.sub(r'\\sqrt\{([^}]+)\}', r'√(\1)', s)

    # Exponentes / Potencias: ^{...} o ^x
    s = re.sub(r'\^\{([^}]+)\}', r'<sup>\1</sup>', s)
    s = re.sub(r'\^([0-9a-zA-Z\+\-])', r'<sup>\1</sup>', s)

    # Subíndices: _{...} o _x
    s = re.sub(r'\_\{([^}]+)\}', r'<sub>\1</sub>', s)
    s = re.sub(r'\_([0-9a-zA-Z])', r'<sub>\1</sub>', s)

    # Limpiar llaves sobrantes de LaTeX si las hay
    s = s.replace('{', '').replace('}', '')

    return (
        f'<span style="font-family: \'Segoe UI\', \'Liberation Serif\', \'Times New Roman\', serif; '
        f'font-size:{font_size}px; color:{color}; line-height:1.3;">'
        f'{s}'
        f'</span>'
    )


def _qt_render_latex_to_png(clean_latex: str, is_display: bool = False, dpi: int = 180, font_size: int = None, color: str = '#111111') -> bytes:
    """Renderiza una expresión LaTeX utilizando el motor nativo de PyQt6."""
    if font_size is None:
        font_size = 14 if is_display else 11

    html_content = _latex_to_qt_html(clean_latex, font_size=font_size, color=color)

    doc = QTextDocument()
    doc.setDefaultFont(QFont("Segoe UI", font_size))
    doc.setHtml(html_content)

    doc_size = doc.size()
    w = max(int(doc_size.width()) + 8, 20)
    h = max(int(doc_size.height()) + 6, 18)

    img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)

    painter = QPainter(img)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    doc.drawContents(painter, QRectF(4, 3, doc_size.width(), doc_size.height()))
    painter.end()

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buffer, "PNG")
    return bytes(buffer.data())


def render_latex_to_png(latex_str: str, is_display: bool = False, dpi: int = 180, font_size: int = None, color: str = '#111111') -> bytes:
    """
    Renderiza una expresión LaTeX a bytes PNG transparentes con alta resolución.
    Utiliza matplotlib si está instalado, o el motor nativo de PyQt6 como respaldo.
    """
    clean_latex = clean_latex_string(latex_str)
    if not clean_latex:
        return None

    if font_size is None:
        font_size = 14 if is_display else 11

    # 1. Intentar renderizar con matplotlib si está disponible
    if HAS_MATPLOTLIB:
        try:
            fig = Figure(dpi=dpi)
            fig.patch.set_alpha(0.0)
            canvas = FigureCanvasAgg(fig)

            t = fig.text(0.5, 0.5, f"${clean_latex}$", fontsize=font_size, color=color, ha='center', va='center')
            canvas.draw()

            bbox = t.get_window_extent(canvas.get_renderer())
            width_in = max(bbox.width / dpi + 0.06, 0.15)
            height_in = max(bbox.height / dpi + 0.06, 0.15)
            fig.set_size_inches(width_in, height_in)

            buf = io.BytesIO()
            fig.savefig(buf, format='png', transparent=True, dpi=dpi, bbox_inches='tight', pad_inches=0.02)
            return buf.getvalue()
        except Exception:
            pass

    # 2. Respaldo nativo con PyQt6 (no requiere matplotlib ni librerías externas)
    try:
        return _qt_render_latex_to_png(clean_latex, is_display=is_display, dpi=dpi, font_size=font_size, color=color)
    except Exception:
        return None


def latex_to_base64_img_tag(latex_str: str, is_display: bool = False, dpi: int = 180, color: str = '#111111') -> str:
    """
    Convierte una expresión LaTeX en una etiqueta HTML <img> con data-URI base64.
    """
    png_bytes = render_latex_to_png(latex_str, is_display=is_display, dpi=dpi, color=color)
    if not png_bytes:
        return None

    b64_str = base64.b64encode(png_bytes).decode('utf-8')
    raw_latex = clean_latex_string(latex_str)
    escaped_alt = html.escape(raw_latex)

    if is_display:
        return f'<div style="text-align: center; margin: 10px 0;"><img src="data:image/png;base64,{b64_str}" alt="{escaped_alt}" title="{escaped_alt}" style="display: block; margin: 6px auto; max-width: 95%;" /></div>'
    else:
        return f'<img src="data:image/png;base64,{b64_str}" alt="{escaped_alt}" title="{escaped_alt}" style="vertical-align: middle; margin: 0 2px;" />'


# ──────────────────────────────────────────────────────────────────────────────
# 2. Detección y Conversión de Fórmulas en Texto / HTML
# ──────────────────────────────────────────────────────────────────────────────

def extract_katex_mathjax(html_content: str) -> str:
    """Extrae las anotaciones LaTeX de estructuras HTML KaTeX y MathJax."""
    if not html_content:
        return ""

    # KaTeX Display
    res = re.sub(
        r'<span[^>]*class=[\'"][^\'"]*katex-display[^\'"]*[\'"][^>]*>.*?<annotation[^>]*encoding=[\'"]application/x-tex[\'"][^>]*>(.*?)</annotation>.*?</span>',
        r'\n$$\1$$\n',
        html_content,
        flags=re.DOTALL
    )
    # KaTeX Inline
    res = re.sub(
        r'<span[^>]*class=[\'"][^\'"]*katex[^\'"]*[\'"][^>]*>.*?<annotation[^>]*encoding=[\'"]application/x-tex[\'"][^>]*>(.*?)</annotation>.*?</span>',
        r' $\1$ ',
        res,
        flags=re.DOTALL
    )
    # MathJax Display
    res = re.sub(
        r'<script[^>]*type=[\'"]math/tex;\s*mode=display[\'"][^>]*>(.*?)</script>',
        r'\n$$\1$$\n',
        res,
        flags=re.DOTALL
    )
    # MathJax Inline
    res = re.sub(
        r'<script[^>]*type=[\'"]math/tex[\'"][^>]*>(.*?)</script>',
        r' $\1$ ',
        res,
        flags=re.DOTALL
    )
    return res


def has_math_formulas(text_or_html: str) -> bool:
    """Determina si una cadena contiene fórmulas LaTeX o KaTeX/MathJax."""
    if not text_or_html:
        return False
    if 'katex' in text_or_html or 'math/tex' in text_or_html or '<math' in text_or_html:
        return True
    if '$$' in text_or_html or r'\[' in text_or_html or r'\(' in text_or_html:
        return True
    # Revisar $...$ excluyendo montos monetarios simples ($10, $25.00)
    matches = re.findall(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', text_or_html)
    for m in matches:
        if not re.match(r'^\s*[\d,\.]+\s*$', m):
            return True
    return False


def convert_math_to_rendered_html(content: str, is_html: bool = False, dpi: int = 180) -> str:
    """
    Convierte todas las fórmulas matemáticas encontradas en el contenido
    en etiquetas <img> con la fórmula renderizada.
    """
    if not content:
        return content

    working_text = content
    if is_html:
        working_text = extract_katex_mathjax(working_text)

    # 1. Reemplazar Fórmulas en bloque $$...$$ y \[...\]
    def repl_display(m):
        latex = m.group(1)
        tag = latex_to_base64_img_tag(latex, is_display=True, dpi=dpi)
        return tag if tag else m.group(0)

    working_text = re.sub(r'\$\$(.+?)\$\$', repl_display, working_text, flags=re.DOTALL)
    working_text = re.sub(r'\\\[(.+?)\\\]', repl_display, working_text, flags=re.DOTALL)

    # 2. Reemplazar Fórmulas en línea $...$ y \(...\)
    def repl_inline(m):
        latex = m.group(1)
        # Evitar montos de dinero como $10, $500.00
        if re.match(r'^\s*[\d,\.]+\s*$', latex):
            return m.group(0)
        tag = latex_to_base64_img_tag(latex, is_display=False, dpi=dpi)
        return tag if tag else m.group(0)

    working_text = re.sub(r'(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)', repl_inline, working_text)
    working_text = re.sub(r'\\\((.+?)\\\)', repl_inline, working_text)

    # Si es texto plano de origen, convertir saltos de línea a párrafos/br
    if not is_html:
        paragraphs = working_text.split('\n\n')
        html_paragraphs = []
        for p in paragraphs:
            p_clean = p.strip()
            if p_clean:
                # Si el párrafo es ya un bloque div con imagen de fórmula, dejarlo directo
                if p_clean.startswith('<div style="text-align: center;') and p_clean.endswith('</div>'):
                    html_paragraphs.append(p_clean)
                else:
                    html_paragraphs.append(f"<p>{p_clean.replace(chr(10), '<br>')}</p>")
        working_text = "".join(html_paragraphs)

    return working_text


# ──────────────────────────────────────────────────────────────────────────────
# 3. MathRichTextEdit — QTextEdit con Soporte de Pegado Inteligente de Fórmulas
# ──────────────────────────────────────────────────────────────────────────────

class MathRichTextEdit(QTextEdit):
    """
    QTextEdit mejorado con captura automática de fórmulas matemáticas al pegar
    (Ctrl+V) y soporte para renderizar LaTeX como imágenes base64 integradas.
    """

    def insertFromMimeData(self, source):
        """Intercepta el pegado para renderizar fórmulas matemáticas de HTML o texto."""
        if source is None:
            return

        has_html_data = source.hasHtml()
        has_text_data = source.hasText()

        html_text = source.html() if has_html_data else ""
        plain_text = source.text() if has_text_data else ""

        # Comprobar si hay fórmulas en HTML o texto plano
        if has_html_data and has_math_formulas(html_text):
            rendered_html = convert_math_to_rendered_html(html_text, is_html=True)
            self.insertHtml(rendered_html)
            return
        elif has_text_data and has_math_formulas(plain_text):
            rendered_html = convert_math_to_rendered_html(plain_text, is_html=False)
            self.insertHtml(rendered_html)
            return

        # Comportamiento normal si no hay fórmulas matemáticas
        super().insertFromMimeData(source)

    def render_all_unrendered_formulas(self):
        """
        Escanea el contenido del documento y convierte cualquier expresión
        LaTeX restante ($$...$$, $...$) en fórmulas renderizadas.
        """
        current_html = self.toHtml()
        if has_math_formulas(current_html):
            new_html = convert_math_to_rendered_html(current_html, is_html=True)
            cursor = self.textCursor()
            pos = cursor.position()
            self.setHtml(new_html)
            cursor.setPosition(min(pos, len(self.toPlainText())))
            self.setTextCursor(cursor)
            return True
        return False


# ──────────────────────────────────────────────────────────────────────────────
# 4. FormulaDialog — Diálogo para Insertar / Editar Fórmulas LaTeX con Vista Previa
# ──────────────────────────────────────────────────────────────────────────────

class FormulaDialog(QDialog):
    """
    Diálogo para escribir o pegar fórmulas matemáticas en LaTeX
    con vista previa interactiva en tiempo real y paleta de símbolos.
    """

    def __init__(self, parent=None, initial_latex=""):
        super().__init__(parent)
        self.setWindowTitle("Insertar Fórmula Matemática (LaTeX)")
        self.resize(600, 480)
        self._initial_latex = initial_latex
        self._generated_tag = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Paleta de botones rápidos
        palette_frame = QFrame()
        palette_frame.setStyleSheet("QFrame { background-color: #F0F2F5; border: 1px solid #D0D7DE; border-radius: 6px; }")
        palette_layout = QVBoxLayout(palette_frame)
        palette_layout.setContentsMargins(8, 8, 8, 8)
        palette_layout.setSpacing(6)

        lbl_palette = QLabel("<b>Plantillas y Símbolos Rápidos:</b>")
        lbl_palette.setStyleSheet("color: #333; font-size: 12px; border: none;")
        palette_layout.addWidget(lbl_palette)

        grid = QGridLayout()
        grid.setSpacing(4)

        symbols = [
            ("Fracción", r"\frac{a}{b}"),
            ("Potencia", r"x^{n}"),
            ("Subíndice", r"x_{i}"),
            ("Raíz", r"\sqrt{x}"),
            ("Raíz n", r"\sqrt[n]{x}"),
            ("Multiplicación", r"\times"),
            ("Aproximado", r"\approx"),
            ("Más/Menos", r"\pm"),
            ("División", r"\div"),
            ("Sumatoria", r"\sum_{i=1}^{n}"),
            ("Integral", r"\int_{a}^{b}"),
            ("Infinito", r"\infty"),
            ("Ohm (Ω)", r"\Omega"),
            ("Micro (µ)", r"\mu"),
            ("Pi (π)", r"\pi"),
            ("Delta (Δ)", r"\Delta"),
        ]

        btn_style = """
            QPushButton {
                background-color: #FFFFFF;
                color: #24292F;
                border: 1px solid #D0D7DE;
                border-radius: 4px;
                padding: 4px 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #E6EDF5;
                border-color: #0969DA;
                color: #0969DA;
            }
        """

        for idx, (lbl_txt, latex_code) in enumerate(symbols):
            r = idx // 4
            c = idx % 4
            btn = QPushButton(lbl_txt)
            btn.setStyleSheet(btn_style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, code=latex_code: self._insert_snippet(code))
            grid.addWidget(btn, r, c)

        palette_layout.addLayout(grid)
        layout.addWidget(palette_frame)

        # Editor de código LaTeX
        lbl_editor = QLabel("<b>Código LaTeX:</b>")
        lbl_editor.setStyleSheet("font-size: 13px; color: #111;")
        layout.addWidget(lbl_editor)

        self.latex_input = QTextEdit()
        self.latex_input.setFixedHeight(80)
        self.latex_input.setFont(QFont("Consolas", 12))
        self.latex_input.setPlaceholderText(r"Ejemplo: FreqWord = \frac{f_{out} \times 2^{28}}{f_{clk}}")
        self.latex_input.setStyleSheet("QTextEdit { background-color: #FFFFFF; border: 1px solid #CCC; border-radius: 4px; padding: 6px; color: #111; }")
        self.latex_input.textChanged.connect(self._update_preview)
        layout.addWidget(self.latex_input)

        # Opciones de presentación
        opts_layout = QHBoxLayout()
        self.radio_display = QRadioButton("Fórmula en bloque (Centrada $$)")
        self.radio_display.setChecked(True)
        self.radio_display.toggled.connect(self._update_preview)
        opts_layout.addWidget(self.radio_display)

        self.radio_inline = QRadioButton("Fórmula en línea (Inline $)")
        self.radio_inline.toggled.connect(self._update_preview)
        opts_layout.addWidget(self.radio_inline)
        opts_layout.addStretch()
        layout.addLayout(opts_layout)

        # Área de Vista Previa en Tiempo Real
        lbl_prev_title = QLabel("<b>Vista Previa:</b>")
        lbl_prev_title.setStyleSheet("font-size: 13px; color: #111;")
        layout.addWidget(lbl_prev_title)

        self.preview_scroll = QScrollArea()
        self.preview_scroll.setFixedHeight(110)
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setStyleSheet("QScrollArea { background-color: #FAFAFA; border: 1px dashed #BBB; border-radius: 6px; }")

        self.preview_label = QLabel("Escribe una fórmula para previsualizar")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("QLabel { background-color: transparent; color: #666; font-size: 13px; padding: 10px; }")
        self.preview_scroll.setWidget(self.preview_label)
        layout.addWidget(self.preview_scroll)

        # Botones de acción
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton(" Cancelar")
        icon_cancel = os.path.join(ICONS_DIR, 'close.svg')
        if os.path.exists(icon_cancel):
            self.btn_cancel.setIcon(QIcon(icon_cancel))
            self.btn_cancel.setIconSize(QSize(14, 14))
        self.btn_cancel.setStyleSheet("QPushButton { padding: 6px 14px; border: 1px solid #CCC; border-radius: 4px; background-color: #E0E0E0; color: #111; } QPushButton:hover { background-color: #CCC; }")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_insert = QPushButton(" Insertar Fórmula")
        icon_insert = os.path.join(ICONS_DIR, 'save.svg')
        if os.path.exists(icon_insert):
            self.btn_insert.setIcon(QIcon(icon_insert))
            self.btn_insert.setIconSize(QSize(16, 16))
        self.btn_insert.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 18px; border-radius: 4px; background-color: #1976D2; color: white; } QPushButton:hover { background-color: #1565C0; }")
        self.btn_insert.clicked.connect(self._accept_formula)
        btn_layout.addWidget(self.btn_insert)

        layout.addLayout(btn_layout)

        if self._initial_latex:
            self.latex_input.setPlainText(self._initial_latex)
        else:
            self.latex_input.setPlainText(r"FreqWord = \frac{f_{out} \times 2^{28}}{f_{clk}}")

    def _insert_snippet(self, code: str):
        cursor = self.latex_input.textCursor()
        cursor.insertText(code)
        self.latex_input.setTextCursor(cursor)
        self.latex_input.setFocus()

    def _update_preview(self):
        latex = self.latex_input.toPlainText().strip()
        if not latex:
            self.preview_label.setText("Escribe una fórmula para previsualizar")
            self.preview_label.setPixmap(QPixmap())
            return

        is_display = self.radio_display.isChecked()
        png_bytes = render_latex_to_png(latex, is_display=is_display, dpi=180)

        if png_bytes:
            pixmap = QPixmap()
            pixmap.loadFromData(png_bytes)
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setText("")
        else:
            self.preview_label.setPixmap(QPixmap())
            self.preview_label.setText("Error en sintaxis LaTeX")

    def _accept_formula(self):
        latex = self.latex_input.toPlainText().strip()
        if not latex:
            QMessageBox.warning(self, "Aviso", "Por favor ingresa una expresión LaTeX.")
            return

        is_display = self.radio_display.isChecked()
        tag = latex_to_base64_img_tag(latex, is_display=is_display, dpi=180)
        if not tag:
            QMessageBox.critical(self, "Error", "No se pudo renderizar la fórmula. Verifica la sintaxis LaTeX.")
            return

        self._generated_tag = tag
        self.accept()

    def get_formula_html(self) -> str:
        return self._generated_tag
