# Web PHP: login e inventario

La autenticación actual por rol se detalla en [AUTENTICACION.md](AUTENTICACION.md):
MFA para asistente (administrador), GitHub para estudiantes (pendiente de configurar)
y contraseña para docente.
La presentación utiliza las referencias `docs/views.zip` y `docs/public.zip`.
Ver [VISTAS.md](VISTAS.md) para la correspondencia de pantallas y sus adaptaciones.

La aplicación está disponible en https://192.168.50.83, puerto APP_HTTPS_PORT (443).
APP_PORT (8080) redirige las visitas a HTTPS. El backend PHP usa PDO y la cuenta técnica de aplicación;
las credenciales personales se guardan como hash en usuarios.password_hash.

## Crear el primer administrador

Desde `/home/facu/-TD2_SGLAB/SGLAB`, ejecutar en una terminal interactiva:

```bash
docker compose exec web php bin/crear-admin.php
```

Pide cédula (solo números), nombre, apellido, correo opcional y contraseña de 12
a 72 bytes con confirmación. La contraseña no se muestra ni se pasa por argumentos.
No hay una contraseña predeterminada. Si la CI ya existe, el comando se detiene
sin modificar su cuenta. También rechaza correos duplicados. El archivo está
fuera de public y solo se ejecuta por CLI. No usar `exec -T`, porque deshabilita
la terminal necesaria para ocultar la contraseña.

Después, abrir la web con esa cédula y contraseña, y vincular Google Authenticator
con el QR y código de confirmación del primer ingreso. Las credenciales
web son independientes del usuario SSH del receptor y de las cuentas de MariaDB.

## Permisos y alcance

| Rol | Consulta | Comentarios | Administración |
|---|---|---|---|
| ALUMNO | Estado administrativo y último diagnóstico de la PC detectada por IP | Solo su PC | Ninguna |
| DOCENTE | PC y estados del laboratorio asignado actualmente | Solo su laboratorio vigente | Ninguna |
| ASISTENTE (administrador) | Todos los laboratorios, equipos, estados, historial y diagnósticos | PC y laboratorios | Inventario, usuarios de todos los roles y asignaciones docentes |

Las restricciones se aplican en consultas y POST del servidor, también si se
modifican los IDs o filtros de la URL. Sin una PC identificada o una asignación
vigente no se muestran datos de otros recursos. El alumno no accede a listados
globales, usuarios, laboratorios ni detalles técnicos completos de las capturas.

### Identificación automática de la PC del alumno

Se usa exclusivamente REMOTE_ADDR (IP real que recibe Apache), no cabeceras
X-Forwarded-For proporcionadas por el navegador. Se compara con red.ipv4 de la
última captura de cada PC, ordenada por fecha de evento e ID. La PC y su laboratorio
deben estar activos. La captura debe haberse recibido en las últimas ocho horas.
El límite se configura con SGLAB_PC_IP_MAX_AGE_HOURS en .env (de 1 a 24) y se
aplica al recrear la web con Docker Compose.

Si la IP no coincide o coincide con más de una PC, se deniega el acceso y se pide
una captura nueva o asistencia. No se usa la CI declarada en el TOML para ampliar
permisos ni se deduce una PC a partir de registros de uso antiguos del alumno.
Una IP obsoleta por DHCP puede identificar un equipo incorrecto mientras todavía
sea reciente: para esta modalidad conviene reservar IP por PC y enviar capturas
al iniciar sesión. Si hay NAT, proxy o accesos por túnel, Apache puede ver una IP
compartida que no coincide con la captura y la detección no funcionará. Validar
la red real de la UTU antes de confiar en esta identificación; no prueba posesión
de una máquina ni sustituye una vinculación con un identificador de dispositivo.

### Asignación temporal de docentes

