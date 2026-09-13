# =============================================================================
# Vito Organizer v2.2 - Bodega Plugin
# Control de Inventario y Alertas de Reposición
# =============================================================================

import os
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QScrollArea, QFrame, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QStackedWidget, QCheckBox, QMessageBox, QDoubleSpinBox, QSpinBox,
    QButtonGroup, QFileDialog
)
from plugins.plugin_base import PluginBase
from data.data_store import DataStore
from plugins.bodega.dialogs import MovementDialog, BodegaSettingsDialog

class BodegaLeftView(QWidget):
    """Página izquierda: Lista consolidada de inventario (Componentes e Insumos)."""
    
    item_selected = pyqtSignal(dict, str) # (item, type: 'components'/'supplies')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.items = [] # list of tuples: (item, type_str)
        self.items_by_id = {}
        self.current_view = "stock" # "stock", "saldos", "costos", "consolidado"
        self.search_query = ""
        self.filter_low_stock = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 15, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_hdr_title = QLabel("Control de Inventario y Alertas")
        self.lbl_hdr_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_hdr_title)
        layout.addWidget(self.hdr_frame)

        # Stacked widget para las vistas
        self.stacked = QStackedWidget()

        # 0. Vista de lista (Stock, Saldos, Costos)
        self.list_widget = QWidget()
        lw_layout = QVBoxLayout(self.list_widget)
        lw_layout.setContentsMargins(0, 0, 0, 0)
        lw_layout.setSpacing(10)

        # Filtros y buscador
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar en bodega...")
        self.search_input.setStyleSheet("QLineEdit { background: white; border: 1px solid #CCC; border-radius: 4px; padding: 4px 8px; color: #333; }")
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_input, 1)

        self.chk_low_stock = QCheckBox("Solo bajo stock")
        self.chk_low_stock.setStyleSheet("QCheckBox { font-weight: bold; color: #555; }")
        self.chk_low_stock.toggled.connect(self._on_filter_changed)
        filter_layout.addWidget(self.chk_low_stock)
        lw_layout.addLayout(filter_layout)

        # Tabla consolidada
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(255, 255, 255, 0.9);
                border: 1px solid #D0C070;
                border-radius: 6px;
                gridline-color: #E5D595;
                color: #111;
            }
            QHeaderView::section {
                background-color: #E5D595 !important;
                color: #5C4033 !important;
                font-weight: bold !important;
                border: 1px solid #D0C070 !important;
                padding: 4px;
            }
        """)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        lw_layout.addWidget(self.table, 1)
        
        self.stacked.addWidget(self.list_widget)

        # 1. Vista Consolidado (Reporte General)
        self.consolidated_widget = QWidget()
        cw_layout = QVBoxLayout(self.consolidated_widget)
        cw_layout.setContentsMargins(0, 0, 0, 0)
        cw_layout.setSpacing(10)

        self.dashboard_frame = QFrame()
        self.dashboard_frame.setStyleSheet("QFrame { background-color: rgba(255, 255, 255, 0.9); border: 1px solid #D0C070; border-radius: 6px; padding: 15px; }")
        df_layout = QVBoxLayout(self.dashboard_frame)
        df_layout.setSpacing(12)

        self.lbl_consolidated_report = QLabel()
        self.lbl_consolidated_report.setWordWrap(True)
        self.lbl_consolidated_report.setStyleSheet("color: #111; font-size: 13px; border: none; background: transparent;")
        df_layout.addWidget(self.lbl_consolidated_report)

        # Tabla de elementos críticos en alerta
        lbl_alert_title = QLabel("⚠️ Elementos Críticos (Bajo Stock Mínimo)")
        lbl_alert_title.setStyleSheet("font-weight: bold; color: #D32F2F; font-size: 12px; border: none; background: transparent; margin-top: 10px;")
        df_layout.addWidget(lbl_alert_title)

        self.alert_table = QTableWidget()
        self.alert_table.setColumnCount(4)
        self.alert_table.setHorizontalHeaderLabels(["Tipo", "Nombre", "Stock", "Límite"])
        self.alert_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.alert_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.alert_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.alert_table.verticalHeader().setVisible(False)
        self.alert_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.alert_table.setColumnWidth(0, 90)   # Tipo
        self.alert_table.setColumnWidth(2, 50)   # Stock
        self.alert_table.setColumnWidth(3, 50)   # Límite
        self.alert_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                border: 1px solid #D32F2F;
                border-radius: 4px;
                color: #111111;
            }
            QHeaderView::section {
                background-color: #FFEBEE !important;
                color: #B71C1C !important;
                font-weight: bold !important;
                border: 1px solid #FFCDD2 !important;
                padding: 4px;
            }
        """)
        df_layout.addWidget(self.alert_table, 1)

        cw_layout.addWidget(self.dashboard_frame)
        self.stacked.addWidget(self.consolidated_widget)

        layout.addWidget(self.stacked, 1)

    def set_data(self, items: list, sort_order: str = 'alpha_asc'):
        self.items = items
        self.sort_order = sort_order
        self.items_by_id = {item.get('id'): (item, type_str) for item, type_str in items if item.get('id')}
        self._refresh()

    def _on_search_changed(self, text):
        self.search_query = text.lower().strip()
        self._refresh()

    def _on_filter_changed(self, checked):
        self.filter_low_stock = checked
        self._refresh()

    def _on_selection_changed(self):
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        item_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if item_id in getattr(self, 'items_by_id', {}):
            item_data, type_str = self.items_by_id[item_id]
            self.item_selected.emit(item_data, type_str)

    def _refresh(self):
        # Ordenar elementos antes de procesar
        sort_order = getattr(self, 'sort_order', 'alpha_asc')
        if sort_order == 'alpha_asc':
            self.items.sort(key=lambda x: str(x[0].get('name', '')).lower())
        elif sort_order == 'alpha_desc':
            self.items.sort(key=lambda x: str(x[0].get('name', '')).lower(), reverse=True)
        elif sort_order == 'date_asc':
            self.items.sort(key=lambda x: str(x[0].get('id', '')))
        elif sort_order == 'date_desc':
            self.items.sort(key=lambda x: str(x[0].get('id', '')), reverse=True)

        if getattr(self, 'current_view', 'stock') == 'consolidado':
            self.stacked.setCurrentIndex(1)
            self.lbl_hdr_title.setText("Consolidado de Bodega")
            self._build_consolidated_dashboard()
            return
        
        self.stacked.setCurrentIndex(0)
        self.table.setRowCount(0)
        
        # Ajustar columnas y cabeceras de la tabla según la vista activa
        view = getattr(self, 'current_view', 'stock')
        if view == 'stock':
            self.lbl_hdr_title.setText("Control de Inventario y Alertas")
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Tipo", "Nombre", "Stock", "Mínimo", "Estado"])
            self.table.setColumnWidth(0, 80)   # Tipo
            self.table.setColumnWidth(2, 50)   # Stock
            self.table.setColumnWidth(3, 50)   # Mínimo
            self.table.setColumnWidth(4, 80)   # Estado
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        elif view == 'saldos':
            self.lbl_hdr_title.setText("Vista de Saldos y Ubicaciones")
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Tipo", "Nombre", "Saldo (Stock)", "Unidad", "Ubicación"])
            self.table.setColumnWidth(0, 80)   # Tipo
            self.table.setColumnWidth(2, 80)   # Saldo
            self.table.setColumnWidth(3, 80)   # Unidad
            self.table.setColumnWidth(4, 150)  # Ubicación
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        elif view == 'costos':
            self.lbl_hdr_title.setText("Valoración y Costos de Inventario")
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Tipo", "Nombre", "Stock", "Costo Unit.", "Valor Total"])
            self.table.setColumnWidth(0, 80)   # Tipo
            self.table.setColumnWidth(2, 60)   # Stock
            self.table.setColumnWidth(3, 100)  # Costo Unit.
            self.table.setColumnWidth(4, 100)  # Valor Total
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        # Rellenar filas
        row_idx = 0
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')

        for item, type_str in self.items:
            name = item.get('name', '')
            stock = item.get('stock_quantity', 0)
            min_stock = item.get('min_stock_quantity', 0)
            is_low = stock <= min_stock

            if self.filter_low_stock and not is_low:
                continue

            if self.search_query:
                if self.search_query not in name.lower() and self.search_query not in type_str.lower():
                    continue

            self.table.insertRow(row_idx)
            
            # Tipo Col
            type_display = "Componente" if type_str == 'components' else "Insumo"
            type_item = QTableWidgetItem(type_display)
            type_item.setData(Qt.ItemDataRole.UserRole, item.get('id'))
            self.table.setItem(row_idx, 0, type_item)

            # Nombre Col
            name_item = QTableWidgetItem(name)
            self.table.setItem(row_idx, 1, name_item)

            if view == 'stock':
                # Stock
                stock_item = QTableWidgetItem(str(stock))
                self.table.setItem(row_idx, 2, stock_item)
                # Mínimo
                min_item = QTableWidgetItem(str(min_stock))
                self.table.setItem(row_idx, 3, min_item)
                # Estado
                status_str = "REPOSICIÓN" if is_low else "OK"
                status_item = QTableWidgetItem(status_str)
                if is_low:
                    status_item.setForeground(QColor("#D32c2c"))
                    status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                else:
                    status_item.setForeground(QColor("#2e7d32"))
                self.table.setItem(row_idx, 4, status_item)

            elif view == 'saldos':
                # Saldo (Stock)
                stock_item = QTableWidgetItem(str(stock))
                self.table.setItem(row_idx, 2, stock_item)
                # Unidad
                unit_str = item.get('unit', 'unidades') if type_str == 'supplies' else 'unidades'
                self.table.setItem(row_idx, 3, QTableWidgetItem(unit_str))
                # Ubicación
                loc_str = item.get('storage_location', 'No definido')
                self.table.setItem(row_idx, 4, QTableWidgetItem(loc_str))

            elif view == 'costos':
                # Stock
                stock_item = QTableWidgetItem(str(stock))
                self.table.setItem(row_idx, 2, stock_item)
                # Costo Unitario
                cost = item.get('cost_value', 0.0)
                cost_item = QTableWidgetItem(f"{cost:.2f} {currency}")
                self.table.setItem(row_idx, 3, cost_item)
                # Valor Total
                total = stock * cost
                total_item = QTableWidgetItem(f"{total:.2f} {currency}")
                total_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                total_item.setForeground(QColor("#1565C0"))
                self.table.setItem(row_idx, 4, total_item)

            row_idx += 1

    def _build_consolidated_dashboard(self):
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')

        total_components = 0
        total_supplies = 0
        value_components = 0.0
        value_supplies = 0.0
        low_stock_items = []

        for item, type_str in self.items:
            stock = item.get('stock_quantity', 0)
            cost = item.get('cost_value', 0.0)
            min_stock = item.get('min_stock_quantity', 0)
            
            if type_str == 'components':
                total_components += stock
                value_components += stock * cost
            else:
                total_supplies += stock
                value_supplies += stock * cost

            if stock <= min_stock:
                low_stock_items.append((item, type_str))

        grand_total_value = value_components + value_supplies

        # Reporte HTML
        txt = f"<h3 style='margin:0; color:#D2691E;'>📊 Balance Consolidado de Existencias</h3>"
        txt += f"<table style='width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 15px; font-size: 12px;'>"
        txt += f"<tr style='background-color: #E5D595; color: #5C4033;'><td style='padding: 6px; font-weight: bold;'>Categoría de Inventario</td><td style='padding: 6px; font-weight: bold; text-align: right;'>Cantidad Total</td><td style='padding: 6px; font-weight: bold; text-align: right;'>Valoración Total ({currency})</td></tr>"
        txt += f"<tr><td style='padding: 6px; border-bottom: 1px solid #CCC;'>Componentes Electrónicos</td><td style='padding: 6px; border-bottom: 1px solid #CCC; text-align: right;'>{total_components} unidades</td><td style='padding: 6px; border-bottom: 1px solid #CCC; text-align: right; color: #1565C0;'>{value_components:.2f} {currency}</td></tr>"
        txt += f"<tr><td style='padding: 6px; border-bottom: 1px solid #CCC;'>Insumos de Taller</td><td style='padding: 6px; border-bottom: 1px solid #CCC; text-align: right;'>{total_supplies} unidades</td><td style='padding: 6px; border-bottom: 1px solid #CCC; text-align: right; color: #1565C0;'>{value_supplies:.2f} {currency}</td></tr>"
        txt += f"<tr style='font-weight: bold; background-color: rgba(210,105,30,0.15);'><td style='padding: 6px;'>VALORACIÓN TOTAL DEL INVENTARIO</td><td style='padding: 6px; text-align: right;'>{total_components + total_supplies} unidades</td><td style='padding: 6px; text-align: right; color: #D2691E;'>{grand_total_value:.2f} {currency}</td></tr>"
        txt += f"</table>"
        txt += f"<p style='margin:0; font-size: 11px;'><b>Alertas Activas:</b> Actualmente hay <span style='color: #D32F2F; font-weight: bold;'>{len(low_stock_items)}</span> elementos que requieren reposición urgente por estar bajo su límite mínimo de stock.</p>"
        
        self.lbl_consolidated_report.setText(txt)

        # Rellenar la tabla de elementos críticos
        self.alert_table.setRowCount(0)
        for idx, (item, type_str) in enumerate(low_stock_items):
            self.alert_table.insertRow(idx)
            
            # Tipo
            type_display = "Componente" if type_str == 'components' else "Insumo"
            item_type = QTableWidgetItem(type_display)
            item_type.setForeground(QColor("#D32F2F"))
            self.alert_table.setItem(idx, 0, item_type)
            
            # Nombre
            item_name = QTableWidgetItem(item.get('name', ''))
            item_name.setForeground(QColor("#111111"))
            self.alert_table.setItem(idx, 1, item_name)
            
            # Stock
            item_stock = QTableWidgetItem(str(item.get('stock_quantity', 0)))
            item_stock.setForeground(QColor("#D32F2F"))
            item_stock.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.alert_table.setItem(idx, 2, item_stock)
            
            # Límite
            item_min = QTableWidgetItem(str(item.get('min_stock_quantity', 0)))
            item_min.setForeground(QColor("#111111"))
            self.alert_table.setItem(idx, 3, item_min)


