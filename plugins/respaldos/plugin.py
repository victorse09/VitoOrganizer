import os
import shutil
import uuid
import json
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QLineEdit, QStackedWidget, QFileDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, QComboBox, QCheckBox
)

from plugins.plugin_base import PluginBase
from data.data_store import DataStore
from plugins.respaldos.dialogs import DiskDialog, RespaldosSettingsDialog, DiskUsageChartDialog, format_size

class ClickableFrame(QFrame):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)

class RespaldosSidebar(QWidget):
    search_changed = pyqtSignal(str)
    add_disk_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()
    sort_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        btn_add = QPushButton(" Nuevo Disco/Respaldo")
        btn_add.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        btn_add.setStyleSheet("""
            QPushButton { text-align: left; padding: 6px 10px; border-radius: 5px; background-color: rgba(255, 255, 255, 0.1); color: #ffffff; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.25); }
        """)
        btn_add.clicked.connect(self.add_disk_clicked.emit)
        layout.addWidget(btn_add)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar disco...")
        self.search_input.addAction(QIcon(os.path.join(icons_dir, 'search.svg')), QLineEdit.ActionPosition.LeadingPosition)
        self.search_input.setStyleSheet("QLineEdit { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px 8px; }")
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        # Combo Ordenar
        self.cmb_sort = QComboBox()
        self.cmb_sort.addItems(["A-Z (Nombre)", "Z-A (Nombre)", "Más antiguos", "Más recientes", "0-9 (Número de disco)", "9-0 (Número de disco)"])
        self.cmb_sort.setStyleSheet("QComboBox { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px 8px; } QComboBox QAbstractItemView { background: #313244; color: white; selection-background-color: #8B0000; }")
        self.cmb_sort.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.cmb_sort)

        layout.addStretch()

        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(icons_dir, 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setStyleSheet("QPushButton { border: none; background: transparent; border-radius: 4px; } QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }")
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def _on_sort_changed(self, index):
        if index == 0: val = 'alpha_asc'
        elif index == 1: val = 'alpha_desc'
        elif index == 2: val = 'date_asc'
        elif index == 3: val = 'date_desc'
        elif index == 4: val = 'num_asc'
        elif index == 5: val = 'num_desc'
        self.sort_changed.emit(val)

    def set_sort_order(self, order_str: str):
        self.cmb_sort.blockSignals(True)
        if order_str == 'alpha_asc': self.cmb_sort.setCurrentIndex(0)
        elif order_str == 'alpha_desc': self.cmb_sort.setCurrentIndex(1)
        elif order_str == 'date_asc': self.cmb_sort.setCurrentIndex(2)
        elif order_str == 'date_desc': self.cmb_sort.setCurrentIndex(3)
        elif order_str == 'num_asc': self.cmb_sort.setCurrentIndex(4)
        elif order_str == 'num_desc': self.cmb_sort.setCurrentIndex(5)
        self.cmb_sort.blockSignals(False)


class RespaldosLeftView(QWidget):
    item_selected = pyqtSignal(dict)
    edit_item_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.items = []
        self.search_query = ''
        self.sort_order = 'alpha_asc'
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 35, 15)
        layout.setSpacing(10)

        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        lbl_hdr_title = QLabel("Catálogo de Respaldos")
        lbl_hdr_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(lbl_hdr_title)
        layout.addWidget(self.hdr_frame)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(6)

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

    def set_data(self, items: list, search_query: str = '', sort_order: str = 'alpha_asc'):
        self.items = items
        self.search_query = search_query.lower().strip()
        self.sort_order = sort_order
        self._refresh()

    def _refresh(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

        filtered = []
        for it in self.items:
            if self.search_query:
                name_match = self.search_query in it.get('name', '').lower()
                cat_match = self.search_query in it.get('category', '').lower()
                num_match = self.search_query in it.get('disk_number', '').lower()
                if not (name_match or cat_match or num_match): continue
            filtered.append(it)

        # Aplicar orden
        sort_order = getattr(self, 'sort_order', 'alpha_asc')
        if sort_order == 'alpha_asc':
            filtered.sort(key=lambda x: str(x.get('name', '')).lower())
        elif sort_order == 'alpha_desc':
            filtered.sort(key=lambda x: str(x.get('name', '')).lower(), reverse=True)
        elif sort_order == 'date_asc':
            filtered.sort(key=lambda x: str(x.get('id', '')))
        elif sort_order == 'date_desc':
            filtered.sort(key=lambda x: str(x.get('id', '')), reverse=True)
        elif sort_order == 'num_asc':
            filtered.sort(key=lambda x: str(x.get('disk_number', '')).lower())
        elif sort_order == 'num_desc':
            filtered.sort(key=lambda x: str(x.get('disk_number', '')).lower(), reverse=True)

        if not filtered:
            lbl_empty = QLabel("No hay discos registrados.")
            lbl_empty.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
            lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(lbl_empty)
        else:
            icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
            for item in filtered:
                card = ClickableFrame()
                card.setFixedHeight(54)
                card.setCursor(Qt.CursorShape.PointingHandCursor)
                card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.85); border: 1px solid #20B2AA; border-radius: 6px; } QFrame:hover { background-color: rgba(255,255,255,1); border-color: #178b85; }")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(10, 4, 10, 4)

                disk_num = item.get('disk_number', '')
                prefix = f"<span style='color:#8B0000; font-weight:bold;'>[{disk_num}]</span> " if disk_num else ""
                
                stats = item.get('storage_stats')
                disp_str = ""
                if stats and 'free_bytes' in stats:
                    free_b = float(stats.get('free_bytes', 0))
                    disp_str = f" • <span style='color:#2E7D32; font-weight:bold; font-size:11px;'>Disponible: {format_size(free_b)}</span>"

                lbl_txt = f"{prefix}<b>{item.get('name')}</b> ({item.get('capacity_gb', 0)} GB){disp_str}<br><span style='color:#555; font-size:11px;'>Categoría: <b>{item.get('category')}</b> | {item.get('tech')}</span>"

                lbl = QLabel(lbl_txt)
                lbl.setStyleSheet("border: none; background: transparent; color: #111111;")
                lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                c_layout.addWidget(lbl, 1)

                btn_edit = QPushButton("Editar")
                btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil.svg')))
                btn_edit.setFixedSize(65, 26)
                btn_edit.setStyleSheet("border: 1px solid #CCC; background: #F0F0F0; border-radius: 4px; font-size: 11px; font-weight: bold; color: #333;")
                btn_edit.clicked.connect(lambda checked, it=item: self.edit_item_requested.emit(it))
                c_layout.addWidget(btn_edit)

                card.clicked.connect(lambda checked=False, it=item: self.item_selected.emit(it))
                self.scroll_layout.addWidget(card)

        self.scroll_layout.addStretch()


