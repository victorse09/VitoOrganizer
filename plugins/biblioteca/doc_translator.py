# =============================================================================
# Vito Organizer v2.2 - Biblioteca: Traductor Técnico de Documentos
# Motor y Diálogo de Traducción Especializada en Electrónica e Ingeniería
# =============================================================================

import os
import re
import json
import urllib.request
import urllib.parse
import urllib.error
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QClipboard, QGuiApplication
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QLineEdit, QComboBox, QSplitter, QProgressBar, QMessageBox, QFileDialog,
    QFrame, QSpinBox, QCheckBox, QWidget, QInputDialog
)

from config.settings import Settings


def get_themed_svg_icon(icon_path: str, color_hex: str = "#0D47A1", size: int = 18) -> QIcon:
    """Carga un archivo SVG y colorea trazos/rellenos con color_hex."""
    if not os.path.exists(icon_path):
        return QIcon()
    try:
        from PyQt6.QtSvg import QSvgRenderer
        from PyQt6.QtCore import QByteArray
        from PyQt6.QtGui import QPixmap, QPainter
        with open(icon_path, 'r', encoding='utf-8') as f:
            content = f.read()
        content = re.sub(r'stroke="(?!none)[^"]+"', f'stroke="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'stroke:\s*(?!none)[^;"]+', f'stroke:{color_hex}', content, flags=re.IGNORECASE)
        content = re.sub(r'fill="(?!none)[^"]+"', f'fill="{color_hex}"', content, flags=re.IGNORECASE)
        content = re.sub(r'fill:\s*(?!none)[^;"]+', f'fill:{color_hex}', content, flags=re.IGNORECASE)

        renderer = QSvgRenderer(QByteArray(content.encode('utf-8')))
        pix = QPixmap(size, size)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        return QIcon(pix)
    except Exception:
        return QIcon(icon_path)


# =============================================================================
# 1. MOTOR DE TRADUCCIÓN TÉCNICA OFFLINE LOCAL (Electrónica e Ingeniería)
# =============================================================================

class TechnicalElectronicsTranslator:
    """
    Motor local de traducción y normalización técnica especializado en electrónica,
    diseño de circuitos, microcontroladores y hardware.
    Funciona 100% offline sin dependencias externas.
    """

    TECHNICAL_DICT = {
        # Componentes y Dispositivos
        "operational amplifier": "amplificador operacional",
        "op-amp": "amplificador operacional",
        "op amp": "amplificador operacional",
        "voltage regulator": "regulador de voltaje",
        "power supply": "fuente de alimentación",
        "switching regulator": "regulador conmutado",
        "linear regulator": "regulador lineal",
        "low-dropout regulator": "regulador de baja caída (LDO)",
        "low dropout": "baja caída (LDO)",
        "microcontroller": "microcontrolador",
        "microprocessor": "microprocesador",
        "integrated circuit": "circuito integrado",
        "printed circuit board": "placa de circuito impreso (PCB)",
        "surface mount device": "dispositivo de montaje superficial (SMD)",
        "through-hole": "orificio pasante (THT)",
        "light emitting diode": "diodo emisor de luz (LED)",
        "zener diode": "diodo zener",
        "schottky diode": "diodo schottky",
        "bridge rectifier": "puente rectificador",
        "decoupling capacitor": "condensador de desacoplo",
        "bypass capacitor": "condensador de bypass",
        "bulk capacitor": "condensador de filtrado principal",
        "pull-up resistor": "resistencia de pull-up",
        "pull-down resistor": "resistencia de pull-down",
        "current sensing resistor": "resistencia de sensado de corriente",
        "shunt resistor": "resistencia shunt",
        "heatsink": "disipador térmico",
        "heat sink": "disipador de calor",
        "crystal oscillator": "oscilador de cristal",
        "quartz crystal": "cristal de cuarzo",
        "pulse width modulation": "modulación por ancho de pulsos (PWM)",
        "analog to digital converter": "conversor analógico-digital (ADC)",
        "digital to analog converter": "conversor digital-analógico (DAC)",
        "logic gate": "compuerta lógica",
        "shift register": "registro de desplazamiento",
        "bandgap reference": "referencia bandgap",
        "voltage reference": "referencia de tensión",

        # Parámetros y Magnitudes Eléctricas
        "input voltage": "tensión de entrada",
        "output voltage": "tensión de salida",
        "input current": "corriente de entrada",
        "output current": "corriente de salida",
        "quiescent current": "corriente de reposo",
        "leakage current": "corriente de fuga",
        "supply voltage": "tensión de alimentación",
        "operating voltage": "tensión de operación",
        "breakdown voltage": "tensión de ruptura",
        "reverse voltage": "tensión inversa",
        "forward voltage": "tensión directa (Vf)",
        "forward bias": "polarización directa",
        "reverse bias": "polarización inversa",
        "threshold voltage": "tensión de umbral",
        "input impedance": "impedancia de entrada",
        "output impedance": "impedancia de salida",
        "cutoff frequency": "frecuencia de corte",
        "resonant frequency": "frecuencia de resonancia",
        "clock frequency": "frecuencia de reloj",
        "sampling rate": "tasa de muestreo",
        "bandwidth": "ancho de banda",
        "gain-bandwidth product": "producto ganancia-ancho de banda (GBW)",
        "slew rate": "velocidad de respuesta (slew rate)",
        "duty cycle": "ciclo de trabajo",
        "ripple voltage": "tensión de rizado",
        "noise figure": "figura de ruido",
        "signal-to-noise ratio": "relación señal a ruido (SNR)",
        "total harmonic distortion": "distorsión armónica total (THD)",
        "power dissipation": "disipación de potencia",
        "thermal resistance": "resistencia térmica",
        "junction temperature": "temperatura de juntura",
        "ambient temperature": "temperatura ambiente",
        "operating temperature range": "rango de temperatura de operación",
        "short circuit protection": "protección contra cortocircuitos",
        "thermal shutdown": "apagado térmico",
        "overcurrent protection": "protección contra sobrecorriente",
        "overvoltage protection": "protección contra sobretensión",
        "reverse polarity protection": "protección contra polaridad inversa",
        "efficiency": "eficiencia",
        "accuracy": "exactitud",
        "precision": "precisión",
        "tolerance": "tolerancia",
        "resolution": "resolución",

        # Pines, Conectores y Hardware
        "pin configuration": "configuración de pines (pinout)",
        "pin description": "descripción de pines",
        "package": "encapsulado",
        "footprint": "huella de montaje",
        "solder pad": "pad de soldadura",
        "ground plane": "plano de masa (GND)",
        "analog ground": "tierra analógica (AGND)",
        "digital ground": "tierra digital (DGND)",
        "enable pin": "pin de habilitación (EN)",
        "chip select": "selección de chip (CS)",
        "clock pin": "pin de reloj (CLK)",
        "data in": "entrada de datos (DIN)",
        "data out": "salida de datos (DOUT)",
        "feedback loop": "lazo de retroalimentación",
        "closed loop": "lazo cerrado",
        "open loop": "lazo abierto",
        "absolute maximum ratings": "valores máximos absolutos",
        "electrical characteristics": "características eléctricas",
        "typical application circuit": "circuito de aplicación típica",
        "block diagram": "diagrama de bloques",
        "schematic diagram": "diagrama esquemático",
        "bill of materials": "lista de materiales (BOM)",
        "datasheet": "hoja de datos (datasheet)",

        # Verbos y Frases Comunes en Hojas Técnicas
        "is connected to": "está conectado a",
        "must be connected to": "debe conectarse a",
        "should be placed": "debe colocarse",
        "recommended value": "valor recomendado",
        "in order to minimize": "para minimizar",
        "in order to prevent": "para evitar",
        "can be adjusted by": "puede ajustarse mediante",
        "is determined by": "está determinado por",
        "is proportional to": "es proporcional a",
        "as shown in figure": "como se muestra en la figura",
        "refer to table": "consulte la tabla",
        "features": "características",
        "applications": "aplicaciones",
        "general description": "descripción general",
        "functional overview": "descripción funcional",
        "design guidelines": "guías de diseño",
        "layout guidelines": "guías de diseño de PCB / trazado",
        "test circuit": "circuito de prueba"
    }

    PATTERNS = [
        (r'\b(the|a|an)\s+', ''),
        (r'\bwith\b', 'con'),
        (r'\bwithout\b', 'sin'),
        (r'\bfrom\b', 'desde'),
        (r'\bto\b', 'a'),
        (r'\bfor\b', 'para'),
        (r'\band\b', 'y'),
        (r'\bor\b', 'o'),
        (r'\bbetween\b', 'entre'),
        (r'\bhigh\b', 'alto'),
        (r'\blow\b', 'bajo'),
        (r'\bwide\b', 'amplio'),
        (r'\bfast\b', 'rápido'),
        (r'\bslow\b', 'lento'),
        (r'\bmaximum\b', 'máximo'),
        (r'\bminimum\b', 'mínimo'),
        (r'\btypical\b', 'típico'),
        (r'\bnominal\b', 'nominal'),
        (r'\bvoltage\b', 'voltaje / tensión'),
        (r'\bcurrent\b', 'corriente'),
        (r'\bpower\b', 'potencia'),
        (r'\bfrequency\b', 'frecuencia'),
        (r'\bresistance\b', 'resistencia'),
        (r'\bcapacitance\b', 'capacitancia'),
        (r'\binductance\b', 'inductancia'),
        (r'\btemperature\b', 'temperatura'),
        (r'\bnoise\b', 'ruido'),
        (r'\bgain\b', 'ganancia'),
        (r'\boutput\b', 'salida'),
        (r'\binput\b', 'entrada'),
        (r'\benable\b', 'habilitar'),
        (r'\bdisable\b', 'deshabilitar'),
        (r'\bconnected\b', 'conectado'),
        (r'\bincreases\b', 'aumenta'),
        (r'\bdecreases\b', 'disminuye'),
        (r'\bconstant\b', 'constante'),
        (r'\brequired\b', 'requerido'),
        (r'\boptional\b', 'opcional')
    ]

    @classmethod
    def translate(cls, text: str) -> str:
        """Traduce texto técnico en inglés a español técnico conservando formato y términos técnicos."""
        if not text or not text.strip():
            return ""

        lines = text.split('\n')
        translated_lines = []

        for line in lines:
            if not line.strip():
                translated_lines.append("")
                continue

            trans = line

            # 1. Reemplazar frases técnicas largas primero (orden descendente de longitud)
            sorted_terms = sorted(cls.TECHNICAL_DICT.items(), key=lambda x: len(x[0]), reverse=True)
            for eng_term, esp_term in sorted_terms:
                pattern = re.compile(r'\b' + re.escape(eng_term) + r'\b', re.IGNORECASE)
                trans = pattern.sub(esp_term, trans)

            # 2. Reemplazar patrones de conexión y enlaces comunes
            for pattern_str, repl_str in cls.PATTERNS:
                p = re.compile(pattern_str, re.IGNORECASE)
                trans = p.sub(repl_str, trans)

            # Limpieza básica
            trans = re.sub(r'\s{2,}', ' ', trans)
            translated_lines.append(trans)

        return '\n'.join(translated_lines)


# =============================================================================
# 2. HILO DE TRABAJO ASÍNCRONO DE TRADUCCIÓN (TranslationWorkerThread)
# =============================================================================

class TranslationWorkerThread(QThread):
    """Ejecuta llamadas de traducción (IA Local, Online o Local Offline) en segundo plano."""
    translation_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)

    def __init__(self, text: str, engine: str = 'ai_local', ai_config: dict = None, parent=None):
        super().__init__(parent)
        self.text = text
        self.engine = engine  # 'ai_local', 'online', 'offline'
        self.ai_config = ai_config or {}

    def run(self):
        try:
            if not self.text or not self.text.strip():
                self.translation_ready.emit("")
                return

            if self.engine == 'ai_local':
                self.status_updated.emit("Conectando con Servidor IA Local (LM Studio / Ollama)...")
                self._translate_ai_local()
            elif self.engine == 'online':
                self.status_updated.emit("Consultando servicio de traducción online...")
                self._translate_online()
            else:
                self.status_updated.emit("Procesando con motor técnico offline local...")
                self._translate_offline()

        except Exception as e:
            # Fallback automático al traductor técnico offline si falló la IA u Online
            print(f"Error en motor '{self.engine}': {e}. Usando respaldo offline técnico...")
            try:
                fallback_trans = TechnicalElectronicsTranslator.translate(self.text)
                self.translation_ready.emit(fallback_trans + f"\n\n*(Nota: Traducido mediante motor técnico offline de respaldo debido a: {e})*")
            except Exception as e2:
                self.error_occurred.emit(f"Error general en la traducción: {e2}")

    def _translate_ai_local(self):
        """Traduce usando LM Studio, Ollama o servidor compatible OpenAI."""
        provider = self.ai_config.get('provider', 'lm_studio')
        endpoint = self.ai_config.get('endpoint', 'http://localhost:1234/v1').rstrip('/')
        model = self.ai_config.get('model', 'qwen2.5-coder-7b-instruct')
        api_key = self.ai_config.get('api_key', 'lm-studio')

        system_prompt = (
            "Eres un traductor técnico profesional experto en ingeniería electrónica, telecomunicaciones, "
            "diseño de hardware, microcontroladores, instrumentación y física de semiconductores.\n"
            "Traduce fielmente el siguiente texto del inglés al español técnico.\n\n"
            "REGLAS TÉCNICAS OBLIGATORIAS:\n"
            "1. Traduce con máxima precisión técnica y claridad en español neutro.\n"
            "2. NO traduzcas acrónimos y términos estándar de la industria (PCB, IC, MOSFET, BJT, SMD, SMT, PWM, "
            "SPI, I2C, UART, CAN, Datasheet, Pull-up, Pull-down, Bypass, Ripple, Forward Bias, Reverse Bias, ESR, "
            "Dropout, Pinout, Footprint, Vcc, Vdd, GND, etc.).\n"
            "3. Conserva exactamente las unidades de medida (V, mV, µV, A, mA, µA, Ω, kΩ, MΩ, pF, nF, µF, H, mH, "
            "µH, Hz, kHz, MHz, GHz, W, mW, dB, dBm, °C, PPM, etc.), fórmulas matemáticas y referencias a componentes (R1, C1, U1, Q1).\n"
            "4. Devuelve ÚNICAMENTE la traducción limpia al español técnico, sin introducciones, saludos ni comentarios."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Texto a traducir:\n\n{self.text}"}
        ]

        if provider == "ollama":
            url = f"{endpoint}/api/chat"
            payload = json.dumps({
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 4096}
            }).encode('utf-8')
        else:  # LM Studio / OpenAI
            url = f"{endpoint}/chat/completions"
            payload = json.dumps({
                "model": model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 4096
            }).encode('utf-8')

        req = urllib.request.Request(
            url, data=payload,
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'VitoOrganizer/2.12 (TechnicalTranslator)'
            }
        )

        with urllib.request.urlopen(req, timeout=90) as resp:
            res_data = json.loads(resp.read().decode('utf-8'))
            if provider == "ollama":
                content = res_data.get('message', {}).get('content', '')
            else:
                choices = res_data.get('choices', [])
                content = choices[0].get('message', {}).get('content', '') if choices else ''

            if content.strip():
                self.translation_ready.emit(content.strip())
            else:
                raise ValueError("El modelo IA devolvió una respuesta vacía.")

    def _translate_online(self):
        """Traduce usando servicio libre online con división por bloques."""
        paragraphs = [p.strip() for p in self.text.split('\n\n') if p.strip()]
        if not paragraphs:
            paragraphs = [self.text]

        results = []
        for p in paragraphs:
            # Dividir en trozos de máx 450 caracteres para la API libre
            chunks = [p[i:i+450] for i in range(0, len(p), 450)]
            p_trans = []
            for chunk in chunks:
                url = 'https://api.mymemory.translated.net/get?' + urllib.parse.urlencode({
                    'q': chunk,
                    'langpair': 'en|es'
                })
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (VitoOrganizer/2.12)'})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                    t = data.get('responseData', {}).get('translatedText', '')
                    p_trans.append(t if t else chunk)
            results.append(" ".join(p_trans))

        self.translation_ready.emit("\n\n".join(results))

    def _translate_offline(self):
        """Traduce usando el motor técnico de reglas y léxico especializado offline."""
        translated = TechnicalElectronicsTranslator.translate(self.text)
        self.translation_ready.emit(translated)


