import configparser
from dataclasses import dataclass

@dataclass
class Config:
    """Configuración de la aplicación"""
    db_name: str
    db_user: str
    db_pass: str
    db_host: str
    db_port: str
    db_bk_name: str
    db_state: bool
    db_drive: bool
    db_time: str
    db_time2: str
    state_doc: bool
    state_anul: bool
    state_ncredi: bool
    state_nventas: bool
    state_guia: bool
    date_header: str

def load_config() -> Config:
    """Cargar configuración desde archivo"""
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    return Config(
        db_name=config['BASE']['DB_NAME'],
        db_user=config['BASE']['DB_USER'],
        db_pass=config['BASE']['DB_PASS'],
        db_host=config['BASE']['DB_HOST'],
        db_port=config['BASE']['DB_PORT'],
        db_bk_name=config['BACKUP']['BU_NAME'],
        db_state=config.getboolean('BACKUP', 'BU_STATE'),
        db_drive=config.getboolean('BACKUP', 'BU_DRIVE'),
        db_time=config['BACKUP']['BU_TIME'],
        db_time2=config['BACKUP']['BU_TIME2'],
        state_doc=config.getboolean('MAIN', 'M_DOC'),
        state_anul=config.getboolean('MAIN', 'M_ANUL'),
        state_ncredi=config.getboolean('MAIN', 'M_NCREDI'),
        state_nventas=config.getboolean('MAIN', 'M_NVENTAS'),
        state_guia=config.getboolean('MAIN', 'M_GUIA'),
        date_header=config['MODELS']['DATE_HEADER']
    )

# Cargar config global al importar el módulo
CONFIG = load_config()