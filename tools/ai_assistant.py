# =============================================================================
# Vito Organizer v2.9 - AI Assistant Floating Tool & Agent Manager
# Ventana Flotante de Inteligencia Artificial (LM Studio / Ollama) con Agente
# =============================================================================

import os
import json
import re
import urllib.request
import urllib.error
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QPoint
from PyQt6.QtGui import QFont, QColor, QIcon, QKeySequence, QShortcut, QTextCursor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QLineEdit,
    QComboBox, QCheckBox, QFrame, QScrollArea, QWidget, QSplitter, QMessageBox,
    QFileDialog, QApplication, QMenu
)

from config.settings import Settings


# =============================================================================
# 1. GESTOR DE HERRAMIENTAS DEL AGENTE (Agenda Inspector)
# =============================================================================

class AgentToolsManager:
    """Proporciona capacidades de inspección y herramientas sobre Vito Organizer."""
    def __init__(self, main_window=None):
        self.main_window = main_window

    def get_agenda_summary(self) -> str:
        """Obtiene un resumen general de la agenda activa."""
        if not self.main_window or not getattr(self.main_window, 'agenda_manager', None):
            return "No hay ninguna agenda abierta actualmente en Vito Organizer."
        
        agenda_name = os.path.basename(self.main_window.agenda_manager.current_path or "Agenda")
        summary_lines = [f"### Resumen de la Agenda Activa: '{agenda_name}'"]

        if hasattr(self.main_window, 'plugin_manager'):
            for p in self.main_window.plugin_manager.get_plugins():
                pid = p.get_id()
                pname = p.get_name()
                summary_lines.append(f"- Sección **{pname}** (`{pid}`) activa.")

        return "\n".join(summary_lines)

    def search_agenda_data(self, query: str) -> str:
        """Busca información en los componentes de laboratorio, proyectos y notas."""
        if not self.main_window or not hasattr(self.main_window, 'plugin_manager'):
            return "Sin acceso a los datos de la agenda."

        results = []
        q_lower = query.lower()

        # Buscar en Laboratorio (Componentes / Proyectos)
        lab_p = self.main_window.plugin_manager.get_plugin_by_id('laboratorio')
        if lab_p and hasattr(lab_p, '_data'):
            data = lab_p._data
            # Componentes
            comps = data.get('components', [])
            matched_comps = [c for c in comps if q_lower in c.get('name', '').lower() or q_lower in c.get('category', '').lower()]
            if matched_comps:
                results.append("### Componentes de Laboratorio Encontrados:")
                for c in matched_comps[:10]:
                    results.append(f"- **{c.get('name')}**: Categoría '{c.get('category')}', Stock {c.get('stock_quantity', 0)} U, Ubicación '{c.get('storage_location', 'N/A')}'")

            # Proyectos
            projects = data.get('projects', [])
            matched_projs = [p for p in projects if q_lower in p.get('name', '').lower() or q_lower in p.get('comment', '').lower()]
            if matched_projs:
                results.append("### Proyectos de Desarrollo Encontrados:")
                for p in matched_projs[:5]:
                    results.append(f"- **{p.get('name')}**: Categoría '{p.get('category')}' ({len(p.get('calculations', []))} elementos)")

        # Buscar en Notas
        notas_p = self.main_window.plugin_manager.get_plugin_by_id('notas')
        if notas_p and hasattr(notas_p, '_data'):
            notes = notas_p._data.get('notes', [])
            matched_notes = [n for n in notes if q_lower in n.get('title', '').lower() or q_lower in n.get('content', '').lower()]
            if matched_notes:
                results.append("### Notas Encontradas:")
                for n in matched_notes[:5]:
                    results.append(f"- **{n.get('title')}**: Notebook '{n.get('notebook', 'General')}'")

        if not results:
            return f"No se encontraron coincidencia para la búsqueda '{query}' en la agenda."
        return "\n".join(results)


# =============================================================================
# 2. HILO DE TRABAJO ASÍNCRONO DE IA (AIWorkerThread)
# =============================================================================

