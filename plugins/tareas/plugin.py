# =============================================================================
# Vito Organizer v2.2 - Tareas Plugin
# =============================================================================

import os
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate, QRectF
from PyQt6.QtGui import QFont, QColor, QIcon, QPainter, QPen, QBrush, QPainterPath
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QCheckBox, QProgressBar, QScrollArea, QFrame, QButtonGroup
)

from plugins.plugin_base import PluginBase
from data.data_store import DataStore
from plugins.tareas.dialogs import TaskDialog, TaskListDialog, TaskSettingsDialog


class CustomCheckBox(QCheckBox):
    """Checkbox personalizado dibujado con QPainter con visto bueno verde perfecto."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(3, 3, 16, 16)
        
        if self.isChecked():
            painter.setPen(QPen(QColor("#2e7d32"), 2))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawRoundedRect(rect, 3, 3)
            
            pen_check = QPen(QColor("#2e7d32"), 2.5)
            pen_check.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen_check.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen_check)
            
            path = QPainterPath()
            path.moveTo(rect.left() + 4, rect.top() + 8)
            path.lineTo(rect.left() + 7, rect.top() + 11.5)
            path.lineTo(rect.right() - 3.5, rect.top() + 4.5)
            painter.drawPath(path)
        else:
            painter.setPen(QPen(QColor("#444444"), 1.5))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawRoundedRect(rect, 3, 3)


class TaskItemWidget(QFrame):
    """Widget para una tarea individual con checkbox, título, prioridad y acciones."""
    
    status_changed = pyqtSignal(dict, bool)
    edit_requested = pyqtSignal(dict)

    def __init__(self, task: dict, parent=None):
        super().__init__(parent)
        self.task = task
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.6);
                border: 1px solid #D0C070;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: rgba(255, 255, 255, 0.9);
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        # Checkbox vector de alta precisión
        self.checkbox = CustomCheckBox()
        self.checkbox.setChecked(self.task.get('completed', False))
        self.checkbox.toggled.connect(self._on_toggled)
        layout.addWidget(self.checkbox)

        # Contenedor vertical de textos
        text_container = QWidget()
        text_container.setStyleSheet("border: none; background: transparent;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.title_label = QLabel(self.task.get('title', ''))
        self.title_label.setWordWrap(True)
        self.title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        text_layout.addWidget(self.title_label)

        self.date_label = QLabel()
        text_layout.addWidget(self.date_label)

        layout.addWidget(text_container, 1)

        # Prioridad Badge
        prio = self.task.get('priority', 'Media')
        prio_colors = {'Alta': '#d32f2f', 'Media': '#f57c00', 'Baja': '#388e3c'}
        prio_label = QLabel(f"● {prio}")
        prio_label.setStyleSheet(f"color: {prio_colors.get(prio, '#388e3c')}; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        layout.addWidget(prio_label)

        # Botón Editar
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        btn_edit = QPushButton()
        btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil_dark.svg')))
        btn_edit.setFixedSize(26, 26)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: rgba(0,0,0,0.1); border-radius: 4px; }")
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.task))
        layout.addWidget(btn_edit)

        self._update_title_style()

    def _on_toggled(self, checked: bool):
        self.task['completed'] = checked
        if checked:
            self.task['completed_date'] = QDate.currentDate().toString("dd/MM/yyyy")
        else:
            self.task['completed_date'] = ""
        self._update_title_style()
        self.status_changed.emit(self.task, checked)

    def _update_title_style(self):
        if self.checkbox.isChecked():
            self.title_label.setStyleSheet("color: #888888; text-decoration: line-through; font-size: 13px; border: none; background: transparent;")
            c_date = self.task.get('completed_date') or QDate.currentDate().toString("dd/MM/yyyy")
            self.date_label.setText(f"✓ Finalizada el {c_date}")
            self.date_label.setStyleSheet("color: #2e7d32; font-size: 11px; font-weight: bold; border: none; background: transparent;")
        else:
            self.title_label.setStyleSheet("color: #111111; font-size: 13px; font-weight: bold; border: none; background: transparent;")
            has_due = self.task.get('has_due_date', bool(self.task.get('due_date')))
            if has_due and self.task.get('due_date'):
                try:
                    q_d = QDate.fromString(self.task.get('due_date'), "yyyy-MM-dd")
                    d_str = q_d.toString("dd/MM/yyyy")
                except:
                    d_str = self.task.get('due_date')
                self.date_label.setText(f"📅 Límite: {d_str}")
                self.date_label.setStyleSheet("color: #555555; font-size: 11px; border: none; background: transparent;")
            else:
                self.date_label.setText("♾️ Sin fecha límite")
                self.date_label.setStyleSheet("color: #777777; font-size: 11px; font-style: italic; border: none; background: transparent;")


class TaskListGroupWidget(QWidget):
    """Widget de Lista de Tareas con cabecera desplegable, barra de progreso y tareas internas."""
    
    task_status_changed = pyqtSignal(dict, bool)
    edit_task_requested = pyqtSignal(dict)
    edit_list_requested = pyqtSignal(dict)
    add_task_to_list_requested = pyqtSignal(str)

    def __init__(self, list_dict: dict, tasks: list, parent=None):
        super().__init__(parent)
        self.list_dict = list_dict
        self.tasks = tasks
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 8)
        main_layout.setSpacing(4)

        # Cabecera de la Lista
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #EAE6D0;
                border: 1px solid #A0A0A0;
                border-radius: 6px;
            }
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 6, 10, 6)
        header_layout.setSpacing(10)

        # Botón desplegable
        self.btn_toggle = QPushButton("▼" if not self.list_dict.get('collapsed', False) else "▶")
        self.btn_toggle.setFixedSize(24, 24)
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.setStyleSheet("border: none; background: transparent; font-weight: bold; color: #333333;")
        self.btn_toggle.clicked.connect(self._toggle_collapse)
        header_layout.addWidget(self.btn_toggle)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # Título de Lista
        folder_img = f"<img src='{os.path.join(icons_dir, 'open_folder_dark.svg')}' width='15' height='15'>"
        title_label = QLabel(f"{folder_img} <b>{self.list_dict.get('title', '')}</b>")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #111111; border: none; background: transparent;")
        header_layout.addWidget(title_label, 1)

        # Barra de Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #B0B0B0;
                border-radius: 4px;
                text-align: center;
                font-size: 10px;
                font-weight: bold;
                color: #111111;
                background-color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #2e7d32;
                border-radius: 3px;
            }
        """)
        header_layout.addWidget(self.progress_bar)

        # Ratio count (ej: 2/5)
        self.ratio_label = QLabel("0/0")
        self.ratio_label.setStyleSheet("font-size: 11px; color: #555555; font-weight: bold; border: none; background: transparent;")
        header_layout.addWidget(self.ratio_label)

        # Botón Agregar Tarea a esta lista
        btn_add = QPushButton()
        btn_add.setIcon(QIcon(os.path.join(icons_dir, 'add_dark.svg')))
        btn_add.setToolTip("Agregar tarea a esta lista")
        btn_add.setFixedSize(26, 26)
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: rgba(0,0,0,0.1); border-radius: 4px; }")
        btn_add.clicked.connect(lambda: self.add_task_to_list_requested.emit(self.list_dict.get('id')))
        header_layout.addWidget(btn_add)

        # Botón Editar Lista
        btn_edit = QPushButton()
        btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'settings_dark.svg')))
        btn_edit.setToolTip("Configurar lista")
        btn_edit.setFixedSize(26, 26)
        btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_edit.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background-color: rgba(0,0,0,0.1); border-radius: 4px; }")
        btn_edit.clicked.connect(lambda: self.edit_list_requested.emit(self.list_dict))
        header_layout.addWidget(btn_edit)

        main_layout.addWidget(header_frame)

        # Contenedor desplegable de Tareas
        self.content_container = QWidget()
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(16, 2, 0, 4)
        self.content_layout.setSpacing(4)

        for t in self.tasks:
            item = TaskItemWidget(t)
            item.status_changed.connect(self._on_item_status_changed)
            item.edit_requested.connect(self.edit_task_requested.emit)
            self.content_layout.addWidget(item)

        main_layout.addWidget(self.content_container)

        # Aplicar estado inicial de colapso
        if self.list_dict.get('collapsed', False):
            self.content_container.hide()

        self.update_progress()

    def _on_item_status_changed(self, task: dict, checked: bool):
        self.update_progress()
        self.task_status_changed.emit(task, checked)

    def _toggle_collapse(self):
        is_collapsed = self.content_container.isVisible()
        self.content_container.setVisible(not is_collapsed)
        self.list_dict['collapsed'] = is_collapsed
        self.btn_toggle.setText("▶" if is_collapsed else "▼")

    def update_progress(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get('completed', False))
        pct = int((completed / total * 100)) if total > 0 else 0
        self.progress_bar.setValue(pct)
        self.ratio_label.setText(f"{completed}/{total}")


