# Historial de Cambios — Vito Organizer

Bitácora de desarrollo y control de versiones del proyecto **Vito Organizer**.

---

## v.2.13 — Octubre 2026

### Gráfico de Contenido en Sección Biblioteca
* **Herramienta de Análisis de Almacenamiento en Biblioteca:** Integración del sistema de gráfico de uso de disco en la sección Biblioteca, accesible mediante un nuevo botón con ícono de gráfico (`chart.svg`) ubicado en la barra lateral inferior, al lado derecho del ícono de configuración (engranaje).
* **Alcance Exclusivo a la Carpeta de Biblioteca:** El escaneo se focaliza exclusivamente en la ruta `<agenda>/biblioteca/`, analizando el tamaño y cantidad de archivos/subcarpetas de cada categoría documental (`Manuales`, `Datasheets`, `Libros`, `Revistas`, `doki`, etc.).
* **Depuración Visual del Diálogo:** Corrección de fondos y estilos en `DiskUsageChartDialog` para eliminar recuadros oscuros accidentales en el título y en el resumen de espacio, integrando las etiquetas con transparencia total.

### Rediseño Estilizado de Barras de Desplazamiento (ScrollBars)
* **Pista y Esquinas Transparentes:** Eliminación de los fondos oscuros sólidos (`#0c0d16`) y recuadros toscos de las barras de scroll en toda la aplicación, permitiendo que la textura y color del papel crema de la agenda fluyan limpiamente.
* **Diseño Minimalista y Delgado:** Reducción del grosor de 12 px a 8 px con tirador redondeado tipo píldora (`border-radius: 4px`) en tono translúcido adaptable (`rgba(130, 140, 160, 0.38)`), ofreciendo una apariencia moderna y armónica tanto sobre hojas claras como sobre paneles oscuros.

