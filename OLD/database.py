# -*- coding: utf-8 -*-
"""
Vito Organizer — Capa de Acceso a Datos (SQLite3)
Gestiona todas las operaciones CRUD para los módulos de la aplicación.
Cada agenda tiene su propia base de datos independiente.
"""

import sqlite3
import os
from datetime import datetime, date


class Database:
    """
    Clase principal de acceso a datos.
    Encapsula todas las operaciones SQLite3 para una agenda específica.
    """

    def __init__(self, db_path: str):
        """
        Inicializa la conexión a la base de datos.
        
        Args:
            db_path: Ruta completa al archivo database.sqlite de la agenda.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Acceso por nombre de columna
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._crear_tablas()

    def _crear_tablas(self):
        """Crea todas las tablas si no existen."""
        cursor = self.conn.cursor()

        # ── Tabla de Eventos (Calendario) ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                start_datetime TEXT NOT NULL,
                end_datetime TEXT NOT NULL,
                color TEXT DEFAULT '#3498DB',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Tabla de Notas ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                filename TEXT NOT NULL UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Tabla de Componentes (Inventario) ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER DEFAULT 0,
                location TEXT DEFAULT '',
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Tabla de Instrumentos ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                model TEXT DEFAULT '',
                last_calibration TEXT DEFAULT '',
                status TEXT DEFAULT 'Operativo',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Tabla de Marcadores (Enlaces) ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT DEFAULT 'General',
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # ── Tabla de Papelera ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trash (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                title TEXT NOT NULL,
                original_data TEXT NOT NULL,
                deleted_at TEXT NOT NULL
            )
        ''')

        # ── Tabla de Configuración ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        ''')

        # ── Tabla de Tareas Diarias ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                task_date TEXT NOT NULL
            )
        ''')

        # ── Tabla de Llamadas Diarias ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact TEXT NOT NULL,
                phone TEXT DEFAULT '',
                done INTEGER DEFAULT 0,
                call_date TEXT NOT NULL
            )
        ''')

        # ── Tabla de Notas Diarias ──
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_notes (
                note_date TEXT PRIMARY KEY,
                content TEXT DEFAULT ''
            )
        ''')

        self.conn.commit()

    def insertar_datos_ejemplo(self):
        """Inserta datos de ejemplo en una agenda recién creada."""
        cursor = self.conn.cursor()

        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM components")
        if cursor.fetchone()[0] > 0:
            return  # Ya tiene datos, no insertar duplicados

        # ── Componentes de ejemplo ──
        componentes = [
            ("AD9833", 3, "Cajón A1", "Generador de señales DDS"),
            ("Condensador Tantalio 10uF", 25, "Cajón B2", "Condensador SMD de tantalio"),
            ("Resistencia 10K Ohm", 100, "Cajón A3", "Resistencia 1/4W 5%"),
            ("Arduino Nano", 5, "Estante C1", "Microcontrolador ATmega328P"),
            ("LED Rojo 5mm", 50, "Cajón B1", "LED difuso estándar"),
            ("ESP32-WROOM-32", 3, "Estante C2", "Módulo WiFi+BT"),
        ]
        cursor.executemany(
            "INSERT INTO components (name, quantity, location, description) VALUES (?, ?, ?, ?)",
            componentes
        )

        # ── Instrumentos de ejemplo ──
        instrumentos = [
            ("Multímetro", "Fluke 287", "2025-03-15", "Operativo", "True RMS, registrador de datos"),
            ("Osciloscopio", "Rigol DHO804", "2025-06-01", "Operativo", "4 canales, 80MHz"),
            ("Fuente de alimentación", "Korad KA3005D", "2024-12-10", "Operativo", "0-30V, 0-5A"),
            ("Generador de funciones", "Siglent SDG1032X", "2025-01-20", "Pendiente calibración",
             "2 canales, 30MHz"),
            ("Analizador lógico", "Saleae Logic 8", "", "Operativo", "8 canales, 25MHz digital"),
        ]
        cursor.executemany(
            "INSERT INTO instruments (name, model, last_calibration, status, notes) VALUES (?, ?, ?, ?, ?)",
            instrumentos
        )

        # ── Marcadores de ejemplo ──
        marcadores = [
            ("Datasheet AD9833", "https://www.analog.com/media/en/technical-documentation/data-sheets/AD9833.pdf",
             "Datasheets", "DDS Waveform Generator"),
            ("Foro de Electrónica", "https://www.forosdeelectronica.com/",
             "Foros", "Comunidad hispana de electrónica"),
            ("DigiKey", "https://www.digikey.com/", "Proveedores", "Distribuidor de componentes"),
            ("Mouser Electronics", "https://www.mouser.com/", "Proveedores", "Distribuidor global"),
            ("Arduino Reference", "https://www.arduino.cc/reference/en/",
             "Datasheets", "Referencia oficial de Arduino"),
            ("EEVblog Forum", "https://www.eevblog.com/forum/",
             "Foros", "Foro de ingeniería electrónica"),
            ("LCSC Electronics", "https://www.lcsc.com/", "Proveedores", "Componentes desde China"),
        ]
        cursor.executemany(
            "INSERT INTO bookmarks (title, url, category, description) VALUES (?, ?, ?, ?)",
            marcadores
        )

        # ── Evento de ejemplo ──
        hoy = date.today()
        cursor.execute(
            "INSERT INTO events (title, description, start_datetime, end_datetime, color) VALUES (?, ?, ?, ?, ?)",
            ("Bienvenido a Vito Organizer",
             "Tu primera agenda está lista. ¡Explora las diferentes secciones!",
             f"{hoy.isoformat()} 10:00",
             f"{hoy.isoformat()} 11:00",
             "#27AE60")
        )

        self.conn.commit()

    # ═══════════════════════════════════════════════════════════
    # EVENTOS (CALENDARIO)
    # ═══════════════════════════════════════════════════════════

    def obtener_eventos(self, fecha_inicio: str = None, fecha_fin: str = None) -> list:
        """Obtiene eventos, opcionalmente filtrados por rango de fechas."""
        cursor = self.conn.cursor()
        if fecha_inicio and fecha_fin:
            cursor.execute(
                "SELECT * FROM events WHERE start_datetime >= ? AND start_datetime <= ? ORDER BY start_datetime",
                (fecha_inicio, fecha_fin)
            )
        else:
            cursor.execute("SELECT * FROM events ORDER BY start_datetime")
        return [dict(row) for row in cursor.fetchall()]

    def obtener_eventos_por_fecha(self, fecha: str) -> list:
        """Obtiene eventos de un día específico (formato: YYYY-MM-DD)."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM events WHERE start_datetime LIKE ? ORDER BY start_datetime",
            (f"{fecha}%",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def obtener_eventos_por_mes(self, anio: int, mes: int) -> list:
        """Obtiene todos los eventos de un mes."""
        cursor = self.conn.cursor()
        prefijo = f"{anio:04d}-{mes:02d}"
        cursor.execute(
            "SELECT * FROM events WHERE start_datetime LIKE ? ORDER BY start_datetime",
            (f"{prefijo}%",)
        )
        return [dict(row) for row in cursor.fetchall()]

    def crear_evento(self, title: str, description: str, start_dt: str, end_dt: str,
                     color: str = "#3498DB") -> int:
        """Crea un nuevo evento y devuelve su ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO events (title, description, start_datetime, end_datetime, color) VALUES (?, ?, ?, ?, ?)",
            (title, description, start_dt, end_dt, color)
        )
        self.conn.commit()
        return cursor.lastrowid

    def actualizar_evento(self, event_id: int, title: str, description: str,
                          start_dt: str, end_dt: str, color: str):
        """Actualiza un evento existente."""
        self.conn.execute(
            """UPDATE events SET title=?, description=?, start_datetime=?, 
               end_datetime=?, color=? WHERE id=?""",
            (title, description, start_dt, end_dt, color, event_id)
        )
        self.conn.commit()

    def eliminar_evento(self, event_id: int):
        """Elimina un evento por su ID (lo envía a la papelera)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title FROM events WHERE id=?", (event_id,))
        row = cursor.fetchone()
        if row:
            self._mover_a_papelera('events', event_id, row['title'])
            cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
            self.conn.commit()

    # ═══════════════════════════════════════════════════════════
    # NOTAS
    # ═══════════════════════════════════════════════════════════

    def obtener_notas(self) -> list:
        """Obtiene todas las notas ordenadas por fecha de actualización."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def crear_nota(self, title: str, filename: str) -> int:
        """Crea un registro de nota y devuelve su ID."""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO notes (title, filename, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (title, filename, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def actualizar_nota(self, note_id: int, title: str):
        """Actualiza el título y la fecha de modificación de una nota."""
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE notes SET title=?, updated_at=? WHERE id=?",
            (title, now, note_id)
        )
        self.conn.commit()

    def eliminar_nota(self, note_id: int):
        """Elimina un registro de nota por su ID (lo envía a la papelera)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title FROM notes WHERE id=?", (note_id,))
        row = cursor.fetchone()
        if row:
            self._mover_a_papelera('notes', note_id, row['title'])
            cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
            self.conn.commit()

    def obtener_nota_por_id(self, note_id: int) -> dict | None:
        """Obtiene una nota específica por su ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM notes WHERE id=?", (note_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ═══════════════════════════════════════════════════════════
    # COMPONENTES (INVENTARIO)
    # ═══════════════════════════════════════════════════════════

    def obtener_componentes(self) -> list:
        """Obtiene todos los componentes."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM components ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def buscar_componentes(self, texto: str) -> list:
        """Busca componentes por nombre o ubicación."""
        cursor = self.conn.cursor()
        patron = f"%{texto}%"
        cursor.execute(
            "SELECT * FROM components WHERE name LIKE ? OR location LIKE ? OR description LIKE ? ORDER BY name",
            (patron, patron, patron)
        )
        return [dict(row) for row in cursor.fetchall()]

    def crear_componente(self, name: str, quantity: int, location: str, description: str = "") -> int:
        """Crea un nuevo componente y devuelve su ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO components (name, quantity, location, description) VALUES (?, ?, ?, ?)",
            (name, quantity, location, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def actualizar_componente(self, comp_id: int, name: str, quantity: int,
                              location: str, description: str = ""):
        """Actualiza un componente existente."""
        self.conn.execute(
            "UPDATE components SET name=?, quantity=?, location=?, description=? WHERE id=?",
            (name, quantity, location, description, comp_id)
        )
        self.conn.commit()

    def eliminar_componente(self, comp_id: int):
        """Elimina un componente por su ID (lo envía a la papelera)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM components WHERE id=?", (comp_id,))
        row = cursor.fetchone()
        if row:
            self._mover_a_papelera('components', comp_id, row['name'])
            cursor.execute("DELETE FROM components WHERE id=?", (comp_id,))
            self.conn.commit()

    # ═══════════════════════════════════════════════════════════
    # INSTRUMENTOS
    # ═══════════════════════════════════════════════════════════

    def obtener_instrumentos(self) -> list:
        """Obtiene todos los instrumentos."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM instruments ORDER BY name")
        return [dict(row) for row in cursor.fetchall()]

    def crear_instrumento(self, name: str, model: str, last_calibration: str,
                          status: str, notes: str = "") -> int:
        """Crea un nuevo instrumento y devuelve su ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO instruments (name, model, last_calibration, status, notes) VALUES (?, ?, ?, ?, ?)",
            (name, model, last_calibration, status, notes)
        )
        self.conn.commit()
        return cursor.lastrowid

    def actualizar_instrumento(self, inst_id: int, name: str, model: str,
                               last_calibration: str, status: str, notes: str = ""):
        """Actualiza un instrumento existente."""
        self.conn.execute(
            "UPDATE instruments SET name=?, model=?, last_calibration=?, status=?, notes=? WHERE id=?",
            (name, model, last_calibration, status, notes, inst_id)
        )
        self.conn.commit()

    def eliminar_instrumento(self, inst_id: int):
        """Elimina un instrumento por su ID (lo envía a la papelera)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM instruments WHERE id=?", (inst_id,))
        row = cursor.fetchone()
        if row:
            self._mover_a_papelera('instruments', inst_id, row['name'])
            cursor.execute("DELETE FROM instruments WHERE id=?", (inst_id,))
            self.conn.commit()

    # ═══════════════════════════════════════════════════════════
    # MARCADORES (ENLACES)
    # ═══════════════════════════════════════════════════════════

    def obtener_marcadores(self) -> list:
        """Obtiene todos los marcadores ordenados por categoría."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM bookmarks ORDER BY category, title")
        return [dict(row) for row in cursor.fetchall()]

    def obtener_categorias(self) -> list:
        """Obtiene la lista de categorías únicas."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM bookmarks ORDER BY category")
        return [row[0] for row in cursor.fetchall()]

    def obtener_marcadores_por_categoria(self, category: str) -> list:
        """Obtiene marcadores de una categoría específica."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM bookmarks WHERE category=? ORDER BY title",
            (category,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def crear_marcador(self, title: str, url: str, category: str, description: str = "") -> int:
        """Crea un nuevo marcador y devuelve su ID."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO bookmarks (title, url, category, description) VALUES (?, ?, ?, ?)",
            (title, url, category, description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def actualizar_marcador(self, bm_id: int, title: str, url: str,
                            category: str, description: str = ""):
        """Actualiza un marcador existente."""
        self.conn.execute(
            "UPDATE bookmarks SET title=?, url=?, category=?, description=? WHERE id=?",
            (title, url, category, description, bm_id)
        )
        self.conn.commit()

    def eliminar_marcador(self, bm_id: int):
        """Elimina un marcador por su ID (lo envía a la papelera)."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT title FROM bookmarks WHERE id=?", (bm_id,))
        row = cursor.fetchone()
        if row:
            self._mover_a_papelera('bookmarks', bm_id, row['title'])
            cursor.execute("DELETE FROM bookmarks WHERE id=?", (bm_id,))
            self.conn.commit()

    # ═══════════════════════════════════════════════════════════
    # UTILIDADES
    # ═══════════════════════════════════════════════════════════

    # ═══════════════════════════════════════════════════════════
    # PAPELERA DE RECICLAJE
    # ═══════════════════════════════════════════════════════════

    def _mover_a_papelera(self, tabla: str, item_id: int, titulo: str):
        """Mueve un elemento a la tabla 'trash' antes de ser borrado."""
        import json
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT * FROM {tabla} WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        if row:
            datos_dict = dict(row)
            datos_json = json.dumps(datos_dict)
            ahora = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO trash (item_type, title, original_data, deleted_at) VALUES (?, ?, ?, ?)",
                (tabla, titulo, datos_json, ahora)
            )

    def obtener_items_papelera(self) -> list:
        """Obtiene la lista de elementos en la papelera."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trash ORDER BY deleted_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def recuento_papelera(self) -> int:
        """Devuelve la cantidad de elementos en la papelera."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trash")
        return cursor.fetchone()[0]

    def vaciar_papelera(self):
        """Elimina permanentemente todos los elementos de la papelera."""
        self.conn.execute("DELETE FROM trash")
        self.conn.commit()

    def restaurar_item_papelera(self, trash_id: int) -> bool:
        """Restaura un elemento de la papelera a su tabla original."""
        import json
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trash WHERE id=?", (trash_id,))
        row = cursor.fetchone()
        if not row:
            return False

        item_type = row['item_type']
        original_data = json.loads(row['original_data'])

        # Insertar de vuelta en la tabla original
        columnas = list(original_data.keys())
        valores = [original_data[col] for col in columnas]
        placeholders = ", ".join(["?"] * len(columnas))
        query = f"INSERT OR REPLACE INTO {item_type} ({', '.join(columnas)}) VALUES ({placeholders})"
        
        try:
            cursor.execute(query, valores)
            # Eliminar de la papelera
            cursor.execute("DELETE FROM trash WHERE id=?", (trash_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error al restaurar: {e}")
            return False

    # ═══════════════════════════════════════════════════════════
    # CONFIGURACIÓN (SETTINGS)
    # ═══════════════════════════════════════════════════════════

    def obtener_config(self, clave: str, valor_defecto: str = "") -> str:
        """Obtiene un valor de configuración de la base de datos."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key=?", (clave,))
        row = cursor.fetchone()
        if row:
            return row['value']
        return valor_defecto

    def guardar_config(self, clave: str, valor: str):
        """Guarda o actualiza un valor de configuración."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (clave, str(valor))
        )
        self.conn.commit()

    def cerrar(self):
        """Cierra la conexión a la base de datos."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Destructor: asegura el cierre de la conexión."""
        self.cerrar()
