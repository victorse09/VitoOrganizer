import os
import shutil
import json
import math
import struct
import zipfile
import io
import re
import xml.etree.ElementTree as ET
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QLineF, QRect, QSize, QRegularExpression, QPoint
from PyQt6.QtGui import (
    QIcon, QPixmap, QDesktopServices, QTextCursor, QTextCharFormat, QFont, 
    QColor, QPainter, QPen, QBrush, QPainterPath, QKeySequence, QShortcut,
    QSyntaxHighlighter, QTextDocument, QImage, QPolygonF, QTransform
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QPlainTextEdit, QLineEdit, QFileDialog, QMessageBox, QFrame, QComboBox,
    QTabWidget, QTabBar, QToolButton, QSlider, QCheckBox, QSpinBox, QDoubleSpinBox, QSplitter,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsPolygonItem, QGraphicsTextItem,
    QGraphicsLineItem, QGraphicsPathItem, QInputDialog, QColorDialog, QApplication, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMenu
)
from plugins.plugin_base import open_local_file, load_image_qimage, IMAGE_FILE_FILTER


# =============================================================================
# 1. EDITOR DE CÓDIGO AVANZADO (Highlighter, LineNumbers, SearchBar, CodeEditorWidget)
# =============================================================================

CODE_TEMPLATES = {
    "Arduino": """// --- Plantilla Arduino ---
void setup() {
  Serial.begin(9600);
  pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
  digitalWrite(LED_BUILTIN, HIGH);
  delay(1000);
  digitalWrite(LED_BUILTIN, LOW);
  delay(1000);
}
""",
    "Pascal": """{ --- Plantilla Pascal --- }
program MiProyecto;

var
  nombre: string;

begin
  writeln('===================================');
  writeln('      PROYECTO EN PASCAL           ');
  writeln('===================================');
  write('Ingresa tu nombre: ');
  readln(nombre);
  writeln('¡Hola, ', nombre, '!');
end.
""",
    "BASIC": """10 REM --- Plantilla BASIC ---
20 CLS
30 PRINT "================================="
40 PRINT "      PROYECTO EN BASIC          "
50 PRINT "================================="
60 INPUT "INGRESE SU NOMBRE: ", N$
70 PRINT "HOLA "; N$
80 END
""",
    "Python": """#!/usr/bin/env python3
# -*- coding: utf-8 -*-

def main():
    print("¡Hola desde Python!")

if __name__ == '__main__':
    main()
""",
    "C / C++": """#include <stdio.h>
#include <stdlib.h>

int main(int argc, char *argv[]) {
    printf("¡Hola Mundo en C/C++!\n");
    return 0;
}
""",
    "JavaScript": """// --- Plantilla JavaScript ---
function main() {
    console.log("¡Hola desde JavaScript!");
}

main();
""",
    "HTML / CSS": """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Proyecto HTML</title>
    <style>
        body { font-family: sans-serif; background: #1e1e2e; color: #cdd6f4; padding: 20px; }
    </style>
</head>
<body>
    <h1>¡Hola Mundo!</h1>
</body>
</html>
""",
    "JSON": """{
  "proyecto": "Mi Proyecto",
  "version": "1.0.0",
  "configuracion": {
    "activo": true,
    "puerto": 8080
  }
}
""",
    "SQL": """-- --- Plantilla SQL ---
CREATE TABLE usuarios (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
);

SELECT * FROM usuarios;
""",
    "Shell / Bash": """#!/bin/bash
# --- Plantilla Bash ---
echo "================================="
echo "   EJECUTANDO SCRIPT BASH        "
echo "================================="
echo "Directorio actual: $(pwd)"
""",
}


class CodeSyntaxHighlighter(QSyntaxHighlighter):
    """Resaltador de sintaxis para múltiples lenguajes usando tema Catppuccin Mocha."""
    def __init__(self, document, language="Python"):
        super().__init__(document)
        self.language = language
        self._rules = []
        self._build_rules()

    def set_language(self, language):
        self.language = language
        self._build_rules()
        self.rehighlight()

    def _build_rules(self):
        self._rules.clear()
        
        # Paleta de Colores
        fmt_keyword = QTextCharFormat()
        fmt_keyword.setForeground(QColor("#cba6f7"))  # Malva/Púrpura
        fmt_keyword.setFontWeight(QFont.Weight.Bold)

        fmt_string = QTextCharFormat()
        fmt_string.setForeground(QColor("#a6e3a1"))  # Verde

        fmt_comment = QTextCharFormat()
        fmt_comment.setForeground(QColor("#6c7086"))  # Gris Muted
        fmt_comment.setFontItalic(True)

        fmt_number = QTextCharFormat()
        fmt_number.setForeground(QColor("#fab387"))  # Naranja

        fmt_function = QTextCharFormat()
        fmt_function.setForeground(QColor("#89dceb"))  # Cyan

        fmt_preproc = QTextCharFormat()
        fmt_preproc.setForeground(QColor("#f9e2af"))  # Amarillo

        # Palabras clave según lenguaje
        keywords = []
        if self.language in ("Python", "Plain Code"):
            keywords = ["and", "as", "assert", "async", "await", "break", "class", "continue", "def", "del", "elif", "else", "except", "False", "finally", "for", "from", "global", "if", "import", "in", "is", "lambda", "None", "nonlocal", "not", "or", "pass", "raise", "return", "True", "try", "while", "with", "yield"]
        elif self.language in ("C / C++", "Arduino"):
            keywords = ["auto", "break", "case", "char", "const", "continue", "default", "do", "double", "else", "enum", "extern", "float", "for", "goto", "if", "int", "long", "register", "return", "short", "signed", "sizeof", "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile", "while", "class", "namespace", "new", "delete", "public", "private", "protected", "template", "using", "boolean", "byte", "word", "setup", "loop", "pinMode", "digitalWrite", "digitalRead", "analogRead", "analogWrite", "delay", "Serial"]
        elif self.language == "Pascal":
            keywords = ["program", "unit", "uses", "type", "var", "const", "begin", "end", "procedure", "function", "if", "then", "else", "case", "of", "while", "do", "repeat", "until", "for", "to", "downto", "array", "record", "file", "set", "string", "integer", "real", "boolean", "char", "writeln", "write", "readln", "read"]
        elif self.language == "BASIC":
            keywords = ["PRINT", "INPUT", "LET", "IF", "THEN", "ELSE", "FOR", "TO", "STEP", "NEXT", "GOTO", "GOSUB", "RETURN", "DIM", "REM", "END", "CLS", "DATA", "READ", "RESTORE", "STOP", "DEF", "FN"]
        elif self.language in ("JavaScript", "HTML / CSS"):
            keywords = ["async", "await", "break", "case", "catch", "class", "const", "continue", "debugger", "default", "delete", "do", "else", "export", "extends", "false", "finally", "for", "function", "if", "import", "in", "instanceof", "let", "new", "null", "of", "return", "super", "switch", "this", "throw", "true", "try", "typeof", "var", "void", "while", "with", "yield"]
        elif self.language == "SQL":
            keywords = ["SELECT", "FROM", "WHERE", "INSERT", "INTO", "UPDATE", "DELETE", "JOIN", "INNER", "LEFT", "RIGHT", "ON", "GROUP", "BY", "ORDER", "HAVING", "CREATE", "TABLE", "ALTER", "DROP", "INDEX", "AND", "OR", "NOT", "NULL", "PRIMARY", "KEY", "FOREIGN", "REFERENCES"]
        elif self.language == "Shell / Bash":
            keywords = ["if", "then", "else", "fi", "for", "do", "done", "while", "until", "case", "esac", "function", "return", "exit", "echo", "export", "set", "unset", "alias", "cd", "pwd", "ls", "grep"]

        opt = QRegularExpression.PatternOption.CaseInsensitiveOption if self.language in ("Pascal", "BASIC", "SQL") else QRegularExpression.PatternOption.NoPatternOption

        for kw in keywords:
            pattern = QRegularExpression(rf"\b{kw}\b", opt)
            self._rules.append((pattern, fmt_keyword))

        # Funciones
        self._rules.append((QRegularExpression(r"\b[A-Za-z_][A-Za-z0-9_]*(?=\s*\()"), fmt_function))

        # Números
        self._rules.append((QRegularExpression(r"\b0x[0-9a-fA-F]+\b|\b\d+(\.\d+)?\b"), fmt_number))

        # Directivas de preprocesador / Decoradores
        if self.language in ("C / C++", "Arduino"):
            self._rules.append((QRegularExpression(r"#\s*[a-zA-Z_]+"), fmt_preproc))
        elif self.language == "Python":
            self._rules.append((QRegularExpression(r"@[a-zA-Z_][a-zA-Z0-9_]*"), fmt_preproc))

        # Strings
        self._rules.append((QRegularExpression(r'"([^"\\]|\\.)*"'), fmt_string))
        self._rules.append((QRegularExpression(r"'([^'\\]|\\.)*'"), fmt_string))

        # Comentarios
        if self.language in ("Python", "Shell / Bash"):
            self._rules.append((QRegularExpression(r"#.*"), fmt_comment))
        elif self.language in ("C / C++", "Arduino", "JavaScript"):
            self._rules.append((QRegularExpression(r"//.*"), fmt_comment))
            self._rules.append((QRegularExpression(r"/\*.*?\*/"), fmt_comment))
        elif self.language == "Pascal":
            self._rules.append((QRegularExpression(r"//.*"), fmt_comment))
            self._rules.append((QRegularExpression(r"\{.*?\}"), fmt_comment))
            self._rules.append((QRegularExpression(r"\(\*.*?\*\)"), fmt_comment))
        elif self.language == "BASIC":
            self._rules.append((QRegularExpression(r"\bREM\b.*", QRegularExpression.PatternOption.CaseInsensitiveOption), fmt_comment))
            self._rules.append((QRegularExpression(r"'.*"), fmt_comment))
        elif self.language == "SQL":
            self._rules.append((QRegularExpression(r"--.*"), fmt_comment))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class LineNumberArea(QWidget):
    """Área lateral para renderizar números de línea."""
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.lineNumberAreaPaintEvent(event)


