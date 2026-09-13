# Especificación Técnica del Formato de Archivo `.doki`

**Versión del Formato:** 1.0  
**Software:** Vito Organizer (v2.12+)  
**Autor y Creador:** Vitokin  
**MIME-Type Sugerido:** `application/x-doki+zip`

---

## 1. Introducción

El formato **`.doki`** es un formato de archivo contenedor abierto y estructurado, diseñado específicamente para la creación, intercambio y preservación de documentos técnicos, guías de laboratorio, reportes de ingeniería y notas científicas en **Vito Organizer**.

Un archivo `.doki` es físicamente un archivo comprimido bajo el estándar **ZIP (Deflate)**, que encapsula metadatos en formato JSON, contenido maquetado en HTML con estilos visuales enriquecidos, representación semántica estandarizada en XML y una subcarpeta con los recursos binarios (imágenes, diagramas vectoriales y esquemas).

```
archivo_ejemplo.doki (ZIP)
│
├── metadata.json       # Metadatos del documento (título, autor, fechas, hoja, tags)
├── content.html        # Contenido visual maquetado (HTML5 + CSS + SVG + Data-URIs)
├── content.xml        # Representación semántica en XML puro
└── images/             # Recursos gráficos, recortes de OCR y esquemas incrustados
    ├── img_01.png
    ├── esquema_02.svg
    └── oscilograma_03.jpg
```

---

## 2. Estructura de los Componentes Internos

### 2.1. `metadata.json`
Almacena la información de catalogación, autoría, formato de hoja física, orientación y control de versiones del documento.

```json
{
  "id": "doki_20260831_013000_fuente_smps",
  "title": "Guía de Diseño de Fuentes Conmutadas Flyback",
  "author": "Vitokin",
  "created_at": "2026-08-31",
  "updated_at": "2026-08-31",
  "page_format": "Carta",
  "orientation": "portrait",
  "margin": "normal",
  "description": "Cálculo de transformadores de pulsos, lazo de control y MOSFETs.",
  "filename": "doki_20260831_013000_fuente_smps.doki",
  "relative_path": "biblioteca/doki/doki_20260831_013000_fuente_smps.doki",
  "tags": [
    "doki",
    "electronica",
    "fuentes",
    "laboratorio"
  ],
  "version": "1.0",
  "exports": {}
}
```

#### Campos de `metadata.json`:
* `id` *(string)*: Identificador correlativo y único con marca de tiempo.
* `title` *(string)*: Título principal del documento.
* `author` *(string)*: Nombre del autor o entidad técnica responsable.
* `created_at` / `updated_at` *(string, formato ISO YYYY-MM-DD)*: Fechas de creación y última modificación.
* `page_format` *(string)*: Tamaño físico de la hoja (`Carta` [Letter], `Oficio` [Legal], `A4`, `A3`, `A5`).
* `orientation` *(string)*: Orientación de impresión (`portrait` / `landscape`).
* `margin` *(string)*: Margen predeterminado (`normal` [20mm], `narrow` [10mm], `wide` [30mm]).
* `description` *(string)*: Resumen o descripción técnica del documento.
* `tags` *(array de strings)*: Etiquetas clave para búsqueda rápida.

---

### 2.2. `content.html`
Almacena el texto enriquecido maquetado con estilos CSS tipográficos, tablas con bordes configurables, listas, imágenes locales y fórmulas matemáticas renderizadas.

* **Saltos de Página:** Los saltos de página se delimitan mediante etiquetas formales:
  ```html
  <p style="page-break-before: always; border-top: 2px dashed #1E88E5; padding-top: 8px; margin-top: 20px; color: #1565C0; font-size: 11px; font-weight: bold; text-align: center;">--- SALTO DE PÁGINA ---</p>
  ```
* **Fórmulas Matemáticas:** Las ecuaciones se insertan como imágenes renderizadas de alta fidelidad vía Data-URI base64 con etiqueta `alt` que contiene el código fuente LaTeX original:
  ```html
  <img src="data:image/png;base64,iVBORw0KGgo..." alt="V_{out} = V_{in} \cdot \frac{D}{1-D}" />
  ```

---

### 2.3. `content.xml`
Representación semántica estructurada del documento, facilitando la indexación, transformación y procesamiento automatizado por agentes de software o scripts externos.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<doki-document version="1.0">
  <metadata>
    <id>doki_20260831_013000_fuente_smps</id>
    <title><![CDATA[Guía de Diseño de Fuentes Conmutadas Flyback]]></title>
    <author><![CDATA[Vitokin]]></author>
    <created-at>2026-08-31</created-at>
    <updated-at>2026-08-31</updated-at>
    <page-format>Carta</page-format>
    <orientation>portrait</orientation>
    <margin>normal</margin>
    <description><![CDATA[Cálculo de transformadores de pulsos, lazo de control y MOSFETs.]]></description>
  </metadata>
  <content>
    <![CDATA[
      <h1>Guía de Diseño de Fuentes Conmutadas Flyback</h1>
      <p>Contenido técnico estructurado...</p>
    ]]>
  </content>
</doki-document>
```

---

### 2.4. Directorio `images/`
Contiene todos los archivos binarios de imágenes (PNG, JPEG, WebP, AVIF, SVG) vinculados al documento. Al abrir el archivo `.doki`, el gestor carga las imágenes en memoria caché para visualización instantánea.

---

## 3. Compatibilidad y Exportación Multiformato

El formato `.doki` cuenta con motores nativos de conversión bidireccional dentro de **Vito Organizer**:

1. **Exportación a PDF (`.pdf`):** Generación de documentos vectoriales con `QPrinter` respetando el tamaño de página configurado (`QPageSize`), márgenes y saltos de página.
2. **Exportación a EPUB (`.epub`):** Empaquetado en estándar digital OEBPS/NCX/XHTML listo para e-readers y lectores móviles.
3. **Exportación a OpenDocument Text (`.odt`):** Formato OASIS OpenDocument compatible con suites ofimáticas (LibreOffice Writer, OpenOffice, Microsoft Word).
4. **Exportación a XML (`.xml`):** Archivo XML puro para interoperabilidad y migración de datos.

---

## 4. Almacenamiento en la Agenda

Dentro del directorio de la agenda de trabajo de Vito Organizer:
* Archivos `.doki`: `<agenda>/biblioteca/doki/*.doki`
* Exportaciones generadas: `<agenda>/biblioteca/doki/exports/`
