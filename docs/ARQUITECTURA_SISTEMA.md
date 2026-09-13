# Arquitectura del Sistema Vito Organizer

**Vito Organizer v2.12**  
*Una aplicación para rememorar a Lotus Organizer con implementaciones modernas.*

---

## 1. Visión General
Vito Organizer está diseñado sobre una arquitectura modular desacoplada en Python 3 y PyQt6:

* **Core (`core/`):** Gestor de ventana principal, barra de menú, libro interactivo con anillas, pestañas esqueumórficas, sistema de ayuda e historial.
* **Plugins (`plugins/`):** Módulos independientes cargados dinámicamente:
  * Portada, Calendario, Planificador, Tareas, Cumpleaños, Notas, Gastos, Biblioteca, Bodega, Laboratorio, Respaldos y ROMs.
* **Tools (`tools/`):** Calculadora electrónica, conversor de unidades, asistente IA local, motor de renderizado matemático LaTeX (`math_renderer.py`).
* **Data (`data/`):** Almacenamiento local estructurado en JSON y ZIP con versionado y compatibilidad hacia atrás.
