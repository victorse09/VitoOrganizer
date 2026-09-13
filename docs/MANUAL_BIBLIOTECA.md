# Manual de Biblioteca, Visor PDF/EPUB y Traductor Técnico

**Vito Organizer v2.12**  
**Sección:** Biblioteca Documental

---

## 1. Visor Integrado de PDF y EPUB
El Visor Integrado permite visualizar libros, manuales, datasheets y revistas en **Modo de Página Única** a pantalla completa:

* **Modos de Vista:**
  * *Vista Página a Página:* Vista clásica por hoja individual.
  * *Vista Continua:* Desplazamiento vertical fluido entre todas las páginas del archivo.
* **Ajustes Rápidos:** Botones de *Ajustar al Ancho* y *Ajustar al Alto*.
* **Panel Lateral con Pestañas:**
  * Miniaturas de páginas completas.
  * Marcadores de lectura guardados con notas.
  * Artículos y secciones extraídas.

---

## 2. Traductor Técnico Especializado en Electrónica
Permite traducir selecciones de texto, texto OCR o páginas completas al español:
* **🤖 IA Local (LM Studio / Ollama):** Modelos locales especializados en preservación de acrónimos técnicos (MOSFET, PCB, PWM, SPI, I2C, UART), unidades de medida y fórmulas matemáticas.
* **🌐 Servicio Online:** Traducción rápida sin configuraciones adicionales.
* **💾 Motor Local Offline:** Diccionario y reglas de ingeniería 100% desconectado.

---

## 3. Extracción de Artículos y Reconocimiento OCR
* **Selector de Artículos:** Extrae un rango de páginas como un nuevo archivo `.pdf` independiente en `biblioteca/Articulos/`.
* **OCR por Selección y Página:** Reconoce texto de zonas seleccionadas y permite enviarlo a un documento Doki o traducirlo.

---

## 4. Creador y Editor de Documentos Doki (.doki)
Permite redactar documentos enriquecidos propios, exportar a PDF, EPUB, ODT y XML, e integrar directamente recortes de imágenes o traducciones.
