# SIGED · Semana 2

SIGED significa **Sistema de Gestión de Desastres**. En este proyecto es un prototipo académico de registro y seguimiento simulado de incidentes asociados a amenazas naturales, contextualizado a La Paz. No predice desastres ni recibe emergencias reales.

## Abrir en este equipo

1. Ejecuta **INICIAR.cmd** en esta carpeta. Conserva también la carpeta `work/siged-runtime` del espacio de trabajo: contiene Python y la base local.
2. Abre http://127.0.0.1:8000/.
3. Consulta **.demo-credentials.txt** para las cuatro cuentas y sus contraseñas. Son credenciales locales generadas, excluidas del ZIP.
4. Entra como ciudadano, pulsa **Nuevo reporte**, completa los datos ficticios y abre la ficha creada.
5. Continúa la demostración de revisión y tareas cambiando entre operador, ciudadano y coordinador según `docs/SEMANA_2.md`.
6. El administrador mantiene cuentas, catálogos y auditoría.

La base aislada escucha en 127.0.0.1:55432. No modifica la instalación PostgreSQL de otros proyectos. El servidor web de desarrollo se utiliza solo para la demostración local.

## Lo entregado

- Proyecto Django modular y base PostgreSQL con migraciones reproducibles.
- Cuatro roles exclusivos: ciudadano, operador, coordinador y administrador.
- Inicio y cierre de sesión; contraseñas almacenadas mediante hash; protección CSRF.
- Registro validado de incidentes, código automático, estado inicial e historial atómico.
- Listado paginado y consulta de reportes propios. Un identificador ajeno devuelve 404.
- Revisión, corrección y reenvío; validación, rechazo y vinculación de duplicados.
- Prioridad motivada, inicio de seguimiento y tareas con responsable, vencimiento y resultado.
- Bandejas de revisión y tareas abiertas; controles de concurrencia y versiones desactualizadas.
- Panel de cuentas y catálogos con motivo obligatorio y auditoría; sin eliminación física desde el panel.
- Estructura de tareas y reservas; prueba técnica concurrente de stock, todavía sin interfaz de reservas.
- Datos ficticios y pruebas automatizadas. La suite acumulada tiene 38 pruebas aprobadas. Consulta `docs/SEMANA_2.md` y `docs/PRUEBAS_SEMANA_2.md`; la documentación de semana 1 se conserva como antecedente.

## Explicación breve para exponer

“SIGED es una aplicación web adaptable a celular para reportar incidentes ficticios. En la semana 1 implementé el registro, la base PostgreSQL y los roles. En la semana 2 añadí la revisión: el operador pide correcciones y valida o rechaza; el ciudadano corrige; el coordinador prioriza, asigna tareas e inicia el seguimiento. El operador asignado completa cada tarea con un resultado. Todo queda en el historial”.

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

`--insecure` sirve los estilos con DEBUG=0 exclusivamente en esta demostración local. Una publicación requeriría servidor WSGI, HTTPS, archivos estáticos, copias de seguridad y configuración de producción; no está incluida en esta entrega.

## Repetir las pruebas

En este equipo ejecuta `scripts/PROBAR.ps1`. Usa una base aislada llamada `test_siged_semana2` y la conserva con `--keepdb`. En otra instalación, configura un usuario de desarrollo con permiso para crear la base de pruebas y sigue `docs/PRUEBAS_SEMANA_2.md`. Nunca utilices el nombre de la base operativa como `DB_TEST_NAME`. Las pruebas no utilizan los reportes de demostración.

## Organización

| Carpeta | Responsabilidad |
|---|---|
| accounts | Usuarios, roles, autenticación y aprovisionamiento |
| incidents | Catálogos, registro, consultas e historial |
| tasks | Asignación, inicio, finalización y cancelación de tareas |
| resources | Catálogo, reservas y prueba técnica de bloqueo |
| audit | Registro administrativo de cambios |
| reports | Espacio reservado para consultas de semana 3 |
| config | Configuración, rutas y panel administrativo |
| docs | Alcance, evidencia y guía de revisión docente |

Las rutas llaman a vistas, formularios y servicios; los servicios aplican permisos y transacciones; los modelos y PostgreSQL mantienen integridad. Las comprobaciones de rol son funcionales, adicionales a la sesión de Django. No se utiliza una cuenta superusuario como administrador funcional.

## Límites y continuidad

Quedan pendientes la revisión docente, reservas y liberación de recursos, resolución/cierre de incidentes, filtros finales y evaluación completa de semanas 3–4. La comprobación móvil se realizó en navegador con ancho de 390 píxeles; falta probar en un teléfono físico. No se deben modificar estados manualmente desde SQL para operar la aplicación.

Referencias técnicas: [Django 5.2](https://docs.djangoproject.com/en/5.2/), [transacciones](https://docs.djangoproject.com/en/5.2/topics/db/transactions/), [bloqueo select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
