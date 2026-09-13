# =============================================================================
# Vito Organizer v2.2 - Bodega PDF Export
# Generador de reportes PDF para el módulo de Bodega
# =============================================================================

import os
from fpdf import FPDF
from PyQt6.QtCore import QDate
from config.settings import Settings
from data.data_store import DataStore


class BodegaPDF(FPDF):
    """Clase base de PDF para reportes de Bodega con formato gráfico idéntico a Laboratorio."""

    def __init__(self, agenda_path: str, subtitle: str = "Informe de Bodega"):
        super().__init__()
        self.agenda_path = agenda_path
        self.report_subtitle = subtitle

        # Cargar configuración global para el logo
        try:
            self.settings = Settings.load()
            self.logo_path = self.settings.general.logo_path
            if not self.logo_path or not os.path.isfile(self.logo_path):
                if self.agenda_path and os.path.exists(self.agenda_path):
                    portada_dir = os.path.join(self.agenda_path, 'portada')
                    if os.path.exists(portada_dir):
                        for f in os.listdir(portada_dir):
                            if f.startswith('custom_logo') and f.lower().endswith(('.png', '.jpg', '.jpeg', '.svg', '.webp', '.avif')):
                                self.logo_path = os.path.join(portada_dir, f)
                                break
        except Exception:
            self.logo_path = ""

        # Cargar título de la agenda desde Portada
        self.agenda_title = "Vito Organizer"
        if self.agenda_path:
            portada_path = DataStore.get_plugin_data_path(self.agenda_path, 'portada')
            portada_data = DataStore.load(portada_path)
            if portada_data:
                self.agenda_title = portada_data.get('title', self.agenda_title)

    def header(self):
        # Fondo oscuro para el encabezado #222436 -> R:34, G:36, B:54
        self.set_fill_color(34, 36, 54)
        self.rect(0, 0, 210, 40, 'F')

        # Dibujar logo si existe y es válido
        logo_x = 15
        if self.logo_path and os.path.isfile(self.logo_path):
            try:
                info = self.image(self.logo_path, x=15, y=10, h=20)
                if hasattr(info, 'rendered_width'):
                    logo_x = 15 + info.rendered_width + 5
                else:
                    logo_x = 45
            except Exception as e:
                print(f"Error cargando logo en PDF Bodega: {e}")

        # Título y Subtítulo
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 22)
        self.set_xy(logo_x, 12)
        self.cell(0, 10, self.agenda_title, border=0, ln=1)

        self.set_font('helvetica', 'I', 11)
        self.set_xy(logo_x, 22)
        self.set_text_color(200, 200, 200)
        self.cell(0, 10, self.report_subtitle, border=0, ln=1)

        # Franja Naranja #FF5722 -> R:255, G:87, B:34
        self.set_fill_color(255, 87, 34)
        self.rect(0, 40, 210, 4, 'F')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Vito Organizer - Página {self.page_no()}', align='R')


def _draw_metadata_box(pdf: BodegaPDF, title: str, serial_num: str, details_dict: dict):
    """Renderiza el bloque superior con los datos principales del reporte."""
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 8, title, ln=1, border='B')
    pdf.ln(4)

    y_start = pdf.get_y()
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)

    # Correlativo
    pdf.set_xy(15, y_start)
    pdf.cell(35, 6, "Folio / Correlativo:")
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(50, 6, serial_num)

    # Fecha
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(110, y_start)
    pdf.cell(30, 6, "Fecha Emisión:")
    pdf.set_font('helvetica', '', 10)
    pdf.cell(50, 6, QDate.currentDate().toString("dd/MM/yyyy"))

    y_current = y_start + 6
    for k, v in details_dict.items():
        pdf.set_xy(15, y_current)
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(35, 6, str(k))
        pdf.set_font('helvetica', '', 10)
        pdf.cell(140, 6, str(v))
        y_current += 6

    pdf.set_y(y_current + 4)


