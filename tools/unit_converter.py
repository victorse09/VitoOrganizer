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
    QSpinBox, QAbstractItemView, QStackedWidget, QFrame,
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
    background: transparent;
    border: none;
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
# Screws, threads and fractional inch conversion data
# =============================================================================

# ISO Metric Screws (Designation, Diam mm, Coarse Pitch mm, Tap Drill mm, Wrench mm, Approx Inch, Fine Pitch)
_METRIC_SCREWS = [
    ("M1.6",  1.6,  0.35,  1.25, "3.2",     '~1/16" (0.063")',          "0.20"),
    ("M2",    2.0,  0.40,  1.60, "4.0",     '~5/64" (#2 / 0.079")',     "0.25"),
    ("M2.5",  2.5,  0.45,  2.05, "5.0",     '~3/32" (#3 / 0.098")',     "0.35"),
    ("M3",    3.0,  0.50,  2.50, "5.5",     '~1/8" (#4-#5 / 0.118")',   "0.35"),
    ("M3.5",  3.5,  0.60,  2.90, "6.0",     '~9/64" (#6 / 0.138")',     "0.35"),
    ("M4",    4.0,  0.70,  3.30, "7.0",     '~5/32" (#8 / 0.157")',     "0.50"),
    ("M5",    5.0,  0.80,  4.20, "8.0",     '~3/16" (#10 / 0.197")',    "0.50"),
    ("M6",    6.0,  1.00,  5.00, "10.0",    '~1/4" (15/64" / 0.236")',  "0.75"),
    ("M7",    7.0,  1.00,  6.00, "11.0",    '~9/32" (0.276")',          "0.75"),
    ("M8",    8.0,  1.25,  6.80, "13.0",    '~5/16" (0.315")',          "1.00 / 0.75"),
    ("M10",  10.0,  1.50,  8.50, "16 / 17", '~3/8" (0.394")',           "1.25 / 1.00"),
    ("M12",  12.0,  1.75, 10.20, "18 / 19", '~1/2" (15/32" / 0.472")',  "1.50 / 1.25"),
    ("M14",  14.0,  2.00, 12.00, "21 / 22", '~9/16" (0.551")',          "1.50"),
    ("M16",  16.0,  2.00, 14.00, "24.0",    '~5/8" (0.630")',           "1.50"),
    ("M18",  18.0,  2.50, 15.50, "27.0",    '~11/16" (0.709")',         "2.00 / 1.50"),
    ("M20",  20.0,  2.50, 17.50, "30.0",    '~3/4" (0.787")',           "2.00 / 1.50"),
    ("M22",  22.0,  2.50, 19.50, "32.0",    '~7/8" (0.866")',           "2.00 / 1.50"),
    ("M24",  24.0,  3.00, 21.00, "36.0",    '~15/16" (0.945")',         "2.00"),
    ("M27",  27.0,  3.00, 24.00, "41.0",    '~1-1/16" (1.063")',        "2.00"),
    ("M30",  30.0,  3.50, 26.50, "46.0",    '~1-3/16" (1.181")',        "2.00"),
]