class TasksLeftView(QWidget):
    """Vista de la página izquierda (Cuaderno de Tareas)."""
    
    task_status_changed = pyqtSignal(dict, bool)
    edit_task_requested = pyqtSignal(dict)
    edit_list_requested = pyqtSignal(dict)
    add_task_to_list_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.lists = []
        self.tasks = []
        self.filter_mode = 'all' # 'all', 'standalone', 'lists', 'completed'
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 15, 15, 15)
        layout.setSpacing(10)

        # Cabecera 3D tipo libro
        hdr_frame = QFrame()
        hdr_frame.setFixedHeight(32)
        hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        task_icon_path = os.path.join(icons_dir, 'tasks_dark.svg')
        title = QLabel(f"<img src='{task_icon_path}' width='14' height='14'> Gestor de Tareas y Proyectos")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(title)
        layout.addWidget(hdr_frame)

        # Área scrollable de listas y tareas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)

        scroll.setWidget(self.scroll_content)
        layout.addWidget(scroll, 1)

    def set_data(self, lists: list, tasks: list, filter_mode: str = 'all', page_part: str = 'all'):
        self.lists = lists
        self.tasks = tasks
        self.filter_mode = filter_mode
        self.page_part = page_part
        self._refresh()

    def _refresh(self):
        # Limpiar layout
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

        # 1. Tareas Sueltas
        standalone_tasks = [t for t in self.tasks if not t.get('list_id')]
        if self.page_part in ('all', 'left'):
            if self.filter_mode in ('all', 'standalone') and standalone_tasks:
                st_group = QFrame()
                st_group.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.4); border: 1px dashed #A0A0A0; border-radius: 6px; }")
                st_layout = QVBoxLayout(st_group)
                st_layout.setContentsMargins(10, 8, 10, 8)
                st_layout.setSpacing(6)

                icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
                pin_img = f"<img src='{os.path.join(icons_dir, 'pushpin.svg')}' width='14' height='14'>"
                lbl = QLabel(f"{pin_img} Tareas Sueltas")
                lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #333333; border: none; background: transparent;")
                st_layout.addWidget(lbl)

                for t in standalone_tasks:
                    if self.filter_mode == 'completed' and not t.get('completed'):
                        continue
                    item = TaskItemWidget(t)
                    item.status_changed.connect(self.task_status_changed.emit)
                    item.edit_requested.connect(self.edit_task_requested.emit)
                    st_layout.addWidget(item)

                self.scroll_layout.addWidget(st_group)

        # 2. Listas / Proyectos
        if self.filter_mode in ('all', 'lists'):
            target_lists = self.lists
            if self.page_part == 'left':
                mid = (len(self.lists) + 1) // 2
                target_lists = self.lists[:mid]
            elif self.page_part == 'right':
                mid = (len(self.lists) + 1) // 2
                target_lists = self.lists[mid:]

            for l in target_lists:
                l_tasks = [t for t in self.tasks if t.get('list_id') == l.get('id')]
                grp_widget = TaskListGroupWidget(l, l_tasks)
                grp_widget.task_status_changed.connect(self.task_status_changed.emit)
                grp_widget.edit_task_requested.connect(self.edit_task_requested.emit)
                grp_widget.edit_list_requested.connect(self.edit_list_requested.emit)
                grp_widget.add_task_to_list_requested.connect(self.add_task_to_list_requested.emit)
                self.scroll_layout.addWidget(grp_widget)

        self.scroll_layout.addStretch()


