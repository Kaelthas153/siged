# Evidencia de verificación · Semana 1

Fecha de ejecución: 21 de octubre de 2026. Entorno local Windows, Python 3.12.14, Django 5.2.18, psycopg 3.3.6 y PostgreSQL 18.2.

## Resultado ejecutado

`python manage.py test incidents --verbosity 2`: **18 pruebas aprobadas**, 208,456 segundos. Base temporal independiente `test_siged`. Se adjunta la salida en `resultado-pruebas.txt`.

`python manage.py check`: sin incidencias. `python manage.py makemigrations --check --dry-run`: sin cambios de modelos pendientes.

| Área | Casos aprobados |
|---|---|
| Sesión | Redirección anónima; inicio y salida; salida por POST |
| Privacidad | Listado propio; ficha ajena 404; notas internas ocultas al ciudadano |
| Permisos | Operador/coordinador sin alta ni administración; administrador fuera del flujo operativo; rechazo de roles múltiples |
| Registro | Autor/estado controlados por servidor; rechazo de fecha futura, catálogo inactivo y descripción vacía |
| Integridad | Reversión del incidente cuando falla su historial; estado inválido rechazado por PostgreSQL |
| Seguridad web | CSRF exigido; HTML escapado; intento de elevar privilegios ignorado al crear una cuenta |
| Administración | Alta auditada sin contraseñas ni hashes en el detalle; catálogos auditados; borrado denegado |
| Concurrencia | Dos conexiones y dos incidentes distintos compiten por 5 unidades: una reserva de 4 aceptada, otra rechazada, saldo 1 e historial único |

## Comprobación visual y límites

La página de acceso y su hoja de estilos se abrieron en el navegador local y se inspeccionó su presentación. Las vistas de listado, detalle y administración fueron ejercitadas mediante el cliente de pruebas de Django. No se declara una evaluación visual completa de todos los tamaños de pantalla ni una prueba de carga.

El caso concurrente verifica el servicio técnico con bloqueo de filas PostgreSQL; no existe aún una interfaz pública de reservas. Las cuentas y catálogos de demostración se cargaron en la base local con un usuario de aplicación sin privilegios de superusuario. La revisión docente no fue realizada por estas pruebas y sigue pendiente.
