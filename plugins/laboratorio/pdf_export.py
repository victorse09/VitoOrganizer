import os
import json
import re
import tempfile
from fpdf import FPDF
from PyQt6.QtCore import QDate
from config.settings import Settings
from data.data_store import DataStore
from plugins.plugin_base import IMAGE_EXTENSIONS, load_image_pixmap


def clean_pdf_text(text: str) -> str:
    """Reemplaza caracteres fuera de latin-1 comunes en fpdf (em-dash, bullets, omega, etc.)."""
    if not text:
        return ""
    text = str(text)
    replacements = {
        '\u2014': '-',   # em-dash —
        '\u2013': '-',   # en-dash –
        '\u2022': '-',   # bullet •
        '\u03a9': 'Ohm', # Omega mayúscula Ω
        '\u03c9': 'ohm', # omega minúscula ω
        '\u03bc': 'u',   # micro griego µ
        '\u201c': '"',   # comilla izquierda “
        '\u201d': '"',   # comilla derecha ”
        '\u2018': "'",   # comilla simple ‘
        '\u2019': "'",   # comilla simple ’
        '\u2026': '...', # elipsis …
        '\u2265': '>=',  # mayor o igual ≥
        '\u2264': '<=',  # menor o igual ≤
        '\u00b1': '+/-', # mas menos ±
        '\u2260': '!=',  # no igual ≠
        '\u2248': '~',   # aprox ≈
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')


class ChecklistPDF(FPDF):
    def __init__(self, agenda_path: str):
        super().__init__()
        self.agenda_path = agenda_path
        
        # Load global settings for logo
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
        
        # Load agenda info (Portada data) for titles
        self.agenda_title = "Vito Organizer"
        self.agenda_subtitle = "Informe de Inspección y Mantenimiento"
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
                print(f"Error cargando logo en PDF: {e}")
                pass
                
        # Título y Subtítulo
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 24)
        self.set_xy(logo_x, 12)
        self.cell(0, 10, self.agenda_title, border=0, ln=1)
        
        self.set_font('helvetica', 'I', 12)
        self.set_xy(logo_x, 22)
        self.set_text_color(200, 200, 200)
        self.cell(0, 10, self.agenda_subtitle, border=0, ln=1)
        
        # Franja Naranja #FF5722 -> R:255, G:87, B:34
        self.set_fill_color(255, 87, 34)
        self.rect(0, 40, 210, 4, 'F')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Vito Organizer - Página {self.page_no()}', align='R')

def generate_checklist_pdf(filepath: str, log_entry: dict, checklist_def: dict, item: dict, agenda_path: str):
    pdf = ChecklistPDF(agenda_path)
    pdf.add_page()
    
    # Datos de la herramienta / equipo
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 10, "Detalles del Equipo y Chequeo", ln=1, border='B')
    pdf.ln(5)
    
    # Helper for key-value
    def draw_kv(k, v, y_pos):
        pdf.set_xy(15, y_pos)
        pdf.set_font('helvetica', 'B', 10)
        pdf.cell(40, 6, str(k))
        pdf.set_font('helvetica', '', 10)
        pdf.cell(80, 6, str(v))
    
    y = pdf.get_y()
    pdf.set_text_color(50, 50, 50)
    draw_kv("Equipo / Ítem:", item.get('name', 'N/A'), y)
    draw_kv("Marca:", item.get('brand', 'N/A'), y+6)
    draw_kv("Modelo:", item.get('model', 'N/A'), y+12)
    draw_kv("Categoría:", item.get('type', 'N/A'), y+18)
    draw_kv("ID Chequeo:", log_entry.get('check_number', 'N/A'), y+24)
    draw_kv("Fecha:", log_entry.get('date', 'N/A'), y+30)
    draw_kv("Resultado:", log_entry.get('result', 'N/A'), y+36)
    
    # Image if available
    bib_img_path = None
    if agenda_path:
        bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
        bib_data = DataStore.load(bib_path)
        if bib_data:
            docs = bib_data.get('documents', [])
    if not bib_img_path and item.get('image'):
        rel = item.get('image')
        full = os.path.join(agenda_path, rel) if agenda_path and not os.path.isabs(rel) else rel
        if os.path.exists(full):
            bib_img_path = full

    if bib_img_path and os.path.isfile(bib_img_path):
        try:
            # Si es AVIF o SVG, convertir temporalmente a PNG para FPDF
            safe_img = bib_img_path
            if bib_img_path.lower().endswith(('.avif', '.webp', '.svg')):
                from plugins.plugin_base import load_image_pixmap
                import tempfile
                pix = load_image_pixmap(bib_img_path)
                if not pix.isNull():
                    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    safe_img = tmp.name
                    tmp.close()
                    pix.save(safe_img, "PNG")

            # Add image in the right space
            pdf.image(safe_img, x=135, y=y, w=60)
        except:
            pass
            
    pdf.set_y(max(pdf.get_y(), y+50))
    pdf.ln(5)
    
    # Checklist Result
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 10, "Lista de Verificación", ln=1, border='B')
    pdf.ln(5)
    
    answers = log_entry.get('checklist_answers', {})
    
    def render_items_grid(items_tuples: list):
        num_cols = 2
        col_width = 88.0
        col_start_x = 15.0
        
        i = 0
        while i < len(items_tuples):
            if pdf.get_y() > 260:
                pdf.add_page()
                
            row_start_y = pdf.get_y()
            max_row_y = row_start_y
            
            for col in range(num_cols):
                if i >= len(items_tuples):
                    break
                    
                item_text, is_checked = items_tuples[i]
                i += 1
                
                col_x = col_start_x + (col * (col_width + 4.0))
                box_x = col_x + 2.0
                box_y = row_start_y + 1.0
                box_size = 4.2
                
                if is_checked:
                    pdf.set_fill_color(46, 125, 50)
                    pdf.set_draw_color(46, 125, 50)
                    pdf.rect(box_x, box_y, box_size, box_size, style='FD')
                    
                    pdf.set_draw_color(255, 255, 255)
                    pdf.set_line_width(0.7)
                    pdf.line(box_x + 0.8, box_y + 2.0, box_x + 1.7, box_y + 3.2)
                    pdf.line(box_x + 1.7, box_y + 3.2, box_x + 3.4, box_y + 0.8)
                    pdf.set_line_width(0.2)
                else:
                    pdf.set_fill_color(250, 250, 250)
                    pdf.set_draw_color(180, 180, 180)
                    pdf.rect(box_x, box_y, box_size, box_size, style='FD')
                    
                text_x = col_x + 8.0
                text_w = col_width - 8.0
                pdf.set_xy(text_x, row_start_y)
                pdf.set_font('helvetica', '', 9.5)
                if is_checked:
                    pdf.set_text_color(33, 37, 41)
                else:
                    pdf.set_text_color(120, 120, 120)
                pdf.multi_cell(text_w, 5, item_text)
                
                if pdf.get_y() > max_row_y:
                    max_row_y = pdf.get_y()
                    
            pdf.set_y(max_row_y + 1.5)

    if checklist_def:
        for g in checklist_def.get('groups', []):
            g_name = g.get('name', 'General')
            
            if pdf.get_y() > 250:
                pdf.add_page()
                
            pdf.ln(2)
            pdf.set_fill_color(240, 243, 246)
            pdf.set_draw_color(210, 215, 220)
            pdf.set_font('helvetica', 'B', 10.5)
            pdf.set_text_color(34, 36, 54)
            pdf.cell(0, 6.5, f"   {g_name}", border=1, fill=True, ln=1)
            pdf.ln(2)
            
            items_tuples = []
            for item_text in g.get('items', []):
                key = f"{g_name}_{item_text}"
                is_checked = answers.get(key, False)
                items_tuples.append((item_text, is_checked))
                
            render_items_grid(items_tuples)
            pdf.ln(2)
    else:
        pdf.ln(2)
        items_tuples = []
        for key, val in answers.items():
            parts = key.split('_', 1)
            item_label = parts[1] if len(parts) > 1 else key
            items_tuples.append((item_label, val))
        render_items_grid(items_tuples)

    pdf.ln(10)
    if pdf.get_y() > 250:
        pdf.add_page()
        
    pdf.set_font('helvetica', 'B', 12)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 8, "Notas y Observaciones:", ln=1)
    
    pdf.set_font('helvetica', '', 10)
    pdf.set_text_color(50, 50, 50)
    notes = log_entry.get('notes', '')
    if not notes.strip():
        notes = "Sin observaciones."
    pdf.multi_cell(0, 6, notes)
    
    pdf.output(filepath)