# Inch Screws & Hardware (Fraction/Designation, Dec in, mm, Common Thread UNC/UNF, Tap Drill, Wrench, Metric Approx)
_INCH_SCREWS = [
    ('#2-56',   0.0860,  2.184, "#2-56 UNC / #2-64 UNF",   "1.85 mm (#50)",     '3/16" (~4.8 mm)',   "~M2.2 / M2"),
    ('#3-48',   0.0990,  2.515, "#3-48 UNC / #3-56 UNF",   "2.10 mm (#47)",     '3/16" (~4.8 mm)',   "~M2.5"),
    ('#4-40',   0.1120,  2.845, "#4-40 UNC / #4-48 UNF",   "2.35 mm (#43)",     '1/4" (~6.3 mm)',    "~M3"),
    ('#5-40',   0.1250,  3.175, "#5-40 UNC / #5-44 UNF",   "2.65 mm (#38)",     '1/4" (~6.3 mm)',    "~M3 / M3.5"),
    ('#6-32',   0.1380,  3.505, "#6-32 UNC / #6-40 UNF",   "2.85 mm (#36)",     '5/16" (~7.9 mm)',   "~M3.5"),
    ('#8-32',   0.1640,  4.166, "#8-32 UNC / #8-36 UNF",   "3.50 mm (#29)",     '11/32" (~8.7 mm)',  "~M4"),
    ('#10-24',  0.1900,  4.826, "#10-24 UNC / #10-32 UNF", "3.90 mm (#25)",     '3/8" (~9.5 mm)',    "~M5"),
    ('#12-24',  0.2160,  5.486, "#12-24 UNC / #12-28 UNF", "4.50 mm (#16)",     '7/16" (~11.1 mm)',  "~M5.5"),
    ('1/16"',   0.0625,  1.588, "1/16\"-64",               "1.20 mm",           '5/32" (~4.0 mm)',   "~M1.6"),
    ('5/64"',   0.0781,  1.984, "5/64\"-56",               "1.55 mm",           '3/16" (~4.8 mm)',   "~M2"),
    ('3/32"',   0.0938,  2.381, "3/32\"-48",               "1.90 mm",           '3/16" (~4.8 mm)',   "~M2.5"),
    ('7/64"',   0.1094,  2.778, "7/64\"-40",               "2.25 mm",           '1/4" (~6.3 mm)',    "~M2.5 / M3"),
    ('1/8"',    0.1250,  3.175, "1/8\"-40 BSW",            "2.55 mm",           '1/4" (~6.3 mm)',    "~M3"),
    ('9/64"',   0.1406,  3.572, "9/64\"-36",               "2.90 mm",           '5/16" (~7.9 mm)',   "~M3.5"),
    ('5/32"',   0.1562,  3.969, "5/32\"-32 BSW",           "3.20 mm",           '5/16" (~7.9 mm)',   "~M4"),
    ('3/16"',   0.1875,  4.762, "3/16\"-24 BSW",           "3.70 mm",           '3/8" (~9.5 mm)',    "~M5"),
    ('7/32"',   0.2188,  5.556, "7/32\"-24",               "4.40 mm",           '7/16" (~11.1 mm)',  "~M5.5"),
    ('1/4"',    0.2500,  6.350, "1/4\"-20 UNC / 28 UNF",   "5.10 mm (#7)",      '7/16" (11.1 mm)',   "~M6"),
    ('5/16"',   0.3125,  7.938, "5/16\"-18 UNC / 24 UNF",  "6.60 mm (F)",       '1/2" (12.7 mm)',    "~M8"),
    ('3/8"',    0.3750,  9.525, "3/8\"-16 UNC / 24 UNF",   "8.00 mm (5/16\")",   '9/16" (14.3 mm)',   "~M10"),
    ('7/16"',   0.4375, 11.112, "7/16\"-14 UNC / 20 UNF",  "9.40 mm (U)",       '5/8" (15.9 mm)',    "~M11 / M12"),
    ('1/2"',    0.5000, 12.700, "1/2\"-13 UNC / 20 UNF",   "10.70 mm (27/64\")", '3/4" (19.0 mm)',    "~M12 / M13"),
    ('9/16"',   0.5625, 14.288, "9/16\"-12 UNC / 18 UNF",  "12.20 mm",          '13/16" (20.6 mm)',  "~M14"),
    ('5/8"',    0.6250, 15.875, "5/8\"-11 UNC / 18 UNF",   "13.50 mm (17/32\")", '15/16" (23.8 mm)',  "~M16"),
    ('3/4"',    0.7500, 19.050, "3/4\"-10 UNC / 16 UNF",   "16.50 mm (21/32\")", '1-1/8" (28.6 mm)',  "~M20"),
    ('7/8"',    0.8750, 22.225, "7/8\"-9 UNC / 14 UNF",    "19.50 mm (49/64\")", '1-5/16" (33.3 mm)', "~M22"),
    ('1"',      1.0000, 25.400, "1\"-8 UNC / 12 UNF",      "22.25 mm (7/8\")",   '1-1/2" (38.1 mm)',  "~M24 / M25"),
    ('1-1/8"',  1.1250, 28.575, "1-1/8\"-7 UNC / 12 UNF",  "25.00 mm",          '1-11/16" (42.9 mm)',"~M27 / M28"),
    ('1-1/4"',  1.2500, 31.750, "1-1/4\"-7 UNC / 12 UNF",  "28.20 mm",          '1-7/8" (47.6 mm)',  "~M30 / M32"),
]

