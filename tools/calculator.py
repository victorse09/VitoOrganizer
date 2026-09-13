# =============================================================================
# Vito Organizer - Calculator Tool
# Calculadora flotante con tres modos: Básica, Científica, Electrónica
# =============================================================================

import os
import math
from functools import partial

from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QKeySequence, QShortcut, QColor, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QFrame, QStackedWidget, QWidget, QScrollArea,
    QComboBox, QDoubleSpinBox, QSpinBox, QListWidget, QListWidgetItem,
    QTabWidget, QSizePolicy, QApplication, QAbstractSpinBox
)

from tools.electronics_formulas import (
    ANALOG_FORMULAS, DIGITAL_FORMULAS, OTHER_FORMULAS, RESISTOR_COLORS
)

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')

# =============================================================================
# Catppuccin Mocha Palette
# =============================================================================
BG = "#1e1e2e"
SURFACE = "#313244"
TEXT = "#cdd6f4"
SUBTEXT = "#a6adc8"
ACCENT = "#f9e2af"
SUCCESS = "#a6e3a1"
ERROR = "#f38ba8"
BLUE = "#89b4fa"
PURPLE = "#cba6f7"
BORDER = "#45475a"
HOVER = "#585b70"

GLOBAL_STYLE = f"""
    QDialog {{
        background-color: {BG};
        color: {TEXT};
        font-family: "Segoe UI", sans-serif;
    }}
    QLabel {{
        color: {TEXT};
        font-family: "Segoe UI", sans-serif;
    }}
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        border-radius: 6px;
        background-color: {BG};
    }}
    QTabBar::tab {{
        background-color: {SURFACE};
        color: {TEXT};
        padding: 6px 14px;
        border: 1px solid {BORDER};
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
        font-size: 12px;
    }}
    QTabBar::tab:selected {{
        background-color: {BORDER};
        color: {ACCENT};
        font-weight: bold;
    }}
    QTabBar::tab:hover {{
        background-color: {HOVER};
    }}
    QScrollArea {{
        border: none;
        background-color: {BG};
    }}
    QScrollBar:vertical {{
        background-color: {BG};
        width: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {BORDER};
        border-radius: 5px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {HOVER};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {BG};
        height: 10px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {BORDER};
        border-radius: 5px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {HOVER};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QComboBox {{
        background-color: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
    }}
    QComboBox:hover {{
        border-color: {ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        selection-background-color: {BORDER};
        selection-color: {ACCENT};
    }}
    QDoubleSpinBox, QSpinBox {{
        background-color: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
    }}
    QDoubleSpinBox:hover, QSpinBox:hover {{
        border-color: {ACCENT};
    }}
    QListWidget {{
        background-color: {SURFACE};
        color: {TEXT};
        border: 1px solid {BORDER};
        border-radius: 6px;
        font-size: 12px;
    }}
    QListWidget::item {{
        padding: 4px 8px;
    }}
    QListWidget::item:hover {{
        background-color: {BORDER};
    }}
    QListWidget::item:selected {{
        background-color: {BORDER};
        color: {ACCENT};
    }}
"""


