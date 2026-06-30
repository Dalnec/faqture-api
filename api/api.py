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

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

log = get_logger()
DEBUG = CONFIG.debug


class ApiClient:
    def __init__(self):
        convenio = read_empresa_pgsql()
        self.url = convenio[1]
        self.token = 'Bearer ' + convenio[0]
        self.headers = {'Content-type': 'application/json', 'Authorization': self.token}
        log.info(f'[API] Cliente inicializado | url={self.url}')

    def _log_payload(self, payload, label="payload"):
        if DEBUG:
            log.debug(f'[{label}] {json.dumps(payload, indent=2, ensure_ascii=False)}')

    def _log_response(self, response, elapsed_ms):
        if DEBUG:
            log.debug(f'[RESPONSE] status={response.status_code} time={elapsed_ms}ms body={response.text[:2000]}')

    def _send_cpe(self, ventas):
        for venta in ventas:
            doc_id = venta.get('id_venta', '?')
            doc_ref = f"{venta.get('serie_documento', '?')}-{venta.get('numero_documento', '?')}"
            try:
                self._log_payload(venta, f'ENVIO payload id={doc_id}')
                start = _time.monotonic()
                res = requests.post(self.url, json=venta, headers=self.headers, verify=False)
                elapsed = int((_time.monotonic() - start) * 1000)
                self._log_response(res, elapsed)

                data = ObjJSON(res.content.decode("UTF8")).decoder()
                if res.status_code == 200:
                    rest = RespuestaREST(
                        data['success'],
                        "{};filename:{};estado:{}".format(
                            data['data']['cod_sale'], data['data']['filename'], data['data']['state']
                        ), data
                    )
                    update_venta_pgsql_external_id(
                        'PROCESADO', rest.message, rest.data['data']['external_id'], int(venta['id_venta'])
                    )
                    log.info(f'[ENVIO] id={doc_id} {doc_ref} -> PROCESADO ({elapsed}ms)')
                else:
                    rest = RespuestaREST(False, data['message'], data)
                    update_venta_pgsql('PROCESADO', ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    log.error(f'[ENVIO] id={doc_id} {doc_ref} -> Error: {rest.message} ({elapsed}ms)')

            except requests.ConnectionError as e:
                log.warning(f'[ENVIO] id={doc_id} {doc_ref} -> ConnectionError: {e}')
            except requests.ConnectTimeout as e:
                log.warning(f'[ENVIO] id={doc_id} {doc_ref} -> Timeout: {e}')
            except requests.HTTPError as e:
                log.warning(f'[ENVIO] id={doc_id} {doc_ref} -> HTTPError: {e}')
            except requests.RequestException as e:
                log.warning(f'[ENVIO] id={doc_id} {doc_ref} -> RequestException: {e}')

    def _send_cpe_anulados(self, data):
        for venta in data:
            doc_id = venta.id_venta
            try:
                self._log_payload({'id_venta': doc_id, 'action': 'anular'}, f'ANULACION payload id={doc_id}')
                start = _time.monotonic()
                res = requests.put(f'{self.url}/api/{doc_id}', headers=self.headers, verify=False)
                elapsed = int((_time.monotonic() - start) * 1000)
                self._log_response(res, elapsed)

                resp_data = ObjJSON(res.content.decode("UTF8")).decoder()
                if res.status_code == 200:
                    rest = RespuestaREST(
                        resp_data['success'],
                        "Anulacion:{};filename:{};estado:{}".format(
                            resp_data['data']['cod_sale'], resp_data['data']['filename'], resp_data['data']['state']
                        ), resp_data
                    )
                    update_anulados_pgsql('ANULADO', 'PROCESADO', ObjJSON(rest.data).encoder(), int(doc_id))
                    log.info(f'[ANULACION] id={doc_id} -> ANULADO ({elapsed}ms)')
                else:
                    rest = RespuestaREST(False, resp_data['message'], resp_data)
                    if 'Document not found!' in rest.message:
                        update_no_200('PENDIENTE', int(doc_id))
                    log.error(f'[ANULACION] id={doc_id} -> Error: {rest.message} ({elapsed}ms)')

            except requests.ConnectionError as e:
                log.warning(f'[ANULACION] id={doc_id} -> ConnectionError: {e}')
            except requests.ConnectTimeout as e:
                log.warning(f'[ANULACION] id={doc_id} -> Timeout: {e}')
            except requests.HTTPError as e:
                log.warning(f'[ANULACION] id={doc_id} -> HTTPError: {e}')
            except requests.RequestException as e:
                log.warning(f'[ANULACION] id={doc_id} -> RequestException: {e}')

    def _send_cpe_notaCredito(self, data):
        for venta in data:
            doc_id = venta.get('id_venta', '?')
            doc_ref = f"{venta.get('serie_documento', '?')}-{venta.get('numero_documento', '?')}"
            try:
                self._log_payload(venta, f'NOTA_CREDITO payload id={doc_id}')
                start = _time.monotonic()
                res = requests.post(self.url, json=venta, headers=self.headers, verify=False)
                elapsed = int((_time.monotonic() - start) * 1000)
                self._log_response(res, elapsed)

                resp_data = ObjJSON(res.content.decode("UTF8")).decoder()
                if res.status_code == 200:
                    rest = RespuestaREST(
                        resp_data['success'],
                        "{};filename:{};estado:{}".format(
                            resp_data['data']['cod_sale'], resp_data['data']['filename'], resp_data['data']['state']
                        ), resp_data
                    )
                    update_notaCredito_pgsql(ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    log.info(f'[NOTA_CREDITO] id={doc_id} {doc_ref} -> PROCESADO ({elapsed}ms)')
                else:
                    rest = RespuestaREST(False, resp_data['message'], resp_data)
                    update_notaCredito_pgsql(ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    log.error(f'[NOTA_CREDITO] id={doc_id} {doc_ref} -> Error: {rest.message} ({elapsed}ms)')

            except requests.ConnectionError as e:
                log.warning(f'[NOTA_CREDITO] id={doc_id} {doc_ref} -> ConnectionError: {e}')
            except requests.ConnectTimeout as e:
                log.warning(f'[NOTA_CREDITO] id={doc_id} {doc_ref} -> Timeout: {e}')
            except requests.HTTPError as e:
                log.warning(f'[NOTA_CREDITO] id={doc_id} {doc_ref} -> HTTPError: {e}')
            except requests.RequestException as e:
                log.warning(f'[NOTA_CREDITO] id={doc_id} {doc_ref} -> RequestException: {e}')

    def _send_cpe_guia(self, data):
        for guia in data:
            doc_id = guia.get('id_venta', '?')
            doc_ref = f"{guia.get('serie_documento', '?')}-{guia.get('numero_documento', '?')}"
            try:
                self._log_payload(guia, f'GUIA payload id={doc_id}')
                start = _time.monotonic()
                res = requests.post(self.url, json=guia, headers=self.headers, verify=False)
                elapsed = int((_time.monotonic() - start) * 1000)
                self._log_response(res, elapsed)

                response = ObjJSON(res.content.decode("UTF8")).decoder()
                if res.status_code == 200:
                    rest = RespuestaREST(
                        response['success'],
                        f"{response['data']['cod_sale']};filename:{response['data']['filename']};estado:{response['data']['state']}",
                        response
                    )
                    update_guia_pgsql(ObjJSON(rest.data).encoder(), int(guia['id_venta']))
                    log.info(f'[GUIA] id={doc_id} {doc_ref} -> PROCESADO ({elapsed}ms)')
                else:
                    rest = RespuestaREST(False, response['message'], response)
                    update_guia_pgsql(ObjJSON(rest.data).encoder(), int(guia['id_venta']))
                    log.error(f'[GUIA] id={doc_id} {doc_ref} -> Error: {rest.message} ({elapsed}ms)')

            except requests.ConnectionError as e:
                log.warning(f'[GUIA] id={doc_id} {doc_ref} -> ConnectionError: {e}')
            except requests.ConnectTimeout as e:
                log.warning(f'[GUIA] id={doc_id} {doc_ref} -> Timeout: {e}')
            except requests.HTTPError as e:
                log.warning(f'[GUIA] id={doc_id} {doc_ref} -> HTTPError: {e}')
            except requests.RequestException as e:
                log.warning(f'[GUIA] id={doc_id} {doc_ref} -> RequestException: {e}')

    def generate_json_file(self, venta, filename):
        with open(filename, 'w') as f:
            json.dump(venta, f, indent=4, ensure_ascii=False)


class RespuestaREST:
    def __init__(self, success, message, data=None):
        self.__success = success
        self.message = message
        self.data = data

    def isSuccess(self):
        return self.__success


class ObjModelEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__


class ObjJSON:
    def __init__(self, obj):
        self.obj = obj

    def encoder(self):
        return json.dumps(self.obj, cls=ObjModelEncoder, indent=4, ensure_ascii=False)

    def decoder(self):
        return json.loads(self.obj)