def generate_bodega_pdf(filepath: str, current_view: str, items_data: list, config: dict, serial_num: str, agenda_path: str):
    """Genera el reporte PDF para el módulo Bodega según la vista y los filtros especificados."""
    subtitle_map = {
        'stock': "Reporte de Control de Inventario y Stock",
        'saldos': "Reporte de Saldos de Inventario y Ubicaciones",
        'costos': "Reporte de Valoración y Costos de Inventario",
        'consolidado': "Informe Consolidado y Balance de Existencias"
    }
    subtitle = subtitle_map.get(current_view, "Informe de Bodega")

    pdf = BodegaPDF(agenda_path, subtitle=subtitle)
    pdf.add_page()

    # Cargar settings para moneda
    try:
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
    except Exception:
        currency = 'CLP'

    # Renderizar metadatos
    if current_view == 'consolidado':
        _draw_metadata_box(
            pdf,
            "Resumen Consolidado de Existencias",
            serial_num,
            {"Sección:": "Bodega", "Tipo de Reporte:": "Resumen General y Balance"}
        )
        _render_consolidado(pdf, items_data, currency)
    elif current_view == 'stock':
        el_type_label = {"all": "Todos", "components": "Solo Componentes", "supplies": "Solo Insumos"}.get(config.get('element_type'), "Todos")
        stock_filter_label = {
            "all": "Todos los elementos",
            "low_stock": "Bajo stock (≤ Mínimo)",
            "min_stock": "Stock Mínimo Exacto",
            "no_stock": "Sin Stock (=0)",
            "high_stock": "Mucho Stock (> 2x Mínimo)"
        }.get(config.get('stock_filter'), "Todos")

        _draw_metadata_box(
            pdf,
            "Listado de Control de Stock",
            serial_num,
            {"Elementos:": el_type_label, "Filtro Aplicado:": stock_filter_label}
        )
        _render_stock_table(pdf, items_data, config)
    elif current_view == 'saldos':
        el_type_label = {"all": "Todos", "components": "Solo Componentes", "supplies": "Solo Insumos"}.get(config.get('element_type'), "Todos")
        loc_label = config.get('location', 'all')
        loc_display = "Todas" if loc_label == 'all' else loc_label

        _draw_metadata_box(
            pdf,
            "Reporte de Saldos y Ubicaciones",
            serial_num,
            {"Elementos:": el_type_label, "Ubicación:": loc_display, "Agrupado:": "Sí" if config.get('group_by_location') else "No"}
        )
        _render_saldos_table(pdf, items_data, config)
    elif current_view == 'costos':
        el_type_label = {"all": "Todos", "components": "Solo Componentes", "supplies": "Solo Insumos"}.get(config.get('element_type'), "Todos")
        cost_filter_label = {
            "all": "Todos los costos",
            "no_cost": "Sin costo ($0)",
            "low_cost": "Costos bajos (≤ $10.000)",
            "high_cost": "Costos altos (> $10.000)"
        }.get(config.get('cost_filter'), "Todos")

        _draw_metadata_box(
            pdf,
            "Valoración de Inventario y Costos",
            serial_num,
            {"Elementos:": el_type_label, "Filtro de Costos:": cost_filter_label, "Moneda:": currency}
        )
        _render_costos_table(pdf, items_data, config, currency)

    pdf.output(filepath)


def _filter_items(items_data: list, config: dict) -> list:
    """Filtra la lista de items según la configuración de exportación."""
    filtered = []
    el_type = config.get('element_type', 'all')
    st_filter = config.get('stock_filter', 'all')
    loc_filter = config.get('location', 'all')
    cost_filter = config.get('cost_filter', 'all')

    for item, type_str in items_data:
        # Filtro de tipo de elemento
        if el_type != 'all' and type_str != el_type:
            continue

        stock = item.get('stock_quantity', 0)
        min_stock = item.get('min_stock_quantity', 0)

        # Filtro de stock
        if st_filter == 'low_stock' and stock > min_stock:
            continue
        elif st_filter == 'min_stock' and stock != min_stock:
            continue
        elif st_filter == 'no_stock' and stock != 0:
            continue
        elif st_filter == 'high_stock' and stock <= min_stock * 2:
            continue

        # Filtro de ubicación
        loc = item.get('storage_location', 'No definido')
        if loc_filter != 'all' and loc != loc_filter:
            continue

        # Filtro de costo
        cost = item.get('cost_value', 0.0)
        if cost_filter == 'no_cost' and cost != 0.0:
            continue
        elif cost_filter == 'low_cost' and (cost == 0.0 or cost > 10000.0):
            continue
        elif cost_filter == 'high_cost' and cost <= 10000.0:
            continue

        filtered.append((item, type_str))

    return filtered


def _render_table_header(pdf: BodegaPDF, col_widths: list, titles: list):
    pdf.set_fill_color(34, 36, 54)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('helvetica', 'B', 10)

    for width, title in zip(col_widths, titles):
        align_mode = 'C' if width < 40 else 'L'
        pdf.cell(width, 8, f" {title}", border=1, fill=True, align=align_mode)
    pdf.ln()
    pdf.set_text_color(50, 50, 50)