class TasksRightView(QWidget):
    """Vista de la página derecha (Estadísticas y Detalle)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.lists = []
        self.tasks = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 25, 15)
        layout.setSpacing(14)

        # Cabecera 3D
        hdr_frame = QFrame()
        hdr_frame.setFixedHeight(32)
        hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        title = QLabel("Resumen y Estadísticas de Progreso")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(title)
        layout.addWidget(hdr_frame)

        # Panel de Resumen Estadístico
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.7); border: 1px solid #D0C070; border-radius: 8px; }")
        stats_layout = QVBoxLayout(stats_frame)
        stats_layout.setContentsMargins(16, 16, 16, 16)
        stats_layout.setSpacing(12)

        self.lbl_total = QLabel("Total Tareas: 0")
        self.lbl_completed = QLabel("Tareas Completadas: 0")
        self.lbl_pending = QLabel("Tareas Pendientes: 0")
        self.lbl_lists = QLabel("Listas / Proyectos Activos: 0")

        lbl_style = "font-size: 13px; font-weight: bold; color: #222222; border: none; background: transparent;"
        for l in (self.lbl_total, self.lbl_completed, self.lbl_pending, self.lbl_lists):
            l.setStyleSheet(lbl_style)
            stats_layout.addWidget(l)

        # Barra de progreso global
        stats_layout.addWidget(QLabel("<b style='color:#111111; font-size:13px;'>Progreso Global:</b>", styleSheet="border:none; background:transparent;"))
        self.global_progress = QProgressBar()
        self.global_progress.setFixedHeight(20)
        self.global_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #B0B0B0;
                border-radius: 6px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                color: #ffffff;
                background-color: #ffffff;
            }
            QProgressBar::chunk {
                background-color: #1b5e20;
                border-radius: 5px;
            }
        """)
        stats_layout.addWidget(self.global_progress)

        layout.addWidget(stats_frame)
        layout.addStretch()

    def set_data(self, lists: list, tasks: list):
        self.lists = lists
        self.tasks = tasks
        self._update_stats()

    def _update_stats(self):
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks if t.get('completed', False))
        pending = total - completed
        pct = int((completed / total * 100)) if total > 0 else 0

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        task_img = f"<img src='{os.path.join(icons_dir, 'tasks_dark.svg')}' width='14' height='14'>"
        check_img = f"<img src='{os.path.join(icons_dir, 'check_dark.svg')}' width='14' height='14'>"
        folder_img = f"<img src='{os.path.join(icons_dir, 'open_folder_dark.svg')}' width='14' height='14'>"

        self.lbl_total.setText(f"{task_img} Total Tareas: {total}")
        self.lbl_completed.setText(f"{check_img} Tareas Completadas: {completed}")
        self.lbl_pending.setText(f"Tareas Pendientes: {pending}")
        self.lbl_lists.setText(f"{folder_img} Listas / Proyectos Activos: {len(self.lists)}")
        self.global_progress.setValue(pct)