_COMMON_FRACTIONS = [
    ('1/16"',  1/16),
    ('5/64"',  5/64),
    ('3/32"',  3/32),
    ('7/64"',  7/64),
    ('1/8"',   1/8),
    ('9/64"',  9/64),
    ('5/32"',  5/32),
    ('3/16"',  3/16),
    ('7/32"',  7/32),
    ('1/4"',   1/4),
    ('5/16"',  5/16),
    ('3/8"',   3/8),
    ('7/16"',  7/16),
    ('1/2"',   1/2),
    ('9/16"',  9/16),
    ('5/8"',   5/8),
    ('11/16"', 11/16),
    ('3/4"',   3/4),
    ('13/16"', 13/16),
    ('7/8"',   7/8),
    ('15/16"', 15/16),
    ('1"',     1.0),
    ('1-1/8"', 1.125),
    ('1-1/4"', 1.25),
]


def _decimal_to_fraction_str(val_inches, max_denom=64):
    """Convierte pulgadas decimales a fracción reducida en 64avos."""
    if val_inches <= 0:
        return '0"', 0.0, 0.0, True
    n = round(val_inches * max_denom)
    if n == 0:
        return '0"', 0.0, -val_inches * 25.4, False
    g = math.gcd(n, max_denom)
    num = n // g
    den = max_denom // g
    whole = num // den
    rem = num % den
    if whole > 0 and rem > 0:
        frac_str = f'{whole} {rem}/{den}"'
    elif whole > 0:
        frac_str = f'{whole}"'
    else:
        frac_str = f'{rem}/{den}"'
    approx_val = n / max_denom
    diff_mm = (val_inches - approx_val) * 25.4
    is_exact = abs(diff_mm) < 0.001
    return frac_str, approx_val, diff_mm, is_exact


def _find_nearest_screws(mm):
    """Encuentra el tornillo métrico y en pulgadas más próximo a una medida en mm."""
    best_m = None
    min_diff_m = float("inf")
    for row in _METRIC_SCREWS:
        diff = abs(row[1] - mm)
        if diff < min_diff_m:
            min_diff_m = diff
            best_m = row

    best_in = None
    min_diff_in = float("inf")
    for row in _INCH_SCREWS:
        diff = abs(row[2] - mm)
        if diff < min_diff_in:
            min_diff_in = diff
            best_in = row

    return best_m, min_diff_m, best_in, min_diff_in


# =============================================================================
# Main dialog
# =============================================================================

