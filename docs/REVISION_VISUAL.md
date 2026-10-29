# Unificación visual de SIGED

Revisión del 29 de octubre de 2026. El panel administrativo conservaba la apariencia predeterminada de Django, incluido su tema oscuro automático. Era la principal ruptura con las pantallas iniciales. La plantilla de error 500 tampoco utilizaba el diseño común.

Se reutilizan los colores, tipografía, cabecera, marca, aviso de simulación, tarjetas, campos y botones de `siged.css`. La administración incorpora una adaptación específica, sin cambiar sus permisos ni formularios de negocio. La cabecera, marca y pie se comparten mediante plantillas incluidas. El panel muestra módulos en español; las tablas amplias se desplazan dentro de su tarjeta en móvil.

## Recorrido y resultado

1. Acceso y listado de reportes: se conserva el diseño inicial; verificados en navegador.
2. Panel administrativo: sustituida la apariencia de Django por las tarjetas y colores de SIGED; verificado en navegador.
3. Usuarios y catálogos: listados, altas y edición con controles comunes. Corregidos campos recortados en móvil y tamaños de botones. Verificados visualmente los formularios de usuarios, zonas y recursos; comprobadas las respuestas de amenazas, edición e historial.
4. Auditoría y contraseña: adaptadas al mismo estilo; verificadas visualmente sin cambiar contraseñas ni registros.
5. Ciudadano: listado, registro y ficha mantienen la identidad visual. Verificados en navegador.
6. Operación y coordinación: revisión, tareas abiertas, asignación y prioridad utilizan los componentes compartidos; comprobados formularios de asignación y prioridad a 390 píxeles.
7. Errores: acceso restringido comprobado en el sistema; 400, 403, 404, 500 y rechazo CSRF usan el diseño común. Las plantillas 500 y CSRF se inspeccionaron como vistas previas locales renderizadas, sin provocar una caída real.

## Verificación técnica

- 38 pruebas funcionales aprobadas en 76,902 segundos tras la integración del tema administrativo y la página CSRF.
- 26 pantallas GET de los cuatro roles responden correctamente y contienen la hoja de estilos, la marca y el aviso común. Esta comprobación incluye páginas que comparten las plantillas revisadas; no sustituye una inspección visual de todos los estados posibles.
- Las 5 plantillas de error se renderizan con el diseño común. La protección CSRF sigue devolviendo 403.
- Sin migraciones pendientes. No se modificaron las reglas de negocio ni los datos del escenario de demostración.

Las pruebas móviles se realizaron en un navegador con ventana de 390 × 844 píxeles. Falta la validación en teléfono físico y con lector de pantalla; las capturas no acreditan conformidad completa de accesibilidad. El foco visible se conserva y las tablas tienen desplazamiento horizontal interno.

Las capturas del informe académico de semanas 1 y 2 documentan su estado histórico. La carpeta de evidencia de esta revisión contiene la apariencia actual y la comparación del panel anterior.
