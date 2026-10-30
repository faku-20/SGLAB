# Pendientes de SGLAB

Revisión del 29/10/2026 contra `Proyecto_Ejemplo_SGLAB_Completo.pdf`, el código y
la configuración local. El PDF es un documento modelo; sus resultados de ejemplo
(48/65 requisitos y mediciones de rendimiento) no son resultados de nuestro sistema.
Esta lista no crea ni modifica tareas de GitHub.

## Base implementada

- Recolector Python, generación TOML, envío SCP/SSH, cola e ingesta con spawn.sh
  hacia MariaDB en Docker; pruebas sintéticas de integración aprobadas.
- Web PHP con sesiones, permisos, MFA del asistente, laboratorios, equipos,
  usuarios, asignaciones docentes, comentarios y bajas lógicas.
- Alumno limitado a su PC detectada por IP; docente a su laboratorio vigente;
  asistente como administrador. La integración de GitHub está preparada.
- Diseño adaptado a las maquetas; revisión en Chromium de escritorio y móvil.
- HTTPS con CA local. El usuario confirmó acceso sin advertencias en Brave
  después de reiniciar el navegador. No es una prueba desde todas las PC de la UTU.

## Pendientes prioritarios

| Tarea | Situación y resultado esperado | Referencia del PDF |
|---|---|---|
| Respaldos automáticos y recuperación | Hay respaldos manuales; no se encontró una tarea programada de SGLAB. Programar dump comprimido, retención de siete días y comprobar restauración en una instancia aislada. Conservar también clave MFA, CA/clave TLS y configuración protegida. Prever copia externa semanal. | RF-LNX-11, RF-NET-08; páginas 10–11 |
| Limpieza programada | Definir y ejecutar retención de TOML ya procesados o entregados. No borrar archivos pendientes de envío/ingesta ni rechazos sin resolver por su antigüedad solamente. | RF-LNX-14, RF-NET-06 |
| Login real de estudiantes | Registrar la OAuth App, configurar Client ID/Secret localmente y probar el flujo con un estudiante cuyo email principal verificado coincida. Las pruebas actuales de OAuth usan un proveedor simulado. | Login/perfiles del PDF y flujo acordado a partir de la referencia del profesor |
| Estado funcional reportado | El alumno puede comentar su PC, pero falta un reporte explícito de funciona/no funciona. Mantenerlo separado de OK/ERROR de lectura y del estado administrativo que modifica el asistente. | RF-WEB-04/05 |
| Importación masiva | Importar estudiantes y PC desde archivo con validación de filas, duplicados, roles e identidades y asignación de equipos al laboratorio. Las altas individuales ya existen. | RF-PHP-10, RF-WEB-06 |
| Consultas y reportes | Ampliar historial con filtros por fecha, equipo y estado; agregar gráficos y exportaciones. Revisar el alcance de endpoints de registros solicitados por el modelo; la web actual usa rutas PHP GET/POST. | RF-PHP-11 a 15, RF-WEB-08, RNF-02 |
| Prueba real en UTU | El recolector ya fue probado allí. Falta probar instalación por usuario, inicio de sesión, envío SSH, recepción, ingesta y consulta en la web; guardar evidencias. Validar además que la IP que recibe Apache permita identificar correctamente la PC. | RF-NET-01/09 y validación del flujo completo |
| Receptor SSH con permisos mínimos | Preparar una cuenta dedicada a recibir TOML y comprobar el envío con ella; actualmente el perfil de pruebas usa facu. | RF-LNX-09 y seguridad de infraestructura |

La frecuencia de respaldo del modelo es inconsistente: la página 10 menciona cada
hora y la 11 cada 24 horas. Hay que fijar y documentar una frecuencia para el proyecto.

## Completar o validar después

- Captura de espacio libre por sistemas de archivos: el esquema contempla los
  datos, pero la captura/ingesta completa todavía requiere ampliación.
- Diagnóstico de latencia y aviso por email cuando falta la serie, si se mantienen
  en el alcance final (RF-NET-07/11). Ya se recopilan IP, gateway y DNS; existe la
  alternativa de identidad por UUID SMBIOS.
- Verificación previa del directorio remoto y diagnóstico claro de conexión SSH.
- Medición de listados con 10.000 equipos, exportaciones con 50.000 registros,
  disponibilidad y auditoría de accesibilidad. Las pruebas funcionales y visuales
  actuales no acreditan esos objetivos (RNF-02/03/04).
- Revisar el script de aprovisionamiento con un despliegue limpio en otro entorno;
  el servidor activo no prueba por sí solo que todo el instalador sea reproducible.
- ESRE propio, matriz requisito/prueba/evidencia, actualización de diagramas de
  clases/casos de uso/despliegue/red, cronograma y responsables. Hay diagramas
  históricos en `../doc`; necesitan contrastarse con la implementación actual.
- Documentar las diferencias respecto del modelo: Python autorizado por el
  profesor, MariaDB/Docker/Rocky, fechas DATETIME UTC frente a epoch y daemon de
  ingesta cada cinco segundos frente a la carga horaria del ejemplo. Confirmar
  qué infraestructura Proxmox/AD/GPO/DNS debe demostrar el equipo y cuál ya provee
  la institución. No modificar esos servicios institucionales por esta revisión.

Prioridad de trabajo sugerida: respaldos y recuperación, limpieza, GitHub y
reportes funcionales/importaciones. La prueba física en UTU puede quedar en el
backlog hasta disponer de los equipos.