# =============================================================================
# Component PDF Export (Ficha Técnica y Datasheets)
# =============================================================================

def get_component_image_path(component: dict, agenda_path: str) -> str:
    """Busca la imagen asociada al componente en Biblioteca o en el propio registro."""
    if not component or not agenda_path:
        return ""

    comp_id = component.get('id')
    # 1. Buscar en documentos asignados de Biblioteca
    bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
    bib_data = DataStore.load(bib_path)
    if bib_data:
        docs = bib_data.get('documents', [])
        for d in docs:
            if comp_id in d.get('assigned_element_ids', []):
                rel = d.get('relative_path', '')
                full = os.path.join(agenda_path, rel)
                if rel.lower().endswith(IMAGE_EXTENSIONS) and os.path.isfile(full):
                    return full

    # 2. Campo directo 'image'
    img_field = component.get('image', '')
    if img_field:
        candidate = os.path.join(agenda_path, img_field) if not os.path.isabs(img_field) else img_field
        if os.path.isfile(candidate):
            return candidate

    return ""


def get_component_datasheets_and_docs(component: dict, agenda_path: str) -> list:
    """Retorna lista de tuplas (nombre, tipo, ruta_absoluta) de documentos vinculados en Biblioteca."""
    docs_list = []
    if not component or not agenda_path:
        return docs_list

    comp_id = component.get('id')
    bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
    bib_data = DataStore.load(bib_path)
    if bib_data:
        docs = bib_data.get('documents', [])
        for d in docs:
            if comp_id in d.get('assigned_element_ids', []):
                rel = d.get('relative_path', '')
                full = os.path.join(agenda_path, rel)
                if os.path.isfile(full):
                    name = d.get('name') or os.path.basename(full)
                    dtype = d.get('type') or 'Documento'
                    docs_list.append((name, dtype, full))

    # También verificar si tiene un archivo en el campo 'datasheet'
    ds_field = component.get('datasheet', '').strip()
    if ds_field:
        candidate = os.path.join(agenda_path, ds_field) if not os.path.isabs(ds_field) else ds_field
        if os.path.isfile(candidate):
            if not any(full == candidate for _, _, full in docs_list):
                docs_list.append((os.path.basename(candidate), "Datasheets", candidate))

    return docs_list


class ComponentPDF(FPDF):
    """Generador de PDF para la Ficha Técnica de Componentes Electrónicos."""

    def __init__(self, agenda_path: str, page_format: str = 'letter'):
        super().__init__(format=page_format)
        self.agenda_path = agenda_path
        self.page_format = page_format
        self.report_title = "Vito Organizer"
        self.report_subtitle = "Ficha Técnica de Componente Electrónico"

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
        if self.agenda_path:
            portada_path = DataStore.get_plugin_data_path(self.agenda_path, 'portada')
            portada_data = DataStore.load(portada_path)
            if portada_data:
                self.report_title = portada_data.get('title', self.report_title)

    def header(self):
        # Fondo oscuro institucional #222436 -> R:34, G:36, B:54
        self.set_fill_color(34, 36, 54)
        self.rect(0, 0, self.w, 40, 'F')

        # Dibujar logo institucional si existe
        logo_x = 15
        if self.logo_path and os.path.isfile(self.logo_path):
            try:
                safe_logo = self.logo_path
                if self.logo_path.lower().endswith(('.svg', '.avif', '.webp')):
                    pix = load_image_pixmap(self.logo_path)
                    if not pix.isNull():
                        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        safe_logo = tmp.name
                        tmp.close()
                        pix.save(safe_logo, "PNG")
                info = self.image(safe_logo, x=15, y=10, h=20)
                if hasattr(info, 'rendered_width'):
                    logo_x = 15 + info.rendered_width + 5
                else:
                    logo_x = 45
            except Exception as e:
                print(f"Error cargando logo en PDF componente: {e}")

        # Título y Subtítulo
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 22)
        self.set_xy(logo_x, 12)
        self.cell(0, 10, self.report_title, border=0, ln=1)

        self.set_font('helvetica', 'I', 11)
        self.set_xy(logo_x, 22)
        self.set_text_color(200, 200, 200)
        self.cell(0, 10, self.report_subtitle, border=0, ln=1)

        # Franja divisoria naranja #FF5722 -> R:255, G:87, B:34
        self.set_fill_color(255, 87, 34)
        self.rect(0, 40, self.w, 4, 'F')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Vito Organizer - Página {self.page_no()}', align='R')


