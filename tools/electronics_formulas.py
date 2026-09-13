"""
electronics_formulas.py — Módulo de datos con todas las fórmulas electrónicas/eléctricas
estructuradas como diccionarios para Vito Organizer.

Cada grupo de fórmulas sigue la estructura:
    {
        'name': str,           # Nombre en español
        'icon': str,           # Emoji representativo
        'variables': list,     # Variables con symbol, name, unit, default
        'formulas': list,      # Fórmulas con solve_for, inputs, expression (lambda), display
    }

Variantes especiales:
    - 'list_input': True  → acepta número variable de entradas (min/max definidos)
    - 'truth_table': dict → tabla de verdad para compuertas lógicas
    - 'type': 'reference' → datos de referencia (como código de colores de resistencias)
"""

import math

# ──────────────────────────────────────────────────────────────────────────────
# Colores de resistencias (referencia global)
# ──────────────────────────────────────────────────────────────────────────────

RESISTOR_COLORS = {
    'Negro':    {'value': 0, 'multiplier': 1,          'tolerance': None, 'hex': '#000000', 'ppm': 250},
    'Marrón':   {'value': 1, 'multiplier': 10,         'tolerance': 1,    'hex': '#8B4513', 'ppm': 100},
    'Rojo':     {'value': 2, 'multiplier': 100,        'tolerance': 2,    'hex': '#FF0000', 'ppm': 50},
    'Naranja':  {'value': 3, 'multiplier': 1000,       'tolerance': None, 'hex': '#FF8C00', 'ppm': 15},
    'Amarillo': {'value': 4, 'multiplier': 10000,      'tolerance': None, 'hex': '#FFD700', 'ppm': 25},
    'Verde':    {'value': 5, 'multiplier': 100000,     'tolerance': 0.5,  'hex': '#00AA00', 'ppm': 20},
    'Azul':     {'value': 6, 'multiplier': 1000000,    'tolerance': 0.25, 'hex': '#0000FF', 'ppm': 10},
    'Violeta':  {'value': 7, 'multiplier': 10000000,   'tolerance': 0.1,  'hex': '#8B00FF', 'ppm': 5},
    'Gris':     {'value': 8, 'multiplier': 100000000,  'tolerance': 0.05, 'hex': '#808080', 'ppm': 1},
    'Blanco':   {'value': 9, 'multiplier': 1000000000, 'tolerance': None, 'hex': '#FFFFFF'},
    'Dorado':   {'value': None, 'multiplier': 0.1,     'tolerance': 5,    'hex': '#DAA520'},
    'Plateado': {'value': None, 'multiplier': 0.01,    'tolerance': 10,   'hex': '#C0C0C0'},
}

# ──────────────────────────────────────────────────────────────────────────────
# ANALOG_FORMULAS
# ──────────────────────────────────────────────────────────────────────────────

