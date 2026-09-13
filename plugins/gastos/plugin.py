import os
import uuid
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QButtonGroup, QComboBox, QProgressBar,
    QStackedWidget, QMessageBox
)

from plugins.plugin_base import PluginBase
from data.data_store import DataStore
from plugins.gastos.dialogs import (
    TransactionDialog, CategoryManagerDialog, BudgetDialog, GastosSettingsDialog, AccountManagerDialog
)

CATEGORY_ICONS = {
    'Alimentación': '🛒', 'Transporte': '🚗', 'Servicios Básicos': '💡',
    'Salud': '🏥', 'Educación': '📚', 'Entretenimiento': '🎮',
    'Hogar': '🏠', 'Vestimenta': '👔', 'Tecnología': '💻', 'Otros': '📦',
    'Salario': '💼', 'Freelance': '🖥️', 'Ventas': '🏪',
    'Inversiones': '📈', 'Otros Ingresos': '💵'
}

def _format_amount(amount: float, symbol: str) -> str:
    """Format with thousands separator (dot), 2 decimals if has cents."""
    if amount == int(amount):
        s = f"{int(amount):,}".replace(',', '.')
    else:
        parts = f"{amount:,.2f}".split('.')
        s = parts[0].replace(',', '.') + ',' + parts[1]
    return f"{symbol} {s}"

def _get_month_label(month_key: str) -> str:
    MONTHS = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    try:
        y, m = month_key.split('-')
        return f"{MONTHS[int(m)]} {y}"
    except:
        return month_key