class CodeTextEdit(QPlainTextEdit):
    """
    Editor de texto plano estilo IDE con números de línea,
    resaltado de sintaxis, resaltado de línea activa y comandos avanzados.
    """
    def __init__(self, parent=None, language="Python"):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.highlighter = CodeSyntaxHighlighter(self.document(), language)

        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

        # Configuración de fuente y tabulaciones
        self.set_font_size(13)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e2e;
                color: #a6e3a1;
                border: none;
                selection-background-color: #45475a;
                selection-color: #ffffff;
            }
        """)

    def set_font_size(self, size_pt: int):
        font = QFont("Consolas", size_pt)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        self.update_line_number_area_width(0)

    def set_language(self, language: str):
        self.setProperty("language", language)
        self.highlighter.set_language(language)

    def line_number_area_width(self):
        digits = 1
        max_val = max(1, self.blockCount())
        while max_val >= 10:
            max_val //= 10
            digits += 1
        space = 16 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def lineNumberAreaPaintEvent(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#181825"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        current_block = self.textCursor().block().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number == current_block:
                    painter.setPen(QColor("#f9e2af"))
                    f = painter.font()
                    f.setBold(True)
                    painter.setFont(f)
                else:
                    painter.setPen(QColor("#6c7086"))
                    f = painter.font()
                    f.setBold(False)
                    painter.setFont(f)

                painter.drawText(0, top, self.line_number_area.width() - 8, self.fontMetrics().height(),
                                 Qt.AlignmentFlag.AlignRight, number)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#252637"))
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def toggle_comment(self):
        lang = self.property("language") or "Python"
        symbols = {
            "Python": "# ", "Shell / Bash": "# ",
            "C / C++": "// ", "Arduino": "// ", "JavaScript": "// ", "Pascal": "// ",
            "BASIC": "REM ", "SQL": "-- "
        }
        symbol = symbols.get(lang, "// ")
        cursor = self.textCursor()
        start_pos = cursor.selectionStart()
        end_pos = cursor.selectionEnd()

        cursor.setPosition(start_pos)
        start_block = cursor.blockNumber()
        cursor.setPosition(end_pos)
        end_block = cursor.blockNumber()

        cursor.beginEditBlock()
        for block_idx in range(start_block, end_block + 1):
            block = self.document().findBlockByNumber(block_idx)
            text = block.text()
            block_cursor = QTextCursor(block)
            stripped_sym = symbol.strip()
            if text.lstrip().startswith(stripped_sym):
                pos = text.find(stripped_sym)
                block_cursor.setPosition(block.position() + pos)
                for _ in range(len(symbol)):
                    block_cursor.deleteChar()
            else:
                block_cursor.setPosition(block.position())
                block_cursor.insertText(symbol)
        cursor.endEditBlock()

    def duplicate_line(self):
        cursor = self.textCursor()
        cursor.beginEditBlock()
        if cursor.hasSelection():
            text = cursor.selectedText()
            cursor.setPosition(cursor.selectionEnd())
            cursor.insertText(text)
        else:
            block = cursor.block()
            line_text = block.text()
            cursor.movePosition(QTextCursor.MoveOperation.EndOfBlock)
            cursor.insertText("\n" + line_text)
        cursor.endEditBlock()


class CodeEditorWidget(QWidget):
    """
    Editor de código IDE completo con soporte multi-pestaña, números de línea,
    resaltado de sintaxis, plantillas de código, buscar/reemplazar y estado en tiempo real.
    """
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, item_calc: dict, project_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item_calc = item_calc
        self.project_item = project_item
        self.agenda_path = agenda_path
        
        self.calc_id = item_calc.get('id', 'unknown')
        item_name = project_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, self.calc_id)
        self.current_font_size = 13
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Barra Superior
        top_bar = QHBoxLayout()
        
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Editor de Código IDE: <b>{self.item_calc.get('name', 'Sin nombre')}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Barra de Herramientas Principal
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        lbl_lang = QLabel("Lenguaje:")
        lbl_lang.setStyleSheet("font-weight: bold; color: #333;")
        toolbar.addWidget(lbl_lang)

        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["Arduino", "Pascal", "BASIC", "Python", "C / C++", "JavaScript", "HTML / CSS", "JSON", "SQL", "Shell / Bash", "Plain Code"])
        self.lang_combo.setStyleSheet("QComboBox { padding: 4px 8px; border-radius: 4px; border: 1px solid #CCC; background: #FFF; color: #111; font-weight: bold; }")
        self.lang_combo.currentTextChanged.connect(self._on_lang_changed)
        toolbar.addWidget(self.lang_combo)

        btn_style = "QPushButton { padding: 4px 8px; border-radius: 4px; background: #E0E0E0; color: #111; border: 1px solid #AAA; font-weight: bold; } QPushButton:hover { background: #CCC; }"

        btn_add_tab = QPushButton("➕ Pestaña")
        btn_add_tab.setStyleSheet(btn_style)
        btn_add_tab.clicked.connect(self._add_new_tab_prompt)
        toolbar.addWidget(btn_add_tab)

        btn_rename_tab = QPushButton("✏️ Renombrar")
        btn_rename_tab.setStyleSheet(btn_style)
        btn_rename_tab.clicked.connect(self._rename_active_tab)
        toolbar.addWidget(btn_rename_tab)

        btn_template = QPushButton("⚡ Plantilla")
        btn_template.setStyleSheet("QPushButton { padding: 4px 8px; border-radius: 4px; background: #cba6f7; color: #111; border: 1px solid #a6e3a1; font-weight: bold; } QPushButton:hover { background: #b4befe; }")
        btn_template.clicked.connect(self._insert_template)
        toolbar.addWidget(btn_template)

        btn_comment = QPushButton("💬 Comentar")
        btn_comment.setStyleSheet(btn_style)
        btn_comment.clicked.connect(self._toggle_comment)
        toolbar.addWidget(btn_comment)

        btn_dup = QPushButton("📑 Duplicar")
        btn_dup.setStyleSheet(btn_style)
        btn_dup.clicked.connect(self._duplicate_line)
        toolbar.addWidget(btn_dup)

        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setStyleSheet(btn_style)
        btn_copy.clicked.connect(self._copy_code)
        toolbar.addWidget(btn_copy)

        btn_search = QPushButton("🔍 Buscar / Reemplazar")
        btn_search.setStyleSheet(btn_style)
        btn_search.clicked.connect(self._toggle_search_panel)
        toolbar.addWidget(btn_search)

        btn_font_plus = QPushButton("A+")
        btn_font_plus.setFixedWidth(32)
        btn_font_plus.setStyleSheet(btn_style)
        btn_font_plus.clicked.connect(lambda: self._change_font_size(1))
        toolbar.addWidget(btn_font_plus)

        btn_font_minus = QPushButton("A-")
        btn_font_minus.setFixedWidth(32)
        btn_font_minus.setStyleSheet(btn_style)
        btn_font_minus.clicked.connect(lambda: self._change_font_size(-1))
        toolbar.addWidget(btn_font_minus)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Panel de Búsqueda y Reemplazo (Oculto por defecto)
        self.search_panel = QFrame()
        self.search_panel.setVisible(False)
        self.search_panel.setStyleSheet("""
            QFrame {
                background-color: #313244;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
            }
            QLineEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton {
                background-color: #45475a;
                color: #cdd6f4;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #585b70;
                color: #f9e2af;
            }
        """)
        sp_layout = QVBoxLayout(self.search_panel)
        sp_layout.setContentsMargins(4, 4, 4, 4)
        sp_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Buscar:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Texto a buscar...")
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._find_next)
        row1.addWidget(self.search_input, 1)

        self.match_count_lbl = QLabel("0 coincidencias")
        self.match_count_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        row1.addWidget(self.match_count_lbl)

        btn_prev = QPushButton("◀ Anterior")
        btn_prev.clicked.connect(self._find_prev)
        row1.addWidget(btn_prev)

        btn_next = QPushButton("Siguiente ▶")
        btn_next.clicked.connect(self._find_next)
        row1.addWidget(btn_next)

        btn_close_search = QPushButton("✕")
        btn_close_search.setFixedWidth(28)
        btn_close_search.clicked.connect(lambda: self.search_panel.setVisible(False))
        row1.addWidget(btn_close_search)

        sp_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Reemplazar:"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Reemplazar por...")
        row2.addWidget(self.replace_input, 1)

        btn_rep_one = QPushButton("Reemplazar")
        btn_rep_one.clicked.connect(self._replace_one)
        row2.addWidget(btn_rep_one)

        btn_rep_all = QPushButton("Reemplazar Todo")
        btn_rep_all.clicked.connect(self._replace_all)
        row2.addWidget(btn_rep_all)

        sp_layout.addLayout(row2)

        layout.addWidget(self.search_panel)

        # Widget de Pestañas (QTabWidget)
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #313244;
                border-radius: 6px;
                background-color: #1e1e2e;
            }
            QTabBar::tab {
                background-color: #181825;
                color: #a6adc8;
                padding: 6px 14px;
                border: 1px solid #313244;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 12px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #1e1e2e;
                color: #89b4fa;
                border-color: #89b4fa;
            }
            QTabBar::tab:hover:!selected {
                background-color: #313244;
                color: #cdd6f4;
            }
        """)

        layout.addWidget(self.tab_widget, 1)

        # Barra de Estado Inferior
        self.status_bar_lbl = QLabel("Línea: 1 | Columna: 1 | Total Líneas: 1 | Caracteres: 0")
        self.status_bar_lbl.setStyleSheet("""
            QLabel {
                background-color: #181825;
                color: #a6adc8;
                border: 1px solid #313244;
                border-radius: 4px;
                padding: 4px 10px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.status_bar_lbl)

    def _create_editor_instance(self, language="Python", content="") -> CodeTextEdit:
        editor = CodeTextEdit(language=language)
        editor.set_font_size(self.current_font_size)
        editor.setPlaceholderText("// Escribe tu código aquí...")
        editor.cursorPositionChanged.connect(self._update_status_bar)
        editor.textChanged.connect(self._update_status_bar)
        if content:
            editor.setPlainText(content)
        return editor

    def _add_tab(self, title: str = "main.py", language: str = "Python", content: str = "") -> CodeTextEdit:
        editor = self._create_editor_instance(language, content)
        idx = self.tab_widget.addTab(editor, title)
        self.tab_widget.setCurrentIndex(idx)
        self._update_status_bar()
        return editor

    def _current_editor(self) -> CodeTextEdit:
        return self.tab_widget.currentWidget()

    def _on_tab_changed(self, index: int):
        editor = self._current_editor()
        if editor:
            lang = editor.property("language") or "Python"
            self.lang_combo.blockSignals(True)
            idx = self.lang_combo.findText(lang)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
            self.lang_combo.blockSignals(False)
            self._update_status_bar()

    def _on_lang_changed(self, lang_name: str):
        editor = self._current_editor()
        if editor:
            editor.set_language(lang_name)

    def _add_new_tab_prompt(self):
        title, ok = QInputDialog.getText(self, "Nueva Pestaña", "Nombre del archivo / pestaña:", text=f"archivo_{self.tab_widget.count()+1}.py")
        if ok and title.strip():
            current_lang = self.lang_combo.currentText()
            self._add_tab(title.strip(), current_lang, "")

    def _rename_active_tab(self):
        idx = self.tab_widget.currentIndex()
        if idx >= 0:
            old_title = self.tab_widget.tabText(idx)
            title, ok = QInputDialog.getText(self, "Renombrar Pestaña", "Nuevo nombre:", text=old_title)
            if ok and title.strip():
                self.tab_widget.setTabText(idx, title.strip())

    def _close_tab(self, index: int):
        if self.tab_widget.count() <= 1:
            QMessageBox.warning(self, "Aviso", "El editor debe conservar al menos una pestaña activa.")
            return
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        if widget:
            widget.deleteLater()

    def _insert_template(self):
        editor = self._current_editor()
        if not editor: return
        lang = self.lang_combo.currentText()
        template_text = CODE_TEMPLATES.get(lang, "// --- Plantilla de código ---")
        if editor.toPlainText().strip():
            reply = QMessageBox.question(
                self, "Confirmar Plantilla",
                "El editor ya contiene texto. ¿Deseas reemplazarlo con la plantilla base?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        editor.setPlainText(template_text)

    def _toggle_comment(self):
        editor = self._current_editor()
        if editor:
            editor.toggle_comment()

    def _duplicate_line(self):
        editor = self._current_editor()
        if editor:
            editor.duplicate_line()

    def _copy_code(self):
        editor = self._current_editor()
        if editor:
            code = editor.toPlainText()
            if code:
                QApplication.clipboard().setText(code)
                QMessageBox.information(self, "Copiado", "Código copiado al portapapeles.")

    def _change_font_size(self, delta: int):
        self.current_font_size = max(9, min(30, self.current_font_size + delta))
        for i in range(self.tab_widget.count()):
            ed = self.tab_widget.widget(i)
            if ed:
                ed.set_font_size(self.current_font_size)

    def _toggle_search_panel(self):
        vis = not self.search_panel.isVisible()
        self.search_panel.setVisible(vis)
        if vis:
            self.search_input.setFocus()
            self.search_input.selectAll()

    def _on_search_text_changed(self, text: str):
        self._find_next()

    def _find_next(self):
        editor = self._current_editor()
        if not editor: return
        text = self.search_input.text()
        if not text:
            self.match_count_lbl.setText("0 coincidencias")
            return
        
        # Buscar coincidencias totales
        doc_text = editor.toPlainText()
        total_matches = doc_text.count(text)
        self.match_count_lbl.setText(f"{total_matches} coincidencias")

        found = editor.find(text)
        if not found:
            # Rebobinar al inicio y re-buscar
            cursor = editor.textCursor()
            cursor.setPosition(0)
            editor.setTextCursor(cursor)
            editor.find(text)

    def _find_prev(self):
        editor = self._current_editor()
        if not editor: return
        text = self.search_input.text()
        if not text: return
        found = editor.find(text, QTextDocument.FindFlag.FindBackward)
        if not found:
            cursor = editor.textCursor()
            cursor.setPosition(len(editor.toPlainText()))
            editor.setTextCursor(cursor)
            editor.find(text, QTextDocument.FindFlag.FindBackward)

    def _replace_one(self):
        editor = self._current_editor()
        if not editor: return
        query = self.search_input.text()
        replacement = self.replace_input.text()
        if not query: return
        cursor = editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == query:
            cursor.insertText(replacement)
        self._find_next()

    def _replace_all(self):
        editor = self._current_editor()
        if not editor: return
        query = self.search_input.text()
        replacement = self.replace_input.text()
        if not query: return
        content = editor.toPlainText()
        new_content = content.replace(query, replacement)
        editor.setPlainText(new_content)
        self.match_count_lbl.setText("Reemplazado todo")

    def _update_status_bar(self):
        editor = self._current_editor()
        if not editor:
            self.status_bar_lbl.setText("Línea: 1 | Columna: 1 | Total Líneas: 1 | Caracteres: 0")
            return
        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        total_lines = editor.blockCount()
        total_chars = len(editor.toPlainText())
        sel_text = f" | Selección: {len(cursor.selectedText())} chars" if cursor.hasSelection() else ""
        self.status_bar_lbl.setText(f"Línea: {line} | Columna: {col} | Total Líneas: {total_lines} | Caracteres: {total_chars}{sel_text}")

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _load_content(self):
        if not os.path.exists(self.storage_dir):
            self._add_tab("main.py", "Python", "")
            return
            
        tabs_path = os.path.join(self.storage_dir, 'tabs.json')
        file_path = os.path.join(self.storage_dir, 'code.txt')
        meta_path = os.path.join(self.storage_dir, 'meta.json')
        
        if os.path.exists(tabs_path):
            try:
                with open(tabs_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    tabs_list = data.get('tabs', [])
                    active_idx = data.get('active_tab', 0)
                    
                    self.tab_widget.blockSignals(True)
                    while self.tab_widget.count():
                        w = self.tab_widget.widget(0)
                        self.tab_widget.removeTab(0)
                        if w: w.deleteLater()
                    self.tab_widget.blockSignals(False)

                    if tabs_list:
                        for tab_item in tabs_list:
                            self._add_tab(
                                tab_item.get('title', 'archivo'),
                                tab_item.get('language', 'Python'),
                                tab_item.get('content', '')
                            )
                        if 0 <= active_idx < self.tab_widget.count():
                            self.tab_widget.setCurrentIndex(active_idx)
                    else:
                        self._add_tab("main.py", "Python", "")
                    return
            except Exception as e:
                print(f"Error loading tabs.json: {e}")

        # Si no existe tabs.json pero existe code.txt (compatibilidad anterior)
        if os.path.exists(file_path):
            try:
                content = ""
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                lang = "Python"
                if os.path.exists(meta_path):
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        lang = meta.get('language', 'Python')
                self._add_tab("main", lang, content)
            except Exception as e:
                print(f"Error loading code.txt: {e}")
                self._add_tab("main.py", "Python", "")
        else:
            self._add_tab("main.py", "Python", "")

    def _save_content(self):
        self._ensure_storage_dir()
        try:
            tabs_path = os.path.join(self.storage_dir, 'tabs.json')
            file_path = os.path.join(self.storage_dir, 'code.txt')
            meta_path = os.path.join(self.storage_dir, 'meta.json')
            
            tabs_data = []
            for i in range(self.tab_widget.count()):
                editor = self.tab_widget.widget(i)
                title = self.tab_widget.tabText(i)
                lang = editor.property("language") or "Python"
                content = editor.toPlainText() if editor else ""
                tabs_data.append({
                    "title": title,
                    "language": lang,
                    "content": content
                })

            data = {
                "active_tab": self.tab_widget.currentIndex(),
                "tabs": tabs_data
            }

            with open(tabs_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

            # Para compatibilidad con lectura única
            active_editor = self._current_editor()
            active_content = active_editor.toPlainText() if active_editor else ""
            active_lang = self.lang_combo.currentText()

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(active_content)
                
            meta = {'language': active_lang}
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2)
                
            QMessageBox.information(self, "Éxito", "Código y pestañas guardados correctamente.")
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el código:\n{str(e)}")


# =============================================================================
# 2. EDITOR DE MAPAS MENTALES (MindMapEditorWidget)
# =============================================================================

class MindMapNodeItem(QGraphicsRectItem):
    """Nodo gráfico para el mapa mental con soporte para cambio de tamaño."""
    def __init__(self, node_id: str, title: str, x: float, y: float, color="#89b4fa", parent_id=None, width=140, height=50):
        self.node_width = max(60, width)
        self.node_height = max(30, height)
        super().__init__(-self.node_width/2, -self.node_height/2, self.node_width, self.node_height)
        self.node_id = node_id
        self.title = title
        self.node_color = color
        self.parent_id = parent_id
        self.setPos(x, y)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.text_item = QGraphicsTextItem(title, self)
        self.text_item.setDefaultTextColor(QColor("#11111b"))
        font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        self.text_item.setFont(font)
        self._recalculate_size()

    def _recalculate_size(self):
        txt_rect = self.text_item.boundingRect()
        w = max(self.node_width, txt_rect.width() + 24)
        h = max(self.node_height, txt_rect.height() + 14)
        self.setRect(-w / 2, -h / 2, w, h)
        self.text_item.setPos(-txt_rect.width() / 2, -txt_rect.height() / 2)
        self.update_style()

    def set_size(self, width: float, height: float):
        self.node_width = max(60, width)
        self.node_height = max(30, height)
        self._recalculate_size()
        scene = self.scene()
        if scene and hasattr(scene, 'update_connections'):
            scene.update_connections()

    def set_title(self, new_title: str):
        self.title = new_title
        self.text_item.setPlainText(new_title)
        self._recalculate_size()

    def set_color(self, hex_color: str):
        self.node_color = hex_color
        self.update_style()

    def update_style(self):
        self.setBrush(QBrush(QColor(self.node_color)))
        self.setPen(QPen(QColor("#45475a"), 2))

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if scene and hasattr(scene, 'update_connections'):
                scene.update_connections()
        return super().itemChange(change, value)


class MindMapScene(QGraphicsScene):
    """Escena interactiva de Mapa Mental."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes = {} # node_id: MindMapNodeItem
        self.connection_lines = []

    def clear_all(self):
        self.clear()
        self.nodes.clear()
        self.connection_lines.clear()

    def add_node(self, node_id: str, title: str, x: float, y: float, color="#89b4fa", parent_id=None, width=140, height=50):
        item = MindMapNodeItem(node_id, title, x, y, color, parent_id, width, height)
        self.addItem(item)
        self.nodes[node_id] = item
        self.update_connections()
        return item

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            item = self.nodes.pop(node_id)
            # Eliminar hijos recursivamente
            children = [nid for nid, n in list(self.nodes.items()) if n.parent_id == node_id]
            for cid in children:
                self.remove_node(cid)
            self.removeItem(item)
            self.update_connections()

    def update_connections(self):
        # Limpiar líneas previas
        for line in self.connection_lines:
            self.removeItem(line)
        self.connection_lines.clear()

        # Dibujar líneas entre padre e hijo
        pen = QPen(QColor("#89b4fa"), 2, Qt.PenStyle.DashLine)
        for nid, node in self.nodes.items():
            if node.parent_id and node.parent_id in self.nodes:
                parent = self.nodes[node.parent_id]
                p1 = parent.pos()
                p2 = node.pos()
                line = self.addLine(QLineF(p1, p2), pen)
                line.setZValue(-1)
                self.connection_lines.append(line)


class MindMapEditorWidget(QWidget):
    """Editor interactivo de mapas mentales."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, item_calc: dict, project_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item_calc = item_calc
        self.project_item = project_item
        self.agenda_path = agenda_path
        
        self.calc_id = item_calc.get('id', 'unknown')
        item_name = project_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, self.calc_id)
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # Barra Superior
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Mapa Mental: <b>{self.item_calc.get('name', 'Sin nombre')}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar Mapa")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Barra de Acciones del Mapa Mental
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_style = "QPushButton { padding: 5px 10px; border-radius: 4px; background: #E0E0E0; color: #111; font-weight: bold; border: 1px solid #AAA; } QPushButton:hover { background: #CCC; }"

        btn_add_child = QPushButton("➕ Agregar Rama / Nodo")
        btn_add_child.setStyleSheet(btn_style)
        btn_add_child.clicked.connect(self._add_child_node)
        toolbar.addWidget(btn_add_child)

        btn_edit_text = QPushButton("✏️ Editar Texto")
        btn_edit_text.setStyleSheet(btn_style)
        btn_edit_text.clicked.connect(self._edit_node_text)
        toolbar.addWidget(btn_edit_text)

        btn_color = QPushButton("🎨 Cambiar Color")
        btn_color.setStyleSheet(btn_style)
        btn_color.clicked.connect(self._change_node_color)
        toolbar.addWidget(btn_color)

        btn_size_inc = QPushButton("🔍 Talla +")
        btn_size_inc.setStyleSheet(btn_style)
        btn_size_inc.clicked.connect(self._resize_node_increase)
        toolbar.addWidget(btn_size_inc)

        btn_size_dec = QPushButton("🔍 Talla -")
        btn_size_dec.setStyleSheet(btn_style)
        btn_size_dec.clicked.connect(self._resize_node_decrease)
        toolbar.addWidget(btn_size_dec)

        btn_size_dialog = QPushButton("📐 Medidas")
        btn_size_dialog.setStyleSheet(btn_style)
        btn_size_dialog.clicked.connect(self._resize_node_dialog)
        toolbar.addWidget(btn_size_dialog)

        btn_delete = QPushButton("🗑️ Eliminar Nodo")
        btn_delete.setStyleSheet("QPushButton { padding: 5px 10px; border-radius: 4px; background: #f38ba8; color: #111; font-weight: bold; } QPushButton:hover { background: #e06c88; }")
        btn_delete.clicked.connect(self._delete_node)
        toolbar.addWidget(btn_delete)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Canvas Gráfico
        self.scene = MindMapScene(self)
        self.scene.setSceneRect(-1000, -1000, 2000, 2000)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("QGraphicsView { background-color: #181825; border: 1px solid #313244; border-radius: 8px; }")
        layout.addWidget(self.view, 1)

    def _get_selected_node(self) -> MindMapNodeItem:
        items = self.scene.selectedItems()
        for it in items:
            if isinstance(it, MindMapNodeItem):
                return it
        return None

    def _add_child_node(self):
        parent = self._get_selected_node()
        parent_id = parent.node_id if parent else "root"
        if parent_id not in self.scene.nodes and self.scene.nodes:
            parent_id = list(self.scene.nodes.keys())[0]

        text, ok = QInputDialog.getText(self, "Nuevo Nodo", "Texto para el nuevo nodo/rama:")
        if ok and text.strip():
            node_id = f"node_{len(self.scene.nodes)+1}_{int(QPointF().x())}"
            parent_node = self.scene.nodes.get(parent_id)
            if parent_node:
                pos = parent_node.pos()
                x = pos.x() + 160
                y = pos.y() + (len(self.scene.nodes) * 30) - 60
            else:
                x, y = 0, 0
                
            colors = ["#a6e3a1", "#f9e2af", "#89b4fa", "#cba6f7", "#f38ba8", "#89dceb"]
            color = colors[len(self.scene.nodes) % len(colors)]
            self.scene.add_node(node_id, text.strip(), x, y, color, parent_id)

    def _edit_node_text(self):
        node = self._get_selected_node()
        if node:
            text, ok = QInputDialog.getText(self, "Editar Nodo", "Nuevo texto:", text=node.title)
            if ok and text.strip():
                node.set_title(text.strip())

    def _change_node_color(self):
        node = self._get_selected_node()
        if node:
            color = QColorDialog.getColor(QColor(node.node_color), self, "Seleccionar Color")
            if color.isValid():
                node.set_color(color.name())

    def _resize_node_increase(self):
        node = self._get_selected_node()
        if node:
            node.set_size(node.node_width + 25, node.node_height + 15)

    def _resize_node_decrease(self):
        node = self._get_selected_node()
        if node:
            node.set_size(max(60, node.node_width - 25), max(30, node.node_height - 15))

    def _resize_node_dialog(self):
        node = self._get_selected_node()
        if node:
            w, ok1 = QInputDialog.getInt(self, "Ancho del Recuadro", "Ancho en píxeles:", int(node.node_width), 60, 1000)
            if ok1:
                h, ok2 = QInputDialog.getInt(self, "Alto del Recuadro", "Alto en píxeles:", int(node.node_height), 30, 1000)
                if ok2:
                    node.set_size(w, h)

    def _delete_node(self):
        node = self._get_selected_node()
        if node:
            if node.node_id == 'root' and len(self.scene.nodes) > 1:
                QMessageBox.warning(self, "Aviso", "No puedes eliminar el nodo raíz si existen subramas.")
                return
            self.scene.remove_node(node.node_id)

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _load_content(self):
        if not os.path.exists(self.storage_dir):
            self._create_default_map()
            return
            
        file_path = os.path.join(self.storage_dir, 'mindmap.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.scene.clear_all()
                    for n in data.get('nodes', []):
                        self.scene.add_node(
                            n['id'], n['title'], n['x'], n['y'], n.get('color', '#89b4fa'), n.get('parent_id'),
                            n.get('width', 140), n.get('height', 50)
                        )
            except Exception as e:
                print(f"Error loading mindmap: {e}")
                self._create_default_map()
        else:
            self._create_default_map()

    def _create_default_map(self):
        self.scene.clear_all()
        root_title = self.project_item.get('name', 'Idea Principal')
        self.scene.add_node('root', root_title, 0, 0, '#89b4fa', None)

    def _save_content(self):
        self._ensure_storage_dir()
        try:
            file_path = os.path.join(self.storage_dir, 'mindmap.json')
            nodes_data = []
            for nid, node in self.scene.nodes.items():
                pos = node.pos()
                nodes_data.append({
                    'id': nid,
                    'title': node.title,
                    'x': pos.x(),
                    'y': pos.y(),
                    'color': node.node_color,
                    'parent_id': node.parent_id,
                    'width': node.node_width,
                    'height': node.node_height
                })
                
            data = {'nodes': nodes_data}
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
                
            QMessageBox.information(self, "Éxito", "Mapa mental guardado correctamente.")
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el mapa mental:\n{str(e)}")


# =============================================================================
# 3. EDITOR DE DIAGRAMAS DE FLUJO DRAW.IO (FlowchartEditorWidget)
# =============================================================================

class FlowchartItem(QGraphicsItem):
    """Elemento interactivo de diagrama de flujo."""
    def __init__(self, item_id: str, shape_type: str, text: str, x: float, y: float, color="#313244"):
        super().__init__()
        self.item_id = item_id
        self.shape_type = shape_type # 'start', 'process', 'decision', 'input'
        self.text = text
        self.bg_color = color
        self.setPos(x, y)
        self.rect = QRectF(-60, -30, 120, 60)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )

        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(QColor("#cdd6f4"))
        self.text_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._center_text()

    def boundingRect(self):
        return self.rect.adjusted(-5, -5, 5, 5)

    def _center_text(self):
        r = self.text_item.boundingRect()
        self.text_item.setPos(-r.width() / 2, -r.height() / 2)

    def set_text(self, text: str):
        self.text = text
        self.text_item.setPlainText(text)
        self._center_text()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(QColor("#89b4fa"), 2)
        if self.isSelected():
            pen = QPen(QColor("#f9e2af"), 3, Qt.PenStyle.DashLine)

        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(self.bg_color)))

        if self.shape_type == 'start': # Oval
            painter.drawRoundedRect(self.rect, 25, 25)
        elif self.shape_type == 'decision': # Rombo
            path = QPainterPath()
            path.moveTo(0, self.rect.top())
            path.lineTo(self.rect.right(), 0)
            path.lineTo(0, self.rect.bottom())
            path.lineTo(self.rect.left(), 0)
            path.closeSubpath()
            painter.drawPath(path)
        elif self.shape_type == 'input': # Paralelogramo
            path = QPainterPath()
            path.moveTo(self.rect.left() + 15, self.rect.top())
            path.lineTo(self.rect.right(), self.rect.top())
            path.lineTo(self.rect.right() - 15, self.rect.bottom())
            path.lineTo(self.rect.left(), self.rect.bottom())
            path.closeSubpath()
            painter.drawPath(path)
        else: # Process (Rectángulo)
            painter.drawRoundedRect(self.rect, 6, 6)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
            scene = self.scene()
            if scene and hasattr(scene, 'update_arrows'):
                scene.update_arrows()
        return super().itemChange(change, value)


class FlowchartScene(QGraphicsScene):
    """Escena interactiva de Diagrama de Flujo Draw.io."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items_dict = {}
        self.connections = [] # (source_id, target_id, label)
        self.arrow_lines = []

    def clear_all(self):
        self.clear()
        self.items_dict.clear()
        self.connections.clear()
        self.arrow_lines.clear()

    def add_flow_item(self, item_id: str, shape_type: str, text: str, x: float, y: float, color="#313244"):
        item = FlowchartItem(item_id, shape_type, text, x, y, color)
        self.addItem(item)
        self.items_dict[item_id] = item
        self.update_arrows()
        return item

    def connect_items(self, source_id: str, target_id: str, label=""):
        if source_id in self.items_dict and target_id in self.items_dict:
            self.connections.append((source_id, target_id, label))
            self.update_arrows()

    def update_arrows(self):
        for line, lbl in self.arrow_lines:
            self.removeItem(line)
            if lbl: self.removeItem(lbl)
        self.arrow_lines.clear()

        pen = QPen(QColor("#a6e3a1"), 2)
        for s_id, t_id, label in self.connections:
            if s_id in self.items_dict and t_id in self.items_dict:
                p1 = self.items_dict[s_id].pos()
                p2 = self.items_dict[t_id].pos()
                line_item = self.addLine(QLineF(p1, p2), pen)
                line_item.setZValue(-1)
                
                txt_item = None
                if label:
                    txt_item = QGraphicsTextItem(label)
                    txt_item.setDefaultTextColor(QColor("#f9e2af"))
                    txt_item.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                    txt_item.setPos((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
                    self.addItem(txt_item)
                    
                self.arrow_lines.append((line_item, txt_item))


class FlowchartEditorWidget(QWidget):
    """Editor de diagramas de flujo con soporte e importación/exportación Draw.io (.xml / .drawio)."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, item_calc: dict, project_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item_calc = item_calc
        self.project_item = project_item
        self.agenda_path = agenda_path
        
        self.calc_id = item_calc.get('id', 'unknown')
        item_name = project_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, self.calc_id)
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 20)
        layout.setSpacing(12)

        # Barra Superior
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Diagrama de Flujo (Draw.io): <b>{self.item_calc.get('name', 'Sin nombre')}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar Diagrama")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Barra de Herramientas de Formas
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)

        btn_style = "QPushButton { padding: 5px 8px; border-radius: 4px; background: #E0E0E0; color: #111; font-weight: bold; border: 1px solid #AAA; font-size: 11px; } QPushButton:hover { background: #CCC; }"

        btn_start = QPushButton("🟢 Inicio / Fin")
        btn_start.setStyleSheet(btn_style)
        btn_start.clicked.connect(lambda: self._add_shape('start', 'Inicio'))
        toolbar.addWidget(btn_start)

        btn_proc = QPushButton("🟦 Proceso")
        btn_proc.setStyleSheet(btn_style)
        btn_proc.clicked.connect(lambda: self._add_shape('process', 'Proceso'))
        toolbar.addWidget(btn_proc)

        btn_dec = QPushButton("🔶 Decisión")
        btn_dec.setStyleSheet(btn_style)
        btn_dec.clicked.connect(lambda: self._add_shape('decision', '¿Condición?'))
        toolbar.addWidget(btn_dec)

        btn_in = QPushButton("▰ E / S")
        btn_in.setStyleSheet(btn_style)
        btn_in.clicked.connect(lambda: self._add_shape('input', 'Entrada / Salida'))
        toolbar.addWidget(btn_in)

        btn_conn = QPushButton("➡️ Conectar")
        btn_conn.setStyleSheet(btn_style)
        btn_conn.clicked.connect(self._connect_selected)
        toolbar.addWidget(btn_conn)

        btn_edit = QPushButton("✏️ Texto")
        btn_edit.setStyleSheet(btn_style)
        btn_edit.clicked.connect(self._edit_selected)
        toolbar.addWidget(btn_edit)

        btn_del = QPushButton("🗑️ Eliminar")
        btn_del.setStyleSheet("QPushButton { padding: 5px 8px; border-radius: 4px; background: #f38ba8; color: #111; font-weight: bold; font-size: 11px; }")
        btn_del.clicked.connect(self._delete_selected)
        toolbar.addWidget(btn_del)

        btn_imp = QPushButton("📥 Importar .drawio")
        btn_imp.setStyleSheet(btn_style)
        btn_imp.clicked.connect(self._import_drawio)
        toolbar.addWidget(btn_imp)

        btn_exp = QPushButton("📤 Exportar .drawio")
        btn_exp.setStyleSheet(btn_style)
        btn_exp.clicked.connect(self._export_drawio)
        toolbar.addWidget(btn_exp)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Canvas Gráfico
        self.scene = FlowchartScene(self)
        self.scene.setSceneRect(-1000, -1000, 2000, 2000)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setStyleSheet("QGraphicsView { background-color: #181825; border: 1px solid #313244; border-radius: 8px; }")
        layout.addWidget(self.view, 1)

    def _get_selected_item(self) -> FlowchartItem:
        items = self.scene.selectedItems()
        for it in items:
            if isinstance(it, FlowchartItem):
                return it
        return None

    def _add_shape(self, shape_type: str, default_text: str):
        text, ok = QInputDialog.getText(self, "Nueva Forma", "Texto para la forma:", QLineEdit.EchoMode.Normal, default_text)
        if ok and text.strip():
            item_id = f"item_{len(self.scene.items_dict)+1}"
            x = (len(self.scene.items_dict) % 4) * 150 - 150
            y = (len(self.scene.items_dict) // 4) * 90 - 100
            self.scene.add_flow_item(item_id, shape_type, text.strip(), x, y)

    def _connect_selected(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, FlowchartItem)]
        if len(items) != 2:
            QMessageBox.information(self, "Conectar Formas", "Selecciona exactamente DOS formas (manteniendo Ctrl) para conectarlas.")
            return

        lbl, ok = QInputDialog.getText(self, "Etiqueta de Conector", "Etiqueta opcional (ej: Sí / No):")
        if ok:
            self.scene.connect_items(items[0].item_id, items[1].item_id, lbl.strip())

    def _edit_selected(self):
        item = self._get_selected_item()
        if item:
            text, ok = QInputDialog.getText(self, "Editar Texto", "Texto:", QLineEdit.EchoMode.Normal, item.text)
            if ok and text.strip():
                item.set_text(text.strip())

    def _delete_selected(self):
        items = [it for it in self.scene.selectedItems() if isinstance(it, FlowchartItem)]
        for item in items:
            iid = item.item_id
            if iid in self.scene.items_dict:
                del self.scene.items_dict[iid]
                self.scene.removeItem(item)
            # Eliminar conexiones asociadas
            self.scene.connections = [c for c in self.scene.connections if c[0] != iid and c[1] != iid]
        self.scene.update_arrows()

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _load_content(self):
        if not os.path.exists(self.storage_dir):
            self._create_default_flowchart()
            return
            
        file_path = os.path.join(self.storage_dir, 'diagram.drawio')
        if os.path.exists(file_path):
            self._parse_drawio_xml(file_path)
        else:
            self._create_default_flowchart()

    def _create_default_flowchart(self):
        self.scene.clear_all()
        i1 = self.scene.add_flow_item('i1', 'start', 'Inicio', -100, -100)
        i2 = self.scene.add_flow_item('i2', 'process', 'Procesar Datos', -100, 0)
        i3 = self.scene.add_flow_item('i3', 'decision', '¿Es Válido?', -100, 100)
        i4 = self.scene.add_flow_item('i4', 'start', 'Fin', -100, 200)
        self.scene.connect_items('i1', 'i2')
        self.scene.connect_items('i2', 'i3')
        self.scene.connect_items('i3', 'i4', 'Sí')

    def _save_content(self):
        self._ensure_storage_dir()
        try:
            file_path = os.path.join(self.storage_dir, 'diagram.drawio')
            xml_str = self._generate_drawio_xml()
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_str)
                
            QMessageBox.information(self, "Éxito", "Diagrama de flujo (Draw.io) guardado correctamente.")
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el diagrama:\n{str(e)}")

    def _generate_drawio_xml(self) -> str:
        """Genera el XML en formato compatible con Draw.io (.drawio)."""
        root = ET.Element("mxfile")
        diagram = ET.SubElement(root, "diagram", name="Flowchart")
        graph = ET.SubElement(diagram, "mxGraphModel")
        root_cell = ET.SubElement(graph, "root")
        
        ET.SubElement(root_cell, "mxCell", id="0")
        ET.SubElement(root_cell, "mxCell", id="1", parent="0")

        # Nodos
        for iid, item in self.scene.items_dict.items():
            pos = item.pos()
            shape_style = "ellipse;whiteSpace=wrap;html=1;" if item.shape_type == 'start' else "rhombus;whiteSpace=wrap;html=1;" if item.shape_type == 'decision' else "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;" if item.shape_type == 'input' else "rounded=1;whiteSpace=wrap;html=1;"
            cell = ET.SubElement(root_cell, "mxCell", id=iid, value=item.text, style=shape_style, vertex="1", parent="1")
            ET.SubElement(cell, "mxGeometry", x=str(pos.x()), y=str(pos.y()), width="120", height="60", **{"as": "geometry"})

        # Conexiones
        for idx, (sid, tid, lbl) in enumerate(self.scene.connections):
            cid = f"edge_{idx+1}"
            cell = ET.SubElement(root_cell, "mxCell", id=cid, value=lbl, style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;", edge="1", parent="1", source=sid, target=tid)
            ET.SubElement(cell, "mxGeometry", **{"relative": "1", "as": "geometry"})

        return ET.tostring(root, encoding="unicode")

    def _parse_drawio_xml(self, file_path: str):
        """Parsea un archivo .drawio / XML e importa los nodos y conectores."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            self.scene.clear_all()
            
            for cell in root.iter("mxCell"):
                cid = cell.get("id")
                if cid in ("0", "1"): continue
                
                is_vertex = cell.get("vertex") == "1"
                is_edge = cell.get("edge") == "1"
                val = cell.get("value", "")
                
                if is_vertex:
                    geom = cell.find("mxGeometry")
                    x = float(geom.get("x", 0)) if geom is not None else 0
                    y = float(geom.get("y", 0)) if geom is not None else 0
                    style = cell.get("style", "")
                    
                    stype = 'start' if 'ellipse' in style else 'decision' if 'rhombus' in style else 'input' if 'parallelogram' in style else 'process'
                    self.scene.add_flow_item(cid, stype, val or "Nodo", x, y)
                elif is_edge:
                    sid = cell.get("source")
                    tid = cell.get("target")
                    if sid and tid:
                        self.scene.connect_items(sid, tid, val)
        except Exception as e:
            print(f"Error parsing drawio xml: {e}")
            self._create_default_flowchart()

    def _export_drawio(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Diagrama Draw.io", "diagrama.drawio", "Draw.io Files (*.drawio *.xml)")
        if file_path:
            try:
                xml_str = self._generate_drawio_xml()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                QMessageBox.information(self, "Exportado", f"Diagrama exportado correctamente a:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al exportar:\n{str(e)}")

    def _import_drawio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Importar Diagrama Draw.io", "", "Draw.io Files (*.drawio *.xml)")
        if file_path:
            self._parse_drawio_xml(file_path)
            QMessageBox.information(self, "Importado", "Diagrama importado correctamente.")


# =============================================================================
# 4. EDITOR DE DIBUJO ESTILO PAINT (PaintEditorWidget)
# =============================================================================

class PaintCanvas(QWidget):
    """Lienzo gráfico interactivo estilo Paint."""
    def __init__(self, width=1280, height=720, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self.image = QImage(self.size(), QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(QColor("#ffffff"))

        self.tool = "pen"  # pen, brush, line, rect, ellipse, fill, eraser, text
        self.pen_color = QColor("#000000")
        self.fill_color = QColor("#89b4fa")
        self.use_fill = False
        self.pen_width = 3

        self.drawing = False
        self.last_point = QPoint()
        self.start_point = QPoint()
        self.temp_image = None

        self.undo_stack = []
        self.redo_stack = []
        self._save_undo_state()

    def _save_undo_state(self):
        if len(self.undo_stack) >= 20:
            self.undo_stack.pop(0)
        self.undo_stack.append(self.image.copy())
        self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.image = self.undo_stack[-1].copy()
            self.update()

    def redo(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state.copy())
            self.image = state.copy()
            self.update()

    def clear_canvas(self):
        self._save_undo_state()
        self.image.fill(QColor("#ffffff"))
        self.update()

    def load_image(self, file_path: str):
        if os.path.exists(file_path):
            img = load_image_qimage(file_path)
            if not img.isNull():
                self._save_undo_state()
                self.image = img.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.drawing and self.temp_image:
            painter.drawImage(0, 0, self.temp_image)
        else:
            painter.drawImage(0, 0, self.image)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drawing = True
            self.last_point = event.pos()
            self.start_point = event.pos()

            if self.tool == "fill":
                self._flood_fill(event.pos(), self.fill_color if self.use_fill else self.pen_color)
                self.drawing = False
            elif self.tool == "text":
                text, ok = QInputDialog.getText(self, "Insertar Texto", "Texto a dibujar:")
                if ok and text.strip():
                    self._save_undo_state()
                    p = QPainter(self.image)
                    p.setPen(QPen(self.pen_color))
                    p.setFont(QFont("Segoe UI", self.pen_width * 3, QFont.Weight.Bold))
                    p.drawText(event.pos(), text.strip())
                    p.end()
                    self.update()
                self.drawing = False

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self.drawing:
            if self.tool in ("pen", "brush", "eraser"):
                p = QPainter(self.image)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                color = QColor("#ffffff") if self.tool == "eraser" else self.pen_color
                w = self.pen_width * 3 if self.tool == "brush" else (self.pen_width * 4 if self.tool == "eraser" else self.pen_width)
                p.setPen(QPen(color, w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                p.drawLine(self.last_point, event.pos())
                p.end()
                self.last_point = event.pos()
                self.update()
            elif self.tool in ("line", "rect", "ellipse"):
                self.temp_image = self.image.copy()
                p = QPainter(self.temp_image)
                p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.setPen(QPen(self.pen_color, self.pen_width))
                if self.use_fill:
                    p.setBrush(QBrush(self.fill_color))
                else:
                    p.setBrush(Qt.BrushStyle.NoBrush)

                if self.tool == "line":
                    p.drawLine(self.start_point, event.pos())
                elif self.tool == "rect":
                    r = QRect(self.start_point, event.pos()).normalized()
                    p.drawRect(r)
                elif self.tool == "ellipse":
                    r = QRect(self.start_point, event.pos()).normalized()
                    p.drawEllipse(r)
                p.end()
                self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.drawing:
            self.drawing = False
            if self.tool in ("line", "rect", "ellipse") and self.temp_image:
                self.image = self.temp_image.copy()
                self.temp_image = None
            self._save_undo_state()
            self.update()

    def _flood_fill(self, pos: QPoint, fill_color: QColor):
        target_color = self.image.pixelColor(pos)
        if target_color == fill_color:
            return

        self._save_undo_state()
        w, h = self.image.width(), self.image.height()
        target_rgb = target_color.rgb()
        fill_rgb = fill_color.rgb()

        pixels = [pos]
        visited = set()

        while pixels:
            p = pixels.pop()
            x, y = p.x(), p.y()
            if (x, y) in visited or x < 0 or x >= w or y < 0 or y >= h:
                continue
            visited.add((x, y))

            if self.image.pixelColor(x, y).rgb() == target_rgb:
                self.image.setPixelColor(x, y, fill_color)
                pixels.append(QPoint(x + 1, y))
                pixels.append(QPoint(x - 1, y))
                pixels.append(QPoint(x, y + 1))
                pixels.append(QPoint(x, y - 1))
        self.update()


class PaintEditorWidget(QWidget):
    """Editor de dibujo interactivo tipo Paint."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, item_calc: dict, project_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item_calc = item_calc
        self.project_item = project_item
        self.agenda_path = agenda_path
        
        self.calc_id = item_calc.get('id', 'unknown')
        item_name = project_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, self.calc_id)
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Barra Superior
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Editor de Dibujo (Paint): <b>{self.item_calc.get('name', 'Sin nombre')}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar Dibujo")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Toolbar de Herramientas
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        btn_style = "QPushButton { padding: 4px 8px; border-radius: 4px; background: #E0E0E0; color: #111; border: 1px solid #AAA; font-weight: bold; font-size: 11px; } QPushButton:hover { background: #CCC; }"

        tools = [
            ("✏️ Lápiz", "pen"), ("🖌️ Pincel", "brush"), ("📏 Línea", "line"),
            ("🔲 Cuadro", "rect"), ("⚪ Elipse", "ellipse"), ("🪣 Relleno", "fill"),
            ("🧹 Goma", "eraser"), ("🔤 Texto", "text")
        ]
        for label, tool_id in tools:
            btn = QPushButton(label)
            btn.setStyleSheet(btn_style)
            btn.clicked.connect(lambda _, t=tool_id: self._set_tool(t))
            toolbar.addWidget(btn)

        toolbar.addSpacing(10)

        # Muestras de Color
        self.btn_pen_color = QPushButton("Color Trazo")
        self.btn_pen_color.setStyleSheet("background-color: #000000; color: #ffffff; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        self.btn_pen_color.clicked.connect(self._pick_pen_color)
        toolbar.addWidget(self.btn_pen_color)

        self.btn_fill_color = QPushButton("Color Relleno")
        self.btn_fill_color.setStyleSheet("background-color: #89b4fa; color: #11111b; font-weight: bold; padding: 4px 8px; border-radius: 4px;")
        self.btn_fill_color.clicked.connect(self._pick_fill_color)
        toolbar.addWidget(self.btn_fill_color)

        self.chk_fill = QCheckBox("Rellenar")
        self.chk_fill.toggled.connect(self._toggle_use_fill)
        toolbar.addWidget(self.chk_fill)

        lbl_w = QLabel("Grosor:")
        toolbar.addWidget(lbl_w)
        self.spin_width = QSpinBox()
        self.spin_width.setRange(1, 50)
        self.spin_width.setValue(3)
        self.spin_width.valueChanged.connect(self._on_width_changed)
        toolbar.addWidget(self.spin_width)

        btn_undo = QPushButton("↩ Deshacer")
        btn_undo.setStyleSheet(btn_style)
        btn_undo.clicked.connect(lambda: self.canvas.undo())
        toolbar.addWidget(btn_undo)

        btn_redo = QPushButton("↪ Rehacer")
        btn_redo.setStyleSheet(btn_style)
        btn_redo.clicked.connect(lambda: self.canvas.redo())
        toolbar.addWidget(btn_redo)

        btn_clear = QPushButton("🧹 Limpiar")
        btn_clear.setStyleSheet("QPushButton { padding: 4px 8px; border-radius: 4px; background: #f38ba8; color: #111; font-weight: bold; font-size: 11px; }")
        btn_clear.clicked.connect(lambda: self.canvas.clear_canvas())
        toolbar.addWidget(btn_clear)

        btn_import = QPushButton("📁 Cargar Foto")
        btn_import.setStyleSheet(btn_style)
        btn_import.clicked.connect(self._import_image)
        toolbar.addWidget(btn_import)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Canvas en contenedor desplazable
        scroll_widget = QWidget()
        sw_layout = QVBoxLayout(scroll_widget)
        self.canvas = PaintCanvas(1280, 720, self)
        sw_layout.addWidget(self.canvas, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(scroll_widget, 1)

    def _set_tool(self, tool_name: str):
        self.canvas.tool = tool_name

    def _pick_pen_color(self):
        c = QColorDialog.getColor(self.canvas.pen_color, self, "Color del Trazo")
        if c.isValid():
            self.canvas.pen_color = c
            self.btn_pen_color.setStyleSheet(f"background-color: {c.name()}; color: {'#fff' if c.lightness() < 128 else '#000'}; font-weight: bold; padding: 4px 8px; border-radius: 4px;")

    def _pick_fill_color(self):
        c = QColorDialog.getColor(self.canvas.fill_color, self, "Color de Relleno")
        if c.isValid():
            self.canvas.fill_color = c
            self.btn_fill_color.setStyleSheet(f"background-color: {c.name()}; color: {'#fff' if c.lightness() < 128 else '#000'}; font-weight: bold; padding: 4px 8px; border-radius: 4px;")

    def _toggle_use_fill(self, checked: bool):
        self.canvas.use_fill = checked

    def _on_width_changed(self, val: int):
        self.canvas.pen_width = val

    def _import_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Cargar Imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.svg)")
        if path:
            self.canvas.load_image(path)

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _load_content(self):
        if not os.path.exists(self.storage_dir): return
        file_path = os.path.join(self.storage_dir, 'drawing.png')
        if os.path.exists(file_path):
            self.canvas.load_image(file_path)

    def _save_content(self):
        self._ensure_storage_dir()
        try:
            file_path = os.path.join(self.storage_dir, 'drawing.png')
            self.canvas.image.save(file_path, "PNG")
            QMessageBox.information(self, "Éxito", "Dibujo guardado correctamente.")
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar el dibujo:\n{str(e)}")


# =============================================================================
# 5. VISOR DE ARCHIVOS 3D STL Y G-CODE (STL3DViewerWidget)
# =============================================================================

class STL3DCanvas(QWidget):
    """Lienzo de renderizado 3D e inspección de trayectorias G-Code."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.facets = []      # list of ((nx,ny,nz), (x1,y1,z1), (x2,y2,z2), (x3,y3,z3))
        self.gcode_layers = [] # list of [{'z': height, 'paths': [[(x1,y1,z1),(x2,y2,z2)], ...]}]
        
        self.mode = "solid"    # 'solid', 'wireframe', 'gcode'
        self.rot_x = -60.0
        self.rot_y = 30.0
        self.scale = 1.0
        self.pan_offset = QPointF(0, 0)
        self.last_mouse_pos = QPoint()
        self.selected_layer = -1

        self.center_x = 0.0
        self.center_y = 0.0
        self.center_z = 0.0
        self.size_x = 0.0
        self.size_y = 0.0
        self.size_z = 0.0

    def load_stl(self, facets, bbox):
        self.facets = facets
        self.gcode_layers = []
        self.mode = "solid"
        min_x, max_x, min_y, max_y, min_z, max_z = bbox
        self.center_x = (min_x + max_x) / 2.0
        self.center_y = (min_y + max_y) / 2.0
        self.center_z = (min_z + max_z) / 2.0
        self.size_x = max_x - min_x
        self.size_y = max_y - min_y
        self.size_z = max_z - min_z
        max_dim = max(1.0, max(self.size_x, self.size_y, self.size_z))
        self.scale = min(self.width(), self.height()) / (max_dim * 2.5)
        self.update()

    def load_gcode(self, layers, bbox):
        self.gcode_layers = layers
        self.facets = []
        self.mode = "gcode"
        min_x, max_x, min_y, max_y, min_z, max_z = bbox
        self.center_x = (min_x + max_x) / 2.0
        self.center_y = (min_y + max_y) / 2.0
        self.center_z = (min_z + max_z) / 2.0
        self.size_x = max_x - min_x
        self.size_y = max_y - min_y
        self.size_z = max_z - min_z
        max_dim = max(1.0, max(self.size_x, self.size_y, self.size_z))
        self.scale = min(self.width(), self.height()) / (max_dim * 2.5)
        self.selected_layer = len(layers) - 1
        self.update()

    def _project_point(self, x, y, z):
        cx, cy, cz = x - self.center_x, y - self.center_y, z - self.center_z
        rad_x = math.radians(self.rot_x)
        rad_y = math.radians(self.rot_y)

        # Rotate X
        y1 = cy * math.cos(rad_x) - cz * math.sin(rad_x)
        z1 = cy * math.sin(rad_x) + cz * math.cos(rad_x)

        # Rotate Y
        x2 = cx * math.cos(rad_y) + z1 * math.sin(rad_y)
        z2 = -cx * math.sin(rad_y) + z1 * math.cos(rad_y)

        screen_x = self.width() / 2.0 + x2 * self.scale + self.pan_offset.x()
        screen_y = self.height() / 2.0 - y1 * self.scale + self.pan_offset.y()
        return screen_x, screen_y, z2

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#181825"))

        if self.mode in ("solid", "wireframe") and self.facets:
            self._draw_stl(painter)
        elif self.mode == "gcode" and self.gcode_layers:
            self._draw_gcode(painter)
        else:
            painter.setPen(QColor("#6c7086"))
            painter.setFont(QFont("Segoe UI", 12))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin modelo 3D / G-Code cargado.\nHaz clic en '📂 Cargar Archivo'.")

    def _draw_stl(self, painter: QPainter):
        lx, ly, lz = 0.577, -0.577, 0.577
        projected = []
        for normal, v1, v2, v3 in self.facets:
            sx1, sy1, z1 = self._project_point(*v1)
            sx2, sy2, z2 = self._project_point(*v2)
            sx3, sy3, z3 = self._project_point(*v3)
            avg_z = (z1 + z2 + z3) / 3.0

            nx, ny, nz = normal
            dot = max(0.25, (nx * lx + ny * ly + nz * lz))
            projected.append((avg_z, (sx1, sy1), (sx2, sy2), (sx3, sy3), dot))

        projected.sort(key=lambda t: t[0])
        base_color = QColor("#89b4fa")

        for avg_z, p1, p2, p3, dot in projected:
            poly = QPolygonF([QPointF(*p1), QPointF(*p2), QPointF(*p3)])
            if self.mode == "solid":
                r = int(base_color.red() * dot)
                g = int(base_color.green() * dot)
                b = int(base_color.blue() * dot)
                painter.setBrush(QBrush(QColor(r, g, b)))
                painter.setPen(QPen(QColor(r // 2, g // 2, b // 2), 0.5))
                painter.drawPolygon(poly)
            else:
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.setPen(QPen(QColor("#89dceb"), 1.0))
                painter.drawPolygon(poly)

    def _draw_gcode(self, painter: QPainter):
        layers_to_draw = self.gcode_layers[:self.selected_layer + 1] if self.selected_layer >= 0 else self.gcode_layers
        for l_idx, layer in enumerate(layers_to_draw):
            color = QColor.fromHsv((l_idx * 15) % 360, 200, 240)
            pen = QPen(color, 1.5)
            painter.setPen(pen)
            for p1, p2 in layer.get('paths', []):
                sx1, sy1, _ = self._project_point(*p1)
                sx2, sy2, _ = self._project_point(*p2)
                painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        pos = event.pos()
        dx = pos.x() - self.last_mouse_pos.x()
        dy = pos.y() - self.last_mouse_pos.y()

        if event.buttons() & Qt.MouseButton.LeftButton:
            self.rot_y += dx * 0.5
            self.rot_x += dy * 0.5
            self.update()
        elif event.buttons() & (Qt.MouseButton.RightButton | Qt.MouseButton.MiddleButton):
            self.pan_offset += QPointF(dx, dy)
            self.update()

        self.last_mouse_pos = pos

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale *= 1.15
        else:
            self.scale /= 1.15
        self.update()


class STL3DViewerWidget(QWidget):
    """Visor completo para archivos 3D STL y trayectorias G-Code."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, item_calc: dict, project_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item_calc = item_calc
        self.project_item = project_item
        self.agenda_path = agenda_path
        
        self.calc_id = item_calc.get('id', 'unknown')
        item_name = project_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, self.calc_id)
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Barra Superior
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Visor 3D STL / G-Code: <b>{self.item_calc.get('name', 'Sin nombre')}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        btn_style = "QPushButton { padding: 4px 8px; border-radius: 4px; background: #E0E0E0; color: #111; border: 1px solid #AAA; font-weight: bold; font-size: 11px; } QPushButton:hover { background: #CCC; }"

        btn_load = QPushButton("📂 Cargar STL / G-Code")
        btn_load.setStyleSheet("QPushButton { padding: 4px 10px; border-radius: 4px; background: #89b4fa; color: #111; border: 1px solid #74c7ec; font-weight: bold; }")
        btn_load.clicked.connect(self._open_file_dialog)
        toolbar.addWidget(btn_load)

        toolbar.addWidget(QLabel("Modo:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Sólido 3D", "Malla 3D", "Ruta G-Code"])
        self.mode_combo.setStyleSheet("QComboBox { padding: 4px 8px; border-radius: 4px; border: 1px solid #CCC; background: #FFF; color: #111; font-weight: bold; }")
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        toolbar.addWidget(self.mode_combo)

        btn_iso = QPushButton("🎲 Isométrica")
        btn_iso.setStyleSheet(btn_style)
        btn_iso.clicked.connect(lambda: self._set_preset_view(-60, 30))
        toolbar.addWidget(btn_iso)

        btn_top = QPushButton("⬆️ Superior")
        btn_top.setStyleSheet(btn_style)
        btn_top.clicked.connect(lambda: self._set_preset_view(-90, 0))
        toolbar.addWidget(btn_top)

        btn_front = QPushButton("👁️ Frontal")
        btn_front.setStyleSheet(btn_style)
        btn_front.clicked.connect(lambda: self._set_preset_view(0, 0))
        toolbar.addWidget(btn_front)

        btn_reset = QPushButton("🎯 Centrar")
        btn_reset.setStyleSheet(btn_style)
        btn_reset.clicked.connect(self._reset_camera)
        toolbar.addWidget(btn_reset)

        self.layer_lbl = QLabel("Capa: -/-")
        self.layer_lbl.setStyleSheet("font-weight: bold; color: #333;")
        toolbar.addWidget(self.layer_lbl)

        self.layer_slider = QSlider(Qt.Orientation.Horizontal)
        self.layer_slider.setRange(0, 1)
        self.layer_slider.valueChanged.connect(self._on_layer_slider_changed)
        toolbar.addWidget(self.layer_slider)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Splitter central
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.canvas_3d = STL3DCanvas(self)
        splitter.addWidget(self.canvas_3d)

        # Panel Lateral Info
        side_panel = QFrame()
        side_panel.setMaximumWidth(340)
        side_panel.setStyleSheet("""
            QFrame { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px; }
            QLabel { color: #cdd6f4; font-size: 12px; }
            QTextEdit { background-color: #181825; color: #a6e3a1; font-family: monospace; font-size: 11px; border: none; }
        """)
        sp_layout = QVBoxLayout(side_panel)
        sp_layout.setContentsMargins(10, 10, 10, 10)
        sp_layout.setSpacing(8)

        sp_layout.addWidget(QLabel("<b>Información del Modelo:</b>"))
        self.info_lbl = QLabel("Dimensiones: —\nTriángulos: —\nVolumen: —")
        self.info_lbl.setWordWrap(True)
        sp_layout.addWidget(self.info_lbl)

        sp_layout.addWidget(QLabel("<b>Inspección G-Code:</b>"))
        self.gcode_text = QTextEdit()
        self.gcode_text.setReadOnly(True)
        sp_layout.addWidget(self.gcode_text, 1)

        splitter.addWidget(side_panel)
        splitter.setSizes([750, 250])
        layout.addWidget(splitter, 1)

    def _on_mode_changed(self, mode_text: str):
        if mode_text == "Sólido 3D":
            self.canvas_3d.mode = "solid"
        elif mode_text == "Malla 3D":
            self.canvas_3d.mode = "wireframe"
        else:
            self.canvas_3d.mode = "gcode"
        self.canvas_3d.update()

    def _set_preset_view(self, rx: float, ry: float):
        self.canvas_3d.rot_x = rx
        self.canvas_3d.rot_y = ry
        self.canvas_3d.update()

    def _reset_camera(self):
        self.canvas_3d.rot_x = -60.0
        self.canvas_3d.rot_y = 30.0
        self.canvas_3d.pan_offset = QPointF(0, 0)
        self.canvas_3d.update()

    def _on_layer_slider_changed(self, val: int):
        self.canvas_3d.selected_layer = val
        total = len(self.canvas_3d.gcode_layers)
        self.layer_lbl.setText(f"Capa: {val + 1}/{total}" if total else "Capa: -/-")
        self.canvas_3d.update()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Archivo 3D / G-Code", "", "Archivos 3D (*.stl *.gcode *.g)")
        if path:
            self._process_file(path)

    def _process_file(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.stl':
            facets, bbox = self._parse_stl(file_path)
            if facets:
                self.canvas_3d.load_stl(facets, bbox)
                dim_x, dim_y, dim_z = self.canvas_3d.size_x, self.canvas_3d.size_y, self.canvas_3d.size_z
                self.info_lbl.setText(
                    f"Archivo: {os.path.basename(file_path)}\n"
                    f"Dimensiones: {dim_x:.1f} x {dim_y:.1f} x {dim_z:.1f} mm\n"
                    f"Triángulos: {len(facets):,}\n"
                    f"Caja Delimitadora: X({dim_x:.1f}) Y({dim_y:.1f}) Z({dim_z:.1f})"
                )
                self.gcode_text.setText("// Archivo STL cargado correctamente.\n// Visualización 3D activa.")
                self._save_imported_file(file_path, 'model.stl')
        elif ext in ('.gcode', '.g'):
            layers, bbox, code_lines = self._parse_gcode(file_path)
            if layers:
                self.canvas_3d.load_gcode(layers, bbox)
                self.layer_slider.setRange(0, len(layers) - 1)
                self.layer_slider.setValue(len(layers) - 1)
                self.layer_lbl.setText(f"Capa: {len(layers)}/{len(layers)}")
                dim_x, dim_y, dim_z = self.canvas_3d.size_x, self.canvas_3d.size_y, self.canvas_3d.size_z
                self.info_lbl.setText(
                    f"Archivo G-Code: {os.path.basename(file_path)}\n"
                    f"Volumen Impresión: {dim_x:.1f} x {dim_y:.1f} x {dim_z:.1f} mm\n"
                    f"Total de Capas Z: {len(layers)}\n"
                    f"Líneas G-Code: {len(code_lines):,}"
                )
                self.gcode_text.setText("\n".join(code_lines[:500]))
                self._save_imported_file(file_path, 'model.gcode')

    def _parse_stl(self, file_path: str):
        facets = []
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')

        try:
            with open(file_path, 'rb') as f:
                header = f.read(80)
                if len(header) < 80: return [], (0,0,0,0,0,0)
                count_bytes = f.read(4)
                if len(count_bytes) == 4:
                    count = struct.unpack('<I', count_bytes)[0]
                    expected = 84 + count * 50
                    if os.path.getsize(file_path) == expected:
                        for _ in range(count):
                            data = f.read(50)
                            if len(data) < 50: break
                            nx, ny, nz, x1, y1, z1, x2, y2, z2, x3, y3, z3 = struct.unpack('<12f', data[:48])
                            facets.append(((nx, ny, nz), (x1, y1, z1), (x2, y2, z2), (x3, y3, z3)))
                            for x, y, z in ((x1,y1,z1), (x2,y2,z2), (x3,y3,z3)):
                                min_x, max_x = min(min_x, x), max(max_x, x)
                                min_y, max_y = min(min_y, y), max(max_y, y)
                                min_z, max_z = min(min_z, z), max(max_z, z)
                        return facets, (min_x, max_x, min_y, max_y, min_z, max_z)

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            cur_normal = (0.0, 0.0, 1.0)
            cur_verts = []
            for line in lines:
                line_s = line.strip().lower()
                if line_s.startswith("facet normal"):
                    parts = line_s.split()
                    if len(parts) >= 5:
                        cur_normal = (float(parts[2]), float(parts[3]), float(parts[4]))
                elif line_s.startswith("vertex"):
                    parts = line_s.split()
                    if len(parts) >= 4:
                        v = (float(parts[1]), float(parts[2]), float(parts[3]))
                        cur_verts.append(v)
                        min_x, max_x = min(min_x, v[0]), max(max_x, v[0])
                        min_y, max_y = min(min_y, v[1]), max(max_y, v[1])
                        min_z, max_z = min(min_z, v[2]), max(max_z, v[2])
                elif line_s.startswith("endfacet"):
                    if len(cur_verts) == 3:
                        facets.append((cur_normal, cur_verts[0], cur_verts[1], cur_verts[2]))
                    cur_verts = []
            return facets, (min_x, max_x, min_y, max_y, min_z, max_z)

        except Exception as e:
            print(f"Error parsing STL: {e}")
            return [], (0,0,0,0,0,0)

    def _parse_gcode(self, file_path: str):
        layers = []
        code_lines = []
        min_x = min_y = min_z = float('inf')
        max_x = max_y = max_z = float('-inf')

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            code_lines = lines
            cur_x = cur_y = cur_z = 0.0
            cur_paths = []
            cur_layer_z = 0.0

            for line in lines:
                line_s = line.strip()
                if not line_s or line_s.startswith(';'): continue
                parts = line_s.split()
                cmd = parts[0].upper()
                if cmd in ('G0', 'G1', 'G00', 'G01'):
                    nx, ny, nz = cur_x, cur_y, cur_z
                    is_move = False
                    for p in parts[1:]:
                        if p.upper().startswith('X'):
                            nx = float(p[1:])
                            is_move = True
                        elif p.upper().startswith('Y'):
                            ny = float(p[1:])
                            is_move = True
                        elif p.upper().startswith('Z'):
                            nz = float(p[1:])
                            is_move = True

                    if nz != cur_layer_z and cur_paths:
                        layers.append({'z': cur_layer_z, 'paths': list(cur_paths)})
                        cur_paths = []
                        cur_layer_z = nz

                    if is_move:
                        cur_paths.append(((cur_x, cur_y, cur_z), (nx, ny, nz)))
                        min_x, max_x = min(min_x, nx), max(max_x, nx)
                        min_y, max_y = min(min_y, ny), max(max_y, ny)
                        min_z, max_z = min(min_z, nz), max(max_z, nz)

                    cur_x, cur_y, cur_z = nx, ny, nz

            if cur_paths:
                layers.append({'z': cur_layer_z, 'paths': cur_paths})

            return layers, (min_x, max_x, min_y, max_y, min_z, max_z), code_lines

        except Exception as e:
            print(f"Error parsing G-Code: {e}")
            return [], (0,0,0,0,0,0), []

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _save_imported_file(self, source_path: str, target_name: str):
        self._ensure_storage_dir()
        try:
            dest = os.path.join(self.storage_dir, target_name)
            shutil.copy2(source_path, dest)
        except Exception as e:
            print(f"Error saving imported file: {e}")

    def _load_content(self):
        if not os.path.exists(self.storage_dir): return
        stl_path = os.path.join(self.storage_dir, 'model.stl')
        gcode_path = os.path.join(self.storage_dir, 'model.gcode')

        if os.path.exists(stl_path):
            self._process_file(stl_path)
        elif os.path.exists(gcode_path):
            self._process_file(gcode_path)

    def _save_content(self):
        self._ensure_storage_dir()
        QMessageBox.information(self, "Éxito", "Modelo 3D / G-Code guardado en el proyecto.")
        self.saved.emit()


# =============================================================================
# 6. VISOR DE ARCHIVOS KICAD Y GERBER (GerberKiCadViewerWidget)
# =============================================================================

class GerberCanvas(QGraphicsView):
    """Lienzo vectorial interactivo para capas PCB Gerber y proyectos KiCad."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setStyleSheet("QGraphicsView { background-color: #181825; border: 1px solid #313244; border-radius: 8px; }")

        self.measuring = False
        self.measure_points = []
        self.measure_line = None
        self.measure_text = None

    def enable_measurement(self, enabled: bool):
        self.measuring = enabled
        self.measure_points.clear()
        if self.measure_line:
            self.scene.removeItem(self.measure_line)
            self.measure_line = None
        if self.measure_text:
            self.scene.removeItem(self.measure_text)
            self.measure_text = None

    def mousePressEvent(self, event):
        if self.measuring and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            self.measure_points.append(scene_pos)
            if len(self.measure_points) == 2:
                p1, p2 = self.measure_points
                dx = p2.x() - p1.x()
                dy = p2.y() - p1.y()
                dist_mm = math.hypot(dx, dy)
                dist_in = dist_mm / 25.4

                pen = QPen(QColor("#f9e2af"), 2, Qt.PenStyle.DashLine)
                if self.measure_line: self.scene.removeItem(self.measure_line)
                self.measure_line = self.scene.addLine(QLineF(p1, p2), pen)

                if self.measure_text: self.scene.removeItem(self.measure_text)
                self.measure_text = QGraphicsTextItem(f"📐 {dist_mm:.2f} mm ({dist_in:.3f} in)")
                self.measure_text.setDefaultTextColor(QColor("#f9e2af"))
                self.measure_text.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.measure_text.setPos((p1.x() + p2.x()) / 2, (p1.y() + p2.y()) / 2)
                self.scene.addItem(self.measure_text)

                self.measure_points.clear()
        else:
            super().mousePressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        factor = 1.15 if delta > 0 else 1 / 1.15
        self.scale(factor, factor)


class GerberKiCadViewerWidget(QWidget):
    """Visor multicapa completo para proyectos KiCad y archivos Gerber (.gbr / .kicad_pcb)."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    LAYER_COLORS = {
        'Top Copper (F.Cu)': '#d4af37',
        'Bottom Copper (B.Cu)': '#b85434',
        'Top Silk (F.SilkS)': '#ffffff',
        'Bottom Silk (B.SilkS)': '#a6adc8',
        'Top Mask (F.Mask)': '#0f3b23',
        'Bottom Mask (B.Mask)': '#1a472a',
        'Edge Cuts (Borde)': '#f9e2af',
        'Drill Holes (Perforaciones)': '#181825',
    }

    def __init__(self, item_calc: dict, project_item: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.item_calc = item_calc
        self.project_item = project_item
        self.agenda_path = agenda_path
        
        self.calc_id = item_calc.get('id', 'unknown')
        item_name = project_item.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        
        self.storage_dir = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, self.calc_id)
        self.loaded_layers = {}  # layer_name -> list of graphics items
        self._setup_ui()
        self._load_content()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)

        # Barra Superior
        top_bar = QHBoxLayout()
        self.btn_back = QPushButton(" Volver")
        self.btn_back.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #A0A0A0; color: #111; } QPushButton:hover { background-color: #888; }")
        self.btn_back.clicked.connect(self.close_requested.emit)
        top_bar.addWidget(self.btn_back)

        title_lbl = QLabel(f"Visor KiCad / Gerber: <b>{self.item_calc.get('name', 'Sin nombre')}</b>")
        title_lbl.setStyleSheet("font-size: 15px; color: #333;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar.addWidget(title_lbl, 1)

        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setStyleSheet("QPushButton { font-weight: bold; padding: 6px 12px; border-radius: 4px; background-color: #2e7d32; color: #fff; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self._save_content)
        top_bar.addWidget(self.btn_save)

        layout.addLayout(top_bar)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        btn_style = "QPushButton { padding: 4px 8px; border-radius: 4px; background: #E0E0E0; color: #111; border: 1px solid #AAA; font-weight: bold; font-size: 11px; } QPushButton:hover { background: #CCC; }"

        btn_load = QPushButton("📂 Cargar Gerber / KiCad / ZIP")
        btn_load.setStyleSheet("QPushButton { padding: 4px 10px; border-radius: 4px; background: #a6e3a1; color: #111; border: 1px solid #94e2d5; font-weight: bold; }")
        btn_load.clicked.connect(self._open_file_dialog)
        toolbar.addWidget(btn_load)

        toolbar.addWidget(QLabel("Tema PCB:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Verde Clásico (FR4)", "Azul Elegante", "Negro Mate Pro", "Rojo PCB"])
        self.theme_combo.setStyleSheet("QComboBox { padding: 4px 8px; border-radius: 4px; border: 1px solid #CCC; background: #FFF; color: #111; font-weight: bold; }")
        self.theme_combo.currentTextChanged.connect(self._on_theme_changed)
        toolbar.addWidget(self.theme_combo)

        self.btn_measure = QPushButton("📏 Medir Distancia")
        self.btn_measure.setCheckable(True)
        self.btn_measure.setStyleSheet(btn_style)
        self.btn_measure.toggled.connect(self._toggle_measurement)
        toolbar.addWidget(self.btn_measure)

        btn_zoom_in = QPushButton("🔍 Zoom +")
        btn_zoom_in.setStyleSheet(btn_style)
        btn_zoom_in.clicked.connect(lambda: self.canvas.scale(1.25, 1.25))
        toolbar.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("🔍 Zoom -")
        btn_zoom_out.setStyleSheet(btn_style)
        btn_zoom_out.clicked.connect(lambda: self.canvas.scale(0.8, 0.8))
        toolbar.addWidget(btn_zoom_out)

        btn_center = QPushButton("🎯 Centrar PCB")
        btn_center.setStyleSheet(btn_style)
        btn_center.clicked.connect(self._fit_pcb_in_view)
        toolbar.addWidget(btn_center)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Main Splitter: Left Layer Manager, Center Canvas, Right Stats
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Gestor de Capas
        layer_panel = QFrame()
        layer_panel.setMaximumWidth(240)
        layer_panel.setStyleSheet("""
            QFrame { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px; }
            QLabel { color: #cdd6f4; font-weight: bold; font-size: 12px; }
            QCheckBox { color: #cdd6f4; font-size: 11px; padding: 3px; }
        """)
        lp_layout = QVBoxLayout(layer_panel)
        lp_layout.setContentsMargins(10, 10, 10, 10)
        lp_layout.setSpacing(6)

        lp_layout.addWidget(QLabel("<b>Capas del PCB:</b>"))
        self.layer_checks_container = QWidget()
        self.layer_checks_layout = QVBoxLayout(self.layer_checks_container)
        self.layer_checks_layout.setContentsMargins(0, 0, 0, 0)
        self.layer_checks_layout.setSpacing(4)
        lp_layout.addWidget(self.layer_checks_container, 1)

        splitter.addWidget(layer_panel)

        # Canvas
        self.canvas = GerberCanvas(self)
        splitter.addWidget(self.canvas)

        # Stats Panel
        stats_panel = QFrame()
        stats_panel.setMaximumWidth(260)
        stats_panel.setStyleSheet("""
            QFrame { background-color: #1e1e2e; border: 1px solid #313244; border-radius: 6px; }
            QLabel { color: #cdd6f4; font-size: 12px; }
        """)
        st_layout = QVBoxLayout(stats_panel)
        st_layout.setContentsMargins(10, 10, 10, 10)
        st_layout.setSpacing(8)

        st_layout.addWidget(QLabel("<b>Métricas del PCB:</b>"))
        self.pcb_info_lbl = QLabel("Dimensiones: —\nCapas Cargadas: 0\nPerforaciones (Drills): 0\nConexiones: —")
        self.pcb_info_lbl.setWordWrap(True)
        st_layout.addWidget(self.pcb_info_lbl, 1)

        splitter.addWidget(stats_panel)
        splitter.setSizes([200, 600, 200])
        layout.addWidget(splitter, 1)

    def _on_theme_changed(self, theme_name: str):
        bg_colors = {
            "Verde Clásico (FR4)": "#0f3b23",
            "Azul Elegante": "#1b2d42",
            "Negro Mate Pro": "#181825",
            "Rojo PCB": "#4a1c1c"
        }
        bg = bg_colors.get(theme_name, "#181825")
        self.canvas.setStyleSheet(f"QGraphicsView {{ background-color: {bg}; border: 1px solid #313244; border-radius: 8px; }}")

    def _toggle_measurement(self, checked: bool):
        self.canvas.enable_measurement(checked)

    def _fit_pcb_in_view(self):
        r = self.canvas.scene.itemsBoundingRect()
        if not r.isEmpty():
            self.canvas.fitInView(r.adjusted(-10, -10, 10, 10), Qt.AspectRatioMode.KeepAspectRatio)

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Proyecto Gerber / KiCad", "", "Archivos PCB (*.gbr *.kicad_pcb *.kicad_sch *.drl *.zip)")
        if path:
            self._process_file(path)

    def _process_file(self, file_path: str):
        ext = os.path.splitext(file_path)[1].lower()
        self.canvas.scene.clear()
        self.loaded_layers.clear()
        self._clear_layer_checkboxes()

        if ext == '.zip':
            self._parse_gerber_zip(file_path)
        elif ext == '.kicad_pcb':
            self._parse_kicad_pcb(file_path)
        elif ext in ('.gbr', '.drl', '.txt', '.pho'):
            self._parse_single_gerber(file_path)

        self._fit_pcb_in_view()
        self._save_imported_file(file_path)

    def _clear_layer_checkboxes(self):
        while self.layer_checks_layout.count():
            child = self.layer_checks_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def _add_layer_checkbox(self, layer_name: str, color_hex: str):
        chk = QCheckBox(layer_name)
        chk.setChecked(True)
        chk.setStyleSheet(f"QCheckBox {{ color: {color_hex}; font-weight: bold; }}")
        chk.toggled.connect(lambda visible, lname=layer_name: self._toggle_layer_visibility(lname, visible))
        self.layer_checks_layout.addWidget(chk)

    def _toggle_layer_visibility(self, layer_name: str, visible: bool):
        for item in self.loaded_layers.get(layer_name, []):
            item.setVisible(visible)

    def _parse_kicad_pcb(self, file_path: str):
        """Parsea archivos KiCad PCB (.kicad_pcb) y renderiza pistas, vias y contorno."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            items_top = []
            items_bot = []
            items_edge = []

            pen_copper_top = QPen(QColor("#d4af37"), 0.5)
            pen_copper_bot = QPen(QColor("#b85434"), 0.5)
            pen_edge = QPen(QColor("#f9e2af"), 1.5)

            # Match segments
            for m in re.finditer(r'\(segment\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\)\s+\(width\s+([\d.-]+)\)\s+\(layer\s+"?([^"\s\)]+)"?\)', content):
                x1, y1, x2, y2, w, layer = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)), float(m.group(5)), m.group(6)
                line = self.canvas.scene.addLine(x1, y1, x2, y2, pen_copper_top if 'F.Cu' in layer else pen_copper_bot)
                if 'F.Cu' in layer: items_top.append(line)
                else: items_bot.append(line)

            # Match edge cuts
            for m in re.finditer(r'\(gr_line\s+\(start\s+([\d.-]+)\s+([\d.-]+)\)\s+\(end\s+([\d.-]+)\s+([\d.-]+)\).*?\(layer\s+"?Edge\.Cuts"?\)', content):
                x1, y1, x2, y2 = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
                line = self.canvas.scene.addLine(x1, y1, x2, y2, pen_edge)
                items_edge.append(line)

            self.loaded_layers['Top Copper (F.Cu)'] = items_top
            self.loaded_layers['Bottom Copper (B.Cu)'] = items_bot
            self.loaded_layers['Edge Cuts (Borde)'] = items_edge

            self._add_layer_checkbox('Top Copper (F.Cu)', '#d4af37')
            self._add_layer_checkbox('Bottom Copper (B.Cu)', '#b85434')
            self._add_layer_checkbox('Edge Cuts (Borde)', '#f9e2af')

            rect = self.canvas.scene.itemsBoundingRect()
            self.pcb_info_lbl.setText(
                f"Proyecto KiCad: {os.path.basename(file_path)}\n"
                f"Dimensiones: {rect.width():.1f} x {rect.height():.1f} mm\n"
                f"Pistas Renderizadas: {len(items_top) + len(items_bot):,}\n"
                f"Contorno PCB: {len(items_edge)} segmentos"
            )

        except Exception as e:
            print(f"Error parsing KiCad PCB: {e}")

    def _parse_single_gerber(self, file_path: str):
        """Parsea un archivo Gerber unitario (.gbr / .drl)."""
        layer_name = os.path.basename(file_path)
        color = self.LAYER_COLORS.get(layer_name, '#a6e3a1')
        items = self._parse_gerber_content(file_path, color)
        self.loaded_layers[layer_name] = items
        self._add_layer_checkbox(layer_name, color)

    def _parse_gerber_zip(self, zip_path: str):
        """Parsea un paquete ZIP de archivos Gerber."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                for fname in z.namelist():
                    if fname.endswith('/'): continue
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in ('.gbr', '.gtl', '.gbl', '.gts', '.gbs', '.gto', '.gbo', '.drl', '.txt'):
                        tmp_dest = os.path.join(self.storage_dir, os.path.basename(fname))
                        self._ensure_storage_dir()
                        with z.open(fname) as source, open(tmp_dest, 'wb') as target:
                            shutil.copyfileobj(source, target)
                        self._parse_single_gerber(tmp_dest)
        except Exception as e:
            print(f"Error parsing Gerber ZIP: {e}")

    def _parse_gerber_content(self, file_path: str, color_hex: str):
        items = []
        pen = QPen(QColor(color_hex), 0.3)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            cur_x = cur_y = 0.0
            for line in lines:
                line_s = line.strip()
                if line_s.startswith('X') or 'D01' in line_s or 'D02' in line_s:
                    m = re.search(r'X([\d.-]+)', line_s)
                    if m:
                        try: cur_x = float(m.group(1)) / 10000.0
                        except: pass
                    m2 = re.search(r'Y([\d.-]+)', line_s)
                    if m2:
                        try: cur_y = float(m2.group(1)) / 10000.0
                        except: pass

                    if 'D01' in line_s or line_s.endswith('D01*'):
                        rect_item = self.canvas.scene.addEllipse(cur_x - 0.2, cur_y - 0.2, 0.4, 0.4, pen, QBrush(QColor(color_hex)))
                        items.append(rect_item)
        except Exception as e:
            print(f"Error parsing gerber content: {e}")
        return items

    def _ensure_storage_dir(self):
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir, exist_ok=True)

    def _save_imported_file(self, source_path: str):
        self._ensure_storage_dir()
        try:
            dest = os.path.join(self.storage_dir, os.path.basename(source_path))
            if source_path != dest:
                shutil.copy2(source_path, dest)
        except Exception as e:
            print(f"Error saving PCB file: {e}")

    def _load_content(self):
        if not os.path.exists(self.storage_dir): return
        for fname in os.listdir(self.storage_dir):
            ext = os.path.splitext(fname)[1].lower()
            if ext in ('.kicad_pcb', '.gbr', '.drl', '.zip'):
                self._process_file(os.path.join(self.storage_dir, fname))
                break

    def _save_content(self):
        self._ensure_storage_dir()
        QMessageBox.information(self, "Éxito", "Proyecto KiCad / Gerber guardado correctamente.")
        self.saved.emit()


# =============================================================================
# 7. LibraryDocViewerWidget - Visor de Documentación desde la Biblioteca
# =============================================================================

class LibraryDocViewerWidget(QFrame):
    """Visor de documentos de la Biblioteca vinculados a un Proyecto o Análisis."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, calc_dict: dict, item_analysis: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.calc_dict = calc_dict
        self.item_analysis = item_analysis
        self.agenda_path = agenda_path
        
        self.setStyleSheet("""
            LibraryDocViewerWidget {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 8px;
            }
            QLabel { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
        """)
        self._setup_ui()
        self._load_documents()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)

        # Header bar
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        proj_name = self.item_analysis.get('name', 'Proyecto')
        lbl_title = QLabel(f"📚 <b>Documentación de Biblioteca: {proj_name}</b>")
        lbl_title.setStyleSheet("font-size: 15px; color: #a6e3a1;")
        hdr.addWidget(lbl_title, 1)

        btn_reload = QPushButton("🔄 Actualizar Listado")
        btn_reload.setStyleSheet("QPushButton { background: #89b4fa; color: #111; font-weight: bold; padding: 5px 12px; border-radius: 4px; }")
        btn_reload.clicked.connect(self._load_documents)
        hdr.addWidget(btn_reload)

        btn_close = QPushButton("⬅ Volver")
        btn_close.setStyleSheet("QPushButton { background: #45475a; color: #fff; font-weight: bold; padding: 5px 12px; border-radius: 4px; }")
        btn_close.clicked.connect(self.close_requested.emit)
        hdr.addWidget(btn_close)

        layout.addLayout(hdr)

        # Scroll Area for documents list
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #181825; border: 1px solid #313244; border-radius: 6px; }")

        self.scroll_container = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(12, 12, 12, 12)
        self.scroll_layout.setSpacing(10)

        self.scroll_area.setWidget(self.scroll_container)
        layout.addWidget(self.scroll_area, 1)

    def _load_documents(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        if not self.agenda_path:
            lbl = QLabel("Sin ruta de agenda válida.")
            lbl.setStyleSheet("color: #f38ba8; font-style: italic;")
            self.scroll_layout.addWidget(lbl)
            return

        from data.data_store import DataStore
        bib_path = DataStore.get_plugin_data_path(self.agenda_path, 'biblioteca')
        bib_data = DataStore.load(bib_path) or {}
        documents = bib_data.get('documents', [])

        target_id = self.item_analysis.get('id')
        target_name = self.item_analysis.get('name')

        matched_docs = []
        for doc in documents:
            assigned_ids = doc.get('assigned_element_ids', [])
            if target_id in assigned_ids or target_name in assigned_ids:
                matched_docs.append(doc)

        if not matched_docs:
            info_frame = QFrame()
            info_frame.setStyleSheet("QFrame { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; padding: 20px; }")
            info_layout = QVBoxLayout(info_frame)
            info_layout.setSpacing(8)

            lbl_empty = QLabel("<b>No hay documentos de la Biblioteca vinculados a este proyecto todavía.</b>")
            lbl_empty.setStyleSheet("color: #f9e2af; font-size: 14px;")
            info_layout.addWidget(lbl_empty)

            lbl_desc = QLabel(
                "Para vincular manuales, datasheets, planos o libros desde la Biblioteca:\n"
                "1. Ve a la sección <b>Biblioteca</b> en Vito Organizer.\n"
                "2. Edita un documento (o sube uno nuevo).\n"
                "3. En <b>Categoría Destino</b> selecciona: <b>'Desarrollo y Proyectos'</b>.\n"
                "4. Marca la casilla correspondiente a este proyecto (<b>" + str(target_name) + "</b>) y guarda."
            )
            lbl_desc.setStyleSheet("color: #cdd6f4; font-size: 12px; line-height: 1.4;")
            info_layout.addWidget(lbl_desc)

            self.scroll_layout.addWidget(info_frame)
        else:
            for doc in matched_docs:
                card = QFrame()
                card.setStyleSheet("QFrame { background-color: #313244; border: 1px solid #45475a; border-radius: 6px; } QFrame:hover { border-color: #89b4fa; }")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(12, 10, 12, 10)
                c_layout.setSpacing(12)

                lbl_icon = QLabel("📖")
                lbl_icon.setStyleSheet("font-size: 24px;")
                c_layout.addWidget(lbl_icon)

                fname = doc.get('filename', '')
                doc_type = doc.get('type', 'Documento')
                desc = doc.get('description', '')
                
                info_txt = f"<b>{doc.get('name')}</b> ({doc_type})<br>"
                info_txt += f"<span style='color: #a6adc8; font-size: 11px;'>Archivo: <b>{fname}</b></span>"
                if desc:
                    info_txt += f"<br><span style='color: #b4befe; font-size: 11px;'>{desc}</span>"

                lbl_info = QLabel(info_txt)
                lbl_info.setStyleSheet("border: none; background: transparent; color: #cdd6f4;")
                lbl_info.setWordWrap(True)
                c_layout.addWidget(lbl_info, 1)

                subfolder_map = {
                    "Manuales": "Manuales",
                    "Datasheets": "Datasheets",
                    "Libros": "Libros",
                    "Revistas": "Revistas",
                    "Información Técnica": "Informacion_Tecnica",
                    "Hojas de Seguridad": "Hojas_de_Seguridad",
                    "Imágenes": "Imagenes",
                    "Otros Documentos": "Otros_Documentos"
                }
                sf = doc.get('subfolder') or subfolder_map.get(doc_type, "Otros_Documentos")
                rel_p = doc.get('relative_path') or os.path.join('biblioteca', sf, fname)
                full_p = os.path.join(self.agenda_path, rel_p)

                btn_open = QPushButton("📂 Abrir Archivo Físico")
                btn_open.setStyleSheet("QPushButton { background: #a6e3a1; color: #111; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background: #94e2d5; }")
                btn_open.clicked.connect(lambda _, fp=full_p: open_local_file(fp))
                c_layout.addWidget(btn_open)

                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()


# =============================================================================
# 8. SchematicEditorWidget - Editor de Diagramas Esquemáticos Electrónicos
# =============================================================================

SCHEMATIC_SYMBOLS = {
    'Resistencia (R)': {'ref': 'R', 'val': '10k', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Condensador (C)': {'ref': 'C', 'val': '100nF', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Condensador Pol (C_POL)': {'ref': 'C', 'val': '10uF', 'pins': [(-30, 0, '+'), (30, 0, '-')]},
    'Inductancia (L)': {'ref': 'L', 'val': '10uH', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Potenciómetro (RV)': {'ref': 'RV', 'val': '10k', 'pins': [(-30, 0, '1'), (30, 0, '3'), (0, -25, '2')]},
    'Cristal Oscilador 2P (Y)': {'ref': 'Y', 'val': '16MHz', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Cristal Oscilador 3P (Y_3P)': {'ref': 'Y', 'val': '16MHz', 'pins': [(-30, 0, '1'), (30, 0, '2'), (0, 25, 'GND')]},
    'Oscilador Módulo 4P (XO)': {'ref': 'Y', 'val': '24MHz', 'pins': [(-35, -15, 'NC/EN'), (-35, 15, 'GND'), (35, 15, 'OUT'), (35, -15, 'VCC')]},
    'Varistor (MOV)': {'ref': 'RV', 'val': 'S10K275', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Descargador de Gas (GDT)': {'ref': 'GDT', 'val': '90V', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Fusible Rearmable (PPTC)': {'ref': 'F', 'val': '500mA', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Diodo (D)': {'ref': 'D', 'val': '1N4148', 'pins': [(-30, 0, 'A'), (30, 0, 'K')]},
    'Diodo Zener (DZ)': {'ref': 'D', 'val': 'BZX55', 'pins': [(-30, 0, 'A'), (30, 0, 'K')]},
    'Diodo TVS Unidireccional': {'ref': 'D', 'val': 'SMBJ5.0A', 'pins': [(-30, 0, 'A'), (30, 0, 'K')]},
    'Diodo TVS Bidireccional': {'ref': 'D', 'val': 'SMBJ5.0CA', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'LED': {'ref': 'D', 'val': 'Verde', 'pins': [(-30, 0, 'A'), (30, 0, 'K')]},
    'Transistor NPN (Q)': {'ref': 'Q', 'val': '2N2222', 'pins': [(-30, 0, 'B'), (20, -25, 'C'), (20, 25, 'E')]},
    'Transistor PNP (Q)': {'ref': 'Q', 'val': '2N3906', 'pins': [(-30, 0, 'B'), (20, -25, 'C'), (20, 25, 'E')]},
    'Amplificador Op (OpAmp)': {'ref': 'U', 'val': 'LM358', 'pins': [(-30, -10, '-'), (-30, 10, '+'), (30, 0, 'OUT')]},
    'Timer NE555': {'ref': 'U', 'val': 'NE555', 'pins': [(-40, -30, 'GND'), (-40, -10, 'TRIG'), (-40, 10, 'OUT'), (-40, 30, 'RST'), (40, -30, 'VCC'), (40, -10, 'DIS'), (40, 10, 'THR'), (40, 30, 'CV')]},
    'Regulador LM7805': {'ref': 'U', 'val': '7805', 'pins': [(-30, 0, 'VI'), (0, 25, 'GND'), (30, 0, 'VO')]},
    'Regulador LM317': {'ref': 'U', 'val': 'LM317', 'pins': [(-30, 0, 'VI'), (0, 25, 'ADJ'), (30, 0, 'VO')]},
    'Regulador LM338K': {'ref': 'U', 'val': 'LM338K', 'pins': [(-30, 0, 'VI'), (0, 25, 'ADJ'), (30, 0, 'VO')]},
    'IC ADC ICL7106': {'ref': 'U', 'val': 'ICL7106', 'pins': [(-45, -30, 'V+'), (-45, -15, 'IN+'), (-45, 0, 'IN-'), (-45, 15, 'REF+'), (-45, 30, 'REF-'), (45, -30, 'V-'), (45, -15, 'OSC1'), (45, 0, 'OSC2'), (45, 15, 'OSC3'), (45, 30, 'TEST')]},
    'IC ADC ICL7107': {'ref': 'U', 'val': 'ICL7107', 'pins': [(-45, -30, 'V+'), (-45, -15, 'IN+'), (-45, 0, 'IN-'), (-45, 15, 'REF+'), (-45, 30, 'REF-'), (45, -30, 'V-'), (45, -15, 'GND'), (45, 0, 'OSC1'), (45, 15, 'OSC2'), (45, 30, 'TEST')]},
    'IC ADC ICL7135': {'ref': 'U', 'val': 'ICL7135', 'pins': [(-45, -25, 'V+'), (-45, -10, 'IN+'), (-45, 5, 'IN-'), (-45, 20, 'REF'), (45, -25, 'V-'), (45, -10, 'CLK'), (45, 5, 'BUSY'), (45, 20, 'D1-D4')]},
    'IC OpAmp/Comp LM736': {'ref': 'U', 'val': 'LM736', 'pins': [(-30, -10, '-'), (-30, 10, '+'), (30, 0, 'OUT')]},
    'IC Inversor ICL7660': {'ref': 'U', 'val': 'ICL7660', 'pins': [(-35, -20, 'NC'), (-35, -5, 'CAP+'), (-35, 10, 'GND'), (-35, 25, 'CAP-'), (35, -20, 'VOUT'), (35, -5, 'LV'), (35, 10, 'OSC'), (35, 25, 'V+')]},
    'Tierra (GND)': {'ref': '#GND', 'val': 'GND', 'pins': [(0, -15, '1')]},
    'Alimentación VCC': {'ref': '#VCC', 'val': '+5V', 'pins': [(0, 15, '1')]},
    'Interruptor (SW)': {'ref': 'SW', 'val': 'SPST', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Pulsador (SW_PUSH)': {'ref': 'SW', 'val': 'NO', 'pins': [(-30, 0, '1'), (30, 0, '2')]},
    'Batería (BAT)': {'ref': 'BAT', 'val': '9V', 'pins': [(-30, 0, '+'), (30, 0, '-')]},
    'Terminal Block 2P': {'ref': 'J', 'val': 'CONN_2', 'pins': [(-20, -10, '1'), (-20, 10, '2')]},
    'Válvula Triodo (V)': {'ref': 'V', 'val': '12AX7', 'pins': [(-30, 0, 'G'), (0, -30, 'P'), (0, 30, 'K')]}
}


class SchematicComponentItem(QGraphicsItem):
    """Elemento componente gráfico para diagramas esquemáticos."""
    def __init__(self, sym_name: str, ref: str, val: str, pos_x=0, pos_y=0, rotation=0):
        super().__init__()
        self.sym_name = sym_name
        self.ref = ref
        self.val = val
        self.angle = rotation
        self.setPos(pos_x, pos_y)
        self.setRotation(self.angle)

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        
        self.pins_def = SCHEMATIC_SYMBOLS.get(sym_name, {}).get('pins', [(-20, 0, '1'), (20, 0, '2')])
        self._recalc_rect()

    def _recalc_rect(self):
        min_x, max_x = -45, 45
        min_y, max_y = -35, 35
        for px, py, pname in self.pins_def:
            min_x = min(min_x, px - 15)
            max_x = max(max_x, px + 15)
            min_y = min(min_y, py - 15)
            max_y = max(max_y, py + 15)
        self._rect = QRectF(min_x, min_y - 12, (max_x - min_x), (max_y - min_y) + 24)

    def boundingRect(self):
        return self._rect

    def get_pin_scene_pos(self, pin_name_or_idx):
        if isinstance(pin_name_or_idx, int) and 0 <= pin_name_or_idx < len(self.pins_def):
            px, py = self.pins_def[pin_name_or_idx][0], self.pins_def[pin_name_or_idx][1]
            return self.mapToScene(QPointF(px, py))
        try:
            idx = int(pin_name_or_idx)
            if 0 <= idx < len(self.pins_def):
                px, py = self.pins_def[idx][0], self.pins_def[idx][1]
                return self.mapToScene(QPointF(px, py))
        except (ValueError, TypeError):
            pass
        key_str = str(pin_name_or_idx)
        for idx, (px, py, pname) in enumerate(self.pins_def):
            if str(pname) == key_str:
                return self.mapToScene(QPointF(px, py))
        return self.scenePos()

    def rotate_90(self):
        self.angle = (self.angle + 90) % 360
        self.setRotation(self.angle)
        self.notify_connected_wires()

    def itemChange(self, change, value):
        if change in (QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged,
                      QGraphicsItem.GraphicsItemChange.ItemRotationHasChanged,
                      QGraphicsItem.GraphicsItemChange.ItemTransformHasChanged):
            self.notify_connected_wires()
        return super().itemChange(change, value)

    def notify_connected_wires(self):
        scene = self.scene()
        if not scene: return
        for item in scene.items():
            if isinstance(item, SchematicWireItem):
                item.update_from_component_move(self)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Pen selection highlight
        if self.isSelected():
            pen_sel = QPen(QColor("#89b4fa"), 2, Qt.PenStyle.DashLine)
            painter.setPen(pen_sel)
            painter.setBrush(QBrush(QColor(137, 180, 250, 30)))
            painter.drawRoundedRect(self._rect, 6, 6)

        pen_line = QPen(QColor("#89dceb"), 2)
        painter.setPen(pen_line)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        s = self.sym_name

        # DIBUJO SIMBÓLICO SEGÚN TIPO
        if 'Resistencia (R)' in s:
            painter.drawLine(-30, 0, -15, 0)
            painter.drawLine(15, 0, 30, 0)
            path = QPainterPath()
            path.moveTo(-15, 0)
            pts = [(-10, -8), (-5, 8), (0, -8), (5, 8), (10, -8), (15, 0)]
            for px, py in pts: path.lineTo(px, py)
            painter.drawPath(path)
        elif 'Cristal' in s or 'Oscilador' in s:
            if '4P' in s or 'Módulo' in s:
                w, h = 64, 40
                painter.drawRect(-w//2, -h//2, w, h)
                for px, py, pname in self.pins_def:
                    if px < 0: painter.drawLine(px, py, -w//2, py)
                    elif px > 0: painter.drawLine(px, py, w//2, py)
                painter.drawRect(-6, -10, 12, 20)
                painter.drawLine(-9, -8, -9, 8)
                painter.drawLine(9, -8, 9, 8)
            else:
                painter.drawLine(-30, 0, -10, 0)
                painter.drawLine(10, 0, 30, 0)
                painter.drawLine(-10, -14, -10, 14)
                painter.drawLine(10, -14, 10, 14)
                painter.drawRect(-6, -16, 12, 32)
                if '3P' in s:
                    painter.drawLine(0, 16, 0, 25)
        elif 'Varistor' in s or 'MOV' in s:
            painter.drawLine(-30, 0, -15, 0)
            painter.drawLine(15, 0, 30, 0)
            painter.drawRect(-15, -7, 30, 14)
            path = QPainterPath()
            path.moveTo(-12, 12)
            path.lineTo(12, -12)
            path.lineTo(18, -12)
            painter.drawPath(path)
        elif 'Descargador' in s or 'GDT' in s:
            painter.drawEllipse(-16, -16, 32, 32)
            painter.drawLine(-30, 0, -10, 0)
            painter.drawLine(10, 0, 30, 0)
            painter.drawLine(-10, -6, -10, 6)
            painter.drawLine(10, -6, 10, 6)
            painter.drawPoint(-3, 0)
            painter.drawPoint(3, 0)
        elif 'PPTC' in s or 'Rearmable' in s:
            painter.drawLine(-30, 0, -15, 0)
            painter.drawLine(15, 0, 30, 0)
            painter.drawRect(-15, -7, 30, 14)
            path = QPainterPath()
            path.moveTo(-10, 10)
            path.lineTo(-10, -10)
            path.lineTo(10, 10)
            painter.drawPath(path)
        elif 'Condensador' in s:
            painter.drawLine(-30, 0, -6, 0)
            painter.drawLine(6, 0, 30, 0)
            painter.drawLine(-6, -15, -6, 15)
            if 'Pol' in s:
                painter.drawArc(-6, -15, 12, 30, -90*16, 180*16)
                painter.drawText(-22, -8, "+")
            else:
                painter.drawLine(6, -15, 6, 15)
        elif 'Inductancia' in s:
            painter.drawLine(-30, 0, -20, 0)
            painter.drawLine(20, 0, 30, 0)
            path = QPainterPath()
            path.moveTo(-20, 0)
            for i in range(4):
                path.arcTo(-20 + i*10, -8, 10, 16, 180, -180)
            painter.drawPath(path)
        elif 'Potenciómetro' in s:
            painter.drawLine(-30, 0, -15, 0)
            painter.drawLine(15, 0, 30, 0)
            painter.drawRect(-15, -7, 30, 14)
            painter.drawLine(0, -25, 0, -7)
            painter.drawLine(0, -7, -4, -12)
            painter.drawLine(0, -7, 4, -12)
        elif 'TVS' in s:
            if 'Bidireccional' in s or 'Bi' in s:
                painter.drawLine(-30, 0, -12, 0)
                painter.drawLine(12, 0, 30, 0)
                p1 = QPainterPath()
                p1.moveTo(-12, -10)
                p1.lineTo(0, 0)
                p1.lineTo(-12, 10)
                p1.closeSubpath()
                painter.drawPath(p1)
                p2 = QPainterPath()
                p2.moveTo(12, -10)
                p2.lineTo(0, 0)
                p2.lineTo(12, 10)
                p2.closeSubpath()
                painter.drawPath(p2)
                painter.drawLine(0, -12, 0, 12)
                painter.drawLine(0, -12, -4, -15)
                painter.drawLine(0, 12, 4, 15)
            else:
                painter.drawLine(-30, 0, -10, 0)
                painter.drawLine(10, 0, 30, 0)
                path = QPainterPath()
                path.moveTo(-10, -12)
                path.lineTo(10, 0)
                path.lineTo(-10, 12)
                path.closeSubpath()
                painter.drawPath(path)
                painter.drawLine(10, -12, 10, 12)
                painter.drawLine(10, -12, 6, -15)
                painter.drawLine(10, 12, 14, 15)
        elif 'Diodo' in s or 'LED' in s:
            painter.drawLine(-30, 0, -10, 0)
            painter.drawLine(10, 0, 30, 0)
            path = QPainterPath()
            path.moveTo(-10, -12)
            path.lineTo(10, 0)
            path.lineTo(-10, 12)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(10, -12, 10, 12)
            if 'Zener' in s:
                painter.drawLine(10, -12, 6, -15)
                painter.drawLine(10, 12, 14, 15)
            elif 'LED' in s:
                painter.drawLine(0, -12, 6, -20)
                painter.drawLine(6, -12, 12, -20)
        elif 'Transistor' in s:
            painter.drawLine(-30, 0, -10, 0)
            painter.drawLine(-10, -18, -10, 18)
            painter.drawLine(-10, -8, 20, -25)
            painter.drawLine(-10, 8, 20, 25)
            # Arrow
            if 'NPN' in s:
                painter.drawLine(20, 25, 10, 20)
                painter.drawLine(20, 25, 14, 14)
            else:
                painter.drawLine(-10, 8, -2, 16)
                painter.drawLine(-10, 8, -2, 6)
        elif 'Amplificador Op' in s:
            path = QPainterPath()
            path.moveTo(-20, -22)
            path.lineTo(20, 0)
            path.lineTo(-20, 22)
            path.closeSubpath()
            painter.drawPath(path)
            painter.drawLine(-30, -10, -20, -10)
            painter.drawLine(-30, 10, -20, 10)
            painter.drawLine(20, 0, 30, 0)
            painter.drawText(-18, -6, "-")
            painter.drawText(-18, 14, "+")
        elif 'Tierra' in s:
            painter.drawLine(0, -15, 0, 0)
            painter.drawLine(-15, 0, 15, 0)
            painter.drawLine(-10, 5, 10, 5)
            painter.drawLine(-5, 10, 5, 10)
        elif 'Alimentación' in s:
            painter.drawLine(0, 15, 0, 0)
            path = QPainterPath()
            path.moveTo(0, 0)
            path.lineTo(-6, 8)
            path.lineTo(6, 8)
            path.closeSubpath()
            painter.drawPath(path)
        elif 'Válvula' in s or 'Tubo' in s:
            painter.drawEllipse(-20, -25, 40, 50)
            painter.drawLine(-12, -12, 12, -12)  # Plate (P)
            painter.drawLine(0, -30, 0, -12)
            painter.drawLine(-12, 0, -6, 0)      # Grid (G)
            painter.drawLine(-2, 0, 2, 0)
            painter.drawLine(6, 0, 12, 0)
            painter.drawLine(-30, 0, -12, 0)
            path = QPainterPath()                # Cathode (K)
            path.moveTo(-10, 12)
            path.lineTo(0, 12)
            path.lineTo(0, 30)
            painter.drawPath(path)
        else: # Generico / IC / Regulators / Logic
            min_px = min([px for px, py, pname in self.pins_def] + [-20])
            max_px = max([px for px, py, pname in self.pins_def] + [20])
            min_py = min([py for px, py, pname in self.pins_def] + [-20])
            max_py = max([py for px, py, pname in self.pins_def] + [20])

            box_w = max(60, max_px - min_px - 20)
            box_h = max(50, max_py - min_py + 20)

            box_rect = QRectF(-box_w/2, -box_h/2, box_w, box_h)
            painter.drawRect(box_rect)

            for px, py, pname in self.pins_def:
                if px < 0:
                    painter.drawLine(px, py, int(-box_w/2), py)
                elif px > 0:
                    painter.drawLine(px, py, int(box_w/2), py)
                elif py < 0:
                    painter.drawLine(px, py, px, int(-box_h/2))
                else:
                    painter.drawLine(px, py, px, int(box_h/2))

        # Dibujar pines (puntos rojos) y sus etiquetas/números
        font_pin = QFont("Segoe UI", 7, QFont.Weight.Bold)
        painter.setFont(font_pin)
        for px, py, pname in self.pins_def:
            painter.setPen(QPen(QColor("#f38ba8"), 4))
            if pname:
                painter.setPen(QPen(QColor("#cdd6f4")))
                if px < 0:
                    painter.drawText(QRectF(px + 4, py - 8, 30, 16), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(pname))
                elif px > 0:
                    painter.drawText(QRectF(px - 34, py - 8, 30, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(pname))
                elif py < 0:
                    painter.drawText(QRectF(px - 15, py + 2, 30, 16), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, str(pname))
                else:
                    painter.drawText(QRectF(px - 15, py - 18, 30, 16), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, str(pname))

        # Dibujar Texto Referencia (U1, R1) y Valor (NE555, 10k)
        font_txt = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font_txt)

        is_ic_type = 'IC' in s or 'NE555' in s or 'Timer' in s or 'Regulad' in s or 'Inversor' in s or ('Diodo' not in s and 'Resist' not in s and 'Conden' not in s and 'Induc' not in s and 'Trans' not in s and 'Tierra' not in s and 'Alimen' not in s and 'Cristal' not in s and 'Varis' not in s and 'Desc' not in s and 'PPTC' not in s and 'Válvula' not in s)

        if is_ic_type:
            min_py = min([py for px, py, pname in self.pins_def] + [-20])
            max_py = max([py for px, py, pname in self.pins_def] + [20])
            box_h = max(50, max_py - min_py + 20)

            # Ref sits centered ABOVE the box
            painter.setPen(QPen(QColor("#f9e2af")))
            painter.drawText(QRectF(-45, -box_h/2 - 16, 90, 14), Qt.AlignmentFlag.AlignCenter, f"{self.ref}")

            # Val sits centered INSIDE the box
            painter.setPen(QPen(QColor("#a6e3a1")))
            painter.drawText(QRectF(-40, -box_h/2 + 4, 80, box_h - 8), Qt.AlignmentFlag.AlignCenter, f"{self.val}")
        else:
            painter.setPen(QPen(QColor("#f9e2af")))
            painter.drawText(QRectF(-45, -30, 90, 14), Qt.AlignmentFlag.AlignCenter, f"{self.ref}")
            painter.setPen(QPen(QColor("#a6e3a1")))
            painter.drawText(QRectF(-45, 18, 90, 14), Qt.AlignmentFlag.AlignCenter, f"{self.val}")


class WireHandleItem(QGraphicsItem):
    """Handle interactivo para editar el trazado de un cable (Wire)."""
    def __init__(self, wire_item, pt_index: int):
        super().__init__()
        self.wire_item = wire_item
        self.pt_index = pt_index
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(20)
        self._rect = QRectF(-5, -5, 10, 10)
        self._updating = False

    def boundingRect(self):
        return self._rect

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor("#11111b"), 1))
        if self.pt_index == 0 or self.pt_index == len(self.wire_item.pts) - 1:
            painter.setBrush(QBrush(QColor("#f9e2af"))) # Endpoints gold
        else:
            painter.setBrush(QBrush(QColor("#89b4fa"))) # Corner handles blue
        painter.drawRect(self._rect)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and not self._updating:
            new_pos = value
            scene = self.scene()
            if scene and hasattr(scene, 'find_snap_point'):
                if self.pt_index == 0 or self.pt_index == len(self.wire_item.pts) - 1:
                    snap_pos, comp, pin_idx = scene.find_snap_point(new_pos, snap_distance=15)
                    new_pos = snap_pos
                    if self.pt_index == 0:
                        self.wire_item.start_comp = comp
                        self.wire_item.start_pin_idx = pin_idx
                    else:
                        self.wire_item.end_comp = comp
                        self.wire_item.end_pin_idx = pin_idx
                else:
                    new_pos = scene.snap(new_pos)

            self.wire_item.update_pt_from_handle(self.pt_index, new_pos)
            return new_pos
        return super().itemChange(change, value)


class SchematicWireItem(QGraphicsPathItem):
    """Conexión ortogonal de cable entre pines o puntos esquemáticos."""
    def __init__(self, pts: list = None, net_name="", start_comp=None, start_pin_idx=None, end_comp=None, end_pin_idx=None):
        super().__init__()
        self.net_name = net_name
        self.pts = pts or [] # Lista de QPointF
        self.start_comp = start_comp
        self.start_pin_idx = start_pin_idx
        self.end_comp = end_comp
        self.end_pin_idx = end_pin_idx
        self.handles = []

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setZValue(5)
        self.update_path()

    def update_path(self):
        path = QPainterPath()
        if len(self.pts) >= 2:
            path.moveTo(self.pts[0])
            for pt in self.pts[1:]:
                path.lineTo(pt)
        self.setPath(path)

    def update_from_component_move(self, comp):
        """Actualiza los puntos extremos cuando un componente conectado se desplaza."""
        if comp is None:
            return
        changed = False
        if self.start_comp == comp and self.start_pin_idx is not None:
            new_p = comp.get_pin_scene_pos(self.start_pin_idx)
            if self.pts and self.pts[0] != new_p:
                self.pts[0] = new_p
                changed = True
        elif not self.start_comp and self.pts:
            for idx, (px, py, pname) in enumerate(comp.pins_def):
                pin_pos = comp.mapToScene(QPointF(px, py))
                if QLineF(self.pts[0], pin_pos).length() < 10:
                    self.start_comp = comp
                    self.start_pin_idx = idx
                    self.pts[0] = pin_pos
                    changed = True
                    break

        if self.end_comp == comp and self.end_pin_idx is not None:
            new_p = comp.get_pin_scene_pos(self.end_pin_idx)
            if self.pts and self.pts[-1] != new_p:
                self.pts[-1] = new_p
                changed = True
        elif not self.end_comp and self.pts:
            for idx, (px, py, pname) in enumerate(comp.pins_def):
                pin_pos = comp.mapToScene(QPointF(px, py))
                if QLineF(self.pts[-1], pin_pos).length() < 10:
                    self.end_comp = comp
                    self.end_pin_idx = idx
                    self.pts[-1] = pin_pos
                    changed = True
                    break

        if changed:
            if len(self.pts) == 3:
                self.pts[1] = QPointF(self.pts[2].x(), self.pts[0].y())
            elif len(self.pts) == 2:
                p0, p1 = self.pts[0], self.pts[1]
                if abs(p0.x() - p1.x()) > 2 and abs(p0.y() - p1.y()) > 2:
                    self.pts = [p0, QPointF(p1.x(), p0.y()), p1]
            self.update_path()
            self.update_handles_pos()

    def update_pt_from_handle(self, idx: int, pos: QPointF):
        if 0 <= idx < len(self.pts):
            self.pts[idx] = pos
            self.update_path()

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
            if value:
                self.show_handles()
            else:
                self.hide_handles()
        return super().itemChange(change, value)

    def show_handles(self):
        self.hide_handles()
        scene = self.scene()
        if not scene: return
        for i, pt in enumerate(self.pts):
            h = WireHandleItem(self, i)
            h.setPos(pt)
            scene.addItem(h)
            self.handles.append(h)

    def hide_handles(self):
        for h in self.handles:
            if h.scene():
                h.scene().removeItem(h)
        self.handles.clear()

    def update_handles_pos(self):
        for i, h in enumerate(self.handles):
            if i < len(self.pts):
                h._updating = True
                h.setPos(self.pts[i])
                h._updating = False

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.isSelected():
            pen = QPen(QColor("#f9e2af"), 3, Qt.PenStyle.SolidLine)
        else:
            pen = QPen(QColor("#a6e3a1"), 2, Qt.PenStyle.SolidLine)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.drawPath(self.path())


class SchematicNetLabelItem(QGraphicsItem):
    """Etiqueta de red (Net Label) para conexiones lógicas (ej: VCC, GND, VIN)."""
    def __init__(self, net_name="NET_1", pos_x=0, pos_y=0):
        super().__init__()
        self.net_name = net_name
        self.setPos(pos_x, pos_y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
        )

    def boundingRect(self):
        return QRectF(-10, -12, 60, 24)

    def paint(self, painter: QPainter, option, widget=None):
        if self.isSelected():
            painter.setPen(QPen(QColor("#89b4fa"), 1, Qt.PenStyle.DashLine))
            painter.setBrush(QBrush(QColor(137, 180, 250, 40)))
            painter.drawRect(self.boundingRect())

        painter.setPen(QPen(QColor("#cba6f7"), 2))
        painter.setBrush(QBrush(QColor("#313244")))
        painter.drawRoundedRect(0, -10, 50, 20, 4, 4)
        
        # Pin indicator dot
        painter.setPen(QPen(QColor("#f38ba8"), 4))
        painter.drawPoint(0, 0)

        painter.setPen(QPen(QColor("#cdd6f4")))
        font = QFont("Segoe UI", 8, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(6, 4, self.net_name[:6])


class BOMDialog(QDialog):
    """Diálogo emergente de Lista de Materiales (BOM)."""
    def __init__(self, components: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Lista de Materiales (BOM) - Esquemático")
        self.setMinimumSize(520, 360)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("<b>Resumen de Componentes del Circuito (BOM):</b>")
        lbl.setStyleSheet("color: #a6e3a1; font-size: 13px;")
        layout.addWidget(lbl)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Símbolo", "Referencia", "Valor", "Cantidad"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet("QTableWidget { background-color: #1e1e2e; color: #cdd6f4; gridline-color: #45475a; }")

        # Agrupar por tipo y valor
        grouped = {}
        for c in components:
            key = (c.sym_name, c.val)
            if key not in grouped: grouped[key] = []
            grouped[key].append(c.ref)

        self.table.setRowCount(len(grouped))
        for row, ((sym, val), refs) in enumerate(grouped.items()):
            self.table.setItem(row, 0, QTableWidgetItem(sym))
            self.table.setItem(row, 1, QTableWidgetItem(", ".join(refs)))
            self.table.setItem(row, 2, QTableWidgetItem(val))
            self.table.setItem(row, 3, QTableWidgetItem(str(len(refs))))

        layout.addWidget(self.table)

        btn_box = QHBoxLayout()
        btn_copy = QPushButton("📋 Copiar BOM")
        btn_copy.setStyleSheet("background: #89b4fa; color: #111; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_copy.clicked.connect(self._copy_bom)
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_copy)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)

    def _copy_bom(self):
        txt = "Símbolo\tReferencia\tValor\tCantidad\n"
        for r in range(self.table.rowCount()):
            row_txt = "\t".join(self.table.item(r, c).text() for c in range(4))
            txt += row_txt + "\n"
        QApplication.clipboard().setText(txt)
        QMessageBox.information(self, "BOM Copiado", "Lista de materiales copiada al portapapeles.")


class NetlistDialog(QDialog):
    """Diálogo emergente para visualización y exportación de Netlist SPICE."""
    def __init__(self, netlist_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Netlist del Circuito Esquemático")
        self.setMinimumSize(480, 320)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        lbl = QLabel("<b>Netlist Generado (SPICE / SKiDL):</b>")
        lbl.setStyleSheet("color: #a6e3a1; font-size: 13px;")
        layout.addWidget(lbl)

        self.txt_edit = QTextEdit()
        self.txt_edit.setText(netlist_text)
        self.txt_edit.setReadOnly(True)
        self.txt_edit.setStyleSheet("QTextEdit { background-color: #181825; color: #a6e3a1; font-family: monospace; border: 1px solid #45475a; }")
        layout.addWidget(self.txt_edit)

        btn_box = QHBoxLayout()
        btn_copy = QPushButton("📋 Copiar Netlist")
        btn_copy.setStyleSheet("background: #a6e3a1; color: #111; font-weight: bold; padding: 6px 12px; border-radius: 4px;")
        btn_copy.clicked.connect(lambda: (QApplication.clipboard().setText(self.txt_edit.toPlainText()), QMessageBox.information(self, "Éxito", "Netlist copiado al portapapeles.")))
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        btn_box.addWidget(btn_copy)
        btn_box.addStretch()
        btn_box.addWidget(btn_close)
        layout.addLayout(btn_box)


class SchematicComponentEditDialog(QDialog):
    """Diálogo interactivo para editar parámetros, etiquetas y pines de un componente esquemático."""
    def __init__(self, comp_item: SchematicComponentItem, parent=None):
        super().__init__(parent)
        self.comp_item = comp_item
        self.setWindowTitle(f"⚡ Editar Componente - {comp_item.ref}")
        self.setMinimumWidth(560)
        self.setMinimumHeight(440)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #cdd6f4; font-size: 12px; }
            QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 5px; font-weight: bold; }
            QTableWidget { background-color: #181825; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; gridline-color: #313244; }
            QHeaderView::section { background-color: #313244; color: #a6e3a1; font-weight: bold; border: none; padding: 4px; }
            QPushButton { background-color: #313244; color: #cdd6f4; border-radius: 4px; padding: 6px 12px; font-size: 11px; font-weight: bold; }
            QPushButton:hover { background-color: #89b4fa; color: #111; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(14)

        # Panel izquierdo: Formulario y tabla de pines
        left_box = QVBoxLayout()
        left_box.setSpacing(10)

        # Header Info
        lbl_sym = QLabel(f"<b>Símbolo:</b> <span style='color:#89b4fa;'>{self.comp_item.sym_name}</span>")
        left_box.addWidget(lbl_sym)

        # Form layout for Ref and Value
        form_layout = QHBoxLayout()
        form_layout.setSpacing(10)

        v_ref = QVBoxLayout()
        v_ref.addWidget(QLabel("Referencia (Designador):"))
        self.txt_ref = QLineEdit(self.comp_item.ref)
        self.txt_ref.textChanged.connect(self._update_preview)
        v_ref.addWidget(self.txt_ref)
        form_layout.addLayout(v_ref)

        v_val = QVBoxLayout()
        v_val.addWidget(QLabel("Valor / Nombre Componente:"))
        self.txt_val = QLineEdit(self.comp_item.val)
        self.txt_val.textChanged.connect(self._update_preview)
        v_val.addWidget(self.txt_val)
        form_layout.addLayout(v_val)

        left_box.addLayout(form_layout)

        # Tabla de Pines
        lbl_pins = QLabel("<b>Etiquetas / Nombres de Pines:</b>")
        left_box.addWidget(lbl_pins)

        self.table_pins = QTableWidget()
        self.table_pins.setColumnCount(2)
        self.table_pins.setHorizontalHeaderLabels(["Pin #", "Etiqueta / Nombre"])
        self.table_pins.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table_pins.setColumnWidth(0, 60)
        self.table_pins.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.table_pins.setRowCount(len(self.comp_item.pins_def))
        for row, (px, py, pname) in enumerate(self.comp_item.pins_def):
            item_num = QTableWidgetItem(f"#{row+1}")
            item_num.setFlags(item_num.flags() ^ Qt.ItemFlag.ItemIsEditable)
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_pins.setItem(row, 0, item_num)

            item_label = QTableWidgetItem(str(pname))
            self.table_pins.setItem(row, 1, item_label)

        self.table_pins.itemChanged.connect(lambda _: self._update_preview())
        left_box.addWidget(self.table_pins, 1)

        # Botones
        btn_box = QHBoxLayout()
        btn_save = QPushButton("💾 Guardar Cambios")
        btn_save.setStyleSheet("background-color: #a6e3a1; color: #111;")
        btn_save.clicked.connect(self.accept_changes)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_save)
        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        left_box.addLayout(btn_box)

        main_layout.addLayout(left_box, 1)

        # Panel derecho: Live Preview Canvas
        right_box = QVBoxLayout()
        lbl_prev = QLabel("<b>Vista Previa:</b>")
        right_box.addWidget(lbl_prev)

        self.preview_scene = QGraphicsScene()
        self.preview_scene.setBackgroundBrush(QBrush(QColor("#181825")))
        self.preview_view = QGraphicsView(self.preview_scene)
        self.preview_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.preview_view.setFixedSize(210, 270)
        self.preview_view.setStyleSheet("QGraphicsView { border: 1px solid #45475a; border-radius: 6px; }")
        right_box.addWidget(self.preview_view)
        right_box.addStretch()

        main_layout.addLayout(right_box)

        self._update_preview()

    def _update_preview(self):
        self.preview_scene.clear()
        temp_pins = []
        for row in range(self.table_pins.rowCount()):
            px, py, _ = self.comp_item.pins_def[row]
            item_label = self.table_pins.item(row, 1)
            lbl_str = item_label.text().strip() if item_label else str(row+1)
            temp_pins.append((px, py, lbl_str))

        prev_item = SchematicComponentItem(
            self.comp_item.sym_name,
            self.txt_ref.text().strip() or "U1",
            self.txt_val.text().strip() or "VAL",
            0, 0, self.comp_item.angle
        )
        prev_item.pins_def = temp_pins
        prev_item._recalc_rect()
        self.preview_scene.addItem(prev_item)
        rect = prev_item.boundingRect().adjusted(-25, -25, 25, 25)
        self.preview_view.setSceneRect(rect)
        self.preview_view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def accept_changes(self):
        self.comp_item.ref = self.txt_ref.text().strip() or self.comp_item.ref
        self.comp_item.val = self.txt_val.text().strip() or self.comp_item.val
        
        new_pins = []
        for row in range(self.table_pins.rowCount()):
            px, py, _ = self.comp_item.pins_def[row]
            item_label = self.table_pins.item(row, 1)
            lbl_str = item_label.text().strip() if item_label else str(row+1)
            new_pins.append((px, py, lbl_str))
        
        self.comp_item.pins_def = new_pins
        self.comp_item._recalc_rect()
        self.comp_item.update()
        self.accept()


class SnapIndicatorItem(QGraphicsItem):
    """Indicador visual de fijación a pines o grilla."""
    def __init__(self):
        super().__init__()
        self.setZValue(30)
        self.is_pin = False
        self.setVisible(False)
        self._rect = QRectF(-8, -8, 16, 16)

    def boundingRect(self):
        return self._rect

    def set_snap(self, pos: QPointF, is_pin: bool):
        self.setPos(pos)
        self.is_pin = is_pin
        self.setVisible(True)
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if self.is_pin:
            painter.setPen(QPen(QColor("#a6e3a1"), 2))
            painter.setBrush(QBrush(QColor(166, 227, 161, 70)))
            painter.drawEllipse(self._rect)
            painter.setBrush(QBrush(QColor("#a6e3a1")))
            painter.drawEllipse(-3, -3, 6, 6)
        else:
            painter.setPen(QPen(QColor("#89b4fa"), 1, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(-5, -5, 10, 10)


def _find_editor_widget(obj):
    """Encuentra recursivamente la instancia de SchematicEditorWidget buscando en los ancestros de Qt."""
    while obj:
        if hasattr(obj, '_edit_component'):
            return obj
        obj = obj.parent() if hasattr(obj, 'parent') and callable(obj.parent) else None
    return None


class SchematicScene(QGraphicsScene):
    """Escena 2D con rejilla CAD y soporte para cableado ortogonal."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSceneRect(-2000, -2000, 4000, 4000)
        self.grid_size = 10
        self.wiring_mode = False
        self.wire_pts = []
        self.start_comp = None
        self.start_pin_idx = None
        self.temp_wire_item = None

        self.snap_indicator = SnapIndicatorItem()
        self.addItem(self.snap_indicator)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor("#181825"))
        pen = QPen(QColor("#313244"), 1, Qt.PenStyle.DotLine)
        painter.setPen(pen)

        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)

        for x in range(left, int(rect.right()), self.grid_size * 2):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
        for y in range(top, int(rect.bottom()), self.grid_size * 2):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def snap(self, pos: QPointF) -> QPointF:
        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPointF(x, y)

    def find_snap_point(self, pos: QPointF, snap_distance: float = 15.0):
        """Encuentra la posición del pin más cercano dentro de snap_distance, o ajusta a la grilla."""
        best_dist = snap_distance
        best_pos = None
        best_comp = None
        best_pin_idx = None

        for item in self.items():
            if isinstance(item, SchematicComponentItem):
                for idx, (px, py, pname) in enumerate(item.pins_def):
                    pin_scene_pos = item.mapToScene(QPointF(px, py))
                    dist = QLineF(pos, pin_scene_pos).length()
                    if dist < best_dist:
                        best_dist = dist
                        best_pos = pin_scene_pos
                        best_comp = item
                        best_pin_idx = idx

        if best_pos is not None:
            return best_pos, best_comp, best_pin_idx

        grid_pos = self.snap(pos)
        return grid_pos, None, None

    def mouseMoveEvent(self, event):
        if self.wiring_mode:
            snap_pos, comp, pin_idx = self.find_snap_point(event.scenePos())
            self.snap_indicator.set_snap(snap_pos, is_pin=(comp is not None))

            if self.wire_pts:
                p0 = self.wire_pts[0]
                p2 = snap_pos
                if abs(p0.x() - p2.x()) > 2 and abs(p0.y() - p2.y()) > 2:
                    mid = QPointF(p2.x(), p0.y())
                    pts = [p0, mid, p2]
                else:
                    pts = [p0, p2]

                path = QPainterPath()
                path.moveTo(pts[0])
                for pt in pts[1:]:
                    path.lineTo(pt)

                if not self.temp_wire_item:
                    self.temp_wire_item = QGraphicsPathItem()
                    pen = QPen(QColor("#a6e3a1"), 2, Qt.PenStyle.DashLine)
                    self.temp_wire_item.setPen(pen)
                    self.addItem(self.temp_wire_item)

                self.temp_wire_item.setPath(path)
        else:
            self.snap_indicator.setVisible(False)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self.wiring_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                snap_pos, comp, pin_idx = self.find_snap_point(event.scenePos())
                if not self.wire_pts:
                    # Iniciar nuevo cable desde este pin o punto de grilla
                    self.wire_pts = [snap_pos]
                    self.start_comp = comp
                    self.start_pin_idx = pin_idx
                else:
                    # Finalizar tramo de cable hacia este punto/pin
                    p0 = self.wire_pts[0]
                    p2 = snap_pos
                    if abs(p0.x() - p2.x()) > 2 and abs(p0.y() - p2.y()) > 2:
                        mid = QPointF(p2.x(), p0.y())
                        pts = [p0, mid, p2]
                    else:
                        pts = [p0, p2]

                    wire = SchematicWireItem(
                        pts,
                        start_comp=self.start_comp,
                        start_pin_idx=self.start_pin_idx,
                        end_comp=comp,
                        end_pin_idx=pin_idx
                    )
                    self.addItem(wire)

                    if comp is not None:
                        self.clear_wiring_state()
                    else:
                        self.wire_pts = [snap_pos]
                        self.start_comp = None
                        self.start_pin_idx = None
                return
            elif event.button() == Qt.MouseButton.RightButton:
                self.clear_wiring_state()
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if not self.wiring_mode:
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, SchematicComponentItem):
                editor = _find_editor_widget(self)
                if editor:
                    editor._edit_component(item)
                    return
            elif isinstance(item, SchematicWireItem):
                new_pt = self.snap(event.scenePos())
                best_idx = 1
                best_d = 99999
                for i in range(len(item.pts) - 1):
                    seg_line = QLineF(item.pts[i], item.pts[i+1])
                    d = seg_line.length()
                    if d < best_d:
                        best_idx = i + 1
                item.pts.insert(best_idx, new_pt)
                item.update_path()
                item.show_handles()
                return
        super().mouseDoubleClickEvent(event)

    def clear_wiring_state(self):
        self.wire_pts = []
        self.start_comp = None
        self.start_pin_idx = None
        if self.temp_wire_item:
            if self.temp_wire_item.scene():
                self.removeItem(self.temp_wire_item)
            self.temp_wire_item = None
        self.snap_indicator.setVisible(False)


class SchematicView(QGraphicsView):
    """Vista 2D para visualización del editor esquemático."""
    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 0.85
            self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def contextMenuEvent(self, event):
        item = self.itemAt(event.pos())
        scene_pos = self.mapToScene(event.pos())
        editor = _find_editor_widget(self) or _find_editor_widget(self.scene())

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; font-family: 'Segoe UI', sans-serif; }
            QMenu::item { padding: 6px 20px; font-weight: bold; }
            QMenu::item:selected { background-color: #89b4fa; color: #11111b; }
        """)

        if isinstance(item, SchematicComponentItem):
            action_rotate = menu.addAction("🔄 Rotar 90° (R)")
            action_edit = menu.addAction("✏️ Editar Componente...")
            menu.addSeparator()
            action_delete = menu.addAction("🗑️ Eliminar (Supr)")

            action_rotate.triggered.connect(item.rotate_90)
            if editor:
                action_edit.triggered.connect(lambda: editor._edit_component(item))
            action_delete.triggered.connect(lambda: self.scene().removeItem(item))
            menu.exec(event.globalPos())
            return

        elif isinstance(item, SchematicWireItem):
            action_net = menu.addAction("🏷️ Asignar Nombre de Red...")
            action_add_pt = menu.addAction("➕ Agregar Nodo de Esquina")
            menu.addSeparator()
            action_delete = menu.addAction("🗑️ Eliminar Cable (Supr)")

            def _edit_wire_net():
                text, ok = QInputDialog.getText(self, "Etiqueta de Red", "Nombre de la Red (Net):", text=item.net_name)
                if ok: item.net_name = text.strip()

            def _add_corner():
                new_pt = self.scene().snap(scene_pos)
                best_idx = 1
                best_d = 99999
                for i in range(len(item.pts) - 1):
                    seg_line = QLineF(item.pts[i], item.pts[i+1])
                    d = seg_line.length()
                    if d < best_d:
                        best_idx = i + 1
                item.pts.insert(best_idx, new_pt)
                item.update_path()
                item.show_handles()

            action_net.triggered.connect(_edit_wire_net)
            action_add_pt.triggered.connect(_add_corner)
            action_delete.triggered.connect(lambda: (item.hide_handles(), self.scene().removeItem(item)))
            menu.exec(event.globalPos())
            return

        elif isinstance(item, SchematicNetLabelItem):
            action_edit = menu.addAction("✏️ Editar Nombre de Red...")
            action_delete = menu.addAction("🗑️ Eliminar Etiqueta (Supr)")

            def _edit_label():
                text, ok = QInputDialog.getText(self, "Editar Etiqueta", "Nombre de la Red:", text=item.net_name)
                if ok and text.strip():
                    item.net_name = text.strip().upper()
                    item.update()

            action_edit.triggered.connect(_edit_label)
            action_delete.triggered.connect(lambda: self.scene().removeItem(item))
            menu.exec(event.globalPos())
            return

        # Menú contextual de lienzo libre (escena)
        action_wire = menu.addAction("✏️ Modo Cableado")
        action_wire.setCheckable(True)
        action_wire.setChecked(self.scene().wiring_mode)
        action_net = menu.addAction("🏷️ Agregar Etiqueta de Red")
        menu.addSeparator()
        action_bom = menu.addAction("📋 Lista de Materiales (BOM)")
        action_netlist = menu.addAction("📄 Netlist SPICE")

        if editor:
            if hasattr(editor, 'btn_wire'):
                action_wire.triggered.connect(lambda chk: editor.btn_wire.setChecked(chk))
            if hasattr(editor, '_add_net_label'):
                action_net.triggered.connect(editor._add_net_label)
            if hasattr(editor, '_show_bom'):
                action_bom.triggered.connect(editor._show_bom)
            if hasattr(editor, '_show_netlist'):
                action_netlist.triggered.connect(editor._show_netlist)

        menu.exec(event.globalPos())


class SchematicEditorWidget(QFrame):
    """Editor interactivo de Diagramas Esquemáticos Electrónicos."""
    close_requested = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, calc_dict: dict, item_analysis: dict, agenda_path: str, parent=None):
        super().__init__(parent)
        self.calc_dict = calc_dict
        self.item_analysis = item_analysis
        self.agenda_path = agenda_path
        self.storage_path = self._get_storage_path()
        
        self.setStyleSheet("""
            SchematicEditorWidget { background-color: #1e1e2e; border: 1px solid #45475a; border-radius: 8px; }
            QLabel { color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
        """)
        self._setup_ui()
        self._load_content()

    def _get_storage_dir(self) -> str:
        if not self.agenda_path: return ""
        item_name = self.item_analysis.get('name', 'Sin_Nombre').strip()
        safe_name = "".join([c for c in item_name if c.isalnum() or c in (' ', '_', '-', '.')]).strip() or 'Sin_Nombre'
        calc_id = self.calc_dict.get('id', 'sch')
        folder_path = os.path.join(self.agenda_path, 'laboratorio', 'desarrollo', safe_name, calc_id)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def _get_storage_path(self) -> str:
        folder = self._get_storage_dir()
        if not folder: return ""
        return os.path.join(folder, "schematic.json")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        # Header toolbar
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        proj_name = self.item_analysis.get('name', 'Proyecto')
        lbl_title = QLabel(f"⚡ <b>Editor Esquemático: {proj_name}</b>")
        lbl_title.setStyleSheet("font-size: 14px; color: #a6e3a1;")
        hdr.addWidget(lbl_title, 1)

        self.btn_wire = QPushButton("✏️ Modo Cableado")
        self.btn_wire.setCheckable(True)
        self.btn_wire.setStyleSheet("QPushButton { background: #313244; color: #cdd6f4; padding: 5px 10px; border-radius: 4px; } QPushButton:checked { background: #f9e2af; color: #111; font-weight: bold; }")
        self.btn_wire.toggled.connect(self._toggle_wire_mode)
        hdr.addWidget(self.btn_wire)

        btn_net = QPushButton("🏷️ Etiqueta Red")
        btn_net.setStyleSheet("QPushButton { background: #cba6f7; color: #111; font-weight: bold; padding: 5px 10px; border-radius: 4px; }")
        btn_net.clicked.connect(self._add_net_label)
        hdr.addWidget(btn_net)

        btn_rotate = QPushButton("🔄 Rotar (R)")
        btn_rotate.setStyleSheet("QPushButton { background: #89b4fa; color: #111; font-weight: bold; padding: 5px 10px; border-radius: 4px; }")
        btn_rotate.clicked.connect(self._rotate_selected)
        hdr.addWidget(btn_rotate)

        btn_bom = QPushButton("📋 BOM")
        btn_bom.setStyleSheet("QPushButton { background: #a6e3a1; color: #111; font-weight: bold; padding: 5px 10px; border-radius: 4px; }")
        btn_bom.clicked.connect(self._show_bom)
        hdr.addWidget(btn_bom)

        btn_netlist = QPushButton("📄 Netlist")
        btn_netlist.setStyleSheet("QPushButton { background: #fab387; color: #111; font-weight: bold; padding: 5px 10px; border-radius: 4px; }")
        btn_netlist.clicked.connect(self._show_netlist)
        hdr.addWidget(btn_netlist)

        btn_png = QPushButton("🖼️ Exportar PNG")
        btn_png.setStyleSheet("QPushButton { background: #94e2d5; color: #111; font-weight: bold; padding: 5px 10px; border-radius: 4px; }")
        btn_png.clicked.connect(self._export_png)
        hdr.addWidget(btn_png)

        btn_save = QPushButton("💾 Guardar")
        btn_save.setStyleSheet("QPushButton { background: #a6e3a1; color: #111; font-weight: bold; padding: 5px 12px; border-radius: 4px; }")
        btn_save.clicked.connect(self._save_content)
        hdr.addWidget(btn_save)

        btn_close = QPushButton("⬅ Volver")
        btn_close.setStyleSheet("QPushButton { background: #45475a; color: #fff; font-weight: bold; padding: 5px 12px; border-radius: 4px; }")
        btn_close.clicked.connect(self.close_requested.emit)
        hdr.addWidget(btn_close)

        layout.addLayout(hdr)

        # Main splitter (Palette on Left, Canvas on Right)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Palette Panel
        palette_w = QWidget()
        palette_l = QVBoxLayout(palette_w)
        palette_l.setContentsMargins(0, 0, 0, 0)
        palette_l.setSpacing(6)

        lbl_pal = QLabel("<b>Símbolos IEEE/IEC</b>")
        lbl_pal.setStyleSheet("color: #89b4fa; font-size: 12px;")
        palette_l.addWidget(lbl_pal)

        scroll_pal = QScrollArea()
        scroll_pal.setWidgetResizable(True)
        scroll_pal.setMinimumWidth(170)
        scroll_pal.setMaximumWidth(210)
        scroll_pal.setStyleSheet("QScrollArea { background-color: #181825; border: 1px solid #313244; border-radius: 4px; }")

        pal_content = QWidget()
        pal_layout = QVBoxLayout(pal_content)
        pal_layout.setContentsMargins(6, 6, 6, 6)
        pal_layout.setSpacing(4)

        for sym_name in SCHEMATIC_SYMBOLS.keys():
            btn_sym = QPushButton(sym_name)
            btn_sym.setStyleSheet("QPushButton { background: #313244; color: #cdd6f4; font-size: 11px; text-align: left; padding: 5px; border-radius: 3px; } QPushButton:hover { background: #89b4fa; color: #111; font-weight: bold; }")
            btn_sym.clicked.connect(lambda _, s=sym_name: self._add_symbol(s))
            pal_layout.addWidget(btn_sym)

        pal_layout.addStretch()
        scroll_pal.setWidget(pal_content)
        palette_l.addWidget(scroll_pal)
        splitter.addWidget(palette_w)

        # Right Scene & View
        self.scene = SchematicScene(self)
        self.view = SchematicView(self.scene, self)
        splitter.addWidget(self.view)
        splitter.setSizes([180, 820])

        layout.addWidget(splitter, 1)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_R:
            self._rotate_selected()
        elif event.key() == Qt.Key.Key_Delete:
            self._delete_selected()
        else:
            super().keyPressEvent(event)

    def _toggle_wire_mode(self, enabled: bool):
        self.scene.wiring_mode = enabled
        self.scene.clear_wiring_state()
        if enabled:
            self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.view.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def _add_symbol(self, sym_name: str):
        sym_info = SCHEMATIC_SYMBOLS.get(sym_name, {})
        ref_prefix = sym_info.get('ref', 'U')
        val_default = sym_info.get('val', '10k')

        # Auto-incremental Ref Designator
        count = sum(1 for it in self.scene.items() if isinstance(it, SchematicComponentItem) and it.sym_name == sym_name) + 1
        ref_str = f"{ref_prefix}{count}" if not ref_prefix.startswith('#') else ref_prefix.replace('#', '')

        comp = SchematicComponentItem(sym_name, ref_str, val_default, 0, 0)
        self.scene.addItem(comp)
        comp.setSelected(True)

    def _add_net_label(self):
        name, ok = QInputDialog.getText(self, "Etiqueta de Red", "Nombre de la Red (Net Label):", text="VCC")
        if ok and name.strip():
            item = SchematicNetLabelItem(name.strip().upper(), 0, 0)
            self.scene.addItem(item)

    def _rotate_selected(self):
        for it in self.scene.selectedItems():
            if isinstance(it, SchematicComponentItem):
                it.rotate_90()

    def _delete_selected(self):
        for item in self.scene.selectedItems():
            if isinstance(item, SchematicComponentItem):
                for it in self.scene.items():
                    if isinstance(it, SchematicWireItem):
                        if it.start_comp == item:
                            it.start_comp = None
                            it.start_pin_idx = None
                        if it.end_comp == item:
                            it.end_comp = None
                            it.end_pin_idx = None
            elif isinstance(item, SchematicWireItem):
                item.hide_handles()
            self.scene.removeItem(item)

    def _show_bom(self):
        comps = [it for it in self.scene.items() if isinstance(it, SchematicComponentItem) and not it.ref.startswith('#')]
        dlg = BOMDialog(comps, self)
        dlg.exec()

    def _show_netlist(self):
        comps = [it for it in self.scene.items() if isinstance(it, SchematicComponentItem)]
        lines = [f"* NETLIST ESQUEMÁTICO SPICE - {self.item_analysis.get('name', 'Proyecto')}", "*"]
        for c in comps:
            lines.append(f"{c.ref}\tNET_IN\tNET_OUT\t{c.val}\t; {c.sym_name}")
        lines.append("\n.END")
        dlg = NetlistDialog("\n".join(lines), self)
        dlg.exec()

    def _export_png(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Exportar Diagrama Esquemático", f"esquematico_{self.item_analysis.get('name', 'circuito')}.png", "Imágenes PNG (*.png)")
        if file_path:
            rect = self.scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
            image = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
            image.fill(QColor("#181825"))
            painter = QPainter(image)
            self.scene.render(painter, QRectF(image.rect()), rect)
            painter.end()
            image.save(file_path)
            QMessageBox.information(self, "Éxito", f"Esquemático exportado correctamente a:\n{file_path}")

    def _edit_component(self, comp: SchematicComponentItem):
        dlg = SchematicComponentEditDialog(comp, parent=self)
        if dlg.exec():
            comp.update()
            self.scene.update()

    def _load_content(self):
        target_path = self.storage_path
        if not target_path or not os.path.exists(target_path):
            proj_id = self.item_analysis.get('id', 'proj')
            raw_name = self.calc_dict.get('name', 'esquematico')
            clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', raw_name).strip('_') or 'esquematico'
            calc_id = self.calc_dict.get('id', 'schematic')
            folder_name = f"{clean_name}_{calc_id}"
            
            misplaced_1 = os.path.join(self.agenda_path, 'desarrollo', proj_id, folder_name, "schematic.json")
            misplaced_2 = os.path.join(self.agenda_path, 'desarrollo', proj_id, f"schematic_{calc_id}.json")
            if os.path.exists(misplaced_1):
                target_path = misplaced_1
            elif os.path.exists(misplaced_2):
                target_path = misplaced_2
            else:
                self._add_symbol("Resistencia (R)")
                self._add_symbol("Condensador (C)")
                self._add_symbol("Tierra (GND)")
                return
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            ref_map = {}
            for c in data.get('components', []):
                item = SchematicComponentItem(c['sym_name'], c['ref'], c['val'], c['x'], c['y'], c.get('rot', 0))
                if 'pins' in c:
                    item.pins_def = [tuple(p) for p in c['pins']]
                    item._recalc_rect()
                self.scene.addItem(item)
                ref_map[c['ref']] = item

            for nl in data.get('net_labels', []):
                item = SchematicNetLabelItem(nl['net_name'], nl['x'], nl['y'])
                self.scene.addItem(item)

            for w in data.get('wires', []):
                pts = [QPointF(p[0], p[1]) for p in w.get('pts', [])]
                start_comp = ref_map.get(w.get('start_ref'))
                end_comp = ref_map.get(w.get('end_ref'))
                wire_item = SchematicWireItem(
                    pts,
                    net_name=w.get('net_name', ''),
                    start_comp=start_comp,
                    start_pin_idx=w.get('start_pin'),
                    end_comp=end_comp,
                    end_pin_idx=w.get('end_pin')
                )
                self.scene.addItem(wire_item)
                wire_item.update_from_component_move(start_comp)
                wire_item.update_from_component_move(end_comp)
        except Exception as e:
            print(f"Error loading schematic layout: {e}")

    def _save_content(self):
        if not self.storage_path: return
        data = {'components': [], 'wires': [], 'net_labels': []}

        for it in self.scene.items():
            if isinstance(it, SchematicComponentItem):
                pins_data = [[px, py, str(pname)] for px, py, pname in it.pins_def]
                data['components'].append({
                    'sym_name': it.sym_name,
                    'ref': it.ref,
                    'val': it.val,
                    'x': it.pos().x(),
                    'y': it.pos().y(),
                    'rot': it.angle,
                    'pins': pins_data
                })
            elif isinstance(it, SchematicNetLabelItem):
                data['net_labels'].append({
                    'net_name': it.net_name,
                    'x': it.pos().x(),
                    'y': it.pos().y()
                })
            elif isinstance(it, SchematicWireItem):
                path_pts = [[p.x(), p.y()] for p in it.pts]
                wire_dict = {
                    'pts': path_pts,
                    'net_name': it.net_name,
                    'start_ref': it.start_comp.ref if it.start_comp else "",
                    'start_pin': it.start_pin_idx,
                    'end_ref': it.end_comp.ref if it.end_comp else "",
                    'end_pin': it.end_pin_idx
                }
                data['wires'].append(wire_dict)

        try:
            folder = self._get_storage_dir()
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Renderizar y guardar imagen de previsualización PNG dentro de la carpeta del esquemático
            preview_p = os.path.join(folder, "preview.png")
            rect = self.scene.itemsBoundingRect().adjusted(-30, -30, 30, 30)
            if rect.width() > 10 and rect.height() > 10:
                img = QImage(int(rect.width()), int(rect.height()), QImage.Format.Format_ARGB32)
                img.fill(QColor("#181825"))
                p = QPainter(img)
                self.scene.render(p, QRectF(img.rect()), rect)
                p.end()
                img.save(preview_p)

            QMessageBox.information(self, "Guardado", f"Diagrama esquemático guardado correctamente en la carpeta:\n{folder}")
            self.saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el esquemático: {e}")


