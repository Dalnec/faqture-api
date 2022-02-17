import time
import sys
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
tipo = config['BASE']['DB_USER']
db_state = eval(config['BACKUP']['BU_STATE'])
db_time = config['BACKUP']['BU_TIME']
db_time2 = config['BACKUP']['BU_TIME2']

state_doc = eval(config['MAIN']['M_DOC'])
state_anul = eval(config['MAIN']['M_ANUL'])
state_ncredi = eval(config['MAIN']['M_NCREDI'])
state_nventas = eval(config['MAIN']['M_NVENTAS'])
state_guia = eval(config['MAIN']['M_GUIA'])

if __name__ == "__main__":
    sys.path.append('models')
    sys.path.append('base')
    sys.path.append('api')
    sys.path.append('backup')

    from models.comercial.models import leer_db_access
    from models.comercial.models_anulate import leer_db_anulados
    from models.comercial.models_notaCredito import leer_db_notaCredito
    from models.comercial.models_guiaRemision import leer_db_guia
    from models.restobar.models import r_leer_db_access
    from models.restobar.models_anulate import r_leer_db_anulados
    # from base.comercial.db import read_empresa_pgsql
    # from base.restobar.db import r_read_empresa_pgsql
    from api.api import ApiClient
    from base.backup.backup import backup
    from logger import log
    
    if tipo == 'comercial':
        
        while True:
            try:
                if state_doc:            
                    lista_ventas = leer_db_access()
                    ApiClient(tipo)._send_cpe(lista_ventas)
                    time.sleep(1)  
            except Exception as e:
                log.error(f'Envio Comprobantes: {e}')
                time.sleep(2)


            try:
                if state_anul:                
                    lista_anulados = leer_db_anulados()
                    ApiClient(tipo)._send_cpe_anulados(lista_anulados)
                    time.sleep(1)
            except Exception as e:
                log.error(f'Anulados Facturas: {e}')
                time.sleep(2)

            # try:
            #     if state_nventas:                
            #         formato, lista_resumen = leer_db_resumen()
            #         create_resumen(formato, lista_resumen)
            #         time.sleep(1)
            # except Exception as e:
            #     log.error(f'Notas Ventas: {e}')
            #     time.sleep(2)
            
            if state_ncredi:  
                try:                
                    lista_notaCredito = leer_db_notaCredito()
                    ApiClient(tipo).create_notaCredito(lista_notaCredito)
                except Exception as e:
                    log.error(f'Notas Creditos: {e}')
                    time.sleep(2)

            try:
                if state_guia:
                    lista_guia = leer_db_guia()
                    ApiClient(tipo).create_guiaRemision(lista_guia)
            except Exception as e:
                log.error(f'Guia de Remision: {e}')
                time.sleep(2)

            time_now = time.localtime()
            time_now = time.strftime("%H:%M:%S", time_now)
            if  time_now >= db_time and time_now <= db_time2 and db_state:
                try:
                    backup()
                    time.sleep(1)
                except Exception as e:
                    log.error(f'Backups: {e}') 
                    time.sleep(1)
    
    if tipo == 'gulash':
        
        while True:
            try:
                if state_doc:            
                    lista_ventas = r_leer_db_access()
                    ApiClient(tipo)._send_cpe(lista_ventas, tipo)
                    time.sleep(1)  
            except Exception as e:
                log.error(f'Envio Comprobantes: {e}')
                time.sleep(2)


            try:
                if state_anul:                
                    lista_anulados = r_leer_db_anulados()
                    ApiClient(tipo)._send_cpe_anulados(lista_anulados, tipo)
                    time.sleep(1)
            except Exception as e:
                log.error(f'Anulados Facturas: {e}')
                time.sleep(2)
            
            time_now = time.localtime()
            time_now = time.strftime("%H:%M:%S", time_now)
            # time_now = _get_time()
            if  time_now >= db_time and time_now <= db_time2 and db_state:
                try:
                    backup()
                    time.sleep(1)
                except Exception as e:
                    log.error(f'Backups: {e}') 
                    time.sleep(1)