# =============================================================================
# FormulaPanel — Collapsible panel for electronics formulas
# =============================================================================
class FormulaPanel(QFrame):
    """Panel colapsable genérico para fórmulas de electrónica."""

    def __init__(self, formula_data: dict, parent=None):
        super().__init__(parent)
        self._formula = formula_data
        self._expanded = False
        self._input_widgets = {}
        self._dynamic_inputs = []
        self._result_label = None
        self._solve_combo = None
        self._truth_table_widget = None
        self._band_buttons = []
        self._resistor_value_label = None
        self._resistor_tolerance_label = None
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            FormulaPanel {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Header bar
        self._header = QPushButton()
        category_icon_map = {
            '⚡': 'lab.svg', '💡': 'lab.svg', '🔗': 'link.svg', '🔀': 'link.svg',
            '🔌': 'component.svg', '🔋': 'component.svg', '⏱️': 'history.svg',
            '🧲': 'tools.svg', '🎵': 'chart.svg', '📊': 'chart.svg', '📈': 'chart.svg',
            '📉': 'chart.svg', '📐': 'ruler.svg', '🔲': 'component.svg', '🌈': 'tag.svg',
            '🧭': 'ruler.svg', '🎛️': 'settings.svg', '📡': 'globe.svg', '🌉': 'link.svg',
            '🔁': 'history.svg', '⏲️': 'history.svg', '📝': 'document.svg', '🔢': 'calculator.svg'
        }
        raw_icon = self._formula.get('icon', '⚡')
        svg_file = category_icon_map.get(raw_icon, 'calculator.svg')
        svg_path = os.path.join(ICONS_DIR, svg_file)
        if os.path.exists(svg_path):
            self._header.setIcon(QIcon(svg_path))
            self._header.setIconSize(QSize(16, 16))

        name_text = self._formula.get('name', 'Fórmula')
        self._header.setText(f" {name_text}  ▶")
        self._header.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT};
                border: none;
                border-radius: 6px;
                text-align: left;
                padding: 10px 12px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
            }}
        """)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.clicked.connect(self._toggle)
        self._main_layout.addWidget(self._header)

        # Content area
        self._content = QWidget()
        self._content.setVisible(False)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 8, 12, 12)
        self._content_layout.setSpacing(8)

        formula_type = self._formula.get('type', 'standard')

        if formula_type == 'truth_table':
            self._build_truth_table_ui()
        elif formula_type == 'resistor_color_code':
            self._build_resistor_color_ui()
        else:
            self._build_standard_ui()

        self._main_layout.addWidget(self._content)

    def _toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        name_text = self._formula.get('name', 'Fórmula')
        arrow = "▼" if self._expanded else "▶"
        self._header.setText(f" {name_text}  {arrow}")

    # ---- Standard formula UI ----
    def _build_standard_ui(self):
        formulas_list = self._formula.get('formulas', [])
        variables = self._formula.get('variables', [])
        has_list_input = self._formula.get('list_input', False)

        if formulas_list:
            solve_row = QHBoxLayout()
            lbl = QLabel("Calcular:")
            lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
            solve_row.addWidget(lbl)
            self._solve_combo = QComboBox()
            for f in formulas_list:
                self._solve_combo.addItem(f.get('solve_for', ''))
            self._solve_combo.currentIndexChanged.connect(self._on_solve_changed)
            solve_row.addWidget(self._solve_combo, 1)
            self._content_layout.addLayout(solve_row)

        # Input fields container
        self._inputs_container = QWidget()
        self._inputs_layout = QVBoxLayout(self._inputs_container)
        self._inputs_layout.setContentsMargins(0, 0, 0, 0)
        self._inputs_layout.setSpacing(6)
        self._content_layout.addWidget(self._inputs_container)

        if has_list_input:
            self._build_list_input_ui(variables)
        else:
            self._build_variable_inputs(variables)

        # Result display
        self._result_label = QLabel("Resultado: —")
        self._result_label.setWordWrap(True)
        self._result_label.setStyleSheet(f"""
            QLabel {{
                color: {SUCCESS};
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        self._content_layout.addWidget(self._result_label)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_copy = QPushButton(" Copiar")
        btn_copy.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy.setIconSize(QSize(16, 16))
        btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy.setToolTip("Copiar fórmula y resultado")
        btn_copy.clicked.connect(self._copy_result)
        btn_row.addWidget(btn_copy)

        btn_copy_detail = QPushButton(" Copiar Detalle")
        btn_copy_detail.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy_detail.setIconSize(QSize(16, 16))
        btn_copy_detail.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy_detail.setToolTip("Copiar selección, detalle de parámetros y resultado")
        btn_copy_detail.clicked.connect(self._copy_detailed_result)
        btn_row.addWidget(btn_copy_detail)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {ERROR};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
            }}
        """)
        btn_clear.clicked.connect(self._clear_inputs)
        btn_row.addWidget(btn_clear)
        btn_row.addStretch()
        self._content_layout.addLayout(btn_row)

        if formulas_list:
            self._on_solve_changed(0)

    def _build_variable_inputs(self, variables):
        self._input_widgets.clear()
        for v in variables:
            row = QHBoxLayout()
            name_lbl = QLabel(f"{v.get('name', v.get('symbol', '?'))}:")
            name_lbl.setFixedWidth(130)
            name_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
            row.addWidget(name_lbl)

            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(-1e15, 1e15)
            spin.setValue(v.get('default', 0.0))
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.setSingleStep(0.1)
            spin.valueChanged.connect(self._calculate)
            row.addWidget(spin, 1)

            unit_lbl = QLabel(v.get('unit', ''))
            unit_lbl.setFixedWidth(40)
            unit_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
            row.addWidget(unit_lbl)

            self._input_widgets[v.get('symbol', v.get('name', ''))] = spin
            self._inputs_layout.addLayout(row)

    def _build_list_input_ui(self, variables):
        self._list_var = {
            'symbol': self._formula.get('input_symbol', 'X'),
            'name': self._formula.get('input_name', 'Valor'),
            'unit': self._formula.get('input_unit', ''),
            'default': 0.0
        }
        for v in variables:
            row = QHBoxLayout()
            name_lbl = QLabel(f"{v.get('name', v.get('symbol', '?'))}:")
            name_lbl.setFixedWidth(130)
            name_lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
            row.addWidget(name_lbl)

            spin = QDoubleSpinBox()
            spin.setDecimals(6)
            spin.setRange(-1e15, 1e15)
            spin.setValue(v.get('default', 0.0))
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.valueChanged.connect(self._calculate)
            row.addWidget(spin, 1)

            unit_lbl = QLabel(v.get('unit', ''))
            unit_lbl.setFixedWidth(40)
            unit_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
            row.addWidget(unit_lbl)

            self._input_widgets[v.get('symbol', v.get('name', ''))] = spin
            self._inputs_layout.addLayout(row)

        if self._list_var:
            count_row = QHBoxLayout()
            count_lbl = QLabel(f"Cantidad de {self._list_var.get('name', 'elementos')}:")
            count_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 12px;")
            count_row.addWidget(count_lbl)
            self._count_spin = QSpinBox()
            self._count_spin.setRange(2, 10)
            self._count_spin.setValue(2)
            self._count_spin.valueChanged.connect(self._rebuild_dynamic_inputs)
            count_row.addWidget(self._count_spin)
            count_row.addStretch()
            self._inputs_layout.addLayout(count_row)

            self._dynamic_container = QWidget()
            self._dynamic_layout = QVBoxLayout(self._dynamic_container)
            self._dynamic_layout.setContentsMargins(0, 0, 0, 0)
            self._dynamic_layout.setSpacing(4)
            self._inputs_layout.addWidget(self._dynamic_container)
            self._rebuild_dynamic_inputs(2)

    def _rebuild_dynamic_inputs(self, count):
        # Clear existing dynamic inputs
        for spin in self._dynamic_inputs:
            spin.valueChanged.disconnect(self._calculate)
        self._dynamic_inputs.clear()
        while self._dynamic_layout.count():
            item = self._dynamic_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        unit = self._list_var.get('unit', 'Ω') if self._list_var else 'Ω'
        sym = self._list_var.get('symbol', 'X') if self._list_var else 'X'
        for i in range(count):
            row = QHBoxLayout()
            lbl = QLabel(f"  {sym}{i+1}:")
            lbl.setFixedWidth(50)
            lbl.setStyleSheet(f"color: {TEXT}; font-size: 12px;")
            row.addWidget(lbl)
            spin = QDoubleSpinBox()
            spin.setDecimals(4)
            spin.setRange(0.0001, 1e12)
            spin.setValue(self._list_var.get('default', 1000.0) if self._list_var else 1000.0)
            spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
            spin.valueChanged.connect(self._calculate)
            row.addWidget(spin, 1)
            u_lbl = QLabel(unit)
            u_lbl.setFixedWidth(40)
            u_lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px;")
            row.addWidget(u_lbl)
            container_w = QWidget()
            container_l = QHBoxLayout(container_w)
            container_l.setContentsMargins(0, 0, 0, 0)
            container_l.addLayout(row)
            self._dynamic_layout.addWidget(container_w)
            self._dynamic_inputs.append(spin)

        self._calculate()

    def _on_solve_changed(self, index):
        formulas_list = self._formula.get('formulas', [])
        if index < 0 or index >= len(formulas_list):
            return
        selected = formulas_list[index]
        needed_inputs = selected.get('inputs', [])

        # Show/hide inputs based on what's needed
        for symbol, spin in self._input_widgets.items():
            parent_widget = spin.parent()
            visible = symbol in needed_inputs
            # Walk up to find the row layout and toggle visibility
            spin.setVisible(visible)
            # Also toggle the label and unit label in the same row
            layout = None
            for i in range(self._inputs_layout.count()):
                item = self._inputs_layout.itemAt(i)
                if item and item.layout():
                    for j in range(item.layout().count()):
                        sub = item.layout().itemAt(j)
                        if sub and sub.widget() == spin:
                            layout = item.layout()
                            break
                    if layout:
                        break
            if layout:
                for j in range(layout.count()):
                    w = layout.itemAt(j).widget()
                    if w:
                        w.setVisible(visible)

        self._calculate()

    def _calculate(self):
        formulas_list = self._formula.get('formulas', [])
        if not formulas_list or not self._solve_combo:
            return

        index = self._solve_combo.currentIndex()
        if index < 0 or index >= len(formulas_list):
            return

        selected = formulas_list[index]
        expr_fn = selected.get('expression')
        display_str = selected.get('display', '')
        solve_for = selected.get('solve_for', '')

        if not expr_fn:
            return

        try:
            # Collect input values
            has_list = self._formula.get('list_input', False)

            vals = {}
            for inp_sym in selected.get('inputs', []):
                if inp_sym in self._input_widgets:
                    vals[inp_sym] = self._input_widgets[inp_sym].value()

            if has_list and self._dynamic_inputs:
                values_list = [s.value() for s in self._dynamic_inputs]
                sym = self._formula.get('input_symbol', 'X')
                list_name = f"{sym}_list"
                vals[list_name] = values_list

            result = expr_fn(vals)

            if result is None:
                self._result_label.setText("Resultado: Error")
                return

            # Format the result nicely
            if abs(result) >= 1e6:
                result_str = f"{result:.4e}"
            elif abs(result) < 0.001 and result != 0:
                result_str = f"{result:.6e}"
            else:
                result_str = f"{result:.4f}".rstrip('0').rstrip('.')

            # Build full display string
            input_parts = []
            if has_list and self._dynamic_inputs:
                vals_str = ", ".join(f"{s.value():.2f}" for s in self._dynamic_inputs)
                input_parts.append(f"[{vals_str}]")
                
            for inp_sym in selected.get('inputs', []):
                if inp_sym.endswith('_list'):
                    continue
                if inp_sym in self._input_widgets:
                    v = self._input_widgets[inp_sym].value()
                    # Find the variable info
                    var_info = next((var for var in self._formula.get('variables', [])
                                     if var.get('symbol') == inp_sym), {})
                    unit = var_info.get('unit', '')
                    input_parts.append(f"{v:.2f} {unit}".strip())

            # If display_str already contains LHS assignment (e.g. "Tj = ...", "1/Rt = ...", "V = ...")
            lhs = display_str.split("=")[0].strip() if "=" in display_str else ""
            if lhs and (solve_for in lhs or display_str.startswith(solve_for)):
                full_display = display_str
            else:
                full_display = f"{solve_for} = {display_str}"

            if input_parts:
                full_display += f" = {' × '.join(input_parts)}"
            full_display += f" = {result_str}"

            # Find unit for the solved variable
            solve_unit = ''
            for var in self._formula.get('variables', []):
                if var.get('symbol') == solve_for or var.get('name') == solve_for:
                    solve_unit = var.get('unit', '')
                    break
            if solve_unit:
                full_display += f" {solve_unit}"

            self._result_label.setText(full_display)
            self._last_result_text = full_display

        except ZeroDivisionError:
            self._result_label.setText("Resultado: ∞ (División por cero)")
            self._last_result_text = "∞"
        except Exception as e:
            if self._result_label:
                self._result_label.setText(f"Resultado: Error ({str(e)[:40]})")
            self._last_result_text = "Error"

    def _copy_result(self):
        text = getattr(self, '_last_result_text', '')
        if text:
            QApplication.clipboard().setText(text)

    def _copy_detailed_result(self):
        formulas_list = self._formula.get('formulas', [])
        formula_name = self._formula.get('name', 'Fórmula')

        lines = [f"[{formula_name}]"]

        if self._solve_combo and formulas_list:
            idx = self._solve_combo.currentIndex()
            if 0 <= idx < len(formulas_list):
                selected = formulas_list[idx]
                solve_for = selected.get('solve_for', '')
                lines.append(f"Calcular: {solve_for}")

                has_list = self._formula.get('list_input', False)
                param_lines = []

                # Variables and parameters
                for inp_sym in selected.get('inputs', []):
                    if inp_sym.endswith('_list'):
                        continue
                    if inp_sym in self._input_widgets:
                        val = self._input_widgets[inp_sym].value()
                        val_str = f"{val:.6f}".rstrip('0').rstrip('.') if '.' in f"{val:.6f}" else f"{val:.0f}"
                        var_info = next((v for v in self._formula.get('variables', []) if v.get('symbol') == inp_sym), {})
                        var_name = var_info.get('name', inp_sym)
                        unit = var_info.get('unit', '')
                        param_lines.append(f"• {var_name}: {val_str} {unit}".strip())

                if has_list and self._dynamic_inputs:
                    sym = self._formula.get('input_symbol', 'X')
                    name = self._formula.get('input_name', 'Elemento')
                    unit = self._formula.get('input_unit', '')
                    param_lines.append(f"• Cantidad de {name}s: {len(self._dynamic_inputs)}")
                    for i, s in enumerate(self._dynamic_inputs, 1):
                        val_str = f"{s.value():.6f}".rstrip('0').rstrip('.') if '.' in f"{s.value():.6f}" else f"{s.value():.0f}"
                        param_lines.append(f"  - {sym}{i}: {val_str} {unit}".strip())

                if param_lines:
                    lines.append("Valores:")
                    lines.extend(param_lines)

        equation_result = getattr(self, '_last_result_text', '')
        if equation_result:
            lines.append("Resultado:")
            lines.append(f"{equation_result}")

        detailed_text = "\n".join(lines)
        QApplication.clipboard().setText(detailed_text)

    def _clear_inputs(self):
        for spin in self._input_widgets.values():
            spin.setValue(0.0)
        if hasattr(self, '_list_var') and self._list_var:
            for spin in self._dynamic_inputs:
                default = self._list_var.get('default', 1000.0)
                spin.setValue(default)
        if self._result_label:
            self._result_label.setText("Resultado: —")

    # ---- Truth Table UI (logic gates) ----
    def _build_truth_table_ui(self):
        gates = self._formula.get('gates', {})
        if not gates:
            lbl = QLabel("Sin compuertas definidas.")
            self._content_layout.addWidget(lbl)
            return

        # Gate selector
        gate_row = QHBoxLayout()
        lbl = QLabel("Compuerta:")
        lbl.setStyleSheet(f"color: {ACCENT}; font-weight: bold; font-size: 12px;")
        gate_row.addWidget(lbl)
        self._gate_combo = QComboBox()
        for gate_name in gates.keys():
            self._gate_combo.addItem(gate_name)
        self._gate_combo.currentTextChanged.connect(self._update_truth_table)
        gate_row.addWidget(self._gate_combo, 1)
        self._content_layout.addLayout(gate_row)

        # Interactive test
        test_frame = QFrame()
        test_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        test_layout = QHBoxLayout(test_frame)
        test_layout.setSpacing(10)

        lbl_a = QLabel("A:")
        lbl_a.setStyleSheet(f"color: {TEXT}; font-weight: bold;")
        test_layout.addWidget(lbl_a)
        self._btn_a = QPushButton("0")
        self._btn_a.setCheckable(True)
        self._btn_a.setFixedSize(40, 32)
        self._btn_a.setStyleSheet(self._toggle_btn_style(False))
        self._btn_a.toggled.connect(lambda checked: (
            self._btn_a.setText("1" if checked else "0"),
            self._btn_a.setStyleSheet(self._toggle_btn_style(checked)),
            self._update_gate_output()
        ))
        test_layout.addWidget(self._btn_a)

        lbl_b = QLabel("B:")
        lbl_b.setStyleSheet(f"color: {TEXT}; font-weight: bold;")
        test_layout.addWidget(lbl_b)
        self._btn_b = QPushButton("0")
        self._btn_b.setCheckable(True)
        self._btn_b.setFixedSize(40, 32)
        self._btn_b.setStyleSheet(self._toggle_btn_style(False))
        self._btn_b.toggled.connect(lambda checked: (
            self._btn_b.setText("1" if checked else "0"),
            self._btn_b.setStyleSheet(self._toggle_btn_style(checked)),
            self._update_gate_output()
        ))
        test_layout.addWidget(self._btn_b)

        lbl_out = QLabel("  →  Salida:")
        lbl_out.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        test_layout.addWidget(lbl_out)
        self._output_lbl = QLabel("0")
        self._output_lbl.setFixedSize(40, 32)
        self._output_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._output_lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {SURFACE};
                color: {SUCCESS};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        test_layout.addWidget(self._output_lbl)
        test_layout.addStretch()
        self._content_layout.addWidget(test_frame)

        # Full truth table display
        self._truth_table_widget = QLabel()
        self._truth_table_widget.setStyleSheet(f"""
            QLabel {{
                color: {TEXT};
                font-family: monospace;
                font-size: 12px;
                padding: 8px;
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        self._content_layout.addWidget(self._truth_table_widget)

        # Copy button
        btn_copy = QPushButton(" Copiar tabla")
        btn_copy.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy.setIconSize(QSize(16, 16))
        btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy.clicked.connect(lambda: QApplication.clipboard().setText(
            self._truth_table_widget.text() if self._truth_table_widget else ''
        ))
        self._content_layout.addWidget(btn_copy, alignment=Qt.AlignmentFlag.AlignLeft)

        self._update_truth_table(self._gate_combo.currentText())

    def _toggle_btn_style(self, checked):
        bg = SUCCESS if checked else SURFACE
        fg = BG if checked else TEXT
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
            }}
        """

    def _update_truth_table(self, gate_name):
        gates = self._formula.get('gates', {})
        gate_data = gates.get(gate_name)
        if not gate_data:
            return
        gate_fn = gate_data.get('expression')

        # Build truth table text
        lines = [f"  {'A':>3}  {'B':>3}  {'Salida':>6}", "  " + "─" * 18]
        for a in (0, 1):
            for b in (0, 1):
                try:
                    out = gate_fn(a, b)
                except TypeError:
                    # Single input gate (like NOT)
                    out = gate_fn(a)
                lines.append(f"  {a:>3}  {b:>3}  {int(out):>6}")

        if self._truth_table_widget:
            self._truth_table_widget.setText("\n".join(lines))

        self._update_gate_output()

    def _update_gate_output(self):
        gates = self._formula.get('gates', {})
        gate_name = self._gate_combo.currentText() if hasattr(self, '_gate_combo') else ''
        gate_data = gates.get(gate_name)
        if not gate_data:
            return
        gate_fn = gate_data.get('expression')

        a = 1 if self._btn_a.isChecked() else 0
        b = 1 if self._btn_b.isChecked() else 0
        try:
            out = gate_fn(a, b)
        except TypeError:
            out = gate_fn(a)
        self._output_lbl.setText(str(int(out)))
        color = SUCCESS if out else ERROR
        self._output_lbl.setStyleSheet(f"""
            QLabel {{
                background-color: {SURFACE};
                color: {color};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)

    # ---- Resistor Color Code UI ----
    def _build_resistor_color_ui(self):
        bands_config = self._formula.get('bands', 4)  # 4 or 5 band
        color_data = RESISTOR_COLORS  # dict with color_name -> {hex, digit, multiplier, tolerance}

        info_lbl = QLabel("Seleccione el color de cada banda:")
        info_lbl.setStyleSheet(f"color: {ACCENT}; font-size: 12px; font-weight: bold;")
        self._content_layout.addWidget(info_lbl)

        band_labels = ["Banda 1 (Dígito)", "Banda 2 (Dígito)", "Banda 3 (Multiplicador)", "Banda 4 (Tolerancia)"]
        if bands_config == 5:
            band_labels = ["Banda 1 (Dígito)", "Banda 2 (Dígito)", "Banda 3 (Dígito)",
                           "Banda 4 (Multiplicador)", "Banda 5 (Tolerancia)"]
        elif bands_config == 6:
            band_labels = ["Banda 1 (Dígito)", "Banda 2 (Dígito)", "Banda 3 (Dígito)",
                           "Banda 4 (Multiplicador)", "Banda 5 (Tolerancia)", "Banda 6 (PPM/K)"]

        self._band_buttons = []
        self._band_selections = [None] * len(band_labels)

        # Available colors list (sorted)
        color_names = list(color_data.keys())

        for band_idx, band_name in enumerate(band_labels):
            band_frame = QFrame()
            band_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG};
                    border: 1px solid {BORDER};
                    border-radius: 4px;
                    padding: 4px;
                }}
            """)
            band_layout = QVBoxLayout(band_frame)
            band_layout.setContentsMargins(6, 4, 6, 4)
            band_layout.setSpacing(4)

            lbl = QLabel(band_name)
            lbl.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px; border: none;")
            band_layout.addWidget(lbl)

            colors_row = QHBoxLayout()
            colors_row.setSpacing(3)
            band_btns = []

            for color_name in color_names:
                cdata = color_data[color_name]
                hex_color = cdata.get('hex', '#808080')

                # Filter colors by band type
                is_last = (band_idx == len(band_labels) - 1)
                is_ppm = (bands_config == 6 and is_last)
                is_tolerance = (band_idx == len(band_labels) - (2 if bands_config == 6 else 1))
                is_multiplier = (band_idx == len(band_labels) - (3 if bands_config == 6 else 2))
                is_digit = not is_ppm and not is_tolerance and not is_multiplier

                if is_digit and cdata.get('value') is None:
                    continue
                if is_multiplier and cdata.get('multiplier') is None:
                    continue
                if is_tolerance and cdata.get('tolerance') is None:
                    continue
                if is_ppm and cdata.get('ppm') is None:
                    continue

                btn = QPushButton()
                btn.setFixedSize(22, 22)
                # Determine text color for contrast
                r_val = int(hex_color[1:3], 16)
                g_val = int(hex_color[3:5], 16)
                b_val = int(hex_color[5:7], 16)
                brightness = (r_val * 299 + g_val * 587 + b_val * 114) / 1000
                text_color = "#000000" if brightness > 128 else "#ffffff"

                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {hex_color};
                        border: 2px solid transparent;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid {ACCENT};
                    }}
                """)
                btn.setToolTip(color_name)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(partial(self._select_band_color, band_idx, color_name))
                colors_row.addWidget(btn)
                band_btns.append((color_name, btn))

            colors_row.addStretch()
            band_layout.addLayout(colors_row)
            self._band_buttons.append(band_btns)
            self._content_layout.addWidget(band_frame)

        # Result labels
        self._resistor_value_label = QLabel("Valor: —")
        self._resistor_value_label.setStyleSheet(f"""
            QLabel {{
                color: {SUCCESS};
                font-size: 16px;
                font-weight: bold;
                padding: 8px;
                background-color: {BG};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
        """)
        self._content_layout.addWidget(self._resistor_value_label)

        self._resistor_tolerance_label = QLabel("Tolerancia: —")
        self._resistor_tolerance_label.setStyleSheet(f"""
            QLabel {{
                color: {BLUE};
                font-size: 13px;
                padding: 4px 8px;
            }}
        """)
        self._content_layout.addWidget(self._resistor_tolerance_label)

        self._resistor_ppm_label = QLabel("Coef. Temp: —")
        self._resistor_ppm_label.setStyleSheet(f"""
            QLabel {{
                color: #fab387;
                font-size: 13px;
                padding: 0px 8px 4px 8px;
            }}
        """)
        if bands_config == 6:
            self._content_layout.addWidget(self._resistor_ppm_label)
        else:
            self._resistor_ppm_label.hide()

        # Copy button
        btn_row = QHBoxLayout()
        btn_copy = QPushButton(" Copiar")
        btn_copy.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy.setIconSize(QSize(16, 16))
        btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy.setToolTip("Copiar resultado")
        btn_copy.clicked.connect(self._copy_resistor_value)
        btn_row.addWidget(btn_copy)

        btn_copy_detail = QPushButton(" Copiar Detalle")
        btn_copy_detail.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy_detail.setIconSize(QSize(16, 16))
        btn_copy_detail.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy_detail.setToolTip("Copiar bandas seleccionadas y resultado")
        btn_copy_detail.clicked.connect(self._copy_resistor_detail)
        btn_row.addWidget(btn_copy_detail)

        btn_row.addStretch()
        self._content_layout.addLayout(btn_row)

    def _select_band_color(self, band_idx, color_name):
        self._band_selections[band_idx] = color_name
        # Highlight selected button
        for cn, btn in self._band_buttons[band_idx]:
            cdata = RESISTOR_COLORS.get(cn, {})
            hex_color = cdata.get('hex', '#808080')
            if cn == color_name:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {hex_color};
                        border: 2px solid {ACCENT};
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid {ACCENT};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {hex_color};
                        border: 2px solid transparent;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid {ACCENT};
                    }}
                """)
        self._calculate_resistor_value()

    def _calculate_resistor_value(self):
        bands_config = self._formula.get('bands', 4)
        selections = self._band_selections

        if any(s is None for s in selections):
            self._resistor_value_label.setText("Valor: — (seleccione todas las bandas)")
            self._resistor_tolerance_label.setText("Tolerancia: —")
            return

        color_data = RESISTOR_COLORS

        try:
            if bands_config == 4:
                d1 = color_data[selections[0]].get('value', 0)
                d2 = color_data[selections[1]].get('value', 0)
                mult = color_data[selections[2]].get('multiplier', 1)
                tol = color_data[selections[3]].get('tolerance', '±20%')
                ppm = None
                value = (d1 * 10 + d2) * mult
            else:
                d1 = color_data[selections[0]].get('value', 0)
                d2 = color_data[selections[1]].get('value', 0)
                d3 = color_data[selections[2]].get('value', 0)
                mult = color_data[selections[3]].get('multiplier', 1)
                tol = color_data[selections[4]].get('tolerance', '±20%')
                ppm = color_data[selections[5]].get('ppm', '') if bands_config == 6 else None
                value = (d1 * 100 + d2 * 10 + d3) * mult

            # Format value
            if value >= 1e6:
                display = f"{value / 1e6:.2f} MΩ"
            elif value >= 1e3:
                display = f"{value / 1e3:.2f} kΩ"
            else:
                display = f"{value:.2f} Ω"

            self._resistor_value_label.setText(f"Valor: {display}")
            self._resistor_tolerance_label.setText(f"Tolerancia: ±{tol}%")
            if bands_config == 6 and ppm is not None:
                self._resistor_ppm_label.setText(f"Coef. Temp: {ppm} PPM/K")
                self._last_resistor_text = f"{display} ±{tol}% {ppm}PPM/K"
            else:
                self._last_resistor_text = f"{display} ±{tol}%"
        except Exception as e:
            self._resistor_value_label.setText(f"Valor: Error ({str(e)[:30]})")
            self._resistor_tolerance_label.setText("Tolerancia: —")
            self._resistor_ppm_label.setText("Coef. Temp: —")

    def _copy_resistor_value(self):
        text = getattr(self, '_last_resistor_text', '')
        if text:
            QApplication.clipboard().setText(text)

    def _copy_resistor_detail(self):
        bands_config = self._formula.get('bands', 4)
        selections = self._band_selections
        band_labels = ["Banda 1 (Dígito)", "Banda 2 (Dígito)", "Banda 3 (Multiplicador)", "Banda 4 (Tolerancia)"]
        if bands_config == 5:
            band_labels = ["Banda 1 (Dígito)", "Banda 2 (Dígito)", "Banda 3 (Dígito)",
                           "Banda 4 (Multiplicador)", "Banda 5 (Tolerancia)"]
        elif bands_config == 6:
            band_labels = ["Banda 1 (Dígito)", "Banda 2 (Dígito)", "Banda 3 (Dígito)",
                           "Banda 4 (Multiplicador)", "Banda 5 (Tolerancia)", "Banda 6 (PPM/K)"]

        formula_name = self._formula.get('name', 'Código de Colores de Resistencia')
        lines = [f"[{formula_name}]", "Bandas seleccionadas:"]
        for label, sel in zip(band_labels, selections):
            lines.append(f"• {label}: {sel if sel else 'No seleccionada'}")

        res_text = getattr(self, '_last_resistor_text', '')
        if res_text:
            lines.append(f"Resultado:\n{res_text}")
        QApplication.clipboard().setText("\n".join(lines))


# =============================================================================
# CalculatorDialog — Main dialog
# =============================================================================
class CalculatorDialog(QDialog):
    """Calculadora flotante con tres modos: Básica, Científica, Electrónica."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Calculadora")
        self.resize(420, 580)
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setStyleSheet(GLOBAL_STYLE)

        # Calculator state
        self._current_value = "0"
        self._expression = ""
        self._pending_op = None
        self._pending_value = None
        self._just_evaluated = False
        self._history = []
        self._memory = 0.0
        self._angle_mode = "DEG"  # DEG, RAD, GRAD
        self._sci_expression = ""

        self._setup_ui()
        self._setup_keyboard_shortcuts()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Mode selector buttons
        mode_row = QHBoxLayout()
        mode_row.setSpacing(4)
        self._mode_buttons = []
        modes = [(" Básica", 0, "calculator.svg"), (" Científica", 1, "chart.svg"), (" Electrónica", 2, "lab.svg")]
        for name, idx, icon_file in modes:
            btn = QPushButton(name)
            btn.setIcon(QIcon(os.path.join(ICONS_DIR, icon_file)))
            btn.setIconSize(QSize(16, 16))
            btn.setCheckable(True)
            btn.setChecked(idx == 0)
            btn.setStyleSheet(self._mode_btn_style())
            btn.clicked.connect(partial(self._set_mode, idx))
            mode_row.addWidget(btn)
            self._mode_buttons.append(btn)
        main_layout.addLayout(mode_row)

        # Stacked widget
        self._stack = QStackedWidget()
        self._stack.addWidget(self._create_basic_page())
        self._stack.addWidget(self._create_scientific_page())
        self._stack.addWidget(self._create_electronics_page())
        main_layout.addWidget(self._stack)

    def _mode_btn_style(self):
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
            }}
            QPushButton:checked {{
                background-color: {BORDER};
                color: {ACCENT};
                border-color: {ACCENT};
            }}
        """

    def _set_mode(self, index):
        self._stack.setCurrentIndex(index)
        for i, btn in enumerate(self._mode_buttons):
            btn.setChecked(i == index)

    # =========================================================================
    # BASIC CALCULATOR PAGE
    # =========================================================================
    def _create_basic_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        # Display
        display_frame = QFrame()
        display_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        d_layout = QVBoxLayout(display_frame)
        d_layout.setContentsMargins(10, 6, 10, 6)
        d_layout.setSpacing(2)

        self._expr_label = QLabel("")
        self._expr_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._expr_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 12px; border: none;")
        d_layout.addWidget(self._expr_label)

        self._display_label = QLabel("0")
        self._display_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._display_label.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self._display_label.setStyleSheet(f"color: {TEXT}; border: none;")
        d_layout.addWidget(self._display_label)
        layout.addWidget(display_frame)

        # Button grid
        grid = QGridLayout()
        grid.setSpacing(4)

        buttons = [
            ("C", 0, 0, "clear"), ("CE", 0, 1, "clear_entry"), ("%", 0, 2, "percent"), ("÷", 0, 3, "op"),
            ("7", 1, 0, "num"), ("8", 1, 1, "num"), ("9", 1, 2, "num"), ("×", 1, 3, "op"),
            ("4", 2, 0, "num"), ("5", 2, 1, "num"), ("6", 2, 2, "num"), ("−", 2, 3, "op"),
            ("1", 3, 0, "num"), ("2", 3, 1, "num"), ("3", 3, 2, "num"), ("+", 3, 3, "op"),
            ("±", 4, 0, "sign"), ("0", 4, 1, "num"), (".", 4, 2, "decimal"), ("=", 4, 3, "equals"),
        ]

        for text, row, col, btn_type in buttons:
            btn = QPushButton(text)
            btn.setFixedHeight(48)
            btn.setFont(QFont("Segoe UI", 14))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if btn_type == "num" or btn_type == "decimal":
                style = self._num_btn_style()
            elif btn_type == "op":
                style = self._op_btn_style()
            elif btn_type == "equals":
                style = self._eq_btn_style()
            elif btn_type in ("clear", "clear_entry"):
                style = self._clear_btn_style()
            elif btn_type == "percent":
                style = self._op_btn_style()
            elif btn_type == "sign":
                style = self._num_btn_style()
            else:
                style = self._num_btn_style()

            btn.setStyleSheet(style)
            btn.clicked.connect(partial(self._on_basic_btn, text, btn_type))
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)

        # Copy button
        copy_row = QHBoxLayout()
        btn_copy = QPushButton(" Copiar")
        btn_copy.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy.setIconSize(QSize(16, 16))
        btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy.clicked.connect(self._copy_display)
        copy_row.addWidget(btn_copy)
        copy_row.addStretch()
        layout.addLayout(copy_row)

        # History section
        self._history_btn = QPushButton(" Historial ▶")
        self._history_btn.setIcon(QIcon(os.path.join(ICONS_DIR, "history.svg")))
        self._history_btn.setIconSize(QSize(14, 14))
        self._history_btn.setCheckable(True)
        self._history_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {SUBTEXT};
                border: none;
                font-size: 12px;
                text-align: left;
                padding: 4px;
            }}
            QPushButton:hover {{
                color: {ACCENT};
            }}
        """)
        self._history_btn.clicked.connect(self._toggle_history)
        layout.addWidget(self._history_btn)

        self._history_list = QListWidget()
        self._history_list.setMaximumHeight(120)
        self._history_list.setVisible(False)
        self._history_list.itemClicked.connect(self._on_history_click)
        layout.addWidget(self._history_list)

        layout.addStretch()
        return page

    def _num_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {BORDER};
                color: {TEXT};
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {HOVER};
            }}
            QPushButton:pressed {{
                background-color: {SURFACE};
            }}
        """

    def _op_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {BORDER};
                color: {ACCENT};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {HOVER};
            }}
            QPushButton:pressed {{
                background-color: {SURFACE};
            }}
        """

    def _eq_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {SUCCESS};
                color: {BG};
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #b5eeb3;
            }}
            QPushButton:pressed {{
                background-color: #8dd98b;
            }}
        """

    def _clear_btn_style(self):
        return f"""
            QPushButton {{
                background-color: {BORDER};
                color: {ERROR};
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {HOVER};
            }}
            QPushButton:pressed {{
                background-color: {SURFACE};
            }}
        """

    # ---- Basic calculator logic ----
    def _on_basic_btn(self, text, btn_type):
        if btn_type == "num":
            self._input_digit(text)
        elif btn_type == "decimal":
            self._input_decimal()
        elif btn_type == "op":
            self._input_operator(text)
        elif btn_type == "equals":
            self._evaluate()
        elif btn_type == "clear":
            self._clear_all()
        elif btn_type == "clear_entry":
            self._clear_entry()
        elif btn_type == "percent":
            self._percent()
        elif btn_type == "sign":
            self._toggle_sign()

    def _input_digit(self, digit):
        if self._just_evaluated:
            self._current_value = digit
            self._expression = ""
            self._just_evaluated = False
        elif self._current_value == "0":
            self._current_value = digit
        else:
            self._current_value += digit
        self._update_display()

    def _input_decimal(self):
        if self._just_evaluated:
            self._current_value = "0."
            self._expression = ""
            self._just_evaluated = False
        elif "." not in self._current_value:
            self._current_value += "."
        self._update_display()

    def _input_operator(self, op):
        op_map = {"÷": "/", "×": "*", "−": "-", "+": "+"}
        actual_op = op_map.get(op, op)

        if self._pending_op and not self._just_evaluated:
            self._evaluate(chain=True)

        self._pending_value = float(self._current_value)
        self._pending_op = actual_op
        self._expression = f"{self._format_number(self._pending_value)} {op} "
        self._just_evaluated = False
        self._current_value = "0"
        self._update_display()

    def _evaluate(self, chain=False):
        if self._pending_op is None or self._pending_value is None:
            return

        current = float(self._current_value)
        op = self._pending_op
        prev = self._pending_value

        op_symbols = {"/": "÷", "*": "×", "-": "−", "+": "+"}
        display_op = op_symbols.get(op, op)

        try:
            if op == "+":
                result = prev + current
            elif op == "-":
                result = prev - current
            elif op == "*":
                result = prev * current
            elif op == "/":
                if current == 0:
                    self._display_label.setText("Error")
                    self._expr_label.setText(f"{self._format_number(prev)} {display_op} 0")
                    hist_entry = f"{self._format_number(prev)} {display_op} 0 = Error (÷0)"
                    self._add_history(hist_entry)
                    self._pending_op = None
                    self._pending_value = None
                    self._current_value = "0"
                    self._just_evaluated = True
                    return
                result = prev / current
            else:
                result = current

            expr_text = f"{self._format_number(prev)} {display_op} {self._format_number(current)} ="
            result_text = self._format_number(result)

            self._expr_label.setText(expr_text)
            self._display_label.setText(result_text)

            hist_entry = f"{self._format_number(prev)} {display_op} {self._format_number(current)} = {result_text}"
            self._add_history(hist_entry)

            self._current_value = str(result)
            if not chain:
                self._pending_op = None
                self._pending_value = None
                self._just_evaluated = True
            else:
                self._pending_value = result
        except Exception:
            self._display_label.setText("Error")
            self._pending_op = None
            self._pending_value = None
            self._just_evaluated = True

    def _clear_all(self):
        self._current_value = "0"
        self._expression = ""
        self._pending_op = None
        self._pending_value = None
        self._just_evaluated = False
        self._expr_label.setText("")
        self._display_label.setText("0")

    def _clear_entry(self):
        self._current_value = "0"
        self._just_evaluated = False
        self._update_display()

    def _percent(self):
        val = float(self._current_value)
        if self._pending_value is not None:
            result = self._pending_value * (val / 100.0)
        else:
            result = val / 100.0
        self._current_value = str(result)
        self._update_display()

    def _toggle_sign(self):
        if self._current_value.startswith("-"):
            self._current_value = self._current_value[1:]
        elif self._current_value != "0":
            self._current_value = "-" + self._current_value
        self._update_display()

    def _update_display(self):
        self._expr_label.setText(self._expression)
        self._display_label.setText(self._format_number(float(self._current_value)))

    def _format_number(self, value):
        if value == int(value) and abs(value) < 1e15:
            return str(int(value))
        elif abs(value) >= 1e15 or (abs(value) < 0.0001 and value != 0):
            return f"{value:.6e}"
        else:
            formatted = f"{value:.10f}".rstrip('0').rstrip('.')
            return formatted

    def _copy_display(self):
        text = self._display_label.text()
        QApplication.clipboard().setText(text)

    def _toggle_history(self):
        visible = not self._history_list.isVisible()
        self._history_list.setVisible(visible)
        self._history_btn.setText("Historial ▼" if visible else "Historial ▶")

    def _add_history(self, entry):
        self._history.insert(0, entry)
        if len(self._history) > 20:
            self._history = self._history[:20]
        self._history_list.clear()
        for h in self._history:
            self._history_list.addItem(QListWidgetItem(h))

    def _on_history_click(self, item):
        QApplication.clipboard().setText(item.text())

    # =========================================================================
    # SCIENTIFIC CALCULATOR PAGE
    # =========================================================================
    def _create_scientific_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(4)

        # Display
        display_frame = QFrame()
        display_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        d_layout = QVBoxLayout(display_frame)
        d_layout.setContentsMargins(10, 4, 10, 4)
        d_layout.setSpacing(2)

        self._sci_expr_label = QLabel("")
        self._sci_expr_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._sci_expr_label.setWordWrap(True)
        self._sci_expr_label.setStyleSheet(f"color: {SUBTEXT}; font-size: 11px; border: none;")
        d_layout.addWidget(self._sci_expr_label)

        self._sci_display = QLabel("0")
        self._sci_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._sci_display.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self._sci_display.setStyleSheet(f"color: {TEXT}; border: none;")
        d_layout.addWidget(self._sci_display)
        layout.addWidget(display_frame)

        # Scientific function rows
        sci_grid = QGridLayout()
        sci_grid.setSpacing(3)

        # Row A: trig + parens + angle toggle
        row_a = [
            ("sin", "sin("), ("cos", "cos("), ("tan", "tan("),
            ("(", "("), (")", ")"),
        ]
        for col, (text, insert) in enumerate(row_a):
            btn = self._make_sci_btn(text)
            btn.clicked.connect(partial(self._sci_insert, insert))
            sci_grid.addWidget(btn, 0, col)
        self._angle_btn = self._make_sci_btn("DEG")
        self._angle_btn.setCheckable(False)
        self._angle_btn.clicked.connect(self._toggle_angle)
        self._angle_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {PURPLE};
                border: 1px solid {BORDER};
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
            }}
        """)
        sci_grid.addWidget(self._angle_btn, 0, 5)

        # Row B: inverse trig + constants
        row_b = [
            ("asin", "asin("), ("acos", "acos("), ("atan", "atan("),
            ("π", "pi"), ("e", "e"), ("φ", "phi"),
        ]
        for col, (text, insert) in enumerate(row_b):
            btn = self._make_sci_btn(text)
            btn.clicked.connect(partial(self._sci_insert, insert))
            sci_grid.addWidget(btn, 1, col)

        # Row C: powers and roots (replaced nroot with comma for functions)
        row_c = [
            ("x²", "**2"), ("x³", "**3"), ("xⁿ", "**("),
            ("√", "sqrt("), ("³√", "cbrt("), (",", ","),
        ]
        for col, (text, insert) in enumerate(row_c):
            btn = self._make_sci_btn(text)
            btn.clicked.connect(partial(self._sci_insert, insert))
            sci_grid.addWidget(btn, 2, col)

        # Row D: logarithms, factorial, abs, reciprocal
        row_d = [
            ("ln", "ln("), ("log₁₀", "log10("), ("log₂", "log2("),
            ("n!", "factorial("), ("|x|", "abs("), ("1/x", "1/("),
        ]
        for col, (text, insert) in enumerate(row_d):
            btn = self._make_sci_btn(text)
            btn.clicked.connect(partial(self._sci_insert, insert))
            sci_grid.addWidget(btn, 3, col)

        # Row E: memory + EXP + mod
        row_e_data = [
            ("MC", "mc"), ("MR", "mr"), ("M+", "m+"),
            ("M-", "m-"), ("EXP", "exp"), ("mod", "mod"),
        ]
        for col, (text, action) in enumerate(row_e_data):
            btn = self._make_sci_btn(text)
            btn.clicked.connect(partial(self._sci_memory_action, action))
            sci_grid.addWidget(btn, 4, col)

        layout.addLayout(sci_grid)

        # Number pad for scientific
        num_grid = QGridLayout()
        num_grid.setSpacing(3)
        sci_nums = [
            ("C", 0, 0, "clear"), ("CE", 0, 1, "ce"), ("%", 0, 2, "percent"), ("÷", 0, 3, "op"),
            ("7", 1, 0, "num"), ("8", 1, 1, "num"), ("9", 1, 2, "num"), ("×", 1, 3, "op"),
            ("4", 2, 0, "num"), ("5", 2, 1, "num"), ("6", 2, 2, "num"), ("−", 2, 3, "op"),
            ("1", 3, 0, "num"), ("2", 3, 1, "num"), ("3", 3, 2, "num"), ("+", 3, 3, "op"),
            ("±", 4, 0, "sign"), ("0", 4, 1, "num"), (".", 4, 2, "decimal"), ("=", 4, 3, "equals"),
        ]
        for text, row, col, btn_type in sci_nums:
            btn = QPushButton(text)
            btn.setFixedHeight(38)
            btn.setFont(QFont("Segoe UI", 12))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            if btn_type == "num" or btn_type == "decimal":
                style = self._num_btn_style()
            elif btn_type == "op":
                style = self._op_btn_style()
            elif btn_type == "equals":
                style = self._eq_btn_style()
            elif btn_type in ("clear", "ce"):
                style = self._clear_btn_style()
            elif btn_type == "percent":
                style = self._op_btn_style()
            elif btn_type == "sign":
                style = self._num_btn_style()
            else:
                style = self._num_btn_style()

            btn.setStyleSheet(style)
            btn.clicked.connect(partial(self._on_sci_num_btn, text, btn_type))
            num_grid.addWidget(btn, row, col)

        layout.addLayout(num_grid)

        # Copy + history
        copy_row = QHBoxLayout()
        btn_copy = QPushButton(" Copiar")
        btn_copy.setIcon(QIcon(os.path.join(ICONS_DIR, "copy.svg")))
        btn_copy.setIconSize(QSize(16, 16))
        btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {TEXT};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
        """)
        btn_copy.clicked.connect(self._copy_sci_display)
        copy_row.addWidget(btn_copy)
        copy_row.addStretch()
        layout.addLayout(copy_row)

        layout.addStretch()
        return page

    def _make_sci_btn(self, text):
        btn = QPushButton(text)
        btn.setFixedHeight(32)
        btn.setFont(QFont("Segoe UI", 10))
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {SURFACE};
                color: {BLUE};
                border: 1px solid {BORDER};
                border-radius: 4px;
                font-size: 10px;
                padding: 2px 4px;
            }}
            QPushButton:hover {{
                background-color: {BORDER};
                color: {ACCENT};
            }}
            QPushButton:pressed {{
                background-color: {BG};
            }}
        """)
        return btn

    def _sci_insert(self, text):
        if self._just_evaluated and text not in ("**2", "**3", "**("):
            self._sci_expression = ""
            self._just_evaluated = False
        self._sci_expression += text
        self._sci_expr_label.setText(self._sci_expression)

    def _toggle_angle(self):
        modes = ["DEG", "RAD", "GRAD"]
        idx = modes.index(self._angle_mode)
        self._angle_mode = modes[(idx + 1) % 3]
        self._angle_btn.setText(self._angle_mode)

    def _sci_memory_action(self, action):
        if action == "mc":
            self._memory = 0.0
        elif action == "mr":
            self._sci_expression += str(self._memory)
            self._sci_expr_label.setText(self._sci_expression)
        elif action == "m+":
            try:
                val = float(self._sci_display.text())
                self._memory += val
            except ValueError:
                pass
        elif action == "m-":
            try:
                val = float(self._sci_display.text())
                self._memory -= val
            except ValueError:
                pass
        elif action == "exp":
            self._sci_expression += "*10**("
            self._sci_expr_label.setText(self._sci_expression)
        elif action == "mod":
            self._sci_expression += "%"
            self._sci_expr_label.setText(self._sci_expression)

    def _on_sci_num_btn(self, text, btn_type):
        if btn_type == "num":
            if self._just_evaluated:
                self._sci_expression = ""
                self._just_evaluated = False
            self._sci_expression += text
            self._sci_expr_label.setText(self._sci_expression)
        elif btn_type == "decimal":
            self._sci_expression += "."
            self._sci_expr_label.setText(self._sci_expression)
        elif btn_type == "op":
            op_map = {"÷": "/", "×": "*", "−": "-", "+": "+"}
            self._sci_expression += op_map.get(text, text)
            self._sci_expr_label.setText(self._sci_expression)
            self._just_evaluated = False
        elif btn_type == "equals":
            self._evaluate_sci()
        elif btn_type == "clear":
            self._sci_expression = ""
            self._sci_expr_label.setText("")
            self._sci_display.setText("0")
            self._just_evaluated = False
        elif btn_type == "ce":
            if self._sci_expression:
                self._sci_expression = self._sci_expression[:-1]
                self._sci_expr_label.setText(self._sci_expression)
        elif btn_type == "percent":
            self._sci_expression += "/100"
            self._sci_expr_label.setText(self._sci_expression)
        elif btn_type == "sign":
            self._sci_expression = "(-" + self._sci_expression + ")"
            self._sci_expr_label.setText(self._sci_expression)

    def _evaluate_sci(self):
        expr = self._sci_expression.strip()
        if not expr:
            return

        # Build safe namespace
        phi_val = (1 + math.sqrt(5)) / 2.0

        # Determine angle conversion
        if self._angle_mode == "DEG":
            angle_fn = math.radians
            inv_angle_fn = math.degrees
        elif self._angle_mode == "GRAD":
            angle_fn = lambda x: math.radians(x * 0.9)
            inv_angle_fn = lambda x: math.degrees(x) / 0.9
        else:  # RAD
            angle_fn = lambda x: x
            inv_angle_fn = lambda x: x

        safe_dict = {
            'sin': lambda x: math.sin(angle_fn(x)),
            'cos': lambda x: math.cos(angle_fn(x)),
            'tan': lambda x: math.tan(angle_fn(x)),
            'asin': lambda x: inv_angle_fn(math.asin(x)),
            'acos': lambda x: inv_angle_fn(math.acos(x)),
            'atan': lambda x: inv_angle_fn(math.atan(x)),
            'sqrt': math.sqrt,
            'cbrt': lambda x: math.copysign(abs(x) ** (1.0 / 3.0), x),
            'nroot': lambda x, n: math.copysign(abs(x) ** (1.0 / n), x),
            'ln': math.log,
            'log10': math.log10,
            'log2': math.log2,
            'factorial': lambda x: math.factorial(int(x)),
            'abs': abs,
            'EXP': lambda x: 10 ** x,
            'pi': math.pi,
            'e': math.e,
            'phi': phi_val,
            'pow': pow,
        }

        try:
            result = eval(expr, {"__builtins__": {}}, safe_dict)
            result_str = self._format_number(float(result))
            self._sci_display.setText(result_str)
            self._sci_expr_label.setText(f"{expr} =")

            hist_entry = f"{expr} = {result_str}"
            self._add_history(hist_entry)

            self._sci_expression = result_str
            self._just_evaluated = True
        except ZeroDivisionError:
            self._sci_display.setText("∞")
            self._sci_expr_label.setText(f"{expr} =")
            self._sci_expression = ""
            self._just_evaluated = True
        except Exception as e:
            self._sci_display.setText("Error")
            self._sci_expr_label.setText(str(e)[:50])
            self._sci_expression = ""
            self._just_evaluated = True

    def _copy_sci_display(self):
        text = self._sci_display.text()
        QApplication.clipboard().setText(text)

    # =========================================================================
    # ELECTRONICS PAGE
    # =========================================================================
    def _create_electronics_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(0)

        tab_widget = QTabWidget()
        tab_widget.addTab(self._create_formula_tab(ANALOG_FORMULAS), "Analógico")
        tab_widget.addTab(self._create_formula_tab(DIGITAL_FORMULAS), "Digital")
        tab_widget.addTab(self._create_formula_tab(OTHER_FORMULAS), "Otras")
        layout.addWidget(tab_widget)

        return page

    def _create_formula_tab(self, formulas_dict):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet(f"background-color: {BG};")
        v_layout = QVBoxLayout(container)
        v_layout.setContentsMargins(6, 6, 6, 6)
        v_layout.setSpacing(6)

        for key, formula_data in formulas_dict.items():
            panel = FormulaPanel(formula_data)
            v_layout.addWidget(panel)

        v_layout.addStretch()
        scroll.setWidget(container)
        return scroll

    # =========================================================================
    # KEYBOARD SUPPORT
    # =========================================================================
    def _setup_keyboard_shortcuts(self):
        pass  # We handle keys via keyPressEvent

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()
        mode = self._stack.currentIndex()

        # Both basic (0) and scientific (1)
        if mode == 0:
            self._handle_basic_key(key, text)
        elif mode == 1:
            self._handle_sci_key(key, text)

        super().keyPressEvent(event)

    def _handle_basic_key(self, key, text):
        if text in "0123456789":
            self._input_digit(text)
        elif text == ".":
            self._input_decimal()
        elif text == "+" or key == Qt.Key.Key_Plus:
            self._input_operator("+")
        elif text == "-" or key == Qt.Key.Key_Minus:
            self._input_operator("−")
        elif text == "*" or key == Qt.Key.Key_Asterisk:
            self._input_operator("×")
        elif text == "/" or key == Qt.Key.Key_Slash:
            self._input_operator("÷")
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Equal):
            self._evaluate()
        elif key == Qt.Key.Key_Escape:
            self._clear_all()
        elif key == Qt.Key.Key_Backspace:
            if self._current_value and len(self._current_value) > 1:
                self._current_value = self._current_value[:-1]
            else:
                self._current_value = "0"
            self._update_display()
        elif key == Qt.Key.Key_Percent:
            self._percent()
        elif key == Qt.Key.Key_Delete:
            self._clear_entry()

    def _handle_sci_key(self, key, text):
        if text in "0123456789":
            self._on_sci_num_btn(text, "num")
        elif text == ".":
            self._on_sci_num_btn(".", "decimal")
        elif text == "+":
            self._on_sci_num_btn("+", "op")
        elif text == "-":
            self._on_sci_num_btn("−", "op")
        elif text == "*":
            self._on_sci_num_btn("×", "op")
        elif text == "/":
            self._on_sci_num_btn("÷", "op")
        elif text == "(":
            self._sci_insert("(")
        elif text == ")":
            self._sci_insert(")")
        elif text == ",":
            self._sci_insert(",")
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Equal):
            self._evaluate_sci()
        elif key == Qt.Key.Key_Escape:
            self._on_sci_num_btn("C", "clear")
        elif key == Qt.Key.Key_Backspace:
            self._on_sci_num_btn("CE", "ce")
