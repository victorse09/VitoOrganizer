# Historial de Cambios — Vito Organizer

Bitácora de desarrollo y control de versiones del proyecto **Vito Organizer**.

---

## v.2.12 — Agosto 2026

### 📖 Centro de Información y Documentación Técnica (Markdown) en Menú Ayuda
* **Nuevo Explorador de Documentación (`InformationDialog`):** Acceso directo desde el menú `Ayuda → Información Técnica y Documentación...` con navegación lateral de artículos `.md` almacenados en `docs/`.
* **Especificación Técnica Completa del Formato `.doki` (`docs/FORMATO_DOKI.md`):** Estructura del paquete ZIP, descripción de `metadata.json`, `content.html`, `content.xml`, subdirectorio `images/`, algoritmos de empaquetado, exportaciones y compatibilidad.
* **Guías Adicionales en Markdown:** Manual de Biblioteca y Visor (`docs/MANUAL_BIBLIOTECA.md`), Guía de Laboratorio e Instrumentación (`docs/GUIA_LABORATORIO.md`) y Arquitectura del Sistema (`docs/ARQUITECTURA_SISTEMA.md`).
* **Visor Interactivo:** Renderizado Markdown nativo con soporte de enlaces externos, filtro de búsqueda y botón para abrir el archivo `.md` original en el editor del sistema.

### ℹ️ Actualización Institucional en Ventana "Acerca de..." (`AboutDialog`)
* Inclusión de la dedicatoria y visión del proyecto:
  * *"Una aplicación para rememorar a **Lotus Organizer** con implementaciones modernas."*
  * *"Desarrollado por **Vitokin** para toda la comunidad Naseriana."*

### 📝 Creador y Editor de Documentos Propios (.doki) en Biblioteca
* **Formato Contenedor Propio `.doki`:** Formato ZIP estructurado con `metadata.json` (identificador, título, autor, fechas, formato de página, orientación, márgenes, tags y versionado), `content.html` (diseño, estilos y tipografía), `content.xml` (representación semántica limpia) y subcarpeta `images/` con recursos gráficos incrustados.
* **Editor en Modo de Página Única (`DokiDocumentEditorWidget`):** Editor de texto enriquecido a pantalla completa con:
  * **Formato de Hoja Dinámico:** Selector de tamaño de página con soporte para **Carta (Letter - Predeterminado)**, **Oficio (Legal)**, **A4**, **A3** y **A5**.
  * **Orientación y Márgenes:** Conmutador para orientación **Vertical (Portrait)** y **Horizontal (Landscape)** con márgenes configurables (Normal 20mm, Estrecho 10mm, Ancho 30mm) y hoja visual con proporciones reales.
  * **Salto de Página Formal (`📄 Salto de Página`):** Inserción de saltos de página que segmentan limpiamente las hojas en la vista del editor y en la exportación a PDF.
  * **Alineación de Texto Completa:** Botones para alineación a la **Izquierda**, **Centrado**, **Derecha** y **Justificado**.
  * **Suite Completa de Formato:** Negrita, Cursiva, Subrayado, Selector de tamaño de fuente (9 a 32 pt), paleta de color de texto y color de resaltador de fondo.
  * Listas con viñetas y Listas numeradas.
  * Inserción de **Tablas Personalizadas** (filas y columnas configurables con bordes y padding).
  * Inserción de **Imágenes Locales** (copiadas al contenedor `.doki` y con previsualización base64 Data-URI).
  * Inserción de **Fórmulas Matemáticas LaTeX** con renderizado automático.
  * Botón directo para pegar texto o recortes desde el portapapeles.
* **Exportación Multiformato Nativa:**
  * **📄 PDF:** Generación nativa de documentos PDF vectoriales de alta resolución respetando tamaño de hoja, orientación y saltos de página.
  * **📚 EPUB:** Creación de libros electrónicos estándar (`application/epub+zip`) con manifest, spine, toc.ncx y xhtml listos para lectores digitales.
  * **📑 OpenDocument (.odt):** Generación de archivos ODF compatibles con LibreOffice, OpenOffice y Word.
  * **⚙️ XML:** Exportación a archivos XML semánticos estructurados.