class BodegaRightView(QWidget):
    """Página derecha: Panel detallado de control de stock y registro de movimientos."""
    
    movement_registered = pyqtSignal()
    card_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.current_item = None
        self.type_str = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 25, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_title = QLabel("Control de Stock")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_title)
        layout.addWidget(self.hdr_frame)

        self.stack = QStackedWidget()

        # 0. Placeholder
        self.empty_lbl = QLabel("Selecciona un elemento de la lista para registrar movimientos.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        self.stack.addWidget(self.empty_lbl)

        # 1. Detalle del stock y acciones
        self.detail_widget = QWidget()
        det_layout = QVBoxLayout(self.detail_widget)
        det_layout.setContentsMargins(0, 0, 0, 0)
        det_layout.setSpacing(10)

        # Ficha Resumen
        self.card_frame = QFrame()
        self.card_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #D0C070; border-radius: 6px; padding: 12px; }")
        cf_layout = QVBoxLayout(self.card_frame)

        self.lbl_item_info = QLabel()
        self.lbl_item_info.setWordWrap(True)
        self.lbl_item_info.setStyleSheet("color: #111; font-size: 13px;")
        cf_layout.addWidget(self.lbl_item_info)

        # Controles de edición en línea dentro de card_frame
        self.edit_frame = QFrame()
        self.edit_frame.setStyleSheet("QFrame { border: none; background: transparent; padding: 0px; }")
        edit_layout = QHBoxLayout(self.edit_frame)
        edit_layout.setContentsMargins(0, 5, 0, 5)
        edit_layout.setSpacing(10)
        
        lbl_min = QLabel("Stock Mín.:")
        lbl_min.setStyleSheet("color: #333; font-weight: bold; border: none; background: transparent; font-size: 11px;")
        self.spin_min_stock = QSpinBox()
        self.spin_min_stock.setRange(0, 999999)
        self.spin_min_stock.setStyleSheet("background-color: white; color: black; border: 1px solid #CCC; border-radius: 4px; padding: 2px; font-size: 11px;")
        
        lbl_cost = QLabel("Costo Unit.:")
        lbl_cost.setStyleSheet("color: #333; font-weight: bold; border: none; background: transparent; font-size: 11px;")
        self.spin_cost = QDoubleSpinBox()
        self.spin_cost.setRange(0.0, 99999999.0)
        self.spin_cost.setDecimals(2)
        self.spin_cost.setStyleSheet("background-color: white; color: black; border: 1px solid #CCC; border-radius: 4px; padding: 2px; font-size: 11px;")
        
        self.btn_save_card = QPushButton("Guardar")
        self.btn_save_card.setStyleSheet("QPushButton { background-color: #f57c00; color: white; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 11px; } QPushButton:hover { background-color: #e64a19; }")
        self.btn_save_card.clicked.connect(self._on_save_card_changes)
        
        edit_layout.addWidget(lbl_min)
        edit_layout.addWidget(self.spin_min_stock)
        edit_layout.addWidget(lbl_cost)
        edit_layout.addWidget(self.spin_cost)
        edit_layout.addWidget(self.btn_save_card)
        
        cf_layout.addWidget(self.edit_frame)

        # Alerta stock mínimo
        self.lbl_alert = QLabel("⚠️ STOCK BAJO NIVEL MÍNIMO DE REPOSICIÓN")
        self.lbl_alert.setStyleSheet("color: #D32F2F; font-weight: bold; font-size: 12px; padding: 4px; border: 1px solid #D32F2F; border-radius: 4px; background-color: #FFEBEE;")
        cf_layout.addWidget(self.lbl_alert)

        # Botones de ingreso / egreso
        btn_layout = QHBoxLayout()
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        
        self.btn_ingreso = QPushButton(" Registrar Ingreso")
        self.btn_ingreso.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        self.btn_ingreso.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_ingreso.clicked.connect(self._on_ingreso)
        btn_layout.addWidget(self.btn_ingreso)

        self.btn_egreso = QPushButton(" Registrar Retiro")
        self.btn_egreso.setIcon(QIcon(os.path.join(icons_dir, 'box.svg')))
        self.btn_egreso.setStyleSheet("QPushButton { background-color: #e65100; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #b71c1c; }")
        self.btn_egreso.clicked.connect(self._on_egreso)
        btn_layout.addWidget(self.btn_egreso)

        cf_layout.addLayout(btn_layout)
        det_layout.addWidget(self.card_frame)

        # Historial de Movimientos Recientes
        self.mv_frame = QFrame()
        self.mv_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.8); border: 1px solid #D0C070; border-radius: 6px; }")
        mvf_layout = QVBoxLayout(self.mv_frame)
        mvf_layout.setContentsMargins(10, 8, 10, 8)

        lbl_mv_title = QLabel("Movimientos Recientes del Ítem")
        lbl_mv_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #333; border: none; background: transparent;")
        mvf_layout.addWidget(lbl_mv_title)

        self.mv_table = QTableWidget()
        self.mv_table.setColumnCount(4)
        self.mv_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Cant.", "Detalles / Motivo"])
        self.mv_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.mv_table.setStyleSheet("QTableWidget { background-color: white; border: 1px solid #CCC; }")
        mvf_layout.addWidget(self.mv_table, 1)

        det_layout.addWidget(self.mv_frame, 1)

        self.stack.addWidget(self.detail_widget)
        layout.addWidget(self.stack, 1)

    def set_item(self, item: dict, type_str: str):
        self.current_item = item
        self.type_str = type_str

        if not item:
            self.stack.setCurrentIndex(0)
            return

        self.stack.setCurrentIndex(1)
        self.lbl_title.setText(f"Control de Stock: {item.get('name')}")

        self.spin_min_stock.setValue(item.get('min_stock_quantity', 0))
        self.spin_cost.setValue(item.get('cost_value', 0.0))
        
        from config.settings import Settings
        settings = Settings.load()
        currency = getattr(settings.general, 'cost_currency', 'CLP')
        self.spin_cost.setSuffix(f" {currency}")
        
        stock = item.get('stock_quantity', 0)
        min_stock = item.get('min_stock_quantity', 0)
        cost = item.get('cost_value', 0.0)
        total = stock * cost
        unit = item.get('unit', 'unidades') if type_str == 'supplies' else 'unidades'
        is_low = stock <= min_stock

        self.lbl_alert.setVisible(is_low)

        txt = f"<h3 style='margin:0; color:#D2691E;'>{item.get('name')}</h3>"
        txt += f"<b>Tipo de elemento:</b> {'Componente Electrónico' if type_str == 'components' else 'Insumo de Taller'}<br>"
        txt += f"<b>Stock Disponible:</b> <span style='font-size: 14px; font-weight: bold; color: {'#D32F2F' if is_low else '#2E7D32'};'>{stock} {unit}</span><br>"
        txt += f"<b>Stock Mínimo (Límite):</b> {min_stock} {unit}<br>"
        txt += f"<b>Costo Unitario:</b> {cost:.2f} {currency}<br>"
        txt += f"<b>Valor Total de Stock:</b> <span style='font-weight: bold; color: #1565C0;'>{total:.2f} {currency}</span><br>"
        txt += f"<b>Lugar de Almacenamiento:</b> {item.get('storage_location', 'No definido')}<br>"
        self.lbl_item_info.setText(txt)

        self._refresh_movements()

    def _refresh_movements(self):
        self.mv_table.setRowCount(0)
        if not self.current_item: return
        mvs = self.current_item.get('movements', [])
        for i, mv in enumerate(mvs):
            self.mv_table.insertRow(i)
            
            # Fecha
            item_date = QTableWidgetItem(mv.get('date', ''))
            item_date.setForeground(QColor("#111111"))
            self.mv_table.setItem(i, 0, item_date)
            
            # Tipo
            item_type = QTableWidgetItem(mv.get('type', '').capitalize())
            item_type.setForeground(QColor("#111111"))
            self.mv_table.setItem(i, 1, item_type)
            
            # Cantidad (Verde para ingresos, Rojo para egresos)
            qty_val = mv.get('quantity', 0)
            is_ingreso = mv.get('type') == 'ingreso'
            qty_str = f"+{qty_val}" if is_ingreso else f"-{qty_val}"
            item_qty = QTableWidgetItem(qty_str)
            item_qty.setForeground(QColor("#2e7d32" if is_ingreso else "#c62828"))
            item_qty.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.mv_table.setItem(i, 2, item_qty)
            
            # Detalles / Motivo
            item_notes = QTableWidgetItem(mv.get('notes', ''))
            item_notes.setForeground(QColor("#111111"))
            self.mv_table.setItem(i, 3, item_notes)

    def _on_ingreso(self):
        self._register_movement(is_egreso=False)

    def _on_egreso(self):
        self._register_movement(is_egreso=True)

    def _register_movement(self, is_egreso: bool):
        if not self.current_item: return
        dlg = MovementDialog(self.current_item.get('name'), self.current_item.get('stock_quantity', 0), is_egreso, self.current_item.get('cost_value', 0.0), self)
        if dlg.exec() and dlg.movement_data:
            mv = dlg.movement_data
            qty = mv.get('quantity', 0)
            if mv.get('type') == 'egreso':
                self.current_item['stock_quantity'] -= qty
            else:
                self.current_item['stock_quantity'] += qty
                self.current_item['cost_value'] = mv.get('cost_value', 0.0)

            self.current_item.setdefault('movements', []).append(mv)
            self.movement_registered.emit()

    def _on_save_card_changes(self):
        if not self.current_item: return
        self.current_item['min_stock_quantity'] = self.spin_min_stock.value()
        self.current_item['cost_value'] = self.spin_cost.value()
        self.card_updated.emit()
        self.set_item(self.current_item, self.type_str)


