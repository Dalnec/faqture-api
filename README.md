# Faqture API

Sistema de procesamiento continuo de comprobantes electrónicos (facturas, boletas, notas de crédito, notas de venta y guías de remisión) para SUNAT. Lee documentos desde una base de datos PostgreSQL local, los envía a un API externo y actualiza el estado de declaración.

## Requisitos

- Python >= 3.14
- PostgreSQL
- `pg_dump` disponible en PATH (para backups)
- Credenciales de Google Cloud (opcional, para backup a Drive)

## Instalación

```bash
# Clonar el repositorio
git clone <repo-url>
cd faqture-api

# Instalar dependencias con uv (recomendado)
uv sync

# O con pip
pip install -r requirements.txt
```

## Configuración

Copiar y editar el archivo de configuración:

```bash
cp config.ini.example config.ini
```

### Secciones de `config.ini`

```ini
; Conexión a PostgreSQL
[BASE]
DB_NAME = nombre_base_datos
DB_USER = postgres
DB_PASS = contraseña
DB_HOST = 127.0.0.1
DB_PORT = 5432

; Backup de base de datos
[BACKUP]
BU_NAME = nombre_backup
BU_STATE = True          ; habilitar backup automático
BU_DRIVE = False         ; subir backup a Google Drive
BU_TIME = 00:00:00       ; hora inicio ventana de backup
BU_TIME2 = 23:59:00      ; hora fin ventana de backup

; Procesos habilitados
[MAIN]
M_DOC = True             ; enviar facturas/boletas
M_ANUL = False           ; enviar anulaciones
M_NCREDI = False         ; enviar notas de crédito
M_NVENTAS = False        ; enviar notas de venta
M_GUIA = False           ; enviar guías de remisión

; Filtro de fecha para consultas
[MODELS]
DATE_HEADER = 2025-01-01

; Opciones de aplicación
[APP]
DEBUG = False

; Opciones de API externa
[API]
SSL_VERIFY = False       ; verificar certificados SSL del API externo
```

## Uso

```bash
# Ejecutar el servicio
python main.py

# Ejecutar en modo debug
# (cambiar DEBUG = True en config.ini)

# Ver versión
python main.py --version
```

El servicio corre en loop continuo ejecutando estos procesos en cada ciclo:

1. **Documentos** — lee ventas pendientes y las envía al API
2. **Anulaciones** — envía solicitudes de anulación
3. **Notas de venta** — envía notas de venta
4. **Notas de crédito** — envía notas de crédito/débito
5. **Guías de remisión** — envía guías
6. **Backup** — crea backup de la BD (si está habilitado y dentro de la ventana horaria)

### Con Docker

```bash
docker-compose up
```
## Backup de Base de Datos

El sistema incluye un módulo de backup automático que ejecuta `pg_dump`, comprime el resultado con gzip y opcionalmente lo sube a Google Drive.

### Flujo del backup

```
pg_dump → .backup → gzip → .backup.gz → Google Drive (opcional)
```

1. Verifica si ya existe un backup del día actual (evita duplicados)
2. Ejecuta `pg_dump` con formato tar (`-F t`)
3. Comprime el archivo con gzip
4. Elimina el archivo sin comprimir
5. Si `BU_DRIVE = True`, sube o actualiza el archivo en Google Drive

### Configuración en `config.ini`

```ini
[BACKUP]
BU_NAME = MiBackup              ; nombre base del archivo (genera MiBackup.backup.gz)
BU_STATE = True                 ; habilitar backup automático
BU_DRIVE = True                 ; subir a Google Drive después de comprimir
BU_TIME = 00:00:00              ; inicio de ventana horaria
BU_TIME2 = 23:59:00             ; fin de ventana horaria
```

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `BU_NAME` | string | Nombre base del archivo de backup |
| `BU_STATE` | bool | Habilitar/deshabilitar backup automático |
| `BU_DRIVE` | bool | Subir backup a Google Drive después de crearlo |
| `BU_TIME` | HH:MM:SS | Hora de inicio de la ventana de ejecución |
| `BU_TIME2` | HH:MM:SS | Hora de fin de la ventana de ejecución |

### Ventana horaria

El backup solo se ejecuta si la hora actual está entre `BU_TIME` y `BU_TIME2`. Ejemplos:

```ini
; Ejecutar solo de noche
BU_TIME = 22:00:00
BU_TIME2 = 06:00:00

; Ejecutar en cualquier momento (ventana completa)
BU_TIME = 00:00:00
BU_TIME2 = 23:59:00

; Ejecutar solo en la madrugada
BU_TIME = 01:00:00
BU_TIME2 = 04:00:00
```

El backup se ejecuta una vez por día. Si ya existe un archivo `.backup.gz` con fecha de hoy, se omite.

### Configurar Google Drive

Para habilitar la subida automática a Google Drive:

#### 1. Crear proyecto en Google Cloud Console

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear un proyecto nuevo o seleccionar uno existente
3. Habilitar la **Google Drive API**

#### 2. Crear credenciales OAuth 2.0

1. Ir a **APIs & Services > Credentials**
2. Click en **Create Credentials > OAuth client ID**
3. Seleccionar **Desktop App** como tipo de aplicación
4. Descargar el archivo JSON de credenciales

#### 3. Colocar credenciales

```bash
# El archivo debe llamarse credentials.json y estar en:
base/credentials.json
```

