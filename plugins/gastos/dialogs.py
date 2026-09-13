import os
import uuid
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QDateEdit,
    QDoubleSpinBox, QCheckBox, QSpinBox, QTabWidget,
    QListWidget, QListWidgetItem, QMessageBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
    QButtonGroup, QWidget, QTextEdit
)

CATPPUCCIN_STYLESHEET = """
    QDialog { background-color: #1e1e2e; color: #cdd6f4; }
    QLabel { color: #cdd6f4; background: transparent; border: none; }
    QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
        background-color: #313244; color: #cdd6f4; border: 1px solid #45475a;
        border-radius: 6px; padding: 6px;
    }
    QComboBox::drop-down { border: none; }
    QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #45475a; }
    QPushButton { padding: 6px 14px; border-radius: 6px; font-weight: bold; }
    QPushButton#primaryButton { background-color: #a6e3a1; color: #11111b; }
    QPushButton#primaryButton:hover { background-color: #94e28f; }
    QPushButton#dangerButton { background-color: #f38ba8; color: #11111b; }
    QPushButton#dangerButton:hover { background-color: #e78284; }
    QPushButton#secondaryButton { background-color: #45475a; color: #cdd6f4; }
    QPushButton#secondaryButton:hover { background-color: #585b70; }
    QTabWidget::pane { border: 1px solid #45475a; border-radius: 6px; }
    QTabBar::tab { background-color: #313244; color: #cdd6f4; padding: 8px 16px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
    QTabBar::tab:selected { background-color: #45475a; color: #f9e2af; }
    QListWidget { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; }
    QListWidget::item:selected { background-color: #45475a; color: #f9e2af; }
    QTableWidget { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; gridline-color: #45475a; }
    QHeaderView::section { background-color: #45475a; color: #f9e2af; padding: 4px; border: none; font-weight: bold; }
    QCheckBox { color: #cdd6f4; spacing: 8px; }
    QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #45475a; border-radius: 4px; background-color: #313244; }
    QCheckBox::indicator:checked { background-color: #a6e3a1; border-color: #a6e3a1; }
"""


