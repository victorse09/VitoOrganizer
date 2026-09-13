# =============================================================================
# Vito Organizer v2.2 - Planificador Plugin
# Gestor de Proyectos, Carta Gantt y Recursos
# =============================================================================

import os
from typing import Dict, Any, List
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QFont, QColor, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QProgressBar, QScrollArea, QFrame, QButtonGroup, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QStackedWidget
)

from plugins.plugin_base import PluginBase
from data.data_store import DataStore
from plugins.planificador.dialogs import ProjectDialog, StageDialog, ResourceDialog, PlannerSettingsDialog
from plugins.planificador.gantt_widget import GanttWidget


class PlannerLeftView(QWidget):
    """Vista de la página izquierda (Resumen de Proyecto, Etapas o Directorio de Recursos)."""

    add_stage_requested = pyqtSignal()
    edit_stage_requested = pyqtSignal(dict)
    edit_resource_requested = pyqtSignal(dict)
    edit_project_requested = pyqtSignal(dict)
    exit_panoramic_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.project = None
        self.stages = []
        self.resources = []
        self.view_mode = 'gantt' # 'gantt', 'resources', 'stages'
        self.is_panoramic = False
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
        
        self.lbl_hdr_title = QLabel("Gestión de Proyectos")
        self.lbl_hdr_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(self.lbl_hdr_title, 1)

        self.btn_edit_proj = QPushButton("Configurar Proyecto")
        self.btn_edit_proj.setStyleSheet("QPushButton { border: none; background: transparent; font-weight: bold; color: #333333; } QPushButton:hover { background-color: rgba(0,0,0,0.1); border-radius: 4px; }")
        self.btn_edit_proj.clicked.connect(lambda: self.edit_project_requested.emit(self.project) if self.project else None)
        hdr_layout.addWidget(self.btn_edit_proj)
        layout.addWidget(self.hdr_frame)

        # Stack para alternar entre vista normal y Gantt izquierdo
        from PyQt6.QtWidgets import QStackedWidget
        self.stack = QStackedWidget()

        # 0. Contenido normal
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(10)
        scroll.setWidget(self.scroll_content)
        self.stack.addWidget(scroll)

        # 1. Gantt Izquierdo (Modo Panorámico)
        self.gantt_container = QWidget()
        gantt_layout = QVBoxLayout(self.gantt_container)
        gantt_layout.setContentsMargins(0, 0, 0, 0)
        gantt_layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.btn_exit_pano = QPushButton(" Salir del Modo Panorámico (Página Única)")
        self.btn_exit_pano.setIcon(QIcon(os.path.join(icons_dir, 'panoramic.svg')))
        self.btn_exit_pano.setStyleSheet("""
            QPushButton { border: 1px solid #A0A0A0; background: rgba(255,255,255,0.8); font-weight: bold; color: #333333; border-radius: 4px; padding: 4px 8px; font-size: 11px; }
            QPushButton:hover { background-color: rgba(0,0,0,0.08); }
        """)
        self.btn_exit_pano.clicked.connect(self.exit_panoramic_requested.emit)
        self.btn_exit_pano.hide()
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_exit_pano)
        gantt_layout.addLayout(btn_layout)

        self.left_gantt = GanttWidget(side='left')
        gantt_layout.addWidget(self.left_gantt, 1)

        self.stack.addWidget(self.gantt_container)

        layout.addWidget(self.stack, 1)

    def set_data(self, project: dict, stages: list, resources: list, view_mode: str = 'gantt', is_panoramic: bool = False):
        self.project = project
        self.stages = stages
        self.resources = resources
        self.view_mode = view_mode
        self.is_panoramic = is_panoramic
        
        if is_panoramic and view_mode == 'gantt':
            self.stack.setCurrentIndex(1)
            self.left_gantt.set_data(project, stages)
        else:
            self.stack.setCurrentIndex(0)
            self._refresh()

    def _refresh(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child:
                w = child.widget()
                if w:
                    w.setParent(None)
                    w.deleteLater()

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        team_img = f"<img src='{os.path.join(icons_dir, 'team.svg')}' width='15' height='15'>"
        planner_img = f"<img src='{os.path.join(icons_dir, 'planner.svg')}' width='15' height='15'>"
        stages_img = f"<img src='{os.path.join(icons_dir, 'stages.svg')}' width='15' height='15'>"

        if self.view_mode == 'resources':
            self.lbl_hdr_title.setText(f"{team_img} Directorio de Recursos y Equipos")
            self.btn_edit_proj.setVisible(False)
            
            if not self.resources:
                lbl_empty = QLabel("No hay recursos registrados. Presiona 'Nuevo Recurso' en la barra lateral.")
                lbl_empty.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
                lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.scroll_layout.addWidget(lbl_empty)
            else:
                for r in self.resources:
                    card = QFrame()
                    card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.7); border: 1px solid #D0C070; border-radius: 6px; }")
                    c_layout = QHBoxLayout(card)
                    c_layout.setContentsMargins(10, 8, 10, 8)
                    
                    lbl_info = QLabel(f"{team_img} <b>{r.get('name')}</b> ({r.get('role', 'Sin rol')})<br><span style='color:#555; font-size:11px;'>{r.get('details', '')}</span>")
                    lbl_info.setStyleSheet("border: none; background: transparent; color: #111111;")
                    c_layout.addWidget(lbl_info, 1)

                    btn_edit = QPushButton("Editar")
                    btn_edit.setIcon(QIcon(os.path.join(icons_dir, 'pencil.svg')))
                    btn_edit.setFixedSize(65, 26)
                    btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_edit.setStyleSheet("border: 1px solid #CCC; background: #F0F0F0; border-radius: 4px; font-size: 11px; font-weight: bold; color: #333;")
                    btn_edit.clicked.connect(lambda checked, res=r: self.edit_resource_requested.emit(res))
                    c_layout.addWidget(btn_edit)

                    self.scroll_layout.addWidget(card)

        else:
            self.btn_edit_proj.setVisible(True)
            if not self.project:
                self.lbl_hdr_title.setText("Selección de Proyecto")
                lbl_empty = QLabel("No hay proyecto activo. Selecciona o crea uno en la barra lateral.")
                lbl_empty.setStyleSheet("color: #666666; font-style: italic; padding: 20px;")
                lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.scroll_layout.addWidget(lbl_empty)
                return

            self.lbl_hdr_title.setText(f"{planner_img} <b>{self.project.get('title')}</b>")

            # Tarjeta resumen proyecto
            p_card = QFrame()
            p_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.7); border: 1px solid #D0C070; border-radius: 6px; }")
            pc_layout = QVBoxLayout(p_card)
            pc_layout.setContentsMargins(12, 10, 12, 10)
            
            lbl_desc = QLabel(f"<b>Estado:</b> {self.project.get('status')} | <b>Inicio:</b> {self.project.get('start_date')} | <b>Término:</b> {self.project.get('end_date')}<br><span style='color:#444;'>{self.project.get('description', '')}</span>")
            lbl_desc.setStyleSheet("border: none; background: transparent; color: #111111; font-size: 12px;")
            pc_layout.addWidget(lbl_desc)
            self.scroll_layout.addWidget(p_card)

            # Sección Etapas / Fases
            hdr_stages = QHBoxLayout()
            lbl_st_title = QLabel(f"{stages_img} Control de Etapas y Fases")
            lbl_st_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #111111;")
            hdr_stages.addWidget(lbl_st_title)
            hdr_stages.addStretch()

            btn_add_st = QPushButton(" Agregar Etapa")
            btn_add_st.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
            btn_add_st.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 4px 8px; border-radius: 4px; font-size: 11px; }")
            btn_add_st.clicked.connect(self.add_stage_requested.emit)
            hdr_stages.addWidget(btn_add_st)
            self.scroll_layout.addLayout(hdr_stages)

            if not self.stages:
                lbl_no_st = QLabel("Este proyecto no tiene etapas asignadas.")
                lbl_no_st.setStyleSheet("color: #666666; font-style: italic; padding: 10px;")
                self.scroll_layout.addWidget(lbl_no_st)
            else:
                for st in self.stages:
                    st_card = QFrame()
                    st_card.setStyleSheet("QFrame { background-color: rgba(255,255,255,0.6); border: 1px solid #C0B060; border-radius: 6px; }")
                    st_layout = QHBoxLayout(st_card)
                    st_layout.setContentsMargins(10, 6, 10, 6)
                    
                    pct = st.get('progress', 0)
                    lbl_st_info = QLabel(f"<b>{st.get('name')}</b><br><span style='color:#555; font-size:11px;'>Progreso: {pct}%</span>")
                    lbl_st_info.setStyleSheet("border: none; background: transparent; color: #111111;")
                    st_layout.addWidget(lbl_st_info, 1)

                    btn_edit_st = QPushButton("Editar")
                    btn_edit_st.setIcon(QIcon(os.path.join(icons_dir, 'pencil.svg')))
                    btn_edit_st.setFixedSize(65, 26)
                    btn_edit_st.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_edit_st.setStyleSheet("border: 1px solid #CCC; background: #F0F0F0; border-radius: 4px; font-size: 11px; font-weight: bold; color: #333;")
                    btn_edit_st.clicked.connect(lambda checked, stage=st: self.edit_stage_requested.emit(stage))
                    st_layout.addWidget(btn_edit_st)

                    self.scroll_layout.addWidget(st_card)

        self.scroll_layout.addStretch()


