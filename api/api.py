import requests
import json
import time as _time
import threading

from base.comercial.db import (
    read_empresa_pgsql, update_no_200, update_venta_pgsql,
    update_anulados_pgsql, update_notaCredito_pgsql,
    update_guia_pgsql, update_venta_pgsql_external_id
)
from logger import get_logger
from config import CONFIG
from client_id import get_client_id
from urllib3.exceptions import InsecureRequestWarning

if not CONFIG.api_ssl_verify:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

log = get_logger()
DEBUG = CONFIG.debug
CLIENT_ID = get_client_id()


class ErrorReporter:
    def __init__(self, back_url):
        self.back_url = back_url

    def report(self, error_type, document_ref, error_message):
        if not self.back_url:
            return
        try:
            requests.post(f'{self.back_url}/api/faqture-errors', json={
                'client_id': CLIENT_ID,
                'client_name': CONFIG.client_name,
                'error_type': error_type,
                'document_ref': document_ref,
                'error_message': error_message,
            }, timeout=5)
        except Exception:
            pass


class ConfigPoller:
    def __init__(self, back_url):
        self.back_url = back_url
        self.paused = False
        self._last_poll = 0

    def sync(self, interval):
        if not self.back_url:
            return
        now = _time.time()
        if now - self._last_poll < interval:
            return
        self._last_poll = now
        try:
            res = requests.get(f'{self.back_url}/api/faqture-config', params={
                'client_id': CLIENT_ID
            }, timeout=5)
            self.paused = res.json().get('paused', False)
        except Exception:
            pass
        try:
            res = requests.get(f'{self.back_url}/api/config-updates/pending', params={
                'client_id': CLIENT_ID
            }, timeout=5)
            for update in res.json().get('updates', []):
                self._apply_to_kenani(update)
                requests.put(f'{self.back_url}/api/config-updates/{update["id"]}/apply', timeout=5)
        except Exception:
            pass

    def _apply_to_kenani(self, update):
        from base.comercial.db import get_connection
        try:
            with get_connection() as cnx:
                with cnx.cursor() as cursor:
                    cursor.execute(
                        "UPDATE comercial.empresa SET efactur_empresa=%s, efactur_url=%s WHERE id_empresa=1",
                        (update['new_token'], update['new_url'])
                    )
                cnx.commit()
            log.info('[CONFIG] Credenciales actualizadas en Kenani DB')
        except Exception as e:
            log.error(f'[CONFIG] Error actualizando credenciales: {e}')


reporter = ErrorReporter(CONFIG.backend_url)
config_poller = ConfigPoller(CONFIG.backend_url)


