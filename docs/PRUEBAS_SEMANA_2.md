# Verificación de la semana 2

Ejecución: 29 de octubre de 2026. Resultado: **38 pruebas aprobadas en 70,958 segundos**, sin fallos. Django no detectó problemas de configuración; no hay migraciones pendientes.

## Cobertura

| Grupo | Comprobaciones |
|---|---|
| Revisión | Permisos, observaciones obligatorias, validación, rechazo, mensajes públicos y privados, criterios de duplicado. |
| Corrección | Solo propietario, estado permitido, conservación de identidad y fecha, fecha inválida y reversión ante error. |
| Prioridad y seguimiento | Estado permitido, justificación, prioridad y tarea pendiente como condiciones de seguimiento. |
| Tareas | Operador activo, vencimiento futuro, propietario, inicio, resultado obligatorio, cancelación motivada y estados terminales. |
| Integridad | Cambios e historial atómicos, formulario desactualizado y dos decisiones simultáneas con una sola transición aceptada. |
| Administración | Bloqueo del cambio de rol o desactivación de operadores con tareas abiertas. |
| Regresión | Las 18 pruebas anteriores de autenticación, registro, aislamiento, catálogos, auditoría, CSRF, escape HTML y reserva concurrente siguen aprobadas. |

Archivos: `incidents/test_week2.py` (20 pruebas nuevas) y `incidents/tests.py` (18 anteriores). La prueba técnica de reservas no representa una interfaz de reservas ya terminada.

## Reproducción

En el equipo de demostración ejecutar `scripts/PROBAR.ps1`. Utiliza credenciales del propietario local solo durante las pruebas y restaura las variables del entorno al finalizar.

En otro equipo, configurar una conexión de desarrollo cuyo usuario pueda crear la base de pruebas:

```powershell
$env:DB_TEST_NAME='test_siged_semana2'
python manage.py test incidents --verbosity 2 --keepdb --noinput
```

Se conserva esta base exclusivamente de pruebas mediante `--keepdb`. Nunca configurar `DB_TEST_NAME` con el nombre de la base operativa. Los casos usan datos aislados, no los reportes de demostración. Un primer intento con una base antigua se bloqueó al eliminarla en PostgreSQL local; se detuvo y la ejecución completa se realizó con la base separada indicada. No se modificaron los reportes operativos para resolver ese problema.

## Comprobación manual

Se recorrieron en el navegador: solicitud de corrección, reenvío por ciudadano, validación, prioridad, asignación, inicio de seguimiento, inicio de tarea y resultado final. Se verificaron las pantallas de coordinador, operador y ciudadano. El formulario de completar tarea se utilizó con un ancho de 390 píxeles, y la ficha no presentó desplazamiento horizontal.

Las capturas adjuntas al informe corresponden a datos ficticios y no contienen contraseñas. No se realizó una prueba en teléfono físico ni una auditoría de seguridad de producción. Las pruebas de reservas operativas, resolución, cierre y filtros finales se ampliarán en semana 3.