class PlannerRightView(QWidget):
    """Vista de la página derecha (Carta Gantt Visor)."""

    panoramic_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('transparentPage')
        self.setStyleSheet('background: transparent;')
        self.is_panoramic = False
        self.panoramic_mode_type = 'dual_page'  # 'dual_page' o 'single_page'
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 25, 15)
        layout.setSpacing(10)

        # Cabecera 3D
        hdr_frame = QFrame()
        hdr_frame.setFixedHeight(34)
        hdr_frame.setStyleSheet("background-color: #FFFFFF; border: 1px solid #A0A0A0;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        
        title = QLabel("Visor de Cronograma Carta Gantt")
        title.setStyleSheet("font-weight: bold; font-size: 13px; color: #8B0000; border: none; background: transparent;")
        hdr_layout.addWidget(title, 1)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')
        self.btn_panoramic = QPushButton(" Modo Panorámico (Ambas Páginas)")
        self.btn_panoramic.setIcon(QIcon(os.path.join(icons_dir, 'panoramic.svg')))
        self.btn_panoramic.setCheckable(True)
        self.btn_panoramic.setToolTip("Estirar la Carta Gantt ocupando ambas páginas de la agenda")
        self.btn_panoramic.setStyleSheet("""
            QPushButton { border: 1px solid #A0A0A0; background: rgba(255,255,255,0.8); font-weight: bold; color: #333333; border-radius: 4px; padding: 3px 8px; font-size: 11px; }
            QPushButton:checked { background-color: #4682B4; color: white; border-color: #2b5b84; }
            QPushButton:hover:!checked { background-color: rgba(0,0,0,0.08); }
        """)
        self.btn_panoramic.clicked.connect(self._on_panoramic_clicked)
        hdr_layout.addWidget(self.btn_panoramic)
        layout.addWidget(hdr_frame)

        self.gantt_widget = GanttWidget()
        layout.addWidget(self.gantt_widget, 1)

    def _on_panoramic_clicked(self, checked: bool):
        self.is_panoramic = checked
        self.panoramic_toggled.emit(checked)

    def update_panoramic_button_text(self, mode_type: str):
        """Actualiza el texto del botón panorámico según el modo configurado."""
        self.panoramic_mode_type = mode_type
        if mode_type == 'single_page':
            self.btn_panoramic.setText(" Modo Panorámico (Página Única)")
            self.btn_panoramic.setToolTip("Mostrar la Carta Gantt en una página única sin encuadernación")
        else:
            self.btn_panoramic.setText(" Modo Panorámico (Ambas Páginas)")
            self.btn_panoramic.setToolTip("Estirar la Carta Gantt ocupando ambas páginas de la agenda")

    def set_data(self, project: dict, stages: list, is_panoramic: bool = False):
        self.gantt_widget.side = 'right' if is_panoramic else 'full'
        self.gantt_widget.set_data(project, stages)


class PlanificadorSidebar(QWidget):
    """Barra lateral para la sección de Planificador."""
    
    view_mode_changed = pyqtSignal(str) # 'gantt', 'resources', 'stages'
    project_changed = pyqtSignal(str)  # project_id
    add_project_clicked = pyqtSignal()
    add_resource_clicked = pyqtSignal()
    settings_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self.projects = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        # 1. Botones de Acción
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(6)

        btn_add_proj = QPushButton(" Nuevo Proyecto")
        btn_add_proj.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))
        btn_add_res = QPushButton(" Nuevo Recurso")
        btn_add_res.setIcon(QIcon(os.path.join(icons_dir, 'add.svg')))

        btn_style = """
            QPushButton { text-align: left; padding: 8px 12px; border-radius: 6px; background-color: rgba(255, 255, 255, 0.08); color: #ffffff; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """
        btn_add_proj.setStyleSheet(btn_style)
        btn_add_res.setStyleSheet(btn_style)

        btn_add_proj.clicked.connect(self.add_project_clicked.emit)
        btn_add_res.clicked.connect(self.add_resource_clicked.emit)

        actions_layout.addWidget(btn_add_proj)
        actions_layout.addWidget(btn_add_res)
        layout.addLayout(actions_layout)

        # 2. Selector de Proyecto
        lbl_proj = QLabel("Proyecto Activo")
        lbl_proj.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px;")
        layout.addWidget(lbl_proj)

        self.proj_combo = QComboBox()
        self.proj_combo.setStyleSheet("QComboBox { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 4px; color: #ffffff; padding: 4px; }")
        self.proj_combo.currentIndexChanged.connect(self._on_proj_combo_changed)
        layout.addWidget(self.proj_combo)

        # 3. Vistas del Planificador
        lbl_views = QLabel("Vistas de Gestión")
        lbl_views.setStyleSheet("color: #a6adc8; font-weight: bold; font-size: 11px; margin-top: 6px;")
        layout.addWidget(lbl_views)

        views_layout = QVBoxLayout()
        views_layout.setSpacing(2)
        self.view_group = QButtonGroup(self)
        
        v_list = [
            ('gantt', ' Proyectos & Gantt', 'planner.svg'),
            ('resources', ' Recursos & Equipos', 'team.svg'),
            ('stages', ' Control de Etapas', 'stages.svg')
        ]
        for i, (vid, vname, vicon) in enumerate(v_list):
            btn = QPushButton(vname)
            btn.setIcon(QIcon(os.path.join(icons_dir, vicon)))
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { text-align: left; padding: 5px 8px; border: none; background: transparent; color: #cdd6f4; border-radius: 4px; font-size: 12px; }
                QPushButton:checked { background-color: #313244; font-weight: bold; color: #f9e2af; }
                QPushButton:hover:!checked { background-color: rgba(255, 255, 255, 0.15); }
            """)
            btn.clicked.connect(lambda checked, v=vid: self.view_mode_changed.emit(v))
            self.view_group.addButton(btn, i)
            views_layout.addWidget(btn)
            if vid == 'gantt': btn.setChecked(True)
        layout.addLayout(views_layout)

        layout.addStretch()

        # 4. Botón de engranaje inferior izquierdo
        bottom_layout = QHBoxLayout()
        self.btn_settings = QPushButton()
        self.btn_settings.setIcon(QIcon(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons', 'settings.svg')))
        self.btn_settings.setFixedSize(32, 32)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.setToolTip("Configurar Planificador")
        self.btn_settings.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 4px; }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.15); }
        """)
        self.btn_settings.clicked.connect(self.settings_clicked.emit)
        bottom_layout.addWidget(self.btn_settings, alignment=Qt.AlignmentFlag.AlignLeft)
        bottom_layout.addStretch()
        layout.addLayout(bottom_layout)

    def set_projects(self, projects: list, active_project_id: str = None):
        self.projects = projects
        self.proj_combo.blockSignals(True)
        self.proj_combo.clear()
        
        if not projects:
            self.proj_combo.addItem("Sin Proyectos", None)
        else:
            sel_idx = 0
            for i, p in enumerate(projects):
                self.proj_combo.addItem(f"Proyecto: {p.get('title')}", p.get('id'))
                if active_project_id and p.get('id') == active_project_id:
                    sel_idx = i
            self.proj_combo.setCurrentIndex(sel_idx)
            
        self.proj_combo.blockSignals(False)

    def _on_proj_combo_changed(self, idx):
        pid = self.proj_combo.currentData()
        if pid:
            self.project_changed.emit(pid)


class PlanificadorPlugin(PluginBase):
    """Plugin para la sección de Planificador."""

    trash_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._data = {'projects': [], 'stages': [], 'resources': [], '_trash': []}
        self._trash = []
        self._is_modified = False
        self.active_project_id = None
        self.active_view_mode = 'gantt'
        self._current_page = 1

        # Sidebar
        self._sidebar = PlanificadorSidebar()
        self._sidebar.view_mode_changed.connect(self._on_view_mode_changed)
        self._sidebar.project_changed.connect(self._on_project_changed)
        self._sidebar.add_project_clicked.connect(self._on_add_project)
        self._sidebar.add_resource_clicked.connect(self._on_add_resource)
        self._sidebar.settings_clicked.connect(self._on_show_settings)

        # Pages
        self._left_page = PlannerLeftView()
        self._right_page = PlannerRightView()

        self._left_page.add_stage_requested.connect(self._on_add_stage)
        self._left_page.edit_stage_requested.connect(self._on_edit_stage)
        self._left_page.edit_resource_requested.connect(self._on_edit_resource)
        self._left_page.edit_project_requested.connect(self._on_edit_project)
        self._left_page.exit_panoramic_requested.connect(lambda: self._on_panoramic_toggled(False))
        self._right_page.panoramic_toggled.connect(self._on_panoramic_toggled)

    def get_total_pages(self) -> int: return 2
    def get_current_page(self) -> int: return self._current_page
    def go_to_page(self, page_num: int):
        if page_num in (1, 2):
            self._current_page = page_num
            self.page_changed.emit(page_num, 2)

    def _get_active_project(self) -> dict:
        projects = self._data.get('projects', [])
        if not projects: return None
        for p in projects:
            if p.get('id') == self.active_project_id:
                return p
        self.active_project_id = projects[0].get('id')
        return projects[0]

    def _get_active_stages(self) -> list:
        p = self._get_active_project()
        if not p: return []
        stages = self._data.get('stages', [])
        return [st for st in stages if st.get('project_id') == p.get('id')]

    def _update_views(self):
        projects = self._data.get('projects', [])
        resources = self._data.get('resources', [])
        active_p = self._get_active_project()
        active_id = active_p.get('id') if active_p else None
        stages = self._get_active_stages()
        is_pano = getattr(self, 'is_panoramic', False)
        pano_mode = self._data.get('panoramic_mode_type', 'dual_page')

        self._sidebar.set_projects(projects, active_id)
        self._right_page.update_panoramic_button_text(pano_mode)

        if is_pano and pano_mode == 'single_page':
            # Modo panorámico de página única: Gantt completo en la página izquierda
            self._left_page.set_data(active_p, stages, resources, self.active_view_mode, is_panoramic=False)
            # Mostrar Gantt full directamente en el stack de la left_page
            self._left_page.stack.setCurrentIndex(1)
            self._left_page.left_gantt.side = 'full'
            self._left_page.left_gantt.set_data(active_p, stages)
            self._left_page.btn_exit_pano.show()
            self._left_page.hdr_frame.hide()
            self._right_page.set_data(active_p, stages, is_panoramic=False)
        elif is_pano and pano_mode == 'dual_page':
            # Modo panorámico dual: split left/right Gantt
            self._left_page.btn_exit_pano.hide()
            self._left_page.hdr_frame.show()
            self._left_page.set_data(active_p, stages, resources, self.active_view_mode, is_panoramic=True)
            self._right_page.set_data(active_p, stages, is_panoramic=True)
        else:
            # Modo normal
            self._left_page.btn_exit_pano.hide()
            self._left_page.hdr_frame.show()
            self._left_page.set_data(active_p, stages, resources, self.active_view_mode, is_panoramic=False)
            self._right_page.set_data(active_p, stages, is_panoramic=False)

    def _on_panoramic_toggled(self, checked: bool):
        self.is_panoramic = checked
        pano_mode = self._data.get('panoramic_mode_type', 'dual_page')
        if checked and pano_mode == 'single_page':
            self.single_page_requested.emit(True)
        else:
            self.single_page_requested.emit(False)
        self._update_views()

    def _on_view_mode_changed(self, mode: str):
        self.active_view_mode = mode
        self._update_views()

    def _on_project_changed(self, project_id: str):
        self.active_project_id = project_id
        self._update_views()

    def _on_add_project(self):
        dlg = ProjectDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.project_data:
            self._data.setdefault('projects', []).append(dlg.project_data)
            self.active_project_id = dlg.project_data.get('id')
            self._is_modified = True
            self._update_views()

    def _on_add_stage(self):
        active_p = self._get_active_project()
        if not active_p: return
        dlg = StageDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.stage_data:
            dlg.stage_data['project_id'] = active_p.get('id')
            self._data.setdefault('stages', []).append(dlg.stage_data)
            self._is_modified = True
            self._update_views()

    def _on_add_resource(self):
        dlg = ResourceDialog(parent=self._sidebar.window())
        if dlg.exec() and dlg.resource_data:
            self._data.setdefault('resources', []).append(dlg.resource_data)
            self._is_modified = True
            self._update_views()

    def _on_edit_project(self, proj_dict: dict):
        if not proj_dict: return
        dlg = ProjectDialog(project_to_edit=proj_dict, parent=self._sidebar.window())
        if dlg.exec():
            projects = self._data.get('projects', [])
            if dlg.is_delete:
                if proj_dict in projects:
                    projects.remove(proj_dict)
                    self.move_to_trash(proj_dict)
                    self._is_modified = True
                    self._update_views()
                    self.trash_changed.emit()
            elif dlg.project_data:
                idx = projects.index(proj_dict) if proj_dict in projects else -1
                if idx >= 0: projects[idx] = dlg.project_data
                self._is_modified = True
                self._update_views()

    def _on_edit_stage(self, stage_dict: dict):
        if not stage_dict: return
        dlg = StageDialog(stage_to_edit=stage_dict, parent=self._sidebar.window())
        if dlg.exec():
            stages = self._data.get('stages', [])
            if dlg.is_delete:
                if stage_dict in stages:
                    stages.remove(stage_dict)
                    self.move_to_trash(stage_dict)
                    self._is_modified = True
                    self._update_views()
                    self.trash_changed.emit()
            elif dlg.stage_data:
                idx = stages.index(stage_dict) if stage_dict in stages else -1
                if idx >= 0:
                    dlg.stage_data['project_id'] = stage_dict.get('project_id')
                    stages[idx] = dlg.stage_data
                self._is_modified = True
                self._update_views()

    def _on_edit_resource(self, res_dict: dict):
        if not res_dict: return
        dlg = ResourceDialog(resource_to_edit=res_dict, parent=self._sidebar.window())
        if dlg.exec():
            resources = self._data.get('resources', [])
            if dlg.is_delete:
                if res_dict in resources:
                    resources.remove(res_dict)
                    self.move_to_trash(res_dict)
                    self._is_modified = True
                    self._update_views()
                    self.trash_changed.emit()
            elif dlg.resource_data:
                idx = resources.index(res_dict) if res_dict in resources else -1
                if idx >= 0: resources[idx] = dlg.resource_data
                self._is_modified = True
                self._update_views()

    def _on_show_settings(self):
        curr_mode = self._data.get('panoramic_mode_type', 'dual_page')
        dlg = PlannerSettingsDialog(panoramic_mode=curr_mode, parent=self._sidebar.window())
        if dlg.exec():
            new_mode = dlg.panoramic_mode
            if new_mode != curr_mode:
                self._data['panoramic_mode_type'] = new_mode
                self._is_modified = True
                # Si el panorámico está activo, re-aplicar el modo correcto
                if getattr(self, 'is_panoramic', False):
                    if new_mode == 'single_page':
                        self.single_page_requested.emit(True)
                    else:
                        self.single_page_requested.emit(False)
                self._update_views()

    # --- Papelera ---
    def move_to_trash(self, item: dict):
        self._trash.append(item)

    def get_trash_items(self) -> list:
        return self._trash

    def restore_item(self, index: int):
        if 0 <= index < len(self._trash):
            item = self._trash.pop(index)
            if 'status' in item:
                self._data.setdefault('projects', []).append(item)
            elif 'progress' in item:
                self._data.setdefault('stages', []).append(item)
            else:
                self._data.setdefault('resources', []).append(item)
            self._is_modified = True
            self._update_views()
            self.trash_changed.emit()

    def get_name(self) -> str: return "Planificador"
    def get_id(self) -> str: return "planificador"
    def get_icon(self) -> str: return "planner.svg"
    def get_tab_color(self) -> str: return "#CD853F"
    def get_order(self) -> int: return 5

    def create_sidebar_widget(self) -> QWidget: return self._sidebar
    def create_left_page(self) -> QWidget: return self._left_page
    def create_right_page(self) -> QWidget: return self._right_page

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