class RespaldosRightView(QWidget):
    scan_requested = pyqtSignal(dict, str, bool) # (item, dir_path, include_files)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.current_item = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(35, 15, 25, 15)
        layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        self.hdr_frame = QFrame()
        self.hdr_frame.setFixedHeight(34)
        self.hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(self.hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        self.lbl_title = QLabel("Detalles del Disco")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_title, 1)

        layout.addWidget(self.hdr_frame)
        
        self.stack = QStackedWidget()
        self.empty_lbl = QLabel("Selecciona un disco para ver su contenido.")
        self.empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_lbl.setStyleSheet("color: #666666; font-size: 13px; font-style: italic;")
        self.stack.addWidget(self.empty_lbl)

        self.detail_container = QWidget()
        d_layout = QVBoxLayout(self.detail_container)
        d_layout.setContentsMargins(0, 0, 0, 0)
        d_layout.setSpacing(8)
        
        self.card_info = QFrame()
        self.card_info.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.9); border: 1px solid #20B2AA; border-radius: 6px; padding: 10px; }")
        ci_layout = QVBoxLayout(self.card_info)
        ci_layout.setSpacing(6)

        self.lbl_detail_text = QLabel()
        self.lbl_detail_text.setWordWrap(True)
        self.lbl_detail_text.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 13px;")
        ci_layout.addWidget(self.lbl_detail_text)

        # Botón para ver gráfico si el disco fue escaneado
        chart_btn_layout = QHBoxLayout()
        self.btn_chart = QPushButton(" Ver Gráfico de Espacio")
        self.btn_chart.setIcon(QIcon(os.path.join(icons_dir, 'chart.svg')))
        self.btn_chart.setStyleSheet("QPushButton { background-color: #20B2AA; color: white; font-weight: bold; padding: 5px 12px; border-radius: 4px; font-size: 12px; } QPushButton:hover { background-color: #178b85; }")
        self.btn_chart.clicked.connect(self._on_show_chart)
        self.btn_chart.setVisible(False)
        chart_btn_layout.addWidget(self.btn_chart)
        chart_btn_layout.addStretch()
        ci_layout.addLayout(chart_btn_layout)

        d_layout.addWidget(self.card_info)

        # Botón para escanear y checkbox de incluir archivos
        scan_layout = QHBoxLayout()
        self.btn_scan = QPushButton(" Escanear / Actualizar Índice del Disco")
        self.btn_scan.setIcon(QIcon(os.path.join(icons_dir, 'search.svg')))
        self.btn_scan.setStyleSheet("QPushButton { background-color: #20B2AA; color: white; font-weight: bold; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #178b85; }")
        self.btn_scan.clicked.connect(self._on_scan_clicked)
        scan_layout.addWidget(self.btn_scan)

        self.chk_include_files = QCheckBox("Incluir archivos")
        self.chk_include_files.setChecked(False)
        self.chk_include_files.setToolTip("Si está marcado incluye archivos individuales. Si está desmarcado solo indexa carpetas y subcarpetas.")
        self.chk_include_files.setStyleSheet("QCheckBox { font-weight: bold; color: #333; margin-left: 10px; }")
        scan_layout.addWidget(self.chk_include_files)

        scan_layout.addStretch()
        d_layout.addLayout(scan_layout)

        # Árbol de directorios
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Árbol de Directorios Indexado")
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(255, 255, 255, 0.92);
                border: 1px solid #20B2AA;
                border-radius: 6px;
                color: #111111;
                font-size: 12px;
                padding: 4px;
                outline: 0;
                selection-background-color: #b2dfdb;
                selection-color: #004d40;
            }
            QTreeWidget::item {
                padding: 3px 6px;
                border-radius: 4px;
                color: #111111;
            }
            QTreeWidget::item:hover {
                background-color: #e0f2f1;
                color: #004d40;
            }
            QTreeWidget::item:selected {
                background-color: #b2dfdb;
                color: #004d40;
                font-weight: bold;
            }
            QTreeWidget::item:selected:hover {
                background-color: #80cbc4;
                color: #00332c;
            }
            QHeaderView::section {
                background-color: #e0f2f1;
                color: #004d40;
                font-weight: bold;
                border: 1px solid #b2dfdb;
                padding: 4px 8px;
                border-radius: 4px;
            }
        """)
        d_layout.addWidget(self.tree_widget, 1)

        self.stack.addWidget(self.detail_container)
        layout.addWidget(self.stack, 1)

    def _on_scan_clicked(self):
        if not self.current_item: return
        dir_path = QFileDialog.getExistingDirectory(self, "Seleccionar la raíz del disco a escanear")
        if dir_path:
            include_files = self.chk_include_files.isChecked()
            self.scan_requested.emit(self.current_item, dir_path, include_files)

    def _on_show_chart(self):
        if not self.current_item or not self.current_item.get('storage_stats'):
            return
        dlg = DiskUsageChartDialog(self, item=self.current_item)
        dlg.exec()

    def set_item(self, item: dict):
        self.current_item = item
        if not item:
            self.stack.setCurrentIndex(0)
            return

        self.stack.setCurrentIndex(1)
        self.lbl_title.setText(f"Disco: {item.get('name')}")
        
        disk_num = item.get('disk_number', '')
        prefix = f"[{disk_num}] " if disk_num else ""
        txt = f"<h3 style='margin:0; color:#8B0000;'>{prefix}{item.get('name')}</h3>"
        txt += f"<b>Tipo:</b> {item.get('type')} | <b>Tecnología:</b> {item.get('tech')}<br>"
        txt += f"<b>Capacidad Declarada:</b> {item.get('capacity_gb', 0)} GB<br>"
        txt += f"<b>Categoría:</b> {item.get('category')}<br>"

        stats = item.get('storage_stats')
        if stats:
            total_b = float(stats.get('total_bytes', 0))
            used_b = float(stats.get('used_bytes', 0))
            free_b = float(stats.get('free_bytes', 0))
            tot_files = stats.get('total_files', 0)
            tot_folders = stats.get('total_folders', 0)
            pct = (used_b / total_b * 100.0) if total_b > 0 else 0.0
            txt += f"<hr style='border: 0; border-top: 1px solid #CCC; margin: 6px 0;'>"
            txt += f"<b>Capacidad de la Unidad:</b> {format_size(total_b)}<br>"
            txt += f"<b>Espacio Ocupado:</b> <span style='color: #8B0000; font-weight: bold;'>{format_size(used_b)}</span> ({pct:.1f}%) | <b>Espacio Libre:</b> <span style='color: #2E7D32; font-weight: bold;'>{format_size(free_b)}</span><br>"
            if tot_files > 0 or tot_folders > 0:
                txt += f"<b>Total en Disco:</b> <span style='color: #004d40; font-weight: bold;'>{tot_files:,}</span> archivos en <span style='color: #004d40; font-weight: bold;'>{tot_folders:,}</span> carpetas<br>".replace(',', '.')
            if stats.get('scanned_path'):
                txt += f"<span style='color: #555; font-size: 11px;'>Último escaneo: {stats.get('scanned_path')} ({'Con archivos' if stats.get('include_files') else 'Solo carpetas'})</span>"
            self.btn_chart.setVisible(True)
        else:
            self.btn_chart.setVisible(False)

        self.lbl_detail_text.setText(txt)

        # Poblar el árbol
        self.tree_widget.clear()
        tree_data = item.get('scanned_tree', {})
        if tree_data:
            self._build_tree(tree_data, self.tree_widget)
            self.tree_widget.expandToDepth(0)

    def _build_tree(self, node_data: dict, parent_item):
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        folder_icon = QIcon(os.path.join(icons_dir, 'open_folder_dark.svg'))
        file_icon = QIcon(os.path.join(icons_dir, 'document_dark.svg'))

        for key, children in node_data.items():
            if str(key).startswith('__'):
                continue
            is_file = (children == "__file__")
            if is_file:
                item = QTreeWidgetItem([key])
                item.setIcon(0, file_icon)
            else:
                f_count = children.get('__files_count__') if isinstance(children, dict) else None
                if f_count is not None:
                    txt = f"{key}  ({f_count} archivo)" if f_count == 1 else f"{key}  ({f_count} archivos)"
                else:
                    txt = key
                item = QTreeWidgetItem([txt])
                item.setIcon(0, folder_icon)

            if isinstance(parent_item, QTreeWidget):
                parent_item.addTopLevelItem(item)
            else:
                parent_item.addChild(item)
            
            if isinstance(children, dict):
                self._build_tree(children, item)


class RespaldosPlugin(PluginBase):
    def get_id(self) -> str: return "respaldos"
    def get_name(self) -> str: return "Respaldos"
    def get_icon(self) -> str: return "respaldos.svg"
    def get_tab_color(self) -> str: return "#20B2AA"
    def get_order(self) -> int: return 12

    def __init__(self):
        super().__init__()
        self._data = {'discos': [], 'config': {}}
        self._current_search = ""

        # Inicializar vistas
        self.sidebar_widget = RespaldosSidebar()
        self.left_view = RespaldosLeftView()
        self.right_view = RespaldosRightView()

        self.sidebar_widget.add_disk_clicked.connect(self._on_add_disk)
        self.sidebar_widget.search_changed.connect(self._on_search)
        self.sidebar_widget.settings_clicked.connect(self._on_settings)
        self.sidebar_widget.sort_changed.connect(self._on_sort_changed)

        self.left_view.item_selected.connect(self._on_item_selected)
        self.left_view.edit_item_requested.connect(self._on_edit_disk)

        self.right_view.scan_requested.connect(self._on_scan_disk)

    def create_sidebar_widget(self) -> QWidget:
        return self.sidebar_widget

    def create_left_page(self) -> QWidget:
        return self.left_view

    def create_right_page(self) -> QWidget:
        return self.right_view

    def on_activate(self):
        super().on_activate()
        self._refresh_ui()
    
    def load_data(self, agenda_path: str):
        self.set_agenda_path(agenda_path)
        data_path = DataStore.get_plugin_data_path(agenda_path, 'respaldos')
        if os.path.exists(data_path):
            with open(data_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        else:
            self._data = {'discos': [], 'config': {
                'categories': ["Películas", "Series", "Anime", "Música", "Respaldos PCs", "Videos Descargados", "General"],
                'types': ["SATA 2.5\"", "SATA 3.5\"", "NVMe M.2", "SATA M.2", "IDE", "USB Externo", "Otro"]
            }}
        
        self._refresh_ui()

    def save_data(self, agenda_path: str):
        data_path = DataStore.get_plugin_data_path(agenda_path, 'respaldos')
        
        # Ensure dir exists
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
        
    def _refresh_ui(self):
        sort_order = self._data.get('config', {}).get('sort_order', 'alpha_asc')
        if self.sidebar_widget:
            self.sidebar_widget.set_sort_order(sort_order)
        if self.left_view:
            self.left_view.set_data(self._data.get('discos', []), self._current_search, sort_order)

    def _on_sort_changed(self, order_str: str):
        if 'config' not in self._data: self._data['config'] = {}
        self._data['config']['sort_order'] = order_str
        self._is_modified = True
        self._refresh_ui()

    def _on_search(self, text: str):
        self._current_search = text
        self._refresh_ui()

    def _on_item_selected(self, item: dict):
        self.right_view.set_item(item)

    def _on_add_disk(self):
        config = self._data.get('config', {})
        dlg = DiskDialog(self.sidebar_widget, item=None, categories=config.get('categories', []), types=config.get('types', []))
        if dlg.exec():
            new_item = dlg.get_data()
            new_item['id'] = str(uuid.uuid4())
            new_item['scanned_tree'] = {}
            if 'discos' not in self._data: self._data['discos'] = []
            self._data['discos'].append(new_item)
            self._is_modified = True
            self._refresh_ui()

    def _on_edit_disk(self, item: dict):
        config = self._data.get('config', {})
        dlg = DiskDialog(self.sidebar_widget, item=item, categories=config.get('categories', []), types=config.get('types', []))
        if dlg.exec():
            updated_item = dlg.get_data()
            for i, d in enumerate(self._data['discos']):
                if d.get('id') == item.get('id'):
                    updated_item['scanned_tree'] = d.get('scanned_tree', {}) # Preserve tree
                    updated_item['storage_stats'] = d.get('storage_stats', {}) # Preserve stats
                    self._data['discos'][i] = updated_item
                    break
            self._is_modified = True
            self._refresh_ui()
            self.right_view.set_item(updated_item)

    def _on_settings(self):
        config = self._data.get('config', {})
        dlg = RespaldosSettingsDialog(self.sidebar_widget, config=config.copy())
        if dlg.exec():
            self._data['config'] = dlg.get_config()
            self._is_modified = True
            QMessageBox.information(self.sidebar_widget, "Configuración", "Configuración de respaldos guardada correctamente.")

    def _on_scan_disk(self, item: dict, dir_path: str, include_files: bool = False):
        msg = f"Se iniciará el escaneo de {dir_path}.\n\n"
        if include_files:
            msg += "Modo: Incluir archivos (puede tomar un poco más de tiempo según la cantidad de archivos)."
        else:
            msg += "Modo: Solo carpetas y subdirectorios."
        QMessageBox.information(self.sidebar_widget, "Escaneando", msg)
        
        # Calcular espacio total, usado y libre del disco/partición
        total_b, used_b, free_b = 0, 0, 0
        try:
            total_b, used_b, free_b = shutil.disk_usage(dir_path)
        except Exception:
            pass

        # Medir tamaño de las carpetas y archivos directos de la raíz
        root_items = []
        try:
            for entry in os.scandir(dir_path):
                size = 0
                is_dir = False
                try:
                    if entry.is_dir(follow_symlinks=False):
                        is_dir = True
                        for root, _, files in os.walk(entry.path):
                            for f in files:
                                try:
                                    size += os.path.getsize(os.path.join(root, f))
                                except (OSError, PermissionError):
                                    pass
                    elif entry.is_file(follow_symlinks=False):
                        size = entry.stat().st_size
                    root_items.append({'name': entry.name, 'size': size, 'is_dir': is_dir})
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            pass

        root_items.sort(key=lambda x: x['size'], reverse=True)

        total_disk_files = 0
        total_disk_folders = 0
        tree_dict = {}
        
        def get_or_create_node(tree: dict, path_parts: list) -> dict:
            current = tree
            for part in path_parts:
                if part not in current or not isinstance(current[part], dict):
                    current[part] = {}
                current = current[part]
            return current
        
        try:
            for root, dirs, files in os.walk(dir_path):
                total_disk_files += len(files)
                total_disk_folders += len(dirs)

                rel_path = os.path.relpath(root, dir_path)
                if rel_path == '.':
                    parts = [os.path.basename(dir_path) or dir_path]
                else:
                    parts = [os.path.basename(dir_path) or dir_path] + rel_path.split(os.sep)
                
                node = get_or_create_node(tree_dict, parts)
                node['__files_count__'] = len(files)

                if include_files:
                    for f in files:
                        node[f] = "__file__"
                
            storage_stats = {
                'total_bytes': total_b,
                'used_bytes': used_b,
                'free_bytes': free_b,
                'total_files': total_disk_files,
                'total_folders': total_disk_folders,
                'root_items': root_items,
                'scanned_path': dir_path,
                'include_files': include_files
            }

            for i, d in enumerate(self._data['discos']):
                if d.get('id') == item.get('id'):
                    self._data['discos'][i]['scanned_tree'] = tree_dict
                    self._data['discos'][i]['storage_stats'] = storage_stats
                    self._is_modified = True
                    self.right_view.set_item(self._data['discos'][i])
                    break
                    
            QMessageBox.information(self.sidebar_widget, "Completado", f"Índice generado correctamente.\nTotal de archivos contabilizados: {total_disk_files:,}".replace(',', '.'))
        except Exception as e:
            QMessageBox.warning(self.sidebar_widget, "Error", f"Ocurrió un error al escanear: {str(e)}")

