# SIGED · Semana 1

SIGED significa **Sistema de Gestión de Desastres**. En este proyecto es un prototipo académico de registro y seguimiento simulado de incidentes asociados a amenazas naturales, contextualizado a La Paz. No predice desastres ni recibe emergencias reales.

## Abrir en este equipo

1. Ejecuta **INICIAR.cmd** en esta carpeta. Conserva también la carpeta `work/siged-runtime` del espacio de trabajo: contiene Python y la base local.
2. Abre http://127.0.0.1:8000/.
3. Consulta **.demo-credentials.txt** para las cuatro cuentas y sus contraseñas. Son credenciales locales generadas, excluidas del ZIP.
4. Entra como ciudadano, pulsa **Nuevo reporte**, completa los datos ficticios y abre la ficha creada.
5. Cierra sesión y entra como administrador para revisar cuentas, zonas, amenazas, recursos y auditoría.

La base aislada escucha en 127.0.0.1:55432. No modifica la instalación PostgreSQL de otros proyectos. El servidor web de desarrollo se utiliza solo para la demostración local.

## Lo entregado

- Proyecto Django modular y base PostgreSQL con migraciones reproducibles.
- Cuatro roles exclusivos: ciudadano, operador, coordinador y administrador.
- Inicio y cierre de sesión; contraseñas almacenadas mediante hash; protección CSRF.
- Registro validado de incidentes, código automático, estado inicial e historial atómico.
- Listado paginado y consulta de reportes propios. Un identificador ajeno devuelve 404.
- Operador y coordinador consultan reportes; sus acciones operativas llegarán en semana 2.
- Panel de cuentas y catálogos con motivo obligatorio y auditoría; sin eliminación física desde el panel.
- Estructura de tareas y reservas; prueba técnica concurrente de stock, todavía sin interfaz de reservas.
- Datos ficticios y pruebas automatizadas. Consulta `docs/SEMANA_1.md` y `docs/PRUEBAS_SEMANA_1.md`.

## Explicación breve para exponer

“Estoy construyendo una aplicación web donde un ciudadano registra un incidente, por ejemplo una inundación ficticia. El sistema guarda quién lo reportó, dónde ocurrió y su descripción. El ciudadano consulta únicamente sus propios reportes. En la primera semana implementé la base de datos, los roles, los catálogos y ese primer flujo. En las próximas semanas añadiré revisión, tareas y reservas. Ya probé que dos solicitudes simultáneas no puedan reservar más unidades de las disponibles”.

## Instalación en otro equipo

Requisitos: Python 3.12 y PostgreSQL 18 (versiones utilizadas). El ZIP contiene código, migraciones y pruebas, no el entorno ni la base local.

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Configura `.env`: clave secreta aleatoria de al menos 40 caracteres, base, usuario, contraseña, host y puerto. Crea una base vacía y un propietario para migraciones; no reutilices contraseñas de ejemplo. Ejecuta con las credenciales del propietario:

```powershell
.\.venv\Scripts\python manage.py migrate
```

Para uso normal configura un usuario PostgreSQL separado sin privilegios de superusuario ni creación de bases. Otórgale USAGE en el esquema public, SELECT/INSERT/UPDATE/DELETE en tablas y USAGE/SELECT en secuencias de esta base. Configura los mismos privilegios predeterminados para futuros objetos del propietario. Cambia `.env` a ese usuario y ejecuta:

```powershell
.\.venv\Scripts\python manage.py seed_demo
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8000 --noreload --insecure
```

`--insecure` sirve los estilos con DEBUG=0 exclusivamente en esta demostración local. Una publicación requeriría servidor WSGI, HTTPS, archivos estáticos, copias de seguridad y configuración de producción; no está incluida en semana 1.

## Repetir las pruebas

En este equipo ejecuta `scripts/PROBAR.ps1`. En otra instalación usa `python manage.py test incidents --verbosity 2` con credenciales de una base de desarrollo cuyo usuario pueda crear y eliminar la base temporal `test_siged`. Nunca ejecutes pruebas contra una configuración de producción. Las pruebas no utilizan los reportes de demostración.

## Organización

| Carpeta | Responsabilidad |
|---|---|
| accounts | Usuarios, roles, autenticación y aprovisionamiento |
| incidents | Catálogos, registro, consultas e historial |
| tasks | Modelo de tareas; acciones previstas para semana 2 |
| resources | Catálogo, reservas y prueba técnica de bloqueo |
| audit | Registro administrativo de cambios |
| reports | Espacio reservado para consultas de semana 3 |
| config | Configuración, rutas y panel administrativo |
| docs | Alcance, evidencia y guía de revisión docente |

Las rutas llaman a vistas, formularios y servicios; los servicios aplican permisos y transacciones; los modelos y PostgreSQL mantienen integridad. Las comprobaciones de rol son funcionales, adicionales a la sesión de Django. No se utiliza una cuenta superusuario como administrador funcional.

## Límites y continuidad

Quedan pendientes la revisión del docente y las funciones de semanas 2–4: corrección/reenvío, validación/rechazo, priorización, asignación y cierre de tareas, liberación de recursos, resolución/cierre, reportes finales y evaluación completa. Las restricciones de base no sustituyen los servicios de transición que todavía deben implementarse. No se deben modificar estados manualmente desde SQL para operar la aplicación.

Referencias técnicas: [Django 5.2](https://docs.djangoproject.com/en/5.2/), [transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/), [bloqueo select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