class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class GastosSidebar(QWidget):
    add_expense_clicked = pyqtSignal()
    add_income_clicked = pyqtSignal()
    filter_changed = pyqtSignal(str)
    month_changed = pyqtSignal(str)
    manage_categories_clicked = pyqtSignal()
    manage_budgets_clicked = pyqtSignal()
    manage_accounts_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(12)

        # Action Buttons
        self.btn_exp = QPushButton(' Nuevo Gasto')
        self.btn_inc = QPushButton(' Nuevo Ingreso')
        self.btn_exp.setStyleSheet("QPushButton { text-align: left; padding: 8px 12px; border-radius: 6px; font-weight: bold; background-color: #f38ba8; color: #11111b; } QPushButton:hover { background-color: #e78284; }")
        self.btn_inc.setStyleSheet("QPushButton { text-align: left; padding: 8px 12px; border-radius: 6px; font-weight: bold; background-color: #a6e3a1; color: #11111b; } QPushButton:hover { background-color: #94e28f; }")
        self.btn_exp.clicked.connect(self.add_expense_clicked.emit)
        self.btn_inc.clicked.connect(self.add_income_clicked.emit)
        layout.addWidget(self.btn_exp)
        layout.addWidget(self.btn_inc)

        line1 = QFrame(); line1.setFrameShape(QFrame.Shape.HLine); line1.setStyleSheet("color: rgba(255,255,255,0.2);")
        layout.addWidget(line1)

        # Month Selector
        lbl_period = QLabel('Período')
        lbl_period.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_period)
        self.month_combo = QComboBox()
        self.month_combo.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px;")
        self.month_combo.currentIndexChanged.connect(self._on_month_index_changed)
        layout.addWidget(self.month_combo)

        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine); line2.setStyleSheet("color: rgba(255,255,255,0.2);")
        layout.addWidget(line2)

        # Filters
        lbl_filter = QLabel('Filtros')
        lbl_filter.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_filter)
        self.filter_group = QButtonGroup(self)
        filters = [('all', ' Todos'), ('expense', ' 💸 Gastos'), ('income', ' 💰 Ingresos')]
        for i, (fid, fname) in enumerate(filters):
            btn = QPushButton(fname)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 6px 10px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #f9e2af; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)
            btn.clicked.connect(lambda checked, f=fid: self.filter_changed.emit(f))
            self.filter_group.addButton(btn, i)
            layout.addWidget(btn)
            if fid == 'all': btn.setChecked(True)

        layout.addStretch()

        # Summary
        self.summary_frame = QFrame()
        self.summary_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; }")
        s_layout = QVBoxLayout(self.summary_frame)
        s_layout.setContentsMargins(8, 8, 8, 8)
        self.lbl_income = QLabel("Ingresos: $0")
        self.lbl_income.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 11px;")
        self.lbl_expense = QLabel("Gastos: $0")
        self.lbl_expense.setStyleSheet("color: #f38ba8; font-weight: bold; font-size: 11px;")
        self.lbl_balance = QLabel("Balance: $0")
        self.lbl_balance.setStyleSheet("color: #cdd6f4; font-weight: bold; font-size: 11px;")
        s_layout.addWidget(self.lbl_income)
        s_layout.addWidget(self.lbl_expense)
        s_layout.addWidget(self.lbl_balance)
        self.budget_bar = QProgressBar()
        self.budget_bar.setFixedHeight(12)
        self.budget_bar.setStyleSheet("QProgressBar { border: none; border-radius: 3px; background-color: rgba(255,255,255,0.1); } QProgressBar::chunk { background-color: #a6e3a1; border-radius: 3px; }")
        s_layout.addWidget(self.budget_bar)
        self.lbl_budget = QLabel("Presupuesto: sin definir")
        self.lbl_budget.setStyleSheet("color: #cdd6f4; font-size: 10px;")
        s_layout.addWidget(self.lbl_budget)
        layout.addWidget(self.summary_frame)

        line3 = QFrame(); line3.setFrameShape(QFrame.Shape.HLine); line3.setStyleSheet("color: rgba(255,255,255,0.2);")
        layout.addWidget(line3)

        # Bottom Buttons
        btn_acc = QPushButton('🏦 Cuentas')
        btn_cat = QPushButton('📂 Categorías')
        btn_bud = QPushButton('📊 Presupuestos')
        b_style = "QPushButton { text-align: left; padding: 6px 10px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; } QPushButton:hover { background-color: rgba(255,255,255,0.15); }"
        btn_acc.setStyleSheet(b_style); btn_cat.setStyleSheet(b_style); btn_bud.setStyleSheet(b_style)
        btn_acc.clicked.connect(self.manage_accounts_clicked.emit)
        btn_cat.clicked.connect(self.manage_categories_clicked.emit)
        btn_bud.clicked.connect(self.manage_budgets_clicked.emit)
        layout.addWidget(btn_acc)
        layout.addWidget(btn_cat)
        layout.addWidget(btn_bud)

        # Settings
        b_layout = QHBoxLayout()
        self.btn_set = QPushButton()
        self.btn_set.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_set.setFixedSize(32, 32)
        self.btn_set.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }")
        self.btn_set.clicked.connect(self.settings_clicked.emit)
        b_layout.addWidget(self.btn_set, alignment=Qt.AlignmentFlag.AlignLeft)
        b_layout.addStretch()
        layout.addLayout(b_layout)

    def _on_month_index_changed(self, idx: int):
        if idx >= 0:
            month_key = self.month_combo.itemData(idx)
            self.month_changed.emit(month_key)

    def populate_months(self, month_keys: list, current: str):
        self.month_combo.blockSignals(True)
        self.month_combo.clear()
        keys = sorted(set(month_keys + [current]), reverse=True)
        for k in keys:
            self.month_combo.addItem(_get_month_label(k), k)
            if k == current:
                self.month_combo.setCurrentIndex(self.month_combo.count() - 1)
        self.month_combo.blockSignals(False)

    def update_summary(self, income: float, expense: float, budget_total: float, budget_used_pct: int, symbol: str, visible: bool = True):
        self.summary_frame.setVisible(visible)
        if not visible: return
        self.lbl_income.setText(f"Ingresos: {_format_amount(income, symbol)}")
        self.lbl_expense.setText(f"Gastos: {_format_amount(expense, symbol)}")
        bal = income - expense
        self.lbl_balance.setText(f"Balance: {_format_amount(bal, symbol)}")
        self.lbl_balance.setStyleSheet(f"color: {'#a6e3a1' if bal >= 0 else '#f38ba8'}; font-weight: bold; font-size: 11px;")
        
        if budget_total > 0:
            self.budget_bar.setVisible(True)
            self.lbl_budget.setVisible(True)
            self.budget_bar.setValue(min(100, budget_used_pct))
            c = '#a6e3a1' if budget_used_pct < 70 else ('#f9e2af' if budget_used_pct < 90 else '#f38ba8')
            self.budget_bar.setStyleSheet(f"QProgressBar {{ border: none; border-radius: 3px; background-color: rgba(255,255,255,0.1); }} QProgressBar::chunk {{ background-color: {c}; border-radius: 3px; }}")
            self.lbl_budget.setText(f"Presupuesto: {_format_amount(budget_total, symbol)}")
        else:
            self.budget_bar.setVisible(False)
            self.lbl_budget.setVisible(False)


