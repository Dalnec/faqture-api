# import time
# import sys
# import configparser


# config = configparser.ConfigParser()
# config.read('config.ini')
# tipo = config['BASE']['DB_USER']
# db_state = eval(config['BACKUP']['BU_STATE'])
# db_time = config['BACKUP']['BU_TIME']
# db_time2 = config['BACKUP']['BU_TIME2']

# state_doc = eval(config['MAIN']['M_DOC'])
# state_anul = eval(config['MAIN']['M_ANUL'])
# state_ncredi = eval(config['MAIN']['M_NCREDI'])
# state_nventas = eval(config['MAIN']['M_NVENTAS'])
# state_guia = eval(config['MAIN']['M_GUIA'])

# if __name__ == "__main__":
#     sys.path.append('models')
#     sys.path.append('base')
#     sys.path.append('api')
#     sys.path.append('backup')

#     from models.comercial.models import leer_db
#     from models.comercial.models_notaventa import leer_db_notas
#     from models.comercial.models_anulate import leer_db_anulados
#     from models.comercial.models_notaCredito import leer_db_notaCredito
#     from models.comercial.models_guiaRemision import leer_db_guia
#     from api.api import ApiClient
#     from base.backup.backup import backup
#     from logger import log
        
#     while True:
#         try:
#             if state_doc:            
#                 lista_ventas = leer_db()
#                 ApiClient()._send_cpe(lista_ventas)
#                 time.sleep(1)  
#         except Exception as e:
#             log.error(f'Envio Comprobantes: {e}')
#             time.sleep(2)

#         try:
#             if state_anul:                
#                 lista_anulados = leer_db_anulados()
#                 ApiClient()._send_cpe_anulados(lista_anulados)
#                 time.sleep(1)
#         except Exception as e:
#             log.error(f'Anulados Facturas: {e}')
#             time.sleep(2)

#         try:
#             if state_nventas:                
#                 lista_notas = leer_db_notas()
#                 ApiClient()._send_cpe(lista_notas)
#                 time.sleep(1)
#         except Exception as e:
#             log.error(f'Notas Ventas: {e}')
#             time.sleep(2)
        
#         if state_ncredi:  
#             try:                
#                 lista_notaCredito = leer_db_notaCredito()
#                 ApiClient()._send_cpe_notaCredito(lista_notaCredito)
#             except Exception as e:
#                 log.error(f'Notas Creditos: {e}')
#                 time.sleep(2)

#         try:
#             if state_guia:
#                 lista_guia = leer_db_guia()
#                 ApiClient().create_guiaRemision(lista_guia)
#         except Exception as e:
#             log.error(f'Guia de Remision: {e}')
#             time.sleep(2)

#         time_now = time.localtime()
#         time_now = time.strftime("%H:%M:%S", time_now)
#         if  time_now >= db_time and time_now <= db_time2 and db_state:
#             try:
#                 backup()
#                 time.sleep(1)
#             except Exception as e:
#                 log.error(f'Backups: {e}') 
#                 time.sleep(1)


import time
import sys
import logging
from datetime import datetime
from typing import Callable
# Importar configuración global
from config import CONFIG, Config

class ProcessManager:
    """Gestor de procesos de negocio"""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_client = None
        self._setup_imports()
        self._setup_api_client()
    
    def _setup_imports(self):
        """Configurar imports dinámicos"""
        sys.path.extend(['models', 'base', 'api', 'backup'])
        
        # Imports dinámicos para evitar errores si no existen
        try:
            from models.comercial.models import leer_db
            from models.comercial.models_notaventa import leer_db_notas
            from models.comercial.models_anulate import leer_db_anulados
            from models.comercial.models_notaCredito import leer_db_notaCredito
            from models.comercial.models_guiaRemision import leer_db_guia
            # from api.api import ApiClient
            from base.backup.backup import backup
            from logger import log
            
            self.readers = {
                'doc': leer_db,
                'anul': leer_db_anulados,
                'nventas': leer_db_notas,
                'ncredi': leer_db_notaCredito,
                'guia': leer_db_guia
            }
            self.backup_func = backup
            self.log = log
            
        except ImportError as e:
            logging.error(f"Error importing modules: {e}")
            raise
    
    def _setup_api_client(self):
        """Configurar cliente API reutilizable"""
        from api.api import ApiClient
        self.api_client = ApiClient()
    
    def _execute_process(
        self, process_name: str, state: bool, reader_func: Callable, 
        api_method: str, sleep_time: int = 1
    ) -> None:
        """Ejecutar un proceso de forma genérica"""
        if not state:
            return
            
        try:
            data = reader_func()
            if data:  # Solo procesar si hay datos
                api_func = getattr(self.api_client, api_method)
                api_func(data)
                time.sleep(sleep_time)
        except Exception as e:
            self.log.error(f'{process_name}: {e}')
            time.sleep(2)
    
    def process_documents(self):
        """Procesar documentos"""
        self._execute_process( 'Envio Comprobantes', self.config.state_doc, self.readers['doc'], '_send_cpe' )
    
    def process_cancellations(self):
        """Procesar anulaciones"""
        self._execute_process( 'Anulados Facturas', self.config.state_anul, self.readers['anul'], '_send_cpe_anulados' )
    
    def process_sales_notes(self):
        """Procesar notas de venta"""
        self._execute_process( 'Notas Ventas', self.config.state_nventas, self.readers['nventas'], '_send_cpe' )
    
    def process_credit_notes(self):
        """Procesar notas de crédito"""
        self._execute_process( 'Notas Creditos', self.config.state_ncredi, self.readers['ncredi'], '_send_cpe_notaCredito' )
    
    def process_delivery_guides(self):
        """Procesar guías de remisión"""
        self._execute_process( 'Guia de Remision', self.config.state_guia, self.readers['guia'], '_send_cpe_guia' )
    
    def process_backup(self):
        """Procesar backup si está en horario"""
        if not self.config.db_state:
            return
            
        current_time = datetime.now().strftime("%H:%M:%S")
        
        if self.config.db_time <= current_time <= self.config.db_time2:
            try:
                self.backup_func()
                time.sleep(1)
            except Exception as e:
                self.log.error(f'Backups: {e}')
                time.sleep(1)
    
    def run_cycle(self):
        """Ejecutar un ciclo completo de procesamiento"""
        processes = [
            self.process_documents,
            self.process_cancellations,
            self.process_sales_notes,
            self.process_credit_notes,
            self.process_delivery_guides,
            self.process_backup
        ]
        
        for process in processes:
            process()

def main():
    """Función principal"""
    try:
        config = CONFIG
        processor = ProcessManager(config)
        
        logging.info("Iniciando procesamiento continuo...")
        
        while True:
            processor.run_cycle()
            time.sleep(0.5)  # Pequeña pausa entre ciclos
            
    except KeyboardInterrupt:
        logging.info("Procesamiento interrumpido por el usuario")
    except Exception as e:
        logging.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()