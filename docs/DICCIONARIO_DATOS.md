# Diccionario de datos implementado

Generado desde los modelos de la entrega de semana 1. Los tipos corresponden a PostgreSQL. Las migraciones contienen los índices y restricciones completas.

## accounts_user

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| password | varchar(128) | No | — | No | No |
| last_login | timestamp with time zone | No | — | Sí | No |
| is_superuser | boolean | No | — | No | No |
| username | varchar(150) | No | — | No | Sí |
| first_name | varchar(150) | No | — | No | No |
| last_name | varchar(150) | No | — | No | No |
| is_staff | boolean | No | — | No | No |
| is_active | boolean | No | — | No | No |
| date_joined | timestamp with time zone | No | — | No | No |
| email | varchar(254) | No | — | No | Sí |

## incidents_zone

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| code | varchar(20) | No | — | No | Sí |
| name | varchar(120) | No | — | No | No |
| municipality | varchar(100) | No | — | No | No |
| active | boolean | No | — | No | No |

## incidents_threattype

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| name | varchar(80) | No | — | No | Sí |
| description | text | No | — | No | No |
| active | boolean | No | — | No | No |

## incidents_incident

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| code | varchar(24) | No | — | No | Sí |
| reporter_id | bigint | No | accounts_user | No | No |
| zone_id | bigint | No | incidents_zone | No | No |
| threat_type_id | bigint | No | incidents_threattype | No | No |
| title | varchar(150) | No | — | No | No |
| description | text | No | — | No | No |
| location_reference | text | No | — | No | No |
| occurred_at | timestamp with time zone | No | — | No | No |
| created_at | timestamp with time zone | No | — | No | No |
| updated_at | timestamp with time zone | No | — | No | No |
| status | varchar(24) | No | — | No | No |
| priority | varchar(10) | No | — | Sí | No |
| resolution_summary | text | No | — | Sí | No |
| resolved_at | timestamp with time zone | No | — | Sí | No |
| closed_at | timestamp with time zone | No | — | Sí | No |
| duplicate_of_id | bigint | No | incidents_incident | Sí | No |

## incidents_incidenthistory

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| incident_id | bigint | No | incidents_incident | No | No |
| actor_id | bigint | No | accounts_user | No | No |
| action | varchar(40) | No | — | No | No |
| previous_status | varchar(24) | No | — | Sí | No |
| new_status | varchar(24) | No | — | Sí | No |
| detail | text | No | — | No | No |
| citizen_message | text | No | — | Sí | No |
| task_id | bigint | No | tasks_task | Sí | No |
| reservation_id | bigint | No | resources_reservation | Sí | No |
| created_at | timestamp with time zone | No | — | No | No |

## tasks_task

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| incident_id | bigint | No | incidents_incident | No | No |
| assignee_id | bigint | No | accounts_user | No | No |
| created_by_id | bigint | No | accounts_user | No | No |
| description | text | No | — | No | No |
| status | varchar(15) | No | — | No | No |
| due_at | timestamp with time zone | No | — | No | No |
| created_at | timestamp with time zone | No | — | No | No |
| started_at | timestamp with time zone | No | — | Sí | No |
| finished_at | timestamp with time zone | No | — | Sí | No |
| result | text | No | — | Sí | No |

## resources_resource

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| code | varchar(20) | No | — | No | Sí |
| name | varchar(120) | No | — | No | No |
| unit | varchar(30) | No | — | No | No |
| total | integer | No | — | No | No |
| active | boolean | No | — | No | No |

## resources_reservation

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| incident_id | bigint | No | incidents_incident | No | No |
| resource_id | bigint | No | resources_resource | No | No |
| assigned_by_id | bigint | No | accounts_user | No | No |
| quantity | integer | No | — | No | No |
| assigned_at | timestamp with time zone | No | — | No | No |
| released_at | timestamp with time zone | No | — | Sí | No |
| released_by_id | bigint | No | accounts_user | Sí | No |

## audit_auditlog

| Campo | Tipo SQL | PK | FK destino | Permite NULL | Único |
|---|---|---|---|---|---|
| id | bigint | Sí | — | No | Sí |
| actor_id | bigint | No | accounts_user | No | No |
| entity | varchar(60) | No | — | No | No |
| record_id | bigint | No | — | No | No |
| action | varchar(30) | No | — | No | No |
| detail | jsonb | No | — | No | No |
| created_at | timestamp with time zone | No | — | No | No |

## Tablas auxiliares

Django incorpora tablas de grupos, permisos, relaciones usuario/grupo, sesiones y registro administrativo. La aplicación exige exactamente un grupo funcional por cuenta. El correo además tiene una restricción única sobre Lower(email).