# =============================================================================
# 3. DIÁLOGO INTERACTIVO DE TRADUCCIÓN TÉCNICA (DocTranslateDialog)
# =============================================================================

class DocTranslateDialog(QDialog):
    """Diálogo completo para traducción de texto seleccionado, OCR o páginas al español."""
    
    def __init__(self, source_text: str = "", doc_context: dict = None, parent=None):
        super().__init__(parent)
        self.source_text = source_text
        self.doc_context = doc_context or {} # {'doc': fitz_doc, 'current_page': int, 'total_pages': int}
        self.worker = None

        self.setWindowTitle("🌐 Traductor Técnico de Documentación — Vito Organizer")
        self.resize(880, 580)
        self.setMinimumSize(700, 460)
        self.icons_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'icons')

        self.setStyleSheet("""
            QDialog { background-color: #1E1E2E; color: #CDD6F4; font-family: sans-serif; }
            QLabel { color: #CDD6F4; font-size: 12px; }
            QTextEdit { background-color: #181825; color: #CDD6F4; border: 1px solid #313244; border-radius: 6px; font-size: 13px; padding: 10px; line-height: 1.4; }
            QLineEdit, QComboBox, QSpinBox { background-color: #181825; color: #CDD6F4; border: 1px solid #313244; border-radius: 4px; padding: 4px 8px; font-size: 12px; }
            QPushButton { background-color: #313244; color: #CDD6F4; border: 1px solid #45475A; padding: 6px 12px; border-radius: 4px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background-color: #45475A; color: #FFFFFF; }
            QPushButton#btnTranslate { background-color: #1E88E5; color: #FFFFFF; border: none; font-size: 13px; padding: 7px 16px; }
            QPushButton#btnTranslate:hover { background-color: #1565C0; }
            QProgressBar { background-color: #181825; border: 1px solid #313244; border-radius: 3px; text-align: center; color: #CDD6F4; font-size: 11px; }
            QProgressBar::chunk { background-color: #1E88E5; }
        """)

        self._setup_ui()
        if self.source_text.strip():
            self._start_translation()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(10)

        # 1. Barra Superior de Control y Motores
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet("background-color: #181825; border: 1px solid #313244; border-radius: 6px; padding: 6px;")
        hdr_layout = QHBoxLayout(hdr_frame)
        hdr_layout.setContentsMargins(6, 4, 6, 4)
        hdr_layout.setSpacing(10)

        hdr_layout.addWidget(QLabel("<b>Motor:</b>"))
        self.cb_engine = QComboBox()
        self.cb_engine.addItem("🤖 IA Local (LM-Studio / Ollama - Especializado Electrónica)", "ai_local")
        self.cb_engine.addItem("🌐 Traductor Online Rápido (Servicio Web)", "online")
        self.cb_engine.addItem("💾 Traductor Local Offline (Reglas Técnicas)", "offline")
        self.cb_engine.setMinimumWidth(320)
        hdr_layout.addWidget(self.cb_engine)

        hdr_layout.addWidget(QLabel("<b>Origen:</b>"))
        self.cb_source_type = QComboBox()
        self.cb_source_type.addItem("Texto Seleccionado / OCR", "custom")
        cur_p = self.doc_context.get('current_page', 1)
        tot_p = self.doc_context.get('total_pages', 1)
        self.cb_source_type.addItem(f"Página Actual ({cur_p})", "current_page")
        self.cb_source_type.addItem("Rango de Páginas...", "range")
        self.cb_source_type.currentIndexChanged.connect(self._on_source_type_changed)
        hdr_layout.addWidget(self.cb_source_type)

        # Controles para Rango de Páginas (Ocultos por defecto)
        self.range_widget = QWidget()
        rw_layout = QHBoxLayout(self.range_widget)
        rw_layout.setContentsMargins(0, 0, 0, 0)
        rw_layout.setSpacing(4)
        rw_layout.addWidget(QLabel("De:"))
        self.spn_from = QSpinBox()
        self.spn_from.setRange(1, tot_p)
        self.spn_from.setValue(cur_p)
        rw_layout.addWidget(self.spn_from)
        rw_layout.addWidget(QLabel("A:"))
        self.spn_to = QSpinBox()
        self.spn_to.setRange(1, tot_p)
        self.spn_to.setValue(min(cur_p + 1, tot_p))
        rw_layout.addWidget(self.spn_to)
        self.btn_load_range = QPushButton("Cargar Páginas")
        self.btn_load_range.clicked.connect(self._load_text_from_range)
        rw_layout.addWidget(self.btn_load_range)
        self.range_widget.setVisible(False)
        hdr_layout.addWidget(self.range_widget)

        hdr_layout.addStretch()

        self.btn_translate = QPushButton(" Traducir al Español")
        self.btn_translate.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'globe.svg'), '#FFFFFF', 16))
        self.btn_translate.setObjectName("btnTranslate")
        self.btn_translate.clicked.connect(self._start_translation)
        hdr_layout.addWidget(self.btn_translate)

        main_layout.addWidget(hdr_frame)

        # 2. Panel Dividido (Texto Original vs Traducción)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #313244; width: 4px; }")

        # 2.1 Panel Izquierdo: Original
        w_left = QWidget()
        l_layout = QVBoxLayout(w_left)
        l_layout.setContentsMargins(0, 0, 0, 0)
        l_layout.setSpacing(4)
        l_hdr = QHBoxLayout()
        l_hdr.addWidget(QLabel("<b>Texto Original (Inglés / Técnico):</b>"))
        self.lbl_src_stats = QLabel("0 palabras")
        self.lbl_src_stats.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        l_hdr.addWidget(self.lbl_src_stats, alignment=Qt.AlignmentFlag.AlignRight)
        l_layout.addLayout(l_hdr)

        self.txt_source = QTextEdit()
        self.txt_source.setPlainText(self.source_text)
        self.txt_source.setPlaceholderText("Ingresa o pega el texto en inglés que deseas traducir al español...")
        self.txt_source.textChanged.connect(self._update_stats)
        l_layout.addWidget(self.txt_source, 1)
        self.splitter.addWidget(w_left)

        # 2.2 Panel Derecho: Traducción
        w_right = QWidget()
        r_layout = QVBoxLayout(w_right)
        r_layout.setContentsMargins(0, 0, 0, 0)
        r_layout.setSpacing(4)
        r_hdr = QHBoxLayout()
        r_hdr.addWidget(QLabel("<b>Traducción al Español Técnico:</b>"))
        self.lbl_target_stats = QLabel("0 palabras")
        self.lbl_target_stats.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        r_hdr.addWidget(self.lbl_target_stats, alignment=Qt.AlignmentFlag.AlignRight)
        r_layout.addLayout(r_hdr)

        self.txt_target = QTextEdit()
        self.txt_target.setPlaceholderText("La traducción técnica al español aparecerá aquí...")
        r_layout.addWidget(self.txt_target, 1)
        self.splitter.addWidget(w_right)

        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        main_layout.addWidget(self.splitter, 1)

        # Barra de Estado / Progreso
        self.lbl_status = QLabel("Listo para traducir.")
        self.lbl_status.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        main_layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # 3. Barra Inferior de Acciones
        ftr_layout = QHBoxLayout()
        ftr_layout.setSpacing(8)

        self.btn_copy = QPushButton(" Copiar Traducción")
        self.btn_copy.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'copy.svg'), '#CDD6F4', 14))
        self.btn_copy.clicked.connect(self._copy_translation)
        ftr_layout.addWidget(self.btn_copy)

        self.btn_send_doki = QPushButton(" 📝 Enviar a Documento Doki...")
        self.btn_send_doki.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'new_note.svg'), '#FFFFFF', 14))
        self.btn_send_doki.setStyleSheet("QPushButton { background-color: #2E7D32; color: #FFFFFF; font-weight: bold; } QPushButton:hover { background-color: #388E3C; }")
        self.btn_send_doki.clicked.connect(self._send_to_doki)
        ftr_layout.addWidget(self.btn_send_doki)

        self.btn_save = QPushButton(" Guardar como .txt...")
        self.btn_save.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'save.svg'), '#CDD6F4', 14))
        self.btn_save.clicked.connect(self._save_translation_file)
        ftr_layout.addWidget(self.btn_save)

        ftr_layout.addStretch()

        self.btn_close = QPushButton(" Cerrar")
        self.btn_close.setIcon(get_themed_svg_icon(os.path.join(self.icons_dir, 'close.svg'), '#CDD6F4', 14))
        self.btn_close.clicked.connect(self.accept)
        ftr_layout.addWidget(self.btn_close)

        main_layout.addLayout(ftr_layout)
        self._update_stats()

    def _on_source_type_changed(self, index: int):
        data = self.cb_source_type.currentData()
        self.range_widget.setVisible(data == "range")
        if data == "current_page":
            self._load_text_from_current_page()

    def _load_text_from_current_page(self):
        doc = self.doc_context.get('doc')
        cur_p = self.doc_context.get('current_page', 1)
        if doc and 1 <= cur_p <= len(doc):
            page = doc[cur_p - 1]
            text = page.get_text("text")
            self.txt_source.setPlainText(text)
            self._update_stats()

    def _load_text_from_range(self):
        doc = self.doc_context.get('doc')
        if not doc: return
        p_from = self.spn_from.value()
        p_to = self.spn_to.value()
        if p_from > p_to:
            QMessageBox.warning(self, "Rango Inválido", "La página inicial no puede ser mayor que la final.")
            return

        pages_text = []
        for p in range(p_from, p_to + 1):
            if 1 <= p <= len(doc):
                pages_text.append(f"--- [Página {p}] ---\n" + doc[p - 1].get_text("text"))

        self.txt_source.setPlainText("\n\n".join(pages_text))
        self._update_stats()

    def _update_stats(self):
        src = self.txt_source.toPlainText()
        words = len(src.split())
        chars = len(src)
        self.lbl_src_stats.setText(f"{words} palabras | {chars} caracteres")

        tgt = self.txt_target.toPlainText()
        tgt_words = len(tgt.split())
        tgt_chars = len(tgt)
        self.lbl_target_stats.setText(f"{tgt_words} palabras | {tgt_chars} caracteres")

    def _start_translation(self):
        text_to_translate = self.txt_source.toPlainText().strip()
        if not text_to_translate:
            QMessageBox.information(self, "Texto Vacío", "Por favor ingresa o carga texto para traducir.")
            return

        engine = self.cb_engine.currentData()

        # Configuración de IA desde settings
        settings = Settings.load()
        ai_cfg = {
            'provider': getattr(settings.ai, 'provider', 'lm_studio'),
            'endpoint': getattr(settings.ai, 'lm_studio_url', 'http://localhost:1234/v1') if getattr(settings.ai, 'provider', 'lm_studio') == 'lm_studio' else getattr(settings.ai, 'ollama_url', 'http://localhost:11434'),
            'model': getattr(settings.ai, 'selected_model', 'qwen2.5-coder-7b-instruct'),
            'api_key': getattr(settings.ai, 'api_key', 'lm-studio')
        }

        self.btn_translate.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.lbl_status.setText("Traduciendo texto técnico al español...")

        self.worker = TranslationWorkerThread(text_to_translate, engine=engine, ai_config=ai_cfg)
        self.worker.status_updated.connect(self.lbl_status.setText)
        self.worker.translation_ready.connect(self._on_translation_success)
        self.worker.error_occurred.connect(self._on_translation_error)
        self.worker.start()

    def _on_translation_success(self, translated_text: str):
        self.txt_target.setPlainText(translated_text)
        self.btn_translate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("✅ Traducción completada con éxito.")
        self._update_stats()

    def _on_translation_error(self, err: str):
        self.btn_translate.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText(f"❌ {err}")
        QMessageBox.warning(self, "Error de Traducción", f"Ocurrió un problema durante la traducción:\n\n{err}")

    def _copy_translation(self):
        text = self.txt_target.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "Sin Contenido", "No hay traducción para copiar.")
            return
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado", "Texto traducido copiado al portapapeles.")

    def _save_translation_file(self):
        text = self.txt_target.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "Sin Contenido", "No hay traducción para guardar.")
            return

        filepath, _ = QFileDialog.getSaveFileName(self, "Guardar Traducción", "traduccion_tecnica.txt", "Archivos de Texto (*.txt)")
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Guardado", f"Traducción guardada exitosamente en:\n{filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo: {e}")

    def _send_to_doki(self):
        text = self.txt_target.toPlainText().strip()
        if not text:
            text = self.txt_source.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Sin Texto", "No hay texto para enviar a un documento Doki.")
            return

        agenda_path = self.doc_context.get('agenda_path', '')
        if not agenda_path and hasattr(self.parent(), 'agenda_path'):
            agenda_path = getattr(self.parent(), 'agenda_path', '')

        if not agenda_path:
            QMessageBox.warning(self, "Agenda no disponible", "No se detectó una ruta de agenda activa para guardar documentos Doki.")
            return

        from plugins.biblioteca.doki_editor import DokiManager, NewDokiDialog
        doki_dir = DokiManager.get_doki_dir(agenda_path)
        doki_files = [f for f in os.listdir(doki_dir) if f.endswith('.doki')]

        options = ["➕ Crear Nuevo Documento Doki..."]
        file_map = {}
        for fn in doki_files:
            fp = os.path.join(doki_dir, fn)
            try:
                data = DokiManager.load_doki(fp)
                t = data.get('metadata', {}).get('title', fn)
                label = f"📄 {t} ({fn})"
                options.append(label)
                file_map[label] = fp
            except Exception:
                pass

        choice, ok = QInputDialog.getItem(self, "Enviar a Documento Doki", "Selecciona el documento destino:", options, 0, False)
        if not ok or not choice: return

        if choice == "➕ Crear Nuevo Documento Doki...":
            dlg = NewDokiDialog(parent=self)
            if dlg.exec():
                d = dlg.get_data()
                meta = DokiManager.create_empty_doki(agenda_path, d['title'], d['author'], d['description'])
                full_p = os.path.join(agenda_path, meta['relative_path'])
                data = DokiManager.load_doki(full_p)
                cur_html = data.get('html', '')
                appended_html = cur_html + f"<br><h3>Texto Traducido</h3><p>{text.replace(chr(10), '<br>')}</p>"
                DokiManager.save_doki(full_p, meta, appended_html, data.get('images', {}))
                QMessageBox.information(self, "Documento Creado", f"Se ha creado el documento Doki y se agregó el texto traducido:\n{meta['title']}")
        else:
            target_fp = file_map.get(choice)
            if target_fp and os.path.exists(target_fp):
                data = DokiManager.load_doki(target_fp)
                meta = data.get('metadata', {})
                cur_html = data.get('html', '')
                appended_html = cur_html + f"<br><h3>Texto Traducido</h3><p>{text.replace(chr(10), '<br>')}</p>"
                DokiManager.save_doki(target_fp, meta, appended_html, data.get('images', {}))
                QMessageBox.information(self, "Texto Insertado", f"Texto insertado exitosamente en:\n{meta.get('title', choice)}")
