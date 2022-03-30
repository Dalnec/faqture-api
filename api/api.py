import requests
import json

from base.comercial.db import (read_empresa_pgsql, update_no_200, update_venta_pgsql, update_anulados_pgsql, update_notaCredito_pgsql, update_guia_pgsql)
from base.restobar.db import (r_read_empresa_pgsql, r_update_no_200, r_update_venta_pgsql, r_update_anulados_pgsql)
from logger import log
from urllib3.exceptions import InsecureRequestWarning

# Disable flag warning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class ApiClient:
    def __init__(self, tipo):#, url, token):
        if tipo == 'comercial':
            convenio = read_empresa_pgsql()
        elif tipo == 'gulash':
            convenio = r_read_empresa_pgsql()
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
                # print(venta)
                # print(ObjJSON(venta).encoder())
                # json_venta = { "document": ObjJSON(venta).encoder()}
                # Realizamos la llamada al API de envío de documentos
                res = requests.post(self.url, json=venta, headers=self.headers, verify=False)
                # Obtenemos la respuesta y lo decodificamos
                data = ObjJSON(res.content.decode("UTF8")).decoder()                
                # Adaptamos la respuesta para guardarlo
                if res.status_code == 200:
                    rest = RespuestaREST( data['success'],"{};filename:{};estado:{}".format(data['data']['cod_sale'],data['data']['filename'], data['data']['state']), data)
                    if tipo:          
                        r_update_venta_pgsql('PROCESADO', rest.message, int(venta['id_venta']))
                    else:
                        update_venta_pgsql('PROCESADO', rest.message, int(venta['id_venta']))
                    
                    log.info(f'{rest.message}')
                else:
                    rest = RespuestaREST(False, data['message'], data)
                    if tipo:
                        r_update_venta_pgsql('PROCESADO', ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    else:
                        update_venta_pgsql('PROCESADO', ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    log.error(f'{venta["id_venta"]} {venta["serie_documento"]}-{venta["numero_documento"]} {rest.message}')
                        
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


    def _send_cpe_anulados(self, data, tipo=None):
        
        for venta in data:
            try:
                # Realizamos la llamada al API de envío de documentos
                res = requests.put(f'{self.url}/api/{venta.id_venta}', headers=self.headers, verify=False)
                # Obtenemos la respuesta y lo decodificamos
                data = ObjJSON(res.content.decode("UTF8")).decoder()
                # Adaptamos la respuesta para guardarlo
                if res.status_code == 200:
                    rest = RespuestaREST( data['success'],"Anulacion:{};filename:{};estado:{}".format(data['data']['cod_sale'],data['data']['filename'], data['data']['state']), data)
                    if tipo:
                        r_update_anulados_pgsql('ANULADO', 'PROCESADO', ObjJSON(rest.data).encoder(), int(venta.id_venta))
                    else:
                        update_anulados_pgsql('ANULADO', 'PROCESADO', ObjJSON(rest.data).encoder(), int(venta.id_venta))
                    log.info(f'{rest.message}')
                else: 
                    rest = RespuestaREST(False, data['message'], data)
                    if (rest.message.find('Document not found!') != -1):
                        if tipo:
                            r_update_no_200('PENDIENTE', int(venta.id_venta))
                        else:
                            update_no_200('PENDIENTE', int(venta.id_venta))
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
                    rest = RespuestaREST( data['success'],"{};filename:{};estado:{}".format(data['data']['cod_sale'],data['data']['filename'], data['data']['state']), data)
                    update_notaCredito_pgsql(ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    log.info(f'{rest.message}')
                else:
                    rest = RespuestaREST(False, data['message'], data)
                    update_notaCredito_pgsql(ObjJSON(rest.data).encoder(), int(venta['id_venta']))
                    log.error(f'{venta["id_venta"]} {venta["serie_documento"]}-{venta["numero_documento"]}|{rest.message}')
                        
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
    def __init__(self, success, message, data=None):
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