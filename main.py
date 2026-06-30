import time
import sys
import logging
from datetime import datetime
from typing import Callable

from app_info import handle_version_arg, show_banner, APP_INFO
from config import CONFIG, Config
from logger import setup_logger

handle_version_arg()


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

        try:
            from models.comercial.models import leer_db
            from models.comercial.models_notaventa import leer_db_notas
            from models.comercial.models_anulate import leer_db_anulados
            from models.comercial.models_notaCredito import leer_db_notaCredito
            from models.comercial.models_guiaRemision import leer_db_guia
            from base.backup.backup import backup

            self.readers = {
                'doc': leer_db,
                'anul': leer_db_anulados,
                'nventas': leer_db_notas,
                'ncredi': leer_db_notaCredito,
                'guia': leer_db_guia
            }
            self.backup_func = backup

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
            if data:
                api_func = getattr(self.api_client, api_method)
                api_func(data)
                time.sleep(sleep_time)
        except Exception as e:
            self.log.error(f'[{process_name}] Error: {e}', exc_info=True)
            time.sleep(2)

    def process_documents(self):
        self._execute_process('ENVIO', self.config.state_doc, self.readers['doc'], '_send_cpe')

    def process_cancellations(self):
        self._execute_process('ANULACION', self.config.state_anul, self.readers['anul'], '_send_cpe_anulados')

    def process_sales_notes(self):
        self._execute_process('NOTA_VENTA', self.config.state_nventas, self.readers['nventas'], '_send_cpe')

    def process_credit_notes(self):
        self._execute_process('NOTA_CREDITO', self.config.state_ncredi, self.readers['ncredi'], '_send_cpe_notaCredito')

    def process_delivery_guides(self):
        self._execute_process('GUIA_REMISION', self.config.state_guia, self.readers['guia'], '_send_cpe_guia')

    def process_backup(self):
        if not self.config.db_state:
            return

        current_time = datetime.now().strftime("%H:%M:%S")

        if self.config.db_time <= current_time <= self.config.db_time2:
            try:
                self.backup_func()
                time.sleep(1)
            except Exception as e:
                self.log.error(f'[BACKUP] Error: {e}')
                time.sleep(1)

    def run_cycle(self):
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
    config = CONFIG
    log = setup_logger(debug=config.debug)

    show_banner()
    log.info(f"Version {APP_INFO['version']} | Build {APP_INFO['build_date']} | Branch {APP_INFO['source_branch']}")
    log.info(f"Debug mode: {'ON' if config.debug else 'OFF'}")
    log.info("Iniciando procesamiento continuo...")

    try:
        processor = ProcessManager(config)
        processor.log = log

        while True:
            processor.run_cycle()
            time.sleep(0.5)

    except KeyboardInterrupt:
        log.info("Procesamiento interrumpido por el usuario")
    except Exception as e:
        log.error(f"Error critico: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