class ApiClient:
    def __init__(self):
        convenio = read_empresa_pgsql()
        self.url = convenio[1]
        self.token = 'Bearer ' + convenio[0]
        self.headers = {'Content-type': 'application/json', 'Authorization': self.token}
        self.verify = CONFIG.api_ssl_verify
        log.info(f'[API] Cliente inicializado | url={self.url}')

    def _log_payload(self, payload, label="payload"):
        if DEBUG:
            log.debug(f'[{label}] {json.dumps(payload, indent=2, ensure_ascii=False)}')

    def _log_response(self, response, elapsed_ms):
        if DEBUG:
            log.debug(f'[RESPONSE] status={response.status_code} time={elapsed_ms}ms body={response.text[:2000]}')

    def _request(self, method, url, **kwargs):
        start = _time.monotonic()
        res = requests.request(method, url, headers=self.headers, verify=self.verify, **kwargs)
        elapsed = int((_time.monotonic() - start) * 1000)
        self._log_response(res, elapsed)
        return res, elapsed

    def _handle_send(self, items, process_name, get_id, get_ref, method, update_success, update_error, endpoint_fn=None):
        for item in items:
            doc_id = get_id(item)
            doc_ref = get_ref(item)
            try:
                self._log_payload(item if isinstance(item, dict) else {'id': doc_id}, f'{process_name} payload id={doc_id}')
                url = endpoint_fn(doc_id) if endpoint_fn else self.url
                res, elapsed = self._request(method, url, json=item if isinstance(item, dict) else None)
                data = json.loads(res.content)

                if res.status_code == 200:
                    message = "{};filename:{};estado:{}".format(
                        data['data']['cod_sale'], data['data']['filename'], data['data']['state']
                    )
                    update_success(item, doc_id, message, data)
                    log.info(f'[{process_name}] id={doc_id} {doc_ref} -> PROCESADO ({elapsed}ms)')
                else:
                    error_msg = data.get('message', data.get('error', data.get('detail', str(data))))
                    update_error(item, doc_id, error_msg, data)
                    log.error(f'[{process_name}] id={doc_id} {doc_ref} -> Error: {error_msg} ({elapsed}ms)')
                    if res.status_code in (401, 403) or 'credential' in error_msg.lower():
                        reporter.report('credential', str(doc_ref), error_msg)
                    else:
                        reporter.report('rejection', str(doc_ref), error_msg)

            except requests.ConnectionError as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> ConnectionError: {e}')
                reporter.report('connection', str(doc_ref), str(e))
            except requests.Timeout as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> Timeout: {e}')
                reporter.report('connection', str(doc_ref), str(e))
            except requests.HTTPError as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> HTTPError: {e}')
                reporter.report('connection', str(doc_ref), str(e))
            except requests.RequestException as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> RequestException: {e}')
                reporter.report('connection', str(doc_ref), str(e))

    def _send_cpe(self, ventas):
        def on_success(venta, doc_id, message, data):
            update_venta_pgsql_external_id(
                'PROCESADO', message, data['data']['external_id'], int(venta['id_venta'])
            )

        def on_error(venta, doc_id, message, data):
            update_venta_pgsql('PROCESADO', json.dumps(data, default=str), int(venta['id_venta']))

        self._handle_send(
            items=ventas,
            process_name='ENVIO',
            get_id=lambda v: v.get('id_venta', '?'),
            get_ref=lambda v: f"{v.get('serie_documento', '?')}-{v.get('numero_documento', '?')}",
            method='POST',
            update_success=on_success,
            update_error=on_error,
        )

    def _send_cpe_anulados(self, data):
        def on_success(venta, doc_id, message, resp_data):
            update_anulados_pgsql('ANULADO', 'PROCESADO', json.dumps(resp_data, default=str), int(doc_id))

        def on_error(venta, doc_id, message, resp_data):
            if 'Document not found!' in message:
                update_no_200('PENDIENTE', int(doc_id))

        self._handle_send(
            items=data,
            process_name='ANULACION',
            get_id=lambda v: v.id_venta,
            get_ref=lambda v: '',
            method='PUT',
            update_success=on_success,
            update_error=on_error,
            endpoint_fn=lambda doc_id: f'{self.url}/api/{doc_id}',
        )

    def _send_cpe_notaCredito(self, data):
        def on_success(venta, doc_id, message, resp_data):
            update_notaCredito_pgsql(json.dumps(resp_data, default=str), int(venta['id_venta']))

        def on_error(venta, doc_id, message, resp_data):
            update_notaCredito_pgsql(json.dumps(resp_data, default=str), int(venta['id_venta']))

        self._handle_send(
            items=data,
            process_name='NOTA_CREDITO',
            get_id=lambda v: v.get('id_venta', '?'),
            get_ref=lambda v: f"{v.get('serie_documento', '?')}-{v.get('numero_documento', '?')}",
            method='POST',
            update_success=on_success,
            update_error=on_error,
        )

    def _send_cpe_guia(self, data):
        def on_success(guia, doc_id, message, resp_data):
            update_guia_pgsql(json.dumps(resp_data, default=str), int(guia['id_venta']))

        def on_error(guia, doc_id, message, resp_data):
            update_guia_pgsql(json.dumps(resp_data, default=str), int(guia['id_venta']))

        self._handle_send(
            items=data,
            process_name='GUIA',
            get_id=lambda v: v.get('id_venta', '?'),
            get_ref=lambda v: f"{v.get('serie_documento', '?')}-{v.get('numero_documento', '?')}",
            method='POST',
            update_success=on_success,
            update_error=on_error,
        )

    def generate_json_file(self, venta, filename):
        with open(filename, 'w') as f:
            json.dump(venta, f, indent=4, ensure_ascii=False)