* **Integración Directa desde el Visor de PDFs y Traductor:**
  * Desde el menú contextual de selección del visor de PDFs: *"📝 Enviar Texto Seleccionado a Doki..."* y *"🖼 Enviar Recorte de Imagen a Doki..."*.
  * Desde el diálogo de OCR (`OCRResultDialog`): botón *"📝 Enviar a Doki..."*.
  * Desde el traductor técnico (`DocTranslateDialog`): botón *"📝 Enviar a Documento Doki..."*.
* **Almacenamiento Organizado:** Todos los documentos se guardan en `<agenda>/biblioteca/doki/` y sus archivos exportados en `<agenda>/biblioteca/doki/exports/`.

### 📚 Visor Integrado de PDF y EPUB en Biblioteca (Modo de Página Única)
* **Visor Completo de Libros y Revistas:** Motor de lectura de alta fidelidad basado en PyMuPDF (`fitz`) para archivos `.pdf` y `.epub` en modo de página única de pantalla completa (`DocViewerSinglePageWidget`).
* **Modos de Visualización:**
  * **Vista Página a Página:** Visualización clásica centrada en la página individual.
  * **Vista Continua:** Flujo vertical continuo con desplazamiento suave entre todas las páginas del documento.
* **Ajustes y Zoom:**
  * **Ajustar al Ancho:** Botón con icono SVG para encajar el ancho del documento al ancho de la pantalla en un solo clic.
  * **Ajustar al Alto / Página Completa:** Botón con icono SVG para ver la página completa ajustada verticalmente.
  * Selector numérico directo de página, botones anterior/siguiente, niveles porcentuales de zoom (`50%` a `200%`) y botón de **Rotación 90°** (`↻`).
* **Panel Lateral con Pestañas:**
  * **Miniaturas:** Vista gráfica previa de todas las páginas del documento.
  * **Marcadores:** Lista interactiva de marcadores guardados por el usuario.
  * **Artículos:** Lista de artículos extraídos con acceso rápido a su PDF y ubicación en la página.
* **Modos de Interacción:** Alternancia entre **Modo Mano** (desplazamiento fluido) y **Modo Recortar / OCR** (selección rectangular de áreas sobre la página).

### 🌐 Traductor Técnico de Electrónica Integrado
* **Traducción Especializada de Documentación:** Traduce al español texto seleccionado, texto reconocido por el OCR, la página actual completa o un rango de páginas de libros y revistas.
* **Arquitectura Multimotor:**
  1. **🤖 IA Local (LM Studio / Ollama):** Modelos LLM locales con prompt de ingeniería que preserva términos y acrónimos estándar (MOSFET, PCB, PWM, SPI, I2C, UART, Datasheet, Pull-up, Ripple, ESR), unidades de medida (V, A, Hz, F, Ω, W, dB) y fórmulas matemáticas.
  2. **🌐 Traductor Online:** Servicio rápido en línea para traducción fluida de párrafos técnicos.
  3. **💾 Traductor Local Offline:** Motor de reglas y léxico especializado en electrónica que opera 100% sin conexión a internet.
* **Diálogo Interactivo (`DocTranslateDialog`):** Vista comparativa lado a lado (Original vs Español), selector de motor, contador de palabras y botones para copiar al portapapeles, enviar a Doki o exportar a `.txt`.

### 📌 Sistema de Marcadores de Página
* **Marcadores Personalizados:** Botón *Marcar Página* en la barra superior para guardar puntos clave de lectura con títulos descriptivos.
* **Salto Directo:** Acceso rápido a cualquier marcador guardado desde la pestaña lateral del visor o directamente desde la ficha derecha de la Biblioteca (`BibRightView`).