def generate_component_pdf(filepath: str, component: dict, options: dict, serial_str: str, agenda_path: str):
    """Construye el documento PDF de la ficha de componente y opcionalmente fusiona el datasheet."""
    page_format = options.get('page_format', 'letter')
    pdf = ComponentPDF(agenda_path, page_format=page_format)
    pdf.add_page()

    # Bloque de folio y fecha de emisión
    y_top = pdf.get_y()
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(15, y_top)
    pdf.cell(35, 6, "Folio / Correlativo:")
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(50, 6, serial_str)

    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(pdf.w - 85, y_top)
    pdf.cell(32, 6, "Fecha Emisión:")
    pdf.set_font('helvetica', '', 10)
    pdf.cell(35, 6, QDate.currentDate().toString("dd/MM/yyyy"))
    pdf.ln(10)

    # Título de sección: Detalles del Componente
    name = component.get('name', 'Componente')
    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 8, f"Ficha Técnica: {name}", ln=1, border='B')
    pdf.ln(5)

    # Buscar imagen del componente
    img_path = get_component_image_path(component, agenda_path)
    img_w = 60
    has_img = False
    safe_img = None
    if img_path and os.path.isfile(img_path):
        try:
            safe_img = img_path
            if img_path.lower().endswith(('.avif', '.webp', '.svg')):
                pix = load_image_pixmap(img_path)
                if not pix.isNull():
                    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    safe_img = tmp.name
                    tmp.close()
                    pix.save(safe_img, "PNG")
            has_img = True
        except Exception as e:
            print(f"Error procesando imagen para PDF: {e}")
            has_img = False

    # Moneda local
    try:
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
    except Exception:
        currency = 'CLP'

    stock = component.get('stock_quantity', 0)
    cost = component.get('cost_value', 0.0)
    total_val = stock * cost
    tested_str = "Testeado Operativo" if component.get('tested', True) else "No Testeado"

    details = [
        ("Nombre / Identificador:", name),
        ("Tipo de Componente:", str(component.get('type', 'N/A'))),
        ("Categoría / Encapsulado:", str(component.get('category', 'N/A'))),
        ("Lugar de Almacenado:", str(component.get('storage_location', 'N/A'))),
        ("Cantidad en Stock:", f"{stock} unidades"),
        ("Stock Mínimo:", f"{component.get('min_stock_quantity', 0)} unidades"),
        ("Costo Unitario:", f"{cost:.2f} {currency}"),
        ("Valor Total en Stock:", f"{total_val:.2f} {currency}"),
        ("Estado de Prueba:", tested_str),
        ("Condición Física:", str(component.get('condition', 'N/A')))
    ]

    y_start_details = pdf.get_y()
    val_w = (pdf.w - 30 - img_w - 55) if has_img else (pdf.w - 30 - 55)

    for label, val in details:
        pdf.set_x(15)
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(50, 6, label)

        pdf.set_font('helvetica', '', 10)
        if label == "Valor Total en Stock:":
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(21, 101, 192)  # Azul #1565C0
        elif label == "Cantidad en Stock:":
            pdf.set_font('helvetica', 'B', 10)
            pdf.set_text_color(34, 36, 54)
        else:
            pdf.set_text_color(60, 60, 60)

        pdf.cell(val_w, 6, str(val), ln=1)

    y_after_details = pdf.get_y()

    if has_img and safe_img:
        try:
            img_x = pdf.w - 15 - img_w
            pdf.image(safe_img, x=img_x, y=y_start_details, w=img_w)
        except Exception as e:
            print(f"Error insertando imagen en PDF: {e}")

    pdf.set_y(max(y_after_details, y_start_details + 55))
    pdf.ln(4)

    # Documentación asociada en Biblioteca
    assigned_docs = get_component_datasheets_and_docs(component, agenda_path)
    if assigned_docs:
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(0, 77, 64)  # #004D40
        pdf.cell(0, 7, "Archivos de Biblioteca y Datasheets Asignados:", ln=1)
        pdf.set_font('helvetica', '', 9.5)
        pdf.set_text_color(70, 70, 70)
        for doc_name, doc_type, _ in assigned_docs:
            clean_type = doc_type.replace("🖼️ ", "").replace("📖 ", "").replace("📄 ", "")
            pdf.set_x(20)
            pdf.cell(0, 5, f"- {clean_type}: {doc_name}", ln=1)
        pdf.ln(4)

    # Movimientos de inventario si se solicitaron
    if options.get('include_movements', False):
        movements = component.get('movements', [])
        if pdf.get_y() > (pdf.h - 60):
            pdf.add_page()

        pdf.set_font('helvetica', 'B', 13)
        pdf.set_text_color(255, 87, 34)
        pdf.cell(0, 8, "Historial de Movimientos de Inventario", ln=1, border='B')
        pdf.ln(3)

        col_widths = [35, 45, 30, pdf.w - 30 - 35 - 45 - 30]
        pdf.set_fill_color(34, 36, 54)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(col_widths[0], 7, "Fecha", border=1, fill=True, align='C')
        pdf.cell(col_widths[1], 7, "Tipo de Operación", border=1, fill=True, align='C')
        pdf.cell(col_widths[2], 7, "Cantidad", border=1, fill=True, align='C')
        pdf.cell(col_widths[3], 7, "Detalle / Observaciones", border=1, fill=True, align='C', ln=1)

        pdf.set_font('helvetica', '', 9)
        if movements:
            for idx, mv in enumerate(movements):
                if pdf.get_y() > (pdf.h - 25):
                    pdf.add_page()
                    pdf.set_fill_color(34, 36, 54)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font('helvetica', 'B', 9)
                    pdf.cell(col_widths[0], 7, "Fecha", border=1, fill=True, align='C')
                    pdf.cell(col_widths[1], 7, "Tipo de Operación", border=1, fill=True, align='C')
                    pdf.cell(col_widths[2], 7, "Cantidad", border=1, fill=True, align='C')
                    pdf.cell(col_widths[3], 7, "Detalle / Observaciones", border=1, fill=True, align='C', ln=1)
                    pdf.set_font('helvetica', '', 9)

                bg_color = 255 if idx % 2 == 0 else 245
                pdf.set_fill_color(bg_color, bg_color, bg_color)

                m_date = str(mv.get('date', 'N/A'))
                m_type = str(mv.get('type', 'N/A')).capitalize()
                m_qty = mv.get('quantity', 0)
                is_ingreso = mv.get('type') == 'ingreso'
                qty_str = f"+{m_qty}" if is_ingreso else f"-{m_qty}"
                m_notes = str(mv.get('notes') or mv.get('reason') or mv.get('comment') or "Registro de stock")

                pdf.set_text_color(50, 50, 50)
                pdf.cell(col_widths[0], 6.5, m_date, border=1, fill=True, align='C')
                pdf.cell(col_widths[1], 6.5, m_type, border=1, fill=True, align='C')

                if is_ingreso:
                    pdf.set_text_color(46, 125, 50)  # Verde
                else:
                    pdf.set_text_color(198, 40, 40)  # Rojo
                pdf.set_font('helvetica', 'B', 9)
                pdf.cell(col_widths[2], 6.5, qty_str, border=1, fill=True, align='C')

                pdf.set_font('helvetica', '', 9)
                pdf.set_text_color(60, 60, 60)
                pdf.cell(col_widths[3], 6.5, m_notes[:50], border=1, fill=True, ln=1)
        else:
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(120, 120, 120)
            pdf.cell(sum(col_widths), 7, "Sin movimientos de stock registrados para este componente.", border=1, fill=True, align='C', ln=1)

    # Anexar páginas del Datasheet (si se marcó la opción)
    include_ds = options.get('include_datasheet', False)
    ds_path = options.get('datasheet_path')

    if include_ds and ds_path and os.path.isfile(ds_path) and ds_path.lower().endswith('.pdf'):
        import fitz

        tmp_fd, tmp_comp_path = tempfile.mkstemp(suffix='.pdf')
        os.close(tmp_fd)

        try:
            pdf.output(tmp_comp_path)
            doc_comp = fitz.open(tmp_comp_path)
            doc_ds = fitz.open(ds_path)

            num_pages = options.get('datasheet_pages', 1)
            if num_pages == 'all' or num_pages == -1:
                doc_comp.insert_pdf(doc_ds)
            else:
                max_page_idx = min(len(doc_ds) - 1, int(num_pages) - 1)
                if max_page_idx >= 0:
                    doc_comp.insert_pdf(doc_ds, from_page=0, to_page=max_page_idx)

            doc_comp.save(filepath)
            doc_comp.close()
            doc_ds.close()
        finally:
            if os.path.exists(tmp_comp_path):
                try:
                    os.unlink(tmp_comp_path)
                except Exception:
                    pass
    else:
        pdf.output(filepath)


# =============================================================================
# Instrument PDF Export (Ficha Técnica, Especificaciones, HTML, CheckLists y Documentos)
# =============================================================================

def get_instrument_image_path(instrument: dict, agenda_path: str) -> str:
    """Busca la imagen asociada al instrumento en Biblioteca o en el propio registro."""
    if not instrument or not agenda_path:
        return ""

    inst_id = instrument.get('id')
    inst_name = str(instrument.get('name', '')).lower()
    inst_model = str(instrument.get('model', '')).lower()

    # 1. Campo directo 'image' o 'image_path'
    img_prop = instrument.get('image') or instrument.get('image_path')
    if img_prop and isinstance(img_prop, str):
        candidate = os.path.join(agenda_path, img_prop) if not os.path.isabs(img_prop) else img_prop
        if os.path.isfile(candidate):
            return candidate

    # 2. Documentos de imagen asignados en Biblioteca
    bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
    bib_data = DataStore.load(bib_path)
    if bib_data:
        docs = bib_data.get('documents', [])
        for d in docs:
            rel = d.get('relative_path', '')
            if not rel.lower().endswith(IMAGE_EXTENSIONS):
                continue
            full = os.path.join(agenda_path, rel)
            if not os.path.isfile(full):
                continue

            doc_assigned_ids = d.get('assigned_element_ids', [])
            tags = [str(t).lower() for t in d.get('tags', [])]
            if (inst_id and inst_id in doc_assigned_ids) or (inst_name and inst_name in tags) or (inst_model and inst_model in tags):
                return full

    return ""