class AIWorkerThread(QThread):
    """Ejecuta llamadas HTTP a servidores locales (LM Studio / Ollama / OpenAI API) sin congelar la GUI."""
    response_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, endpoint_url: str, provider: str, model: str, messages: list, temperature=0.7, max_tokens=2048, api_key="lm-studio", parent=None):
        super().__init__(parent)
        self.endpoint_url = endpoint_url.rstrip('/')
        self.provider = provider
        self.model = model
        self.messages = messages
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_key = api_key

    def run(self):
        try:
            if self.provider == "ollama":
                url = f"{self.endpoint_url}/api/chat"
                payload = json.dumps({
                    "model": self.model,
                    "messages": self.messages,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens
                    }
                }).encode('utf-8')
            else:  # LM Studio / Custom OpenAI Compatible
                url = f"{self.endpoint_url}/chat/completions"
                payload = json.dumps({
                    "model": self.model,
                    "messages": self.messages,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                }).encode('utf-8')

            req = urllib.request.Request(
                url, data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                    'User-Agent': 'VitoOrganizer/2.9'
                }
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
                if self.provider == "ollama":
                    content = data.get('message', {}).get('content', '')
                else:
                    choices = data.get('choices', [])
                    content = choices[0].get('message', {}).get('content', '') if choices else ''

                self.response_received.emit(content or "(Respuesta vacía del modelo IA)")

        except urllib.error.URLError as e:
            self.error_occurred.emit(f"Error de conexión con el servidor IA ({self.endpoint_url}).\nAsegúrate de que LM Studio u Ollama estén iniciados.\n\nDetalles: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Error procesando la respuesta de la IA:\n{str(e)}")


# =============================================================================
# 3. WIDGET DE MENSAJE DE CHAT CON BOTONES DE COPIA RÁPIDA
# =============================================================================

class ChatMessageWidget(QFrame):
    """Burbuja individual de mensaje con botón de copia de código y respuesta."""
    def __init__(self, sender: str, text: str, parent=None):
        super().__init__(parent)
        self.sender_name = sender
        self.raw_text = text
        self._setup_ui()

    def _setup_ui(self):
        is_user = self.sender_name.lower() in ("usuario", "tú", "you")
        bg_color = "#313244" if is_user else "#1e1e2e"
        border_color = "#89b4fa" if is_user else "#a6e3a1"
        title_color = "#f9e2af" if is_user else "#a6e3a1"

        self.setStyleSheet(f"""
            ChatMessageWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
            QLabel {{ color: #cdd6f4; font-size: 13px; }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # Header del mensaje
        hdr = QHBoxLayout()
        icon_str = "👤" if is_user else "🤖"
        lbl_sender = QLabel(f"<b>{icon_str} {self.sender_name}</b>")
        lbl_sender.setStyleSheet(f"color: {title_color}; font-size: 13px;")
        hdr.addWidget(lbl_sender)
        hdr.addStretch()

        if not is_user:
            btn_copy_all = QPushButton("📋 Copiar Respuesta")
            btn_copy_all.setStyleSheet("QPushButton { font-weight: bold; padding: 2px 8px; font-size: 11px; background: #45475a; color: #fff; border-radius: 4px; } QPushButton:hover { background: #585b70; }")
            btn_copy_all.clicked.connect(self._copy_full_response)
            hdr.addWidget(btn_copy_all)

        layout.addLayout(hdr)

        # Cuerpo del mensaje
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                color: #cdd6f4;
                border: none;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
        """)
        self.text_display.setMarkdown(self.raw_text)
        
        # Ajustar altura según el texto
        doc_height = int(self.text_display.document().size().height()) + 20
        self.text_display.setMinimumHeight(min(max(50, doc_height), 400))
        layout.addWidget(self.text_display)

        # Detectar bloques de código y colocar botones dedicados de copia
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', self.raw_text, re.DOTALL)
        if code_blocks and not is_user:
            code_bar = QHBoxLayout()
            code_bar.setSpacing(6)
            for idx, code_str in enumerate(code_blocks, start=1):
                btn_code = QPushButton(f"💻 Copiar Código #{idx}")
                btn_code.setStyleSheet("QPushButton { font-weight: bold; padding: 4px 8px; font-size: 11px; background: #89b4fa; color: #111; border-radius: 4px; } QPushButton:hover { background: #74c7ec; }")
                btn_code.clicked.connect(lambda _, c=code_str: self._copy_code_snippet(c))
                code_bar.addWidget(btn_code)
            code_bar.addStretch()
            layout.addLayout(code_bar)

    def _copy_full_response(self):
        QApplication.clipboard().setText(self.raw_text)
        QMessageBox.information(self, "Copiado", "Respuesta completa copiada al portapapeles.")

    def _copy_code_snippet(self, code_text: str):
        QApplication.clipboard().setText(code_text.strip())
        QMessageBox.information(self, "Código Copiado", "Fragmento de código copiado al portapapeles.")


# =============================================================================
# 4. DIÁLOGO PRINCIPAL FLOTANTE DE IA (AIAssistantDialog)
# =============================================================================