# ---------------------------------------------------------------------------
# Class 1: TransactionDialog
# ---------------------------------------------------------------------------
class TransactionDialog(QDialog):
    """Dialog for creating or editing a financial transaction."""

    def __init__(
        self,
        categories: dict,
        accounts: list,
        transaction_to_edit: dict = None,
        preset_type: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self.categories = categories
        self.accounts = accounts
        self.transaction_to_edit = transaction_to_edit
        self.preset_type = preset_type

        self.transaction_data = None
        self.is_delete = False

        self._editing = transaction_to_edit is not None

        # Determine window title
        if self._editing:
            title = 'Editar Transacción'
        elif preset_type == 'income':
            title = 'Nuevo Ingreso'
        else:
            title = 'Nuevo Gasto'

        self.setWindowTitle(title)
        self.setMinimumWidth(450)
        self.setStyleSheet(CATPPUCCIN_STYLESHEET)

        self._build_ui()
        self._connect_signals()

        if self._editing:
            self._populate_from_transaction(transaction_to_edit)
        elif preset_type:
            self._set_type(preset_type)
        else:
            self._set_type('expense')

    # ---- UI construction ---------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # -- Type selector --
        type_layout = QHBoxLayout()
        self.btn_expense = QPushButton('💸 Gasto')
        self.btn_income = QPushButton('💰 Ingreso')
        self.btn_expense.setCheckable(True)
        self.btn_income.setCheckable(True)

        self.type_group = QButtonGroup(self)
        self.type_group.addButton(self.btn_expense, 0)
        self.type_group.addButton(self.btn_income, 1)
        self.type_group.setExclusive(True)

        self._style_type_buttons()

        type_layout.addWidget(self.btn_expense)
        type_layout.addWidget(self.btn_income)
        layout.addLayout(type_layout)

        # -- Form --
        form = QFormLayout()
        form.setSpacing(10)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        form.addRow('Fecha:', self.date_edit)

        # Amount
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setRange(0, 999999999)
        self.amount_spin.setDecimals(2)
        self.amount_spin.setSingleStep(100)
        form.addRow('Monto:', self.amount_spin)

        # Category
        self.category_combo = QComboBox()
        form.addRow('Categoría:', self.category_combo)

        # Description
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText('Descripción del movimiento...')
        form.addRow('Descripción:', self.description_edit)

        # Account (Cuenta)
        self.account_combo = QComboBox()
        for acc in self.accounts:
            self.account_combo.addItem(f"{acc.get('name', 'Cuenta')} ({acc.get('currency', '$')})", acc.get('id'))
        form.addRow('Cuenta:', self.account_combo)

        # Tags
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText('Etiquetas separadas por comas')
        form.addRow('Etiquetas:', self.tags_edit)

        layout.addLayout(form)

        # -- Recurring --
        recurring_layout = QHBoxLayout()
        self.recurring_check = QCheckBox('Transacción recurrente mensual')
        recurring_layout.addWidget(self.recurring_check)

        self.recurring_day_label = QLabel('Día del mes:')
        self.recurring_day_spin = QSpinBox()
        self.recurring_day_spin.setRange(1, 31)
        self.recurring_day_spin.setValue(1)
        self.recurring_day_label.setVisible(False)
        self.recurring_day_spin.setVisible(False)
        recurring_layout.addWidget(self.recurring_day_label)
        recurring_layout.addWidget(self.recurring_day_spin)
        recurring_layout.addStretch()
        layout.addLayout(recurring_layout)

        # -- Notes --
        notes_label = QLabel('Notas:')
        layout.addWidget(notes_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText('Notas adicionales (opcional)')
        self.notes_edit.setMaximumHeight(72)
        layout.addWidget(self.notes_edit)

        # -- Separator --
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('background-color: #45475a;')
        layout.addWidget(sep)

        # -- Buttons --
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setObjectName('secondaryButton')
        btn_layout.addWidget(self.btn_cancel)

        if self._editing:
            self.btn_delete = QPushButton('Eliminar')
            self.btn_delete.setObjectName('dangerButton')
            btn_layout.addWidget(self.btn_delete)

        self.btn_save = QPushButton('Guardar')
        self.btn_save.setObjectName('primaryButton')
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    # ---- Signals -----------------------------------------------------------

    def _connect_signals(self):
        self.btn_expense.clicked.connect(lambda: self._on_type_changed('expense'))
        self.btn_income.clicked.connect(lambda: self._on_type_changed('income'))
        self.recurring_check.toggled.connect(self._on_recurring_toggled)
        self.account_combo.currentIndexChanged.connect(self._update_currency_prefix)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)
        if self._editing:
            self.btn_delete.clicked.connect(self._on_delete)
        
        # Trigger initial prefix
        if self.accounts:
            self._update_currency_prefix(0)

    # ---- Helpers -----------------------------------------------------------

    def _style_type_buttons(self):
        self.btn_expense.setStyleSheet("""
            QPushButton {
                padding: 8px 16px; border-radius: 6px; font-weight: bold;
                background-color: #45475a; color: #cdd6f4; border: 1px solid #45475a;
            }
            QPushButton:checked {
                background-color: #f38ba8; color: #11111b; border: 1px solid #f38ba8;
            }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:checked:hover { background-color: #e78284; }
        """)
        self.btn_income.setStyleSheet("""
            QPushButton {
                padding: 8px 16px; border-radius: 6px; font-weight: bold;
                background-color: #45475a; color: #cdd6f4; border: 1px solid #45475a;
            }
            QPushButton:checked {
                background-color: #a6e3a1; color: #11111b; border: 1px solid #a6e3a1;
            }
            QPushButton:hover { background-color: #585b70; }
            QPushButton:checked:hover { background-color: #94e28f; }
        """)

    def _set_type(self, ttype: str):
        if ttype == 'income':
            self.btn_income.setChecked(True)
        else:
            self.btn_expense.setChecked(True)
        self._update_categories(ttype)

    def _current_type(self) -> str:
        return 'income' if self.btn_income.isChecked() else 'expense'

    def _update_categories(self, ttype: str):
        self.category_combo.clear()
        cats = self.categories.get(ttype, [])
        self.category_combo.addItems(cats)

    def _on_type_changed(self, ttype: str):
        self._update_categories(ttype)

    def _on_recurring_toggled(self, checked: bool):
        self.recurring_day_label.setVisible(checked)
        self.recurring_day_spin.setVisible(checked)

    def _update_currency_prefix(self, index: int):
        if 0 <= index < len(self.accounts):
            curr = self.accounts[index].get('currency', '$')
            self.amount_spin.setPrefix(f'{curr} ')

    def _populate_from_transaction(self, t: dict):
        ttype = t.get('type', 'expense')
        self._set_type(ttype)

        date_str = t.get('date', '')
        if date_str:
            d = QDate.fromString(date_str, 'yyyy-MM-dd')
            if d.isValid():
                self.date_edit.setDate(d)

        self.amount_spin.setValue(t.get('amount', 0.0))

        cat = t.get('category', '')
        idx = self.category_combo.findText(cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)

        self.description_edit.setText(t.get('description', ''))

        acc_id = t.get('account_id', '')
        idx = self.account_combo.findData(acc_id)
        if idx >= 0:
            self.account_combo.setCurrentIndex(idx)

        tags = t.get('tags', [])
        self.tags_edit.setText(', '.join(tags) if tags else '')

        is_rec = t.get('is_recurring', False)
        self.recurring_check.setChecked(is_rec)
        if is_rec:
            self.recurring_day_spin.setValue(t.get('recurring_day', 1) or 1)

        self.notes_edit.setPlainText(t.get('notes', ''))

    def _on_save(self):
        amount = self.amount_spin.value()
        if amount <= 0:
            QMessageBox.warning(self, 'Error', 'El monto debe ser mayor a 0.')
            return

        if not self.category_combo.currentText():
            QMessageBox.warning(self, 'Error', 'Debe seleccionar una categoría.')
            return

        tags_raw = self.tags_edit.text().strip()
        tags = [t.strip() for t in tags_raw.split(',') if t.strip()] if tags_raw else []

        tid = self.transaction_to_edit.get('id', str(uuid.uuid4())) if self._editing else str(uuid.uuid4())

        self.transaction_data = {
            'id': tid,
            'date': self.date_edit.date().toString('yyyy-MM-dd'),
            'type': self._current_type(),
            'amount': amount,
            'category': self.category_combo.currentText(),
            'description': self.description_edit.text().strip(),
            'account_id': self.account_combo.currentData(),
            'tags': tags,
            'is_recurring': self.recurring_check.isChecked(),
            'recurring_day': self.recurring_day_spin.value() if self.recurring_check.isChecked() else None,
            'notes': self.notes_edit.toPlainText().strip(),
        }
        self.accept()

    def _on_delete(self):
        reply = QMessageBox.question(
            self,
            'Confirmar eliminación',
            '¿Está seguro de que desea eliminar esta transacción?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.is_delete = True
            self.accept()


# ---------------------------------------------------------------------------
# Class 2: CategoryManagerDialog
# ---------------------------------------------------------------------------
class CategoryManagerDialog(QDialog):
    """Dialog for managing custom categories (expenses and income)."""

    def __init__(self, categories: dict, transactions: list = None, parent=None):
        super().__init__(parent)
        self.updated_categories = {
            'expense': list(categories.get('expense', [])),
            'income': list(categories.get('income', [])),
        }
        self.transactions = transactions or []

        self.setWindowTitle('Administrar Categorías')
        self.setMinimumSize(450, 400)
        self.setStyleSheet(CATPPUCCIN_STYLESHEET)

        self._build_ui()
        self._connect_signals()
        self._refresh_lists()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.tab_widget = QTabWidget()

        # Expense tab
        self.expense_tab = QWidget()
        exp_layout = QVBoxLayout(self.expense_tab)
        self.expense_list = QListWidget()
        exp_layout.addWidget(self.expense_list)
        exp_btn_layout = QHBoxLayout()
        self.btn_add_expense = QPushButton('Agregar')
        self.btn_add_expense.setObjectName('primaryButton')
        self.btn_edit_expense = QPushButton('Editar')
        self.btn_edit_expense.setObjectName('secondaryButton')
        self.btn_del_expense = QPushButton('Eliminar')
        self.btn_del_expense.setObjectName('dangerButton')
        exp_btn_layout.addWidget(self.btn_add_expense)
        exp_btn_layout.addWidget(self.btn_edit_expense)
        exp_btn_layout.addWidget(self.btn_del_expense)
        exp_layout.addLayout(exp_btn_layout)
        self.tab_widget.addTab(self.expense_tab, 'Gastos')

        # Income tab
        self.income_tab = QWidget()
        inc_layout = QVBoxLayout(self.income_tab)
        self.income_list = QListWidget()
        inc_layout.addWidget(self.income_list)
        inc_btn_layout = QHBoxLayout()
        self.btn_add_income = QPushButton('Agregar')
        self.btn_add_income.setObjectName('primaryButton')
        self.btn_edit_income = QPushButton('Editar')
        self.btn_edit_income.setObjectName('secondaryButton')
        self.btn_del_income = QPushButton('Eliminar')
        self.btn_del_income.setObjectName('dangerButton')
        inc_btn_layout.addWidget(self.btn_add_income)
        inc_btn_layout.addWidget(self.btn_edit_income)
        inc_btn_layout.addWidget(self.btn_del_income)
        inc_layout.addLayout(inc_btn_layout)
        self.tab_widget.addTab(self.income_tab, 'Ingresos')

        layout.addWidget(self.tab_widget)

        # Bottom accept button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_accept = QPushButton('Aceptar')
        self.btn_accept.setObjectName('primaryButton')
        bottom_layout.addWidget(self.btn_accept)
        layout.addLayout(bottom_layout)

    def _connect_signals(self):
        self.btn_add_expense.clicked.connect(lambda: self._add_category('expense'))
        self.btn_edit_expense.clicked.connect(lambda: self._edit_category('expense'))
        self.btn_del_expense.clicked.connect(lambda: self._delete_category('expense'))
        self.btn_add_income.clicked.connect(lambda: self._add_category('income'))
        self.btn_edit_income.clicked.connect(lambda: self._edit_category('income'))
        self.btn_del_income.clicked.connect(lambda: self._delete_category('income'))
        self.btn_accept.clicked.connect(self.accept)

    def _refresh_lists(self):
        self.expense_list.clear()
        for cat in self.updated_categories.get('expense', []):
            self.expense_list.addItem(QListWidgetItem(cat))

        self.income_list.clear()
        for cat in self.updated_categories.get('income', []):
            self.income_list.addItem(QListWidgetItem(cat))

    def _get_list_widget(self, ctype: str) -> QListWidget:
        return self.expense_list if ctype == 'expense' else self.income_list

    def _add_category(self, ctype: str):
        from PyQt6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, 'Nueva Categoría', 'Nombre de la categoría:')
        if ok and name.strip():
            name = name.strip()
            if name in self.updated_categories[ctype]:
                QMessageBox.warning(self, 'Duplicado', f'La categoría "{name}" ya existe.')
                return
            self.updated_categories[ctype].append(name)
            self._refresh_lists()

    def _edit_category(self, ctype: str):
        lw = self._get_list_widget(ctype)
        current = lw.currentItem()
        if not current:
            QMessageBox.information(self, 'Selección', 'Seleccione una categoría para editar.')
            return
        old_name = current.text()

        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, 'Editar Categoría', 'Nuevo nombre:', text=old_name)
        if ok and new_name.strip():
            new_name = new_name.strip()
            if new_name != old_name and new_name in self.updated_categories[ctype]:
                QMessageBox.warning(self, 'Duplicado', f'La categoría "{new_name}" ya existe.')
                return
            idx = self.updated_categories[ctype].index(old_name)
            self.updated_categories[ctype][idx] = new_name
            self._refresh_lists()

    def _delete_category(self, ctype: str):
        lw = self._get_list_widget(ctype)
        current = lw.currentItem()
        if not current:
            QMessageBox.information(self, 'Selección', 'Seleccione una categoría para eliminar.')
            return
        cat_name = current.text()

        # Check if category is in use
        in_use = any(
            t.get('category') == cat_name and t.get('type') == ctype
            for t in self.transactions
        )
        if in_use:
            reply = QMessageBox.warning(
                self,
                'Categoría en uso',
                f'La categoría "{cat_name}" está siendo usada en transacciones existentes.\n'
                '¿Desea eliminarla de todos modos?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.updated_categories[ctype].remove(cat_name)
        self._refresh_lists()


# ---------------------------------------------------------------------------
# Class 3: BudgetDialog
# ---------------------------------------------------------------------------
class BudgetDialog(QDialog):
    """Dialog for setting monthly budgets with progress indicators."""

    MONTH_NAMES = [
        '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
    ]

    def __init__(
        self,
        budgets: dict,
        categories: list,
        current_month: str,
        currency_symbol: str = '$',
        transactions: list = None,
        parent=None,
    ):
        super().__init__(parent)
        # Deep-copy budgets so we can modify freely
        self.updated_budgets = {}
        for k, v in budgets.items():
            if isinstance(v, dict):
                self.updated_budgets[k] = dict(v)
            else:
                self.updated_budgets[k] = v

        self.categories = list(categories)
        self.current_month = current_month
        self.currency_symbol = currency_symbol
        self.transactions = transactions or []

        # Parse month for display
        parts = current_month.split('-')
        year = int(parts[0])
        month = int(parts[1])
        month_name = self.MONTH_NAMES[month] if 1 <= month <= 12 else ''

        self.setWindowTitle(f'Presupuesto Mensual — {month_name} {year}')
        self.setMinimumWidth(550)
        self.setStyleSheet(CATPPUCCIN_STYLESHEET)

        self._build_ui(year, month)
        self._connect_signals()
        self._load_month(self.current_month)

    def _build_ui(self, year: int, month: int):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Month selector
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel('Mes:'))
        self.month_edit = QDateEdit()
        self.month_edit.setDisplayFormat('yyyy-MM')
        self.month_edit.setDate(QDate(year, month, 1))
        self.month_edit.setCalendarPopup(True)
        month_layout.addWidget(self.month_edit)
        month_layout.addStretch()
        layout.addLayout(month_layout)

        # Global budget
        global_layout = QHBoxLayout()
        global_layout.addWidget(QLabel('Presupuesto global:'))
        self.global_budget_spin = QDoubleSpinBox()
        self.global_budget_spin.setRange(0, 999999999)
        self.global_budget_spin.setDecimals(2)
        self.global_budget_spin.setPrefix(f'{self.currency_symbol} ')
        self.global_budget_spin.setSingleStep(1000)
        global_layout.addWidget(self.global_budget_spin)
        global_layout.addStretch()
        layout.addLayout(global_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Categoría', 'Presupuesto', 'Gastado', '% Usado'])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setObjectName('secondaryButton')
        btn_layout.addWidget(self.btn_cancel)
        self.btn_save = QPushButton('Guardar')
        self.btn_save.setObjectName('primaryButton')
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.month_edit.dateChanged.connect(self._on_month_changed)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)

    def _on_month_changed(self, date: QDate):
        self.current_month = date.toString('yyyy-MM')
        month = date.month()
        year = date.year()
        month_name = self.MONTH_NAMES[month] if 1 <= month <= 12 else ''
        self.setWindowTitle(f'Presupuesto Mensual — {month_name} {year}')
        self._load_month(self.current_month)

    def _calculate_spent(self, category: str, month_key: str) -> float:
        total = 0.0
        for t in self.transactions:
            if t.get('type') != 'expense':
                continue
            if t.get('category') != category:
                continue
            t_date = t.get('date', '')
            if t_date[:7] == month_key:
                total += t.get('amount', 0.0)
        return total

    def _load_month(self, month_key: str):
        month_budgets = self.updated_budgets.get(month_key, {})
        if isinstance(month_budgets, (int, float)):
            month_budgets = {}

        global_val = 0.0
        if isinstance(self.updated_budgets.get(month_key), dict):
            global_val = self.updated_budgets[month_key].get('_global', 0.0)
        self.global_budget_spin.setValue(global_val)

        self.table.setRowCount(len(self.categories))
        self._budget_spins = []

        for row, cat in enumerate(self.categories):
            # Category name
            cat_item = QTableWidgetItem(cat)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, cat_item)

            # Budget spin
            budget_spin = QDoubleSpinBox()
            budget_spin.setRange(0, 999999999)
            budget_spin.setDecimals(2)
            budget_spin.setPrefix(f'{self.currency_symbol} ')
            budget_spin.setSingleStep(100)
            budget_val = month_budgets.get(cat, 0.0) if isinstance(month_budgets, dict) else 0.0
            budget_spin.setValue(budget_val)
            self.table.setCellWidget(row, 1, budget_spin)
            self._budget_spins.append((cat, budget_spin))

            # Spent
            spent = self._calculate_spent(cat, month_key)
            spent_item = QTableWidgetItem(f'{self.currency_symbol} {spent:,.2f}')
            spent_item.setFlags(spent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            spent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, spent_item)

            # Progress bar
            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(100)
            if budget_val > 0:
                pct = min(int((spent / budget_val) * 100), 100)
            else:
                pct = 0
            progress.setValue(pct)

            # Color the progress bar
            if pct < 60:
                bar_color = '#a6e3a1'  # green
            elif pct < 85:
                bar_color = '#f9e2af'  # yellow/amber
            else:
                bar_color = '#f38ba8'  # red

            progress.setStyleSheet(f"""
                QProgressBar {{
                    background-color: #313244;
                    border: 1px solid #45475a;
                    border-radius: 4px;
                    text-align: center;
                    color: #cdd6f4;
                }}
                QProgressBar::chunk {{
                    background-color: {bar_color};
                    border-radius: 3px;
                }}
            """)
            self.table.setCellWidget(row, 3, progress)

    def _on_save(self):
        month_key = self.current_month

        month_data = {'_global': self.global_budget_spin.value()}
        for cat, spin in self._budget_spins:
            month_data[cat] = spin.value()

        self.updated_budgets[month_key] = month_data
        self.accept()