### Conversor de Tornillería y Equivalencias Métrico / Pulgadas en Conversor de Unidades
* **Conversor Bidireccional en Vivo (mm ↔ Pulgadas Decimales y Fracciones):** Incorporación de una nueva pestaña ("Tornillos ↔ Pulgadas") con cálculo dinámico en tiempo real entre milímetros, pulgadas en decimales y fracciones comerciales reducidas en base 64 (desde 1/16" hasta 1-1/4"), indicando la aproximación fraccionaria más cercana y el desvío exacto.
* **Tabla Completa de Tornillos Métricos (M):** Catálogo de tornillería métrica ISO (M1.6 hasta M30, incluyendo M4, M6, etc.) con especificación de diámetro nominal, paso de rosca estándar y fino, broca recomendada para macho de roscar, medida de llave para tuerca/cabeza y equivalencia en pulgadas.
* **Tabla de Tornillería y Tuercas en Pulgadas:** Guía técnica para tornillería estándar (#2 hasta 1-1/4", pasos UNC y UNF) con conversión exacta a milímetros, broca de roscado, medida de llave de tuerca y tornillo métrico equivalente más próximo.
* **Búsqueda Dinámica y Copiado Rápido:** Buscador en tiempo real para filtrar por designación (ej: M6, M4, 1/4), medida de broca o llave, sincronización directa con el conversor al hacer clic en cualquier fila de las tablas y botones para copiar resultados o especificaciones técnicas completas al portapapeles.
* **Depuración Estética (Transparencia en Etiquetas):** Corrección de estilos en el conversor de tornillería (`QFrame#calcCard`), eliminando fondos y recuadros oscuros accidentales para que los textos y resultados fluyan con transparencia total y perfecta armonía visual.
* **Purga Integral de Emojis:** Reemplazo de caracteres de emojis en botones de copiado y avisos del conversor por texto claro y homogéneo, garantizando estabilidad visual y compatibilidad tipográfica total entre Linux y Windows.

### Exportación a PDF de Ficha Técnica de Componentes en Laboratorio
* **Generación de Ficha Técnica en PDF:** Integración del exportador a PDF para componentes electrónicos en Laboratorio. El botón de la barra de herramientas principal (`Generar PDF`) y la opción en el menú se habilitan dinámicamente cuando un componente se encuentra seleccionado y visible en la ficha de la página derecha.
* **Diálogo de Configuración de Documento:** Ventana interactiva que permite seleccionar el tamaño de hoja con **Carta** (Letter) por defecto, **Oficio** (Legal) y **A4**; opciones para adjuntar la 1ª página, las 2 primeras páginas o el datasheet completo del PDF vinculado; y casilla para incluir el historial completo de movimientos de inventario (ingresos y egresos).
* **Fusión Vectorial de Datasheets:** Integración de páginas del datasheet mediante PyMuPDF (`fitz`), garantizando texto seleccionable, máxima resolución y fidelidad gráfica del archivo original.
* **Diseño Institucional Homogéneo:** Formato unificado con membrete oscuro (`#222436`), franja naranja corporativa (`#FF5722`), folio correlativo (`CorrelativosManager`), renderizado proporcional de la fotografía del componente y tabla detallada de movimientos de stock.

### Exportación a PDF de Ficha Técnica de Instrumentos en Laboratorio
* **Generación Formal de Ficha Técnica en PDF:** Habilitación reactiva del botón `Generar PDF` en la barra de herramientas principal al seleccionar cualquier instrumento de laboratorio (en la lista de inventario o en la vista detallada de registros).
* **Diálogo Integral de Configuración de Documento:** Ventana que permite seleccionar el tamaño de página con **Carta** (Letter) por defecto, **Oficio** (Legal) y **A4**; opciones modulares para incluir la Ficha Principal (portada con fotografía, marca, modelo, tipo, S/N y estado operativo), Especificaciones Técnicas con tablas de funciones y escalas de medición, Descripción Técnica formateada en HTML y el Historial de Check Lists e inspecciones.
* **Fusión Vectorial de Documentación (Datasheets y Manuales):** Inclusión de páginas seleccionadas (primera página, dos primeras páginas o documento completo) tanto para datasheets técnicos como para manuales de usuario asociados mediante PyMuPDF (`fitz`), conservando nitidez tipográfica y vectorial original.
* **Diseño Institucional Unificado:** Documento formal con membrete corporativo (`#222436`), franja naranja (`#FF5722`), folio correlativo (`CorrelativosManager`), renderizado proporcional de la imagen del instrumento y tablas estilizadas.

### Exportación a PDF de Ficha Técnica de Herramientas en Laboratorio
* **Generación Formal de Ficha Técnica en PDF:** Habilitación reactiva del botón `Generar PDF` en la barra de herramientas principal al seleccionar cualquier herramienta de taller en la vista de Laboratorio.
* **Diálogo Integral de Configuración de Documento:** Ventana que permite seleccionar el formato de página con **Carta** (Letter) por defecto, **Oficio** (Legal) y **A4**; opciones modulares para incluir la Ficha Principal (portada con fotografía, marca, modelo, tipo, estado operativo y notas), casilla para adjuntar el Historial de Chequeos y Mantenimientos, y selector de páginas (primera página, dos primeras páginas o documento completo) para manuales o documentación técnica asociada.
* **Fusión Vectorial de Documentación:** Concatena limpiamente las páginas seleccionadas de los manuales y guías de operación en PDF mediante PyMuPDF (`fitz`), garantizando máxima nitidez vectorial y tipográfica.
* **Diseño Institucional Unificado:** Documento formal con membrete corporativo (`#222436`), franja naranja (`#FF5722`), folio correlativo (`CorrelativosManager`), fotografía proporcional de la herramienta y tablas estilizadas de inspecciones.

---

## v.2.13 — Septiembre 2026

### Paginación y Navegación en Sección de Respaldos
* **Paginación Dinámica del Catálogo de Discos:** Implementación del cálculo adaptativo de elementos por página (`items_per_page`) en función de la altura disponible de la ventana.
* **Integración con la Barra de Herramientas y Encuadernación:** Conexión de las señales `pagination_changed`, `go_to_page`, `get_total_pages` y `get_current_page` con los controles de navegación superior (`< Página X de Y >`) y la rotulación de números de página de la agenda abierta.
* **Segmentación Limpia:** Eliminación de la lista infinita con scroll desbordado, permitiendo una lectura organizada pliego por pliego.

### Mejoras de Visibilidad y Contraste en Biblioteca
* **Iconografía Tematizada en Tarjetas Documentales:** Aplicación de `get_themed_svg_icon` con tono oscuro `#263238` para los iconos de categoría/documento y `#455A64` para el botón de edición rápida (lápiz/cuaderno), garantizando alto contraste y legibilidad sobre el fondo claro del papel.
* **Estilos del Buscador y Botones Laterales:** Ajuste del campo de filtrado (eliminando fondo negro transparente) y mejora visual en los botones de exportación en el panel de lectura. Se ocultaron acciones duplicadas para los archivos propios.
* **Pestañas de Configuración Independientes del SO:** Estandarización estética mediante CSS personalizado para todos los menús de configuración (Global, Laboratorio, Retro, Gastos), anulando la dependencia de temas nativos del sistema operativo (KDE, Cinnamon, Windows) y sustituyendo emojis por íconos SVG unificados para asegurar una apariencia oscura, moderna y homogénea en toda la plataforma.

### Mejoras Mayores en el Editor Doki (.doki)
* **Vista de Documento Continuo (Web Layout) Mejorada:** Rediseño visual del lienzo del editor con cálculo dinámico asíncrono (`documentSizeChanged`) que garantiza que todo el contenido se muestre sin recortes.
* **Indicadores de Página Claros:** Implementación de líneas separadoras segmentadas grises y marcadores de número de página visibles en la esquina derecha que aparecen solo cuando se llena el espacio de la hoja base.
* **Erradicación del Scroll Interno:** Incorporación de cálculo matemático de márgenes (`padding_y`) y evasión intencional de la rueda del ratón (`wheelEvent().ignore()`) en el editor de texto, forzando a que la navegación de la interfaz descanse exclusivamente sobre el deslizador externo general, logrando un flujo suave.
* **Exportación PDF Precisa (WYSIWYG):** Añadido de un botón de exportación rápida a PDF en la barra de herramientas principal. El motor de impresión migró a `ScreenResolution` y fuentes basadas en puntos (`pt`), erradicando las discrepancias de escala (texto minúsculo) y doble marginación en el documento final.

### Correcciones y Optimización en la Sección Notas
* **Optimización de Rendimiento al Escribir:** Se eliminó la reconstrucción innecesaria del panel lateral de notas al tipear (evento `textChanged`), erradicando el parpadeo constante y mejorando la fluidez de escritura en texto plano y Markdown.
* **Corrección del Lienzo a Mano Alzada:** Rediseño del área de dibujo (`HandwritingCanvasWidget`). Se eliminó el fondo sólido que tapaba los trazos, se aplicaron estilos a los menús de grosor y color para hacerlos visibles, y se implementó un mapeo preciso (`_map_to_image`) para alinear matemáticamente el trazo con la punta del cursor sin importar la resolución.
* **Visibilidad de Interfaz Corregida:** Solucionado el problema de texto invisible (blanco sobre blanco) en la tabla de Enlaces Web y en los botones de alternancia de Markdown. Actualización del ícono de "Propiedades" por su versión oscura para mayor legibilidad.

### Ajustes y Mejoras en la Sección Bodega
* **Paginación Adaptativa de Listados:** Incorporación de cálculo automático de filas para la tabla de inventario en función del alto de la ventana, permitiendo navegar pliego por pliego y eliminando las barras de desplazamiento vertical nativas (integración total con el navegador de páginas general).
* **Renovación del Panel de Alertas:** Reemplazo de la inestable tabla de elementos críticos (`QTableWidget`) en la vista de Consolidado por una inyección nativa en HTML/CSS, resolviendo problemas gráficos graves y conflictos de herencia visual con los temas globales.
* **Depuración Visual (UI):** Sustitución de iconografía con problemas de contraste por vectores tematizados (`get_themed_svg_icon`) en botones de la vista detallada (Movimientos, Ficha), mejorando la legibilidad sobre fondos claros.

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