def _check_page_break(pdf: BodegaPDF):
    if pdf.get_y() > 260:
        pdf.add_page()


def _render_stock_table(pdf: BodegaPDF, items_data: list, config: dict):
    filtered = _filter_items(items_data, config)

    col_widths = [30, 80, 25, 25, 25]
    titles = ["Tipo", "Nombre del Elemento", "Stock", "Mínimo", "Estado"]
    _render_table_header(pdf, col_widths, titles)

    pdf.set_font('helvetica', '', 9)
    for item, type_str in filtered:
        _check_page_break(pdf)
        stock = item.get('stock_quantity', 0)
        min_stock = item.get('min_stock_quantity', 0)
        is_low = stock <= min_stock

        type_lbl = "Componente" if type_str == 'components' else "Insumo"
        name = item.get('name', 'N/A')

        pdf.cell(30, 7, f" {type_lbl}", border=1)
        pdf.cell(80, 7, f" {name[:45]}", border=1)
        pdf.cell(25, 7, str(stock), border=1, align='C')
        pdf.cell(25, 7, str(min_stock), border=1, align='C')

        if is_low:
            pdf.set_text_color(211, 47, 47)
            pdf.set_font('helvetica', 'B', 9)
            pdf.cell(25, 7, "REPOSICIÓN", border=1, align='C', ln=1)
            pdf.set_font('helvetica', '', 9)
            pdf.set_text_color(50, 50, 50)
        else:
            pdf.set_text_color(46, 125, 50)
            pdf.cell(25, 7, "OK", border=1, align='C', ln=1)
            pdf.set_text_color(50, 50, 50)

    pdf.ln(5)
    pdf.set_font('helvetica', 'I', 9)
    pdf.cell(0, 6, f"Total elementos listados: {len(filtered)}", ln=1)


def _render_saldos_table(pdf: BodegaPDF, items_data: list, config: dict):
    filtered = _filter_items(items_data, config)
    group_by_loc = config.get('group_by_location', False)

    if group_by_loc:
        grouped = {}
        for item, type_str in filtered:
            loc = item.get('storage_location', 'No definido')
            grouped.setdefault(loc, []).append((item, type_str))

        col_widths = [30, 85, 35, 35]
        titles = ["Tipo", "Nombre del Elemento", "Saldo (Stock)", "Unidad"]

        for loc_name, loc_items in grouped.items():
            _check_page_break(pdf)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(210, 105, 30)
            pdf.cell(185, 8, f" Ubicación: {loc_name}", border=1, fill=True, ln=1)

            _render_table_header(pdf, col_widths, titles)
            pdf.set_font('helvetica', '', 9)

            for item, type_str in loc_items:
                _check_page_break(pdf)
                stock = item.get('stock_quantity', 0)
                unit_str = item.get('unit', 'unidades') if type_str == 'supplies' else 'unidades'
                type_lbl = "Componente" if type_str == 'components' else "Insumo"

                pdf.cell(30, 7, f" {type_lbl}", border=1)
                pdf.cell(85, 7, f" {item.get('name', '')[:48]}", border=1)
                pdf.cell(35, 7, str(stock), border=1, align='C')
                pdf.cell(35, 7, f" {unit_str}", border=1, ln=1)
            pdf.ln(4)
    else:
        col_widths = [30, 70, 25, 25, 35]
        titles = ["Tipo", "Nombre del Elemento", "Saldo", "Unidad", "Ubicación"]
        _render_table_header(pdf, col_widths, titles)

        pdf.set_font('helvetica', '', 9)
        for item, type_str in filtered:
            _check_page_break(pdf)
            stock = item.get('stock_quantity', 0)
            unit_str = item.get('unit', 'unidades') if type_str == 'supplies' else 'unidades'
            loc = item.get('storage_location', 'No definido')
            type_lbl = "Componente" if type_str == 'components' else "Insumo"

            pdf.cell(30, 7, f" {type_lbl}", border=1)
            pdf.cell(70, 7, f" {item.get('name', '')[:40]}", border=1)
            pdf.cell(25, 7, str(stock), border=1, align='C')
            pdf.cell(25, 7, f" {unit_str[:12]}", border=1)
            pdf.cell(35, 7, f" {loc[:20]}", border=1, ln=1)

    pdf.ln(5)
    pdf.set_font('helvetica', 'I', 9)
    pdf.cell(0, 6, f"Total elementos listados: {len(filtered)}", ln=1)


