# Plan: Monitoreo de Errores y Control de faqture-api

## Resumen Ejecutivo

Sistema completo de monitoreo de errores, control de envíos y corrección de credenciales entre faqture-api (Python, local) y faqture_back (Express, VPS).

## Arquitectura

```
Kenani DB (PostgreSQL, PC local)     faqture_back (VPS)              faqture_front (Vue)
┌──────────────────────┐            ┌──────────────────────┐        ┌──────────────────────┐
│ comercial.empresa    │◀─read/write│ faqture_errors       │◀───────│ Tab "Errores"        │
│  - efactur_empresa   │            │ config_updates       │◀───────│ Corrección remota    │
│  - efactur_url       │            │ faqture_config       │◀───────│ Pausar/Reanudar      │
└──────────────────────┘            └──────────────────────┘        └──────────────────────┘
        ▲                                     ▲
        │                                     │
┌──────────────────────┐                     │
│ faqture-api (Python) │─────────────────────┘
│                      │
│ - Lee credenciales   │
│ - Lee estado pause   │
│ - Envía documentos   │
│ - Reporta errores    │
│ - Polling cada 12h   │
│ - Aplica updates     │
└──────────────────────┘
```

## Flujo de Corrección de Credenciales

### Opción A — Manual en Kenani DB
1. Usuario ve error en faqture_front
2. Usuario actualiza efactur_empresa en Kenani DB directamente
3. faqture-api re-lee credenciales en el próximo ciclo de polling (12h)
4. Error se resuelve automáticamente

### Opción B — Remota desde faqture_front
1. Usuario ve error en faqture_front
2. Usuario ingresa nuevas credenciales en modal
3. faqture_back guarda en config_updates
4. faqture-api hace polling cada 12h, obtiene update
5. faqture-api escribe en Kenani DB
6. faqture-api re-intenta envío

## Flujo de Pausa/Reanudación

1. Usuario hace clic en "Pausar" en faqture_front
2. faqture_back actualiza faqture_config.paused = true
3. faqture-api lee config en cada ciclo (0.5s)
4. Si paused = true, salta el envío de documentos
5. Usuario hace clic en "Reanudar"
6. faqture_back actualiza paused = false
7. faqture-api reanuda envíos

---

## FASE 1: Backend (faqture_back)

### Paso 1.1: Crear migración de DB

Archivo: `faqture_back/database/faqture_monitoring.sql`

```sql
-- Tabla de errores de faqture-api
CREATE TABLE IF NOT EXISTS faqture_errors (
  id SERIAL PRIMARY KEY,
  error_type VARCHAR(50) NOT NULL,
  document_ref VARCHAR(100),
  error_message TEXT,
  resolved BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de actualizaciones de credenciales pendientes
CREATE TABLE IF NOT EXISTS config_updates (
  id SERIAL PRIMARY KEY,
  new_token TEXT,
  new_url TEXT,
  applied BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  applied_at TIMESTAMP
);

-- Tabla de configuración de faqture-api
CREATE TABLE IF NOT EXISTS faqture_config (
  id SERIAL PRIMARY KEY,
  paused BOOLEAN DEFAULT FALSE,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Insertar config por defecto
INSERT INTO faqture_config (paused) VALUES (FALSE)
ON CONFLICT DO NOTHING;
```

### Paso 1.2: Crear controller

Archivo: `faqture_back/src/controllers/faqtureController.js`

Funciones:
- `reportError(req, res)` — Inserta error en faqture_errors
- `getErrors(req, res)` — Lista errores con filtros
- `resolveError(req, res)` — Marca error como resuelto
- `saveConfigUpdate(req, res)` — Guarda actualización de credenciales
- `getPendingUpdates(req, res)` — Retorna updates no aplicados
- `markUpdateApplied(req, res)` — Marca update como aplicado
- `getConfig(req, res)` — Retorna estado de faqture_config
- `pauseService(req, res)` — Pausa envíos
- `resumeService(req, res)` — Reanuda envíos

### Paso 1.3: Crear rutas

Archivo: `faqture_back/src/routes/faqture.routes.js`

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/faqture-errors` | POST | Recibe errores de faqture-api |
| `/api/faqture-errors` | GET | Lista errores (para faqture_front) |
| `/api/faqture-errors/:id/resolve` | PUT | Marca error como resuelto |
| `/api/config-updates` | POST | Guarda actualización de credenciales |
| `/api/config-updates/pending` | GET | faqture-api consulta pendientes |
| `/api/config-updates/:id/apply` | PUT | Marca como aplicada |
| `/api/faqture-config` | GET | faqture-api lee estado |
| `/api/faqture-config/pause` | PUT | Pausa envíos |
| `/api/faqture-config/resume` | PUT | Reanuda envíos |

### Paso 1.4: Registrar rutas en app.js

---

## FASE 2: Backend Python (faqture-api)

### Paso 2.1: Actualizar config.py

Agregar nuevas variables:
```python
backend_url: str
poll_interval: int
```

### Paso 2.2: Actualizar config.ini

Nueva sección:
```ini
[BACKEND]
BACKEND_URL = https://faqtureapi.tsifactur.com
POLL_INTERVAL = 43200
```

### Paso 2.3: Crear ErrorReporter en api/api.py

```python
class ErrorReporter:
    def __init__(self, back_url):
        self.back_url = back_url

    def report(self, error_type, document_ref, error_message):
        try:
            requests.post(f'{self.back_url}/api/faqture-errors', json={
                'error_type': error_type,
                'document_ref': document_ref,
                'error_message': error_message,
            }, timeout=5)
        except Exception:
            pass