class TareasSidebar(QWidget):
    """Barra lateral para la sección de Tareas."""
    
    filter_changed = pyqtSignal(str)
    add_task_clicked = pyqtSignal()
    add_list_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(12)

        # 1. Acciones principales
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        btn_add_task = QPushButton(" Nueva Tarea")
        btn_add_task.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        btn_add_list = QPushButton(" Nueva Lista")
        btn_add_list.setIcon(QIcon(os.path.join(icons_dir, 'open_folder.svg')))

        btn_style = """
            QPushButton { text-align: left; padding: 8px 12px; border-radius: 6px; background-color: rgba(255, 255, 255, 0.08); color: #ffffff; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """
        btn_add_task.setStyleSheet(btn_style)
        btn_add_list.setStyleSheet(btn_style)

        btn_add_task.clicked.connect(self.add_task_clicked.emit)
        btn_add_list.clicked.connect(self.add_list_clicked.emit)

        actions_layout.addWidget(btn_add_task)
        actions_layout.addWidget(btn_add_list)
        layout.addLayout(actions_layout)

        # Separador
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: rgba(255, 255, 255, 0.2);")
        layout.addWidget(line)

        # 2. Filtros
        lbl_filter = QLabel("Filtros")
        lbl_filter.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_filter)

        filters_layout = QVBoxLayout()
        filters_layout.setSpacing(4)

        self.filter_group = QButtonGroup(self)
        filters = [
            ('all', ' Todas las tareas', 'tasks.svg'),
            ('standalone', ' Tareas Sueltas', 'tasks.svg'),
            ('lists', ' Listas y Proyectos', 'open_folder.svg')
        ]

        for i, (fid, fname, ficon) in enumerate(filters):
            btn = QPushButton(fname)
            btn.setIcon(QIcon(os.path.join(icons_dir, ficon)))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 6px 10px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #f9e2af; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)
            btn.clicked.connect(lambda checked, f=fid: self.filter_changed.emit(f))
            self.filter_group.addButton(btn, i)
            filters_layout.addWidget(btn)
            if fid == 'all': btn.setChecked(True)

        layout.addLayout(filters_layout)
        layout.addStretch()

        # 3. Panel de Estadísticas en Sidebar (opcional)
        self.stats_frame = QFrame()
        self.stats_frame.setVisible(False)
        self.stats_frame.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15); border-radius: 6px; }")
        s_layout = QVBoxLayout(self.stats_frame)
        s_layout.setContentsMargins(8, 8, 8, 8)
        s_layout.setSpacing(4)

        lbl_s_title = QLabel("Estadísticas")
        lbl_s_title.setStyleSheet("color: #f9e2af; font-weight: bold; font-size: 11px; border: none; background: transparent;")
        s_layout.addWidget(lbl_s_title)

        self.lbl_s_total = QLabel("Total: 0")
        self.lbl_s_completed = QLabel("Completadas: 0")
        self.lbl_s_pending = QLabel("Pendientes: 0")
        for l in (self.lbl_s_total, self.lbl_s_completed, self.lbl_s_pending):
            l.setStyleSheet("color: #cdd6f4; font-size: 11px; border: none; background: transparent;")
            s_layout.addWidget(l)

        self.s_progress = QProgressBar()
        self.s_progress.setFixedHeight(12)
        self.s_progress.setStyleSheet("""
            QProgressBar { border: none; border-radius: 3px; text-align: center; font-size: 9px; color: #ffffff; background-color: rgba(255,255,255,0.1); }
            QProgressBar::chunk { background-color: #2e7d32; border-radius: 3px; }
        """)
        s_layout.addWidget(self.s_progress)
        layout.addWidget(self.stats_frame)

        # 4. Botón de engranaje inferior izquierdo para configuración de tareas
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Tareas")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def update_stats_display(self, lists: list, tasks: list, visible: bool):
        self.stats_frame.setVisible(visible)
        if visible:
            total = len(tasks)
            completed = sum(1 for t in tasks if t.get('completed', False))
            pending = total - completed
            pct = int((completed / total * 100)) if total > 0 else 0

            self.lbl_s_total.setText(f"Total: {total}")
            self.lbl_s_completed.setText(f"Completadas: {completed}")
            self.lbl_s_pending.setText(f"Pendientes: {pending}")
            self.s_progress.setValue(pct)


