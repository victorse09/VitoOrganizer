# =============================================================================
# Vito Organizer v2.2 - Calendar Views
# Vistas del calendario (Día, Semana, Mes, etc.)
# =============================================================================

from PyQt6.QtCore import Qt, QDate, QRectF, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QStackedWidget

def format_time_display(t_str: str, fmt: str = '24h') -> str:
    if not t_str:
        return ""
    if fmt == '12h':
        try:
            h, m = map(int, t_str.split(':'))
            am_pm = "AM" if h < 12 else "PM"
            h_12 = h % 12
            if h_12 == 0:
                h_12 = 12
            return f"{h_12:02d}:{m:02d} {am_pm}"
        except:
            return t_str
    return t_str

def event_matches_date(ev: dict, qdate: QDate) -> bool:
    ev_date_str = ev.get('date')
    if not ev_date_str:
        return False
    ev_type = ev.get('event_type') or ev.get('type')
    if ev_type in ('birthday', 'anniversary', 'holiday'):
        try:
            parts = ev_date_str.split('-')
            if len(parts) >= 3:
                return int(parts[1]) == qdate.month() and int(parts[2]) == qdate.day()
        except:
            pass
    return ev_date_str == qdate.toString("yyyy-MM-dd")

def get_event_title(ev: dict, target_date: QDate) -> str:
    title = ev.get('title', 'Evento')
    if ev.get('event_type') == 'birthday':
        orig = ev.get('original_event', {})
        orig_age = orig.get('age', 0)
        orig_date_str = orig.get('date', '')
        if orig_age and orig_date_str:
            try:
                birth_year = int(orig_date_str.split('-')[0]) - orig_age
                current_age = target_date.year() - birth_year
                return f"🎂 {orig.get('name', '')} ({current_age} años)"
            except:
                pass
    return title

