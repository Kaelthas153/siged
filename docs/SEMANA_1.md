# Entrega académica · Semana 1

## Objetivo y criterio de aceptación

Entregar una base ejecutable donde una cuenta ciudadana aprovisionada por el administrador pueda iniciar sesión, registrar un incidente ficticio y consultar exclusivamente sus reportes. La información inicial y su historial deben persistir juntos.

## Trabajo organizado por día

| Día | Plan original | Producto verificable |
|---|---|---|
| 1 · 6 h | Requisitos 2 h, arquitectura 2 h, entorno 2 h | Alcance de este documento, módulos Django y PostgreSQL aislado |
| 2 · 6 h | Modelos/migraciones 3 h, catálogos/admin 2 h, auditoría 1 h | Migraciones versionadas y panel con motivos |
| 3 · 6 h | Autenticación/roles 4 h, pruebas 2 h | Cuatro perfiles exclusivos y pruebas de acceso |
| 4 · 6 h | Registro 3 h, listado propio 1 h, historial/pruebas 2 h | Formulario, listado, detalle e historial transaccional |
| 5 · 4 h + 2 h reserva | Smoke 1 h, concurrencia 2 h, revisión docente 1 h | Pruebas y guía de demostración; reunión docente pendiente |

Las horas son estimaciones del cronograma, no horas efectivamente trabajadas ni evidencia de una reunión realizada.

## Requisitos implementados en este incremento

| ID local | Requisito | Evidencia |
|---|---|---|
| S1-01 | Autenticación y cierre de sesión | /ingresar/ y /salir/ |
| S1-02 | Un rol funcional y restricciones por operación | accounts/roles.py y pruebas de permisos |
| S1-03 | Alta de usuarios y catálogos con motivo | /administracion/ y audit.AuditLog |
| S1-04 | Reportar con zona/tipo activos y fecha no futura | IncidentForm y create_incident |
| S1-05 | Autor, código y estado inicial controlados por servidor | Servicio y prueba de inyección de campos |
| S1-06 | Consultar solo reportes propios | Consulta filtrada y detalle 404 ajeno |
| S1-07 | Registro e historial indivisibles | Transacción y prueba de fallo simulado |
| S1-08 | Viabilidad técnica del control de stock | Dos conexiones concurrentes: 5 unidades, dos reservas de 4 |

Estos identificadores pertenecen a esta entrega, no renumeran los requisitos de la propuesta. Seguridad inicial: CSRF, escape HTML, hash de contraseñas, mínimo 10 caracteres en altas del panel, correo único sin distinguir mayúsculas, roles comprobados en servidor, panel sin borrado y auditoría sin contraseñas. Rendimiento, accesibilidad completa, recuperación de contraseña y seguridad de producción todavía no han sido evaluados integralmente.

## Modelo implementado

Cada tabla tiene PK `id`; las relaciones se materializan como columnas `<campo>_id`.

| Entidad / tabla Django | Campos principales y relaciones |
|---|---|
| Usuario / accounts_user | username, email único, password hash, nombre, activo; grupos Django para rol exclusivo |
| Zona / incidents_zone | code único, name, municipality, active |
| Amenaza / incidents_threattype | name único, description, active |
| Incidente / incidents_incident | code único, reporter→Usuario, zone→Zona, threat_type→Amenaza, título, descripción, ubicación referencial, fechas, estado, prioridad, resolución, duplicate_of→Incidente opcional |
| Historial / incidents_incidenthistory | incident→Incidente, actor→Usuario, acción, estados anterior/nuevo, detalle interno, mensaje ciudadano, task→Tarea opcional, reservation→Reserva opcional, fecha |
| Tarea / tasks_task | incident→Incidente, assignee/created_by→Usuario, descripción, estado, fechas y resultado |
| Recurso / resources_resource | code único, name, unit, total, active; reservado y disponible se calculan |
| Reserva / resources_reservation | incident→Incidente, resource→Recurso, assigned_by/released_by→Usuario, quantity, fechas |
| Auditoría / audit_auditlog | actor→Usuario, entity, record_id, action, detail JSON, created_at |

Un usuario reporta muchos incidentes; cada incidente tiene varios eventos, tareas y reservas. Las reservas relacionan incidentes y recursos. Las FK usan protección de borrado. Los modelos y migraciones contienen el diccionario exacto de tipos, longitudes, índices y restricciones.

## Demostración de 5 minutos

1. Iniciar sesión como ciudadano y mostrar el reporte ficticio inicial.
2. Registrar un ejemplo con fecha pasada, zona activa y descripción; abrir su ficha y mostrar “Pendiente de revisión”.
3. Intentar una fecha futura: debe mostrar un error y no guardar.
4. Cerrar sesión; ingresar como administrador y mostrar catálogos y auditoría. El administrador no accede al listado operativo.
5. Mostrar el resultado de pruebas y explicar el caso de stock. La reserva aún es una prueba técnica, no una pantalla terminada.

## Acta de revisión docente · PENDIENTE

- Fecha: por completar después de la reunión.
- Docente y estudiante: por completar.
- Versión revisada: Semana 1.
- Elementos demostrados: por completar.
- Observaciones y cambios solicitados: por completar.
- Criterios aceptados/rechazados: por completar.
- Responsable y fecha de cada ajuste: por completar.
- Aprobación: pendiente. No se presupone por haber preparado esta entrega.

## Próximo incremento

Semana 2 implementará los servicios de transición de estado y permisos operativos, corrección y reenvío ciudadano, tareas y su historial. Semana 3 integrará reservas/liberaciones y reportes. Semana 4 cerrará validación integral y documentación. Antes de avanzar, revisar con el docente nombres de roles, campos obligatorios y tamaño del alcance.