def _render_costos_table(pdf: BodegaPDF, items_data: list, config: dict, currency: str):
    filtered = _filter_items(items_data, config)

    col_widths = [30, 75, 20, 30, 30]
    titles = ["Tipo", "Nombre del Elemento", "Stock", f"Costo U. ({currency})", f"Valor Total ({currency})"]
    _render_table_header(pdf, col_widths, titles)

    total_inventory_valuation = 0.0
    pdf.set_font('helvetica', '', 9)

    for item, type_str in filtered:
        _check_page_break(pdf)
        stock = item.get('stock_quantity', 0)
        cost = item.get('cost_value', 0.0)
        total_val = stock * cost
        total_inventory_valuation += total_val
        type_lbl = "Componente" if type_str == 'components' else "Insumo"

        pdf.cell(30, 7, f" {type_lbl}", border=1)
        pdf.cell(75, 7, f" {item.get('name', '')[:42]}", border=1)
        pdf.cell(20, 7, str(stock), border=1, align='C')
        pdf.cell(30, 7, f" {cost:.2f}", border=1, align='R')
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(21, 101, 192)
        pdf.cell(30, 7, f" {total_val:.2f}", border=1, align='R', ln=1)
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)

    # Fila de Total Valoración
    pdf.set_fill_color(255, 235, 230)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(125, 8, " VALORACIÓN TOTAL DEL INVENTARIO LISTADO:", border=1, fill=True)
    pdf.set_text_color(210, 105, 30)
    pdf.cell(60, 8, f" {total_inventory_valuation:.2f} {currency}", border=1, fill=True, align='R', ln=1)


def _render_consolidado(pdf: BodegaPDF, items_data: list, currency: str):
    total_components = 0
    total_supplies = 0
    val_components = 0.0
    val_supplies = 0.0
    low_stock_list = []

    for item, type_str in items_data:
        stock = item.get('stock_quantity', 0)
        min_stock = item.get('min_stock_quantity', 0)
        cost = item.get('cost_value', 0.0)

        if type_str == 'components':
            total_components += stock
            val_components += stock * cost
        else:
            total_supplies += stock
            val_supplies += stock * cost

        if stock <= min_stock:
            low_stock_list.append((item, type_str))

    grand_total_val = val_components + val_supplies

    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(210, 105, 30)
    pdf.cell(0, 8, "Balance General de Inventario", ln=1)
    pdf.ln(2)

    col_w = [90, 45, 50]
    titles = ["Categoría de Inventario", "Cantidad Total", f"Valoración ({currency})"]
    _render_table_header(pdf, col_w, titles)

    pdf.set_font('helvetica', '', 10)
    pdf.cell(90, 8, " Componentes Electrónicos", border=1)
    pdf.cell(45, 8, f"{total_components} unidades", border=1, align='C')
    pdf.cell(50, 8, f"{val_components:.2f} {currency}", border=1, align='R', ln=1)

    pdf.cell(90, 8, " Insumos de Taller", border=1)
    pdf.cell(45, 8, f"{total_supplies} unidades", border=1, align='C')
    pdf.cell(50, 8, f"{val_supplies:.2f} {currency}", border=1, align='R', ln=1)

    pdf.set_fill_color(255, 235, 230)
    pdf.set_font('helvetica', 'B', 10)
    pdf.cell(90, 8, " TOTAL INVENTARIO", border=1, fill=True)
    pdf.cell(45, 8, f"{total_components + total_supplies} unidades", border=1, fill=True, align='C')
    pdf.set_text_color(210, 105, 30)
    pdf.cell(50, 8, f"{grand_total_val:.2f} {currency}", border=1, fill=True, align='R', ln=1)

    pdf.ln(10)
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(211, 47, 47)
    pdf.cell(0, 8, f" Elementos Críticos que Requieren Reposición ({len(low_stock_list)})", ln=1)
    pdf.ln(2)

    crit_w = [35, 85, 30, 35]
    crit_titles = ["Tipo", "Nombre del Elemento", "Stock Actual", "Stock Mínimo"]
    _render_table_header(pdf, crit_w, crit_titles)

    pdf.set_font('helvetica', '', 9)
    for item, type_str in low_stock_list:
        _check_page_break(pdf)
        type_lbl = "Componente" if type_str == 'components' else "Insumo"
        pdf.cell(35, 7, f" {type_lbl}", border=1)
        pdf.cell(85, 7, f" {item.get('name', '')[:48]}", border=1)
        pdf.set_font('helvetica', 'B', 9)
        pdf.set_text_color(211, 47, 47)
        pdf.cell(30, 7, str(item.get('stock_quantity', 0)), border=1, align='C')
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(35, 7, str(item.get('min_stock_quantity', 0)), border=1, align='C', ln=1)