# ---------------------------------------------------------------------------
# Class 4: GastosSettingsDialog
# ---------------------------------------------------------------------------
class GastosSettingsDialog(QDialog):
    """Simple settings dialog for the Gastos plugin."""

    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.updated_settings = dict(settings)

        self.setWindowTitle('Configuración de Gastos')
        self.setMinimumWidth(350)
        self.setStyleSheet(CATPPUCCIN_STYLESHEET)

        self._build_ui()
        self._connect_signals()
        self._populate(settings)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(10)

        # Currency symbol
        self.currency_edit = QLineEdit()
        self.currency_edit.setMaxLength(5)
        form.addRow('Símbolo de moneda:', self.currency_edit)

        layout.addLayout(form)

        # Sidebar checkbox
        self.sidebar_check = QCheckBox('Mostrar resumen en barra lateral')
        layout.addWidget(self.sidebar_check)

        layout.addStretch()

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet('background-color: #45475a;')
        layout.addWidget(sep)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_cancel = QPushButton('Cancelar')
        self.btn_cancel.setObjectName('secondaryButton')
        btn_layout.addWidget(self.btn_cancel)
        self.btn_save = QPushButton('Guardar')
        self.btn_save.setObjectName('primaryButton')
        btn_layout.addWidget(self.btn_save)
        layout.addLayout(btn_layout)

    def _connect_signals(self):
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._on_save)

    def _populate(self, settings: dict):
        self.currency_edit.setText(settings.get('currency_symbol', '$'))
        self.sidebar_check.setChecked(settings.get('show_sidebar_summary', True))

    def _on_save(self):
        self.updated_settings['currency_symbol'] = self.currency_edit.text().strip() or '$'
        self.updated_settings['show_sidebar_summary'] = self.sidebar_check.isChecked()
        self.accept()