class AIAssistantDialog(QDialog):
    """Ventana flotante independiente del Asistente de IA (con traba / Stay On Top)."""
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent or main_window)
        self.main_window = main_window
        self.agent_manager = AgentToolsManager(main_window)
        self.settings = Settings.load()
        self.conversation_history = []
        self.ai_thread = None
        self.is_pinned = True

        self.setWindowTitle("🤖 Asistente de IA Flotante - Vito Organizer (v2.9)")
        self.resize(880, 660)
        self._set_floating_flags()
        self._setup_ui()
        self._init_conversation()

    def _set_floating_flags(self):
        """Configura la ventana como flotante y opción de traba por encima."""
        flags = Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint
        if self.is_pinned:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(10)

        # Barra Superior de Controles
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        lbl_title = QLabel("🤖 <b>Asistente de IA Local</b>")
        lbl_title.setStyleSheet("font-size: 15px; color: #a6e3a1;")
        top_bar.addWidget(lbl_title)

        top_bar.addSpacing(10)

        # Selector de Modelo
        top_bar.addWidget(QLabel("Modelo:"))
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        self.model_combo.setStyleSheet("QComboBox { padding: 4px 8px; border-radius: 4px; background: #313244; color: #cdd6f4; font-weight: bold; }")
        
        # Cargar modelo de settings
        cur_model = getattr(self.settings.ai, 'selected_model', 'qwen2.5-coder-7b-instruct')
        self.model_combo.addItem(cur_model)
        self.model_combo.setCurrentText(cur_model)
        top_bar.addWidget(self.model_combo, 1)

        # Toggle Modo Agente
        self.chk_agent = QCheckBox("🤖 Modo Agente (Agenda)")
        self.chk_agent.setChecked(getattr(self.settings.ai, 'enable_agent', True))
        self.chk_agent.setStyleSheet("QCheckBox { color: #f9e2af; font-weight: bold; }")
        top_bar.addWidget(self.chk_agent)

        # Botón Fijar arriba (Traba)
        self.btn_pin = QPushButton("📌 Trabar Arriba")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setChecked(self.is_pinned)
        self.btn_pin.setStyleSheet("QPushButton { font-weight: bold; padding: 4px 10px; background: #45475a; color: #fff; border-radius: 4px; } QPushButton:checked { background: #f9e2af; color: #111; }")
        self.btn_pin.toggled.connect(self._toggle_pin)
        top_bar.addWidget(self.btn_pin)

        btn_clear = QPushButton("🧹 Limpiar")
        btn_clear.setStyleSheet("QPushButton { font-weight: bold; padding: 4px 8px; background: #f38ba8; color: #111; border-radius: 4px; }")
        btn_clear.clicked.connect(self._clear_chat)
        top_bar.addWidget(btn_clear)

        btn_export = QPushButton("📤 Exportar Chat")
        btn_export.setStyleSheet("QPushButton { font-weight: bold; padding: 4px 8px; background: #89b4fa; color: #111; border-radius: 4px; }")
        btn_export.clicked.connect(self._export_chat)
        top_bar.addWidget(btn_export)

        layout.addLayout(top_bar)

        # Área de Mensajes de Chat (Scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { background-color: #181825; border: 1px solid #313244; border-radius: 8px; }")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)
        layout.addWidget(self.scroll_area, 1)

        # Barra de Accesos Rápidos de Prompt
        quick_bar = QHBoxLayout()
        quick_bar.setSpacing(6)
        btn_q1 = QPushButton("🔍 Buscar Inventario")
        btn_q1.clicked.connect(lambda: self._insert_quick_prompt("¿Qué componentes o herramientas tenemos disponibles en el inventario?"))
        btn_q2 = QPushButton("📝 Resumir Agenda")
        btn_q2.clicked.connect(lambda: self._insert_quick_prompt("Haz un resumen general de la agenda activa."))
        btn_q3 = QPushButton("💻 Explicar Código")
        btn_q3.clicked.connect(lambda: self._insert_quick_prompt("Revisa este código y me explicas su funcionamiento:"))
        btn_q4 = QPushButton("⚡ Plantilla Proyecto")
        btn_q4.clicked.connect(lambda: self._insert_quick_prompt("Genera una plantilla de código estructurada para C++ / Arduino."))

        btn_q_style = "QPushButton { font-size: 11px; padding: 3px 8px; background: #313244; color: #cdd6f4; border-radius: 4px; border: 1px solid #45475a; } QPushButton:hover { background: #45475a; }"
        for b in (btn_q1, btn_q2, btn_q3, btn_q4):
            b.setStyleSheet(btn_q_style)
            quick_bar.addWidget(b)
        quick_bar.addStretch()
        layout.addLayout(quick_bar)

        # Entrada de Texto de Consulta
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.txt_input = QTextEdit()
        self.txt_input.setMaximumHeight(80)
        self.txt_input.setPlaceholderText("Escribe tu consulta o instrucción para la IA... (Ctrl+Enter para enviar)")
        self.txt_input.setStyleSheet("QTextEdit { background-color: #1e1e2e; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px; font-size: 13px; }")
        
        # Shortcut Ctrl+Enter
        shortcut = QShortcut(QKeySequence("Ctrl+Return"), self.txt_input)
        shortcut.activated.connect(self._send_message)

        input_layout.addWidget(self.txt_input, 1)

        btn_send = QPushButton("📤 Enviar")
        btn_send.setMinimumHeight(75)
        btn_send.setStyleSheet("QPushButton { font-weight: bold; font-size: 14px; background: #a6e3a1; color: #11111b; border-radius: 6px; padding: 0 16px; } QPushButton:hover { background: #94e2d5; }")
        btn_send.clicked.connect(self._send_message)
        input_layout.addWidget(btn_send)

        layout.addLayout(input_layout)

    def _toggle_pin(self, checked: bool):
        self.is_pinned = checked
        self._set_floating_flags()
        self.show()

    def _init_conversation(self):
        sys_prompt = getattr(self.settings.ai, 'system_prompt', 'Eres el asistente virtual de Vito Organizer.')
        self.conversation_history = [{"role": "system", "content": sys_prompt}]
        self._append_message_widget("Asistente IA", "¡Hola! Soy tu **Asistente de IA flotante (v2.9)**. Estoy conectado a tu servidor local (LM Studio / Ollama). ¿En qué te puedo ayudar hoy?")

    def _insert_quick_prompt(self, text: str):
        self.txt_input.setText(text)
        self.txt_input.setFocus()

    def _append_message_widget(self, sender: str, text: str):
        msg_w = ChatMessageWidget(sender, text, self)
        # Insert before stretch
        count = self.chat_layout.count()
        self.chat_layout.insertWidget(count - 1, msg_w)
        
        # Scroll to bottom
        QApplication.processEvents()
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _send_message(self):
        user_text = self.txt_input.toPlainText().strip()
        if not user_text: return

        self.txt_input.clear()
        self._append_message_widget("Tú", user_text)

        # Si el modo agente está activo, enriquecer el prompt con contexto de la agenda
        augmented_prompt = user_text
        if self.chk_agent.isChecked():
            # Si el usuario pregunta por inventario, agenda o proyectos, obtener datos
            if any(k in user_text.lower() for k in ("inventario", "componente", "proyecto", "resumen", "agenda", "nota", "tarea", "laboratorio")):
                agenda_info = self.agent_manager.search_agenda_data(user_text)
                augmented_prompt = f"[CONTEXTO AUTOMÁTICO DE LA AGENDA VITO ORGANIZER]:\n{agenda_info}\n\n[CONSULTA DEL USUARIO]:\n{user_text}"

        self.conversation_history.append({"role": "user", "content": augmented_prompt})

        # Datos del servidor IA desde settings
        provider = getattr(self.settings.ai, 'provider', 'lm_studio')
        if provider == 'lm_studio':
            url = getattr(self.settings.ai, 'lm_studio_url', 'http://localhost:1234/v1')
        elif provider == 'ollama':
            url = getattr(self.settings.ai, 'ollama_url', 'http://localhost:11434')
        else:
            url = getattr(self.settings.ai, 'custom_url', 'http://localhost:8000/v1')

        model = self.model_combo.currentText().strip() or getattr(self.settings.ai, 'selected_model', 'qwen2.5-coder-7b-instruct')
        temp = getattr(self.settings.ai, 'temperature', 0.7)
        max_t = getattr(self.settings.ai, 'max_tokens', 2048)
        api_k = getattr(self.settings.ai, 'api_key', 'lm-studio')

        # Lanzar Hilo Asíncrono
        self.ai_thread = AIWorkerThread(url, provider, model, self.conversation_history, temp, max_t, api_k, self)
        self.ai_thread.response_received.connect(self._on_ai_response)
        self.ai_thread.error_occurred.connect(self._on_ai_error)
        self.ai_thread.start()

    def _on_ai_response(self, content: str):
        self.conversation_history.append({"role": "assistant", "content": content})
        self._append_message_widget("Asistente IA", content)

    def _on_ai_error(self, err_msg: str):
        QMessageBox.critical(self, "Error de IA", err_msg)

    def _clear_chat(self):
        # Remove all message widgets
        while self.chat_layout.count() > 1:
            child = self.chat_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()
        self._init_conversation()

    def _export_chat(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exportar Chat en Markdown", "conversacion_ia.md", "Markdown (*.md *.txt)")
        if path:
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("# Historial de Conversación - Asistente IA Vito Organizer\n\n")
                    for m in self.conversation_history:
                        role = m.get('role', 'user').upper()
                        f.write(f"### {role}:\n{m.get('content')}\n\n---\n\n")
                QMessageBox.information(self, "Exportado", f"Chat exportado correctamente a:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al exportar:\n{str(e)}")