En Usuarios y asignaciones, el asistente o administrador selecciona docente,
laboratorio, inicio y fin opcional. Las fechas usan UTC y el formulario lo indica.
Inicio vacío significa ahora; fin vacío dura hasta revocar o reemplazar.
Cada docente tiene una asignación actual (se reemplaza al cambiar de laboratorio).
Las asignaciones futuras o vencidas no dan acceso. Finalizar una asignación corta
el acceso inmediatamente sin exigir un nuevo login. Esta primera versión no guarda
un historial de reemplazos de asignaciones ni soporta reservas de varios turnos.

### Usuarios y bajas

El asistente es el administrador del sistema: puede crear, editar y desactivar
cuentas de todos los perfiles y restablecer sus contraseñas locales. Los alumnos
acceden con GitHub. No puede quitar el último asistente administrador activo. Desactivar o cambiar el rol finaliza la asignación
docente; la cuenta desactivada pierde sus sesiones en la siguiente solicitud.
No se muestran hashes ni contraseñas existentes.

Eliminar PC o laboratorios archiva (activo=0), sin borrar historia. Antes de
archivar un laboratorio hay que retirar sus PC activas y finalizar sus asignaciones
docentes vigentes/futuras. Se pueden consultar eliminados y restaurarlos. Una PC
archivada pierde acceso estudiantil y no recibe nuevas capturas de spawn.sh.

## Uso

1. Ingresar según el rol: MFA para asistente administrador, contraseña para docente, GitHub para estudiante.
2. En Laboratorios, crear la sala con su nombre; se puede renombrar después.
3. En Equipos, registrar la PC y seleccionar el laboratorio y estado administrativo.
4. Informar una serie real o UUID SMBIOS, o ambos; al menos uno es obligatorio.
5. Ejecutar el cliente de esa PC. El daemon la reconoce por esos identificadores.
6. Consultar el resumen y el detalle de la PC para ver hasta 25 capturas recientes.

La serie se normaliza a mayúsculas y el UUID se valida y normaliza. No se admiten
identificadores de relleno ni UUID vacíos/todos F. Las identidades son únicas.
El hostname es opcional. El laboratorio es obligatorio al dar de alta desde la web,
aunque la BD admita NULL para datos históricos.

El inventario tiene búsqueda por nombre/serie/UUID, filtros de laboratorio y estado,
y paginación de 25 PC. La eliminación es lógica y preserva el historial; también se puede marcar una PC
en reparación o fuera de servicio sin archivarla.
El estado administrativo no se cambia al recibir una captura.

Las fechas de captura se muestran en UTC. El laboratorio actual de una PC y la
etiqueta declarada por el cliente son datos distintos. El cliente no reasigna PC.
La cédula declarada por la ventana provisional no autentica a una persona; solo
se vincula a usuarios si la CI ya existe en la BD.

## Sesiones y protección

- Hash de contraseña con password_hash/password_verify; sin contraseñas por defecto.
- Segundo factor TOTP obligatorio para asistentes administradores.
- Estudiantes exclusivamente por GitHub, con email principal verificado y cuenta activa.
- Sesión regenerada al ingresar y salir; vencimiento por 15 minutos de inactividad
  y duración máxima de 8 horas.
- Cookie Secure, HttpOnly y SameSite=Lax en el acceso HTTPS.
- Token CSRF en todos los POST, incluido login/logout.
- Consultas preparadas PDO y salida HTML escapada.
- Límite de 10 intentos fallidos por combinación IP/cédula durante 15 minutos;
  se guarda en el volumen web_state para persistir entre recreaciones de la web.
- Cabeceras CSP, no-store, protección frente a inclusión en frames y nosniff.
- Errores técnicos en logs del servidor; sin mostrar SQL ni credenciales en pantalla.

HTTPS está configurado con una CA local. Instalar su certificado público en las
PC del laboratorio antes de ingresar: [HTTPS.md](HTTPS.md). Apache atiende TLS
directamente y mantiene la IP del cliente para detectar la PC del alumno.
La IP de acceso y el certificado deben revisarse si cambia la red del servidor.