### 📑 Extracción y Selector de Artículos (Exportar a PDF)
* **Extractor de Artículos:** Permite seleccionar un rango de páginas (ej. páginas 15 a 22) de cualquier revista o libro y exportarlas como un nuevo documento PDF independiente guardado en `biblioteca/Articulos/`.
* **Gestión en Ficha:** Visualización de todos los artículos extraídos en la ficha derecha con botones dedicados para abrir su PDF individual o saltar a la página inicial en el libro maestro.

### 🔍 Reconocimiento de Texto (OCR) y Recorte de Áreas
* **OCR de Página Completa:** Reconoce y extrae el texto legible de la página completa mediante el botón *OCR*.
* **OCR por Selección:** Selección rectangular interactiva de párrafos, esquemas o diagramas para extraer su texto, traducirlo o enviarlo directamente a un documento Doki.

### ⚙️ Configuración de Apertura de Documentos
* Nueva opción en la configuración de Biblioteca (⚙) para definir el comportamiento predeterminado al abrir documentos PDF/EPUB:
  1. *Usar Visor Integrado de VitoOrganizer* (Recomendado).
  2. *Usar Visor del Sistema Operativo*.
  3. *Preguntar Siempre al Abrir* (con ventana emergente `OpenDocChoiceDialog` y opción de recordar la elección).

### 🔬 Laboratorio: Calibradores, Guías de Calibración y Especificaciones
* **Módulo de Calibradores y Dispositivos de Referencia:** Gestión completa de referencias patrón con persistencia en `laboratorio/calibradores/` y tablas de *Mediciones Realizadas* (importación/exportación Excel/CSV) y *Puntos de Referencia Patrón*.
* **Especificaciones Técnicas en Instrumentos:** Tablas dinámicas de rangos por función con resolución, exactitud porcentual y cuentas.
* **Visualización de Escalas de Contraste en Guías:** Muestra con qué escala y valor se está contrastando cada punto de medición.
* **Suite Completa de Texto Enriquecido en Guías:** Formato completo de texto, tablas HTML, imágenes locales y fórmulas matemáticas LaTeX.
* **Modo Panorámico / Pantalla Completa:** Expansión de fichas y tablas técnicas a pantalla completa sin compresión horizontal.

### 🎨 Iconografía Vectorial SVG Completa
* Estandarización de todos los botones, herramientas y diálogos del visor, biblioteca y creador de documentos utilizando iconos vectoriales SVG tematizados de alto contraste (`get_themed_svg_icon`).

---

## v.2.11 — Agosto 2026

* **Renderizado Automático y Pegado Inteligente de Fórmulas Matemáticas (LaTeX):**
  * Integración del motor de fórmulas LaTeX (`tools/math_renderer.py`).
  * Pegado inteligente (Ctrl+V) de ecuaciones desde la web o documentos Markdown.
  * Incrustación de fórmulas como imágenes base64 Data-URI dentro de documentos HTML.
  * Asistente interactivo *"📐 Fórmula"* con vista previa en vivo y paleta de símbolos matemáticos.
* **Modo Registros de Instrumentos en Laboratorio:**
  * Navegación sincronizada de dos páginas con menú lateral para Ficha, Documentación, Descripción Técnica (HTML), Checklists y Banco de Pruebas de Calibración.
* **Nuevo Apartado "Software / Firmware / Drivers" en Biblioteca.**
* **Soporte Completo para Imágenes AVIF (`.avif`).**
* **Nuevos Plugins "Gestor de Discos y Respaldos" y "Colección Retro y ROMs".**

---

## v.2.10 — Julio 2026

* **Editor CAD 2D de Diagramas Esquemáticos:** Trazado ortogonal inteligente, snapping magnético a pines, manipulación de cables por handles, catálogo de componentes IEEE/IEC y exportación BOM / Netlist SPICE / PNG.
* **Editor IDE de Código:** Resaltado de sintaxis para 10 lenguajes, plantillas para microcontroladores y búsqueda/reemplazo interactivo.
* **Listas de Chequeo y Reportes PDF:** Emisión de informes técnicos formales con logotipo y foliado correlativo.