def get_instrument_documents(instrument: dict, agenda_path: str) -> dict:
    """Retorna un diccionario con listas de tuplas (nombre, ruta) de datasheets y manuales asociados.
    Formato: {'datasheets': [(nombre, ruta), ...], 'manuals': [(nombre, ruta), ...]}
    """
    result = {'datasheets': [], 'manuals': []}
    if not instrument or not agenda_path:
        return result

    seen_paths = set()
    inst_id = instrument.get('id')
    inst_name = str(instrument.get('name', '')).lower()
    inst_model = str(instrument.get('model', '')).lower()

    # 1. Comprobar campo 'manual' directo
    manual_field = (instrument.get('manual') or '').strip()
    if manual_field and manual_field.lower().endswith('.pdf'):
        candidate = manual_field if os.path.isabs(manual_field) else os.path.join(agenda_path, manual_field)
        if not os.path.isfile(candidate):
            candidate_bib = os.path.join(agenda_path, 'biblioteca', manual_field)
            if os.path.isfile(candidate_bib):
                candidate = candidate_bib
        if os.path.isfile(candidate) and candidate not in seen_paths:
            seen_paths.add(candidate)
            name = os.path.basename(candidate)
            result['manuals'].append((name, candidate))

    # 2. Comprobar campo 'datasheet' directo
    ds_field = (instrument.get('datasheet') or '').strip()
    if ds_field and ds_field.lower().endswith('.pdf'):
        candidate = ds_field if os.path.isabs(ds_field) else os.path.join(agenda_path, ds_field)
        if not os.path.isfile(candidate):
            candidate_bib = os.path.join(agenda_path, 'biblioteca', ds_field)
            if os.path.isfile(candidate_bib):
                candidate = candidate_bib
        if os.path.isfile(candidate) and candidate not in seen_paths:
            seen_paths.add(candidate)
            name = os.path.basename(candidate)
            result['datasheets'].append((name, candidate))

    # 3. Buscar en biblioteca por ID asignado o etiquetas
    bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
    bib_data = DataStore.load(bib_path)
    if bib_data:
        docs = bib_data.get('documents', [])
        for d in docs:
            rel = d.get('relative_path', '')
            if not rel.lower().endswith('.pdf'):
                continue
            full = os.path.join(agenda_path, rel)
            if not os.path.isfile(full) or full in seen_paths:
                continue

            doc_assigned_ids = d.get('assigned_element_ids', [])
            tags = [str(t).lower() for t in d.get('tags', [])]
            is_match = False
            if inst_id and inst_id in doc_assigned_ids:
                is_match = True
            elif inst_name and inst_name in tags:
                is_match = True
            elif inst_id and str(inst_id).lower() in tags:
                is_match = True
            elif inst_model and inst_model in tags:
                is_match = True

            if is_match:
                seen_paths.add(full)
                doc_name = d.get('name') or os.path.basename(full)
                doc_type = (d.get('type') or d.get('category') or '').lower()
                if 'manual' in doc_type or 'manual' in doc_name.lower():
                    result['manuals'].append((doc_name, full))
                else:
                    result['datasheets'].append((doc_name, full))

    return result


class InstrumentPDF(FPDF):
    """Generador de PDF para la Ficha Técnica de Instrumentos de Laboratorio."""

    def __init__(self, agenda_path: str, page_format: str = 'letter'):
        super().__init__(format=page_format)
        self.agenda_path = agenda_path
        self.page_format = page_format
        self.report_title = "Vito Organizer"
        self.report_subtitle = "Ficha Técnica de Instrumento de Laboratorio"

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
        if self.agenda_path:
            portada_path = DataStore.get_plugin_data_path(self.agenda_path, 'portada')
            portada_data = DataStore.load(portada_path)
            if portada_data:
                self.report_title = portada_data.get('title', self.report_title)

    def header(self):
        # Fondo oscuro institucional #222436 -> R:34, G:36, B:54
        self.set_fill_color(34, 36, 54)
        self.rect(0, 0, self.w, 40, 'F')

        # Dibujar logo institucional si existe
        logo_x = 15
        if self.logo_path and os.path.isfile(self.logo_path):
            try:
                safe_logo = self.logo_path
                if self.logo_path.lower().endswith(('.svg', '.avif', '.webp')):
                    pix = load_image_pixmap(self.logo_path)
                    if not pix.isNull():
                        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        safe_logo = tmp.name
                        tmp.close()
                        pix.save(safe_logo, "PNG")
                info = self.image(safe_logo, x=15, y=10, h=20)
                if hasattr(info, 'rendered_width'):
                    logo_x = 15 + info.rendered_width + 5
                else:
                    logo_x = 45
            except Exception as e:
                print(f"Error cargando logo en PDF instrumento: {e}")

        # Título y Subtítulo
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 22)
        self.set_xy(logo_x, 12)
        self.cell(0, 10, self.report_title, border=0, ln=1)

        self.set_font('helvetica', 'I', 11)
        self.set_xy(logo_x, 22)
        self.set_text_color(200, 200, 200)
        self.cell(0, 10, self.report_subtitle, border=0, ln=1)

        # Franja divisoria naranja #FF5722 -> R:255, G:87, B:34
        self.set_fill_color(255, 87, 34)
        self.rect(0, 40, self.w, 4, 'F')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Vito Organizer - Página {self.page_no()}', align='R')


