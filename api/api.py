import requests
import json
import time as _time

from base.comercial.db import (
    read_empresa_pgsql, update_no_200, update_venta_pgsql,
    update_anulados_pgsql, update_notaCredito_pgsql,
    update_guia_pgsql, update_venta_pgsql_external_id
)
from logger import get_logger
from config import CONFIG
from urllib3.exceptions import InsecureRequestWarning

if not CONFIG.api_ssl_verify:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

log = get_logger()
DEBUG = CONFIG.debug


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

            except requests.ConnectionError as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> ConnectionError: {e}')
            except requests.Timeout as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> Timeout: {e}')
            except requests.HTTPError as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> HTTPError: {e}')
            except requests.RequestException as e:
                log.warning(f'[{process_name}] id={doc_id} {doc_ref} -> RequestException: {e}')

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
