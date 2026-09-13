import os
from fpdf import FPDF
from config.settings import Settings
from data.data_store import DataStore

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
