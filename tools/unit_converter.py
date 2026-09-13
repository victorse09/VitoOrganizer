# =============================================================================
# Vito Organizer - Unit Converter Tool
# Conversor de unidades flotante con pestañas de conversión física,
# tabla AWG y conversor numérico de bases.
# =============================================================================

import math
from functools import partial
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QWidget, QDoubleSpinBox, QComboBox, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QApplication,
    QSpinBox, QAbstractItemView,
)

# =============================================================================
# Catppuccin Mocha stylesheet
# =============================================================================
_MOCHA_STYLE = """
QDialog {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}
QTabWidget::pane {
    border: 1px solid #45475a;
    border-radius: 6px;
    background-color: #1e1e2e;
    top: -1px;
}
QTabBar::tab {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-bottom: none;
    padding: 5px 10px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 12px;
}
QTabBar::tab:selected {
    background-color: #45475a;
    color: #f9e2af;
    font-weight: bold;
}
QTabBar::tab:hover:!selected {
    background-color: #3b3b52;
}
QDoubleSpinBox, QSpinBox, QLineEdit, QComboBox {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 13px;
    selection-background-color: #f9e2af;
    selection-color: #1e1e2e;
}
QDoubleSpinBox:focus, QSpinBox:focus, QLineEdit:focus, QComboBox:focus {
    border: 1px solid #f9e2af;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #cdd6f4;
    margin-right: 5px;
}
QComboBox QAbstractItemView {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    selection-background-color: #45475a;
    selection-color: #f9e2af;
}
QPushButton {
    background-color: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #45475a;
    color: #f9e2af;
}
QPushButton:pressed {
    background-color: #585b70;
}
QTableWidget {
    background-color: #1e1e2e;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: 6px;
    gridline-color: #45475a;
    font-size: 12px;
    selection-background-color: #45475a;
    selection-color: #f9e2af;
}
QTableWidget::item {
    padding: 3px 6px;
}
QHeaderView::section {
    background-color: #313244;
    color: #f9e2af;
    border: 1px solid #45475a;
    padding: 4px;
    font-weight: bold;
    font-size: 12px;
}
QLabel {
    color: #cdd6f4;
}
QScrollBar:vertical {
    background: #1e1e2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #45475a;
    border-radius: 5px;
    min-height: 20px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #1e1e2e;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #45475a;
    border-radius: 5px;
    min-width: 20px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""

# =============================================================================
# Conversion data – factors relative to base unit
# Temperature is handled separately with direct formulas.
# =============================================================================

_LENGTH_UNITS = {
    "mm":             0.001,
    "cm":             0.01,
    "m":              1.0,
    "km":             1000.0,
    "pulgada (in)":   0.0254,
    "pie (ft)":       0.3048,
    "yarda (yd)":     0.9144,
    "milla (mi)":     1609.344,
    "mil (thou)":     0.0000254,
    "micra (µm)":     1e-6,
}

_MASS_UNITS = {
    "mg":                 0.000001,
    "g":                  0.001,
    "kg":                 1.0,
    "tonelada métrica":   1000.0,
    "onza (oz)":          0.028349523125,
    "libra (lb)":         0.45359237,
}

_AREA_UNITS = {
    "mm²":           1e-6,
    "cm²":           1e-4,
    "m²":            1.0,
    "km²":           1e6,
    "hectárea":      1e4,
    "acre":          4046.8564224,
    "pie²":          0.09290304,
    "pulgada²":      0.00064516,
}

_VOLUME_UNITS = {
    "mL":               1e-6,
    "L":                 0.001,
    "m³":                1.0,
    "galón US":          0.003785411784,
    "galón UK":          0.00454609,
    "onza fluida US":    2.9573529563e-5,
    "pie³":              0.028316846592,
    "pulgada³":          1.6387064e-5,
}

_PRESSURE_UNITS = {
    "Pa":      1.0,
    "kPa":     1000.0,
    "MPa":     1e6,
    "bar":     1e5,
    "atm":     101325.0,
    "psi":     6894.757293168,
    "mmHg":    133.322387415,
    "Torr":    133.322368421,
}

_SPEED_UNITS = {
    "m/s":     1.0,
    "km/h":    1.0 / 3.6,
    "mph":     0.44704,
    "nudos":   0.514444444,
    "ft/s":    0.3048,
}

_ENERGY_UNITS = {
    "J":       1.0,
    "kJ":      1000.0,
    "cal":     4.184,
    "kcal":    4184.0,
    "kWh":     3600000.0,
    "BTU":     1055.05585262,
    "eV":      1.602176634e-19,
}

_POWER_UNITS = {
    "W":       1.0,
    "kW":      1000.0,
    "HP":      745.7,
    "BTU/h":   0.29307107017,
    "cal/s":   4.184,
}

_FREQUENCY_UNITS = {
    "Hz":    1.0,
    "kHz":   1e3,
    "MHz":   1e6,
    "GHz":   1e9,
    "rpm":   1.0 / 60.0,
}


# =============================================================================
# Temperature helpers (direct formulas, no factors)
# =============================================================================

def _temp_to_celsius(value, unit):
    """Convert *value* in *unit* to Celsius."""
    if unit == "°C":
        return value
    if unit == "°F":
        return (value - 32.0) * 5.0 / 9.0
    if unit == "K":
        return value - 273.15
    if unit == "°R":
        return (value - 491.67) * 5.0 / 9.0
    return value


def _celsius_to_unit(celsius, unit):
    """Convert Celsius to *unit*."""
    if unit == "°C":
        return celsius
    if unit == "°F":
        return celsius * 9.0 / 5.0 + 32.0
    if unit == "K":
        return celsius + 273.15
    if unit == "°R":
        return (celsius + 273.15) * 9.0 / 5.0
    return celsius


# =============================================================================
# AWG data helpers
# =============================================================================

_AWG_LABELS = (
    ["0000 (4/0)", "000 (3/0)", "00 (2/0)", "0 (1/0)"]
    + [str(n) for n in range(1, 41)]
)
_AWG_NUMBERS = list(range(-3, 41))  # -3=4/0 … 0=1/0 … 40

_COPPER_RESISTIVITY = 1.724e-8  # Ω·m

# Recommended max current (A) for chassis wiring – standard reference table
_AWG_AMPACITY = {
    -3: 230, -2: 200, -1: 175, 0: 150,
    1: 130, 2: 115, 3: 100, 4: 85,
    5: 75, 6: 65, 7: 55, 8: 50,
    9: 40, 10: 35, 11: 30, 12: 25,
    13: 20, 14: 17, 15: 15, 16: 13,
    17: 11, 18: 10, 19: 8, 20: 7,
    21: 5, 22: 5, 23: 4, 24: 3.5,
    25: 3, 26: 2.5, 27: 2, 28: 1.5,
    29: 1.2, 30: 1.0, 31: 0.8, 32: 0.7,
    33: 0.5, 34: 0.4, 35: 0.3, 36: 0.25,
    37: 0.2, 38: 0.15, 39: 0.12, 40: 0.1,
}


def _awg_diameter_mm(n):
    """Diameter in mm for AWG number *n* (use -3 for 4/0, etc.)."""
    return 0.127 * 92.0 ** ((36.0 - n) / 39.0)


def _awg_section_mm2(n):
    d = _awg_diameter_mm(n)
    return math.pi / 4.0 * d * d


def _awg_resistance_ohm_per_km(n):
    area_m2 = _awg_section_mm2(n) * 1e-6  # mm² → m²
    # R = ρ·L / A  with L = 1000 m
    return _COPPER_RESISTIVITY * 1000.0 / area_m2


# =============================================================================
# Main dialog
# =============================================================================

class UnitConverterDialog(QDialog):
    """Floating unit‑converter tool with physical, AWG and numeric tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversor de Unidades")
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(520, 600)
        self.setStyleSheet(_MOCHA_STYLE)
        self._setup_ui()

    # --------------------------------------------------------------------- #
    # UI setup
    # --------------------------------------------------------------------- #
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # 10 physical tabs ------------------------------------------------
        self._create_conversion_tab("Longitud", _LENGTH_UNITS)
        self._create_conversion_tab("Masa / Peso", _MASS_UNITS)
        self._create_conversion_tab("Área", _AREA_UNITS)
        self._create_conversion_tab("Volumen", _VOLUME_UNITS)
        self._create_temperature_tab()
        self._create_conversion_tab("Presión", _PRESSURE_UNITS)
        self._create_conversion_tab("Velocidad", _SPEED_UNITS)
        self._create_conversion_tab("Energía", _ENERGY_UNITS)
        self._create_conversion_tab("Potencia", _POWER_UNITS)
        self._create_conversion_tab("Frecuencia", _FREQUENCY_UNITS)

        # Special tabs ----------------------------------------------------
        self._create_awg_tab()
        self._create_numeric_tab()

    # --------------------------------------------------------------------- #
    # Helper: generic factor‑based conversion tab
    # --------------------------------------------------------------------- #
    def _create_conversion_tab(self, category_name, units_dict):
        """Build a complete conversion tab for *units_dict* (name → factor)."""
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        unit_names = list(units_dict.keys())

        # --- Top row: input + source combo ---
        row1 = QHBoxLayout()
        lbl_in = QLabel("Valor:")
        lbl_in.setFixedWidth(40)
        row1.addWidget(lbl_in)

        spin = QDoubleSpinBox()
        spin.setDecimals(10)
        spin.setRange(-1e15, 1e15)
        spin.setValue(1.0)
        spin.setMinimumWidth(160)
        row1.addWidget(spin, 1)

        combo_src = QComboBox()
        combo_src.addItems(unit_names)
        combo_src.setMinimumWidth(120)
        row1.addWidget(combo_src)
        vbox.addLayout(row1)

        # --- Swap button ---
        row_swap = QHBoxLayout()
        row_swap.addStretch()
        btn_swap = QPushButton("⇅")
        btn_swap.setFixedSize(36, 28)
        btn_swap.setToolTip("Intercambiar unidades")
        row_swap.addWidget(btn_swap)
        row_swap.addStretch()
        vbox.addLayout(row_swap)

        # --- Output row ---
        row2 = QHBoxLayout()
        lbl_out = QLabel("Result:")
        lbl_out.setFixedWidth(40)
        row2.addWidget(lbl_out)

        output = QLineEdit()
        output.setReadOnly(True)
        output.setMinimumWidth(160)
        row2.addWidget(output, 1)

        combo_dst = QComboBox()
        combo_dst.addItems(unit_names)
        if len(unit_names) > 1:
            combo_dst.setCurrentIndex(1)
        combo_dst.setMinimumWidth(120)
        row2.addWidget(combo_dst)

        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setFixedWidth(90)
        row2.addWidget(btn_copy)
        vbox.addLayout(row2)

        # --- Reference table ---
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Unidad", "Valor"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setRowCount(len(unit_names))
        for i, name in enumerate(unit_names):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(""))
        vbox.addWidget(table, 1)

        self._tabs.addTab(widget, category_name)

        # --- Conversion logic ---
        def _convert(*_args):
            val = spin.value()
            src = combo_src.currentText()
            dst = combo_dst.currentText()
            src_factor = units_dict[src]
            dst_factor = units_dict[dst]
            result = val * src_factor / dst_factor
            output.setText(self._format_number(result))
            # Update reference table
            for i, name in enumerate(unit_names):
                factor = units_dict[name]
                converted = val * src_factor / factor
                table.item(i, 1).setText(self._format_number(converted))

        spin.valueChanged.connect(_convert)
        combo_src.currentIndexChanged.connect(_convert)
        combo_dst.currentIndexChanged.connect(_convert)

        def _swap():
            si = combo_src.currentIndex()
            di = combo_dst.currentIndex()
            combo_src.setCurrentIndex(di)
            combo_dst.setCurrentIndex(si)

        btn_swap.clicked.connect(_swap)

        def _copy():
            txt = f"{spin.value()} {combo_src.currentText()} = {output.text()} {combo_dst.currentText()}"
            QApplication.clipboard().setText(txt)

        btn_copy.clicked.connect(_copy)

        # Initial conversion
        _convert()

    # --------------------------------------------------------------------- #
    # Temperature tab (direct formulas)
    # --------------------------------------------------------------------- #
    def _create_temperature_tab(self):
        temp_units = ["°C", "°F", "K", "°R"]

        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        # --- Input row ---
        row1 = QHBoxLayout()
        lbl_in = QLabel("Valor:")
        lbl_in.setFixedWidth(40)
        row1.addWidget(lbl_in)

        spin = QDoubleSpinBox()
        spin.setDecimals(10)
        spin.setRange(-1e15, 1e15)
        spin.setValue(0.0)
        spin.setMinimumWidth(160)
        row1.addWidget(spin, 1)

        combo_src = QComboBox()
        combo_src.addItems(temp_units)
        combo_src.setMinimumWidth(120)
        row1.addWidget(combo_src)
        vbox.addLayout(row1)

        # --- Swap ---
        row_swap = QHBoxLayout()
        row_swap.addStretch()
        btn_swap = QPushButton("⇅")
        btn_swap.setFixedSize(36, 28)
        btn_swap.setToolTip("Intercambiar unidades")
        row_swap.addWidget(btn_swap)
        row_swap.addStretch()
        vbox.addLayout(row_swap)

        # --- Output row ---
        row2 = QHBoxLayout()
        lbl_out = QLabel("Result:")
        lbl_out.setFixedWidth(40)
        row2.addWidget(lbl_out)

        output = QLineEdit()
        output.setReadOnly(True)
        output.setMinimumWidth(160)
        row2.addWidget(output, 1)

        combo_dst = QComboBox()
        combo_dst.addItems(temp_units)
        combo_dst.setCurrentIndex(1)
        combo_dst.setMinimumWidth(120)
        row2.addWidget(combo_dst)

        btn_copy = QPushButton("📋 Copiar")
        btn_copy.setFixedWidth(90)
        row2.addWidget(btn_copy)
        vbox.addLayout(row2)

        # --- Reference table ---
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(["Unidad", "Valor"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setRowCount(len(temp_units))
        for i, name in enumerate(temp_units):
            table.setItem(i, 0, QTableWidgetItem(name))
            table.setItem(i, 1, QTableWidgetItem(""))
        vbox.addWidget(table, 1)

        self._tabs.addTab(widget, "Temperatura")

        # --- Conversion logic ---
        def _convert(*_args):
            val = spin.value()
            src = combo_src.currentText()
            dst = combo_dst.currentText()
            celsius = _temp_to_celsius(val, src)
            result = _celsius_to_unit(celsius, dst)
            output.setText(self._format_number(result))
            for i, name in enumerate(temp_units):
                converted = _celsius_to_unit(celsius, name)
                table.item(i, 1).setText(self._format_number(converted))

        spin.valueChanged.connect(_convert)
        combo_src.currentIndexChanged.connect(_convert)
        combo_dst.currentIndexChanged.connect(_convert)

        def _swap():
            si = combo_src.currentIndex()
            di = combo_dst.currentIndex()
            combo_src.setCurrentIndex(di)
            combo_dst.setCurrentIndex(si)

        btn_swap.clicked.connect(_swap)

        def _copy():
            txt = f"{spin.value()} {combo_src.currentText()} = {output.text()} {combo_dst.currentText()}"
            QApplication.clipboard().setText(txt)

        btn_copy.clicked.connect(_copy)

        _convert()

    # --------------------------------------------------------------------- #
    # AWG ↔ Métrico tab
    # --------------------------------------------------------------------- #
    def _create_awg_tab(self):
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        # --- Search row ---
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar AWG o mm²:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Ej: 14  o  2.08")
        search_input.setMinimumWidth(120)
        search_row.addWidget(search_input, 1)

        btn_copy_awg = QPushButton("📋 Copiar fila")
        btn_copy_awg.setFixedWidth(110)
        search_row.addWidget(btn_copy_awg)
        vbox.addLayout(search_row)

        # --- Table ---
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "AWG", "Diámetro (mm)", "Sección (mm²)",
            "Resistencia (Ω/km)", "Corriente máx. (A)",
        ])
        table.horizontalHeader().setStretchLastSection(True)
        for col in range(4):
            table.horizontalHeader().setSectionResizeMode(
                col, QHeaderView.ResizeMode.Stretch
            )
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)

        num_rows = len(_AWG_NUMBERS)
        table.setRowCount(num_rows)
        for i, n in enumerate(_AWG_NUMBERS):
            label = _AWG_LABELS[i]
            d_mm = _awg_diameter_mm(n)
            s_mm2 = _awg_section_mm2(n)
            r_ohm_km = _awg_resistance_ohm_per_km(n)
            amp = _AWG_AMPACITY.get(n, 0.0)

            items = [
                QTableWidgetItem(label),
                QTableWidgetItem(f"{d_mm:.4f}"),
                QTableWidgetItem(f"{s_mm2:.4f}"),
                QTableWidgetItem(f"{r_ohm_km:.4f}"),
                QTableWidgetItem(f"{amp:.1f}"),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    if col > 0
                    else Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
                )
                table.setItem(i, col, item)

        vbox.addWidget(table, 1)
        self._tabs.addTab(widget, "AWG ↔ Métrico")

        # --- Search logic ---
        def _search(text):
            text = text.strip()
            if not text:
                table.clearSelection()
                return
            # Try matching by AWG label first
            for i, label in enumerate(_AWG_LABELS):
                # Match exact AWG number or label prefix
                clean_label = label.split(" ")[0]  # "0000", "000", "00", "0", "1"…
                if text == clean_label or text == label:
                    table.selectRow(i)
                    table.scrollToItem(table.item(i, 0))
                    return
            # Try matching by mm² (closest)
            try:
                target = float(text)
                best_i = 0
                best_diff = float("inf")
                for i, n in enumerate(_AWG_NUMBERS):
                    diff = abs(_awg_section_mm2(n) - target)
                    if diff < best_diff:
                        best_diff = diff
                        best_i = i
                table.selectRow(best_i)
                table.scrollToItem(table.item(best_i, 0))
            except ValueError:
                table.clearSelection()

        search_input.textChanged.connect(_search)

        def _copy_row():
            row = table.currentRow()
            if row < 0:
                return
            parts = []
            for col in range(table.columnCount()):
                header = table.horizontalHeaderItem(col).text()
                value = table.item(row, col).text()
                parts.append(f"{header}: {value}")
            QApplication.clipboard().setText(" | ".join(parts))

        btn_copy_awg.clicked.connect(_copy_row)

    # --------------------------------------------------------------------- #
    # Numeric base‑converter tab
    # --------------------------------------------------------------------- #
    def _create_numeric_tab(self):
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(10)

        title = QLabel("Conversor de Bases Numéricas")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #f9e2af; margin-bottom: 4px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(title)

        # Bit‑width selector
        bw_row = QHBoxLayout()
        bw_row.addStretch()
        bw_row.addWidget(QLabel("Ancho de bits:"))
        combo_bits = QComboBox()
        combo_bits.addItems(["8", "16", "32", "64"])
        combo_bits.setCurrentIndex(2)  # default 32
        combo_bits.setFixedWidth(70)
        bw_row.addWidget(combo_bits)
        bw_row.addStretch()
        vbox.addLayout(bw_row)

        # Fields
        fields = {}
        _updating = {"flag": False}

        for label_text, base_key in [
            ("Binario:", "bin"),
            ("Octal:", "oct"),
            ("Decimal:", "dec"),
            ("Hexadecimal:", "hex"),
        ]:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFixedWidth(100)
            row.addWidget(lbl)

            le = QLineEdit("0")
            le.setFont(QFont("Segoe UI", 13))
            row.addWidget(le, 1)

            btn = QPushButton("📋")
            btn.setFixedWidth(36)
            btn.setToolTip(f"Copiar {label_text.replace(':', '')}")
            row.addWidget(btn)
            vbox.addLayout(row)

            fields[base_key] = le

            # Copy button
            btn.clicked.connect(partial(
                lambda field: QApplication.clipboard().setText(field.text()),
                le,
            ))

        # Error label
        err_label = QLabel("")
        err_label.setStyleSheet("color: #f38ba8; font-size: 11px;")
        err_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vbox.addWidget(err_label)

        vbox.addStretch()
        self._tabs.addTab(widget, "Numérico")

        # --- Conversion logic ---
        def _get_max():
            bits = int(combo_bits.currentText())
            return (1 << bits) - 1

        def _update_from(source_key, *_args):
            if _updating["flag"]:
                return
            _updating["flag"] = True
            err_label.setText("")

            text = fields[source_key].text().strip()
            if not text:
                for k in fields:
                    if k != source_key:
                        fields[k].setText("")
                _updating["flag"] = False
                return

            base_map = {"bin": 2, "oct": 8, "dec": 10, "hex": 16}
            base = base_map[source_key]
            max_val = _get_max()

            try:
                value = int(text, base)
                if value < 0:
                    raise ValueError("Valores negativos no soportados")
                if value > max_val:
                    bits = combo_bits.currentText()
                    err_label.setText(
                        f"⚠ Valor excede {bits} bits (máx {max_val})"
                    )
                    value = value & max_val  # mask to fit
            except ValueError as e:
                err_label.setText(f"⚠ Entrada inválida: {e}")
                _updating["flag"] = False
                return

            if source_key != "bin":
                fields["bin"].setText(bin(value)[2:])
            if source_key != "oct":
                fields["oct"].setText(oct(value)[2:])
            if source_key != "dec":
                fields["dec"].setText(str(value))
            if source_key != "hex":
                fields["hex"].setText(hex(value)[2:].upper())

            _updating["flag"] = False

        fields["bin"].textChanged.connect(partial(_update_from, "bin"))
        fields["oct"].textChanged.connect(partial(_update_from, "oct"))
        fields["dec"].textChanged.connect(partial(_update_from, "dec"))
        fields["hex"].textChanged.connect(partial(_update_from, "hex"))

        def _bits_changed(*_args):
            _update_from("dec")

        combo_bits.currentIndexChanged.connect(_bits_changed)

    # --------------------------------------------------------------------- #
    # Number formatting
    # --------------------------------------------------------------------- #
    @staticmethod
    def _format_number(value):
        """Return a human‑friendly string for *value*."""
        if value == 0:
            return "0"
        abs_val = abs(value)
        # Very large or very small → scientific
        if abs_val >= 1e12 or (abs_val != 0 and abs_val < 1e-6):
            return f"{value:.10g}"
        # Up to 10 meaningful decimals
        formatted = f"{value:.10f}"
        # Strip trailing zeros but keep at least one decimal
        if "." in formatted:
            formatted = formatted.rstrip("0").rstrip(".")
        return formatted
