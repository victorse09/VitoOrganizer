# =============================================================================
# Vito Organizer v2.3 - Connectivity Module
# Herramientas de sincronización por red local y servidor HTTP
# =============================================================================

import os
import json
import hashlib
import socket
import urllib.request
import urllib.parse
from datetime import datetime
import http.server
from core.version import APP_VERSION

from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer, QSettings
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QTextEdit,
    QProgressBar, QMessageBox, QHeaderView, QFrame, QTabWidget, QFormLayout,
    QWidget
)


def get_local_ip() -> str:
    """Retorna la dirección IP local de la interfaz de red activa."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"


def get_folder_size(path: str) -> int:
    """Calcula el tamaño total en disco (en bytes) de un directorio recursivamente."""
    total_size = 0
    if not path or not os.path.exists(path):
        return 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    total_size += os.path.getsize(fp)
                except:
                    pass
    return total_size


def format_size(size_bytes: int) -> str:
    """Da formato legible (B, KB, MB, GB) a un tamaño en bytes."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class ConnectivityServerThread(QThread):
    """Hilo secundario que aloja el servidor HTTP de sincronización."""
    log_event = pyqtSignal(str)
    clients_changed = pyqtSignal()

    def __init__(self, port: int, password: str, agenda_path: str, parent=None):
        super().__init__(parent)
        self.port = port
        self.password = password
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.agenda_path = agenda_path
        self.server = None
        self.is_running = False
        
        # Estructuras de control
        self.blocked_ips = set()
        self.kicked_ips = set()
        self.connected_clients = {}  # IP -> {name, last_seen, last_action}

    def run(self):
        class ConnectivityRequestHandler(http.server.BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # Evita imprimir en stderr directamente

            def send_error_response(self, code, message):
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': message}).encode('utf-8'))

            def authenticate(self) -> bool:
                client_ip = self.client_address[0]
                
                # Verificar lista negra (IPs bloqueadas)
                if client_ip in self.server.thread.blocked_ips:
                    self.send_error_response(403, "Acceso denegado: IP bloqueada.")
                    return False
                
                # Verificar si fue desconectado (kicked)
                if client_ip in self.server.thread.kicked_ips:
                    self.send_error_response(401, "Desconectado. Por favor, reautentíquese.")
                    return False

                # Validar token
                token = self.headers.get('X-Auth-Token')
                if not token or token != self.server.thread.password_hash:
                    self.send_error_response(401, "No autorizado. Contraseña incorrecta.")
                    return False

                # Registrar/Actualizar cliente
                client_name = self.headers.get('X-Client-Name', 'Desconocido')
                self.server.thread.connected_clients[client_ip] = {
                    'name': client_name,
                    'last_seen': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'last_action': self.path.split('?')[0]
                }
                self.server.thread.clients_changed.emit()
                return True

            def do_GET(self):
                if not self.authenticate():
                    return

                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)

                if parsed_url.path == '/handshake':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        'status': 'ok', 
                        'server': socket.gethostname(),
                        'version': APP_VERSION,
                        'agenda_size': get_folder_size(self.server.thread.agenda_path)
                    }).encode('utf-8'))
                    self.server.thread.log_activity(self.client_address[0], self.headers.get('X-Client-Name'), f"Prueba de conexión (Handshake) exitosa. Versión compartida: v{APP_VERSION} (Tamaño: {format_size(get_folder_size(self.server.thread.agenda_path))})")
                    return

                elif parsed_url.path == '/manifest':
                    if not self.server.thread.agenda_path or not os.path.exists(self.server.thread.agenda_path):
                        self.send_error_response(500, "No hay agenda abierta en el servidor.")
                        return

                    # Crear manifest de archivos
                    manifest = {}
                    agenda_dir = self.server.thread.agenda_path
                    for root, _, files in os.walk(agenda_dir):
                        for file in files:
                            # Ignorar historial de red y archivos ocultos
                            if file == 'connectivity_log.json' or file.startswith('.'):
                                continue
                            full_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_path, agenda_dir)
                            mtime = os.path.getmtime(full_path)
                            size = os.path.getsize(full_path)
                            manifest[rel_path] = {'mtime': mtime, 'size': size}

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(manifest).encode('utf-8'))
                    return

                elif parsed_url.path == '/download':
                    file_param = query_params.get('file')
                    if not file_param:
                        self.send_error_response(400, "Parámetro 'file' faltante.")
                        return

                    rel_path = file_param[0]
                    agenda_dir = self.server.thread.agenda_path
                    full_path = os.path.abspath(os.path.join(agenda_dir, rel_path))
                    
                    # Evitar Path Traversal
                    if not full_path.startswith(os.path.abspath(agenda_dir)):
                        self.send_error_response(403, "Acceso prohibido.")
                        return

                    if not os.path.exists(full_path) or os.path.isdir(full_path):
                        self.send_error_response(404, "Archivo no encontrado.")
                        return

                    try:
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/octet-stream')
                        self.send_header('Content-Length', str(os.path.getsize(full_path)))
                        self.end_headers()
                        with open(full_path, 'rb') as f:
                            self.wfile.write(f.read())
                        self.server.thread.log_activity(self.client_address[0], self.headers.get('X-Client-Name'), f"Descargó archivo: {rel_path}")
                    except Exception as e:
                        self.send_error_response(500, f"Error de lectura: {str(e)}")
                    return

                self.send_error_response(404, "Ruta no encontrada.")

            def do_POST(self):
                if not self.authenticate():
                    return

                parsed_url = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_url.query)

                if parsed_url.path == '/upload':
                    file_param = query_params.get('file')
                    if not file_param:
                        self.send_error_response(400, "Parámetro 'file' faltante.")
                        return

                    rel_path = file_param[0]
                    agenda_dir = self.server.thread.agenda_path
                    full_path = os.path.abspath(os.path.join(agenda_dir, rel_path))
                    
                    # Evitar Path Traversal
                    if not full_path.startswith(os.path.abspath(agenda_dir)):
                        self.send_error_response(403, "Acceso prohibido.")
                        return

                    try:
                        content_length = int(self.headers.get('Content-Length', 0))
                        file_content = self.rfile.read(content_length)

                        # Asegurar subcarpetas
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        with open(full_path, 'wb') as f:
                            f.write(file_content)

                        # Preservar marca de tiempo
                        mtime_param = query_params.get('mtime')
                        if mtime_param:
                            mtime = float(mtime_param[0])
                            os.utime(full_path, (mtime, mtime))

                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'status': 'ok'}).encode('utf-8'))
                        self.server.thread.log_activity(self.client_address[0], self.headers.get('X-Client-Name'), f"Subió/Actualizó archivo: {rel_path}")
                    except Exception as e:
                        self.send_error_response(500, f"Error de escritura: {str(e)}")
                    return

                self.send_error_response(404, "Ruta no encontrada.")

        self.is_running = True
        try:
            self.server = http.server.HTTPServer(('0.0.0.0', self.port), ConnectivityRequestHandler)
            self.server.thread = self
            self.log_event.emit(f"Servidor HTTP de sincronización iniciado en el puerto {self.port}.")
            self.server.serve_forever()
        except Exception as e:
            self.log_event.emit(f"Error crítico en servidor: {str(e)}")
            self.is_running = False

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.is_running = False
        self.log_event.emit("Servidor HTTP detenido.")
        self.wait()

    def log_activity(self, ip: str, client_name: str, description: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] IP: {ip} ({client_name}) - {description}"
        self.log_event.emit(log_entry)

        # Guardar historial físico en la agenda activa
        if self.agenda_path and os.path.exists(self.agenda_path):
            log_file = os.path.join(self.agenda_path, 'data', 'connectivity_log.json')
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            log_data = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                except:
                    pass
            
            log_data.append({
                'timestamp': timestamp,
                'ip': ip,
                'client': client_name,
                'description': description
            })
            
            try:
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump(log_data, f, indent=4, ensure_ascii=False)
            except:
                pass