```

### Paso 2.4: Crear ConfigPoller en api/api.py

```python
class ConfigPoller:
    def __init__(self, back_url):
        self.back_url = back_url
        self.paused = False
        self._last_poll = 0

    def sync(self, interval):
        now = time.time()
        if now - self._last_poll < interval:
            return
        self._last_poll = now
        try:
            # Check pause state
            res = requests.get(f'{self.back_url}/api/faqture-config', timeout=5)
            self.paused = res.json().get('paused', False)
            # Check pending credential updates
            res = requests.get(f'{self.back_url}/api/config-updates/pending', timeout=5)
            for update in res.json().get('updates', []):
                self._apply_to_kenani(update)
                requests.put(f'{self.back_url}/api/config-updates/{update["id"]}/apply', timeout=5)
        except Exception:
            pass

    def _apply_to_kenani(self, update):
        from base.comercial.db import get_connection
        with get_connection() as cnx:
            with cnx.cursor() as cursor:
                cursor.execute(
                    "UPDATE comercial.empresa SET efactur_empresa=%s, efactur_url=%s WHERE id_empresa=1",
                    (update['new_token'], update['new_url'])
                )
            cnx.commit()
```

### Paso 2.5: Integrar en _handle_send

Categorizar errores y reportar:
```python
if res.status_code in (401, 403) or 'credential' in error_msg.lower():
    reporter.report('credential', doc_ref, error_msg)
elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
    reporter.report('connection', doc_ref, error_msg)
else:
    reporter.report('rejection', doc_ref, error_msg)
```

### Paso 2.6: Actualizar main.py

Agregar polling en el loop:
```python
while running:
    config_poller.sync(config.poll_interval)
    if not config_poller.paused:
        processor.run_cycle()
    time.sleep(0.5)
```

---

## FASE 3: Frontend (faqture_front)

### Paso 3.1: Actualizar apiVoucher.js

Nuevos métodos:
```javascript
getFaqtureErrors(params) {
  return this.get('faqture-errors', params);
}

resolveFaqtureError(id) {
  return this.put(`faqture-errors/${id}/resolve`);
}

saveConfigUpdate(data) {
  return this.post('config-updates', data);
}

getFaqtureConfig() {
  return this.get('faqture-config');
}

pauseFaqtureService() {
  return this.put('faqture-config/pause');
}

resumeFaqtureService() {
  return this.put('faqture-config/resume');
}
```

### Paso 3.2: Crear ErrorsTab.vue

Componente que muestra:
- Cards de resumen: Credenciales (N), Conexión (N), Rechazos (N)
- Tabla de detalles con filtros
- Botón "Corregir" → abre CredentialFixModal

### Paso 3.3: Crear CredentialFixModal.vue

Formulario con:
- Campos: Token (efactur_empresa), URL (efactur_url)
- Botón "Guardar" → envía a faqture_back
- Feedback de éxito/error

### Paso 3.4: Crear PauseButton.vue

Botón toggle:
- Si activo → muestra "Pausar" (verde)
- Si pausado → muestra "Reanudar" (naranja)
- Click → llama a pause/resume endpoint

### Paso 3.5: Actualizar Voucher.view.vue

Agregar tab "Errores" junto a "Comprobantes" y "Rechazados":
```vue
<n-tabs>
  <n-tab-pane name="vouchers" tab="Comprobantes">
    <!-- contenido existente -->
  </n-tab-pane>
  <n-tab-pane name="rejected" tab="Rechazados">
    <!-- contenido existente -->
  </n-tab-pane>
  <n-tab-pane name="errors" tab="Errores">
    <ErrorsTab />
  </n-tab-pane>
</n-tabs>
```

---

## Checklist de Implementación

| # | Tarea | Estado |
|---|-------|--------|
| 1 | Crear migración SQL en faqture_back | Pendiente |
| 2 | Crear controller faqtureController.js | Pendiente |
| 3 | Crear rutas faqture.routes.js | Pendiente |
| 4 | Registrar rutas en app.js | Pendiente |
| 5 | Actualizar config.py (faqture-api) | Pendiente |
| 6 | Actualizar config.ini (faqture-api) | Pendiente |
| 7 | Crear ErrorReporter en api/api.py | Pendiente |
| 8 | Crear ConfigPoller en api/api.py | Pendiente |
| 9 | Integrar reporter en _handle_send | Pendiente |
| 10 | Actualizar main.py con polling | Pendiente |
| 11 | Actualizar apiVoucher.js (faqture_front) | Pendiente |
| 12 | Crear ErrorsTab.vue | Pendiente |
| 13 | Crear CredentialFixModal.vue | Pendiente |
| 14 | Crear PauseButton.vue | Pendiente |
| 15 | Actualizar Voucher.view.vue | Pendiente |