class GastosLeftView(QWidget):
    item_selected = pyqtSignal(dict)
    edit_item_requested = pyqtSignal(dict)
    pagination_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.transactions = []
        self.accounts_dict = {}
        self.filter_type = 'all'
        self.current_page = 1
        self.total_pages = 1
        self.month_label = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        hdr = QFrame()
        hdr.setFixedHeight(34)
        hdr.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(10, 0, 10, 0)
        self.lbl_hdr = QLabel("💰 Registro de Gastos y Finanzas")
        self.lbl_hdr.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hl.addWidget(self.lbl_hdr)
        layout.addWidget(hdr)

        # Scroll
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 0px; }")
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(4)
        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll)

    def set_data(self, transactions: list, accounts: list, month_label: str, filter_type: str, page: int):
        self.transactions = transactions
        self.accounts_dict = {a['id']: a for a in accounts}
        self.month_label = month_label
        self.filter_type = filter_type
        self.current_page = max(1, page)
        self._refresh()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._recalculate_items_per_page()

    def _recalculate_items_per_page(self):
        if not self.transactions:
            self.total_pages = 1
            self.pagination_changed.emit(self.current_page, self.total_pages)
            return
        
        filtered = [t for t in self.transactions if self.filter_type == 'all' or t.get('type') == self.filter_type]
        if not filtered:
            self.total_pages = 1
            self.pagination_changed.emit(self.current_page, self.total_pages)
            return

        margins_y = 30
        hdr_y = 44
        card_step = 44
        available_y = self.height() - margins_y - hdr_y
        new_items_per_page = max(1, available_y // card_step)
        
        import math
        self.total_pages = max(1, math.ceil(len(filtered) / new_items_per_page))
        if self.current_page > self.total_pages:
            self.current_page = self.total_pages
        
        start = (self.current_page - 1) * new_items_per_page
        end = start + new_items_per_page
        self._render_page(filtered[start:end])
        self.pagination_changed.emit(self.current_page, self.total_pages)

    def _refresh(self):
        self.lbl_hdr.setText(f"💰 Registro de Gastos y Finanzas — {self.month_label}")
        self._recalculate_items_per_page()

    def _render_page(self, items: list):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        for t in items:
            cat = t.get('category', '')
            emoji = CATEGORY_ICONS.get(cat, '💵')
            desc = t.get('description', 'Sin descripción')
            amt = t.get('amount', 0.0)
            ttype = t.get('type', 'expense')
            acc_id = t.get('account_id', '')
            acc = self.accounts_dict.get(acc_id, {})
            acc_name = acc.get('name', 'Cuenta desconocida')
            curr = acc.get('currency', '$')
            
            c = '#f38ba8' if ttype == 'expense' else '#a6e3a1'
            sgn = '-' if ttype == 'expense' else '+'
            
            card = ClickableFrame()
            card.setFixedHeight(40)
            card.setStyleSheet("""
                QFrame { background-color: rgba(255,255,255,0.75); border: 1px solid #D0C070; border-radius: 6px; }
                QFrame:hover { border: 1px solid #8A2BE2; background-color: rgba(255,255,255,0.9); }
            """)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(10, 4, 10, 4)
            cl.setSpacing(10)
            
            # Left side
            vl = QVBoxLayout()
            vl.setSpacing(0)
            lbl_title = QLabel(f"{emoji} {desc}")
            lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #11111b; border: none; background: transparent;")
            
            date_str = QDate.fromString(t.get('date', ''), 'yyyy-MM-dd').toString('dd/MM/yyyy')
            lbl_sub = QLabel(f"{date_str} | {cat} | {acc_name}")
            lbl_sub.setStyleSheet("font-size: 10px; color: #555555; border: none; background: transparent;")
            
            vl.addWidget(lbl_title)
            vl.addWidget(lbl_sub)
            cl.addLayout(vl)
            cl.addStretch()
            
            # Right side
            lbl_amt = QLabel(f"{sgn}{_format_amount(amt, curr)}")
            lbl_amt.setStyleSheet(f"font-weight: bold; font-size: 13px; color: {c}; border: none; background: transparent;")
            cl.addWidget(lbl_amt)
            
            btn_edit = QPushButton()
            btn_edit.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'pencil_dark.svg')))
            btn_edit.setFixedSize(24, 24)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: rgba(0,0,0,0.1); border-radius: 4px; }")
            btn_edit.clicked.connect(lambda checked, tx=t: self.edit_item_requested.emit(tx))
            cl.addWidget(btn_edit)
            
            card.clicked.connect(lambda tx=t: self.item_selected.emit(tx))
            self.scroll_layout.addWidget(card)
        
        self.scroll_layout.addStretch()


