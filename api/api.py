import requests
import json

from base.db import (read_empresa_pgsql, update_no_200, update_venta_pgsql, update_anulados_pgsql, update_notaCredito_pgsql, update_guia_pgsql)
from logger import log
from urllib3.exceptions import InsecureRequestWarning

# Disable flag warning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ApiClient:
    def __init__(self):#, url, token):
        convenio = read_empresa_pgsql()
        self.url = convenio[1]
        self.token = 'Bearer ' + convenio[0]
        self.headers = {'Content-type': 'application/json', 'Authorization': self.token}


    def _send_cpe(self, ventas, tipo=None):
        
        for venta in ventas:
            # print(venta)
            # f = open(f"format_{venta['id_venta']}.json", "a")
            # f.write(json.dumps(venta))
            # f.close()
            # Manejamos las excepciones
            try:
                json_venta = { "document": ObjJSON(venta).encoder()}
                # Realizamos la llamada al API de envío de documentos
                res = requests.post(self.url, json=json_venta, headers=self.headers, verify=False)
                # Obtenemos la respuesta y lo decodificamos
                data = ObjJSON(res.content.decode("UTF8")).decoder()                
                # Adaptamos la respuesta para guardarlo
                if res.status_code == 200:
                    rest = RespuestaREST( data['success'],"{};filename:{};estado:{}".format(data['data']['cod_sale'],data['data']['filename'], data['data']['state']), data)
                    if tipo == 'R': # Es rechazado?           
                        update_venta_pgsql('ANULADO', rest.message, int(venta['id_venta']))
                    else:
                        update_venta_pgsql('PROCESADO', rest.message, int(venta['id_venta']))
                    
                    log.info(f'{rest.message}')
                else:
                    rest = RespuestaREST(False, data['error'], data)
                    update_venta_pgsql('PROCESADO', res.data, int(venta['id_venta']))
                    log.error(f'{rest.message}')
                        
            except requests.ConnectionError as e:
                log.warning(e)
                rest = RespuestaREST(False, "No se puede establecer una conexión")
                log.warning(f'{rest.message}')
            except requests.ConnectTimeout as e:
                log.warning(e)
                rest = RespuestaREST(False, "Tiempo de espera de conexión agotada")
                log.warning(f'{rest.message}')
            except requests.HTTPError as e:
                log.warning(e)
                rest = RespuestaREST(False, "Ruta de enlace no encontrada")
                log.warning(f'{rest.message}')
            except requests.RequestException as e:
                log.warning(e)
                rest = RespuestaREST(False, "No se puede conectar al servicio")
                log.warning(f'{rest.message}')


    def _send_cpe_anulados(self, data):
        
        for venta in data:
            # print(venta)
            try:
                # Realizamos la llamada al API de envío de documentos
                res = requests.post(self.url, json=venta, headers=self.headers, verify=False)
                # Obtenemos la respuesta y lo decodificamos
                data = ObjJSON(res.content.decode("UTF8")).decoder()
                # Adaptamos la respuesta para guardarlo
                if res.status_code == 200:
                    external_id="{}".format(data['data'])
                    update_anulados_pgsql('ANULADO', 'PROCESADO', external_id, int(venta['id_venta']))
                    rest = RespuestaREST(data['success'], "Anulacion ticket:{} {} {}".format(data['data']['ticket'], venta['fecha_de_emision_de_documentos'], venta['documento']), data)
                    log.info(f'{rest.message}')
                else:
                    rest = RespuestaREST(False, data['message'], data)
                    log.error(f'{rest.message}')
                        
            except requests.ConnectionError as e:
                log.warning(e)
                rest = RespuestaREST(False, "No se puede establecer una conexión")
                log.warning(f'{rest.message}')
            except requests.ConnectTimeout as e:
                log.warning(e)
                rest = RespuestaREST(False, "Tiempo de espera de conexión agotada")
                log.warning(f'{rest.message}')
            except requests.HTTPError as e:
                log.warning(e)
                rest = RespuestaREST(False, "Ruta de enlace no encontrada")
                log.warning(f'{rest.message}')
            except requests.RequestException as e:
                log.warning(e)
                rest = RespuestaREST(False, "No se puede conectar al servicio")
                log.warning(f'{rest.message}')



    def _send_cpe_notaCredito(self, data):
        
        for venta in data:        
            try:
                # Realizamos la llamada al API de envío de documentos
                res = requests.post(self.url, json=venta, headers=self.headers, verify=False)
                # Obtenemos la respuesta y lo decodificamos
                data = ObjJSON(res.content.decode("UTF8")).decoder()
                # Adaptamos la respuesta para guardarlo
                if res.status_code == 200:
                    external_id=data['data']['external_id']
                    update_notaCredito_pgsql(external_id, int(venta['id_venta']))
                    rest = RespuestaREST(
                        data['success'],"filename:{};estado:{}".format(data['data']['filename'],
                        data['data']['state_type_description']), data)
                    log.info(f'{rest.message}')
                else:
                    rest = RespuestaREST(False, data['message'], data)
                    log.error(f'{rest.message}')
                        
            except requests.ConnectionError as e:
                log.warning(e)
                rest = RespuestaREST(False, "No se puede establecer una conexión")
                log.warning(f'{rest.message}')
            except requests.ConnectTimeout as e:
                log.warning(e)
                rest = RespuestaREST(False, "Tiempo de espera de conexión agotada")
                log.warning(f'{rest.message}')
            except requests.HTTPError as e:
                log.warning(e)
                rest = RespuestaREST(False, "Ruta de enlace no encontrada")
                log.warning(f'{rest.message}')
            except requests.RequestException as e:
                log.warning(e)
                rest = RespuestaREST(False, "No se puede conectar al servicio")
                log.warning(f'{rest.message}')


    def _send_cpe_guia(self, data):
        
        for guia in data:
            #print(guia)
            res = requests.post(self.url, json=guia, headers=self.headers, verify=False)
            if res.status_code == 200:
                r_json=res.json()
                external_id=r_json['data']['external_id']
                update_guia_pgsql(external_id, int(guia['id_guia']))
                print(res.content)
            else:
                print(res.content)
                print(res.status_code)


# Clase para controlar el formato de respuesta
class RespuestaREST:
    def __init__(self, success, message, data=None, anulado=None):
        self.__success = success
        self.message = message
        self.data = data

    def isSuccess(self):
        return self.__success

# Clase para el control del tipo de codificación en JSON
class ObjModelEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__
    
# Clase para la codificación y decodificación de documentos y json
class ObjJSON:
    def __init__(self, obj):
        self.obj = obj

    def encoder(self):
        return json.dumps(self.obj, cls=ObjModelEncoder, indent=4, ensure_ascii=False)

    def decoder(self):
        return json.loads(self.obj)