class BodegaSidebar(QWidget):
    """Barra lateral: Estadísticas y leyendas rápidas de bodega."""
    
    refresh_clicked = pyqtSignal()
    view_changed = pyqtSignal(str)
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(15)

        title = QLabel("Módulos Bodega")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; padding-bottom: 5px;")
        layout.addWidget(title)

        # Panel de Estado
        self.status_card = QFrame()
        self.status_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 10px; }")
        sc_layout = QVBoxLayout(self.status_card)

        self.lbl_stats = QLabel("Consolidado Stock:<br>Cargando datos...")
        self.lbl_stats.setStyleSheet("color: #E0E0E0; font-size: 11px; line-height: 1.4;")
        sc_layout.addWidget(self.lbl_stats)
        layout.addWidget(self.status_card)

        # Grupo de Navegación de Vistas
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        self.btn_stock = QPushButton("  Vista de Stock")
        self.btn_stock.setCheckable(True)
        self.btn_stock.setChecked(True)
        self.btn_stock.setIcon(QIcon(os.path.join(icons_dir, 'box.svg')))
        self.btn_stock.setStyleSheet("QPushButton { text-align: left; padding: 8px 12px; border-radius: 5px; background-color: transparent; color: #E0E0E0; font-weight: bold; font-size: 11px; border: none; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); } QPushButton:checked { background-color: rgba(255, 255, 255, 0.15); color: #FFFFFF; border-left: 3px solid #ff5722; }")
        self.btn_stock.clicked.connect(lambda: self.view_changed.emit('stock'))
        
        self.btn_saldos = QPushButton("  Vista de Saldos")
        self.btn_saldos.setCheckable(True)
        self.btn_saldos.setIcon(QIcon(os.path.join(icons_dir, 'box.svg')))
        self.btn_saldos.setStyleSheet("QPushButton { text-align: left; padding: 8px 12px; border-radius: 5px; background-color: transparent; color: #E0E0E0; font-weight: bold; font-size: 11px; border: none; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); } QPushButton:checked { background-color: rgba(255, 255, 255, 0.15); color: #FFFFFF; border-left: 3px solid #ff5722; }")
        self.btn_saldos.clicked.connect(lambda: self.view_changed.emit('saldos'))

        self.btn_costos = QPushButton("  Vista de Costos")
        self.btn_costos.setCheckable(True)
        self.btn_costos.setIcon(QIcon(os.path.join(icons_dir, 'tag.svg')))
        self.btn_costos.setStyleSheet("QPushButton { text-align: left; padding: 8px 12px; border-radius: 5px; background-color: transparent; color: #E0E0E0; font-weight: bold; font-size: 11px; border: none; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); } QPushButton:checked { background-color: rgba(255, 255, 255, 0.15); color: #FFFFFF; border-left: 3px solid #ff5722; }")
        self.btn_costos.clicked.connect(lambda: self.view_changed.emit('costos'))

        self.btn_consolidado = QPushButton("  Consolidado")
        self.btn_consolidado.setCheckable(True)
        self.btn_consolidado.setIcon(QIcon(os.path.join(icons_dir, 'chart.svg')))
        self.btn_consolidado.setStyleSheet("QPushButton { text-align: left; padding: 8px 12px; border-radius: 5px; background-color: transparent; color: #E0E0E0; font-weight: bold; font-size: 11px; border: none; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); } QPushButton:checked { background-color: rgba(255, 255, 255, 0.15); color: #FFFFFF; border-left: 3px solid #ff5722; }")
        self.btn_consolidado.clicked.connect(lambda: self.view_changed.emit('consolidado'))

        self.nav_group.addButton(self.btn_stock, 0)
        self.nav_group.addButton(self.btn_saldos, 1)
        self.nav_group.addButton(self.btn_costos, 2)
        self.nav_group.addButton(self.btn_consolidado, 3)

        layout.addWidget(self.btn_stock)
        layout.addWidget(self.btn_saldos)
        layout.addWidget(self.btn_costos)
        layout.addWidget(self.btn_consolidado)

        # Botón de Refrescar
        btn_refresh = QPushButton(" Refrescar Bodega")
        btn_refresh.setIcon(QIcon(os.path.join(icons_dir, 'history.svg')))
        btn_refresh.setStyleSheet("QPushButton { text-align: left; padding: 6px 10px; border-radius: 5px; background-color: rgba(255, 255, 255, 0.08); color: #ffffff; font-weight: bold; font-size: 11px; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }")
        btn_refresh.clicked.connect(self.refresh_clicked)
        layout.addWidget(btn_refresh)

        layout.addStretch()

        # Botón de engranaje inferior izquierdo
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Bodega")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def update_stats(self, total_items: int, low_stock_items: int):
        txt = f"<b>Estado General Bodega:</b><br>"
        txt += f"Total de Ítems: <b>{total_items}</b><br>"
        txt += f"Bajo Mínimo (Alerta): <span style='color: #ff8a80; font-weight: bold;'>{low_stock_items}</span>"
        self.lbl_stats.setText(txt)