class TareasPlugin(PluginBase):
    """Plugin para la sección de Tareas."""

    trash_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._data = {'lists': [], 'tasks': [], '_trash': []}
        self._trash = []
        self._is_modified = False
        self.current_filter = 'all'

        # Sidebar
        self._sidebar = TareasSidebar()
        self._sidebar.filter_changed.connect(self._on_filter_changed)
        self._sidebar.add_task_clicked.connect(self._on_add_task)
        self._sidebar.add_list_clicked.connect(self._on_add_list)
        self._sidebar.settings_clicked.connect(self._on_show_settings)

        # Pages
        self._left_page = TasksLeftView()
        
        from PyQt6.QtWidgets import QStackedWidget
        self._right_stack = QStackedWidget()
        self._right_stats_page = TasksRightView()
        self._right_task_page = TasksLeftView()
        self._right_stack.addWidget(self._right_stats_page)
        self._right_stack.addWidget(self._right_task_page)

        self._left_page.task_status_changed.connect(self._on_task_status_changed)
        self._left_page.edit_task_requested.connect(self._on_edit_task)
        self._left_page.edit_list_requested.connect(self._on_edit_list)
        self._left_page.add_task_to_list_requested.connect(self._on_add_task_to_list)

        self._right_task_page.task_status_changed.connect(self._on_task_status_changed)
        self._right_task_page.edit_task_requested.connect(self._on_edit_task)
        self._right_task_page.edit_list_requested.connect(self._on_edit_list)
        self._right_task_page.add_task_to_list_requested.connect(self._on_add_task_to_list)

    def _update_views(self):
        lists = self._data.get('lists', [])
        tasks = self._data.get('tasks', [])
        in_sidebar = self._data.get('stats_in_sidebar', False)

        self._sidebar.update_stats_display(lists, tasks, visible=in_sidebar)

        if in_sidebar:
            self._right_stack.setCurrentIndex(1)
            self._left_page.set_data(lists, tasks, self.current_filter, page_part='left')
            self._right_task_page.set_data(lists, tasks, self.current_filter, page_part='right')
        else:
            self._right_stack.setCurrentIndex(0)
            self._left_page.set_data(lists, tasks, self.current_filter, page_part='all')
            self._right_stats_page.set_data(lists, tasks)

    def _on_show_settings(self):
        curr_val = self._data.get('stats_in_sidebar', False)
        dlg = TaskSettingsDialog(stats_in_sidebar=curr_val, parent=self._sidebar)
        if dlg.exec():
            self._data['stats_in_sidebar'] = dlg.stats_in_sidebar
            self._is_modified = True
            self._update_views()

    def _on_filter_changed(self, filter_mode: str):
        self.current_filter = filter_mode
        self._update_views()

    def _on_add_task(self):
        lists = self._data.get('lists', [])
        dlg = TaskDialog(lists=lists, parent=self._sidebar)
        if dlg.exec() and dlg.task_data:
            self._data.setdefault('tasks', []).append(dlg.task_data)
            self._is_modified = True
            self._update_views()

    def _on_add_task_to_list(self, list_id: str):
        lists = self._data.get('lists', [])
        dlg = TaskDialog(lists=lists, selected_list_id=list_id, parent=self._sidebar)
        if dlg.exec() and dlg.task_data:
            self._data.setdefault('tasks', []).append(dlg.task_data)
            self._is_modified = True
            self._update_views()

    def _on_add_list(self):
        dlg = TaskListDialog(parent=self._sidebar)
        if dlg.exec() and dlg.list_data:
            self._data.setdefault('lists', []).append(dlg.list_data)
            self._is_modified = True
            self._update_views()

    def _on_task_status_changed(self, task: dict, checked: bool):
        self._is_modified = True
        self._update_views()

    def _on_edit_task(self, task_dict: dict):
        lists = self._data.get('lists', [])
        dlg = TaskDialog(lists=lists, task_to_edit=task_dict, parent=self._sidebar)
        if dlg.exec():
            tasks = self._data.get('tasks', [])
            if dlg.is_delete:
                if task_dict in tasks:
                    tasks.remove(task_dict)
                    self.move_to_trash(task_dict)
                    self._is_modified = True
                    self._update_views()
                    self.trash_changed.emit()
            elif dlg.task_data:
                idx = tasks.index(task_dict) if task_dict in tasks else -1
                if idx >= 0:
                    tasks[idx] = dlg.task_data
                else:
                    tasks.append(dlg.task_data)
                self._is_modified = True
                self._update_views()

    def _on_edit_list(self, list_dict: dict):
        dlg = TaskListDialog(list_to_edit=list_dict, parent=self._sidebar)
        if dlg.exec():
            lists = self._data.get('lists', [])
            tasks = self._data.get('tasks', [])
            if dlg.is_delete:
                if list_dict in lists:
                    lists.remove(list_dict)
                    self.move_to_trash(list_dict)
                    # Mover también las tareas pertenecientes a esta lista a tareas sueltas o papelera
                    for t in tasks:
                        if t.get('list_id') == list_dict.get('id'):
                            t['list_id'] = None
                    self._is_modified = True
                    self._update_views()
                    self.trash_changed.emit()
            elif dlg.list_data:
                idx = lists.index(list_dict) if list_dict in lists else -1
                if idx >= 0:
                    lists[idx] = dlg.list_data
                else:
                    lists.append(dlg.list_data)
                self._is_modified = True
                self._update_views()

    # --- Papelera ---
    def move_to_trash(self, item: dict):
        self._trash.append(item)

    def get_trash_items(self) -> list:
        return self._trash

    def restore_item(self, index: int):
        if 0 <= index < len(self._trash):
            item = self._trash.pop(index)
            if 'title' in item and 'completed' in item:
                self._data.setdefault('tasks', []).append(item)
            else:
                self._data.setdefault('lists', []).append(item)
            self._is_modified = True
            self._update_views()
            self.trash_changed.emit()

    def delete_permanently(self, index: int):
        if 0 <= index < len(self._trash):
            self._trash.pop(index)
            self._is_modified = True
            self.trash_changed.emit()

    def empty_trash(self):
        if self._trash:
            self._trash.clear()
            self._is_modified = True
            self.trash_changed.emit()

    def get_name(self) -> str: return "Tareas"
    def get_id(self) -> str: return "tareas"
    def get_icon(self) -> str: return "tasks.svg"
    def get_tab_color(self) -> str: return "#228B22"
    def get_order(self) -> int: return 3

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_stack

    def load_data(self, agenda_path: str):
        data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
        loaded = DataStore.load(data_path)
        if loaded:
            self._data.update(loaded)
            self._trash = loaded.get('_trash', [])
        self._update_views()
        self._is_modified = False

    def save_data(self, agenda_path: str):
        if self._is_modified:
            data_path = DataStore.get_plugin_data_path(agenda_path, self.get_id())
            self._data['_trash'] = self._trash
            DataStore.save(data_path, self._data)
            self._is_modified = False