# ---------------------------------------------------------------------------
# Class 5: AccountManagerDialog
# ---------------------------------------------------------------------------
class AccountManagerDialog(QDialog):
    """Dialog for managing accounts and their currencies."""

    def __init__(self, accounts: list, transactions: list = None, parent=None):
        super().__init__(parent)
        self.updated_accounts = [dict(a) for a in accounts]
        self.transactions = transactions or []

        self.setWindowTitle('Administrar Cuentas')
        self.setMinimumSize(500, 400)
        self.setStyleSheet(CATPPUCCIN_STYLESHEET)

        self._build_ui()
        self._connect_signals()
        self._refresh_list()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        self.account_list = QListWidget()
        layout.addWidget(self.account_list)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton('Agregar')
        self.btn_add.setObjectName('primaryButton')
        self.btn_edit = QPushButton('Editar')
        self.btn_edit.setObjectName('secondaryButton')
        self.btn_del = QPushButton('Eliminar')
        self.btn_del.setObjectName('dangerButton')
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_del)
        layout.addLayout(btn_layout)

        # Bottom accept button
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.btn_accept = QPushButton('Aceptar')
        self.btn_accept.setObjectName('primaryButton')
        bottom_layout.addWidget(self.btn_accept)
        layout.addLayout(bottom_layout)

    def _connect_signals(self):
        self.btn_add.clicked.connect(self._add_account)
        self.btn_edit.clicked.connect(self._edit_account)
        self.btn_del.clicked.connect(self._delete_account)
        self.btn_accept.clicked.connect(self.accept)

    def _refresh_list(self):
        self.account_list.clear()
        for acc in self.updated_accounts:
            name = acc.get('name', 'Cuenta')
            curr = acc.get('currency', '$')
            bal = acc.get('initial_balance', 0.0)
            text = f"{name} ({curr}) - Saldo Inicial: {bal:,.2f}"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, acc['id'])
            self.account_list.addItem(item)

    def _add_account(self):
        dlg = _AccountEditDialog(parent=self)
        if dlg.exec():
            acc = dlg.account_data
            acc['id'] = str(uuid.uuid4())
            self.updated_accounts.append(acc)
            self._refresh_list()

    def _edit_account(self):
        current = self.account_list.currentItem()
        if not current:
            QMessageBox.information(self, 'Selección', 'Seleccione una cuenta para editar.')
            return
        
        acc_id = current.data(Qt.ItemDataRole.UserRole)
        acc = next((a for a in self.updated_accounts if a['id'] == acc_id), None)
        if not acc: return

        dlg = _AccountEditDialog(account_to_edit=acc, parent=self)
        if dlg.exec():
            # Update
            for i, a in enumerate(self.updated_accounts):
                if a['id'] == acc_id:
                    self.updated_accounts[i] = dlg.account_data
                    self.updated_accounts[i]['id'] = acc_id
                    break
            self._refresh_list()

    def _delete_account(self):
        current = self.account_list.currentItem()
        if not current:
            QMessageBox.information(self, 'Selección', 'Seleccione una cuenta para eliminar.')
            return
        
        acc_id = current.data(Qt.ItemDataRole.UserRole)
        
        # Check if in use
        in_use = any(t.get('account_id') == acc_id for t in self.transactions)
        if in_use:
            reply = QMessageBox.warning(
                self,
                'Cuenta en uso',
                'Esta cuenta tiene transacciones asociadas.\\n'
                '¿Desea eliminarla de todos modos?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
                
        self.updated_accounts = [a for a in self.updated_accounts if a['id'] != acc_id]
        self._refresh_list()


class _AccountEditDialog(QDialog):
    """Sub-dialog for editing a single account."""
    def __init__(self, account_to_edit: dict = None, parent=None):
        super().__init__(parent)
        self.account_to_edit = account_to_edit
        self.account_data = None
        
        self.setWindowTitle('Editar Cuenta' if account_to_edit else 'Nueva Cuenta')
        self.setMinimumWidth(350)
        self.setStyleSheet(CATPPUCCIN_STYLESHEET)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        form.addRow('Nombre:', self.name_edit)
        
        self.curr_edit = QLineEdit()
        self.curr_edit.setMaxLength(5)
        self.curr_edit.setText('$')
        form.addRow('Símbolo Moneda:', self.curr_edit)
        
        self.bal_spin = QDoubleSpinBox()
        self.bal_spin.setRange(-999999999, 999999999)
        self.bal_spin.setDecimals(2)
        form.addRow('Saldo Inicial:', self.bal_spin)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_cancel = QPushButton('Cancelar')
        btn_cancel.setObjectName('secondaryButton')
        btn_save = QPushButton('Guardar')
        btn_save.setObjectName('primaryButton')
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        layout.addLayout(btn_layout)
        
        btn_cancel.clicked.connect(self.reject)
        btn_save.clicked.connect(self._on_save)
        
        if account_to_edit:
            self.name_edit.setText(account_to_edit.get('name', ''))
            self.curr_edit.setText(account_to_edit.get('currency', '$'))
            self.bal_spin.setValue(account_to_edit.get('initial_balance', 0.0))
            
    def _on_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, 'Error', 'El nombre no puede estar vacío.')
            return
            
        self.account_data = {
            'name': name,
            'currency': self.curr_edit.text().strip() or '$',
            'initial_balance': self.bal_spin.value()
        }
        self.accept()