## Estructura y cambios

```text
server/web/app/
├── public/
│   ├── index.php              # Entrada: rutas, POST, sesión y errores
│   └── assets/               # app.css, img/, svg/ y fonts/ (recursos locales)
├── src/
│   ├── bootstrap.php          # PDO y funciones compartidas
│   ├── Auth.php               # Autenticación, sesiones y límite de intentos
│   ├── Inventory.php          # Inventario y bajas lógicas
│   ├── Access.php             # Alcance por rol e identificación por IP
│   ├── People.php             # Cuentas y asignaciones docentes
│   └── Comments.php           # Comentarios autorizados por recurso
├── views/                     # Login, MFA, cabecera/pie, paneles y administración
└── bin/crear-admin.php         # Alta interactiva del administrador
```

Solo public es accesible por Apache. Los archivos PHP se copian en la imagen;
para aplicar cambios hay que reconstruir la web, sin recrear ni borrar la BD:

```bash
docker compose up -d --build web
docker compose logs --tail 50 web
```

Se aplicó la migración 003, con respaldo previo, para asignaciones docentes,
comentarios de laboratorio y bajas lógicas. Se agregaron permisos técnicos
limitados sobre esas dos tablas; no se otorgó DELETE a la web.
El volumen sglab_web_state contiene el límite de intentos y la clave de cifrado MFA;
respaldar esta clave junto con la BD según AUTENTICACION.md. La BD continúa en sglab_db_data y la cola en var/.

## Pruebas

Pruebas locales comunes:

```bash
python3 -m unittest discover -s tests -v
```

La integración HTTP es optativa porque escribe datos sintéticos en el despliegue
activo. Requiere Docker, web, BD y sglab-spawn activos. Ejecutar solo en el entorno
de pruebas. Crea cuentas y registros temporales y luego los elimina:

```bash
SGLAB_TEST_WEB=1 python3 -m unittest discover -s tests -v
```

Cubre login correcto/incorrecto, CSRF, cookies, alta/edición de inventario,
identidades duplicadas, escape HTML, filtros, ingesta real de una PC dada de alta
por PHP, permisos de lectura, retiro de rol, logout, 404 y expiración de sesión. tests/test_role_scope.py verifica además
alumnos por IP (sin coincidencia y con IP ambigua), docentes con vigencia,
comentarios permitidos/prohibidos, gestión restringida de cuentas, archivado y
revocación de accesos.
La limpieza usa root desde el contenedor DB: la cuenta de la web no tiene DELETE.
Se comprobó también sintaxis PHP. La adaptación de las vistas se revisó con
Chromium en escritorio y móvil, usando cuentas sintéticas. Las evidencias y las
diferencias respecto de las maquetas se detallan en [VISTAS.md](VISTAS.md).
La prueba en una PC real de la UTU sigue pendiente.

## Pendientes fuera de este módulo

Importación masiva de usuarios, recuperación de contraseñas por autoservicio,
gráficos, exportación, consulta ampliada del documento y discos, y pruebas
de rendimiento/accesibilidad. La prueba de envío desde una PC real de la UTU
sigue en el backlog; esta prueba de integración genera el TOML en el servidor.

## Equivalencia con el ejemplo del profesor

El actor Administrador del ZIP es nuestro ASISTENTE. No hay dos niveles de
administración. Los tres perfiles funcionales son ASISTENTE, DOCENTE y ALUMNO.
La BD conserva el valor ADMINISTRADOR como alias compatible para cuentas antiguas;
no se crea como perfil separado en la web. Ambas cuentas de prueba de personal
administrativo conservan sus credenciales y ahora exigen MFA. Las cuentas nuevas
se guardan como ASISTENTE. El comando recomendado es
`docker compose exec web php bin/crear-asistente.php`; crear-admin.php se conserva
como alias del mismo comando.