ANALOG_FORMULAS = {

    # 1. Ley de Ohm ─────────────────────────────────────────────────────────
    'ohms_law': {
        'name': 'Ley de Ohm',
        'icon': '⚡',
        'variables': [
            {'symbol': 'V', 'name': 'Voltaje', 'unit': 'V', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente', 'unit': 'A', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'V',
                'inputs': ['I', 'R'],
                'expression': lambda vals: vals['I'] * vals['R'],
                'display': 'V = I × R',
            },
            {
                'solve_for': 'I',
                'inputs': ['V', 'R'],
                'expression': lambda vals: vals['V'] / vals['R'] if vals['R'] != 0 else float('inf'),
                'display': 'I = V / R',
            },
            {
                'solve_for': 'R',
                'inputs': ['V', 'I'],
                'expression': lambda vals: vals['V'] / vals['I'] if vals['I'] != 0 else float('inf'),
                'display': 'R = V / I',
            },
        ],
    },

    # 2. Potencia eléctrica ─────────────────────────────────────────────────
    'power': {
        'name': 'Potencia Eléctrica',
        'icon': '💡',
        'variables': [
            {'symbol': 'P', 'name': 'Potencia', 'unit': 'W', 'default': 0.0},
            {'symbol': 'V', 'name': 'Voltaje', 'unit': 'V', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente', 'unit': 'A', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'P',
                'inputs': ['V', 'I'],
                'expression': lambda vals: vals['V'] * vals['I'],
                'display': 'P = V × I',
            },
            {
                'solve_for': 'P',
                'inputs': ['I', 'R'],
                'expression': lambda vals: vals['I'] ** 2 * vals['R'],
                'display': 'P = I² × R',
            },
            {
                'solve_for': 'P',
                'inputs': ['V', 'R'],
                'expression': lambda vals: vals['V'] ** 2 / vals['R'] if vals['R'] != 0 else float('inf'),
                'display': 'P = V² / R',
            },
            {
                'solve_for': 'V',
                'inputs': ['P', 'I'],
                'expression': lambda vals: vals['P'] / vals['I'] if vals['I'] != 0 else float('inf'),
                'display': 'V = P / I',
            },
            {
                'solve_for': 'V',
                'inputs': ['P', 'R'],
                'expression': lambda vals: math.sqrt(vals['P'] * vals['R']) if vals['P'] * vals['R'] >= 0 else float('nan'),
                'display': 'V = √(P × R)',
            },
            {
                'solve_for': 'I',
                'inputs': ['P', 'V'],
                'expression': lambda vals: vals['P'] / vals['V'] if vals['V'] != 0 else float('inf'),
                'display': 'I = P / V',
            },
            {
                'solve_for': 'I',
                'inputs': ['P', 'R'],
                'expression': lambda vals: math.sqrt(vals['P'] / vals['R']) if vals['R'] != 0 and vals['P'] / vals['R'] >= 0 else float('inf'),
                'display': 'I = √(P / R)',
            },
            {
                'solve_for': 'R',
                'inputs': ['P', 'I'],
                'expression': lambda vals: vals['P'] / (vals['I'] ** 2) if vals['I'] != 0 else float('inf'),
                'display': 'R = P / I²',
            },
            {
                'solve_for': 'R',
                'inputs': ['V', 'P'],
                'expression': lambda vals: vals['V'] ** 2 / vals['P'] if vals['P'] != 0 else float('inf'),
                'display': 'R = V² / P',
            },
        ],
    },

    # 3. Resistencias en serie ──────────────────────────────────────────────
    'resistors_series': {
        'name': 'Resistencias en Serie',
        'icon': '🔗',
        'list_input': True,
        'min_inputs': 2,
        'max_inputs': 10,
        'input_symbol': 'R',
        'input_name': 'Resistencia',
        'input_unit': 'Ω',
        'variables': [
            {'symbol': 'Rt', 'name': 'Resistencia Total', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Rt',
                'inputs': ['R_list'],
                'expression': lambda vals: sum(vals['R_list']),
                'display': 'Rt = R1 + R2 + … + Rn',
            },
        ],
    },

    # 4. Resistencias en paralelo ───────────────────────────────────────────
    'resistors_parallel': {
        'name': 'Resistencias en Paralelo',
        'icon': '🔀',
        'list_input': True,
        'min_inputs': 2,
        'max_inputs': 10,
        'input_symbol': 'R',
        'input_name': 'Resistencia',
        'input_unit': 'Ω',
        'variables': [
            {'symbol': 'Rt', 'name': 'Resistencia Total', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Rt',
                'inputs': ['R_list'],
                'expression': lambda vals: (
                    1.0 / sum(1.0 / r for r in vals['R_list'] if r != 0)
                    if all(r != 0 for r in vals['R_list']) and len(vals['R_list']) > 0
                    else float('inf')
                ),
                'display': '1/Rt = 1/R1 + 1/R2 + … + 1/Rn',
            },
        ],
    },

    # 5. Divisor de voltaje ─────────────────────────────────────────────────
    'voltage_divider': {
        'name': 'Divisor de Voltaje',
        'icon': '🔌',
        'variables': [
            {'symbol': 'Vin', 'name': 'Voltaje de Entrada', 'unit': 'V', 'default': 0.0},
            {'symbol': 'R1', 'name': 'Resistencia 1 (superior)', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'R2', 'name': 'Resistencia 2 (inferior)', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['Vin', 'R1', 'R2'],
                'expression': lambda vals: vals['Vin'] * vals['R2'] / (vals['R1'] + vals['R2']) if (vals['R1'] + vals['R2']) != 0 else float('inf'),
                'display': 'Vout = Vin × R2 / (R1 + R2)',
            },
            {
                'solve_for': 'R1',
                'inputs': ['Vin', 'Vout', 'R2'],
                'expression': lambda vals: vals['R2'] * (vals['Vin'] - vals['Vout']) / vals['Vout'] if vals['Vout'] != 0 else float('inf'),
                'display': 'R1 = R2 × (Vin − Vout) / Vout',
            },
            {
                'solve_for': 'R2',
                'inputs': ['Vin', 'Vout', 'R1'],
                'expression': lambda vals: vals['R1'] * vals['Vout'] / (vals['Vin'] - vals['Vout']) if (vals['Vin'] - vals['Vout']) != 0 else float('inf'),
                'display': 'R2 = R1 × Vout / (Vin − Vout)',
            },
        ],
    },

    # 6. Divisor de corriente ───────────────────────────────────────────────
    'current_divider': {
        'name': 'Divisor de Corriente',
        'icon': '🔃',
        'variables': [
            {'symbol': 'It', 'name': 'Corriente Total', 'unit': 'A', 'default': 0.0},
            {'symbol': 'R1', 'name': 'Resistencia 1', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'R2', 'name': 'Resistencia 2', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'I1', 'name': 'Corriente por R1', 'unit': 'A', 'default': 0.0},
            {'symbol': 'I2', 'name': 'Corriente por R2', 'unit': 'A', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'I1',
                'inputs': ['It', 'R1', 'R2'],
                'expression': lambda vals: vals['It'] * vals['R2'] / (vals['R1'] + vals['R2']) if (vals['R1'] + vals['R2']) != 0 else float('inf'),
                'display': 'I1 = It × R2 / (R1 + R2)',
            },
            {
                'solve_for': 'I2',
                'inputs': ['It', 'R1', 'R2'],
                'expression': lambda vals: vals['It'] * vals['R1'] / (vals['R1'] + vals['R2']) if (vals['R1'] + vals['R2']) != 0 else float('inf'),
                'display': 'I2 = It × R1 / (R1 + R2)',
            },
        ],
    },

    # 7. Reactancia capacitiva ──────────────────────────────────────────────
    'capacitor_reactance': {
        'name': 'Reactancia Capacitiva',
        'icon': '🔋',
        'variables': [
            {'symbol': 'Xc', 'name': 'Reactancia Capacitiva', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'f', 'name': 'Frecuencia', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Xc',
                'inputs': ['f', 'C'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * vals['f'] * vals['C']) if (vals['f'] * vals['C']) != 0 else float('inf'),
                'display': 'Xc = 1 / (2πfC)',
            },
            {
                'solve_for': 'f',
                'inputs': ['Xc', 'C'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * vals['Xc'] * vals['C']) if (vals['Xc'] * vals['C']) != 0 else float('inf'),
                'display': 'f = 1 / (2πXcC)',
            },
            {
                'solve_for': 'C',
                'inputs': ['Xc', 'f'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * vals['Xc'] * vals['f']) if (vals['Xc'] * vals['f']) != 0 else float('inf'),
                'display': 'C = 1 / (2πXcf)',
            },
        ],
    },

    # 8. Capacitores en serie ───────────────────────────────────────────────
    'capacitors_series': {
        'name': 'Capacitores en Serie',
        'icon': '🔗',
        'list_input': True,
        'min_inputs': 2,
        'max_inputs': 10,
        'input_symbol': 'C',
        'input_name': 'Capacitancia',
        'input_unit': 'F',
        'variables': [
            {'symbol': 'Ct', 'name': 'Capacitancia Total', 'unit': 'F', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Ct',
                'inputs': ['C_list'],
                'expression': lambda vals: (
                    1.0 / sum(1.0 / c for c in vals['C_list'] if c != 0)
                    if all(c != 0 for c in vals['C_list']) and len(vals['C_list']) > 0
                    else float('inf')
                ),
                'display': '1/Ct = 1/C1 + 1/C2 + … + 1/Cn',
            },
        ],
    },

    # 9. Capacitores en paralelo ────────────────────────────────────────────
    'capacitors_parallel': {
        'name': 'Capacitores en Paralelo',
        'icon': '🔀',
        'list_input': True,
        'min_inputs': 2,
        'max_inputs': 10,
        'input_symbol': 'C',
        'input_name': 'Capacitancia',
        'input_unit': 'F',
        'variables': [
            {'symbol': 'Ct', 'name': 'Capacitancia Total', 'unit': 'F', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Ct',
                'inputs': ['C_list'],
                'expression': lambda vals: sum(vals['C_list']),
                'display': 'Ct = C1 + C2 + … + Cn',
            },
        ],
    },

    # 10. Energía del capacitor ─────────────────────────────────────────────
    'capacitor_energy': {
        'name': 'Energía del Capacitor',
        'icon': '⚡',
        'variables': [
            {'symbol': 'E', 'name': 'Energía', 'unit': 'J', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
            {'symbol': 'V', 'name': 'Voltaje', 'unit': 'V', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'E',
                'inputs': ['C', 'V'],
                'expression': lambda vals: 0.5 * vals['C'] * vals['V'] ** 2,
                'display': 'E = ½CV²',
            },
            {
                'solve_for': 'C',
                'inputs': ['E', 'V'],
                'expression': lambda vals: 2.0 * vals['E'] / (vals['V'] ** 2) if vals['V'] != 0 else float('inf'),
                'display': 'C = 2E / V²',
            },
            {
                'solve_for': 'V',
                'inputs': ['E', 'C'],
                'expression': lambda vals: math.sqrt(2.0 * vals['E'] / vals['C']) if vals['C'] != 0 and (2.0 * vals['E'] / vals['C']) >= 0 else float('inf'),
                'display': 'V = √(2E / C)',
            },
        ],
    },

    # 11. Constante de tiempo RC ────────────────────────────────────────────
    'rc_time_constant': {
        'name': 'Constante de Tiempo RC',
        'icon': '⏱️',
        'variables': [
            {'symbol': 'τ', 'name': 'Constante de Tiempo', 'unit': 's', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
            {'symbol': 't63', 'name': 'Tiempo al 63.2%', 'unit': 's', 'default': 0.0},
            {'symbol': 't99', 'name': 'Tiempo al ~100% (5τ)', 'unit': 's', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'τ',
                'inputs': ['R', 'C'],
                'expression': lambda vals: vals['R'] * vals['C'],
                'display': 'τ = R × C',
            },
            {
                'solve_for': 'R',
                'inputs': ['τ', 'C'],
                'expression': lambda vals: vals['τ'] / vals['C'] if vals['C'] != 0 else float('inf'),
                'display': 'R = τ / C',
            },
            {
                'solve_for': 'C',
                'inputs': ['τ', 'R'],
                'expression': lambda vals: vals['τ'] / vals['R'] if vals['R'] != 0 else float('inf'),
                'display': 'C = τ / R',
            },
            {
                'solve_for': 't63',
                'inputs': ['R', 'C'],
                'expression': lambda vals: vals['R'] * vals['C'],
                'display': 't(63.2%) = τ = R × C',
            },
            {
                'solve_for': 't99',
                'inputs': ['R', 'C'],
                'expression': lambda vals: 5.0 * vals['R'] * vals['C'],
                'display': 't(≈100%) = 5τ = 5 × R × C',
            },
        ],
    },

    # 12. Reactancia inductiva ──────────────────────────────────────────────
    'inductor_reactance': {
        'name': 'Reactancia Inductiva',
        'icon': '🧲',
        'variables': [
            {'symbol': 'XL', 'name': 'Reactancia Inductiva', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'f', 'name': 'Frecuencia', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'L', 'name': 'Inductancia', 'unit': 'H', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'XL',
                'inputs': ['f', 'L'],
                'expression': lambda vals: 2.0 * math.pi * vals['f'] * vals['L'],
                'display': 'XL = 2πfL',
            },
            {
                'solve_for': 'f',
                'inputs': ['XL', 'L'],
                'expression': lambda vals: vals['XL'] / (2.0 * math.pi * vals['L']) if vals['L'] != 0 else float('inf'),
                'display': 'f = XL / (2πL)',
            },
            {
                'solve_for': 'L',
                'inputs': ['XL', 'f'],
                'expression': lambda vals: vals['XL'] / (2.0 * math.pi * vals['f']) if vals['f'] != 0 else float('inf'),
                'display': 'L = XL / (2πf)',
            },
        ],
    },

    # 13. Inductores en serie ───────────────────────────────────────────────
    'inductors_series': {
        'name': 'Inductores en Serie',
        'icon': '🔗',
        'list_input': True,
        'min_inputs': 2,
        'max_inputs': 10,
        'input_symbol': 'L',
        'input_name': 'Inductancia',
        'input_unit': 'H',
        'variables': [
            {'symbol': 'Lt', 'name': 'Inductancia Total', 'unit': 'H', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Lt',
                'inputs': ['L_list'],
                'expression': lambda vals: sum(vals['L_list']),
                'display': 'Lt = L1 + L2 + … + Ln',
            },
        ],
    },

    # 14. Inductores en paralelo ────────────────────────────────────────────
    'inductors_parallel': {
        'name': 'Inductores en Paralelo',
        'icon': '🔀',
        'list_input': True,
        'min_inputs': 2,
        'max_inputs': 10,
        'input_symbol': 'L',
        'input_name': 'Inductancia',
        'input_unit': 'H',
        'variables': [
            {'symbol': 'Lt', 'name': 'Inductancia Total', 'unit': 'H', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Lt',
                'inputs': ['L_list'],
                'expression': lambda vals: (
                    1.0 / sum(1.0 / l_val for l_val in vals['L_list'] if l_val != 0)
                    if all(l_val != 0 for l_val in vals['L_list']) and len(vals['L_list']) > 0
                    else float('inf')
                ),
                'display': '1/Lt = 1/L1 + 1/L2 + … + 1/Ln',
            },
        ],
    },

    # 15. Energía del inductor ──────────────────────────────────────────────
    'inductor_energy': {
        'name': 'Energía del Inductor',
        'icon': '⚡',
        'variables': [
            {'symbol': 'E', 'name': 'Energía', 'unit': 'J', 'default': 0.0},
            {'symbol': 'L', 'name': 'Inductancia', 'unit': 'H', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente', 'unit': 'A', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'E',
                'inputs': ['L', 'I'],
                'expression': lambda vals: 0.5 * vals['L'] * vals['I'] ** 2,
                'display': 'E = ½LI²',
            },
            {
                'solve_for': 'L',
                'inputs': ['E', 'I'],
                'expression': lambda vals: 2.0 * vals['E'] / (vals['I'] ** 2) if vals['I'] != 0 else float('inf'),
                'display': 'L = 2E / I²',
            },
            {
                'solve_for': 'I',
                'inputs': ['E', 'L'],
                'expression': lambda vals: math.sqrt(2.0 * vals['E'] / vals['L']) if vals['L'] != 0 and (2.0 * vals['E'] / vals['L']) >= 0 else float('inf'),
                'display': 'I = √(2E / L)',
            },
        ],
    },

    # 16. Constante de tiempo RL ────────────────────────────────────────────
    'rl_time_constant': {
        'name': 'Constante de Tiempo RL',
        'icon': '⏱️',
        'variables': [
            {'symbol': 'τ', 'name': 'Constante de Tiempo', 'unit': 's', 'default': 0.0},
            {'symbol': 'L', 'name': 'Inductancia', 'unit': 'H', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'τ',
                'inputs': ['L', 'R'],
                'expression': lambda vals: vals['L'] / vals['R'] if vals['R'] != 0 else float('inf'),
                'display': 'τ = L / R',
            },
            {
                'solve_for': 'L',
                'inputs': ['τ', 'R'],
                'expression': lambda vals: vals['τ'] * vals['R'],
                'display': 'L = τ × R',
            },
            {
                'solve_for': 'R',
                'inputs': ['τ', 'L'],
                'expression': lambda vals: vals['L'] / vals['τ'] if vals['τ'] != 0 else float('inf'),
                'display': 'R = L / τ',
            },
        ],
    },

    # 17. Frecuencia de corte filtro RC ─────────────────────────────────────
    'rc_filter_cutoff': {
        'name': 'Frecuencia de Corte RC',
        'icon': '📉',
        'variables': [
            {'symbol': 'fc', 'name': 'Frecuencia de Corte', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
        ],
        'description': 'Aplica tanto a filtros pasa-bajos como pasa-altos RC',
        'formulas': [
            {
                'solve_for': 'fc',
                'inputs': ['R', 'C'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * vals['R'] * vals['C']) if (vals['R'] * vals['C']) != 0 else float('inf'),
                'display': 'fc = 1 / (2πRC)',
            },
            {
                'solve_for': 'R',
                'inputs': ['fc', 'C'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * vals['fc'] * vals['C']) if (vals['fc'] * vals['C']) != 0 else float('inf'),
                'display': 'R = 1 / (2πfcC)',
            },
            {
                'solve_for': 'C',
                'inputs': ['fc', 'R'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * vals['fc'] * vals['R']) if (vals['fc'] * vals['R']) != 0 else float('inf'),
                'display': 'C = 1 / (2πfcR)',
            },
        ],
    },

    # 18. Resonancia LC ─────────────────────────────────────────────────────
    'lc_resonance': {
        'name': 'Frecuencia de Resonancia LC',
        'icon': '🎵',
        'variables': [
            {'symbol': 'fr', 'name': 'Frecuencia de Resonancia', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'L', 'name': 'Inductancia', 'unit': 'H', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'fr',
                'inputs': ['L', 'C'],
                'expression': lambda vals: 1.0 / (2.0 * math.pi * math.sqrt(vals['L'] * vals['C'])) if (vals['L'] * vals['C']) > 0 else float('inf'),
                'display': 'fr = 1 / (2π√(LC))',
            },
            {
                'solve_for': 'L',
                'inputs': ['fr', 'C'],
                'expression': lambda vals: 1.0 / ((2.0 * math.pi * vals['fr']) ** 2 * vals['C']) if (vals['fr'] != 0 and vals['C'] != 0) else float('inf'),
                'display': 'L = 1 / ((2πfr)²C)',
            },
            {
                'solve_for': 'C',
                'inputs': ['fr', 'L'],
                'expression': lambda vals: 1.0 / ((2.0 * math.pi * vals['fr']) ** 2 * vals['L']) if (vals['fr'] != 0 and vals['L'] != 0) else float('inf'),
                'display': 'C = 1 / ((2πfr)²L)',
            },
        ],
    },

    # 19. Factor de calidad Q ───────────────────────────────────────────────
    'q_factor': {
        'name': 'Factor de Calidad Q',
        'icon': '📊',
        'variables': [
            {'symbol': 'Q', 'name': 'Factor Q', 'unit': '', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'L', 'name': 'Inductancia', 'unit': 'H', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
            {'symbol': 'fr', 'name': 'Frecuencia de Resonancia', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'BW', 'name': 'Ancho de Banda', 'unit': 'Hz', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Q',
                'inputs': ['R', 'L', 'C'],
                'expression': lambda vals: (1.0 / vals['R']) * math.sqrt(vals['L'] / vals['C']) if (vals['R'] != 0 and vals['C'] != 0 and vals['L'] / vals['C'] >= 0) else float('inf'),
                'display': 'Q = (1/R) × √(L/C)',
            },
            {
                'solve_for': 'Q',
                'inputs': ['fr', 'BW'],
                'expression': lambda vals: vals['fr'] / vals['BW'] if vals['BW'] != 0 else float('inf'),
                'display': 'Q = fr / BW',
            },
            {
                'solve_for': 'BW',
                'inputs': ['fr', 'Q'],
                'expression': lambda vals: vals['fr'] / vals['Q'] if vals['Q'] != 0 else float('inf'),
                'display': 'BW = fr / Q',
            },
        ],
    },

    # 20. Transformador ─────────────────────────────────────────────────────
    'transformer': {
        'name': 'Transformador',
        'icon': '🔄',
        'variables': [
            {'symbol': 'Vp', 'name': 'Voltaje Primario', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vs', 'name': 'Voltaje Secundario', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Np', 'name': 'Espiras Primario', 'unit': '', 'default': 0.0},
            {'symbol': 'Ns', 'name': 'Espiras Secundario', 'unit': '', 'default': 0.0},
            {'symbol': 'Ip', 'name': 'Corriente Primario', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Is', 'name': 'Corriente Secundario', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Zp', 'name': 'Impedancia Primario', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Zs', 'name': 'Impedancia Secundario', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vs',
                'inputs': ['Vp', 'Np', 'Ns'],
                'expression': lambda vals: vals['Vp'] * vals['Ns'] / vals['Np'] if vals['Np'] != 0 else float('inf'),
                'display': 'Vs = Vp × (Ns / Np)',
            },
            {
                'solve_for': 'Vp',
                'inputs': ['Vs', 'Np', 'Ns'],
                'expression': lambda vals: vals['Vs'] * vals['Np'] / vals['Ns'] if vals['Ns'] != 0 else float('inf'),
                'display': 'Vp = Vs × (Np / Ns)',
            },
            {
                'solve_for': 'Is',
                'inputs': ['Ip', 'Np', 'Ns'],
                'expression': lambda vals: vals['Ip'] * vals['Np'] / vals['Ns'] if vals['Ns'] != 0 else float('inf'),
                'display': 'Is = Ip × (Np / Ns)',
            },
            {
                'solve_for': 'Ip',
                'inputs': ['Is', 'Np', 'Ns'],
                'expression': lambda vals: vals['Is'] * vals['Ns'] / vals['Np'] if vals['Np'] != 0 else float('inf'),
                'display': 'Ip = Is × (Ns / Np)',
            },
            {
                'solve_for': 'Zp',
                'inputs': ['Zs', 'Np', 'Ns'],
                'expression': lambda vals: vals['Zs'] * (vals['Np'] / vals['Ns']) ** 2 if vals['Ns'] != 0 else float('inf'),
                'display': 'Zp = Zs × (Np / Ns)²',
            },
            {
                'solve_for': 'Zs',
                'inputs': ['Zp', 'Np', 'Ns'],
                'expression': lambda vals: vals['Zp'] * (vals['Ns'] / vals['Np']) ** 2 if vals['Np'] != 0 else float('inf'),
                'display': 'Zs = Zp × (Ns / Np)²',
            },
        ],
    },

    # 21. OpAmp Inversor ────────────────────────────────────────────────────
    'opamp_inverting': {
        'name': 'OpAmp Inversor',
        'icon': '🔻',
        'variables': [
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vin', 'name': 'Voltaje de Entrada', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Rf', 'name': 'Resistencia Realimentación', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Ri', 'name': 'Resistencia de Entrada', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'G', 'name': 'Ganancia', 'unit': '', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['Vin', 'Rf', 'Ri'],
                'expression': lambda vals: -vals['Vin'] * (vals['Rf'] / vals['Ri']) if vals['Ri'] != 0 else float('inf'),
                'display': 'Vout = −Vin × (Rf / Ri)',
            },
            {
                'solve_for': 'G',
                'inputs': ['Rf', 'Ri'],
                'expression': lambda vals: -(vals['Rf'] / vals['Ri']) if vals['Ri'] != 0 else float('inf'),
                'display': 'G = −Rf / Ri',
            },
            {
                'solve_for': 'Rf',
                'inputs': ['Vout', 'Vin', 'Ri'],
                'expression': lambda vals: abs(vals['Vout'] / vals['Vin']) * vals['Ri'] if vals['Vin'] != 0 else float('inf'),
                'display': 'Rf = |Vout / Vin| × Ri',
            },
            {
                'solve_for': 'Ri',
                'inputs': ['Vout', 'Vin', 'Rf'],
                'expression': lambda vals: abs(vals['Vin'] / vals['Vout']) * vals['Rf'] if vals['Vout'] != 0 else float('inf'),
                'display': 'Ri = |Vin / Vout| × Rf',
            },
        ],
    },

    # 22. OpAmp No Inversor ─────────────────────────────────────────────────
    'opamp_noninverting': {
        'name': 'OpAmp No Inversor',
        'icon': '🔺',
        'variables': [
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vin', 'name': 'Voltaje de Entrada', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Rf', 'name': 'Resistencia Realimentación', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Ri', 'name': 'Resistencia de Entrada', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'G', 'name': 'Ganancia', 'unit': '', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['Vin', 'Rf', 'Ri'],
                'expression': lambda vals: vals['Vin'] * (1.0 + vals['Rf'] / vals['Ri']) if vals['Ri'] != 0 else float('inf'),
                'display': 'Vout = Vin × (1 + Rf / Ri)',
            },
            {
                'solve_for': 'G',
                'inputs': ['Rf', 'Ri'],
                'expression': lambda vals: 1.0 + vals['Rf'] / vals['Ri'] if vals['Ri'] != 0 else float('inf'),
                'display': 'G = 1 + Rf / Ri',
            },
            {
                'solve_for': 'Rf',
                'inputs': ['Vout', 'Vin', 'Ri'],
                'expression': lambda vals: (vals['Vout'] / vals['Vin'] - 1.0) * vals['Ri'] if vals['Vin'] != 0 else float('inf'),
                'display': 'Rf = (Vout/Vin − 1) × Ri',
            },
            {
                'solve_for': 'Ri',
                'inputs': ['Vout', 'Vin', 'Rf'],
                'expression': lambda vals: vals['Rf'] / (vals['Vout'] / vals['Vin'] - 1.0) if (vals['Vin'] != 0 and (vals['Vout'] / vals['Vin'] - 1.0) != 0) else float('inf'),
                'display': 'Ri = Rf / (Vout/Vin − 1)',
            },
        ],
    },

    # 23. OpAmp Sumador ─────────────────────────────────────────────────────
    'opamp_summing': {
        'name': 'OpAmp Sumador Inversor',
        'icon': '➕',
        'variables': [
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'V1', 'name': 'Voltaje Entrada 1', 'unit': 'V', 'default': 0.0},
            {'symbol': 'V2', 'name': 'Voltaje Entrada 2', 'unit': 'V', 'default': 0.0},
            {'symbol': 'V3', 'name': 'Voltaje Entrada 3', 'unit': 'V', 'default': 0.0},
            {'symbol': 'R1', 'name': 'Resistencia Entrada 1', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'R2', 'name': 'Resistencia Entrada 2', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'R3', 'name': 'Resistencia Entrada 3', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Rf', 'name': 'Resistencia Realimentación', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['V1', 'R1', 'V2', 'R2', 'Rf'],
                'expression': lambda vals: -(
                    (vals['V1'] / vals['R1'] if vals['R1'] != 0 else 0) +
                    (vals['V2'] / vals['R2'] if vals['R2'] != 0 else 0)
                ) * vals['Rf'],
                'display': 'Vout = −(V1/R1 + V2/R2) × Rf',
            },
            {
                'solve_for': 'Vout',
                'inputs': ['V1', 'R1', 'V2', 'R2', 'V3', 'R3', 'Rf'],
                'expression': lambda vals: -(
                    (vals['V1'] / vals['R1'] if vals['R1'] != 0 else 0) +
                    (vals['V2'] / vals['R2'] if vals['R2'] != 0 else 0) +
                    (vals['V3'] / vals['R3'] if vals['R3'] != 0 else 0)
                ) * vals['Rf'],
                'display': 'Vout = −(V1/R1 + V2/R2 + V3/R3) × Rf',
            },
        ],
    },

    # 24. OpAmp Diferencial ─────────────────────────────────────────────────
    'opamp_differential': {
        'name': 'OpAmp Diferencial',
        'icon': '↔️',
        'variables': [
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'V1', 'name': 'Voltaje Entrada 1', 'unit': 'V', 'default': 0.0},
            {'symbol': 'V2', 'name': 'Voltaje Entrada 2', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Rf', 'name': 'Resistencia Realimentación', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Ri', 'name': 'Resistencia de Entrada', 'unit': 'Ω', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['V1', 'V2', 'Rf', 'Ri'],
                'expression': lambda vals: (vals['V2'] - vals['V1']) * (vals['Rf'] / vals['Ri']) if vals['Ri'] != 0 else float('inf'),
                'display': 'Vout = (V2 − V1) × (Rf / Ri)',
            },
            {
                'solve_for': 'Rf',
                'inputs': ['Vout', 'V1', 'V2', 'Ri'],
                'expression': lambda vals: vals['Vout'] * vals['Ri'] / (vals['V2'] - vals['V1']) if (vals['V2'] - vals['V1']) != 0 else float('inf'),
                'display': 'Rf = Vout × Ri / (V2 − V1)',
            },
        ],
    },

    # 25. Polarización BJT ──────────────────────────────────────────────────
    'bjt_bias': {
        'name': 'Polarización BJT',
        'icon': '🔲',
        'variables': [
            {'symbol': 'Vcc', 'name': 'Voltaje de Alimentación', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Rc', 'name': 'Resistencia de Colector', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Rb', 'name': 'Resistencia de Base', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'β', 'name': 'Ganancia de Corriente (hFE)', 'unit': '', 'default': 0.0},
            {'symbol': 'Vbe', 'name': 'Voltaje Base-Emisor', 'unit': 'V', 'default': 0.7},
            {'symbol': 'Ib', 'name': 'Corriente de Base', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Ic', 'name': 'Corriente de Colector', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Vce', 'name': 'Voltaje Colector-Emisor', 'unit': 'V', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Ib',
                'inputs': ['Vcc', 'Vbe', 'Rb'],
                'expression': lambda vals: (vals['Vcc'] - vals['Vbe']) / vals['Rb'] if vals['Rb'] != 0 else float('inf'),
                'display': 'Ib = (Vcc − Vbe) / Rb',
            },
            {
                'solve_for': 'Ic',
                'inputs': ['β', 'Ib'],
                'expression': lambda vals: vals['β'] * vals['Ib'],
                'display': 'Ic = β × Ib',
            },
            {
                'solve_for': 'Ic',
                'inputs': ['Vcc', 'Vbe', 'Rb', 'β'],
                'expression': lambda vals: vals['β'] * (vals['Vcc'] - vals['Vbe']) / vals['Rb'] if vals['Rb'] != 0 else float('inf'),
                'display': 'Ic = β × (Vcc − Vbe) / Rb',
            },
            {
                'solve_for': 'Vce',
                'inputs': ['Vcc', 'Ic', 'Rc'],
                'expression': lambda vals: vals['Vcc'] - vals['Ic'] * vals['Rc'],
                'display': 'Vce = Vcc − Ic × Rc',
            },
            {
                'solve_for': 'Rb',
                'inputs': ['Vcc', 'Vbe', 'Ib'],
                'expression': lambda vals: (vals['Vcc'] - vals['Vbe']) / vals['Ib'] if vals['Ib'] != 0 else float('inf'),
                'display': 'Rb = (Vcc − Vbe) / Ib',
            },
        ],
    },

    # 26. Resistencia de cable ──────────────────────────────────────────────
    'wire_resistance': {
        'name': 'Resistencia de Cable',
        'icon': '🔌',
        'variables': [
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'ρ', 'name': 'Resistividad', 'unit': 'Ω·m', 'default': 1.68e-8},  # cobre a 20°C
            {'symbol': 'L', 'name': 'Longitud', 'unit': 'm', 'default': 0.0},
            {'symbol': 'A', 'name': 'Sección Transversal', 'unit': 'm²', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'R',
                'inputs': ['ρ', 'L', 'A'],
                'expression': lambda vals: vals['ρ'] * vals['L'] / vals['A'] if vals['A'] != 0 else float('inf'),
                'display': 'R = ρ × L / A',
            },
            {
                'solve_for': 'L',
                'inputs': ['R', 'ρ', 'A'],
                'expression': lambda vals: vals['R'] * vals['A'] / vals['ρ'] if vals['ρ'] != 0 else float('inf'),
                'display': 'L = R × A / ρ',
            },
            {
                'solve_for': 'A',
                'inputs': ['ρ', 'L', 'R'],
                'expression': lambda vals: vals['ρ'] * vals['L'] / vals['R'] if vals['R'] != 0 else float('inf'),
                'display': 'A = ρ × L / R',
            },
        ],
    },

    # 27. Caída de voltaje en cable ─────────────────────────────────────────
    'voltage_drop_cable': {
        'name': 'Caída de Voltaje en Cable',
        'icon': '📉',
        'variables': [
            {'symbol': 'Vdrop', 'name': 'Caída de Voltaje', 'unit': 'V', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente', 'unit': 'A', 'default': 0.0},
            {'symbol': 'R_cable', 'name': 'Resistencia del Cable', 'unit': 'Ω', 'default': 0.0},
        ],
        'description': 'Ida y vuelta (round trip)',
        'formulas': [
            {
                'solve_for': 'Vdrop',
                'inputs': ['I', 'R_cable'],
                'expression': lambda vals: 2.0 * vals['I'] * vals['R_cable'],
                'display': 'Vdrop = 2 × I × R_cable',
            },
            {
                'solve_for': 'I',
                'inputs': ['Vdrop', 'R_cable'],
                'expression': lambda vals: vals['Vdrop'] / (2.0 * vals['R_cable']) if vals['R_cable'] != 0 else float('inf'),
                'display': 'I = Vdrop / (2 × R_cable)',
            },
            {
                'solve_for': 'R_cable',
                'inputs': ['Vdrop', 'I'],
                'expression': lambda vals: vals['Vdrop'] / (2.0 * vals['I']) if vals['I'] != 0 else float('inf'),
                'display': 'R_cable = Vdrop / (2 × I)',
            },
        ],
    },


    # 29. Conversión Rectangular / Polar ─────────────────────────────────────
    'rectangular_polar': {
        'name': 'Conversión Rectangular / Polar',
        'icon': '🧭',
        'variables': [
            {'symbol': 'X', 'name': 'Parte Real', 'unit': '', 'default': 0.0},
            {'symbol': 'Y', 'name': 'Parte Imaginaria', 'unit': '', 'default': 0.0},
            {'symbol': 'M', 'name': 'Módulo (Magnitud)', 'unit': '', 'default': 0.0},
            {'symbol': 'A', 'name': 'Ángulo (Fase)', 'unit': '°', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'M',
                'inputs': ['X', 'Y'],
                'expression': lambda vals: math.sqrt(vals['X']**2 + vals['Y']**2),
                'display': 'M = √(X² + Y²)',
            },
            {
                'solve_for': 'A',
                'inputs': ['X', 'Y'],
                'expression': lambda vals: math.degrees(math.atan2(vals['Y'], vals['X'])),
                'display': 'A = arctan(Y/X)',
            },
            {
                'solve_for': 'X',
                'inputs': ['M', 'A'],
                'expression': lambda vals: vals['M'] * math.cos(math.radians(vals['A'])),
                'display': 'X = M × cos(A)',
            },
            {
                'solve_for': 'Y',
                'inputs': ['M', 'A'],
                'expression': lambda vals: vals['M'] * math.sin(math.radians(vals['A'])),
                'display': 'Y = M × sin(A)',
            },
        ],
    },

    # 30. Filtro Pasa Banda / Rechaza Banda ──────────────────────────────────
    'bandpass_filter': {
        'name': 'Filtro Pasa Banda',
        'icon': '🎛️',
        'variables': [
            {'symbol': 'fL', 'name': 'Frecuencia de Corte Inf.', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'fH', 'name': 'Frecuencia de Corte Sup.', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'fr', 'name': 'Frecuencia Central', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'BW', 'name': 'Ancho de Banda', 'unit': 'Hz', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'BW',
                'inputs': ['fH', 'fL'],
                'expression': lambda vals: vals['fH'] - vals['fL'],
                'display': 'BW = fH − fL',
            },
            {
                'solve_for': 'fr',
                'inputs': ['fH', 'fL'],
                'expression': lambda vals: math.sqrt(vals['fH'] * vals['fL']) if (vals['fH']*vals['fL'] >= 0) else float('inf'),
                'display': 'fr = √(fH × fL)',
            },
            {
                'solve_for': 'fH',
                'inputs': ['BW', 'fL'],
                'expression': lambda vals: vals['fL'] + vals['BW'],
                'display': 'fH = fL + BW',
            },
            {
                'solve_for': 'fL',
                'inputs': ['fH', 'BW'],
                'expression': lambda vals: vals['fH'] - vals['BW'],
                'display': 'fL = fH − BW',
            },
        ],
    },

    # 31. Ganancia de Tensión y Corriente (dB) ──────────────────────────────
    'gain_calc': {
        'name': 'Ganancia (dB)',
        'icon': '📈',
        'variables': [
            {'symbol': 'Vin', 'name': 'Voltaje de Entrada', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Av_dB', 'name': 'Ganancia en Tensión', 'unit': 'dB', 'default': 0.0},
            {'symbol': 'Iin', 'name': 'Corriente de Entrada', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Iout', 'name': 'Corriente de Salida', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Ai_dB', 'name': 'Ganancia en Corriente', 'unit': 'dB', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Av_dB',
                'inputs': ['Vout', 'Vin'],
                'expression': lambda vals: 20 * math.log10(abs(vals['Vout'] / vals['Vin'])) if vals['Vin'] != 0 and vals['Vout'] != 0 else float('-inf'),
                'display': 'Av(dB) = 20 × log10(Vout / Vin)',
            },
            {
                'solve_for': 'Vout',
                'inputs': ['Av_dB', 'Vin'],
                'expression': lambda vals: vals['Vin'] * (10 ** (vals['Av_dB'] / 20.0)),
                'display': 'Vout = Vin × 10^(Av/20)',
            },
            {
                'solve_for': 'Ai_dB',
                'inputs': ['Iout', 'Iin'],
                'expression': lambda vals: 20 * math.log10(abs(vals['Iout'] / vals['Iin'])) if vals['Iin'] != 0 and vals['Iout'] != 0 else float('-inf'),
                'display': 'Ai(dB) = 20 × log10(Iout / Iin)',
            },
            {
                'solve_for': 'Iout',
                'inputs': ['Ai_dB', 'Iin'],
                'expression': lambda vals: vals['Iin'] * (10 ** (vals['Ai_dB'] / 20.0)),
                'display': 'Iout = Iin × 10^(Ai/20)',
            },
        ],
    },

    # 32. Sumatoria AC + DC (RMS) ───────────────────────────────────────────
    'ac_dc_sum': {
        'name': 'Sumatoria AC + DC',
        'icon': '〽️',
        'variables': [
            {'symbol': 'Vdc', 'name': 'Componente DC', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vac', 'name': 'Componente AC (RMS)', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vrms', 'name': 'Voltaje Total (RMS)', 'unit': 'V', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vrms',
                'inputs': ['Vdc', 'Vac'],
                'expression': lambda vals: math.sqrt(vals['Vdc']**2 + vals['Vac']**2),
                'display': 'Vrms = √(Vdc² + Vac²)',
            },
            {
                'solve_for': 'Vac',
                'inputs': ['Vrms', 'Vdc'],
                'expression': lambda vals: math.sqrt(vals['Vrms']**2 - vals['Vdc']**2) if (vals['Vrms']**2 >= vals['Vdc']**2) else 0.0,
                'display': 'Vac = √(Vrms² − Vdc²)',
            },
        ],
    },

    # 33. Potencia dBm ──────────────────────────────────────────────────────
    'dbm_calc': {
        'name': 'Potencia dBm y Referencia',
        'icon': '📡',
        'variables': [
            {'symbol': 'P_mW', 'name': 'Potencia', 'unit': 'mW', 'default': 1.0},
            {'symbol': 'dBm', 'name': 'Nivel de Potencia', 'unit': 'dBm', 'default': 0.0},
            {'symbol': 'Vrms', 'name': 'Voltaje (RMS)', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Rref', 'name': 'Resistencia de Referencia', 'unit': 'Ω', 'default': 50.0},
        ],
        'formulas': [
            {
                'solve_for': 'dBm',
                'inputs': ['P_mW'],
                'expression': lambda vals: 10 * math.log10(vals['P_mW']) if vals['P_mW'] > 0 else float('-inf'),
                'display': 'dBm = 10 × log10(P(mW))',
            },
            {
                'solve_for': 'P_mW',
                'inputs': ['dBm'],
                'expression': lambda vals: 10 ** (vals['dBm'] / 10.0),
                'display': 'P(mW) = 10^(dBm / 10)',
            },
            {
                'solve_for': 'P_mW',
                'inputs': ['Vrms', 'Rref'],
                'expression': lambda vals: ((vals['Vrms']**2) / vals['Rref']) * 1000.0 if vals['Rref'] != 0 else float('inf'),
                'display': 'P(mW) = (Vrms² / Rref) × 1000',
            },
            {
                'solve_for': 'Vrms',
                'inputs': ['P_mW', 'Rref'],
                'expression': lambda vals: math.sqrt((vals['P_mW'] / 1000.0) * vals['Rref']) if (vals['P_mW'] * vals['Rref']) >= 0 else float('inf'),
                'display': 'Vrms = √((P(mW)/1000) × Rref)',
            },
            {
                'solve_for': 'dBm',
                'inputs': ['Vrms', 'Rref'],
                'expression': lambda vals: 10 * math.log10(((vals['Vrms']**2) / vals['Rref']) * 1000.0) if (vals['Rref'] != 0 and vals['Vrms'] != 0) else float('-inf'),
                'display': 'dBm = 10 × log10((Vrms² / Rref) × 1000)',
            },
        ],
    },


    # 34. Teorema de Thévenin ───────────────────────────────────────────────
    'thevenin_theorem': {
        'name': 'Teorema de Thévenin (Carga RL)',
        'icon': '🔋',
        'variables': [
            {'symbol': 'Vth', 'name': 'Voltaje de Thévenin', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Rth', 'name': 'Resistencia de Thévenin', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'RL', 'name': 'Resistencia de Carga', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'IL', 'name': 'Corriente en Carga', 'unit': 'A', 'default': 0.0},
            {'symbol': 'VL', 'name': 'Voltaje en Carga', 'unit': 'V', 'default': 0.0},
            {'symbol': 'PL', 'name': 'Potencia en Carga', 'unit': 'W', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'IL',
                'inputs': ['Vth', 'Rth', 'RL'],
                'expression': lambda vals: vals['Vth'] / (vals['Rth'] + vals['RL']) if (vals['Rth'] + vals['RL']) != 0 else float('inf'),
                'display': 'IL = Vth / (Rth + RL)',
            },
            {
                'solve_for': 'VL',
                'inputs': ['Vth', 'Rth', 'RL'],
                'expression': lambda vals: vals['Vth'] * vals['RL'] / (vals['Rth'] + vals['RL']) if (vals['Rth'] + vals['RL']) != 0 else float('inf'),
                'display': 'VL = Vth × RL / (Rth + RL)',
            },
            {
                'solve_for': 'PL',
                'inputs': ['IL', 'VL'],
                'expression': lambda vals: vals['IL'] * vals['VL'],
                'display': 'PL = IL × VL',
            },
            {
                'solve_for': 'Vth',
                'inputs': ['VL', 'Rth', 'RL'],
                'expression': lambda vals: vals['VL'] * (vals['Rth'] + vals['RL']) / vals['RL'] if vals['RL'] != 0 else float('inf'),
                'display': 'Vth = VL × (Rth + RL) / RL',
            },
            {
                'solve_for': 'RL',
                'inputs': ['Vth', 'Rth', 'VL'],
                'expression': lambda vals: vals['Rth'] / (vals['Vth'] / vals['VL'] - 1.0) if (vals['VL'] != 0 and vals['Vth'] != vals['VL']) else float('inf'),
                'display': 'RL = Rth / (Vth/VL − 1)',
            },
        ],
    },

    # 35. Teorema de Norton ─────────────────────────────────────────────────
    'norton_theorem': {
        'name': 'Teorema de Norton (Carga RL)',
        'icon': '⚡',
        'variables': [
            {'symbol': 'In', 'name': 'Corriente de Norton', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Rn', 'name': 'Resistencia de Norton', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'RL', 'name': 'Resistencia de Carga', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'IL', 'name': 'Corriente en Carga', 'unit': 'A', 'default': 0.0},
            {'symbol': 'VL', 'name': 'Voltaje en Carga', 'unit': 'V', 'default': 0.0},
            {'symbol': 'PL', 'name': 'Potencia en Carga', 'unit': 'W', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'IL',
                'inputs': ['In', 'Rn', 'RL'],
                'expression': lambda vals: vals['In'] * vals['Rn'] / (vals['Rn'] + vals['RL']) if (vals['Rn'] + vals['RL']) != 0 else float('inf'),
                'display': 'IL = In × Rn / (Rn + RL)',
            },
            {
                'solve_for': 'VL',
                'inputs': ['In', 'Rn', 'RL'],
                'expression': lambda vals: (vals['In'] * vals['Rn'] / (vals['Rn'] + vals['RL'])) * vals['RL'] if (vals['Rn'] + vals['RL']) != 0 else float('inf'),
                'display': 'VL = IL × RL',
            },
            {
                'solve_for': 'PL',
                'inputs': ['IL', 'VL'],
                'expression': lambda vals: vals['IL'] * vals['VL'],
                'display': 'PL = IL × VL',
            },
            {
                'solve_for': 'In',
                'inputs': ['IL', 'Rn', 'RL'],
                'expression': lambda vals: vals['IL'] * (vals['Rn'] + vals['RL']) / vals['Rn'] if vals['Rn'] != 0 else float('inf'),
                'display': 'In = IL × (Rn + RL) / Rn',
            },
        ],
    },

    # 36. Filtro PI (LC Pasa Bajos / EMI) ───────────────────────────────────
    'pi_filter_emi': {
        'name': 'Filtro PI Pasa Bajos (EMI)',
        'icon': '🌉',
        'variables': [
            {'symbol': 'Z0', 'name': 'Impedancia Característica', 'unit': 'Ω', 'default': 50.0},
            {'symbol': 'fc', 'name': 'Frecuencia de Corte', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'L', 'name': 'Inductancia Serie', 'unit': 'H', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia Paralelo (C1=C2)', 'unit': 'F', 'default': 0.0},
        ],
        'description': 'Diseño de filtro Pi simétrico (C-L-C) adaptado a impedancia Z0',
        'formulas': [
            {
                'solve_for': 'fc',
                'inputs': ['L', 'C'],
                'expression': lambda vals: 1.0 / (math.pi * math.sqrt(vals['L'] * vals['C'])) if (vals['L'] * vals['C'] > 0) else float('inf'),
                'display': 'fc = 1 / (π × √(L × C))',
            },
            {
                'solve_for': 'L',
                'inputs': ['Z0', 'fc'],
                'expression': lambda vals: vals['Z0'] / (math.pi * vals['fc']) if vals['fc'] != 0 else float('inf'),
                'display': 'L = Z0 / (π × fc)',
            },
            {
                'solve_for': 'C',
                'inputs': ['Z0', 'fc'],
                'expression': lambda vals: 1.0 / (math.pi * vals['Z0'] * vals['fc']) if (vals['Z0'] != 0 and vals['fc'] != 0) else float('inf'),
                'display': 'C = 1 / (π × Z0 × fc)',
            },
            {
                'solve_for': 'Z0',
                'inputs': ['L', 'C'],
                'expression': lambda vals: math.sqrt(vals['L'] / vals['C']) if vals['C'] != 0 else float('inf'),
                'display': 'Z0 = √(L / C)',
            },
        ],
    },

    # 28. Sección mínima de cable ───────────────────────────────────────────
    'min_wire_section': {
        'name': 'Sección Mínima de Cable',
        'icon': '📐',
        'variables': [
            {'symbol': 'A', 'name': 'Sección Transversal', 'unit': 'm²', 'default': 0.0},
            {'symbol': 'ρ', 'name': 'Resistividad', 'unit': 'Ω·m', 'default': 1.68e-8},  # cobre a 20°C
            {'symbol': 'L', 'name': 'Longitud', 'unit': 'm', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente', 'unit': 'A', 'default': 0.0},
            {'symbol': 'Vdrop_max', 'name': 'Caída de Voltaje Máxima', 'unit': 'V', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'A',
                'inputs': ['ρ', 'L', 'I', 'Vdrop_max'],
                'expression': lambda vals: (2.0 * vals['ρ'] * vals['L'] * vals['I']) / vals['Vdrop_max'] if vals['Vdrop_max'] != 0 else float('inf'),
                'display': 'A = 2 × ρ × L × I / Vdrop_max',
            },
            {
                'solve_for': 'Vdrop_max',
                'inputs': ['ρ', 'L', 'I', 'A'],
                'expression': lambda vals: (2.0 * vals['ρ'] * vals['L'] * vals['I']) / vals['A'] if vals['A'] != 0 else float('inf'),
                'display': 'Vdrop_max = 2 × ρ × L × I / A',
            },
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# DIGITAL_FORMULAS
# ──────────────────────────────────────────────────────────────────────────────

DIGITAL_FORMULAS = {

    # 1. Compuertas lógicas ─────────────────────────────────────────────────
    'logic_gates': {
        'name': 'Compuertas Lógicas',
        'icon': '🔲',
        'type': 'truth_table',
        'description': 'Tablas de verdad para compuertas lógicas básicas (2 entradas)',
        'gates': {
            'AND': {
                'symbol': '∧',
                'description': 'Salida 1 solo si ambas entradas son 1',
                'truth_table': [
                    {'A': 0, 'B': 0, 'Y': 0},
                    {'A': 0, 'B': 1, 'Y': 0},
                    {'A': 1, 'B': 0, 'Y': 0},
                    {'A': 1, 'B': 1, 'Y': 1},
                ],
                'expression': lambda a, b: int(a and b),
            },
            'OR': {
                'symbol': '∨',
                'description': 'Salida 1 si al menos una entrada es 1',
                'truth_table': [
                    {'A': 0, 'B': 0, 'Y': 0},
                    {'A': 0, 'B': 1, 'Y': 1},
                    {'A': 1, 'B': 0, 'Y': 1},
                    {'A': 1, 'B': 1, 'Y': 1},
                ],
                'expression': lambda a, b: int(a or b),
            },
            'NAND': {
                'symbol': '⊼',
                'description': 'Salida 0 solo si ambas entradas son 1',
                'truth_table': [
                    {'A': 0, 'B': 0, 'Y': 1},
                    {'A': 0, 'B': 1, 'Y': 1},
                    {'A': 1, 'B': 0, 'Y': 1},
                    {'A': 1, 'B': 1, 'Y': 0},
                ],
                'expression': lambda a, b: int(not (a and b)),
            },
            'NOR': {
                'symbol': '⊽',
                'description': 'Salida 1 solo si ambas entradas son 0',
                'truth_table': [
                    {'A': 0, 'B': 0, 'Y': 1},
                    {'A': 0, 'B': 1, 'Y': 0},
                    {'A': 1, 'B': 0, 'Y': 0},
                    {'A': 1, 'B': 1, 'Y': 0},
                ],
                'expression': lambda a, b: int(not (a or b)),
            },
            'XOR': {
                'symbol': '⊕',
                'description': 'Salida 1 si las entradas son diferentes',
                'truth_table': [
                    {'A': 0, 'B': 0, 'Y': 0},
                    {'A': 0, 'B': 1, 'Y': 1},
                    {'A': 1, 'B': 0, 'Y': 1},
                    {'A': 1, 'B': 1, 'Y': 0},
                ],
                'expression': lambda a, b: int(a ^ b),
            },
            'XNOR': {
                'symbol': '⊙',
                'description': 'Salida 1 si las entradas son iguales',
                'truth_table': [
                    {'A': 0, 'B': 0, 'Y': 1},
                    {'A': 0, 'B': 1, 'Y': 0},
                    {'A': 1, 'B': 0, 'Y': 0},
                    {'A': 1, 'B': 1, 'Y': 1},
                ],
                'expression': lambda a, b: int(not (a ^ b)),
            },
            'NOT': {
                'symbol': '¬',
                'description': 'Invierte la entrada',
                'truth_table': [
                    {'A': 0, 'Y': 1},
                    {'A': 1, 'Y': 0},
                ],
                'expression': lambda a: int(not a),
            },
        },
    },

    # 2. Timer 555 Astable ──────────────────────────────────────────────────
    'timer_555_astable': {
        'name': 'Timer 555 Astable',
        'icon': '🔁',
        'variables': [
            {'symbol': 'R1', 'name': 'Resistencia R1', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'R2', 'name': 'Resistencia R2', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
            {'symbol': 'f', 'name': 'Frecuencia', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'T', 'name': 'Período Total', 'unit': 's', 'default': 0.0},
            {'symbol': 'T_high', 'name': 'Tiempo en Alto', 'unit': 's', 'default': 0.0},
            {'symbol': 'T_low', 'name': 'Tiempo en Bajo', 'unit': 's', 'default': 0.0},
            {'symbol': 'duty', 'name': 'Ciclo de Trabajo', 'unit': '%', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'f',
                'inputs': ['R1', 'R2', 'C'],
                'expression': lambda vals: 1.44 / ((vals['R1'] + 2.0 * vals['R2']) * vals['C']) if ((vals['R1'] + 2.0 * vals['R2']) * vals['C']) != 0 else float('inf'),
                'display': 'f = 1.44 / ((R1 + 2R2) × C)',
            },
            {
                'solve_for': 'T',
                'inputs': ['R1', 'R2', 'C'],
                'expression': lambda vals: 0.693 * (vals['R1'] + 2.0 * vals['R2']) * vals['C'],
                'display': 'T = 0.693 × (R1 + 2R2) × C',
            },
            {
                'solve_for': 'T_high',
                'inputs': ['R1', 'R2', 'C'],
                'expression': lambda vals: 0.693 * (vals['R1'] + vals['R2']) * vals['C'],
                'display': 'T_high = 0.693 × (R1 + R2) × C',
            },
            {
                'solve_for': 'T_low',
                'inputs': ['R2', 'C'],
                'expression': lambda vals: 0.693 * vals['R2'] * vals['C'],
                'display': 'T_low = 0.693 × R2 × C',
            },
            {
                'solve_for': 'duty',
                'inputs': ['R1', 'R2'],
                'expression': lambda vals: ((vals['R1'] + vals['R2']) / (vals['R1'] + 2.0 * vals['R2'])) * 100.0 if (vals['R1'] + 2.0 * vals['R2']) != 0 else float('inf'),
                'display': 'Duty = (R1 + R2) / (R1 + 2R2) × 100%',
            },
        ],
    },

    # 3. Timer 555 Monoestable ──────────────────────────────────────────────
    'timer_555_monostable': {
        'name': 'Timer 555 Monoestable',
        'icon': '⏲️',
        'variables': [
            {'symbol': 'T', 'name': 'Duración del Pulso', 'unit': 's', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'C', 'name': 'Capacitancia', 'unit': 'F', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'T',
                'inputs': ['R', 'C'],
                'expression': lambda vals: 1.1 * vals['R'] * vals['C'],
                'display': 'T = 1.1 × R × C',
            },
            {
                'solve_for': 'R',
                'inputs': ['T', 'C'],
                'expression': lambda vals: vals['T'] / (1.1 * vals['C']) if vals['C'] != 0 else float('inf'),
                'display': 'R = T / (1.1 × C)',
            },
            {
                'solve_for': 'C',
                'inputs': ['T', 'R'],
                'expression': lambda vals: vals['T'] / (1.1 * vals['R']) if vals['R'] != 0 else float('inf'),
                'display': 'C = T / (1.1 × R)',
            },
        ],
    },

    # 4. Frecuencia y Período ───────────────────────────────────────────────
    'frequency_period': {
        'name': 'Frecuencia y Período',
        'icon': '🔄',
        'variables': [
            {'symbol': 'f', 'name': 'Frecuencia', 'unit': 'Hz', 'default': 0.0},
            {'symbol': 'T', 'name': 'Período', 'unit': 's', 'default': 0.0},
            {'symbol': 'ω', 'name': 'Velocidad Angular', 'unit': 'rad/s', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'f',
                'inputs': ['T'],
                'expression': lambda vals: 1.0 / vals['T'] if vals['T'] != 0 else float('inf'),
                'display': 'f = 1 / T',
            },
            {
                'solve_for': 'T',
                'inputs': ['f'],
                'expression': lambda vals: 1.0 / vals['f'] if vals['f'] != 0 else float('inf'),
                'display': 'T = 1 / f',
            },
            {
                'solve_for': 'ω',
                'inputs': ['f'],
                'expression': lambda vals: 2.0 * math.pi * vals['f'],
                'display': 'ω = 2πf',
            },
            {
                'solve_for': 'f',
                'inputs': ['ω'],
                'expression': lambda vals: vals['ω'] / (2.0 * math.pi) if math.pi != 0 else float('inf'),
                'display': 'f = ω / (2π)',
            },
        ],
    },

    # 5. Registro de desplazamiento ─────────────────────────────────────────
    'shift_register': {
        'name': 'Registro de Desplazamiento',
        'icon': '📝',
        'variables': [
            {'symbol': 'n', 'name': 'Número de Bits', 'unit': 'bits', 'default': 0.0},
            {'symbol': 'states', 'name': 'Número de Estados', 'unit': '', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'states',
                'inputs': ['n'],
                'expression': lambda vals: 2 ** int(vals['n']) if vals['n'] >= 0 else 0,
                'display': 'Estados = 2ⁿ',
            },
            {
                'solve_for': 'n',
                'inputs': ['states'],
                'expression': lambda vals: math.log2(vals['states']) if vals['states'] > 0 else float('inf'),
                'display': 'n = log₂(Estados)',
            },
        ],
    },

    # 6. Salidas de decodificador ───────────────────────────────────────────
    'decoder_outputs': {
        'name': 'Decodificador',
        'icon': '🔢',
        'variables': [
            {'symbol': 'n', 'name': 'Número de Entradas', 'unit': 'bits', 'default': 0.0},
            {'symbol': 'outputs', 'name': 'Número de Salidas', 'unit': '', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'outputs',
                'inputs': ['n'],
                'expression': lambda vals: 2 ** int(vals['n']) if vals['n'] >= 0 else 0,
                'display': 'Salidas = 2ⁿ',
            },
            {
                'solve_for': 'n',
                'inputs': ['outputs'],
                'expression': lambda vals: math.log2(vals['outputs']) if vals['outputs'] > 0 else float('inf'),
                'display': 'n = log₂(Salidas)',
            },
        ],
    },

    # 7. Resolución ADC ─────────────────────────────────────────────────────
    'adc_resolution': {
        'name': 'Resolución ADC',
        'icon': '📊',
        'variables': [
            {'symbol': 'Vref', 'name': 'Voltaje de Referencia', 'unit': 'V', 'default': 5.0},
            {'symbol': 'n', 'name': 'Número de Bits', 'unit': 'bits', 'default': 10.0},
            {'symbol': 'resolution', 'name': 'Resolución (paso)', 'unit': 'V/paso', 'default': 0.0},
            {'symbol': 'Vin', 'name': 'Voltaje de Entrada', 'unit': 'V', 'default': 0.0},
            {'symbol': 'digital', 'name': 'Valor Digital', 'unit': '', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'resolution',
                'inputs': ['Vref', 'n'],
                'expression': lambda vals: vals['Vref'] / (2 ** int(vals['n'])) if vals['n'] >= 0 else float('inf'),
                'display': 'Resolución = Vref / 2ⁿ',
            },
            {
                'solve_for': 'digital',
                'inputs': ['Vin', 'Vref', 'n'],
                'expression': lambda vals: (vals['Vin'] / vals['Vref']) * (2 ** int(vals['n'])) if vals['Vref'] != 0 else float('inf'),
                'display': 'Digital = (Vin / Vref) × 2ⁿ',
            },
            {
                'solve_for': 'Vin',
                'inputs': ['digital', 'Vref', 'n'],
                'expression': lambda vals: (vals['digital'] / (2 ** int(vals['n']))) * vals['Vref'] if vals['n'] >= 0 else float('inf'),
                'display': 'Vin = (Digital / 2ⁿ) × Vref',
            },
        ],
    },

    # 8. Salida DAC ─────────────────────────────────────────────────────────
    'dac_output': {
        'name': 'Salida DAC',
        'icon': '📈',
        'variables': [
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'digital', 'name': 'Valor Digital', 'unit': '', 'default': 0.0},
            {'symbol': 'n', 'name': 'Número de Bits', 'unit': 'bits', 'default': 10.0},
            {'symbol': 'Vref', 'name': 'Voltaje de Referencia', 'unit': 'V', 'default': 5.0},
        ],
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['digital', 'n', 'Vref'],
                'expression': lambda vals: (vals['digital'] / (2 ** int(vals['n']))) * vals['Vref'] if vals['n'] >= 0 else float('inf'),
                'display': 'Vout = (Digital / 2ⁿ) × Vref',
            },
            {
                'solve_for': 'digital',
                'inputs': ['Vout', 'n', 'Vref'],
                'expression': lambda vals: (vals['Vout'] / vals['Vref']) * (2 ** int(vals['n'])) if (vals['Vref'] != 0 and vals['n'] >= 0) else float('inf'),
                'display': 'Digital = (Vout / Vref) × 2ⁿ',
            },
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# OTHER_FORMULAS
# ──────────────────────────────────────────────────────────────────────────────

# Tabla de secciones normalizadas de cable (mm²) con corriente máxima (A) en instalación empotrada (PVC, Cu, monofásico)
WIRE_SECTION_TABLE = [
    {'section_mm2': 0.5,  'max_current_a': 3},
    {'section_mm2': 0.75, 'max_current_a': 5},
    {'section_mm2': 1.0,  'max_current_a': 8},
    {'section_mm2': 1.5,  'max_current_a': 12},
    {'section_mm2': 2.5,  'max_current_a': 17},
    {'section_mm2': 4.0,  'max_current_a': 23},
    {'section_mm2': 6.0,  'max_current_a': 30},
    {'section_mm2': 10.0, 'max_current_a': 40},
    {'section_mm2': 16.0, 'max_current_a': 54},
    {'section_mm2': 25.0, 'max_current_a': 70},
    {'section_mm2': 35.0, 'max_current_a': 86},
    {'section_mm2': 50.0, 'max_current_a': 104},
    {'section_mm2': 70.0, 'max_current_a': 131},
    {'section_mm2': 95.0, 'max_current_a': 159},
    {'section_mm2': 120.0, 'max_current_a': 183},
    {'section_mm2': 150.0, 'max_current_a': 209},
    {'section_mm2': 185.0, 'max_current_a': 238},
    {'section_mm2': 240.0, 'max_current_a': 276},
    {'section_mm2': 300.0, 'max_current_a': 315},
]

OTHER_FORMULAS = {

    # 1. Código de colores de resistencias ──────────────────────────────────
    'resistor_color_code': {
        'name': 'Código de Colores de Resistencias',
        'icon': '🌈',
        'type': 'resistor_color_code',
        'description': 'Código de colores estándar para resistencias de 4 y 5 bandas',
        'colors': RESISTOR_COLORS,
        'band_order_4': ['Banda 1 (dígito)', 'Banda 2 (dígito)', 'Multiplicador', 'Tolerancia'],
        'band_order_5': ['Banda 1 (dígito)', 'Banda 2 (dígito)', 'Banda 3 (dígito)', 'Multiplicador', 'Tolerancia'],
        'calculate_4band': lambda b1, b2, mult: (
            (RESISTOR_COLORS[b1]['value'] * 10 + RESISTOR_COLORS[b2]['value']) * RESISTOR_COLORS[mult]['multiplier']
            if (RESISTOR_COLORS[b1]['value'] is not None and
                RESISTOR_COLORS[b2]['value'] is not None and
                RESISTOR_COLORS[mult]['multiplier'] is not None)
            else None
        ),
        'calculate_5band': lambda b1, b2, b3, mult: (
            (RESISTOR_COLORS[b1]['value'] * 100 + RESISTOR_COLORS[b2]['value'] * 10 + RESISTOR_COLORS[b3]['value']) * RESISTOR_COLORS[mult]['multiplier']
            if (RESISTOR_COLORS[b1]['value'] is not None and
                RESISTOR_COLORS[b2]['value'] is not None and
                RESISTOR_COLORS[b3]['value'] is not None and
                RESISTOR_COLORS[mult]['multiplier'] is not None)
            else None
        ),
    },


    'resistor_color_code_5': {
        'name': 'Código de Colores (5 Bandas)',
        'icon': '🌈',
        'type': 'resistor_color_code',
        'bands': 5,
        'description': 'Código de colores estándar para resistencias de 5 bandas',
    },


    'resistor_color_code_6': {
        'name': 'Código de Colores (6 Bandas)',
        'icon': '🌈',
        'type': 'resistor_color_code',
        'bands': 6,
        'description': 'Código de colores para resistencias de precisión (añade Coeficiente de Temperatura)',
    },

    # 2. Resistencia para LED ───────────────────────────────────────────────
    'led_resistor': {
        'name': 'Resistencia para LED',
        'icon': '💡',
        'variables': [
            {'symbol': 'R', 'name': 'Resistencia Necesaria', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Vs', 'name': 'Voltaje de Fuente', 'unit': 'V', 'default': 5.0},
            {'symbol': 'Vf', 'name': 'Voltaje Directo LED', 'unit': 'V', 'default': 2.0},
            {'symbol': 'If', 'name': 'Corriente del LED', 'unit': 'A', 'default': 0.02},
        ],
        'formulas': [
            {
                'solve_for': 'R',
                'inputs': ['Vs', 'Vf', 'If'],
                'expression': lambda vals: (vals['Vs'] - vals['Vf']) / vals['If'] if vals['If'] != 0 else float('inf'),
                'display': 'R = (Vs − Vf) / If',
            },
            {
                'solve_for': 'If',
                'inputs': ['Vs', 'Vf', 'R'],
                'expression': lambda vals: (vals['Vs'] - vals['Vf']) / vals['R'] if vals['R'] != 0 else float('inf'),
                'display': 'If = (Vs − Vf) / R',
            },
            {
                'solve_for': 'Vs',
                'inputs': ['Vf', 'If', 'R'],
                'expression': lambda vals: vals['Vf'] + vals['If'] * vals['R'],
                'display': 'Vs = Vf + If × R',
            },
        ],
    },

    # 3. LM317 Voltaje de salida ────────────────────────────────────────────
    'lm317_voltage': {
        'name': 'LM317 Voltaje de Salida',
        'icon': '🔧',
        'variables': [
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'R1', 'name': 'Resistencia R1', 'unit': 'Ω', 'default': 240.0},
            {'symbol': 'R2', 'name': 'Resistencia R2', 'unit': 'Ω', 'default': 0.0},
            {'symbol': 'Iadj', 'name': 'Corriente de Ajuste', 'unit': 'A', 'default': 50e-6},
        ],
        'description': 'Vref típica del LM317 = 1.25V, Iadj típica ≈ 50µA',
        'formulas': [
            {
                'solve_for': 'Vout',
                'inputs': ['R1', 'R2', 'Iadj'],
                'expression': lambda vals: 1.25 * (1.0 + vals['R2'] / vals['R1']) + vals['Iadj'] * vals['R2'] if vals['R1'] != 0 else float('inf'),
                'display': 'Vout = 1.25 × (1 + R2/R1) + Iadj × R2',
            },
            {
                'solve_for': 'R2',
                'inputs': ['Vout', 'R1', 'Iadj'],
                'expression': lambda vals: (
                    (vals['Vout'] - 1.25) / (1.25 / vals['R1'] + vals['Iadj'])
                    if (1.25 / vals['R1'] + vals['Iadj']) != 0 and vals['R1'] != 0
                    else float('inf')
                ),
                'display': 'R2 = (Vout − 1.25) / (1.25/R1 + Iadj)',
            },
            {
                'solve_for': 'Vout',
                'inputs': ['R1', 'R2'],
                'expression': lambda vals: 1.25 * (1.0 + vals['R2'] / vals['R1']) if vals['R1'] != 0 else float('inf'),
                'display': 'Vout ≈ 1.25 × (1 + R2/R1)  (Iadj≈0)',
            },
        ],
    },

    # 4. LM317 Disipación de potencia ───────────────────────────────────────
    'lm317_dissipation': {
        'name': 'LM317 Disipación de Potencia',
        'icon': '🌡️',
        'variables': [
            {'symbol': 'Pd', 'name': 'Potencia Disipada', 'unit': 'W', 'default': 0.0},
            {'symbol': 'Vin', 'name': 'Voltaje de Entrada', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Vout', 'name': 'Voltaje de Salida', 'unit': 'V', 'default': 0.0},
            {'symbol': 'Iout', 'name': 'Corriente de Salida', 'unit': 'A', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'Pd',
                'inputs': ['Vin', 'Vout', 'Iout'],
                'expression': lambda vals: (vals['Vin'] - vals['Vout']) * vals['Iout'],
                'display': 'Pd = (Vin − Vout) × Iout',
            },
            {
                'solve_for': 'Iout',
                'inputs': ['Pd', 'Vin', 'Vout'],
                'expression': lambda vals: vals['Pd'] / (vals['Vin'] - vals['Vout']) if (vals['Vin'] - vals['Vout']) != 0 else float('inf'),
                'display': 'Iout = Pd / (Vin − Vout)',
            },
            {
                'solve_for': 'Vin',
                'inputs': ['Pd', 'Vout', 'Iout'],
                'expression': lambda vals: vals['Pd'] / vals['Iout'] + vals['Vout'] if vals['Iout'] != 0 else float('inf'),
                'display': 'Vin = Pd / Iout + Vout',
            },
        ],
    },

    # 5. Tiempo de descarga de batería ──────────────────────────────────────
    'battery_discharge_time': {
        'name': 'Tiempo de Descarga de Batería',
        'icon': '🔋',
        'variables': [
            {'symbol': 'T', 'name': 'Tiempo de Descarga', 'unit': 'h', 'default': 0.0},
            {'symbol': 'C_ah', 'name': 'Capacidad', 'unit': 'Ah', 'default': 0.0},
            {'symbol': 'I_a', 'name': 'Corriente de Descarga', 'unit': 'A', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'T',
                'inputs': ['C_ah', 'I_a'],
                'expression': lambda vals: vals['C_ah'] / vals['I_a'] if vals['I_a'] != 0 else float('inf'),
                'display': 'T = C(Ah) / I(A)',
            },
            {
                'solve_for': 'C_ah',
                'inputs': ['T', 'I_a'],
                'expression': lambda vals: vals['T'] * vals['I_a'],
                'display': 'C(Ah) = T × I(A)',
            },
            {
                'solve_for': 'I_a',
                'inputs': ['C_ah', 'T'],
                'expression': lambda vals: vals['C_ah'] / vals['T'] if vals['T'] != 0 else float('inf'),
                'display': 'I(A) = C(Ah) / T',
            },
        ],
    },

    # 6. Energía de batería ─────────────────────────────────────────────────
    'battery_energy': {
        'name': 'Energía de Batería',
        'icon': '⚡',
        'variables': [
            {'symbol': 'E', 'name': 'Energía', 'unit': 'Wh', 'default': 0.0},
            {'symbol': 'V', 'name': 'Voltaje Nominal', 'unit': 'V', 'default': 0.0},
            {'symbol': 'C_ah', 'name': 'Capacidad', 'unit': 'Ah', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'E',
                'inputs': ['V', 'C_ah'],
                'expression': lambda vals: vals['V'] * vals['C_ah'],
                'display': 'E(Wh) = V × C(Ah)',
            },
            {
                'solve_for': 'V',
                'inputs': ['E', 'C_ah'],
                'expression': lambda vals: vals['E'] / vals['C_ah'] if vals['C_ah'] != 0 else float('inf'),
                'display': 'V = E(Wh) / C(Ah)',
            },
            {
                'solve_for': 'C_ah',
                'inputs': ['E', 'V'],
                'expression': lambda vals: vals['E'] / vals['V'] if vals['V'] != 0 else float('inf'),
                'display': 'C(Ah) = E(Wh) / V',
            },
        ],
    },

    # 7. Potencia trifásica ─────────────────────────────────────────────────
    'three_phase_power': {
        'name': 'Potencia Trifásica',
        'icon': '🔌',
        'variables': [
            {'symbol': 'P', 'name': 'Potencia Activa', 'unit': 'W', 'default': 0.0},
            {'symbol': 'Q', 'name': 'Potencia Reactiva', 'unit': 'VAR', 'default': 0.0},
            {'symbol': 'S', 'name': 'Potencia Aparente', 'unit': 'VA', 'default': 0.0},
            {'symbol': 'V', 'name': 'Voltaje de Línea', 'unit': 'V', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente de Línea', 'unit': 'A', 'default': 0.0},
            {'symbol': 'φ', 'name': 'Ángulo de Fase', 'unit': '°', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'P',
                'inputs': ['V', 'I', 'φ'],
                'expression': lambda vals: math.sqrt(3) * vals['V'] * vals['I'] * math.cos(math.radians(vals['φ'])),
                'display': 'P = √3 × V × I × cos(φ)',
            },
            {
                'solve_for': 'Q',
                'inputs': ['V', 'I', 'φ'],
                'expression': lambda vals: math.sqrt(3) * vals['V'] * vals['I'] * math.sin(math.radians(vals['φ'])),
                'display': 'Q = √3 × V × I × sin(φ)',
            },
            {
                'solve_for': 'S',
                'inputs': ['V', 'I'],
                'expression': lambda vals: math.sqrt(3) * vals['V'] * vals['I'],
                'display': 'S = √3 × V × I',
            },
            {
                'solve_for': 'I',
                'inputs': ['P', 'V', 'φ'],
                'expression': lambda vals: vals['P'] / (math.sqrt(3) * vals['V'] * math.cos(math.radians(vals['φ']))) if (vals['V'] != 0 and math.cos(math.radians(vals['φ'])) != 0) else float('inf'),
                'display': 'I = P / (√3 × V × cos(φ))',
            },
            {
                'solve_for': 'S',
                'inputs': ['P', 'Q'],
                'expression': lambda vals: math.sqrt(vals['P'] ** 2 + vals['Q'] ** 2),
                'display': 'S = √(P² + Q²)',
            },
        ],
    },

    # 8. Factor de potencia ─────────────────────────────────────────────────
    'power_factor': {
        'name': 'Factor de Potencia',
        'icon': '📊',
        'variables': [
            {'symbol': 'cosφ', 'name': 'Factor de Potencia (cos φ)', 'unit': '', 'default': 0.0},
            {'symbol': 'sinφ', 'name': 'Factor Reactivo (sin φ)', 'unit': '', 'default': 0.0},
            {'symbol': 'P', 'name': 'Potencia Activa', 'unit': 'W', 'default': 0.0},
            {'symbol': 'Q', 'name': 'Potencia Reactiva', 'unit': 'VAR', 'default': 0.0},
            {'symbol': 'S', 'name': 'Potencia Aparente', 'unit': 'VA', 'default': 0.0},
            {'symbol': 'φ', 'name': 'Ángulo de Fase', 'unit': '°', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'cosφ',
                'inputs': ['P', 'S'],
                'expression': lambda vals: vals['P'] / vals['S'] if vals['S'] != 0 else float('inf'),
                'display': 'cos(φ) = P / S',
            },
            {
                'solve_for': 'sinφ',
                'inputs': ['Q', 'S'],
                'expression': lambda vals: vals['Q'] / vals['S'] if vals['S'] != 0 else float('inf'),
                'display': 'sin(φ) = Q / S',
            },
            {
                'solve_for': 'φ',
                'inputs': ['P', 'S'],
                'expression': lambda vals: math.degrees(math.acos(min(max(vals['P'] / vals['S'], -1.0), 1.0))) if vals['S'] != 0 else float('inf'),
                'display': 'φ = arccos(P / S)',
            },
            {
                'solve_for': 'P',
                'inputs': ['S', 'cosφ'],
                'expression': lambda vals: vals['S'] * vals['cosφ'],
                'display': 'P = S × cos(φ)',
            },
            {
                'solve_for': 'Q',
                'inputs': ['S', 'sinφ'],
                'expression': lambda vals: vals['S'] * vals['sinφ'],
                'display': 'Q = S × sin(φ)',
            },
        ],
    },

    # 9. Velocidad sincrónica de motor ──────────────────────────────────────
    'motor_sync_speed': {
        'name': 'Velocidad Sincrónica del Motor',
        'icon': '⚙️',
        'variables': [
            {'symbol': 'Ns', 'name': 'Velocidad Sincrónica', 'unit': 'RPM', 'default': 0.0},
            {'symbol': 'f', 'name': 'Frecuencia', 'unit': 'Hz', 'default': 50.0},
            {'symbol': 'P', 'name': 'Número de Polos', 'unit': '', 'default': 4.0},
        ],
        'formulas': [
            {
                'solve_for': 'Ns',
                'inputs': ['f', 'P'],
                'expression': lambda vals: 120.0 * vals['f'] / vals['P'] if vals['P'] != 0 else float('inf'),
                'display': 'Ns = 120 × f / P',
            },
            {
                'solve_for': 'f',
                'inputs': ['Ns', 'P'],
                'expression': lambda vals: vals['Ns'] * vals['P'] / 120.0,
                'display': 'f = Ns × P / 120',
            },
            {
                'solve_for': 'P',
                'inputs': ['Ns', 'f'],
                'expression': lambda vals: 120.0 * vals['f'] / vals['Ns'] if vals['Ns'] != 0 else float('inf'),
                'display': 'P = 120 × f / Ns',
            },
        ],
    },

    # 10. Torque del motor ──────────────────────────────────────────────────
    'motor_torque': {
        'name': 'Torque del Motor',
        'icon': '🔩',
        'variables': [
            {'symbol': 'T', 'name': 'Torque', 'unit': 'N·m', 'default': 0.0},
            {'symbol': 'P', 'name': 'Potencia', 'unit': 'W', 'default': 0.0},
            {'symbol': 'n', 'name': 'Velocidad', 'unit': 'RPM', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'T',
                'inputs': ['P', 'n'],
                'expression': lambda vals: 9.5493 * vals['P'] / vals['n'] if vals['n'] != 0 else float('inf'),
                'display': 'T = 9.5493 × P / n  [= P / (2π × n/60)]',
            },
            {
                'solve_for': 'P',
                'inputs': ['T', 'n'],
                'expression': lambda vals: vals['T'] * 2.0 * math.pi * vals['n'] / 60.0,
                'display': 'P = T × 2π × n / 60',
            },
            {
                'solve_for': 'n',
                'inputs': ['P', 'T'],
                'expression': lambda vals: 9.5493 * vals['P'] / vals['T'] if vals['T'] != 0 else float('inf'),
                'display': 'n = 9.5493 × P / T',
            },
        ],
    },

    # 11. Eficiencia del motor ──────────────────────────────────────────────
    'motor_efficiency': {
        'name': 'Eficiencia del Motor',
        'icon': '📈',
        'variables': [
            {'symbol': 'η', 'name': 'Eficiencia', 'unit': '%', 'default': 0.0},
            {'symbol': 'Pout', 'name': 'Potencia de Salida', 'unit': 'W', 'default': 0.0},
            {'symbol': 'Pin', 'name': 'Potencia de Entrada', 'unit': 'W', 'default': 0.0},
            {'symbol': 'Ploss', 'name': 'Pérdidas', 'unit': 'W', 'default': 0.0},
        ],
        'formulas': [
            {
                'solve_for': 'η',
                'inputs': ['Pout', 'Pin'],
                'expression': lambda vals: (vals['Pout'] / vals['Pin']) * 100.0 if vals['Pin'] != 0 else float('inf'),
                'display': 'η = (Pout / Pin) × 100%',
            },
            {
                'solve_for': 'Pout',
                'inputs': ['η', 'Pin'],
                'expression': lambda vals: vals['η'] / 100.0 * vals['Pin'],
                'display': 'Pout = (η/100) × Pin',
            },
            {
                'solve_for': 'Pin',
                'inputs': ['η', 'Pout'],
                'expression': lambda vals: vals['Pout'] / (vals['η'] / 100.0) if vals['η'] != 0 else float('inf'),
                'display': 'Pin = Pout / (η/100)',
            },
            {
                'solve_for': 'Ploss',
                'inputs': ['Pin', 'Pout'],
                'expression': lambda vals: vals['Pin'] - vals['Pout'],
                'display': 'Pérdidas = Pin − Pout',
            },
            {
                'solve_for': 'η',
                'inputs': ['Pin', 'Ploss'],
                'expression': lambda vals: ((vals['Pin'] - vals['Ploss']) / vals['Pin']) * 100.0 if vals['Pin'] != 0 else float('inf'),
                'display': 'η = ((Pin − Pérdidas) / Pin) × 100%',
            },
        ],
    },

    # 12. Sección de cable por corriente ────────────────────────────────────
    'wire_section_by_current': {
        'name': 'Sección de Cable por Corriente',
        'icon': '📐',
        'type': 'table_lookup',
        'description': 'Sección normalizada de cable de cobre (PVC, instalación empotrada)',
        'variables': [
            {'symbol': 'I', 'name': 'Corriente de Carga', 'unit': 'A', 'default': 0.0},
            {'symbol': 'section', 'name': 'Sección Recomendada', 'unit': 'mm²', 'default': 0.0},
        ],
        'wire_table': WIRE_SECTION_TABLE,
        'formulas': [
            {
                'solve_for': 'section',
                'inputs': ['I'],
                'expression': lambda vals: next(
                    (entry['section_mm2'] for entry in WIRE_SECTION_TABLE if entry['max_current_a'] >= vals['I']),
                    float('inf')
                ),
                'display': 'Sección mínima según tabla normalizada para I dado',
            },
        ],
    },

    # 13. Máxima caída de voltaje (%) ───────────────────────────────────────
    'max_voltage_drop': {
        'name': 'Porcentaje de Caída de Voltaje',
        'icon': '📉',
        'variables': [
            {'symbol': 'Vdrop_pct', 'name': '% Caída de Voltaje', 'unit': '%', 'default': 0.0},
            {'symbol': 'I', 'name': 'Corriente', 'unit': 'A', 'default': 0.0},
            {'symbol': 'R', 'name': 'Resistencia por km de cable', 'unit': 'Ω/km', 'default': 0.0},
            {'symbol': 'L', 'name': 'Longitud del Cable', 'unit': 'm', 'default': 0.0},
            {'symbol': 'V', 'name': 'Voltaje Nominal', 'unit': 'V', 'default': 220.0},
        ],
        'description': 'Monofásico. Para trifásico multiplicar por √3/2 ≈ 0.866',
        'formulas': [
            {
                'solve_for': 'Vdrop_pct',
                'inputs': ['I', 'R', 'L', 'V'],
                'expression': lambda vals: (2.0 * vals['I'] * (vals['R'] / 1000.0) * vals['L'] / vals['V']) * 100.0 if vals['V'] != 0 else float('inf'),
                'display': '%Vdrop = (2 × I × R × L / V) × 100',
            },
            {
                'solve_for': 'L',
                'inputs': ['Vdrop_pct', 'I', 'R', 'V'],
                'expression': lambda vals: (vals['Vdrop_pct'] / 100.0 * vals['V']) / (2.0 * vals['I'] * (vals['R'] / 1000.0)) if (vals['I'] != 0 and vals['R'] != 0) else float('inf'),
                'display': 'L = (%Vdrop/100 × V) / (2 × I × R)',
            },
            {
                'solve_for': 'I',
                'inputs': ['Vdrop_pct', 'R', 'L', 'V'],
                'expression': lambda vals: (vals['Vdrop_pct'] / 100.0 * vals['V']) / (2.0 * (vals['R'] / 1000.0) * vals['L']) if (vals['R'] != 0 and vals['L'] != 0) else float('inf'),
                'display': 'I = (%Vdrop/100 × V) / (2 × R × L)',
            },
        ],
    },

    # 39. Cálculo de Disipador de Calor ─────────────────────────────────────
    'heatsink_calc': {
        'name': 'Cálculo de Disipador de Calor',
        'icon': '🌡️',
        'variables': [
            {'symbol': 'Tj', 'name': 'Temp. Unión Máx. (Tj)', 'unit': '°C', 'default': 125.0},
            {'symbol': 'Ta', 'name': 'Temp. Ambiente Máx. (Ta)', 'unit': '°C', 'default': 25.0},
            {'symbol': 'Pd', 'name': 'Potencia Disipada (Pd)', 'unit': 'W', 'default': 10.0},
            {'symbol': 'Rjc', 'name': 'Resist. Unión-Caja (Rjc)', 'unit': '°C/W', 'default': 1.5},
            {'symbol': 'Rcs', 'name': 'Resist. Caja-Disipador (Rcs)', 'unit': '°C/W', 'default': 0.5},
            {'symbol': 'Rsa', 'name': 'Resist. Disipador-Amb. (Rsa)', 'unit': '°C/W', 'default': 0.0},
        ],
        'description': 'Calcula la resistencia térmica necesaria del disipador de calor (Rsa) o la temperatura de unión resultante (Tj). Rcs típica: 0.1 a 1.0 °C/W según grasa térmica/silicona.',
        'formulas': [
            {
                'solve_for': 'Rsa',
                'inputs': ['Tj', 'Ta', 'Pd', 'Rjc', 'Rcs'],
                'expression': lambda vals: ((vals['Tj'] - vals['Ta']) / vals['Pd']) - vals['Rjc'] - vals['Rcs'] if vals['Pd'] != 0 else float('inf'),
                'display': 'Rsa = (Tj − Ta) / Pd − Rjc − Rcs',
            },
            {
                'solve_for': 'Tj',
                'inputs': ['Ta', 'Pd', 'Rjc', 'Rcs', 'Rsa'],
                'expression': lambda vals: vals['Ta'] + vals['Pd'] * (vals['Rjc'] + vals['Rcs'] + vals['Rsa']),
                'display': 'Tj = Ta + Pd × (Rjc + Rcs + Rsa)',
            },
            {
                'solve_for': 'Pd',
                'inputs': ['Tj', 'Ta', 'Rjc', 'Rcs', 'Rsa'],
                'expression': lambda vals: (vals['Tj'] - vals['Ta']) / (vals['Rjc'] + vals['Rcs'] + vals['Rsa']) if (vals['Rjc'] + vals['Rcs'] + vals['Rsa']) != 0 else float('inf'),
                'display': 'Pd = (Tj − Ta) / (Rjc + Rcs + Rsa)',
            },
            {
                'solve_for': 'Ta',
                'inputs': ['Tj', 'Pd', 'Rjc', 'Rcs', 'Rsa'],
                'expression': lambda vals: vals['Tj'] - vals['Pd'] * (vals['Rjc'] + vals['Rcs'] + vals['Rsa']),
                'display': 'Ta = Tj − Pd × (Rjc + Rcs + Rsa)',
            },
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────

# Diccionario maestro que agrupa todas las categorías
# ──────────────────────────────────────────────────────────────────────────────

ALL_FORMULA_CATEGORIES = {
    'analog': {
        'name': 'Fórmulas Analógicas',
        'icon': '📻',
        'formulas': ANALOG_FORMULAS,
    },
    'digital': {
        'name': 'Fórmulas Digitales',
        'icon': '💻',
        'formulas': DIGITAL_FORMULAS,
    },
    'other': {
        'name': 'Otras Fórmulas',
        'icon': '🔧',
        'formulas': OTHER_FORMULAS,
    },
}


def get_all_formula_keys():
    """Retorna una lista de todas las claves de fórmulas disponibles con su categoría."""
    result = []
    for cat_key, cat_data in ALL_FORMULA_CATEGORIES.items():
        for formula_key, formula_data in cat_data['formulas'].items():
            result.append({
                'category': cat_key,
                'category_name': cat_data['name'],
                'key': formula_key,
                'name': formula_data['name'],
                'icon': formula_data['icon'],
            })
    return result


def search_formulas(query):
    """Busca fórmulas por nombre o clave. Retorna lista de coincidencias."""
    query_lower = query.lower()
    results = []
    for cat_key, cat_data in ALL_FORMULA_CATEGORIES.items():
        for formula_key, formula_data in cat_data['formulas'].items():
            if (query_lower in formula_key.lower() or
                    query_lower in formula_data['name'].lower() or
                    query_lower in formula_data.get('description', '').lower()):
                results.append({
                    'category': cat_key,
                    'category_name': cat_data['name'],
                    'key': formula_key,
                    'name': formula_data['name'],
                    'icon': formula_data['icon'],
                    'data': formula_data,
                })
    return results


def format_resistance_value(ohms):
    """Formatea un valor de resistencia con prefijo apropiado (Ω, kΩ, MΩ, GΩ)."""
    if ohms is None:
        return "N/A"
    if ohms >= 1e9:
        return f"{ohms / 1e9:.2f} GΩ"
    elif ohms >= 1e6:
        return f"{ohms / 1e6:.2f} MΩ"
    elif ohms >= 1e3:
        return f"{ohms / 1e3:.2f} kΩ"
    elif ohms >= 1:
        return f"{ohms:.2f} Ω"
    elif ohms >= 0.001:
        return f"{ohms * 1e3:.2f} mΩ"
    else:
        return f"{ohms:.6f} Ω"


def format_capacitance_value(farads):
    """Formatea un valor de capacitancia con prefijo apropiado (F, mF, µF, nF, pF)."""
    if farads is None:
        return "N/A"
    if farads >= 1:
        return f"{farads:.3f} F"
    elif farads >= 1e-3:
        return f"{farads * 1e3:.3f} mF"
    elif farads >= 1e-6:
        return f"{farads * 1e6:.3f} µF"
    elif farads >= 1e-9:
        return f"{farads * 1e9:.3f} nF"
    else:
        return f"{farads * 1e12:.3f} pF"


def format_inductance_value(henrys):
    """Formatea un valor de inductancia con prefijo apropiado (H, mH, µH, nH)."""
    if henrys is None:
        return "N/A"
    if henrys >= 1:
        return f"{henrys:.3f} H"
    elif henrys >= 1e-3:
        return f"{henrys * 1e3:.3f} mH"
    elif henrys >= 1e-6:
        return f"{henrys * 1e6:.3f} µH"
    else:
        return f"{henrys * 1e9:.3f} nH"


def format_frequency_value(hertz):
    """Formatea un valor de frecuencia con prefijo apropiado (Hz, kHz, MHz, GHz)."""
    if hertz is None:
        return "N/A"
    if hertz >= 1e9:
        return f"{hertz / 1e9:.3f} GHz"
    elif hertz >= 1e6:
        return f"{hertz / 1e6:.3f} MHz"
    elif hertz >= 1e3:
        return f"{hertz / 1e3:.3f} kHz"
    else:
        return f"{hertz:.3f} Hz"


def format_engineering(value, unit=''):
    """Formatea un valor numérico con notación de ingeniería y su unidad."""
    if value is None or value == float('inf') or value == float('-inf') or value != value:
        return "N/A"

    abs_val = abs(value)
    sign = '-' if value < 0 else ''

    if abs_val == 0:
        return f"0 {unit}".strip()
    elif abs_val >= 1e12:
        return f"{sign}{abs_val / 1e12:.3f} T{unit}".strip()
    elif abs_val >= 1e9:
        return f"{sign}{abs_val / 1e9:.3f} G{unit}".strip()
    elif abs_val >= 1e6:
        return f"{sign}{abs_val / 1e6:.3f} M{unit}".strip()
    elif abs_val >= 1e3:
        return f"{sign}{abs_val / 1e3:.3f} k{unit}".strip()
    elif abs_val >= 1:
        return f"{sign}{abs_val:.3f} {unit}".strip()
    elif abs_val >= 1e-3:
        return f"{sign}{abs_val * 1e3:.3f} m{unit}".strip()
    elif abs_val >= 1e-6:
        return f"{sign}{abs_val * 1e6:.3f} µ{unit}".strip()
    elif abs_val >= 1e-9:
        return f"{sign}{abs_val * 1e9:.3f} n{unit}".strip()
    elif abs_val >= 1e-12:
        return f"{sign}{abs_val * 1e12:.3f} p{unit}".strip()
    else:
        return f"{sign}{abs_val:.3e} {unit}".strip()
