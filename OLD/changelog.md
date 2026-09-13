# Historial de Cambios — Vito Organizer

Aquí se lleva el control del desarrollo y las características añadidas en cada versión de la aplicación.

---

## v.1.0 – Junio 2026

### Características Clave
* **Estética Retro/Esqueumórfica**: Recreación de la clásica agenda Lotus Organizer de los años 90.
* **Diseño Física Abierta**: Vista a doble página de libro con anillas centrales metálicas realistas (6 anillas) y costuras de cuero.
* **Pestañas Verticales de Colores**: Pestañas de acceso rápido a cada sección colocadas en los bordes izquierdo y derecho del mazo de hojas.
* **Navegación de Secciones**: Menú dedicado `Sección` para saltar a cualquier módulo o a la página de **Portada**.

### Módulos Implementados
* **Portada**: Página de presentación que muestra el nombre de la agenda, la versión de software, la ruta del archivo y estadísticas de uso de la base de datos.
* **Calendario**:
  * **Vista Diaria**: Horario de 8:00 a 22:00 en la página izquierda, y listas de tareas, llamadas y notas rápidas a la derecha.
  * **Vista Agenda**: Vista semanal con organización clásica.
  * **Vista Mensual**: Grilla completa del mes seleccionado con marcas de eventos.
  * **Vista Semestral**: Vista panorámica de 6 meses (el mes actual y los 5 siguientes) para un control de fechas a largo plazo.
  * **Eventos**: Creación de anotaciones y alertas de fechas específicas (reemplazando el concepto de reuniones).
* **Notas**: Bloc de notas basado en Markdown con renderizado HTML en tiempo real y división de pantalla (editor / vista previa).
* **Inventario**: Control de existencias de componentes electrónicos por cantidad y ubicación física.
* **Instrumentos**: Bitácora para el estado del banco de trabajo, controlando calibraciones y estado operativo de multímetros, osciloscopios, etc.
* **Enlaces**: Gestor de marcadores Web categorizados.

### Infraestructura y Datos
* **Base de Datos SQLite**: Almacenamiento local estructurado e independiente por cada agenda.
* **Papelera de Reciclaje Esqueumórfica**:
  * Tacho de zinc clásico en la parte inferior de la barra lateral.
  * Cambia visualmente su estado: vacío si no hay datos, o lleno de papeles arrugados si contiene elementos borrados.
  * Permite recuperar eventos, notas, componentes o marcadores borrados, o vaciarlos permanentemente.
* **Opciones del Sistema (Menú Edición)**:
  * **Autoguardado**: Ajuste de guardado automático para notas y agenda en intervalos personalizables en minutos.
  * **Respaldos**: Utilidad para exportar y empaquetar toda la agenda activa en formato `.zip` desde la interfaz.