def generate_instrument_pdf(filepath: str, instrument: dict, options: dict, serial_str: str, agenda_path: str):
    """Construye el documento PDF de la ficha de instrumento con especificaciones, HTML, checklists y documentación."""
    from plugins.laboratorio.instrument_records import get_instrument_dir

    page_format = options.get('page_format', 'letter')
    pdf = InstrumentPDF(agenda_path, page_format=page_format)
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_page()

    # Bloque de folio y fecha de emisión
    y_top = pdf.get_y()
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(15, y_top)
    pdf.cell(35, 6, "Folio / Correlativo:")
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(50, 6, serial_str)

    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(pdf.w - 85, y_top)
    pdf.cell(32, 6, "Fecha Emisión:")
    pdf.set_font('helvetica', '', 10)
    pdf.cell(35, 6, QDate.currentDate().toString("dd/MM/yyyy"))
    pdf.ln(10)

    # Título de sección: Ficha Técnica del Instrumento
    name = instrument.get('name', 'Instrumento')
    brand = instrument.get('brand', '')
    model = instrument.get('model', '')
    title_sub = f"{name} ({brand} {model})".strip() if (brand or model) else name
    title_sub = clean_pdf_text(title_sub)

    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 8, f"Ficha Técnica: {title_sub}", ln=1, border='B')
    pdf.ln(5)

    # Buscar imagen del instrumento
    img_path = get_instrument_image_path(instrument, agenda_path)
    img_w = 60
    has_img = False
    safe_img = None
    if img_path and os.path.isfile(img_path):
        try:
            safe_img = img_path
            if img_path.lower().endswith(('.avif', '.webp', '.svg')):
                pix = load_image_pixmap(img_path)
                if not pix.isNull():
                    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    safe_img = tmp.name
                    tmp.close()
                    pix.save(safe_img, "PNG")
            has_img = True
        except Exception as e:
            print(f"Error procesando imagen para PDF de instrumento: {e}")
            has_img = False

    avail_w = pdf.w - 30
    meta_w = avail_w - img_w - 5 if has_img else avail_w
    y_meta_start = pdf.get_y()

    def draw_row(label: str, value: str, y_offset: float):
        pdf.set_xy(15, y_meta_start + y_offset)
        pdf.set_font('helvetica', 'B', 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(46, 6, label)
        pdf.set_font('helvetica', '', 9.5)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(meta_w - 46, 6, clean_pdf_text(str(value)))

    draw_row("Identificador (ID):", instrument.get('id', 'N/A'), 0)
    draw_row("Tipo de Instrumento:", instrument.get('type', 'General'), 6)
    draw_row("Marca y Modelo:", f"{brand} {model}".strip() or 'N/A', 12)
    draw_row("Número de Serie (S/N):", instrument.get('serial_number', 'N/A'), 18)

    status_str = instrument.get('status', 'Operativo')
    pdf.set_xy(15, y_meta_start + 24)
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(46, 6, "Estado Operativo:")
    if status_str.lower() in ('operativo', 'excelente', 'bueno'):
        pdf.set_text_color(46, 125, 50)  # Verde
    elif status_str.lower() in ('en calibración', 'mantenimiento', 'en espera'):
        pdf.set_text_color(230, 81, 0)   # Naranja
    else:
        pdf.set_text_color(198, 40, 40)  # Rojo
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(meta_w - 46, 6, clean_pdf_text(status_str))

    draw_row("Ubicación / Almacenaje:", instrument.get('storage_location', 'Laboratorio / Taller'), 30)
    draw_row("Insumos / Accesorios:", instrument.get('supplies', 'Ninguno'), 36)

    # Dibujar la fotografía del instrumento si existe
    meta_h = 44
    if has_img and safe_img:
        try:
            info = pdf.image(safe_img, x=pdf.w - 15 - img_w, y=y_meta_start, w=img_w)
            rendered_h = getattr(info, 'rendered_height', 45)
            meta_h = max(meta_h, rendered_h)
        except Exception as e:
            print(f"Error renderizando imagen en PDF de instrumento: {e}")

    pdf.set_y(y_meta_start + meta_h + 4)

    # Resumen / Descripción general de la ficha
    general_desc = instrument.get('description', '').strip()
    if general_desc:
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(34, 36, 54)
        pdf.cell(0, 6, "Resumen General / Notas:", ln=1)
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, clean_pdf_text(general_desc))
        pdf.ln(3)

    inst_dir = get_instrument_dir(agenda_path, instrument) if agenda_path else ""

    # =========================================================================
    # SECCIÓN: Especificaciones Técnicas y Rangos de Medición
    # =========================================================================
    include_specs = options.get('include_specs', True)
    if include_specs and inst_dir:
        specs_file = os.path.join(inst_dir, 'specifications.json')
        functions = []
        if os.path.exists(specs_file):
            try:
                with open(specs_file, 'r', encoding='utf-8') as f:
                    specs_data = json.load(f)
                    functions = specs_data.get('functions', [])
            except Exception as e:
                print(f"Error cargando specifications.json en PDF: {e}")

        if functions:
            if pdf.get_y() > pdf.h - 60:
                pdf.add_page()
            else:
                pdf.ln(5)

            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(21, 101, 192)  # Azul #1565C0
            pdf.cell(0, 7, "Especificaciones Técnicas y Rangos de Medición", ln=1, border='B')
            pdf.ln(3)

            # Anchos proporcionales de columnas para tablas de especificaciones
            col_w = [
                avail_w * 0.24,  # Rango / Escala
                avail_w * 0.18,  # Resolución
                avail_w * 0.18,  # Exactitud (%)
                avail_w * 0.18,  # Dígitos/Cuentas
                avail_w * 0.22   # Notas
            ]

            for func in functions:
                func_name = clean_pdf_text(func.get('name', 'Función'))
                func_desc = clean_pdf_text(func.get('description', ''))
                ranges = func.get('ranges', [])

                if pdf.get_y() > pdf.h - 45:
                    pdf.add_page()

                pdf.set_font('helvetica', 'B', 10)
                pdf.set_text_color(34, 36, 54)
                desc_extra = f" - {func_desc}" if func_desc else ""
                pdf.cell(0, 6, f"- {func_name}{desc_extra}", ln=1)

                if ranges:
                    # Encabezado de la tabla de rangos
                    pdf.set_fill_color(34, 36, 54)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font('helvetica', 'B', 8.5)
                    pdf.cell(col_w[0], 6.5, "Rango / Escala", border=1, fill=True, align='C')
                    pdf.cell(col_w[1], 6.5, "Resolución", border=1, fill=True, align='C')
                    pdf.cell(col_w[2], 6.5, "Exactitud (%)", border=1, fill=True, align='C')
                    pdf.cell(col_w[3], 6.5, "Dígitos / Cuentas", border=1, fill=True, align='C')
                    pdf.cell(col_w[4], 6.5, "Notas", border=1, fill=True, align='C', ln=1)

                    # Filas de rangos
                    for idx, r_item in enumerate(ranges):
                        if pdf.get_y() > pdf.h - 25:
                            pdf.add_page()
                            # Redibujar cabecera
                            pdf.set_fill_color(34, 36, 54)
                            pdf.set_text_color(255, 255, 255)
                            pdf.set_font('helvetica', 'B', 8.5)
                            pdf.cell(col_w[0], 6.5, "Rango / Escala", border=1, fill=True, align='C')
                            pdf.cell(col_w[1], 6.5, "Resolución", border=1, fill=True, align='C')
                            pdf.cell(col_w[2], 6.5, "Exactitud (%)", border=1, fill=True, align='C')
                            pdf.cell(col_w[3], 6.5, "Dígitos / Cuentas", border=1, fill=True, align='C')
                            pdf.cell(col_w[4], 6.5, "Notas", border=1, fill=True, align='C', ln=1)

                        if idx % 2 == 0:
                            pdf.set_fill_color(255, 255, 255)
                        else:
                            pdf.set_fill_color(245, 247, 250)

                        pdf.set_font('helvetica', '', 8.5)
                        pdf.set_text_color(30, 30, 30)

                        r_val = clean_pdf_text(str(r_item.get('range', '')))
                        res_val = clean_pdf_text(str(r_item.get('resolution', '')))
                        acc_val = clean_pdf_text(str(r_item.get('accuracy_pct', '')))
                        dig_val = clean_pdf_text(str(r_item.get('accuracy_digits', '')))
                        note_val = clean_pdf_text(str(r_item.get('notes', ''))[:40])

                        pdf.cell(col_w[0], 6, r_val, border=1, fill=True, align='C')
                        pdf.cell(col_w[1], 6, res_val, border=1, fill=True, align='C')
                        pdf.cell(col_w[2], 6, acc_val, border=1, fill=True, align='C')
                        pdf.cell(col_w[3], 6, dig_val, border=1, fill=True, align='C')
                        pdf.cell(col_w[4], 6, note_val, border=1, fill=True, ln=1)

                    pdf.ln(2)
                else:
                    pdf.set_font('helvetica', 'I', 8.5)
                    pdf.set_text_color(100, 100, 100)
                    pdf.cell(0, 5, "Sin escalas de medición registradas para esta función.", ln=1)
                    pdf.ln(2)

    # =========================================================================
    # SECCIÓN: Descripción Técnica (HTML / Texto Enriquecido)
    # =========================================================================
    include_desc = options.get('include_desc', True)
    if include_desc and inst_dir:
        desc_file = os.path.join(inst_dir, 'description.html')
        html_content = ""
        if os.path.exists(desc_file):
            try:
                with open(desc_file, 'r', encoding='utf-8') as f:
                    html_content = f.read().strip()
            except Exception as e:
                print(f"Error leyendo description.html en PDF: {e}")

        if html_content:
            if pdf.get_y() > pdf.h - 60:
                pdf.add_page()
            else:
                pdf.ln(5)

            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(142, 36, 170)  # Púrpura #8E24AA
            pdf.cell(0, 7, "Descripción Técnica Detallada (HTML)", ln=1, border='B')
            pdf.ln(4)

            try:
                # Sanitizar HTML para compatibilidad de FPDF write_html
                clean_html = re.sub(r'<!DOCTYPE[^>]*>', '', html_content, flags=re.IGNORECASE)
                clean_html = re.sub(r'<html[^>]*>', '', clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r'</html>', '', clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r'<head[^>]*>.*?</head>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
                clean_html = re.sub(r'<body[^>]*>', '', clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r'</body>', '', clean_html, flags=re.IGNORECASE)
                clean_html = re.sub(r'<style[^>]*>.*?</style>', '', clean_html, flags=re.IGNORECASE | re.DOTALL)
                clean_html = clean_pdf_text(clean_html)
                pdf.write_html(clean_html)
                pdf.ln(4)
            except Exception as e:
                print(f"Aviso: error procesando write_html de descripción ({e}), aplicando texto formateado:")
                from PyQt6.QtGui import QTextDocument
                doc_t = QTextDocument()
                doc_t.setHtml(html_content)
                plain_desc = clean_pdf_text(doc_t.toPlainText())
                pdf.set_font('helvetica', '', 9.5)
                pdf.set_text_color(40, 40, 40)
                pdf.multi_cell(0, 5.5, plain_desc)
                pdf.ln(4)

    # =========================================================================
    # SECCIÓN: Historial de Check Lists y Mantenimientos
    # =========================================================================
    include_checklist = options.get('include_checklist', True)
    if include_checklist:
        history = instrument.get('history', [])
        if history:
            if pdf.get_y() > pdf.h - 55:
                pdf.add_page()
            else:
                pdf.ln(5)

            pdf.set_font('helvetica', 'B', 12)
            pdf.set_text_color(46, 125, 50)  # Verde #2E7D32
            pdf.cell(0, 7, "Historial de Check Lists y Mantenimientos", ln=1, border='B')
            pdf.ln(3)

            col_chk = [
                28,               # Fecha
                32,               # Folio / Nº
                38,               # Resultado
                avail_w - 98      # Observaciones / Notas
            ]

            pdf.set_fill_color(34, 36, 54)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font('helvetica', 'B', 9)
            pdf.cell(col_chk[0], 6.5, "Fecha", border=1, fill=True, align='C')
            pdf.cell(col_chk[1], 6.5, "Nº / Folio", border=1, fill=True, align='C')
            pdf.cell(col_chk[2], 6.5, "Resultado", border=1, fill=True, align='C')
            pdf.cell(col_chk[3], 6.5, "Observaciones y Notas", border=1, fill=True, align='C', ln=1)

            for idx, h_item in enumerate(history):
                if pdf.get_y() > pdf.h - 25:
                    pdf.add_page()
                    pdf.set_fill_color(34, 36, 54)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_font('helvetica', 'B', 9)
                    pdf.cell(col_chk[0], 6.5, "Fecha", border=1, fill=True, align='C')
                    pdf.cell(col_chk[1], 6.5, "Nº / Folio", border=1, fill=True, align='C')
                    pdf.cell(col_chk[2], 6.5, "Resultado", border=1, fill=True, align='C')
                    pdf.cell(col_chk[3], 6.5, "Observaciones y Notas", border=1, fill=True, align='C', ln=1)

                if idx % 2 == 0:
                    pdf.set_fill_color(255, 255, 255)
                else:
                    pdf.set_fill_color(245, 247, 250)

                pdf.set_font('helvetica', '', 9)
                pdf.set_text_color(30, 30, 30)

                d_val = clean_pdf_text(str(h_item.get('date', '')))
                pdf.cell(col_chk[0], 6.5, d_val, border=1, fill=True, align='C')
                
                check_num = clean_pdf_text(str(h_item.get('check_number', '')) or 'N/A')
                pdf.cell(col_chk[1], 6.5, check_num, border=1, fill=True, align='C')

                res = str(h_item.get('result', ''))
                if 'aprobado' in res.lower():
                    pdf.set_text_color(46, 125, 50)
                elif 'rechazado' in res.lower() or 'falla' in res.lower():
                    pdf.set_text_color(198, 40, 40)
                else:
                    pdf.set_text_color(230, 81, 0)
                pdf.set_font('helvetica', 'B', 9)
                pdf.cell(col_chk[2], 6.5, clean_pdf_text(res), border=1, fill=True, align='C')

                pdf.set_font('helvetica', '', 8.5)
                pdf.set_text_color(60, 60, 60)
                notes = clean_pdf_text(str(h_item.get('notes', ''))[:65])
                pdf.cell(col_chk[3], 6.5, notes, border=1, fill=True, ln=1)

    # =========================================================================
    # FUSIÓN VECTORIAL DE DOCUMENTACIÓN (Datasheet y Manual)
    # =========================================================================
    docs_to_merge = []
    if options.get('include_datasheet'):
        ds_p = options.get('datasheet_path')
        if ds_p and os.path.isfile(ds_p) and ds_p.lower().endswith('.pdf'):
            docs_to_merge.append((ds_p, options.get('datasheet_pages', 1)))

    if options.get('include_manual'):
        man_p = options.get('manual_path')
        if man_p and os.path.isfile(man_p) and man_p.lower().endswith('.pdf'):
            docs_to_merge.append((man_p, options.get('manual_pages', 1)))

    if docs_to_merge:
        import fitz

        tmp_fd, tmp_inst_path = tempfile.mkstemp(suffix='.pdf')
        os.close(tmp_fd)

        try:
            pdf.output(tmp_inst_path)
            doc_main = fitz.open(tmp_inst_path)

            for doc_path, num_pages in docs_to_merge:
                try:
                    doc_sub = fitz.open(doc_path)
                    if num_pages == 'all' or num_pages == -1:
                        doc_main.insert_pdf(doc_sub)
                    else:
                        max_page_idx = min(len(doc_sub) - 1, int(num_pages) - 1)
                        if max_page_idx >= 0:
                            doc_main.insert_pdf(doc_sub, from_page=0, to_page=max_page_idx)
                    doc_sub.close()
                except Exception as e:
                    print(f"Error fusionando documento {doc_path} en PDF instrumento: {e}")

            doc_main.save(filepath)
            doc_main.close()
        finally:
            if os.path.exists(tmp_inst_path):
                try:
                    os.unlink(tmp_inst_path)
                except Exception:
                    pass
    else:
        pdf.output(filepath)


def get_tool_image_path(tool: dict, agenda_path: str) -> str:
    """Busca la imagen asociada a la herramienta en Biblioteca o en el propio registro."""
    if not tool or not agenda_path:
        return ""

    tool_id = tool.get('id')
    tool_name = str(tool.get('name', '')).lower()
    tool_model = str(tool.get('model', '')).lower()

    # 1. Campo directo 'image' o 'image_path'
    img_prop = tool.get('image') or tool.get('image_path')
    if img_prop and isinstance(img_prop, str):
        candidate = os.path.join(agenda_path, img_prop) if not os.path.isabs(img_prop) else img_prop
        if os.path.isfile(candidate):
            return candidate

    # 2. Documentos de imagen asignados en Biblioteca
    bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
    bib_data = DataStore.load(bib_path)
    if bib_data:
        docs = bib_data.get('documents', [])
        for d in docs:
            rel = d.get('relative_path', '')
            if not rel.lower().endswith(IMAGE_EXTENSIONS):
                continue
            full = os.path.join(agenda_path, rel)
            if not os.path.isfile(full):
                continue

            doc_assigned_ids = d.get('assigned_element_ids', [])
            tags = [str(t).lower() for t in d.get('tags', [])]
            if (tool_id and tool_id in doc_assigned_ids) or (tool_name and tool_name in tags) or (tool_model and tool_model in tags):
                return full

    return ""


def get_tool_documents_and_datasheets(tool: dict, agenda_path: str) -> list:
    """Retorna lista de tuplas (nombre, ruta_absoluta) de manuales o documentos asociados a la herramienta."""
    docs_list = []
    if not tool or not agenda_path:
        return docs_list

    seen_paths = set()
    tool_id = tool.get('id')
    tool_name = str(tool.get('name', '')).lower()
    tool_model = str(tool.get('model', '')).lower()

    # 1. Campo directo 'manual' o 'datasheet'
    for fld in ('manual', 'datasheet', 'document'):
        val = (tool.get(fld) or '').strip()
        if val and val.lower().endswith('.pdf'):
            candidate = val if os.path.isabs(val) else os.path.join(agenda_path, val)
            if not os.path.isfile(candidate):
                cand_bib = os.path.join(agenda_path, 'biblioteca', val)
                if os.path.isfile(cand_bib):
                    candidate = cand_bib
            if os.path.isfile(candidate) and candidate not in seen_paths:
                seen_paths.add(candidate)
                name = os.path.basename(candidate)
                docs_list.append((name, candidate))

    # 2. Buscar en Biblioteca por ID asignado o etiquetas
    bib_path = DataStore.get_plugin_data_path(agenda_path, 'biblioteca')
    bib_data = DataStore.load(bib_path)
    if bib_data:
        docs = bib_data.get('documents', [])
        for d in docs:
            rel = d.get('relative_path', '')
            if not rel.lower().endswith('.pdf'):
                continue
            full = os.path.join(agenda_path, rel)
            if not os.path.isfile(full) or full in seen_paths:
                continue

            doc_assigned_ids = d.get('assigned_element_ids', [])
            tags = [str(t).lower() for t in d.get('tags', [])]
            is_match = False
            if tool_id and tool_id in doc_assigned_ids:
                is_match = True
            elif tool_name and tool_name in tags:
                is_match = True
            elif tool_id and str(tool_id).lower() in tags:
                is_match = True
            elif tool_model and tool_model in tags:
                is_match = True

            if is_match:
                seen_paths.add(full)
                doc_name = d.get('name') or os.path.basename(full)
                docs_list.append((doc_name, full))

    return docs_list


class ToolPDF(FPDF):
    """Generador de PDF para la Ficha Técnica de Herramientas de Taller."""

    def __init__(self, agenda_path: str, page_format: str = 'letter'):
        super().__init__(format=page_format)
        self.agenda_path = agenda_path
        self.page_format = page_format
        self.report_title = "Vito Organizer"
        self.report_subtitle = "Ficha Técnica de Herramienta de Taller"

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
        if self.agenda_path:
            portada_path = DataStore.get_plugin_data_path(self.agenda_path, 'portada')
            portada_data = DataStore.load(portada_path)
            if portada_data:
                self.report_title = portada_data.get('title', self.report_title)

    def header(self):
        # Fondo oscuro institucional #222436 -> R:34, G:36, B:54
        self.set_fill_color(34, 36, 54)
        self.rect(0, 0, self.w, 40, 'F')

        # Dibujar logo institucional si existe
        logo_x = 15
        if self.logo_path and os.path.isfile(self.logo_path):
            try:
                safe_logo = self.logo_path
                if self.logo_path.lower().endswith(('.svg', '.avif', '.webp')):
                    pix = load_image_pixmap(self.logo_path)
                    if not pix.isNull():
                        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                        safe_logo = tmp.name
                        tmp.close()
                        pix.save(safe_logo, "PNG")
                info = self.image(safe_logo, x=15, y=10, h=20)
                if hasattr(info, 'rendered_width'):
                    logo_x = 15 + info.rendered_width + 5
                else:
                    logo_x = 45
            except Exception as e:
                print(f"Error cargando logo en PDF herramienta: {e}")

        # Título y Subtítulo
        self.set_text_color(255, 255, 255)
        self.set_font('helvetica', 'B', 22)
        self.set_xy(logo_x, 12)
        self.cell(0, 10, self.report_title, border=0, ln=1)

        self.set_font('helvetica', 'I', 11)
        self.set_xy(logo_x, 22)
        self.set_text_color(200, 200, 200)
        self.cell(0, 10, self.report_subtitle, border=0, ln=1)

        # Franja divisoria naranja #FF5722 -> R:255, G:87, B:34
        self.set_fill_color(255, 87, 34)
        self.rect(0, 40, self.w, 4, 'F')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Vito Organizer - Página {self.page_no()}', align='R')


def generate_tool_pdf(filepath: str, tool: dict, options: dict, serial_str: str, agenda_path: str):
    """Construye el documento PDF de la ficha de herramienta con imagen, especificaciones, historial de chequeos y documentación."""
    page_format = options.get('page_format', 'letter')
    pdf = ToolPDF(agenda_path, page_format=page_format)
    pdf.set_auto_page_break(True, margin=20)
    pdf.add_page()

    # Bloque de folio y fecha de emisión
    y_top = pdf.get_y()
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(15, y_top)
    pdf.cell(35, 6, "Folio / Correlativo:")
    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(50, 6, serial_str)

    pdf.set_font('helvetica', 'B', 10)
    pdf.set_text_color(50, 50, 50)
    pdf.set_xy(pdf.w - 85, y_top)
    pdf.cell(32, 6, "Fecha Emisión:")
    pdf.set_font('helvetica', '', 10)
    pdf.cell(35, 6, QDate.currentDate().toString("dd/MM/yyyy"))
    pdf.ln(10)

    # Título de sección: Ficha Técnica de la Herramienta
    name = tool.get('name', 'Herramienta')
    brand = tool.get('brand', '')
    model = tool.get('model', '')
    title_sub = f"{name} ({brand} {model})".strip() if (brand or model) else name
    title_sub = clean_pdf_text(title_sub)

    pdf.set_font('helvetica', 'B', 14)
    pdf.set_text_color(255, 87, 34)
    pdf.cell(0, 8, f"Ficha Técnica: {title_sub}", ln=1, border='B')
    pdf.ln(5)

    # Buscar imagen de la herramienta
    img_path = get_tool_image_path(tool, agenda_path)
    img_w = 60
    has_img = False
    safe_img = None
    if img_path and os.path.isfile(img_path):
        try:
            safe_img = img_path
            if img_path.lower().endswith(('.avif', '.webp', '.svg')):
                pix = load_image_pixmap(img_path)
                if not pix.isNull():
                    tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                    safe_img = tmp.name
                    tmp.close()
                    pix.save(safe_img, "PNG")
            has_img = True
        except Exception as e:
            print(f"Error procesando imagen para PDF de herramienta: {e}")
            has_img = False

    avail_w = pdf.w - 30
    meta_w = avail_w - img_w - 5 if has_img else avail_w
    y_meta_start = pdf.get_y()

    def draw_row(label: str, value: str, y_offset: float):
        pdf.set_xy(15, y_meta_start + y_offset)
        pdf.set_font('helvetica', 'B', 9.5)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(46, 6, label)
        pdf.set_font('helvetica', '', 9.5)
        pdf.set_text_color(20, 20, 20)
        pdf.cell(meta_w - 46, 6, clean_pdf_text(str(value)))

    draw_row("Identificador (ID):", tool.get('id', 'N/A'), 0)
    draw_row("Tipo de Herramienta:", tool.get('type', 'Taller / Laboratorio'), 6)
    draw_row("Marca:", tool.get('brand', 'N/A') or 'N/A', 12)
    draw_row("Modelo / Medida:", tool.get('model', 'N/A') or 'N/A', 18)

    status_str = tool.get('status', 'Excelente') or 'Excelente'
    pdf.set_xy(15, y_meta_start + 24)
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(46, 6, "Estado Operativo:")
    if status_str.lower() in ('excelente', 'bueno', 'operativo'):
        pdf.set_text_color(46, 125, 50)  # Verde
    elif status_str.lower() in ('regular', 'en mantenimiento', 'en espera', 'revisión', 'revision'):
        pdf.set_text_color(230, 81, 0)   # Naranja
    else:
        pdf.set_text_color(198, 40, 40)  # Rojo
    pdf.set_font('helvetica', 'B', 9.5)
    pdf.cell(meta_w - 46, 6, clean_pdf_text(status_str))

    loc_str = tool.get('storage_location') or tool.get('location') or 'Taller / Laboratorio'
    draw_row("Ubicación / Almacenaje:", loc_str, 30)

    # Dibujar la fotografía de la herramienta si existe
    meta_h = 40
    if has_img and safe_img:
        try:
            info = pdf.image(safe_img, x=pdf.w - 15 - img_w, y=y_meta_start, w=img_w)
            rendered_h = getattr(info, 'rendered_height', 45)
            meta_h = max(meta_h, rendered_h)
        except Exception as e:
            print(f"Error renderizando imagen en PDF de herramienta: {e}")

    pdf.set_y(y_meta_start + meta_h + 4)

    # Resumen / Observaciones generales si existen
    general_desc = (tool.get('description') or tool.get('notes') or '').strip()
    if general_desc:
        pdf.set_font('helvetica', 'B', 10)
        pdf.set_text_color(34, 36, 54)
        pdf.cell(0, 6, "Descripción y Observaciones:", ln=1)
        pdf.set_font('helvetica', '', 9)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 5, clean_pdf_text(general_desc))
        pdf.ln(3)

    # Documentación asociada en Biblioteca
    assigned_docs = get_tool_documents_and_datasheets(tool, agenda_path)
    if assigned_docs:
        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(0, 77, 64)  # #004D40
        pdf.cell(0, 7, "Documentación y Manuales Asignados:", ln=1)
        pdf.set_font('helvetica', '', 9.5)
        pdf.set_text_color(70, 70, 70)
        for doc_name, _ in assigned_docs:
            clean_name = doc_name.replace("🖼️ ", "").replace("📖 ", "").replace("📄 ", "")
            pdf.set_x(20)
            pdf.cell(0, 5, f"- {clean_name}", ln=1)
        pdf.ln(4)

    # =========================================================================
    # SECCIÓN: Historial de Chequeos y Mantenimientos
    # =========================================================================
    include_history = options.get('include_history', True)
    history = tool.get('history', [])
    if include_history and history:
        if pdf.get_y() > pdf.h - 55:
            pdf.add_page()
        else:
            pdf.ln(4)

        pdf.set_font('helvetica', 'B', 12)
        pdf.set_text_color(46, 125, 50)  # Verde #2E7D32
        pdf.cell(0, 7, "Historial de Chequeos y Mantenimientos", ln=1, border='B')
        pdf.ln(3)

        col_chk = [
            28,               # Fecha
            32,               # Folio / Nº
            38,               # Resultado
            avail_w - 98      # Observaciones / Notas
        ]

        pdf.set_fill_color(34, 36, 54)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('helvetica', 'B', 9)
        pdf.cell(col_chk[0], 6.5, "Fecha", border=1, fill=True, align='C')
        pdf.cell(col_chk[1], 6.5, "Nº / Folio", border=1, fill=True, align='C')
        pdf.cell(col_chk[2], 6.5, "Resultado", border=1, fill=True, align='C')
        pdf.cell(col_chk[3], 6.5, "Observaciones y Notas", border=1, fill=True, align='C', ln=1)

        for idx, h_item in enumerate(history):
            if pdf.get_y() > pdf.h - 25:
                pdf.add_page()
                pdf.set_fill_color(34, 36, 54)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font('helvetica', 'B', 9)
                pdf.cell(col_chk[0], 6.5, "Fecha", border=1, fill=True, align='C')
                pdf.cell(col_chk[1], 6.5, "Nº / Folio", border=1, fill=True, align='C')
                pdf.cell(col_chk[2], 6.5, "Resultado", border=1, fill=True, align='C')
                pdf.cell(col_chk[3], 6.5, "Observaciones y Notas", border=1, fill=True, align='C', ln=1)

            if idx % 2 == 0:
                pdf.set_fill_color(255, 255, 255)
            else:
                pdf.set_fill_color(245, 247, 250)

            pdf.set_font('helvetica', '', 9)
            pdf.set_text_color(30, 30, 30)

            d_val = clean_pdf_text(str(h_item.get('date', '')))
            pdf.cell(col_chk[0], 6.5, d_val, border=1, fill=True, align='C')

            check_num = clean_pdf_text(str(h_item.get('check_number', '')) or 'N/A')
            pdf.cell(col_chk[1], 6.5, check_num, border=1, fill=True, align='C')

            res = str(h_item.get('result', ''))
            if 'aprobado' in res.lower() or 'conforme' in res.lower() or 'excelente' in res.lower() or 'bueno' in res.lower():
                pdf.set_text_color(46, 125, 50)
            elif 'rechazado' in res.lower() or 'falla' in res.lower() or 'malo' in res.lower() or 'daño' in res.lower():
                pdf.set_text_color(198, 40, 40)
            else:
                pdf.set_text_color(230, 81, 0)
            pdf.set_font('helvetica', 'B', 9)
            pdf.cell(col_chk[2], 6.5, clean_pdf_text(res), border=1, fill=True, align='C')

            pdf.set_font('helvetica', '', 8.5)
            pdf.set_text_color(60, 60, 60)
            notes = clean_pdf_text(str(h_item.get('notes', ''))[:65])
            pdf.cell(col_chk[3], 6.5, notes, border=1, fill=True, ln=1)

    # =========================================================================
    # FUSIÓN VECTORIAL DE DOCUMENTACIÓN (Manual o Hoja Técnica)
    # =========================================================================
    include_doc = options.get('include_document')
    doc_p = options.get('document_path')
    if include_doc and doc_p and os.path.isfile(doc_p) and doc_p.lower().endswith('.pdf'):
        import fitz

        tmp_fd, tmp_tool_path = tempfile.mkstemp(suffix='.pdf')
        os.close(tmp_fd)

        try:
            pdf.output(tmp_tool_path)
            doc_main = fitz.open(tmp_tool_path)
            doc_sub = fitz.open(doc_p)

            num_pages = options.get('document_pages', 1)
            if num_pages == 'all' or num_pages == -1:
                doc_main.insert_pdf(doc_sub)
            else:
                max_page_idx = min(len(doc_sub) - 1, int(num_pages) - 1)
                if max_page_idx >= 0:
                    doc_main.insert_pdf(doc_sub, from_page=0, to_page=max_page_idx)

            doc_sub.close()
            doc_main.save(filepath)
            doc_main.close()
        except Exception as e:
            print(f"Error fusionando documento en PDF de herramienta: {e}")
            pdf.output(filepath)
        finally:
            if os.path.exists(tmp_tool_path):
                try:
                    os.unlink(tmp_tool_path)
                except Exception:
                    pass
    else:
        pdf.output(filepath)