class BodegaPlugin(PluginBase):
    """Plugin de la sección Bodega."""

    def __init__(self):
        super().__init__()
        self._data = {}
        self._is_modified = False

        # Inicializar vistas
        self._sidebar = BodegaSidebar()
        self._left_page = BodegaLeftView()
        self._right_page = BodegaRightView()

        # Conectar señales
        self._sidebar.refresh_clicked.connect(self._refresh_data)
        self._sidebar.view_changed.connect(self._on_view_changed)
        self._sidebar.settings_clicked.connect(self._on_show_settings)
        self._left_page.item_selected.connect(self._on_item_selected)
        self._right_page.movement_registered.connect(self._on_movement_registered)
        self._right_page.card_updated.connect(self._on_movement_registered)

    def get_name(self) -> str: return "Bodega"
    def get_id(self) -> str: return "bodega"
    def get_icon(self) -> str: return "box.svg"
    def get_tab_color(self) -> str: return "#D2691E"
    def get_order(self) -> int: return 8

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

    def supports_pdf_export(self) -> bool:
        return True

    def set_correlativos_manager(self, manager):
        self.correlativos_manager = manager

    def export_pdf(self, parent_widget=None):
        cur_view = getattr(self._left_page, 'current_view', 'stock')
        items = getattr(self._left_page, 'items', [])

        config = {}
        if cur_view == 'consolidado':
            config = {'element_type': 'all', 'stock_filter': 'all'}
        else:
            locations = sorted(list({item.get('storage_location') for item, _ in items if item.get('storage_location')}))
            from plugins.bodega.dialogs import BodegaPDFExportDialog
            dlg = BodegaPDFExportDialog(cur_view, locations, parent_widget)
            if not dlg.exec():
                return
            config = dlg.export_config or {}

        # Seleccionar ruta para guardar el PDF
        def_name = f"Reporte_Bodega_{cur_view.capitalize()}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(
            parent_widget,
            "Guardar Reporte PDF",
            def_name,
            "Archivos PDF (*.pdf)"
        )

        if not filepath:
            return

        if not filepath.lower().endswith('.pdf'):
            filepath += '.pdf'

        # Obtener gestor de correlativos
        manager = getattr(self, 'correlativos_manager', None)
        if not manager:
            from core.correlativos_manager import CorrelativosManager
            agenda_p = self.get_agenda_path()
            if agenda_p:
                manager = CorrelativosManager(agenda_p)
                self.correlativos_manager = manager

        serial_str = "INFO0000000"
        key = "GLOBAL"
        count = 1

        if manager:
            key, count, serial_str = manager.get_next_serial_info("Información")

        try:
            from plugins.bodega.pdf_export import generate_bodega_pdf
            generate_bodega_pdf(
                filepath,
                cur_view,
                items,
                config,
                serial_str,
                self.get_agenda_path()
            )

            if manager:
                manager.commit_serial("Información", key, count)

            QMessageBox.information(
                parent_widget,
                "PDF Generado Exitosamente",
                f"El reporte de Bodega fue guardado en:\n{filepath}\n\nCorrelativo asignado: {serial_str}"
            )
        except Exception as e:
            QMessageBox.critical(
                parent_widget,
                "Error al Generar PDF",
                f"Ocurrió un error al crear el archivo PDF:\n{str(e)}"
            )

    def on_activate(self):
        super().on_activate()
        self._refresh_data()

    def load_data(self, agenda_path: str):
        self.agenda_path = agenda_path
        self._refresh_data()

    def save_data(self, agenda_path: str):
        # La Bodega modifica el inventario de laboratorio directamente, por lo que guardaremos los datos de Laboratorio.
        if self._is_modified:
            lab_path = DataStore.get_plugin_data_path(agenda_path, 'laboratorio')
            lab_data = DataStore.load(lab_path)
            if lab_data:
                # Mapear los cambios
                # Dado que modificamos los diccionarios por referencia (in-place) en memoria, lab_data puede que ya tenga los cambios si cargó en el mismo proceso.
                # Para asegurar la consistencia, guardamos el estado de self._data (que es el de laboratorio) en el archivo de laboratorio.
                DataStore.save(lab_path, self._data)
            self._is_modified = False

    def _refresh_data(self):
        cur_agenda = getattr(self, 'agenda_path', None)
        if not cur_agenda:
            return

        # Cargar datos de laboratorio
        lab_path = DataStore.get_plugin_data_path(cur_agenda, 'laboratorio')
        lab_data = DataStore.load(lab_path)
        if not lab_data:
            lab_data = {'components': [], 'instruments': [], 'tools': [], 'supplies': [], '_trash': []}

        self._data = lab_data

        # Consolidar componentes e insumos
        consolidated = []
        low_stock_count = 0
        
        components = lab_data.get('components', [])
        for c in components:
            consolidated.append((c, 'components'))
            if c.get('stock_quantity', 0) <= c.get('min_stock_quantity', 0):
                low_stock_count += 1

        supplies = lab_data.get('supplies', [])
        for s in supplies:
            consolidated.append((s, 'supplies'))
            if s.get('stock_quantity', 0) <= s.get('min_stock_quantity', 0):
                low_stock_count += 1

        self._left_page.set_data(consolidated, sort_order=self._data.get('bodega_sort_order', 'alpha_asc'))
        self._sidebar.update_stats(len(consolidated), low_stock_count)
        
        # Mantener selección si el elemento sigue existiendo
        current = self._right_page.current_item
        current_type = self._right_page.type_str
        if current:
            # Buscar el elemento actualizado en los nuevos datos cargados
            found = None
            items_list = self._data.get(current_type, [])
            for it in items_list:
                if it.get('id') == current.get('id'):
                    found = it
                    break
            if found:
                self._right_page.set_item(found, current_type)
            else:
                self._right_page.set_item(None, "")
        else:
            self._right_page.set_item(None, "")

    def _on_item_selected(self, item: dict, type_str: str):
        self._right_page.set_item(item, type_str)

    def _on_view_changed(self, view_name: str):
        self._left_page.current_view = view_name
        self._left_page._refresh()

    def _on_movement_registered(self):
        self._is_modified = True
        # Guardar inmediatamente para persistencia
        cur_agenda = getattr(self, 'agenda_path', None)
        if cur_agenda:
            self.save_data(cur_agenda)
        self._refresh_data()

    def _on_show_settings(self):
        dlg = BodegaSettingsDialog(plugin_data=self._data, parent=self._sidebar.window())
        if dlg.exec():
            self._is_modified = True
            self._refresh_data()
            if self.agenda_path:
                self.save_data(self.agenda_path)

