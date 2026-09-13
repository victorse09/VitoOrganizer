# =============================================================================
# Vito Organizer v2.2 - Help Dialogs
# Diálogos de Ayuda: Instrucciones, Acerca de, Versiones
# =============================================================================

import os
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QPushButton, QFrame, QScrollArea,
    QListWidget, QListWidgetItem, QLineEdit, QSplitter, QTextBrowser, QWidget
)

from core.version import APP_VERSION, APP_NAME


class InstructionsDialog(QDialog):
    """Diálogo interactivo de Centro de Ayuda e Instrucciones de Uso."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📖 Centro de Ayuda e Instrucciones de Uso - Vito Organizer")
        self.resize(900, 600)
        self.setMinimumSize(750, 480)
        self.setStyleSheet("""
            QDialog { background-color: #181825; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #cdd6f4; }
            QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px 10px; font-size: 13px; }
            QListWidget { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; font-size: 13px; outline: none; }
            QListWidget::item { padding: 8px 10px; border-bottom: 1px solid #313244; border-radius: 4px; }
            QListWidget::item:selected { background-color: #89b4fa; color: #11111b; font-weight: bold; }
            QListWidget::item:hover:!selected { background-color: #313244; }
            QTextBrowser { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 14px; font-size: 13px; line-height: 1.5; }
            QPushButton { background-color: #313244; color: #cdd6f4; border-radius: 4px; padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background-color: #89b4fa; color: #111; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header bar
        hdr = QHBoxLayout()
        hdr.setSpacing(10)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')
        lib_img = f"<img src='{os.path.join(icons_dir, 'library.svg')}' width='22' height='22'>"
        title = QLabel(f"{lib_img} <b>Centro de Ayuda e Instrucciones de Uso</b> <span style='color:#a6adc8; font-size:12px;'>v{APP_VERSION}</span>")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #f9e2af;")
        hdr.addWidget(title, 1)

        # Buscador interactivo
        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("🔍 Buscar en las instrucciones...")
        self.txt_search.setFixedWidth(260)
        self.txt_search.textChanged.connect(self._on_search_changed)
        hdr.addWidget(self.txt_search)

        layout.addLayout(hdr)

        # Body Splitter: Menú interactivo lateral + Visor HTML
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Menú lateral de temas
        self.list_topics = QListWidget()
        self.list_topics.setFixedWidth(240)
        
        # Visor HTML
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)

        # Contenido por temas
        self.topics = [
            ("📖 Conceptos y Navegación", self._get_doc_conceptos()),
            ("📅 Calendario y Agenda", self._get_doc_calendario()),
            ("🎂 Cumpleaños y Aniversarios", self._get_doc_cumpleanos()),
            ("📝 Notas y Tareas", self._get_doc_notas_tareas()),
            ("📊 Planificador y Carta Gantt", self._get_doc_planificador()),
            ("🔬 Laboratorio e Inventario", self._get_doc_laboratorio()),
            ("⚡ Editor Esquemático 2D", self._get_doc_esquematico()),
            ("💻 Editor IDE de Código", self._get_doc_ide_codigo()),
            ("📄 Listas de Chequeo y PDF", self._get_doc_checklists()),
            ("📦 Bodega y Consolidado", self._get_doc_bodega()),
            ("📚 Biblioteca Documental", self._get_doc_biblioteca()),
            ("🤖 Asistente de IA y Agente", self._get_doc_ia()),
            ("🛠️ Calculadoras y Conversor", self._get_doc_herramientas()),
            ("🌐 Conectividad y Red Local", self._get_doc_red()),
            ("🗑️ Papelera y Respaldos", self._get_doc_papelera_respaldos()),
            ("🕹️ Colección Retro y ROMs", self._get_doc_retro()),
            ("💾 Gestor de Discos y Respaldos", self._get_doc_respaldos_discos()),
        ]

        for idx, (title_str, _) in enumerate(self.topics):
            item = QListWidgetItem(title_str)
            item.setData(Qt.ItemDataRole.UserRole, idx)
            self.list_topics.addItem(item)

        self.list_topics.currentRowChanged.connect(self._on_topic_selected)
        
        splitter.addWidget(self.list_topics)
        splitter.addWidget(self.browser)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Footer bar
        ftr = QHBoxLayout()
        lbl_hint = QLabel("💡 <i>Presiona F1 en cualquier momento para abrir estas instrucciones.</i>")
        lbl_hint.setStyleSheet("color: #a6adc8; font-size: 11px;")
        ftr.addWidget(lbl_hint)
        ftr.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        ftr.addWidget(btn_close)

        layout.addLayout(ftr)

        # Seleccionar primer tema
        self.list_topics.setCurrentRow(0)

    def _on_topic_selected(self, row: int):
        if 0 <= row < len(self.topics):
            _, html = self.topics[row]
            self.browser.setHtml(html)

    def _on_search_changed(self, text: str):
        query = text.strip().lower()
        if not query:
            for i in range(self.list_topics.count()):
                self.list_topics.item(i).setHidden(False)
            return

        for i in range(self.list_topics.count()):
            item = self.list_topics.item(i)
            idx = item.data(Qt.ItemDataRole.UserRole)
            title_str, html_str = self.topics[idx]
            match = (query in title_str.lower()) or (query in html_str.lower())
            item.setHidden(not match)

    def _get_doc_conceptos(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📖 1. Conceptos Generales y Navegación</h2>
        <p>Vito Organizer combina la calidez y el diseño de una <b>agenda física esqueumórfica</b> sobre un tapete de escritorio de taller con potentes herramientas digitales.</p>

        <h3 style='color:#f9e2af;'>📌 Pestañas y Solapas Laterales</h3>
        <ul>
            <li>Haz clic en las solapas de colores del lomo (<i>Calendario, Cumpleaños, Notas, Tareas, Planificador, Laboratorio, Biblioteca, Gastos</i>) para pasar las páginas de la agenda.</li>
            <li>En <b>Opciones ➔ Configuración ➔ General</b> puedes reordenar libremente el orden de las solapas.</li>
        </ul>

        <h3 style='color:#f9e2af;'>🎨 Personalización y Logotipo</h3>
        <ul>
            <li>Puedes cargar un <b>Logotipo personalizado</b> (PNG, JPG, SVG) desde <i>Opciones ➔ Configuración ➔ General</i> para lucirlo en la solapa Portada.</li>
            <li>Elige entre encuadernación de <b>Anillas metálicas 3D</b>, <b>Espiral</b> o <b>Sin encuadernación</b>.</li>
        </ul>

        <h3 style='color:#f9e2af;'>💾 Guardado Automático y Estado</h3>
        <ul>
            <li>Toda modificación se guarda atómicamente en tiempo real en la carpeta física de la agenda abierta. La barra de estado inferior confirma cada guardado en 3 segundos (<i>✓ Agenda guardada</i>).</li>
        </ul>
        """

    def _get_doc_calendario(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📅 2. Calendario y Agenda Diaria</h2>
        <p>El módulo de Calendario permite planificar citas, eventos y tareas diarias en 5 modos de visualización dinámica.</p>

        <h3 style='color:#f9e2af;'>🗓️ Vistas de Tiempo</h3>
        <ul>
            <li><b>Día:</b> Agenda por horas de la jornada laboral configurable.</li>
            <li><b>Semana:</b> Distribución semanal en dos páginas abiertas.</li>
            <li><b>Mes:</b> Rejilla mensual completa con indicadores de eventos.</li>
            <li><b>Semestre y Año:</b> Visión panorámica del año completo.</li>
        </ul>

        <h3 style='color:#f9e2af;'>⚡ Retorno Rápido a HOY</h3>
        <ul>
            <li>Haz clic en la fecha fijada en la parte inferior para regresar de inmediato al día actual.</li>
        </ul>
        """

    def _get_doc_cumpleanos(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🎂 3. Cumpleaños y Aniversarios</h2>
        <p>Registra las fechas especiales de contactos y familiares para mantener un seguimiento automático ininterrumpido.</p>

        <h3 style='color:#f9e2af;'>🔄 Sincronización Automática</h3>
        <ul>
            <li>Los cumpleaños registrados se destacan automáticamente en las vistas de Calendario.</li>
            <li>La edad del contacto se calcula dinámicamente según el año que estés consultando en la agenda.</li>
        </ul>
        """

    def _get_doc_notas_tareas(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📝 4. Notas y 📋 Tareas</h2>
        <h3 style='color:#f9e2af;'>📝 Bitácoras y Cuadernos de Notas</h3>
        <ul>
            <li>Organiza apuntes y actas en cuadernos temáticos. Soporta formato de texto enriquecido y búsqueda de notas.</li>
        </ul>

        <h3 style='color:#f9e2af;'>📋 Listas de Tareas Pendientes</h3>
        <ul>
            <li>Crea listas de control (checklists) con casillas de verificación. El porcentaje de progreso global del proyecto se calcula reactivamente en tiempo real.</li>
        </ul>
        """

    def _get_doc_planificador(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📊 5. Planificador y Carta Gantt</h2>
        <p>Gestor de proyectos basado en gráficos Gantt estilo Lotus Organizer.</p>

        <h3 style='color:#f9e2af;'>🚀 Modo Panorámico</h3>
        <ul>
            <li>Activa el <b>Modo Panorámico</b> (botón superior o engranaje de configuración) para extender el gráfico Gantt a ambas páginas o a pantalla completa sin encuadernación.</li>
            <li>Gestiona etapas, hitos y el <b>Directorio de Recursos</b> asignados a cada fase.</li>
        </ul>
        """

    def _get_doc_laboratorio(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🔬 6. Módulo de Laboratorio y Taller</h2>
        <p>Control integral de inventario técnico para <b>Componentes Electrónicos</b>, <b>Instrumentos</b>, <b>Calibradores / Referencias</b>, <b>Herramientas</b>, <b>Insumos</b>, <b>Análisis</b> y <b>Proyectos de Desarrollo</b>.</p>

        <h3 style='color:#f9e2af;'>🧰 Calibradores y Dispositivos de Referencia</h3>
        <ul>
            <li><b>Referencias Patrón:</b> Registro y seguimiento de placas de referencia, referencias de tensión, corriente y pasivas (comparadas o fabricadas).</li>
            <li><b>Tablas de Mediciones y Puntos Patrón:</b> Registro de mediciones con unidades completas (V, mV, µV, A, mA, Ω, kΩ, etc.), cálculo de desviación/error y temperatura, con importación/exportación de archivos Excel y CSV.</li>
            <li><b>Sincronización Automática:</b> Generación instantánea de puntos patrón a partir de las mediciones realizadas.</li>
        </ul>

        <h3 style='color:#f9e2af;'>🔍 Ficha Técnica, Especificaciones y Registros</h3>
        <ul>
            <li><b>Especificaciones de Instrumentos:</b> Tablas dinámicas de funciones y escalas (Vdc, Vac, Adc, Aac, Resistencia, etc.) con resolución, exactitud porcentual y cuentas/dígitos. Carga rápida de plantillas de multímetros y medidores LCR.</li>
            <li><b>Modo Panorámico / Página Única:</b> Botones <i>"Pantalla"</i> y <i>"Vista Panorámica"</i> para expandir cualquier ficha o tabla a pantalla completa sin compresión horizontal.</li>
            <li><b>Guías de Calibración y Editor de Estructura:</b>
                <ul>
                    <li><b>Editor de Estructura:</b> Diseña procedimientos paso a paso mediante bloques (Título, Texto Enriquecido con fórmulas matemáticas LaTeX, Tablas de Verificación de Escalas contrastadas contra referencias patrón, Avisos de Seguridad e Imágenes).</li>
                    <li><b>Editor de Texto Enriquecido Completo:</b> Barra de herramientas con formato de texto (negrita, cursiva, subrayado, tamaño, color de texto, alineación, listas con viñetas y numeradas, inserción de tablas HTML, imágenes locales y fórmulas matemáticas LaTeX).</li>
                    <li><b>Visualización de Escalas de Contraste:</b> Al seleccionar una referencia patrón, el sistema muestra automáticamente con qué escala y valor se está contrastando cada punto de medición.</li>
                    <li><b>Ejecutor de Guía (Guide Runner):</b> Ejecuta y registra pruebas de calibración paso a paso con cálculo automático de errores y desviación.</li>
                </ul>
            </li>
            <li><b>Historial y Check Lists:</b> Registra mantenimientos, calibraciones, revisiones periódicas y fichas técnicas interactivas.</li>
            <li><b>Stock Mínimo y Costos:</b> Asigna stock mínimo de alerta y costo unitario por moneda (CLP, USD, EUR). El stock se gestiona de forma centralizada desde <b>Bodega</b>.</li>
            <li><b>Listas Configurables:</b> Personaliza todas las opciones de los menús desplegables del taller desde el engranaje de configuración inferior del Laboratorio.</li>
        </ul>
        """

    def _get_doc_esquematico(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>⚡ 7. Editor de Diagramas Esquemáticos 2D</h2>
        <p>Entorno CAD 2D integrado en <i>Desarrollo y Proyectos</i> para el diseño y captura de esquemas electrónicos.</p>

        <h3 style='color:#f9e2af;'>✏️ Cableado Ortogonal Inteligente y Snapping</h3>
        <ul>
            <li><b>Pin Snapping:</b> En modo cableado (<code>✏️</code>), el cursor se fija magnéticamente al centro exacto de los pines rojos (radio de 15px) con un indicador verde visual.</li>
            <li><b>Trazado Dinámico:</b> Al mover o rotar componentes (<code>R</code>), los cables conectados se adaptan automáticamente sin desconectarse.</li>
            <li><b>Handles de Edición:</b> Al seleccionar un cable aparecen nodos cuadrados interactivos en sus extremos y esquinas. Arrástralos para modificar el trazado o haz <b>doble clic</b> en un segmento para agregar un nuevo nodo.</li>
        </ul>

        <h3 style='color:#f9e2af;'>🖱️ Doble Clic y Menú Contextual (Clic Derecho)</h3>
        <ul>
            <li><b>Doble Clic en Componentes:</b> Abre la ventana de edición para modificar la <i>Referencia</i> (ej. U1), el <i>Valor</i> (ej. NE555) y editar individualmente las <b>etiquetas/números de cada pin</b> con vista previa en tiempo real.</li>
            <li><b>Clic Derecho:</b> Menú contextual para 🔄 <b>Rotar 90° (R)</b>, ✏️ <b>Editar Componente...</b>, 🏷️ <b>Asignar Nombre de Red</b> y 🗑️ <b>Eliminar (Supr)</b>.</li>
            <li><b>Exportación:</b> Generación instantánea de Lista de Materiales (<b>BOM</b>), <b>Netlist SPICE</b> e imágenes <b>PNG</b>.</li>
        </ul>
        """

    def _get_doc_ide_codigo(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>💻 8. Editor IDE de Código y Microcontroladores</h2>
        <p>Entorno de desarrollo integrado para programación de sistemas embebidos (Arduino, ESP32, Raspberry Pi, STM32, PIC, Python, C++, C#, JS).</p>

        <h3 style='color:#f9e2af;'>⚡ Funciones del Editor IDE</h3>
        <ul>
            <li><b>Resaltado de Sintaxis:</b> Coloración inteligente para 10 lenguajes y números de línea.</li>
            <li><b>Plantillas Base:</b> Carga plantillas <i>setup()/loop()</i> para Arduino, ESP32, Raspberry Pi Pico y Python.</li>
            <li><b>Buscar y Reemplazar:</b> Panel interactivo activable mediante <code>Ctrl+F</code> / <code>Ctrl+H</code>.</li>
            <li><b>Compilador/Verificador:</b> Verificación de código en tiempo real.</li>
        </ul>
        """

    def _get_doc_checklists(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📄 9. Listas de Chequeo y Reportes PDF</h2>
        <p>Módulo de inspección técnica, control de calidad y mantenimiento preventivo con emisión de informes formales.</p>

        <h3 style='color:#f9e2af;'>📋 Características Principales</h3>
        <ul>
            <li><b>Plantillas Predefinidas:</b> Protocolos listos para Inspección de Banco, Calibración de Multímetro, Mantenimiento de Soldador, etc.</li>
            <li><b>Asignación Múltiple:</b> Aplica un único chequeo sobre múltiples herramientas o equipos simultáneamente.</li>
            <li><b>Correlativos Continuos:</b> Asignación automática de folios correlativos (ej. CHK-2026-07-001).</li>
            <li><b>Reporte PDF Técnico:</b> Genera informes PDF formateados con el logotipo corporativo, foto de la herramienta y tabla de verificación de resultados.</li>
        </ul>
        """

    def _get_doc_bodega(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📦 10. Bodega e Inventario Consolidado</h2>
        <p>Gestión centralizada de existencias, ubicaciones y valorización financiera.</p>

        <h3 style='color:#f9e2af;'>📊 Sub-Vistas de Bodega</h3>
        <ul>
            <li><b>Ingresos / Egresos:</b> Registro de movimientos con costo unitario asignado.</li>
            <li><b>Vista de Stock:</b> Límites de existencias y alertas de mínimo.</li>
            <li><b>Vista de Saldos:</b> Ubicaciones físicas en estantes, gavetas o empaques.</li>
            <li><b>Vista de Costos y Balance Consolidado:</b> Valorización financiera total del inventario por divisa con tabla de repuestos críticos destacados en rojo.</li>
        </ul>
        """

    def _get_doc_biblioteca(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>📚 11. Biblioteca Documental, Libros y Revistas</h2>
        <p>Almacenamiento, indexación y visualización avanzada de archivos técnicos, manuales, hojas MSDS, imágenes, libros y revistas electrónicas.</p>

        <h3 style='color:#f9e2af;'>📝 Creador y Editor de Documentos Propios (.doki)</h3>
        <ul>
            <li><b>Nuevo Formato Propio <code>.doki</code>:</b> Contenedor comprimido ZIP estructurado con <code>metadata.json</code> (título, autor, fechas, formato de hoja, orientación, márgenes, tags), <code>content.html</code> (diseño y maquetación), <code>content.xml</code> (representación semántica) y carpeta <code>images/</code> con recursos gráficos incrustados.</li>
            <li><b>Editor en Modo de Página Única:</b> Editor de texto enriquecido a pantalla completa con hoja adaptativa con proporciones reales:
                <ul>
                    <li><b>Formato de Hoja:</b> Selector de tamaño de página con opciones para <b>Carta (Letter - Predeterminado)</b>, <b>Oficio (Legal)</b>, <b>A4</b>, <b>A3</b> y <b>A5</b>.</li>
                    <li><b>Orientación y Márgenes:</b> Alterna entre <b>Vertical (Portrait)</b> y <b>Horizontal (Landscape)</b> con márgenes configurables (Normal 20mm, Estrecho 10mm, Ancho 30mm).</li>
                    <li><b>Salto de Página Formal:</b> Botón <i>📄 Salto de Página</i> que inserta un marcador visual y realiza la partición real de páginas en la vista y en la exportación a PDF.</li>
                    <li><b>Alineación Completa de Párrafo:</b> Botones para alineación a la <b>Izquierda</b>, <b>Centrado</b>, <b>Derecha</b> y <b>Justificado</b>.</li>
                    <li><b>Herramientas de Formato:</b> Negrita, cursiva, subrayado, tamaños de fuente, colores, resaltador, viñetas, numeración, tablas personalizadas, imágenes locales y fórmulas matemáticas LaTeX.</li>
                </ul>
            </li>
            <li><b>Exportación Multiformato Nativa:</b>
                <ul>
                    <li><b>📄 PDF:</b> Generación de documentos PDF de alta resolución respetando tamaño de hoja, orientación y saltos de página.</li>
                    <li><b>📚 EPUB:</b> Creación de libros digitales estándar listos para lectores electrónicos.</li>
                    <li><b>📑 OpenDocument (.odt):</b> Documentos compatibles con LibreOffice, OpenOffice y suites ofimáticas.</li>
                    <li><b>⚙️ XML:</b> Exportación a archivos XML semánticos limpios.</li>
                </ul>
            </li>
            <li><b>Integración Directa desde el Visor de PDFs y Traductor:</b> Puedes enviar recortes de imágenes, párrafos reconocidos por OCR o traducciones técnicas al español directamente a un documento <code>.doki</code> existente o crear uno nuevo con un solo clic.</li>
            <li><b>Almacenamiento Local:</b> Todos los archivos se guardan organizadamente en la subcarpeta <code>biblioteca/doki/</code> y sus exportaciones en <code>biblioteca/doki/exports/</code>.</li>
        </ul>

        <h3 style='color:#f9e2af;'>📖 Visor Integrado de PDF y EPUB (Modo de Página Única)</h3>
        <ul>
            <li><b>Lectura de Pantalla Completa:</b> Al abrir un documento en el visor integrado, la agenda se expande a modo de página única para una lectura cómoda sin distracción.</li>
            <li><b>Modos de Visualización:</b>
                <ul>
                    <li><b>Página a Página:</b> Vista clásica centrada en la página actual.</li>
                    <li><b>Vista Continua:</b> Flujo vertical continuo con desplazamiento suave entre todas las páginas del documento.</li>
                </ul>
            </li>
            <li><b>Ajustes y Zoom:</b> Botones de <b>Ajustar al Ancho</b> y <b>Ajustar al Alto</b> en un solo clic, selector porcentual de zoom (50% a 200%) y botón de rotación en 90°.</li>
            <li><b>Panel Lateral con Miniaturas:</b> Vista gráfica rápida de todas las páginas del libro o revista.</li>
            <li><b>Modos de Cursor:</b> Alterna entre <i>Mano</i> (desplazamiento suave) y <i>Recortar / OCR</i> (selección rectangular de áreas).</li>
        </ul>

        <h3 style='color:#f9e2af;'>🌐 Traductor Técnico de Electrónica Integrado</h3>
        <ul>
            <li><b>Traducción Especializada:</b> Traduce al español texto seleccionado, texto reconocido por el OCR, la página actual o un rango completo de páginas.</li>
            <li><b>Motores de Traducción Compatibles:</b>
                <ol>
                    <li><b>🤖 IA Local (LM Studio / Ollama):</b> Usa modelos LLM locales con prompt especializado en ingeniería electrónica que preserva acrónimos estándar (PCB, IC, MOSFET, SMD, PWM, SPI, I2C, UART), unidades de medida y fórmulas matemáticas.</li>
                    <li><b>🌐 Traductor Online:</b> Servicio rápido en línea para traducción fluida de párrafos técnicos.</li>
                    <li><b>💾 Traductor Local Offline:</b> Motor de reglas y léxico técnico de ingeniería que funciona 100% sin conexión.</li>
                </ol>
            </li>
            <li><b>Exportación y Notas:</b> Diálogo interactivo para copiar la traducción al portapapeles o guardarla como archivo <code>.txt</code>.</li>
        </ul>

        <h3 style='color:#f9e2af;'>📌 Sistema de Marcadores de Página</h3>
        <ul>
            <li><b>Creación de Marcadores:</b> Guarda páginas clave con notas descriptivas mediante el botón <i>Marcar</i>.</li>
            <li><b>Salto Directo:</b> Accede a tus marcadores guardados desde la pestaña lateral del visor o directamente desde la ficha derecha de la Biblioteca en un solo clic.</li>
        </ul>

        <h3 style='color:#f9e2af;'>📑 Extracción y Selector de Artículos (Exportar a PDF)</h3>
        <ul>
            <li><b>Extractor de Artículos:</b> Selecciona un rango de páginas (ej. páginas 15 a 22) de una revista o libro y expórtalas instantáneamente como un nuevo documento PDF independiente en la carpeta <code>biblioteca/Articulos/</code>.</li>
            <li><b>Gestión en Ficha:</b> Los artículos generados quedan listados en la ficha del documento con acceso directo para abrirlos o ver su ubicación en el documento original.</li>
        </ul>

        <h3 style='color:#f9e2af;'>🔍 Reconocimiento de Texto (OCR) y Recorte de Áreas</h3>
        <ul>
            <li><b>OCR de Página Completa:</b> Extrae el texto legible de la página completa mediante el botón <i>OCR</i>.</li>
            <li><b>OCR por Selección:</b> Dibuja un recuadro sobre cualquier párrafo, diagrama o texto de la página para extraer su contenido o traducirlo directamente.</li>
            <li><b>Exportación de Texto:</b> Ventana interactiva para copiar el texto reconocido, traducirlo o guardarlo directamente como archivo <code>.txt</code>.</li>
        </ul>

        <h3 style='color:#f9e2af;'>⚙️ Configuración de Apertura de Documentos</h3>
        <ul>
            <li>Desde el engranaje de configuración (⚙) de Biblioteca puedes elegir la acción predeterminada al abrir documentos:
                <ol>
                    <li><b>Visor Integrado de VitoOrganizer:</b> Abre en el visor interactivo de página única con todas las herramientas de lectura y marcadores.</li>
                    <li><b>Visor Predeterminado del Sistema:</b> Abre el archivo con la aplicación externa de tu sistema operativo.</li>
                    <li><b>Preguntar Siempre:</b> Muestra una ventana emergente cada vez que haces clic en un documento, permitiendo además recordar tu preferencia.</li>
                </ol>
            </li>
        </ul>
        """

    def _get_doc_ia(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🤖 12. Asistente de IA Local y Agente</h2>
        <p>Asistente virtual inteligente flotante (<code>Ctrl+Shift+I</code>) integrado con IA Local (LM Studio, Ollama, OpenAI API).</p>

        <h3 style='color:#f9e2af;'>⚡ Capacidades Autónomas del Agente</h3>
        <ul>
            <li><b>Inspección de Agenda:</b> Consulta y analiza en tiempo real componentes, proyectos, notas e inventario de tu agenda.</li>
            <li><b>Traba Flotante:</b> Activa 📌 <i>Trabar Arriba</i> para mantener el asistente visible sobre la pantalla mientras trabajas.</li>
            <li><b>Copia Rápida:</b> Botones dedicados para copiar código formateado o respuestas completas, y exportar chats a Markdown (<code>.md</code>).</li>
        </ul>
        """

    def _get_doc_herramientas(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🛠️ 13. Calculadoras y Conversor de Unidades</h2>
        <h3 style='color:#f9e2af;'>🧮 Calculadora Flotante (Ctrl+K)</h3>
        <ul>
            <li><b>Básica y Científica:</b> Historial de operaciones y funciones trigonométricas/logarítmicas.</li>
            <li><b>Electrónica Avanzada:</b> Más de 38 fórmulas analógicas, digitales y de potencia, disipación térmica, mallas por determinante (Cramer), compuertas lógicas con tabla de verdad y código de colores de resistencias (4, 5 y 6 bandas).</li>
        </ul>

        <h3 style='color:#f9e2af;'>📏 Conversor de Unidades (Ctrl+U)</h3>
        <ul>
            <li>Conversión de magnitudes físicas, calibres de cable AWG y conversión entre bases numéricas (Binario, Octal, Decimal, Hexadecimal).</li>
        </ul>
        """

    def _get_doc_red(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🌐 14. Conectividad y Red Local</h2>
        <p>Herramientas para compartir y sincronizar agendas en red local (LAN).</p>

        <h3 style='color:#f9e2af;'>📡 Servidor y Cliente</h3>
        <ul>
            <li><b>Modo Servidor:</b> Comparte tu agenda localmente con protección por contraseña.</li>
            <li><b>Modo Cliente:</b> Sincroniza cambios asíncronamente en ambas direcciones con barra de progreso.</li>
        </ul>
        """

    def _get_doc_papelera_respaldos(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🗑️ 15. Papelera de Reciclaje y Respaldos</h2>
        <h3 style='color:#f9e2af;'>♻️ Papelera Esqueumórfica</h3>
        <p>Recuperación segura de elementos eliminados con estados visuales (vacía / llena).</p>

        <h3 style='color:#f9e2af;'>📦 Respaldos Completos ZIP</h3>
        <p>Crea copias de seguridad de toda la base de datos y archivos multimedia en un solo archivo comprimido.</p>
        """

    def _get_doc_retro(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>🕹️ 16. Colección Retro y Gestor de ROMs</h2>
        <p>Catálogo de consolas retro, placas arcade y ficheros ROM con metadatos técnicos y portadas.</p>
        """

    def _get_doc_respaldos_discos(self) -> str:
        return """
        <h2 style='color:#a6e3a1;'>💾 17. Gestor de Discos y Respaldos</h2>
        <p>Monitoreo de unidades de almacenamiento, discos duros externos y sincronización de copias de seguridad.</p>
        """


class AboutDialog(QDialog):
    """Diálogo de información institucional sobre el software."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Acerca de {APP_NAME}")
        self.setFixedSize(560, 470)
        self.setStyleSheet("""
            QDialog {
                background-color: #181825;
                color: #cdd6f4;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                background: transparent;
                background-color: transparent;
                border: none;
                color: #cdd6f4;
            }
            QFrame#cardFrame {
                background-color: #1e1e2e;
                border: 1px solid #313244;
                border-radius: 8px;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 4px;
                padding: 6px 20px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #89b4fa;
                color: #11111b;
                border-color: #89b4fa;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Cabecera con Logo y Versión
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')
        app_icon_path = os.path.join(icons_dir, 'vito_organizer_icon.svg')

        logo_layout = QHBoxLayout()
        logo_layout.setSpacing(14)
        if os.path.exists(app_icon_path):
            lbl_logo = QLabel()
            lbl_logo.setStyleSheet("background: transparent; border: none;")
            pix = QPixmap(app_icon_path).scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lbl_logo.setPixmap(pix)
            logo_layout.addWidget(lbl_logo)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        lbl_app = QLabel(f"<h2 style='margin:0; padding:0; color:#89b4fa; font-size: 22px;'>{APP_NAME}</h2>")
        lbl_app.setStyleSheet("background: transparent; border: none;")
        info_layout.addWidget(lbl_app)

        lbl_ver = QLabel(f"<b style='color:#a6adc8; font-size:13px;'>Versión {APP_VERSION}</b>")
        lbl_ver.setStyleSheet("background: transparent; border: none;")
        info_layout.addWidget(lbl_ver)
        logo_layout.addLayout(info_layout)
        logo_layout.addStretch()
        layout.addLayout(logo_layout)

        # 2. Recuadro / Tarjeta Principal Estructurada
        card = QFrame()
        card.setObjectName("cardFrame")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        # Texto superior descriptivo normalizado
        lbl_desc = QLabel(
            "Entorno de Organización Profesional y Gestión Técnica de Laboratorio, "
            "Electrónica, Taller y Desarrollo con interfaz esqueumórfica retro."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("background: transparent; border: none; color: #cdd6f4; font-size: 13px; line-height: 1.5;")
        card_layout.addWidget(lbl_desc)

        # Línea divisoria sutil
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Plain)
        sep.setStyleSheet("background-color: #313244; max-height: 1px; border: none; margin: 2px 0;")
        card_layout.addWidget(sep)

        # Mensaje institucional solicitado (Lotus Organizer y Vitokin)
        lbl_homage = QLabel(
            "<p style='margin:0; font-size: 13px; color: #cdd6f4; line-height: 1.6;'>"
            "Una aplicación para rememorar a <b>Lotus Organizer</b> con implementaciones modernas.<br><br>"
            "<i style='color: #89b4fa; font-size: 13px;'>Desarrollado por <b>Vitokin</b> con especial dedicatoria para todos los entusiastas de la electrónica y el grupo de <b>Naser Electrónica</b>.</i>"
            "</p>"
        )
        lbl_homage.setWordWrap(True)
        lbl_homage.setStyleSheet("background: transparent; border: none;")
        card_layout.addWidget(lbl_homage)

        layout.addWidget(card)

        # 3. Pie de página Legal
        legal = QLabel(
            "© 2026 Vito Organizer Development Team.<br>"
            "Desarrollado para ingeniería, electrónica, investigación y gestión técnica."
        )
        legal.setStyleSheet("background: transparent; border: none; color: #6c7086; font-size: 11px; line-height: 1.4;")
        layout.addWidget(legal)

        layout.addStretch()

        # 4. Botón Aceptar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Aceptar")
        btn_close.setFixedWidth(110)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)


class InformationDialog(QDialog):
    """Diálogo con el explorador de documentación técnica en Markdown (.md) de la aplicación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Información Técnica y Documentación — {APP_NAME}")
        self.resize(920, 640)
        self.setStyleSheet("""
            QDialog { background-color: #181825; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QLabel { color: #cdd6f4; }
            QListWidget { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; padding: 4px; font-size: 12px; }
            QListWidget::item { padding: 8px 10px; border-radius: 4px; margin-bottom: 2px; }
            QListWidget::item:selected { background-color: #313244; color: #89b4fa; font-weight: bold; }
            QListWidget::item:hover:!selected { background-color: rgba(255, 255, 255, 0.05); }
            QTextBrowser { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; padding: 18px; font-size: 13px; line-height: 1.6; }
            QPushButton { background-color: #313244; color: #cdd6f4; border-radius: 4px; padding: 6px 14px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: #89b4fa; color: #111; }
            QLineEdit { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #313244; border-radius: 4px; padding: 5px 8px; font-size: 11px; }
        """)
        self.docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs')
        self._setup_ui()
        self._load_docs_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Cabecera
        hdr_layout = QHBoxLayout()
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')
        lbl_ico = QLabel()
        ico_p = os.path.join(icons_dir, 'document.svg')
        if os.path.exists(ico_p):
            lbl_ico.setPixmap(QPixmap(ico_p).scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        hdr_layout.addWidget(lbl_ico)

        lbl_hdr = QLabel("<b>Centro de Información y Documentación Técnica (Markdown)</b>")
        lbl_hdr.setStyleSheet("font-size: 14px; color: #89b4fa;")
        hdr_layout.addWidget(lbl_hdr)
        hdr_layout.addStretch()
        layout.addLayout(hdr_layout)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #313244; width: 2px; }")

        # Panel Izquierdo: Lista de documentos y buscador
        left_widget = QWidget()
        l_layout = QVBoxLayout(left_widget)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(6)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Buscar tema...")
        self.txt_search.textChanged.connect(self._filter_docs)
        l_layout.addWidget(self.txt_search)

        self.list_docs = QListWidget()
        self.list_docs.currentRowChanged.connect(self._on_doc_selected)
        l_layout.addWidget(self.list_docs)

        left_widget.setMinimumWidth(240)
        left_widget.setMaximumWidth(320)
        splitter.addWidget(left_widget)

        # Panel Derecho: Visor de Markdown
        self.doc_viewer = QTextBrowser()
        self.doc_viewer.setOpenExternalLinks(True)
        splitter.addWidget(self.doc_viewer)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Botones inferiores
        btn_row = QHBoxLayout()
        self.btn_open_file = QPushButton(" Abrir Archivo .md")
        if os.path.exists(os.path.join(icons_dir, 'open_folder.svg')):
            self.btn_open_file.setIcon(QIcon(os.path.join(icons_dir, 'open_folder.svg')))
        self.btn_open_file.clicked.connect(self._open_selected_file)
        btn_row.addWidget(self.btn_open_file)

        btn_row.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.setFixedWidth(90)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _load_docs_list(self):
        self.docs = []
        if os.path.exists(self.docs_dir):
            for fn in sorted(os.listdir(self.docs_dir)):
                if fn.lower().endswith(('.md', '.markdown')):
                    full_p = os.path.join(self.docs_dir, fn)
                    title = fn.replace('_', ' ').replace('.md', '').title()
                    try:
                        with open(full_p, 'r', encoding='utf-8') as f:
                            for line in f:
                                line_s = line.strip()
                                if line_s.startswith('# '):
                                    title = line_s.replace('# ', '').strip()
                                    break
                    except Exception:
                        pass
                    self.docs.append({'title': title, 'filename': fn, 'path': full_p})

        self._render_list()
        if self.list_docs.count() > 0:
            self.list_docs.setCurrentRow(0)

    def _render_list(self):
        self.list_docs.clear()
        q = self.txt_search.text().lower().strip()
        for doc in self.docs:
            if not q or q in doc['title'].lower() or q in doc['filename'].lower():
                item = QListWidgetItem(f"📄  {doc['title']}")
                item.setData(Qt.ItemDataRole.UserRole, doc)
                self.list_docs.addItem(item)

    def _filter_docs(self):
        self._render_list()

    def _on_doc_selected(self, row: int):
        item = self.list_docs.item(row)
        if not item: return
        doc = item.data(Qt.ItemDataRole.UserRole)
        if not doc or not os.path.exists(doc['path']): return

        try:
            with open(doc['path'], 'r', encoding='utf-8') as f:
                content_md = f.read()
            self.doc_viewer.setMarkdown(content_md)
        except Exception as e:
            self.doc_viewer.setHtml(f"<p style='color:#f38ba8;'>Error al leer documento: {e}</p>")

    def _open_selected_file(self):
        item = self.list_docs.currentItem()
        if not item: return
        doc = item.data(Qt.ItemDataRole.UserRole)
        if doc and os.path.exists(doc['path']):
            from plugins.plugin_base import open_local_file
            open_local_file(doc['path'])


class VersionDialog(QDialog):
    """Diálogo con el historial de versiones y bitácora de cambios."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Bitácora de Versiones - Vito Organizer")
        self.resize(580, 480)
        self.setStyleSheet("""
            QDialog { background-color: #181825; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QLabel { background: transparent; border: none; color: #cdd6f4; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background-color: #89b4fa; color: #111; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')
        hist_img = f"<img src='{os.path.join(icons_dir, 'history.svg')}' width='20' height='20'>"
        title = QLabel(f"{hist_img} <b>Historial de Cambios y Versiones</b>")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #f9e2af;")
        layout.addWidget(title)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
            }
        """)

        changelog_html = """
        <h3 style='color: #a6e3a1; margin-bottom: 4px;'>v.2.12 - Agosto 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Creador y Editor de Documentos Propios (.doki) en Biblioteca:</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Formato Contenedor Propio <code>.doki</code>:</b> Estructura ZIP que almacena <code>metadata.json</code>, <code>content.html</code>, <code>content.xml</code> y carpeta <code>images/</code> con recursos locales.</li>
                    <li><b>Formato de Hoja y Maquetación:</b> Tamaños de página configurables (<b>Carta [Predeterminado]</b>, <b>Oficio</b>, <b>A4</b>, <b>A3</b>, <b>A5</b>), orientación <b>Vertical / Horizontal</b> y márgenes personalizables.</li>
                    <li><b>Salto de Página y Alineación:</b> Botón dedicado <i>📄 Salto de Página</i> con paginación formal en vista y PDF, más alineación a la izquierda, centrado, derecha y justificado.</li>
                    <li><b>Editor en Modo de Página Única:</b> Editor de texto enriquecido a pantalla completa con herramientas de formato (negrita, cursiva, subrayado, tamaños de fuente, colores, resaltador, viñetas, listas numeradas, tablas personalizadas, imágenes locales y fórmulas matemáticas LaTeX).</li>
                    <li><b>Exportación Multiformato Nativa:</b> Exportación directa a <b>PDF</b> (respetando tamaños de hoja y saltos), <b>EPUB</b> (libros electrónicos), <b>OpenDocument (.odt)</b> y <b>XML</b> semántico.</li>
                    <li><b>Integración con Visor y Traductor:</b> Permite enviar texto seleccionado, texto reconocido por OCR, recortes de imágenes y traducciones directamente al documento Doki.</li>
                </ul>
            </li>
            <li><b>Visor Integrado de PDF y EPUB en Biblioteca (Modo de Página Única):</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Visor Completo de Libros y Revistas:</b> Motor de renderizado de alta fidelidad basado en PyMuPDF (fitz) para archivos <code>.pdf</code> y <code>.epub</code> en modo de pantalla completa.</li>
                    <li><b>Modos de Visualización:</b> Conmutador para <i>Vista Página a Página</i> individual y <i>Vista Continua</i> con flujo de scroll vertical entre páginas.</li>
                    <li><b>Controles de Ajuste y Zoom:</b> Botones de <b>Ajustar al Ancho</b> y <b>Ajustar al Alto</b> directos, selector numérico de página, selector porcentual de zoom (50% a 200%) y rotación en 90°.</li>
                    <li><b>Panel Lateral con Pestañas:</b> Miniaturas de páginas completas, lista interactiva de marcadores y lista de artículos extraídos.</li>
                    <li><b>Modos de Interacción:</b> Modo Mano (desplazamiento fluido) y Modo Recortar / OCR (selección rectangular de áreas sobre la página).</li>
                </ul>
            </li>
            <li><b>Traductor Técnico al Español Integrado (Electrónica e Ingeniería):</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Traducción Especializada de Texto:</b> Traduce selección de texto, texto reconocido por OCR, página completa o rango de páginas.</li>
                    <li><b>Integración Multimotor:</b>
                        <ul>
                            <li><b>🤖 IA Local (LM Studio / Ollama):</b> Modelos locales con prompt de ingeniería que preserva términos clave (MOSFET, PCB, PWM, SPI, I2C, UART), unidades eléctricas y fórmulas matemáticas.</li>
                            <li><b>🌐 Servicio Online:</b> Traducción web rápida sin configuraciones adicionales.</li>
                            <li><b>💾 Motor Local Offline:</b> Traductor de reglas y léxico especializado en electrónica que opera 100% sin conexión a internet.</li>
                        </ul>
                    </li>
                    <li><b>Diálogo Interactivo:</b> Vista comparativa lado a lado (Original vs Español), copiado al portapapeles y guardado en archivo <code>.txt</code>.</li>
                </ul>
            </li>
            <li><b>Sistema de Marcadores de Página y Extracción de Artículos:</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Marcadores Personalizados:</b> Botón <i>Marcar Página</i> para guardar puntos de lectura con títulos descriptivos y salto directo desde el visor o desde la ficha derecha de Biblioteca.</li>
                    <li><b>Extractor de Artículos a PDF:</b> Herramienta interactiva para seleccionar un rango de páginas de cualquier libro o revista y exportarlas como un nuevo archivo <code>.pdf</code> independiente en <code>biblioteca/Articulos/</code>.</li>
                </ul>
            </li>
            <li><b>Reconocimiento Óptico de Caracteres (OCR) y Recorte de Áreas:</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Extracción de Texto:</b> Herramienta de OCR para reconocer y extraer texto de toda la página o de áreas seleccionadas en pantalla.</li>
                    <li><b>Diálogo Modal Interactivo:</b> Vista previa del texto reconocido con contador de palabras/caracteres, botón de copiado al portapapeles y guardado como archivo <code>.txt</code>.</li>
                </ul>
            </li>
            <li><b>Configuración de Comportamiento al Abrir Documentos:</b>
                <ul style='margin-top: 2px;'>
                    <li>Opción en la configuración de Biblioteca para definir la acción predeterminada al abrir documentos: <i>Usar Visor Integrado de VitoOrganizer</i>, <i>Usar Visor del Sistema</i> o <i>Preguntar Siempre</i> (con ventana emergente y opción de recordar).</li>
                </ul>
            </li>
            <li><b>Módulo de Calibradores y Dispositivos de Referencia en Laboratorio:</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Nuevo Apartado de Calibradores:</b> Gestión completa de referencias patrón clasificadas en comparadas o fabricadas, fecha de última calibración y comentarios.</li>
                    <li><b>Estructura de Almacenamiento Dedicada:</b> Persistencia local y atómica en la subcarpeta <code>laboratorio/calibradores/</code> con índice <code>calibradores.json</code>.</li>
                    <li><b>Pestañas con Iconos SVG Tematizados de Alto Contraste:</b> Mediciones Realizadas (con importación/exportación Excel/CSV) y Puntos de Referencia Patrón.</li>
                    <li><b>Selector Unificado "Nuevo Elemento":</b> Rediseño del panel lateral para agrupar las opciones de creación en un único botón con menú desplegable.</li>
                </ul>
            </li>
            <li><b>Especificaciones Técnicas y Rangos de Medición en Instrumentos:</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Tablas Dinámicas de Funciones y Escalas:</b> Creación y administración de múltiples tablas por función (Vdc, Vac, Adc, Aac, Resistencia, etc.) con resolución, exactitud porcentual y cuentas.</li>
                    <li><b>Plantillas Rápidas de Instrumentos:</b> Carga en 1 clic de configuraciones base para multímetros estándar, True-RMS y medidores LCR.</li>
                </ul>
            </li>
            <li><b>Mejoras en Guías de Calibración y Editor de Estructura (Laboratorio):</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Visualización de Escalas de Contraste:</b> Al seleccionar un patrón de referencia, se visualiza claramente con qué escala y valor se está contrastando cada punto de medición.</li>
                    <li><b>Suite Completa de Texto Enriquecido en Bloques de Guía:</b> Formato de texto completo (negrita, cursiva, subrayado, tamaño, color, alineación, listas con viñetas y numeradas, inserción de tablas HTML, imágenes locales y fórmulas matemáticas LaTeX).</li>
                    <li><b>Corrección de Contraste:</b> Solución integral de contraste en botones y cuadros de texto enriquecido en el editor de estructura y en el ejecutor de guías.</li>
                </ul>
            </li>
            <li><b>Modo de Página Única / Panorámica en Ficha Técnica y Especificaciones:</b>
                <ul style='margin-top: 2px;'>
                    <li>Botones <i>"Pantalla"</i> y <i>"Vista Panorámica"</i> para expandir cualquier ficha o tabla a pantalla completa sin compresión horizontal.</li>
                </ul>
            </li>
            <li><b>Iconografía Vectorial SVG Completa:</b> Estandarización de todos los botones y herramientas con iconos SVG tematizados de alto contraste.</li>
        </ul>
        <h3 style='color: #89b4fa; margin-bottom: 4px;'>v.2.11 - Agosto 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
                <ul style='margin-top: 2px;'>
                    <li>Nuevo botón <b>"Copiar Detalle"</b> en el panel de fórmulas de Electrónica para copiar informes técnicos estructurados con título del cálculo, variable seleccionada, desglose con viñetas de cada parámetro de entrada con su nombre descriptivo y unidad, y ecuación resuelta.</li>
                    <li>Soporte de copia detallada en el panel de Código de Colores de Resistencias (bandas seleccionadas, multiplicador, tolerancia y PPM).</li>
                    <li>Corrección de prefijos duplicados en la visualización de fórmulas.</li>
                </ul>
            </li>
            <li><b>Modo Registros de Instrumentos en Laboratorio:</b> Nuevo sistema integral para la gestión técnica avanzada y documentación de cada instrumento de laboratorio (`laboratorio/instrumentos/<ID>_<Nombre>/`):
                <ul style='margin-top: 2px;'>
                    <li><b>Navegación Sincronizada de 2 Páginas:</b> Activación con el botón <i>"Registros"</i> en la cabecera del instrumento. La página izquierda incorpora una tarjeta con imagen miniatura (cargada dinámicamente desde la ficha, biblioteca o icono), botón <i>"← Volver al Inventario"</i> y menú lateral interactivo para cambiar entre las 5 secciones especializadas.</li>
                    <li><b>Ficha del Instrumento:</b> Resumen técnico con marca, modelo, S/N, estado operativo con badge de color, insumos/accesorios y ubicación.</li>
                    <li><b>Documentación Técnica del Instrumento:</b> Acceso directo para abrir manuales de usuario y guías de operación (URLs o archivos locales) y explorador de documentos y manuales vinculados desde la Biblioteca de VitoOrganizer con apertura inmediata.</li>
                    <li><b>Descripción Técnica (HTML):</b> Editor de texto enriquecido nativo (`description.html`) con barra de herramientas compacta y optimizada con solo iconos vectoriales oscuros (`_dark.svg`) de alto contraste: Negrita, Cursiva, Subrayado, nuevo Selector de Tamaño de Fuente desplegable (9 a 36 pt), Color de texto, Listas con viñetas, Tablas e Inserción de imágenes locales en la subcarpeta `images/`.</li>
                    <li><b>Sistema de Check List y Mantenimiento:</b> Historial cronológico de eventos y revisiones con registro de chequeos interactivos y visualización con doble clic.</li>
                    <li><b>Banco de Pruebas de Calibración:</b> Matriz de calibración con cálculo automático de desviación/error (nominal vs. medido), importador de estructuras base (Multímetro, Osciloscopio, Fuente de Poder) y almacenamiento estructurado en `calibration.json`.</li>
                    <li><b>Diseño Visual e Iconos Vectoriales:</b> Iconos vectoriales oscuros (`_dark.svg`) de alto contraste en toda la interfaz y eliminación de secciones duplicadas en la ficha general de inventario.</li>
                </ul>
            </li>
            <li><b>Nuevo Apartado "Software / Firmware / Drivers" en Biblioteca:</b> Sección especializada dentro de la Biblioteca para catalogar y almacenar instaladores de software, utilidades de PC, paquetes de controladores (drivers USB/RS232) y volcados de firmware (`.bin`, `.hex`, `.iso`, `.zip`, `.exe`, `.deb`, `.appimage`, `.ino`, `.elf`, etc.):
                <ul style='margin-top: 2px;'>
                    <li>Almacenamiento dedicado e indexado automáticamente en `<agenda>/biblioteca/Software/`.</li>
                    <li>Asignación cruzada a cualquier elemento de los módulos de Laboratorio (Instrumentos, Componentes, Herramientas, Insumos, Análisis y Proyectos).</li>
                    <li>Botón de acción directa <i>"Abrir / Ejecutar Software"</i> en la ficha del archivo para instalación o apertura inmediata.</li>
                </ul>
            </li>
            <li><b>Soporte Integral para Imágenes AVIF (`.avif`):</b> Compatibilidad ampliada en toda la aplicación para el formato de imagen de última generación AVIF (alta compresión y calidad). Ahora es posible visualizar, cargar y vincular imágenes `.avif` en la Biblioteca, Fichas de Laboratorio, Portada, Notas, Modo Registros, Editores de Proyectos/Desarrollo y exportación a PDF.</li>
            <li><b>Nuevo Plugin "Gestor de Discos y Respaldos":</b> Sección dedicada para gestionar colecciones masivas de discos duros.
                <ul style='margin-top: 2px;'>
                    <li>Registro de características físicas (formato, capacidad, tecnología) y categorización de contenido.</li>
                    <li>Campo identificador "Número de Disco" y administrador de "Tipos de disco" configurables.</li>
                    <li>Escáner integrado que construye y memoriza un árbol jerárquico de directorios para saber qué contiene cada disco sin conectarlo.</li>
                    <li>Filtros y menú de ordenamiento (A-Z, cronológico y por Número de Disco) integrado en la barra lateral.</li>
                </ul>
            </li>
            <li><b>Nuevo Plugin "Retro":</b> Módulo dedicado para coleccionistas de computación retro (Atari de 8/16 bits, Commodore, ZX Spectrum, MSX, etc.).
                <ul style='margin-top: 2px;'>
                    <li>Gestión organizada de <b>Equipos y Consolas</b>, <b>Medios</b> (Cartuchos, Disquetes, Casetes), <b>Periféricos</b> y <b>Modificaciones/Repuestos</b>.</li>
                    <li>Seguimiento específico del estado funcional (100% Funcional, Muerto, En restauración), condición estética, número de serie y valor estimado.</li>
                    <li>Icono SVG temático inspirado en el diseño de un Atari clásico.</li>
                </ul>
            </li>
            <li><b>Biblioteca Documental Retro:</b> Nuevo apartado para agregar imágenes, manuales, datasheets, esquemas y diagramas a la colección retro. Permite asignar archivos a Equipos, Medios, Periféricos, Mods o Proyectos mediante casillas de verificación, almacenamiento automático en la agenda (`retro/biblioteca/`), previsualización de imágenes y PDFs, y botón para abrir archivos físicos con el visor del sistema.</li>
            <li><b>Almacenamiento de ROMs y Software:</b> Nuevo apartado dedicado para organizar volcados de ROMs, imágenes de disco (ATR, D64, ADF), casetes (CAS, TAP) y ejecutables binarios. Permite asociar estos archivos digitales a su medio físico correspondiente (cartucho, disquete) y vincular portadas o carátulas desde la Biblioteca. Incluye botón directo para ejecutar o abrir el archivo ROM con el emulador del sistema operativo.</li>
            <li><b>Desarrollo y Proyectos Retro:</b> Integración completa de la suite de editores avanzados (Visor 3D STL, Editor Esquemático, Visor KiCad/Gerber, Mapa Mental, IDE de Código, etc.) para documentar restauraciones de hardware y modificaciones electrónicas.</li>
            <li><b>Editor de Diagramas Esquemáticos:</b> Añadidos tubos o válvulas al vacío (Válvula Triodo) al catálogo de componentes para la captura de circuitos retro o de audio.</li>
            <li><b>Pestaña "Secciones y Pestañas" en Configuración:</b> Nueva pestaña en <i>Opciones ➔ Configuración</i> para activar/desactivar la visibilidad de cualquier sección de la agenda, reordenar solapas y renombrar de forma personalizada los títulos de las pestañas. Por defecto todas las secciones están habilitadas.</li>
            <li><b>Mejora en UI de Pestañas:</b> Orden natural 3D para el bloque de solapas derechas anclado al margen inferior de la agenda para mayor realismo con agendas físicas.</li>
        </ul>
        <h3 style='color: #89b4fa; margin-bottom: 4px;'>v.2.10 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Editor de Diagramas Esquemáticos Electrónicos (`SchematicEditorWidget`):</b> Entorno CAD 2D avanzado para captura de circuitos electrónicos en Desarrollo y Proyectos:
                <ul style='margin-top: 2px;'>
                    <li><b>Simbología Vectorial IEEE/IEC Ampliada:</b> Pasivos (R, C, C_POL, L, RV), Osciladores de cristal (2P, 3P, 4P), Varistores (MOV), Dispositivos de Descarga (GDT), Fusibles Rearmables (PPTC), Diodos TVS Uni/Bidireccionales, Transistores, Circuitos Integrados (OpAmp, NE555, LM7805, LM317, LM338K, ICL7106, ICL7107, ICL7135, LM736, ICL7660) y VCC/GND.</li>
                    <li><b>Snapping Magnético y Conexión sin Espacios:</b> Fijación automática del cable al centro exacto del pin (radio 15px) con indicador verde visual. Adaptación dinámica del trazado al mover o rotar componentes (`R`).</li>
                    <li><b>Handles de Edición y Trazado (KiCad / QElectrotech):</b> Tiradores interactivos en extremos y esquinas para ajustar la trayectoria de los cables y adición de vértices mediante doble clic.</li>
                    <li><b>Diseño de CI y Etiquetas de Pines:</b> Nombre/valor del CI centrado dentro del cuerpo del circuito integrado y números/nombres impresos en cada pin (1, 2, VCC, GND, TRIG, OUT, etc.).</li>
                    <li><b>Edición Doble Clic y Menú Contextual:</b> Ventana emergente `SchematicComponentEditDialog` con tabla de edición de pines y vista previa en tiempo real. Menú contextual con clic derecho para rotar (R), editar y eliminar.</li>
                    <li><b>Estructura de Almacenamiento Correcta:</b> Guardado atómico dentro de la subcarpeta del proyecto (`<agenda>/laboratorio/desarrollo/<proyecto>/<id>/schematic.json`) e imagen de previsualización `preview.png`.</li>
                    <li><b>Análisis y Exportación:</b> Generador automático de Lista de Materiales (BOM), Netlist SPICE e imagen PNG.</li>
                </ul>
            </li>
            <li><b>Centro de Ayuda e Instrucciones Interactivas:</b> Rediseño completo del diálogo de Instrucciones (menú <i>Ayuda ➔ Instrucciones</i> o tecla <code>F1</code>) en un Centro de Ayuda interactivo organizado en 15 categorías con buscador en tiempo real.</li>
            <li><b>Sincronización de Red y Conectividad:</b>
                <ul style='margin-top: 2px;'>
                    <li><b>Botón de Sincronización en Barra de Herramientas:</b> Nuevo icono directo de sincronización (`sync.svg`) para ejecutar la actualización de datos entre Cliente y Servidor en segundo plano.</li>
                    <li><b>Sincronización de Logotipo e Imagen de Portada:</b> Transferencia y detección automática en cliente/servidor del logotipo personalizado de la aplicación y la imagen frontal de la portada.</li>
                </ul>
            </li>
            <li><b>PDF de Listas de Chequeo de Herramientas:</b> Optimización del diseño en la exportación PDF reemplazando tablas por listados en columnas con casillas de verificación (checkboxes).</li>
            <li><b>Integración de Documentación Biblioteca a Proyectos (`LibraryDocViewerWidget`):</b> Sincronización bidireccional entre la Biblioteca y Desarrollo/Proyectos con visor especializado y botón directo <b>`📂 Abrir Archivo Físico`</b>.</li>
        </ul>
        <h3 style='color: #89b4fa; margin-bottom: 4px;'>v.2.9 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Asistente de IA Flotante & Capacidad de Agente (`AIAssistantDialog`):</b> Nueva herramienta en el menú Utilidades (`Ctrl+Shift+I`) y la barra de herramientas principal. Abre una ventana flotante independiente (con traba `📌 Trabar Arriba` sobre la agenda) que permite:
                <ul style='margin-top: 2px;'>
                    <li><b>Conexión a Modelos de IA Locales:</b> Integración directa con <b>LM Studio</b> (OpenAI API), <b>Ollama</b> (API Nativa) y servidores OpenAI personalizados.</li>
                    <li><b>Capacidad de Agente Autónoma (`AgentToolsManager`):</b> Inspección en tiempo real de los datos de la agenda (componentes de laboratorio, proyectos de desarrollo, notas, inventario y métricas).</li>
                    <li><b>Copia Rápida de Respuestas y Código:</b> Botones dedicados `💻 Copiar Código #N` en bloques de código y `📋 Copiar Respuesta` completa.</li>
                    <li><b>Prompts Rápidos y Exportación:</b> Botones de consulta rápida y exportación del historial de chat a formato Markdown (`.md`).</li>
                </ul>
            </li>
            <li><b>Pestaña de Configuración IA (`Opciones ➔ Configuración`):</b> Nueva pestaña <b>"🤖 IA (Inteligencia Artificial)"</b> para configurar endpoints de LM Studio/Ollama, token/API Key, detector automático de modelos (`🔍 Buscar Modelos`), probador de conexión (`⚡ Probar Conexión`), temperatura, max tokens y prompt del sistema.</li>
            <li><b>Suite IDE de Código Avanzada:</b> Evolución completa del editor de código en Desarrollo y Proyectos con resaltado de sintaxis para 10 lenguajes, plantillas base, panel interactivo de Buscar/Reemplazar (`Ctrl+F` / `Ctrl+H`), comentarios inteligentes, duplicar líneas y barra de estado.</li>
            <li><b>Editor de Dibujo Estilo Paint (`PaintEditorWidget`):</b> Lienzo gráfico interactivo (1280x720) integrado con herramientas de Lápiz, Pincel, Líneas, Cuadros, Elipses, Relleno de Color (Flood Fill), Goma de Borrar, Texto, Grosor de trazo, Muestras de color, Carga e Importación de Fotos y pila completa de Deshacer/Rehacer (`Ctrl+Z`).</li>
            <li><b>Visor de Archivos 3D STL y G-Code (`STL3DViewerWidget`):</b> Visualizador 3D CAD interactivo para archivos `.stl` (Sólido Sombreado y Malla Wireframe) con cámara 360° orbital, cálculo de dimensiones/volumen y visor de trayectorias G-Code (`.gcode` / `.g`) cortado capa por capa mediante slider Z.</li>
            <li><b>Integración de Documentación desde Biblioteca a Proyectos (`LibraryDocViewerWidget`):</b> Vinculación bidireccional entre la Biblioteca y los Proyectos de Desarrollo / Análisis:
                <ul style='margin-top: 2px;'>
                    <li><b>Asignación desde Biblioteca:</b> Nueva opción <b>"Desarrollo y Proyectos"</b> en la <i>Categoría Destino</i> al subir o editar archivos en la Biblioteca, desplegando el listado dinámico de proyectos activos para marcar mediante casillas.</li>
                    <li><b>Nuevo Módulo 'Documentación Biblioteca':</b> Herramienta seleccionable en los proyectos para ver todos los manuales, datasheets, imágenes o libros vinculados con botón directo <b>`📂 Abrir Archivo Físico`</b>.</li>
                </ul>
            </li>
            <li><b>Editor de Diagramas Esquemáticos Electrónicos (`SchematicEditorWidget`):</b> Entorno interactivo 2D para captura de esquemas circuitales con rejilla CAD (Snap-to-Grid 10px), biblioteca de símbolos vectoriales IEEE/IEC (Pasivos R/C/L, Diodos, Transistores NPN/PNP, OpAmp, NE555, LM7805, VCC/GND), trazado de cables ortogonales a 90° con puntos de unión junction, etiquetas de red (Net Labels), rotación (tecla `R`), edición rápida de designador/valor, generador de Lista de Materiales (BOM), exportador de Netlist (SPICE/SKiDL) y guardado en JSON / PNG.</li>
            <li><b>Visor de Proyectos KiCad y Gerber Multicapa (`GerberKiCadViewerWidget`):</b> Inspección vectorial para proyectos PCB KiCad (`.kicad_pcb`, `.kicad_sch`) y capas Gerber (`.gbr`, `.gtl`, `.gbl`, `.drl`, `.zip`), con gestor de capas de visibilidad individual, regla interactiva para medir distancias en mm/pulgadas y temas visuales de PCB.</li>
        </ul>
        <h3 style='color: #89b4fa; margin-bottom: 4px;'>v.2.8 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Nuevo Módulo Desarrollo y Proyectos con Herramientas Especializadas:</b> Integración de un gestor de proyectos dentro de la sección de Laboratorio con Texto Enriquecido, Editor IDE de Código, Mapa Mental interactivo con recuadros redimensionables, Diagrama de Flujo con soporte e importación/exportación Draw.io (`.drawio` / `.xml`), Texto Plano e Imágenes.</li>
            <li><b>Inclusión de Herramientas Flotantes en Empaquetado:</b> Inclusión de la carpeta `tools/` en la construcción de paquetes de distribución (`.deb` y `.flatpak`), asegurando la ejecución fluida del Conversor de Unidades y la Calculadora instaladas a nivel de sistema.</li>
            <li><b>Migración de Emojis a Iconos Vectoriales SVG en Calculadora:</b> Reemplazo completo de emojis por iconos SVG escalables (`calculator.svg`, `chart.svg`, `lab.svg`, `copy.svg`, `history.svg`, `ruler.svg`, `component.svg`) en la interfaz de la calculadora flotante.</li>
            <li><b>Módulo de Análisis en Laboratorio:</b> Incorporación de un gestor de análisis técnicos. Permite organizar estudios por categorías e integrar cálculos adjuntos mediante un editor a pantalla completa interactivo con soporte para texto plano, imágenes y edición en Markdown.</li>
            <li><b>Exportación PDF de Inventario:</b> Nueva herramienta accesible desde el menú Editar y la barra de Herramientas. Genera listados profesionales en PDF con prefijo correlativo "INFO-" según la vista actual de Bodega (Stock, Saldos, Costos o Consolidado) y permite filtrar por nivel de existencias y costos.</li>
            <li><b>Nuevo Módulo de Gastos:</b> Implementación de un plugin completo para la gestión de cuentas independientes con soporte multidivisa. Permite registrar transacciones financieras y organizar presupuestos mensuales.</li>
            <li><b>Gestor Global de Correlativos:</b> Herramienta centralizada en el menú Opciones para administrar secuencias documentales en toda la agenda. Permite configurar prefijos personalizados (ej: CHK-) y mantener un conteo continuo ininterrumpido (hasta 999) aplicable para múltiples tipos de informes, facturas y checks.</li>
            <li><b>Paginación y Adaptabilidad en Biblioteca:</b> Refactorización de la vista izquierda de la biblioteca para calcular matemática y automáticamente la cantidad de tarjetas visibles según la altura de la pantalla, unificando la lógica con la sección de Laboratorio.</li>
            <li><b>Personalización de Resultados de Chequeo:</b> La lista desplegable de "Resultado / Estado" de la ventana de chequeos ahora es totalmente configurable desde la sección de configuración del Laboratorio.</li>
            <li><b>Generador de Reportes PDF:</b> Nuevo exportador integrado en los detalles de las listas de chequeos completados. Construye reportes de mantenimiento técnicos e imprimibles (vía FPDF2) incorporando el título de la agenda, logotipo corporativo SVG nativo, fotografía de la herramienta y resultados del chequeo.</li>
        </ul>
        <h3 style='color: #cba6f7; margin-bottom: 4px;'>v.2.7 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Función de Restauración de Respaldos:</b> Incorporación en la pestaña "Respaldos" de un gestor de descompresión. Permite seleccionar el archivo de respaldo, confirmar la operación cerrando la agenda en caliente, extraer los datos (.zip, .rar, .7z, .arj) y recargarla automáticamente en la interfaz.</li>
            <li><b>Listas de Chequeo (Check Lists) en Laboratorio:</b> Nueva sección de creación y administración de listas estructuradas por grupos, permitiendo la asignación múltiple (casillas de verificación) sobre varios elementos inventariados de cualquier categoría simultáneamente (ej: un único checklist de rutina para todos los alicates).</li>
            <li><b>Secuencial Correlativo Mensual (AAMMNNN):</b> Autogeneración de códigos correlativos para chequeos con persistencia local en `laboratorio/correlativos.json`. El contador se ajusta a la fecha seleccionada y se reinicia si cambia el mes o si alcanza la marca de 999.</li>
            <li><b>Registro y Visor de Históricos:</b> Pantalla de inspección para marcar ítems en tiempo real al registrar eventos, y visor interactivo de sólo lectura al hacer doble clic sobre cualquier celda del historial de la ficha técnica.</li>
        </ul>
        <h3 style='color: #cba6f7; margin-bottom: 4px;'>v.2.6 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Gestión de Respaldos de la Agenda:</b> Nueva pestaña "Respaldos" en el panel de Configuración que permite realizar respaldos instantáneos de la agenda abierta. Soporta definición de nombre del archivo y ruta de destino de almacenamiento.</li>
            <li><b>Formatos y Compresión Multivolumen:</b> Compresión nativa en formato ZIP y soporte para herramientas del sistema (7ZIP, RAR, ARJ). Permite además activar la opción de dividir el archivo resultante en volúmenes definiendo su tamaño en MB.</li>
            <li><b>Arreglos en Reapertura de Diálogos:</b> Corrección del bug que impedía abrir la calculadora o el conversor de unidades una vez que se habían cerrado, logrando además que preserven sus datos en memoria tras ocultarse.</li>
            <li><b>Fórmula de Disipación Térmica:</b> Adición en la calculadora del cálculo completo de disipadores de calor (temperatura de unión, resistencia térmica del disipador Rsa, potencia disipada y temperatura ambiente máxima).</li>
        </ul>
        <h3 style='color: #a6e3a1; margin-bottom: 4px;'>v.2.5 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Nuevas Ventanas Flotantes de Herramientas:</b> Adición en el menú Editar de un "Conversor de Unidades" físico/AWG/binario-hex y una "Calculadora" integrada con tres pestañas (Básica con historial, Científica completa y Electrónica/Eléctrica avanzada). Las ventanas se ejecutan de manera asíncrona y no modal.</li>
            <li><b>Módulo de Ecuaciones de Laboratorio:</b> Implementación de más de 38 fórmulas analógicas, digitales y misceláneas con resolución en tiempo real, copia formateada al portapapeles y limpieza rápida.</li>
            <li><b>Nuevas Fórmulas de Ingeniería:</b> Integración de conversiones Rectangular a Polar, filtros Pasa Bajos/Banda/Altos (EMI), ganancias de tensión y corriente en decibelios (dB), sumas complejas AC+DC, potencia en dBm con resistencia de referencia dinámica y cálculo de mallas por determinantes (Regla de Cramer 2x2 y 3x3).</li>
            <li><b>Selector Interactivo de Código de Colores:</b> Visualizador dinámico de bandas que ahora soporta resistencias de 4, 5 y 6 bandas (añadiendo coeficiente de temperatura PPM/K).</li>
            <li><b>Compuertas Lógicas Digitales:</b> Probador lógico visual para AND, OR, NAND, NOR, XOR, XNOR, NOT que incluye el despliegue automático de sus respectivas tablas de verdad.</li>
        </ul>
        <h3 style='color: #cba6f7; margin-bottom: 4px;'>v.2.4 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Logotipo Personalizado de la Aplicación:</b> Opción en Opciones &gt; Configuración &gt; pestaña General para cargar un archivo de imagen. El logo se mostrará de forma dinámica en la parte superior de la barra lateral en la sección Portada.</li>
            <li><b>Estabilización de Componentes de Interfaz:</b> Corrección del refresco del layout de listados de Laboratorio, Biblioteca, Notas, Tareas y Planificador para evitar que queden widgets fantasma ("copias") de componentes o libros antiguos al cambiar rápidamente de sección o pestaña.</li>
            <li><b>Ayuda de Usuario Actualizada:</b> Guía de instrucciones enriquecida para reflejar las nuevas funciones añadidas en las últimas versiones.</li>
            <li><b>Estilización de Alertas en Bodega:</b> Corrección de contraste del encabezado de la tabla de stock crítico del balance consolidado y ajuste en la visualización de anchos de columna para evitar el truncado de nombres de insumos o componentes.</li>
        </ul>
        <h3 style='color: #f9e2af; margin-bottom: 4px;'>v.2.3 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Herramienta de Conectividad y Sincronización de Red:</b> Modo Servidor para compartir la agenda localmente con contraseña, control de seguridad (bloquear/desconectar IPs) e historial físico persistente. Modo Cliente para sincronizaciones asíncronas bidireccionales, de subida y de bajada con barra de progreso.</li>
            <li><b>Validación de Versión y Prerrequisitos en Red:</b> Exigencia de tener una agenda abierta para abrir la conectividad y alertas preventivas de discrepancia de versión (versión cruzada entre Cliente/Servidor) para evitar la inconsistencia de datos.</li>
            <li><b>Indicador de Espacio en Disco:</b> Medición en tiempo real y visualización del espacio físico ocupado en disco por la carpeta de la agenda, tanto local como en el servidor.</li>
            <li><b>Auto-Guardado Inteligente y Confirmación Visual:</b> Grabación atómica instantánea a disco al crear, editar o eliminar elementos en todas las secciones, eliminando la dependencia del botón de guardado. Se agregaron notificaciones de confirmación de 3 segundos en la barra de estado inferior (ej. *✓ Notas: Cambios auto-guardados correctamente* o alertas con *❌* en caso de fallos).</li>
            <li><b>Previsualización de Documentos PDFs:</b> Integración con PyMuPDF (`fitz`) para renderizar y mostrar la primera página de archivos PDF en el panel de previsualización de Biblioteca y Laboratorio.</li>
            <li><b>Valoración Financiera y Gestión de Costos:</b> Entrada de Costo Unitario en registros de Bodega, edición directa de Costo y Stock Mínimo en ficha técnica, valorización del stock y selección de divisa (CLP, USD, EUR) en configuración general.</li>
            <li><b>Sub-vistas y Reporte Consolidado en Bodega:</b> Pestañas laterales exclusivas en la barra lateral para alternar entre Vista de Stock, Vista de Saldos (con ubicaciones/presentaciones), Vista de Costos y Balance Consolidado (reporte general y tabla de elementos bajo el mínimo).</li>
            <li><b>Monitoreo de Espacio en Portada:</b> Despliegue en la barra lateral de la Portada del peso de la agenda y el espacio libre remanente de la partición del disco local.</li>
            <li><b>Silenciamiento de Advertencias de GLib (Linux):</b> Redirección y descarte silencioso (`/dev/null`) de advertencias de consola críticas de visores externos (como *xreader*) al abrir manuales o hojas de datos en la Biblioteca y Laboratorio.</li>
            <li><b>Iconos del Menú Archivo:</b> Nuevos iconos claros vectoriales en blanco hueso para las opciones "Guardar Como..." y "Cerrar" del menú superior.</li>
            <li><b>Paginación Autodinámica en Laboratorio:</b> Ajuste dinámico de tarjetas por página en tiempo real basado en el alto visible de la ventana, eliminando las barras de desplazamiento verticales para preservar la estética de papel física.</li>
            <li><b>Botón de Recargar y Estado de Red:</b> Botón de recarga en caliente en la barra de herramientas superior e indicación en tiempo real del estado de red en la barra de estado inferior (Local, Servidor Activo o Cliente Sincronizado).</li>
            <li><b>Barra de Herramientas 100% SVG:</b> Migración completa de los botones de navegación y recarga a iconos vectoriales SVG unificados en color blanco hueso.</li>
            <li><b>Gestión de Listas y Configuración en Laboratorio:</b> Nueva pestaña "Listas" en la configuración de Laboratorio para editar, agregar y eliminar opciones desplegables con verificación de dependencias de inventario activa y guardado automático en el directorio de la agenda.</li>
            <li><b>Estado Operativo de Instrumentos:</b> Incorporación del campo "Estado Operativo" y personalización de sus opciones en el inventario.</li>
            <li><b>Nuevas Categorías en Biblioteca:</b> Soporte y carpetas de almacenamiento para *Libros*, *Revistas* e *Información Técnica* con prefijos de indexación física automática.</li>
            <li><b>Sincronización de Cumpleaños en Calendario:</b> Reflejo interactivo automático de cumpleaños y aniversarios en todas las vistas de Calendario, indicando la edad correspondiente al año visualizado.</li>
            <li><b>Ayuda y Licencia:</b> Nueva sección de Licencia MIT y reescritura de la Guía de Uso del Proyecto.</li>
            <li><b>Mejoras Visuales y de Contraste:</b> Optimización del panel de asignación en Biblioteca para modo oscuro, unificación del diseño de botones y corrección del contraste de iconos en Notas y Tareas, con legibilidad mejorada en el Kardex y en los diálogos de ingreso de bodega.</li>
        </ul>
        <h3 style='color: #a6e3a1; margin-bottom: 4px; margin-top: 12px;'>v.2.2 - Julio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Modo Panorámico a Página Única:</b> Opción en la configuración del Planificador para mostrar el diagrama Gantt sin encuadernación, aprovechando todo el ancho de la pantalla (como en el Lotus Organizer original), con botón de salida.</li>
            <li><b>Mejora Visual en Pestañas:</b> Texto en color blanco para mejor contraste (en negrita para la pestaña activa), reducción del ancho a 26 píxeles para acomodar mayor densidad, y sistema dinámico automático de pestañas escalonadas en 2 o más columnas cuando se agregan nuevas secciones.</li>
            <li><b>Reemplazo de Emojis por SVG Vectoriales:</b> Reemplazo total de emojis nativos por iconos SVG escalables y personalizables en las secciones de Tareas y Proyectos, y Cumpleaños, mejorando el estilo visual del entorno de escritorio.</li>
        </ul>
        <h3 style='color: #89b4fa; margin-bottom: 4px; margin-top: 12px;'>v.2.1 - Junio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Gestor de Proyectos y Carta Gantt (Planificador):</b> Diagrama Gantt estilo matriz Lotus Organizer con modo panorámico continuo de 2 páginas.</li>
            <li><b>Sección Laboratorio de Electrónica:</b> Gestión integral de Componentes, Instrumentos, Herramientas e Insumos con historial de calibraciones.</li>
            <li><b>Sección Biblioteca Documental:</b> Almacenamiento e indexación automática de archivos en carpetas físicas (Manuales, Datasheets, MSDS, Imágenes) vinculados a Laboratorio.</li>
            <li><b>Reordenador de Pestañas de la Agenda:</b> Herramienta en Configuración &gt; General para reordenar libremente las pestañas laterales del cuaderno en tiempo real.</li>
            <li><b>Nuevos Iconos SVG Vectoriales:</b> Iconos vectoriales locales integrados para toda la interfaz (Multímetro, Componentes, Herramientas, Insumos).</li>
        </ul>
        <h3 style='color: #cba6f7; margin-bottom: 4px; margin-top: 12px;'>v.2.0 - Junio 2026</h3>
        <ul style='margin-top: 4px; line-height: 1.5;'>
            <li><b>Diseño Esqueumórfico Moderno:</b> Rediseño completo imitando una agenda de papel física Lotus Organizer sobre tapete de escritorio de fieltro verde.</li>
            <li><b>Sistema de Encuadernación Intercambiable:</b> Selección desde configuración entre Anillas metálicas 3D aplanadas, Espiral metálico con perforaciones finas, Clip o Sin encuadernación.</li>
            <li><b>Pestañas/Solapas Físicas:</b> Pestañas laterales integradas al lomo con comportamiento interactivo entre páginas izquierdas y derechas.</li>
            <li><b>Efecto de Hojas Apiladas:</b> Renderizado de volumen y perspectiva en los bordes para simular el grosor real del libro.</li>
            <li><b>Vistas de Calendario completas:</b> Implementación de 5 modos de visualización: Día, Semana, Mes, Semestre y Año a la vista.</li>
            <li><b>Gestión de Eventos:</b> Diálogo interactivo para agregar eventos por Inicio/Duración, Periodo o Jornada Completa.</li>
            <li><b>Configuración de Jornada Laboral:</b> Acceso rápido mediante botón de engranaje en la barra lateral.</li>
            <li><b>Papelera 3D:</b> Cesto metálico en tres dimensiones con estado dinámico de papel reciclado.</li>
            <li><b>Navegación Rápida:</b> Indicador de fecha fija con retorno rápido al día actual al hacer clic.</li>
        </ul>
        """
        text.setHtml(changelog_html)
        layout.addWidget(text)

        btn_close = QPushButton("Cerrar")
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)


class LicenseDialog(QDialog):
    """Diálogo con la licencia MIT de la aplicación."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Licencia MIT - Vito Organizer")
        self.resize(520, 400)
        self.setStyleSheet("""
            QDialog { background-color: #181825; color: #cdd6f4; font-family: 'Segoe UI', sans-serif; }
            QLabel { background: transparent; border: none; color: #cdd6f4; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 4px; padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background-color: #89b4fa; color: #111; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'icons')
        doc_img = f"<img src='{os.path.join(icons_dir, 'document.svg')}' width='20' height='20'>"
        title = QLabel(f"{doc_img} <b>Licencia de Software</b>")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #f9e2af;")
        layout.addWidget(title)

        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
                font-family: monospace;
            }
        """)

        mit_license = """
        <p><b>MIT License</b></p>
        <p>Copyright (c) 2026 Vitokin</p>
        <p>Permission is hereby granted, free of charge, to any person obtaining a copy
        of this software and associated documentation files (the "Software"), to deal
        in the Software without restriction, including without limitation the rights
        to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
        copies of the Software, and to permit persons to whom the Software is
        furnished to do so, subject to the following conditions:</p>
        <p>The above copyright notice and this permission notice shall be included in all
        copies or substantial portions of the Software.</p>
        <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
        IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
        AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
        OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
        SOFTWARE.</p>
        """
        text.setHtml(mit_license)
        layout.addWidget(text)

        btn_close = QPushButton("Aceptar")
        btn_close.setObjectName("primaryButton")
        btn_close.setDefault(True)
        btn_close.setFixedWidth(100)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

