# Avance de la semana 2

Actualización: 29 de octubre de 2026. Autor: Cael Mathew Cuevas Alconini. Docente: Brigida Carvajal. Carrera: Informática.

El segundo incremento permite revisar la información de los reportes, solicitar correcciones, reenviarlos, validarlos o rechazarlos y organizar su seguimiento mediante prioridad y tareas. Se conserva la aplicación web adaptable con Django y PostgreSQL; no se requiere una aplicación Android o iOS independiente.

## Funciones implementadas

| Actor | Funciones de esta entrega |
|---|---|
| Ciudadano | Corregir y reenviar un reporte propio observado; consultar mensajes públicos y estado. |
| Operador | Consultar pendientes y reenviados; solicitar corrección; validar; rechazar con motivo interno y mensaje público; vincular un duplicado a un original admisible. Iniciar y completar únicamente tareas asignadas a su cuenta. |
| Coordinador | Definir prioridad con justificación, asignar tareas a operadores activos con vencimiento futuro, iniciar seguimiento y cancelar tareas abiertas con motivo. |
| Administrador | Mantener cuentas y catálogos. No puede desactivar o cambiar el rol de un operador que conserva tareas abiertas. |

## Reglas aplicadas

- El ciudadano conserva el código, propietario y fecha de registro al corregir. La ocurrencia no puede ser posterior al registro original.
- La revisión solo admite reportes pendientes o reenviados. Rechazar exige motivo interno y mensaje público.
- Un original de duplicado debe ser distinto, estar validado, en seguimiento, resuelto o cerrado, y no ser a su vez duplicado. La referencia no se revela a otro ciudadano.
- Priorizar y asignar requieren un incidente validado o en seguimiento. El seguimiento comienza expresamente cuando hay prioridad y al menos una tarea pendiente asignada a un operador activo.
- El operador inicia una tarea pendiente y la completa desde En progreso, con resultado obligatorio, mientras el incidente está en seguimiento.
- Las tareas completadas o canceladas no se reabren ni reasignan. Cancelar exige coordinación y motivo.
- Las escrituras y el historial se guardan en una misma transacción. Los bloqueos de PostgreSQL evitan decisiones simultáneas incompatibles. Los formularios de incidente rechazan una versión desactualizada.
- Los mensajes públicos están separados de los detalles operativos. Las acciones se envían por POST con protección CSRF y validación de rol en el servidor.

## Correspondencia con el cronograma

La tabla organiza los resultados según los días previstos; no representa un registro de horas reales trabajadas.

| Día previsto | Trabajo de la semana 2 | Resultado verificable |
|---|---|---|
| 6 | Revisión y observaciones | Bandeja de pendientes/reenviados y formulario de decisión. |
| 7 | Corrección, reenvío y duplicados | Flujo del propietario y rechazo con original válido. |
| 8 | Prioridad y seguimiento | Motivo de prioridad y comprobación de condiciones antes de iniciar seguimiento. |
| 9 | Tareas | Asignación, vencimiento, inicio, resultado y cancelación. |
| 10 | Integración y verificación | 38 pruebas aprobadas, recorrido en navegador y evidencia móvil. |

## Datos y arquitectura

Se reutilizan las tablas de incidentes, historial, usuarios, roles y tareas definidas en la semana 1; no se añadieron tablas ni migraciones. `makemigrations --check --dry-run` confirmó que no hay cambios pendientes. La base operativa continúa en PostgreSQL.

Las vistas reciben la solicitud y los formularios validan los datos. Los servicios de `incidents/workflow.py` y `tasks/services.py` vuelven a comprobar rol, estado y reglas dentro de transacciones. Los modelos y restricciones de PostgreSQL mantienen las relaciones e integridad.

## Demostración para la docente

1. Abrir `INICIAR.cmd` y entrar a http://127.0.0.1:8000/.
2. Ciudadano: crear un reporte ficticio. Operador: abrirlo y solicitar una corrección concreta.
3. Ciudadano: corregir y reenviar. Mostrar que se conserva su código.
4. Operador: validar la información reenviada.
5. Coordinador: definir prioridad con motivo, asignar una tarea con fecha futura e iniciar seguimiento.
6. Operador asignado: iniciar la tarea, registrar un resultado y completarla.
7. Mostrar el historial y volver al ciudadano para comprobar la información pública.

La demostración del 29 de octubre recorrió estos pasos sobre el incidente ficticio 2, creado en la semana 1. Quedó En seguimiento, prioridad Alta, con la tarea 1 Completada. Completar una tarea no resuelve ni cierra automáticamente el incidente. Para repetir el ciclo desde el inicio, crear otro reporte; no alterar el estado manualmente en la base.

## Verificación y límites

La suite acumulada aprobó 38 pruebas en 70,958 segundos sobre una base PostgreSQL separada. Incluye 20 pruebas nuevas y 18 de la semana 1. Detalle en [PRUEBAS_SEMANA_2.md](PRUEBAS_SEMANA_2.md).

Se comprobó el formulario de resultado y la ficha con un ancho de ventana de 390 píxeles. Se completó la tarea desde esa vista; no se observó desbordamiento horizontal. Esta evidencia corresponde a un navegador de escritorio con tamaño móvil, no a un teléfono físico. Quedan pendientes la aceptación docente, la evaluación completa de accesibilidad y rendimiento y las pruebas en equipos móviles reales.

Las reservas y liberación de recursos, resolución y cierre de incidentes y filtros finales corresponden a la semana 3. El despliegue público de la aplicación no forma parte de esta entrega: GitHub permite consultar el código, no utilizar el servidor local.

## Explicación breve

En la primera semana construí el registro inicial y los roles. En la segunda añadí el flujo de revisión: el operador puede pedir correcciones y el ciudadano responder. Cuando se valida la información, el coordinador fija prioridad y asigna una tarea. El responsable registra su resultado y todo queda en el historial. El sistema es una web adaptable a celular y utiliza PostgreSQL.