class UnitConverterDialog(QDialog):
    """Floating unit‑converter tool with physical, AWG, screws and numeric tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversor de Unidades")
        self.setWindowFlags(
            Qt.WindowType.Tool | Qt.WindowType.WindowCloseButtonHint
        )
        self.resize(560, 620)
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
        self._create_screws_tab()
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

        btn_copy = QPushButton("Copiar")
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

        btn_copy = QPushButton("Copiar")
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

        btn_copy_awg = QPushButton("Copiar fila")
        btn_copy_awg.setFixedWidth(100)
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
    # Tornillos ↔ Pulgadas tab
    # --------------------------------------------------------------------- #
    def _create_screws_tab(self):
        widget = QWidget()
        vbox = QVBoxLayout(widget)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(6)

        # --- Card superior: Conversor interactivo ---
        card = QFrame()
        card.setObjectName("calcCard")
        card.setStyleSheet("""
            QFrame#calcCard {
                background-color: #24273a;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px;
            }
            QFrame#calcCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(8, 8, 8, 8)
        card_layout.setSpacing(6)

        title = QLabel("Conversor Rápido: Métrico ↔ Pulgadas (Tornillos y Tuercas)")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: #f9e2af; margin-bottom: 2px; background: transparent; border: none;")
        card_layout.addWidget(title)

        # Fila de controles interactivos
        input_row = QHBoxLayout()
        input_row.setSpacing(6)

        input_row.addWidget(QLabel("mm:"))
        spin_mm = QDoubleSpinBox()
        spin_mm.setDecimals(3)
        spin_mm.setRange(0.01, 500.0)
        spin_mm.setValue(6.0)
        spin_mm.setSingleStep(0.5)
        spin_mm.setMinimumWidth(85)
        input_row.addWidget(spin_mm)

        input_row.addWidget(QLabel("Pulgada:"))
        spin_in = QDoubleSpinBox()
        spin_in.setDecimals(4)
        spin_in.setRange(0.001, 20.0)
        spin_in.setValue(6.0 / 25.4)
        spin_in.setSingleStep(0.0625)
        spin_in.setMinimumWidth(85)
        input_row.addWidget(spin_in)

        input_row.addWidget(QLabel("Fracción:"))
        combo_frac = QComboBox()
        combo_frac.addItem("(Elegir fracción...)")
        for frac_label, frac_val in _COMMON_FRACTIONS:
            combo_frac.addItem(f"{frac_label} ({frac_val * 25.4:.2f} mm)")
        combo_frac.setMinimumWidth(130)
        input_row.addWidget(combo_frac)

        btn_copy_calc = QPushButton("Copiar")
        btn_copy_calc.setFixedWidth(70)
        input_row.addWidget(btn_copy_calc)
        card_layout.addLayout(input_row)

        # Cuadro de resultados resumidos
        lbl_res_frac = QLabel()
        lbl_res_frac.setStyleSheet("color: #cdd6f4; font-size: 12px; background: transparent; border: none;")
        card_layout.addWidget(lbl_res_frac)

        lbl_res_screw = QLabel()
        lbl_res_screw.setStyleSheet("color: #a6e3a1; font-size: 12px; font-weight: bold; background: transparent; border: none;")
        card_layout.addWidget(lbl_res_screw)

        vbox.addWidget(card)

        # --- Selector de tabla y búsqueda ---
        nav_row = QHBoxLayout()
        nav_row.setSpacing(6)

        btn_view_metric = QPushButton("Tornillos Métricos (M)")
        btn_view_metric.setCheckable(True)
        btn_view_metric.setChecked(True)

        btn_view_inch = QPushButton("Pulgadas (Tornillos y Tuercas)")
        btn_view_inch.setCheckable(True)
        btn_view_inch.setChecked(False)

        def _update_tab_buttons():
            if btn_view_metric.isChecked():
                btn_view_metric.setStyleSheet("background-color: #45475a; color: #f9e2af; font-weight: bold; border: 1px solid #89b4fa;")
                btn_view_inch.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;")
            else:
                btn_view_metric.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;")
                btn_view_inch.setStyleSheet("background-color: #45475a; color: #f9e2af; font-weight: bold; border: 1px solid #89b4fa;")

        nav_row.addWidget(btn_view_metric)
        nav_row.addWidget(btn_view_inch)
        nav_row.addStretch()
        vbox.addLayout(nav_row)

        # Fila de búsqueda y copiado de fila
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Buscar:"))
        search_input = QLineEdit()
        search_input.setPlaceholderText("Ej: M6, M4, 1/4, llave 10, broca 5...")
        search_input.setMinimumWidth(150)
        search_row.addWidget(search_input, 1)

        btn_copy_row = QPushButton("Copiar fila")
        btn_copy_row.setFixedWidth(90)
        search_row.addWidget(btn_copy_row)
        vbox.addLayout(search_row)

        # --- Contenedor Stacked para ambas tablas ---
        stack = QStackedWidget()

        # 1. Tabla Métrica
        table_m = QTableWidget()
        table_m.setColumnCount(6)
        table_m.setHorizontalHeaderLabels([
            "Métrica", "Diám. (mm)", "Paso Estándar",
            "Broca Roscado", "Llave / Tuerca", "Equiv. Pulgada",
        ])
        table_m.horizontalHeader().setStretchLastSection(True)
        for col in range(5):
            table_m.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        table_m.verticalHeader().setVisible(False)
        table_m.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_m.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table_m.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table_m.setRowCount(len(_METRIC_SCREWS))

        for row_idx, data in enumerate(_METRIC_SCREWS):
            items = [
                QTableWidgetItem(data[0]),
                QTableWidgetItem(f"{data[1]:.2f}"),
                QTableWidgetItem(f"{data[2]:.2f} mm"),
                QTableWidgetItem(f"{data[3]:.2f} mm"),
                QTableWidgetItem(f"{data[4]} mm"),
                QTableWidgetItem(data[5]),
            ]
            for col_idx, item in enumerate(items):
                align = Qt.AlignmentFlag.AlignCenter if col_idx == 0 else (
                    Qt.AlignmentFlag.AlignRight if col_idx in (1, 2, 3, 4) else Qt.AlignmentFlag.AlignLeft
                )
                item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                table_m.setItem(row_idx, col_idx, item)

        stack.addWidget(table_m)

        # 2. Tabla en Pulgadas
        table_in = QTableWidget()
        table_in.setColumnCount(7)
        table_in.setHorizontalHeaderLabels([
            "Medida Pulg.", "Decimal (in)", "Métrico (mm)",
            "Rosca Estándar", "Broca Roscado", "Llave Tuerca / Cabeza", "Equiv. Métrica",
        ])
        table_in.horizontalHeader().setStretchLastSection(True)
        for col in range(6):
            table_in.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        table_in.verticalHeader().setVisible(False)
        table_in.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_in.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table_in.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table_in.setRowCount(len(_INCH_SCREWS))

        for row_idx, data in enumerate(_INCH_SCREWS):
            items = [
                QTableWidgetItem(data[0]),
                QTableWidgetItem(f"{data[1]:.4f}\""),
                QTableWidgetItem(f"{data[2]:.3f}"),
                QTableWidgetItem(data[3]),
                QTableWidgetItem(data[4]),
                QTableWidgetItem(data[5]),
                QTableWidgetItem(data[6]),
            ]
            for col_idx, item in enumerate(items):
                align = Qt.AlignmentFlag.AlignCenter if col_idx == 0 else (
                    Qt.AlignmentFlag.AlignRight if col_idx in (1, 2) else Qt.AlignmentFlag.AlignLeft
                )
                item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                table_in.setItem(row_idx, col_idx, item)

        stack.addWidget(table_in)
        vbox.addWidget(stack, 1)

        _update_tab_buttons()

        def _switch_to_metric():
            btn_view_metric.setChecked(True)
            btn_view_inch.setChecked(False)
            _update_tab_buttons()
            stack.setCurrentIndex(0)
            _apply_search(search_input.text())

        def _switch_to_inch():
            btn_view_metric.setChecked(False)
            btn_view_inch.setChecked(True)
            _update_tab_buttons()
            stack.setCurrentIndex(1)
            _apply_search(search_input.text())

        btn_view_metric.clicked.connect(_switch_to_metric)
        btn_view_inch.clicked.connect(_switch_to_inch)

        # --- Lógica de sincronización del Conversor Rápido ---
        _syncing = {"flag": False}

        def _update_results(mm_val, in_val):
            frac_str, approx_in, diff_mm, is_exact = _decimal_to_fraction_str(in_val)
            exact_txt = "exacta" if is_exact else f"más cercana (dif: {diff_mm:+.2f} mm)"
            lbl_res_frac.setText(
                f"<b>{mm_val:.3f} mm</b> = <b>{in_val:.4f}\"</b> | Fracción {exact_txt}: <b>{frac_str}</b>"
            )

            best_m, diff_m, best_in, diff_in = _find_nearest_screws(mm_val)
            parts = []
            if best_m:
                m_diff = f" (dif: {diff_m:.2f} mm)" if diff_m > 0.05 else ""
                parts.append(f"Métrica: <b>{best_m[0]}</b> (Paso {best_m[2]} mm, Broca {best_m[3]} mm, Llave {best_m[4]} mm){m_diff}")
            if best_in:
                in_diff = f" (dif: {diff_in:.2f} mm)" if diff_in > 0.05 else ""
                parts.append(f"Pulgada: <b>{best_in[0]}</b> ({best_in[3]}, Llave {best_in[5]}){in_diff}")

            lbl_res_screw.setText("<br>".join(parts))

        def _on_mm_changed(val):
            if _syncing["flag"]:
                return
            _syncing["flag"] = True
            in_val = val / 25.4
            spin_in.setValue(in_val)
            _update_results(val, in_val)
            _syncing["flag"] = False

        def _on_in_changed(val):
            if _syncing["flag"]:
                return
            _syncing["flag"] = True
            mm_val = val * 25.4
            spin_mm.setValue(mm_val)
            _update_results(mm_val, val)
            _syncing["flag"] = False

        def _on_frac_changed(idx):
            if _syncing["flag"] or idx <= 0:
                return
            _syncing["flag"] = True
            frac_val = _COMMON_FRACTIONS[idx - 1][1]
            spin_in.setValue(frac_val)
            spin_mm.setValue(frac_val * 25.4)
            _update_results(frac_val * 25.4, frac_val)
            _syncing["flag"] = False

        spin_mm.valueChanged.connect(_on_mm_changed)
        spin_in.valueChanged.connect(_on_in_changed)
        combo_frac.currentIndexChanged.connect(_on_frac_changed)

        # Clic en fila de tabla -> Cargar en conversor
        def _on_metric_row_clicked(row, _col):
            if row < 0 or row >= len(_METRIC_SCREWS):
                return
            mm = _METRIC_SCREWS[row][1]
            spin_mm.setValue(mm)

        def _on_inch_row_clicked(row, _col):
            if row < 0 or row >= len(_INCH_SCREWS):
                return
            dec_in = _INCH_SCREWS[row][1]
            spin_in.setValue(dec_in)

        table_m.cellClicked.connect(_on_metric_row_clicked)
        table_in.cellClicked.connect(_on_inch_row_clicked)

        # Búsqueda / filtrado
        def _apply_search(text):
            query = text.strip().lower()
            current_table = table_m if stack.currentIndex() == 0 else table_in
            for r in range(current_table.rowCount()):
                match = False
                if not query:
                    match = True
                else:
                    for c in range(current_table.columnCount()):
                        cell_item = current_table.item(r, c)
                        if cell_item and query in cell_item.text().lower():
                            match = True
                            break
                current_table.setRowHidden(r, not match)

        search_input.textChanged.connect(_apply_search)

        # Copiado
        def _copy_calc():
            mm_val = spin_mm.value()
            in_val = spin_in.value()
            frac_str, approx_in, diff_mm, is_exact = _decimal_to_fraction_str(in_val)
            best_m, diff_m, best_in, diff_in = _find_nearest_screws(mm_val)
            summary = (
                f"{mm_val:.3f} mm = {in_val:.4f}\" ({frac_str})\n"
                f"Métrica sugerida: {best_m[0]} (Paso {best_m[2]} mm, Broca {best_m[3]} mm, Llave {best_m[4]} mm)\n"
                f"Pulgada sugerida: {best_in[0]} ({best_in[3]}, Llave {best_in[5]})"
            )
            QApplication.clipboard().setText(summary)

        btn_copy_calc.clicked.connect(_copy_calc)

        def _copy_table_row():
            current_table = table_m if stack.currentIndex() == 0 else table_in
            row = current_table.currentRow()
            if row < 0:
                return
            parts = []
            for col in range(current_table.columnCount()):
                h = current_table.horizontalHeaderItem(col).text()
                val = current_table.item(row, col).text()
                parts.append(f"{h}: {val}")
            QApplication.clipboard().setText(" | ".join(parts))

        btn_copy_row.clicked.connect(_copy_table_row)

        # Inicialización con M6
        _update_results(6.0, 6.0 / 25.4)

        self._tabs.addTab(widget, "Tornillos ↔ Pulgadas")

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
        title.setStyleSheet("color: #f9e2af; margin-bottom: 4px; background: transparent; border: none;")
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

            btn = QPushButton("Copiar")
            btn.setFixedWidth(60)
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
        err_label.setStyleSheet("color: #f38ba8; font-size: 11px; background: transparent; border: none;")
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
                        f"Aviso: Valor excede {bits} bits (máx {max_val})"
                    )
                    value = value & max_val  # mask to fit
            except ValueError as e:
                err_label.setText(f"Error: Entrada inválida: {e}")
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