class GastosRightView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 25, 15)
        layout.setSpacing(14)

        hdr = QFrame()
        hdr.setFixedHeight(34)
        hdr.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(10, 0, 10, 0)
        lbl_hdr = QLabel("📊 Resumen Financiero del Mes")
        lbl_hdr.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hl.addWidget(lbl_hdr)
        layout.addWidget(hdr)

        # Balance Card
        bal_card = QFrame()
        bal_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.7); border: 1px solid #D0C070; border-radius: 8px; }")
        bl = QVBoxLayout(bal_card)
        self.lbl_r_inc = QLabel("💰 Total Ingresos: $0")
        self.lbl_r_inc.setStyleSheet("font-weight: bold; font-size: 13px; color: #1b5e20; border: none; background: transparent;")
        self.lbl_r_exp = QLabel("💸 Total Gastos: $0")
        self.lbl_r_exp.setStyleSheet("font-weight: bold; font-size: 13px; color: #b71c1c; border: none; background: transparent;")
        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setStyleSheet("color: #A0A0A0;")
        self.lbl_r_bal = QLabel("📋 Balance: $0")
        self.lbl_r_bal.setStyleSheet("font-weight: bold; font-size: 15px; color: #111111; border: none; background: transparent;")
        bl.addWidget(self.lbl_r_inc)
        bl.addWidget(self.lbl_r_exp)
        bl.addWidget(line)
        bl.addWidget(self.lbl_r_bal)
        layout.addWidget(bal_card)

        # Top Categories Card
        self.cat_card = QFrame()
        self.cat_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.7); border: 1px solid #D0C070; border-radius: 8px; }")
        self.cat_layout = QVBoxLayout(self.cat_card)
        layout.addWidget(self.cat_card)
        
        layout.addStretch()

    def set_data(self, transactions: list, accounts: list, currency_symbol: str):
        inc = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'income')
        exp = sum(t.get('amount', 0) for t in transactions if t.get('type') == 'expense')
        bal = inc - exp

        self.lbl_r_inc.setText(f"💰 Total Ingresos: {_format_amount(inc, currency_symbol)}")
        self.lbl_r_exp.setText(f"💸 Total Gastos: {_format_amount(exp, currency_symbol)}")
        self.lbl_r_bal.setText(f"📋 Balance: {_format_amount(bal, currency_symbol)}")
        self.lbl_r_bal.setStyleSheet(f"font-weight: bold; font-size: 15px; color: {'#1b5e20' if bal >= 0 else '#b71c1c'}; border: none; background: transparent;")

        while self.cat_layout.count():
            child = self.cat_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            elif child.layout():
                while child.layout().count():
                    c = child.layout().takeAt(0)
                    if c.widget(): c.widget().deleteLater()
                child.layout().deleteLater()
        
        lbl_top = QLabel("🏆 Top Categorías de Gasto")
        lbl_top.setStyleSheet("font-weight: bold; font-size: 12px; color: #333333; border: none; background: transparent;")
        self.cat_layout.addWidget(lbl_top)

        cats = {}
        for t in transactions:
            if t.get('type') == 'expense':
                c = t.get('category', 'Otros')
                cats[c] = cats.get(c, 0) + t.get('amount', 0)
        
        sorted_cats = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
        if not sorted_cats:
            lbl_none = QLabel("No hay gastos registrados en este período.")
            lbl_none.setStyleSheet("font-style: italic; font-size: 11px; color: #555555; border: none; background: transparent;")
            self.cat_layout.addWidget(lbl_none)
        else:
            max_amt = sorted_cats[0][1]
            for c, amt in sorted_cats:
                emoji = CATEGORY_ICONS.get(c, '💵')
                cl = QHBoxLayout()
                cl.addWidget(QLabel(f"{emoji} {c}", styleSheet="font-size: 11px; color: #111111; border: none; background: transparent;"))
                cl.addStretch()
                cl.addWidget(QLabel(_format_amount(amt, currency_symbol), styleSheet="font-weight: bold; font-size: 11px; color: #b71c1c; border: none; background: transparent;"))
                self.cat_layout.addLayout(cl)
                pb = QProgressBar()
                pb.setFixedHeight(6)
                pb.setTextVisible(False)
                pb.setValue(int(amt / max_amt * 100))
                pb.setStyleSheet("QProgressBar { border: none; border-radius: 2px; background-color: rgba(0,0,0,0.1); } QProgressBar::chunk { background-color: #f38ba8; border-radius: 2px; }")
                self.cat_layout.addWidget(pb)


class GastosPlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self._data = {
            'transactions': [],
            'accounts': [],
            'categories': {
                'expense': ['Alimentación', 'Transporte', 'Servicios Básicos', 'Salud', 'Educación', 'Entretenimiento', 'Hogar', 'Vestimenta', 'Tecnología', 'Otros'],
                'income': ['Salario', 'Freelance', 'Ventas', 'Inversiones', 'Otros Ingresos']
            },
            'budgets': {},
            'settings': {'default_currency': '$', 'show_sidebar_summary': True},
            '_trash': []
        }
        self._trash = []
        self._is_modified = False
        self.current_filter = 'all'
        self.current_month = QDate.currentDate().toString('yyyy-MM')
        self.current_page = 1
        
        self._sidebar = GastosSidebar()
        self._left_page = GastosLeftView()
        self._right_page = GastosRightView()

        self._sidebar.add_expense_clicked.connect(self._on_add_expense)
        self._sidebar.add_income_clicked.connect(self._on_add_income)
        self._sidebar.filter_changed.connect(self._on_filter_changed)
        self._sidebar.month_changed.connect(self._on_month_changed)
        self._sidebar.manage_categories_clicked.connect(self._on_manage_categories)
        self._sidebar.manage_budgets_clicked.connect(self._on_manage_budgets)
        self._sidebar.manage_accounts_clicked.connect(self._on_manage_accounts)
        self._sidebar.settings_clicked.connect(self._on_settings)
        
        self._left_page.edit_item_requested.connect(self._on_edit_transaction)
        self._left_page.pagination_changed.connect(self.page_changed.emit)

    def get_name(self): return "Gastos"
    def get_id(self): return "gastos"
    def get_icon(self): return "wallet.svg"
    def get_tab_color(self): return "#4CAF50"
    def get_order(self): return 9

    def create_sidebar_widget(self): return self._sidebar
    def create_left_page(self): return self._left_page
    def create_right_page(self): return self._right_page

    def load_data(self, agenda_path):
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
            self._trash = loaded.get('_trash', [])
        
        # Ensure at least one account exists
        if not self._data.get('accounts'):
            self._data['accounts'] = [{'id': str(uuid.uuid4()), 'name': 'Efectivo', 'currency': '$', 'initial_balance': 0.0}]
            self._is_modified = True

        self._update_views()
        self._is_modified = False

    def save_data(self, agenda_path):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            DataStore.save(data_path, self._data)
            self._is_modified = False

    def _get_month_transactions(self):
        return [t for t in self._data.get('transactions', []) if t.get('date', '')[:7] == self.current_month]

    def _update_views(self):
        txs = self._get_month_transactions()
        
        # Months for combobox
        all_txs = self._data.get('transactions', [])
        month_keys = list(set([t.get('date', '')[:7] for t in all_txs if t.get('date')]))
        self._sidebar.populate_months(month_keys, self.current_month)
        
        # Left page
        sym = self._data.get('settings', {}).get('default_currency', '$')
        self._left_page.set_data(
            txs, self._data.get('accounts', []),
            _get_month_label(self.current_month), self.current_filter, self.current_page
        )
        
        # Right page & Sidebar Summary
        inc = sum(t.get('amount', 0) for t in txs if t.get('type') == 'income')
        exp = sum(t.get('amount', 0) for t in txs if t.get('type') == 'expense')
        bud = self._data.get('budgets', {}).get(self.current_month, {}).get('_global', 0)
        pct = int(exp / bud * 100) if bud > 0 else 0
        
        show_summary = self._data.get('settings', {}).get('show_sidebar_summary', True)
        self._sidebar.update_summary(inc, exp, bud, pct, sym, show_summary)
        
        self._right_page.set_data(txs, self._data.get('accounts', []), sym)

    def _on_add_expense(self):
        dlg = TransactionDialog(self._data['categories'], self._data['accounts'], preset_type='expense', parent=self._sidebar)
        if dlg.exec() and dlg.transaction_data:
            self._data.setdefault('transactions', []).append(dlg.transaction_data)
            self._is_modified = True
            self._update_views()

    def _on_add_income(self):
        dlg = TransactionDialog(self._data['categories'], self._data['accounts'], preset_type='income', parent=self._sidebar)
        if dlg.exec() and dlg.transaction_data:
            self._data.setdefault('transactions', []).append(dlg.transaction_data)
            self._is_modified = True
            self._update_views()

    def _on_edit_transaction(self, tx: dict):
        dlg = TransactionDialog(self._data['categories'], self._data['accounts'], transaction_to_edit=tx, parent=self._sidebar)
        if dlg.exec():
            txs = self._data.get('transactions', [])
            if dlg.is_delete:
                if tx in txs:
                    txs.remove(tx)
                    self.move_to_trash(tx)
            elif dlg.transaction_data:
                idx = txs.index(tx) if tx in txs else -1
                if idx >= 0: txs[idx] = dlg.transaction_data
                else: txs.append(dlg.transaction_data)
            self._is_modified = True
            self._update_views()

    def _on_manage_categories(self):
        dlg = CategoryManagerDialog(self._data['categories'], self._data['transactions'], parent=self._sidebar)
        if dlg.exec():
            self._data['categories'] = dlg.updated_categories
            self._is_modified = True
            self._update_views()

    def _on_manage_budgets(self):
        dlg = BudgetDialog(self._data['budgets'], self._data['categories']['expense'], self.current_month, self._data['settings'].get('default_currency', '$'), self._data['transactions'], parent=self._sidebar)
        if dlg.exec():
            self._data['budgets'] = dlg.updated_budgets
            self._is_modified = True
            self._update_views()

    def _on_manage_accounts(self):
        dlg = AccountManagerDialog(self._data['accounts'], self._data['transactions'], parent=self._sidebar)
        if dlg.exec():
            self._data['accounts'] = dlg.updated_accounts
            self._is_modified = True
            self._update_views()

    def _on_settings(self):
        dlg = GastosSettingsDialog(self._data['settings'], parent=self._sidebar)
        if dlg.exec():
            self._data['settings'] = dlg.updated_settings
            self._is_modified = True
            self._update_views()

    def _on_filter_changed(self, f: str):
        self.current_filter = f
        self.current_page = 1
        self._update_views()

    def _on_month_changed(self, m: str):
        self.current_month = m
        self.current_page = 1
        self._update_views()

    def get_total_pages(self): return self._left_page.total_pages
    def get_current_page(self): return self._left_page.current_page
    def go_to_page(self, n: int):
        self.current_page = n
        self._left_page.current_page = n
        self._left_page._recalculate_items_per_page()

    def move_to_trash(self, item: dict): self._trash.append(item)
    def get_trash_items(self): return self._trash
    def restore_item(self, idx: int):
        if 0 <= idx < len(self._trash):
            self._data.setdefault('transactions', []).append(self._trash.pop(idx))
            self._is_modified = True
            self._update_views()
    def delete_permanently(self, idx: int):
        if 0 <= idx < len(self._trash):
            self._trash.pop(idx)
            self._is_modified = True
    def empty_trash(self):
        if self._trash:
            self._trash.clear()
            self._is_modified = True
