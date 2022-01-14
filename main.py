import time
import sys
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
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

    from models.models import leer_db_access
    from models.models_anulate import leer_db_fanulados, leer_db_banulados
    from models.models_notaCredito import leer_db_notaCredito
    from models.models_guiaRemision import leer_db_guia
    from models.models_rechazados import leer_db_rechazados
    from api.api import ApiClient#( create_document, create_anulados, create_notaCredito, create_guiaRemision )
    from base.backup.backup import backup
    # from base.db import _get_time
    from logger import log

    while True:
        try:
            if state_doc:            
                lista_ventas = leer_db_access()
                ApiClient()._send_cpe(lista_ventas)
                time.sleep(1)  
        except Exception as e:
            log.error(f'Envio Comprobantes: {e}')
            time.sleep(2)

        try:
            if state_anul:               
                lista_rechazados = leer_db_rechazados()
                ApiClient()._send_cpe(lista_rechazados, 'R')
                time.sleep(1)
        except Exception as e:
            log.error(f'Anulados Rechazados: {e}')
            time.sleep(2)

        try:
            if state_anul:                
                lista_anulados = leer_db_fanulados()
                ApiClient().create_anulados(lista_anulados, 1)
                time.sleep(1)
        except Exception as e:
            log.error(f'Anulados Facturas: {e}')
            time.sleep(2)

        try:
            if state_anul:                
                lista_anulados = leer_db_banulados()
                ApiClient().create_anulados(lista_anulados, 3)
                time.sleep(1)
        except Exception as e:
            log.error(f'Anulados Boletas: {e}')
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
                ApiClient().create_notaCredito(lista_notaCredito)
            except Exception as e:
                log.error(f'Notas Creditos: {e}')
                time.sleep(2)

        try:
            if state_guia:
                lista_guia = leer_db_guia()
                ApiClient().create_guiaRemision(lista_guia)
        except Exception as e:
            log.error(f'Guia de Remision: {e}')
            time.sleep(2)

        # time_now = _get_time()
        # if  time_now >= db_time and time_now <= db_time2 and db_state:
        #     try:
        #         backup()
        #         time.sleep(1)
        #     except Exception as e:
        #         log.error(f'Backups: {e}') 
        #         time.sleep(1)