#### 4. Primera autenticación

En la primera ejecución con `BU_DRIVE = True`:

1. El sistema abrirá un navegador para autorización OAuth
2. Iniciar sesión con la cuenta de Google donde están los archivos
3. Aceptar los permisos de acceso a Drive
4. El token se guarda automáticamente en `token.json` (se reutiliza en ejecuciones futuras)

```
Permisos solicitados:
- drive.appdata  — acceso a datos de aplicación
- drive.file     — acceso a archivos creados por la app
```

#### 5. Estructura de archivos

```
faqture-api/
├── base/
│   └── credentials.json   # Credenciales OAuth (NO versionar)
├── token.json             # Token de acceso (se genera automáticamente, NO versionar)
```

> **Importante**: ni `credentials.json` ni `token.json` deben subirse al repositorio. Verificar que estén en `.gitignore`.

### Ejecución manual de backup

```python
from base.backup.backup import backup
backup()
```

### Requisitos del sistema

- `pg_dump` debe estar disponible en el PATH del sistema
- La contraseña de PostgreSQL se pasa por variable de entorno `PGPASSWORD` (no por línea de comandos)
- El usuario de BD necesita permisos de lectura sobre todas las tablas del esquema `comercial`

## Estructura del proyecto

```
faqture-api/
├── main.py                          # Entry point, loop principal
├── config.py                        # Config dataclass + loader
├── config.ini                       # Configuración (no versionado)
├── logger.py                        # Logger con consola coloreada + archivos rotativos
├── app_info.py                      # Versión y banner de la app
├── pyproject.toml                   # Dependencias y config pytest
│
├── api/
│   └── api.py                       # ApiClient para enviar comprobantes al API externo
│
├── base/
│   ├── backup/
│   │   ├── backup.py                # Lógica de backup PostgreSQL + Drive
│   │   └── send_drive.py            # DriveClient para Google Drive
│   └── comercial/
│       └── db.py                    # Connection pool PostgreSQL + funciones de actualización
│
├── models/
│   └── comercial/
│       ├── base_models.py           # Clases Venta y DetalleVenta compartidas
│       ├── ventas.py                # Lectura de documentos (facturas + notas de venta)
│       ├── models_anulate.py        # Lectura de anulaciones
│       ├── models_notaCredito.py    # Lectura de notas de crédito/débito
│       └── models_guiaRemision.py   # Lectura de guías de remisión
│
├── tests/
│   ├── test_config.py               # Tests de configuración
│   ├── test_api.py                  # Tests de ApiClient (mocked)
│   └── test_models.py               # Tests de lógica de negocio (IGV, descuentos, totales)
│
└── logs/                            # Logs rotativos (faqture.log, faqture_error.log)
```

## Arquitectura

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │────▶│    Models    │────▶│  ApiClient   │────▶ API Externo
│  (lectura)   │     │  (lectura +  │     │  (requests)  │
└─────────────┘     │  JSON build) │     └──────────────┘
                    └──────────────┘
                           │
                    ┌──────────────┐
                    │   DB module  │────▶ PostgreSQL (updates)
                    │  (pool +     │
                    │   escritura) │
                    └──────────────┘

┌─────────────┐     ┌──────────────┐
│   pg_dump    │────▶│   Backup     │────▶ Google Drive (opcional)
└─────────────┘     └──────────────┘
```

### Flujo de documentos

1. Los models consultan PostgreSQL buscando registros con `estado_declaracion = 'PENDIENTE'`
2. Construyen un JSON con el formato requerido por SUNAT (cabecera + detalle + totales)
3. `ApiClient` envía el JSON al API externo vía HTTP POST/PUT
4. Según la respuesta, actualiza el estado a `PROCESADO` o guarda el error

### Connection pooling

`db.py` usa `psycopg2.pool.ThreadedConnectionPool` (1-10 conexiones) con context manager:

```python
with get_connection() as cnx:
    with cnx.cursor() as cursor:
        cursor.execute("SELECT ...", (param,))
```

El pool se inicializa en `main.py` al arrancar y se cierra con `close_pool()` en el shutdown.

## Tests

```bash
# Ejecutar todos los tests
uv run pytest

# Con verbosidad
uv run pytest -v

# Ejecutar un archivo específico
uv run pytest tests/test_models.py

# Ejecutar un test específico
uv run pytest tests/test_models.py::TestGenerateLista::test_totales_con_igv
```

Los tests cubren:
- **Config** — creación y campos booleanos
- **API** — callbacks de success/error, manejo de ConnectionError
- **Models** — generación de JSON con IGV, descuentos, crédito, placa, redondeo

## Dependencias

| Paquete | Uso |
|---------|-----|
| `psycopg2` | Conexión a PostgreSQL |
| `requests` | HTTP al API externo |
| `google-api-python-client` | Google Drive API |
| `google-auth-oauthlib` | OAuth2 para Drive |
| `pyodbc` | Conexión ODBC (futuro) |
| `pytest` | Framework de tests |

## Logs

Los logs se escriben en `logs/` con rotación automática (5 MB, 5 backups):

- `faqture.log` — todos los niveles
- `faqture_error.log` — solo ERROR y CRITICAL

Formato: `2025-06-15 10:30:00 [INFO    ] [module:42] mensaje`

En consola se muestran con colores ANSI.