class SyncWorkerThread(QThread):
    """Hilo para realizar operaciones de red y sincronización sin congelar la GUI."""
    progress = pyqtSignal(int, str)
    finished_sync = pyqtSignal(bool, str)

    def __init__(self, mode: str, server_ip: str, port: int, password: str, client_name: str, agenda_path: str):
        super().__init__()
        self.mode = mode  # 'download', 'upload', 'bidirectional'
        self.server_ip = server_ip
        self.port = port
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        self.client_name = client_name
        self.agenda_path = agenda_path

    def run(self):
        base_url = f"http://{self.server_ip}:{self.port}"
        try:
            self.progress.emit(0, "Estableciendo conexión y validando credenciales...")
            
            # Handshake
            handshake_url = f"{base_url}/handshake"
            req = urllib.request.Request(handshake_url, headers={
                'X-Auth-Token': self.password_hash,
                'X-Client-Name': self.client_name
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                handshake_data = json.loads(resp.read().decode('utf-8'))
            
            server_version = handshake_data.get('version', 'unknown')
            self.version_mismatch = (server_version != APP_VERSION)
            self.server_version_str = server_version

            self.progress.emit(15, "Obteniendo estado del manifest del servidor...")
            # Obtener manifest remoto
            manifest_url = f"{base_url}/manifest"
            req = urllib.request.Request(manifest_url, headers={
                'X-Auth-Token': self.password_hash,
                'X-Client-Name': self.client_name
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                server_manifest = json.loads(resp.read().decode('utf-8'))

            # Escanear archivos locales
            self.progress.emit(30, "Analizando archivos locales...")
            local_manifest = {}
            for root, _, files in os.walk(self.agenda_path):
                for file in files:
                    if file == 'connectivity_log.json' or file.startswith('.'):
                        continue
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.agenda_path)
                    mtime = os.path.getmtime(full_path)
                    size = os.path.getsize(full_path)
                    local_manifest[rel_path] = {'mtime': mtime, 'size': size}

            to_download = []
            to_upload = []

            all_files = set(server_manifest.keys()) | set(local_manifest.keys())

            for rel_path in all_files:
                srv = server_manifest.get(rel_path)
                loc = local_manifest.get(rel_path)

                if self.mode == 'download':
                    if srv:
                        if not loc or srv['mtime'] > loc['mtime'] + 1.0:
                            to_download.append(rel_path)
                elif self.mode == 'upload':
                    if loc:
                        if not srv or loc['mtime'] > srv['mtime'] + 1.0:
                            to_upload.append(rel_path)
                elif self.mode == 'bidirectional':
                    if srv and not loc:
                        to_download.append(rel_path)
                    elif loc and not srv:
                        to_upload.append(rel_path)
                    elif srv and loc:
                        # Diferencia de tiempo mayor a 1 segundo para tolerar sistemas de archivos
                        if srv['mtime'] > loc['mtime'] + 1.0:
                            to_download.append(rel_path)
                        elif loc['mtime'] > srv['mtime'] + 1.0:
                            to_upload.append(rel_path)

            total_ops = len(to_download) + len(to_upload)
            if total_ops == 0:
                self.finished_sync.emit(True, "La agenda local ya se encuentra sincronizada.")
                return

            completed = 0
            
            # Descargas
            for rel_path in to_download:
                self.progress.emit(int((completed / total_ops) * 100), f"Descargando {rel_path}...")
                
                download_url = f"{base_url}/download?file={urllib.parse.quote(rel_path)}"
                req = urllib.request.Request(download_url, headers={
                    'X-Auth-Token': self.password_hash,
                    'X-Client-Name': self.client_name
                })
                with urllib.request.urlopen(req, timeout=15) as resp:
                    file_content = resp.read()

                local_path = os.path.join(self.agenda_path, rel_path)
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(file_content)

                # Ajustar marca de tiempo
                srv_mtime = server_manifest[rel_path]['mtime']
                os.utime(local_path, (srv_mtime, srv_mtime))
                completed += 1

            # Subidas
            for rel_path in to_upload:
                self.progress.emit(int((completed / total_ops) * 100), f"Subiendo {rel_path}...")
                
                local_path = os.path.join(self.agenda_path, rel_path)
                with open(local_path, 'rb') as f:
                    file_content = f.read()

                loc_mtime = local_manifest[rel_path]['mtime']
                upload_url = f"{base_url}/upload?file={urllib.parse.quote(rel_path)}&mtime={loc_mtime}"
                
                req = urllib.request.Request(upload_url, data=file_content, headers={
                    'X-Auth-Token': self.password_hash,
                    'X-Client-Name': self.client_name,
                    'Content-Type': 'application/octet-stream'
                }, method='POST')
                
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp.read()

                completed += 1

            self.progress.emit(100, "Sincronización de red completada.")
            msg = f"Sincronización completa exitosa.\n- {len(to_download)} descargas.\n- {len(to_upload)} subidas."
            if getattr(self, 'version_mismatch', False):
                msg += f"\n\n⚠️ ALERTA DE COMPATIBILIDAD:\nEl servidor ejecuta la versión v{self.server_version_str} mientras que este cliente ejecuta la v{APP_VERSION}.\nSe recomienda unificar las versiones de la aplicación para evitar inconsistencias en los datos."
            self.finished_sync.emit(True, msg)

        except urllib.error.HTTPError as e:
            err_msg = f"Error del servidor ({e.code}): "
            try:
                err_data = json.loads(e.read().decode('utf-8'))
                err_msg += err_data.get('error', e.reason)
            except:
                err_msg += e.reason
            self.finished_sync.emit(False, err_msg)
        except Exception as e:
            self.finished_sync.emit(False, f"Fallo al conectar con el servidor: {str(e)}")


class ConnectivityDialog(QDialog):
    """Ventana principal de configuración de red y sincronización local/servidor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conectividad de Red y Sincronización")
        self.resize(600, 520)
        self.qsettings = QSettings("Vitokin", "VitoOrganizerConnectivity")
        
        self.sync_thread = None
        self._setup_ui()
        self._load_saved_settings()
        self._update_server_ui_state()

        # Validar si hay una agenda abierta localmente
        main_win = self.parent()
        agenda_path = getattr(main_win, 'agenda_path', None)
        self.has_open_agenda = bool(agenda_path and os.path.exists(agenda_path))
        
        if not self.has_open_agenda:
            self._disable_controls_no_agenda()
            QTimer.singleShot(100, lambda: QMessageBox.warning(
                self,
                "Agenda Requerida",
                "Para poder configurar el Servidor o utilizar el Cliente de Sincronización, "
                "debe abrir o crear una agenda previamente desde el menú Archivo."
            ))

        # Timer para refrescar datos del servidor cada 3 segundos
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._refresh_server_data)
        self.refresh_timer.start(3000)

    def _disable_controls_no_agenda(self):
        """Deshabilita todos los controles si no hay una agenda abierta localmente."""
        # Deshabilitar controles del Servidor
        self.srv_port.setEnabled(False)
        self.srv_pass.setEnabled(False)
        self.btn_toggle_server.setEnabled(False)
        self.btn_toggle_server.setText("Requiere Agenda Abierta")
        self.lbl_server_status.setText("<b>Estado:</b> <span style='color:#f38ba8;'>No disponible (Requiere agenda abierta)</span>")
        
        # Deshabilitar controles del Cliente
        self.cli_ip.setEnabled(False)
        self.cli_port.setEnabled(False)
        self.cli_pass.setEnabled(False)
        self.cli_name.setEnabled(False)
        self.btn_test_conn.setEnabled(False)
        self.btn_sync_pull.setEnabled(False)
        self.btn_sync_push.setEnabled(False)
        self.btn_sync_both.setEnabled(False)
        self.lbl_sync_status.setText("Sincronización no disponible: Por favor abra o cree una agenda primero.")
        self.lbl_sync_status.setStyleSheet("color: #f38ba8; font-style: italic; font-weight: bold;")

    def _setup_ui(self):
        self.setStyleSheet("""
            QDialog { background-color: #111322; }
            QLabel { color: #cdd6f4; font-size: 12px; }
            QLineEdit { background-color: #1e1e2e; border: 1px solid #2d314e; border-radius: 4px; color: #edf2f4; padding: 5px; }
            QTabWidget::pane { border: 1px solid #2d314e; background: #1e1e2e; border-radius: 6px; }
            QTabBar::tab { background: #25263a; color: #a6adc8; border: 1px solid #2d314e; padding: 8px 16px; font-weight: bold; border-top-left-radius: 4px; border-top-right-radius: 4px; }
            QTabBar::tab:selected { background: #1e1e2e; color: #edf2f4; border-bottom: 2px solid #ff5722; }
            QPushButton { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 6px; padding: 6px 14px; font-weight: bold; }
            QPushButton:hover { background-color: #45475a; border-color: #ff5722; }
            QPushButton#primaryButton { background-color: #ff5722; color: #ffffff; border: none; }
            QPushButton#primaryButton:hover { background-color: #ff784e; }
            QTableWidget { background-color: #1e1e2e; gridline-color: #2d314e; color: #cdd6f4; border: 1px solid #2d314e; border-radius: 4px; }
            QHeaderView::section { background-color: #25263a; color: #cdd6f4; border: 1px solid #2d314e; padding: 4px; font-weight: bold; }
            QTextEdit { background-color: #111322; border: 1px solid #2d314e; border-radius: 4px; color: #a6da95; font-family: monospace; font-size: 11px; padding: 6px; }
        """)

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        # --- TAB 1: MODO SERVIDOR ---
        self.tab_server = QWidget()
        srv_layout = QVBoxLayout(self.tab_server)
        srv_layout.setSpacing(10)
        srv_layout.setContentsMargins(12, 12, 12, 12)

        form_srv = QFormLayout()
        self.srv_port = QLineEdit()
        self.srv_port.setPlaceholderText("Ej: 8080")
        self.srv_port.setText("8080")
        self.srv_port.setFixedWidth(100)
        self.srv_pass = QLineEdit()
        self.srv_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.srv_pass.setPlaceholderText("Clave requerida para los clientes")
        
        form_srv.addRow("Puerto de Red:", self.srv_port)
        form_srv.addRow("Contraseña Servidor:", self.srv_pass)
        srv_layout.addLayout(form_srv)

        # Botón Encender / Apagar
        self.btn_toggle_server = QPushButton("Iniciar Servidor")
        self.btn_toggle_server.setObjectName("primaryButton")
        self.btn_toggle_server.clicked.connect(self._toggle_server)
        srv_layout.addWidget(self.btn_toggle_server)

        # Panel de Estado del Servidor
        self.frame_status = QFrame()
        self.frame_status.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_status.setStyleSheet("QFrame { background-color: #111322; border: 1px solid #2d314e; border-radius: 6px; padding: 6px; }")
        status_layout = QVBoxLayout(self.frame_status)
        self.lbl_server_status = QLabel("<b>Estado:</b> Apagado")
        self.lbl_server_url = QLabel("<b>Dirección URL:</b> -")
        self.lbl_server_agenda_size = QLabel("<b>Tamaño de la Agenda compartida:</b> -")
        status_layout.addWidget(self.lbl_server_status)
        status_layout.addWidget(self.lbl_server_url)
        status_layout.addWidget(self.lbl_server_agenda_size)
        srv_layout.addWidget(self.frame_status)

        # Tabla de Clientes Conectados
        srv_layout.addWidget(QLabel("<b>Equipos Clientes Conectados:</b>"))
        self.tbl_clients = QTableWidget(0, 3)
        self.tbl_clients.setHorizontalHeaderLabels(["Nombre Máquina", "Dirección IP", "Último Acceso"])
        self.tbl_clients.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_clients.setMaximumHeight(120)
        srv_layout.addWidget(self.tbl_clients)

        # Acciones de Clientes
        client_btns = QHBoxLayout()
        self.btn_refresh_clients = QPushButton("Refrescar")
        self.btn_refresh_clients.clicked.connect(self._refresh_server_data)
        self.btn_kick_client = QPushButton("Desconectar")
        self.btn_kick_client.clicked.connect(self._kick_selected_client)
        self.btn_block_ip = QPushButton("Bloquear IP")
        self.btn_block_ip.setStyleSheet("background-color: #f38ba8; color: #11111b; border: none;")
        self.btn_block_ip.clicked.connect(self._block_selected_ip)
        
        client_btns.addWidget(self.btn_refresh_clients)
        client_btns.addWidget(self.btn_kick_client)
        client_btns.addWidget(self.btn_block_ip)
        srv_layout.addLayout(client_btns)

        # Log de Actividad
        srv_layout.addWidget(QLabel("<b>Historial de Actividad y Transferencias:</b>"))
        self.txt_srv_log = QTextEdit()
        self.txt_srv_log.setReadOnly(True)
        srv_layout.addWidget(self.txt_srv_log)

        self.tabs.addTab(self.tab_server, "Modo Servidor")

        # --- TAB 2: MODO CLIENTE ---
        self.tab_client = QWidget()
        cli_layout = QVBoxLayout(self.tab_client)
        cli_layout.setSpacing(12)
        cli_layout.setContentsMargins(15, 15, 15, 15)

        form_cli = QFormLayout()
        self.cli_ip = QLineEdit()
        self.cli_ip.setPlaceholderText("Ej: 192.168.1.50")
        self.cli_port = QLineEdit()
        self.cli_port.setPlaceholderText("Ej: 8080")
        self.cli_port.setText("8080")
        self.cli_port.setFixedWidth(100)
        self.cli_pass = QLineEdit()
        self.cli_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.cli_name = QLineEdit()
        self.cli_name.setText(socket.gethostname())
        self.cli_name.setPlaceholderText("Ej: PC Taller 1")

        form_cli.addRow("IP del Servidor:", self.cli_ip)
        form_cli.addRow("Puerto Servidor:", self.cli_port)
        form_cli.addRow("Contraseña Servidor:", self.cli_pass)
        form_cli.addRow("Nombre de este Equipo:", self.cli_name)
        cli_layout.addLayout(form_cli)

        # Botón Probar Conexión
        self.btn_test_conn = QPushButton("Probar Conectividad")
        self.btn_test_conn.clicked.connect(self._test_connectivity)
        cli_layout.addWidget(self.btn_test_conn)

        # Acciones de sincronización
        cli_layout.addWidget(QLabel("<b>Acciones de Sincronización de Agenda:</b>"))
        
        sync_grid = QHBoxLayout()
        self.btn_sync_pull = QPushButton("Recibir del Servidor")
        self.btn_sync_pull.clicked.connect(lambda: self._start_sync('download'))
        self.btn_sync_push = QPushButton("Subir al Servidor")
        self.btn_sync_push.clicked.connect(lambda: self._start_sync('upload'))
        self.btn_sync_both = QPushButton("Sincronización Bidireccional")
        self.btn_sync_both.setObjectName("primaryButton")
        self.btn_sync_both.clicked.connect(lambda: self._start_sync('bidirectional'))

        sync_grid.addWidget(self.btn_sync_pull)
        sync_grid.addWidget(self.btn_sync_push)
        sync_grid.addWidget(self.btn_sync_both)
        cli_layout.addLayout(sync_grid)

        # Progreso de Sincronización
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet("QProgressBar { background-color: #111322; border: 1px solid #2d314e; border-radius: 4px; text-align: center; color: white; } QProgressBar::chunk { background-color: #ff5722; }")
        cli_layout.addWidget(self.progress_bar)

        self.lbl_sync_status = QLabel("Listo para sincronizar.")
        self.lbl_sync_status.setStyleSheet("color: #a6adc8; font-style: italic;")
        self.lbl_sync_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cli_layout.addWidget(self.lbl_sync_status)

        # Panel de Estado del Cliente
        self.frame_client_status = QFrame()
        self.frame_client_status.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame_client_status.setStyleSheet("QFrame { background-color: #111322; border: 1px solid #2d314e; border-radius: 6px; padding: 6px; }")
        cli_status_layout = QVBoxLayout(self.frame_client_status)
        self.lbl_client_agenda_size = QLabel("<b>Tamaño de Agenda Local:</b> -")
        self.lbl_remote_agenda_size = QLabel("<b>Tamaño de Agenda en Servidor:</b> -")
        cli_status_layout.addWidget(self.lbl_client_agenda_size)
        cli_status_layout.addWidget(self.lbl_remote_agenda_size)
        cli_layout.addWidget(self.frame_client_status)

        cli_layout.addStretch()

        self.tabs.addTab(self.tab_client, "Modo Cliente")

        layout.addWidget(self.tabs)

        # Botón Cerrar
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        bottom_layout.addWidget(btn_close)
        layout.addLayout(bottom_layout)

    def _load_saved_settings(self):
        """Carga los parámetros de red persistidos."""
        self.srv_port.setText(self.qsettings.value("srv_port", "8080"))
        self.srv_pass.setText(self.qsettings.value("srv_pass", ""))
        self.cli_ip.setText(self.qsettings.value("cli_ip", ""))
        self.cli_port.setText(self.qsettings.value("cli_port", "8080"))
        self.cli_pass.setText(self.qsettings.value("cli_pass", ""))
        self.cli_name.setText(self.qsettings.value("cli_name", socket.gethostname()))

        # Cargar tamaño de agenda local en el cliente
        main_win = self.parent()
        agenda_path = getattr(main_win, 'agenda_path', None)
        if agenda_path and os.path.exists(agenda_path):
            sz = get_folder_size(agenda_path)
            self.lbl_client_agenda_size.setText(f"<b>Tamaño de Agenda Local:</b> {format_size(sz)}")
        else:
            self.lbl_client_agenda_size.setText("<b>Tamaño de Agenda Local:</b> -")

    def _save_current_settings(self):
        """Guarda persistentemente los parámetros ingresados."""
        self.qsettings.setValue("srv_port", self.srv_port.text().strip())
        self.qsettings.setValue("srv_pass", self.srv_pass.text())
        self.qsettings.setValue("cli_ip", self.cli_ip.text().strip())
        self.qsettings.setValue("cli_port", self.cli_port.text().strip())
        self.qsettings.setValue("cli_pass", self.cli_pass.text())
        self.qsettings.setValue("cli_name", self.cli_name.text().strip())

    def _update_server_ui_state(self):
        """Ajusta el estado visual de los controles según si el servidor está encendido."""
        main_win = self.parent()
        thread = getattr(main_win, 'server_thread', None)

        if thread and thread.is_running:
            self.srv_port.setEnabled(False)
            self.srv_pass.setEnabled(False)
            self.btn_toggle_server.setText("Detener Servidor")
            self.btn_toggle_server.setStyleSheet("background-color: #f38ba8; color: #11111b; border: none; font-weight: bold;")
            self.lbl_server_status.setText("<b>Estado:</b> <span style='color:#a6da95;'>En ejecución (Activo)</span>")
            self.lbl_server_url.setText(f"<b>Dirección URL:</b> http://{get_local_ip()}:{thread.port}/")
            
            # Reconectar log si el diálogo fue reabierto
            try:
                thread.log_event.disconnect()
            except:
                pass
            try:
                thread.clients_changed.disconnect()
            except:
                pass
            
            thread.log_event.connect(self._on_server_log)
            thread.clients_changed.connect(self._on_server_clients_changed)
            
            # Forzar primera actualización
            self._refresh_server_data()
        else:
            self.srv_port.setEnabled(True)
            self.srv_pass.setEnabled(True)
            self.btn_toggle_server.setText("Iniciar Servidor")
            self.btn_toggle_server.setStyleSheet("")
            self.lbl_server_status.setText("<b>Estado:</b> Apagado")
            self.lbl_server_url.setText("<b>Dirección URL:</b> -")
            self.tbl_clients.setRowCount(0)
            self.txt_srv_log.clear()

        # Actualizar tamaño de la agenda compartida (local) en pestaña servidor
        agenda_path = getattr(main_win, 'agenda_path', None)
        if agenda_path and os.path.exists(agenda_path):
            sz = get_folder_size(agenda_path)
            self.lbl_server_agenda_size.setText(f"<b>Tamaño de la Agenda compartida:</b> {format_size(sz)}")
        else:
            self.lbl_server_agenda_size.setText("<b>Tamaño de la Agenda compartida:</b> -")

    def _toggle_server(self):
        """Inicia o detiene el servidor HTTP en segundo plano."""
        main_win = self.parent()
        thread = getattr(main_win, 'server_thread', None)

        if thread and thread.is_running:
            # Apagar
            thread.stop()
            setattr(main_win, 'server_thread', None)
            self._update_server_ui_state()
            if hasattr(main_win, '_update_connectivity_status'):
                main_win._update_connectivity_status()
            QMessageBox.information(self, "Servidor Detenido", "El servidor de sincronización se ha detenido correctamente.")
        else:
            # Validar
            port_str = self.srv_port.text().strip()
            if not port_str.isdigit():
                QMessageBox.warning(self, "Puerto inválido", "El puerto de red debe ser un número entero válido.")
                return
            port = int(port_str)
            password = self.srv_pass.text()
            if not password:
                QMessageBox.warning(self, "Contraseña requerida", "Por favor, configure una contraseña para proteger la sincronización.")
                return

            agenda_path = getattr(main_win, 'agenda_path', None)
            if not agenda_path or not os.path.exists(agenda_path):
                QMessageBox.warning(self, "Agenda requerida", "Debe tener una agenda abierta para poder compartirla en modo servidor.")
                return

            # Guardar configuraciones
            self._save_current_settings()

            # Encender
            thread = ConnectivityServerThread(port, password, agenda_path, main_win)
            setattr(main_win, 'server_thread', thread)
            thread.start()
            
            # Esperar arranque breve
            QTimer.singleShot(200, self._update_server_ui_state)
            if hasattr(main_win, '_update_connectivity_status'):
                QTimer.singleShot(200, main_win._update_connectivity_status)
            QMessageBox.information(self, "Servidor Iniciado", f"Servidor compartido activado exitosamente en http://{get_local_ip()}:{port}/")

    def _on_server_log(self, text: str):
        self.txt_srv_log.append(text)

    def _on_server_clients_changed(self):
        self._refresh_server_data()

    def _refresh_server_data(self):
        """Actualiza la tabla de clientes conectados y lee el log físico si aplica."""
        main_win = self.parent()
        thread = getattr(main_win, 'server_thread', None)
        if not thread or not thread.is_running:
            return

        # Refrescar clientes
        self.tbl_clients.setRowCount(0)
        for ip, info in thread.connected_clients.items():
            row = self.tbl_clients.rowCount()
            self.tbl_clients.insertRow(row)
            self.tbl_clients.setItem(row, 0, QTableWidgetItem(info['name']))
            self.tbl_clients.setItem(row, 1, QTableWidgetItem(ip))
            self.tbl_clients.setItem(row, 2, QTableWidgetItem(info['last_seen']))

        # Recargar log desde archivo físico para mostrar historial persistente completo
        log_file = os.path.join(thread.agenda_path, 'data', 'connectivity_log.json')
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                
                log_lines = []
                for entry in log_data[-40:]:  # Mostrar últimos 40 eventos
                    log_lines.append(f"[{entry['timestamp']}] IP: {entry['ip']} ({entry['client']}) - {entry['description']}")
                
                self.txt_srv_log.setPlainText("\n".join(log_lines))
            except:
                pass

    def _kick_selected_client(self):
        """Desconecta temporalmente al cliente seleccionado."""
        curr_row = self.tbl_clients.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Seleccionar cliente", "Por favor, seleccione un cliente de la tabla.")
            return

        ip = self.tbl_clients.item(curr_row, 1).text()
        client_name = self.tbl_clients.item(curr_row, 0).text()

        main_win = self.parent()
        thread = getattr(main_win, 'server_thread', None)
        if thread:
            thread.kicked_ips.add(ip)
            if ip in thread.connected_clients:
                del thread.connected_clients[ip]
            thread.log_activity(ip, client_name, "Desconectado/expulsado por el administrador.")
            self._refresh_server_data()
            QMessageBox.information(self, "Cliente expulsado", f"El cliente con IP {ip} ha sido desconectado.")

    def _block_selected_ip(self):
        """Bloquea y agrega la IP del cliente a la lista negra."""
        curr_row = self.tbl_clients.currentRow()
        if curr_row < 0:
            QMessageBox.warning(self, "Seleccionar cliente", "Por favor, seleccione un cliente de la tabla.")
            return

        ip = self.tbl_clients.item(curr_row, 1).text()
        client_name = self.tbl_clients.item(curr_row, 0).text()

        main_win = self.parent()
        thread = getattr(main_win, 'server_thread', None)
        if thread:
            thread.blocked_ips.add(ip)
            if ip in thread.connected_clients:
                del thread.connected_clients[ip]
            thread.log_activity(ip, client_name, "IP BLOQUEADA por seguridad.")
            self._refresh_server_data()
            QMessageBox.information(self, "IP Bloqueada", f"La dirección IP {ip} ha sido bloqueada y añadida a la lista negra.")

    def _test_connectivity(self):
        """Prueba la conexión HTTP y credenciales contra el servidor remoto."""
        ip = self.cli_ip.text().strip()
        port_str = self.cli_port.text().strip()
        password = self.cli_pass.text()
        client_name = self.cli_name.text().strip()

        if not ip or not port_str or not password or not client_name:
            QMessageBox.warning(self, "Campos requeridos", "Por favor, complete todos los campos en la sección de cliente.")
            return

        self._save_current_settings()
        self.btn_test_conn.setEnabled(False)
        self.lbl_sync_status.setText("Probando conexión...")

        base_url = f"http://{ip}:{port_str}"
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        try:
            req = urllib.request.Request(f"{base_url}/handshake", headers={
                'X-Auth-Token': password_hash,
                'X-Client-Name': client_name
            })
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                server_name = data.get('server', 'Desconocido')
                server_version = data.get('version', 'Desconocida')
                server_size = data.get('agenda_size', 0)
                
                main_win = self.parent()
                if main_win:
                    main_win.client_connected = True
                    main_win.client_server_ip = ip
                    if hasattr(main_win, '_update_connectivity_status'):
                        main_win._update_connectivity_status()
                
                # Actualizar tamaño remoto en la interfaz
                self.lbl_remote_agenda_size.setText(f"<b>Tamaño de Agenda en Servidor:</b> {format_size(server_size)}")
                
                if server_version != APP_VERSION:
                    QMessageBox.warning(
                        self,
                        "Alerta de Compatibilidad",
                        f"¡ADVERTENCIA DE COMPATIBILIDAD!\n\n"
                        f"Se estableció la conexión, pero hay discrepancia de versiones:\n"
                        f"- Servidor: v{server_version}\n"
                        f"- Cliente (Local): v{APP_VERSION}\n\n"
                        f"Para evitar daños o inconsistencias en los datos compartidos, "
                        f"por favor actualice ambos equipos a la misma versión."
                    )
                else:
                    QMessageBox.information(
                        self, 
                        "Conexión Exitosa", 
                        f"Conectado correctamente con el servidor: {server_name}\n"
                        f"Versión compatible: v{server_version}"
                    )
                self.lbl_sync_status.setText("Conexión de prueba exitosa.")
        except Exception as e:
            QMessageBox.critical(self, "Error de Conexión", f"No se pudo establecer comunicación con el servidor:\n{str(e)}")
            self.lbl_sync_status.setText("Fallo de conexión.")
        finally:
            self.btn_test_conn.setEnabled(True)

    def _start_sync(self, mode: str):
        """Inicia el proceso de sincronización en segundo plano."""
        main_win = self.parent()
        agenda_path = getattr(main_win, 'agenda_path', None)
        if not agenda_path or not os.path.exists(agenda_path):
            QMessageBox.warning(self, "Agenda requerida", "Debe tener una agenda abierta localmente para poder sincronizar.")
            return

        ip = self.cli_ip.text().strip()
        port_str = self.cli_port.text().strip()
        password = self.cli_pass.text()
        client_name = self.cli_name.text().strip()

        if not ip or not port_str or not password or not client_name:
            QMessageBox.warning(self, "Campos requeridos", "Por favor, complete todos los campos de conexión del cliente.")
            return

        self._save_current_settings()

        # Deshabilitar botones
        self.btn_sync_pull.setEnabled(False)
        self.btn_sync_push.setEnabled(False)
        self.btn_sync_both.setEnabled(False)
        self.progress_bar.setValue(0)

        # Arrancar hilo de sincronización
        self.sync_thread = SyncWorkerThread(mode, ip, int(port_str), password, client_name, agenda_path)
        self.sync_thread.progress.connect(self._on_sync_progress)
        self.sync_thread.finished_sync.connect(self._on_sync_finished)
        self.sync_thread.start()

    def _on_sync_progress(self, value: int, message: str):
        self.progress_bar.setValue(value)
        self.lbl_sync_status.setText(message)

    def _on_sync_finished(self, success: bool, message: str):
        self.btn_sync_pull.setEnabled(True)
        self.btn_sync_push.setEnabled(True)
        self.btn_sync_both.setEnabled(True)
        
        if success:
            # Recalcular tamaño local y remoto tras sincronización
            main_win = self.parent()
            agenda_path = getattr(main_win, 'agenda_path', None)
            if agenda_path and os.path.exists(agenda_path):
                sz = get_folder_size(agenda_path)
                self.lbl_client_agenda_size.setText(f"<b>Tamaño de Agenda Local:</b> {format_size(sz)}")
                self.lbl_remote_agenda_size.setText(f"<b>Tamaño de Agenda en Servidor:</b> {format_size(sz)}")

            QMessageBox.information(self, "Sincronización Completada", message)
            self.lbl_sync_status.setText("Sincronización completada exitosamente.")
            
            # Recargar la agenda para que los datos nuevos se muestren inmediatamente en pantalla
            if main_win:
                main_win.client_connected = True
                main_win.client_server_ip = self.cli_ip.text().strip()
                if hasattr(main_win, '_update_connectivity_status'):
                    main_win._update_connectivity_status()
                    
            if hasattr(main_win, '_reload_agenda'):
                main_win._reload_agenda()
        else:
            QMessageBox.critical(self, "Error en Sincronización", message)
            self.lbl_sync_status.setText("Error en la sincronización.")

    def closeEvent(self, event):
        # Desconectar señales de actualización para evitar referencias colgantes
        main_win = self.parent()
        thread = getattr(main_win, 'server_thread', None)
        if thread:
            try:
                thread.log_event.disconnect(self._on_server_log)
                thread.clients_changed.disconnect(self._on_server_clients_changed)
            except:
                pass
        self.refresh_timer.stop()
        super().closeEvent(event)