class DayView(QWidget):
    """Vista de Día a la Vista."""
    
    create_event_requested = pyqtSignal(str) # Emite hora inicio ("14:00")
    edit_event_requested = pyqtSignal(dict) # Emite el diccionario del evento

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.date = QDate.currentDate()
        self.events = []
        self.time_format = '24h'
        self._drawn_events = [] # Guardará (QRectF, ev_dict)

    def set_date(self, date: QDate):
        self.date = date
        self.update()
        
    def set_events(self, events: list):
        self.events = events
        self.update()

    def set_time_format(self, fmt: str):
        self.time_format = fmt
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        self._drawn_events.clear()
        
        header_h = 40
        y_start = header_h + 10
        hour_h = 40
        x_margin = 75 if self.time_format == '12h' else 60
        right_margin = 30
        
        # 2. Header (Date)
        header_rect = QRectF(10, 5, rect.width() - 10 - right_margin, header_h - 10)
        painter.fillRect(header_rect, QColor("#FFFFFF"))
        
        # Dashed border
        pen = QPen(QColor("#000000"))
        pen.setStyle(Qt.PenStyle.DashLine)
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawRect(header_rect)
        
        # Date text
        d = self.date.toPyDate()
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        left_text = f"{dias[d.weekday()]} {d.day}"
        right_text = f"{meses[d.month-1]} {d.year}"
        
        is_red_day = (self.date.dayOfWeek() == 7) or any(event_matches_date(ev, self.date) and (ev.get('event_type')=='holiday' or ev.get('type')=='holiday') for ev in self.events)
        painter.setPen(QColor("#D32F2F") if is_red_day else QColor("#8B0000")) # Red if Sunday or Holiday
        font = QFont("Arial", 12, QFont.Weight.Bold)
        painter.setFont(font)
        
        painter.drawText(header_rect.adjusted(10, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, left_text)
        painter.drawText(header_rect.adjusted(0, 0, -10, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, right_text)
        
        # 3. Vertical line separating hours from lines
        painter.setPen(QPen(QColor("#000000"), 1))
        painter.drawLine(x_margin, y_start, x_margin, y_start + (22-7+1)*hour_h)
        
        # 4. Horarios y líneas
        font = QFont("Arial", 8 if self.time_format == '12h' else 9)
        painter.setFont(font)
        
        for i in range(7, 24):
            y = y_start + (i - 7) * hour_h
            
            # Texto hora
            if i < 23:
                painter.setPen(QColor("#000000"))
                time_text = format_time_display(f"{i:02d}:00", self.time_format)
                painter.drawText(QRectF(0, y - 10, x_margin - 5, 20), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, time_text)
            
            # Línea hora
            pen = QPen(QColor("#D0C070"), 1)
            painter.setPen(pen)
            painter.drawLine(x_margin, int(y), int(rect.width() - right_margin), int(y))
            
            # Media hora
            if i < 23:
                pen = QPen(QColor("#D0C070"), 1)
                pen.setStyle(Qt.PenStyle.DotLine)
                painter.setPen(pen)
                painter.drawLine(x_margin, int(y + hour_h/2), int(rect.width() - right_margin), int(y + hour_h/2))
                
        # Dibujar eventos
        for ev in self.events:
            if event_matches_date(ev, self.date):
                title = get_event_title(ev, self.date)
                start_str = ev.get('start_time', '08:00')
                end_str = ev.get('end_time', '09:00')
                all_day = ev.get('all_day', False)
                
                try:
                    sh, sm = map(int, start_str.split(':'))
                    eh, em = map(int, end_str.split(':'))
                except:
                    sh, sm, eh, em = 8, 0, 9, 0
                    
                if all_day:
                    sh, sm, eh, em = 8, 0, 17, 0
                    
                y1 = y_start + (sh - 7 + sm/60.0) * hour_h
                y2 = y_start + (eh - 7 + em/60.0) * hour_h
                if y2 <= y1:
                    y2 = y1 + 30
                    
                ev_rect = QRectF(x_margin + 5, y1 + 2, rect.width() - x_margin - right_margin - 10, y2 - y1 - 4)
                self._drawn_events.append((ev_rect, ev))
                
                painter.fillRect(ev_rect, QColor("#E0F7FA"))
                painter.setPen(QPen(QColor("#00838F"), 1.5))
                painter.drawRoundedRect(ev_rect, 4, 4)
                
                painter.setPen(QColor("#004D40"))
                font_ev = QFont("Arial", 9, QFont.Weight.Bold)
                painter.setFont(font_ev)
                
                st_disp = format_time_display(start_str, self.time_format)
                et_disp = format_time_display(end_str, self.time_format)
                time_info = f"{st_disp}-{et_disp}" if not all_day else "Todo el día"
                painter.drawText(ev_rect.adjusted(6, 4, -6, -4), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"📌 {title} ({time_info})")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            # Verificar si se hizo click sobre un evento existente
            for ev_rect, ev in self._drawn_events:
                if ev_rect.contains(pos):
                    return # Si es sobre evento, dejar que lo maneje el doble click o selección
                    
            # Si es en una hora vacía
            header_h = 40
            y_start = header_h + 10
            hour_h = 40
            x_margin = 60
            
            if pos.x() >= x_margin and pos.y() >= y_start:
                hour = int(7 + (pos.y() - y_start) // hour_h)
                hour = max(7, min(22, hour))
                time_str = f"{hour:02d}:00"
                self.create_event_requested.emit(time_str)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            for ev_rect, ev in self._drawn_events:
                if ev_rect.contains(pos):
                    self.edit_event_requested.emit(ev)
                    return
        super().mouseDoubleClickEvent(event)

class RightSideView(QWidget):
    """Vista de la página derecha para el modo Día (Tareas, Llamadas, Notas)."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []
        self.time_format = '24h'

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def set_time_format(self, fmt: str):
        self.time_format = fmt
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Margins
        m_left = 30
        m_right = 10
        m_top = 10
        m_bottom = 10
        
        available_h = rect.height() - m_top - m_bottom
        h_tasks = available_h * 0.4
        h_calls = available_h * 0.25
        h_notes = available_h * 0.35
        
        y_current = m_top
        
        # 1. Tasks
        self.draw_section(painter, m_left, y_current, rect.width() - m_left - m_right, h_tasks, "Tasks", 1)
        y_current += h_tasks
        
        # 2. Calls
        self.draw_section(painter, m_left, y_current, rect.width() - m_left - m_right, h_calls, "Calls", 2)
        y_current += h_calls
        
        # 3. Daily Notes
        self.draw_section(painter, m_left, y_current, rect.width() - m_left - m_right, h_notes, "Daily Notes", 3)

    def draw_section(self, painter, x, y, w, h, title, section_type):
        header_h = 24
        header_rect = QRectF(x, y, w, header_h)
        
        # 3D Bevel for header
        painter.fillRect(header_rect, QColor("#FDF18C"))
        
        # Bevel highlights and shadows
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawLine(int(x), int(y), int(x+w), int(y))
        painter.drawLine(int(x), int(y), int(x), int(y+header_h))
        
        painter.setPen(QPen(QColor("#BDB76B"), 1))
        painter.drawLine(int(x), int(y+header_h), int(x+w), int(y+header_h))
        painter.drawLine(int(x+w), int(y), int(x+w), int(y+header_h))
        
        # Title text
        painter.setPen(QColor("#000000"))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(header_rect.adjusted(30, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title)
        
        # Mock Icon
        icon_rect = QRectF(x + 6, y + 4, 16, 16)
        painter.fillRect(icon_rect, QColor("#E0E0E0"))
        painter.setPen(QPen(QColor("#808080"), 1))
        painter.drawRect(icon_rect)
        if section_type == 1:
            painter.setPen(QColor("#FF0000")) # Red checkmark mock
            painter.drawLine(int(icon_rect.left()+3), int(icon_rect.center().y()), int(icon_rect.center().x()), int(icon_rect.bottom()-3))
            painter.drawLine(int(icon_rect.center().x()), int(icon_rect.bottom()-3), int(icon_rect.right()-3), int(icon_rect.top()+3))
        elif section_type == 2:
            painter.setPen(QColor("#0000FF")) # Blue phone mock
            painter.drawEllipse(icon_rect.adjusted(2, 2, -2, -2))
        elif section_type == 3:
            painter.setPen(QColor("#008000")) # Green notes mock
            painter.drawLine(int(icon_rect.left()+4), int(icon_rect.top()+4), int(icon_rect.right()-4), int(icon_rect.top()+4))
            painter.drawLine(int(icon_rect.left()+4), int(icon_rect.top()+8), int(icon_rect.right()-4), int(icon_rect.top()+8))
            painter.drawLine(int(icon_rect.left()+4), int(icon_rect.top()+12), int(icon_rect.right()-8), int(icon_rect.top()+12))
            
        # Content Area
        content_rect = QRectF(x, y + header_h, w, h - header_h)
            
        # Draw border for content
        painter.setPen(QPen(QColor("#A0A0A0"), 1))
        painter.drawRect(content_rect)
        
        # Grids and Lines
        painter.setPen(QPen(QColor("#D0C070"), 1))
        row_h = 20
        num_rows = int(content_rect.height() // row_h)
        
        for i in range(1, num_rows + 1):
            line_y = y + header_h + i * row_h
            if line_y < y + h:
                painter.drawLine(int(x), int(line_y), int(x + w), int(line_y))
                
        # Columns
        if section_type == 1: # Tasks
            painter.setPen(QPen(QColor("#A0A0A0"), 1))
            painter.drawLine(int(x + 25), int(y + header_h), int(x + 25), int(y + h))
            painter.drawLine(int(x + 50), int(y + header_h), int(x + 50), int(y + h))
            
            painter.setPen(QPen(QColor("#808080"), 1))
            for i in range(num_rows):
                line_y = y + header_h + i * row_h
                if line_y + 16 <= y + h:
                    painter.drawRect(int(x + 6), int(line_y + 4), 12, 12)
                
        elif section_type == 2: # Calls
            painter.setPen(QPen(QColor("#A0A0A0"), 1))
            painter.drawLine(int(x + 25), int(y + header_h), int(x + 25), int(y + h))
            
            painter.setPen(QPen(QColor("#808080"), 1))
            for i in range(num_rows):
                line_y = y + header_h + i * row_h
                if line_y + 16 <= y + h:
                    painter.drawRect(int(x + 6), int(line_y + 4), 12, 12)
                
        elif section_type == 3: # Daily Notes
            painter.setPen(QPen(QColor("#FF4040"), 1))
            painter.drawLine(int(x + 30), int(y + header_h), int(x + 30), int(y + h))
            painter.drawLine(int(x + 32), int(y + header_h), int(x + 32), int(y + h))


# =============================================================================
# Helper para dibujar minicalendarios
# =============================================================================

def is_holiday_or_sunday(qdate: QDate, events: list = None) -> bool:
    if qdate.dayOfWeek() == 7: # Sunday
        return True
    if events:
        for ev in events:
            if event_matches_date(ev, qdate):
                if ev.get('event_type') == 'holiday' or ev.get('type') == 'holiday':
                    return True
    return False

def draw_mini_month(painter: QPainter, rect: QRectF, year: int, month: int, highlight_date: QDate, events: list = None):
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    hdr_rect = QRectF(rect.left(), rect.top(), rect.width(), 18)
    painter.fillRect(hdr_rect, QColor("#EAE6D0"))
    painter.setPen(QPen(QColor("#8B0000"), 1))
    painter.drawRect(hdr_rect)
    painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
    painter.drawText(hdr_rect, Qt.AlignmentFlag.AlignCenter, f"{meses[month-1]} {year}")
    
    days_hdr = ["L", "M", "X", "J", "V", "S", "D"]
    cell_w = rect.width() / 7.0
    cell_h = (rect.height() - 32) / 6.0
    
    painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
    for i, d in enumerate(days_hdr):
        painter.setPen(QColor("#D32F2F") if i == 6 else QColor("#000000"))
        painter.drawText(QRectF(rect.left() + i*cell_w, rect.top() + 18, cell_w, 14), Qt.AlignmentFlag.AlignCenter, d)
        
    first = QDate(year, month, 1)
    start = first.addDays(1 - first.dayOfWeek())

    painter.setFont(QFont("Arial", 7))
    for r in range(6):
        for c in range(7):
            cur = start.addDays(r*7 + c)
            c_rect = QRectF(rect.left() + c*cell_w, rect.top() + 32 + r*cell_h, cell_w, cell_h)
            if cur.month() == month:
                if cur == highlight_date:
                    painter.fillRect(c_rect, QColor("#FDF18C"))
                
                is_red = is_holiday_or_sunday(cur, events)
                painter.setPen(QColor("#D32F2F") if is_red else QColor("#000000"))
                painter.drawText(c_rect, Qt.AlignmentFlag.AlignCenter, str(cur.day()))
                
                if events and any(event_matches_date(ev, cur) for ev in events):
                    painter.setBrush(QBrush(QColor("#D32F2F") if is_red else QColor("#00838F")))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawEllipse(int(c_rect.center().x() - 2), int(c_rect.bottom() - 3), 4, 4)


# =============================================================================
# Vistas de Semana (Week Views)
# =============================================================================

class WeekLeftView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []
        self.time_format = '24h'

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def set_time_format(self, fmt: str):
        self.time_format = fmt
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        day_of_week = self.date.dayOfWeek()
        monday = self.date.addDays(1 - day_of_week)
        
        dias = ["Lunes", "Martes", "Miércoles"]
        m_top, m_left, m_right, m_bottom = 15, 10, 30, 15
        available_h = rect.height() - m_top - m_bottom
        slot_h = available_h / 3.0
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        for i in range(3):
            current_day = monday.addDays(i)
            cur_str = current_day.toString("yyyy-MM-dd")
            y = m_top + i * slot_h
            w = rect.width() - m_left - m_right
            
            h_rect = QRectF(m_left, y, w, 22)
            painter.fillRect(h_rect, QColor("#FDF18C") if current_day == self.date else QColor("#EAE6D0"))
            painter.setPen(QPen(QColor("#8B0000"), 1))
            painter.drawRect(h_rect)
            
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            text = f"{dias[i]} {current_day.day()} {meses[current_day.month()-1]}"
            painter.drawText(h_rect.adjusted(8, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
            
            content_h = slot_h - 26
            num_lines = int(content_h // 18)
            painter.setPen(QPen(QColor("#D0C070"), 1))
            for line_idx in range(1, num_lines + 1):
                line_y = y + 22 + line_idx * 18
                painter.drawLine(int(m_left), int(line_y), int(m_left + w), int(line_y))

            # Render events for this day
            day_events = [ev for ev in self.events if event_matches_date(ev, current_day)]
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor("#004D40"))
            for ev_idx, ev in enumerate(day_events[:num_lines]):
                line_y = y + 22 + (ev_idx + 1) * 18
                st_disp = format_time_display(ev.get('start_time',''), self.time_format)
                title = get_event_title(ev, current_day)
                t_str = f"📌 {st_disp} {title}"
                painter.drawText(QRectF(m_left + 10, line_y - 16, w - 15, 16), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, t_str)


class WeekRightView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []
        self.time_format = '24h'

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def set_time_format(self, fmt: str):
        self.time_format = fmt
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        day_of_week = self.date.dayOfWeek()
        monday = self.date.addDays(1 - day_of_week)
        
        dias = ["Jueves", "Viernes", "Sábado", "Domingo"]
        m_top, m_left, m_right, m_bottom = 15, 30, 10, 15
        available_h = rect.height() - m_top - m_bottom
        slot_h = available_h / 3.0
        w = rect.width() - m_left - m_right
        meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        
        for i in range(2):
            current_day = monday.addDays(3 + i)
            cur_str = current_day.toString("yyyy-MM-dd")
            y = m_top + i * slot_h
            h_rect = QRectF(m_left, y, w, 22)
            painter.fillRect(h_rect, QColor("#FDF18C") if current_day == self.date else QColor("#EAE6D0"))
            painter.setPen(QPen(QColor("#8B0000"), 1))
            painter.drawRect(h_rect)
            
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            text = f"{dias[i]} {current_day.day()} {meses[current_day.month()-1]}"
            painter.drawText(h_rect.adjusted(8, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
            
            content_h = slot_h - 26
            num_lines = int(content_h // 18)
            painter.setPen(QPen(QColor("#D0C070"), 1))
            for line_idx in range(1, num_lines + 1):
                line_y = y + 22 + line_idx * 18
                painter.drawLine(int(m_left), int(line_y), int(m_left + w), int(line_y))

            day_events = [ev for ev in self.events if event_matches_date(ev, current_day)]
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.setPen(QColor("#004D40"))
            for ev_idx, ev in enumerate(day_events[:num_lines]):
                line_y = y + 22 + (ev_idx + 1) * 18
                st_disp = format_time_display(ev.get('start_time',''), self.time_format)
                title = get_event_title(ev, current_day)
                t_str = f"📌 {st_disp} {title}"
                painter.drawText(QRectF(m_left + 10, line_y - 16, w - 15, 16), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, t_str)
                
        y = m_top + 2 * slot_h
        half_w = (w - 10) / 2.0
        for i in range(2):
            current_day = monday.addDays(5 + i)
            cur_str = current_day.toString("yyyy-MM-dd")
            x_pos = m_left + i * (half_w + 10)
            h_rect = QRectF(x_pos, y, half_w, 22)
            painter.fillRect(h_rect, QColor("#FDF18C") if current_day == self.date else QColor("#EAE6D0"))
            painter.setPen(QPen(QColor("#8B0000"), 1))
            painter.drawRect(h_rect)
            
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            text = f"{dias[2+i]} {current_day.day()}"
            painter.drawText(h_rect.adjusted(4, 0, 0, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
            
            content_h = slot_h - 26
            num_lines = int(content_h // 18)
            painter.setPen(QPen(QColor("#D0C070"), 1))
            for line_idx in range(1, num_lines + 1):
                line_y = y + 22 + line_idx * 18
                painter.drawLine(int(x_pos), int(line_y), int(x_pos + half_w), int(line_y))

            day_events = [ev for ev in self.events if event_matches_date(ev, current_day)]
            painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
            painter.setPen(QColor("#004D40"))
            for ev_idx, ev in enumerate(day_events[:num_lines]):
                line_y = y + 22 + (ev_idx + 1) * 18
                title = get_event_title(ev, current_day)
                t_str = f"📌 {title}"
                painter.drawText(QRectF(x_pos + 4, line_y - 16, half_w - 6, 16), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, t_str)


# =============================================================================
# Vistas de Mes (Month Views)
# =============================================================================

class MonthLeftView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        m_top, m_left, m_right, m_bottom = 15, 10, 30, 15
        w = rect.width() - m_left - m_right
        h = rect.height() - m_top - m_bottom
        
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        title_rect = QRectF(m_left, m_top, w, 24)
        painter.fillRect(title_rect, QColor("#FFFFFF"))
        painter.setPen(QPen(QColor("#8B0000"), 1))
        painter.drawRect(title_rect)
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, f"{meses[self.date.month()-1]} {self.date.year()}")
        
        grid_y = m_top + 28
        grid_h = h - 28
        col_w = w / 3.0
        num_rows = 5
        row_h = (grid_h - 20) / num_rows
        
        dias_hdr = ["Lunes", "Martes", "Miércoles"]
        first_of_month = QDate(self.date.year(), self.date.month(), 1)
        start_date = first_of_month.addDays(1 - first_of_month.dayOfWeek())
        
        for c in range(3):
            hdr_rect = QRectF(m_left + c*col_w, grid_y, col_w, 20)
            painter.fillRect(hdr_rect, QColor("#EAE6D0"))
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawRect(hdr_rect)
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(hdr_rect, Qt.AlignmentFlag.AlignCenter, dias_hdr[c])
            
            for r in range(num_rows):
                day_date = start_date.addDays(r*7 + c)
                day_str = day_date.toString("yyyy-MM-dd")
                cell_rect = QRectF(m_left + c*col_w, grid_y + 20 + r*row_h, col_w, row_h)
                
                if day_date == self.date:
                    painter.fillRect(cell_rect, QColor("#FFF8DC"))
                elif day_date.month() != self.date.month():
                    painter.fillRect(cell_rect, QColor(0, 0, 0, 10))
                    
                painter.setPen(QPen(QColor("#D0C070"), 1))
                painter.drawRect(cell_rect)
                
                is_red = is_holiday_or_sunday(day_date, self.events)
                pen_color = QColor("#D32F2F") if is_red else (QColor("#8B0000") if day_date.month() == self.date.month() else QColor("#A0A0A0"))
                painter.setPen(pen_color)
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(cell_rect.adjusted(2, 2, -4, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, str(day_date.day()))

                # Events in cell
                day_events = [ev for ev in self.events if event_matches_date(ev, day_date)]
                if day_events:
                    painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                    painter.setPen(QColor("#00838F"))
                    for ev_idx, ev in enumerate(day_events[:2]):
                        title = get_event_title(ev, day_date)
                        painter.drawText(cell_rect.adjusted(4, 16 + ev_idx*12, -2, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"📌 {title}")


class MonthRightView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        
        m_top, m_left, m_right, m_bottom = 15, 30, 10, 15
        w = rect.width() - m_left - m_right
        h = rect.height() - m_top - m_bottom
        
        grid_y = m_top + 28
        grid_h = h - 28
        col_w = w / 4.0
        num_rows = 5
        row_h = (grid_h - 20) / num_rows
        
        dias_hdr = ["Jueves", "Viernes", "Sábado", "Domingo"]
        first_of_month = QDate(self.date.year(), self.date.month(), 1)
        start_date = first_of_month.addDays(1 - first_of_month.dayOfWeek())
        
        for c in range(4):
            hdr_rect = QRectF(m_left + c*col_w, grid_y, col_w, 20)
            painter.fillRect(hdr_rect, QColor("#EAE6D0"))
            painter.setPen(QPen(QColor("#000000"), 1))
            painter.drawRect(hdr_rect)
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            painter.drawText(hdr_rect, Qt.AlignmentFlag.AlignCenter, dias_hdr[c])
            
            for r in range(num_rows):
                day_date = start_date.addDays(r*7 + (3 + c))
                day_str = day_date.toString("yyyy-MM-dd")
                cell_rect = QRectF(m_left + c*col_w, grid_y + 20 + r*row_h, col_w, row_h)
                
                if day_date == self.date:
                    painter.fillRect(cell_rect, QColor("#FFF8DC"))
                elif day_date.month() != self.date.month():
                    painter.fillRect(cell_rect, QColor(0, 0, 0, 10))
                    
                painter.setPen(QPen(QColor("#D0C070"), 1))
                painter.drawRect(cell_rect)
                
                is_red = is_holiday_or_sunday(day_date, self.events)
                pen_color = QColor("#D32F2F") if is_red else (QColor("#8B0000") if day_date.month() == self.date.month() else QColor("#A0A0A0"))
                painter.setPen(pen_color)
                painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                painter.drawText(cell_rect.adjusted(2, 2, -4, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, str(day_date.day()))

                day_events = [ev for ev in self.events if event_matches_date(ev, day_date)]
                if day_events:
                    painter.setFont(QFont("Arial", 7, QFont.Weight.Bold))
                    painter.setPen(QColor("#00838F"))
                    for ev_idx, ev in enumerate(day_events[:2]):
                        title = get_event_title(ev, day_date)
                        painter.drawText(cell_rect.adjusted(4, 16 + ev_idx*12, -2, 0), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, f"📌 {title}")


# =============================================================================
# Vistas de Semestre y Año (Semester & Year Views)
# =============================================================================

class SemesterLeftView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        m_top, m_left, m_right, m_bottom = 15, 10, 30, 15
        w = rect.width() - m_left - m_right
        h = rect.height() - m_top - m_bottom
        
        sem = 1 if self.date.month() <= 6 else 2
        start_month = 1 if sem == 1 else 7
        
        slot_h = h / 3.0
        for i in range(3):
            m_rect = QRectF(m_left, m_top + i*slot_h, w, slot_h - 10)
            draw_mini_month(painter, m_rect, self.date.year(), start_month + i, self.date, self.events)


class SemesterRightView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        m_top, m_left, m_right, m_bottom = 15, 30, 10, 15
        w = rect.width() - m_left - m_right
        h = rect.height() - m_top - m_bottom
        
        sem = 1 if self.date.month() <= 6 else 2
        start_month = 4 if sem == 1 else 10
        
        slot_h = h / 3.0
        for i in range(3):
            m_rect = QRectF(m_left, m_top + i*slot_h, w, slot_h - 10)
            draw_mini_month(painter, m_rect, self.date.year(), start_month + i, self.date, self.events)


class YearLeftView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        m_top, m_left, m_right, m_bottom = 15, 10, 30, 15
        w = rect.width() - m_left - m_right
        h = rect.height() - m_top - m_bottom
        
        col_w = (w - 10) / 2.0
        row_h = h / 3.0
        
        for i in range(6):
            r = i // 2
            c = i % 2
            m_rect = QRectF(m_left + c*(col_w + 10), m_top + r*row_h, col_w, row_h - 10)
            draw_mini_month(painter, m_rect, self.date.year(), 1 + i, self.date, self.events)


class YearRightView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.date = QDate.currentDate()
        self.events = []

    def set_date(self, date: QDate):
        self.date = date
        self.update()

    def set_events(self, events: list):
        self.events = events
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect()
        m_top, m_left, m_right, m_bottom = 15, 30, 10, 15
        w = rect.width() - m_left - m_right
        h = rect.height() - m_top - m_bottom
        
        col_w = (w - 10) / 2.0
        row_h = h / 3.0
        
        for i in range(6):
            r = i // 2
            c = i % 2
            m_rect = QRectF(m_left + c*(col_w + 10), m_top + r*row_h, col_w, row_h - 10)
            draw_mini_month(painter, m_rect, self.date.year(), 7 + i, self.date, self.events)

class DayRightContainer(QStackedWidget):
    """Contenedor para la página derecha de la vista Día a la Vista.
    Permite alternar entre la vista del día siguiente y el resumen del día."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet('background: transparent;')
        
        self.next_day_view = DayView(self)
        self.summary_view = RightSideView(self)
        
        self.addWidget(self.next_day_view) # index 0
        self.addWidget(self.summary_view)  # index 1
        
        self.current_date = QDate.currentDate()
        self.events = []
        self.time_format = '24h'
        self.mode = 'next_day'
        self.set_date(self.current_date)
        
    def set_date(self, date: QDate):
        self.current_date = date
        self.next_day_view.set_date(date.addDays(1))
        self.summary_view.set_date(date)
        
    def set_events(self, events: list):
        self.events = events
        self.next_day_view.set_events(events)
        self.summary_view.set_events(events)
        
    def set_time_format(self, fmt: str):
        self.time_format = fmt
        self.next_day_view.set_time_format(fmt)
        self.summary_view.set_time_format(fmt)
        
    def set_mode(self, mode: str):
        self.mode = mode
        if mode == 'summary':
            self.setCurrentIndex(1)
        else:
            self.setCurrentIndex(0)
