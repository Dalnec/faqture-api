import psycopg2
import configparser
from logger import get_logger

config = configparser.ConfigParser()
config.read('config.ini')

db_name = config['BASE']['DB_NAME']
db_user = config['BASE']['DB_USER']
db_pass = config['BASE']['DB_PASS']
db_host = config['BASE']['DB_HOST']
db_port = config['BASE']['DB_PORT']

log = get_logger()


def __conectarse():
    try:
        cnx = psycopg2.connect(
            database=db_name, user=db_user,
            password=db_pass, host=db_host, port=db_port
        )
        log.debug(f'[DB] Conectado a {db_host}:{db_port}/{db_name}')
        return cnx
    except (Exception, psycopg2.Error) as error:
        log.error(f'[DB] Fallo de conexion a {db_host}:{db_port}/{db_name} | {error}')
        raise


def update_venta_pgsql(estado, obs, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.ventas SET estado_declaracion = %s, observaciones_declaracion = %s WHERE id_venta = %s",
            (estado, obs, id)
        )
        cnx.commit()
        log.debug(f'[DB] update_venta id={id} estado={estado}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def update_venta_pgsql_external_id(estado, obs, external_id, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.ventas SET estado_declaracion = %s, observaciones_declaracion = %s, external_id=%s WHERE id_venta = %s",
            (estado, obs, external_id, id)
        )
        cnx.commit()
        log.debug(f'[DB] update_venta_external id={id} external_id={external_id}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def read_empresa_pgsql():
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute("SELECT efactur_empresa, efactur_url FROM comercial.empresa WHERE id_empresa=%s", (1,))
        convenio = cursor.fetchone()
        log.debug(f'[DB] read_empresa url={convenio[1] if convenio else "N/A"}')
        return convenio
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def update_anulados_pgsql(estado, estado_anulado, ext_id, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.ventas SET estado_declaracion = %s, estado_declaracion_anulado=%s, observaciones_declaracion = %s WHERE id_venta = %s",
            (estado, estado_anulado, ext_id, id)
        )
        cnx.commit()
        log.debug(f'[DB] update_anulado id={id} estado={estado}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def update_rechazados_pgsql(estado, ext_id, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.ventas SET estado_declaracion = %s, estado_declaracion_anulado=%s WHERE id_venta = %s",
            (estado, ext_id, id)
        )
        cnx.commit()
        log.debug(f'[DB] update_rechazado id={id} estado={estado}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def update_notaCredito_pgsql(ext_id, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.notas_credito_debito SET observaciones_declaracion = %s, estado_declaracion='PROCESADO' WHERE id_notas_credito_debito = %s",
            (ext_id, id)
        )
        cnx.commit()
        log.debug(f'[DB] update_notaCredito id={id}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def update_guia_pgsql(data, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.guia SET motivo_anulado=%s, estado_declaracion=%s WHERE id_guia=%s",
            (data, 'PROCESADO', id)
        )
        cnx.commit()
        log.debug(f'[DB] update_guia id={id}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()


def update_no_200(estado, id):
    try:
        cnx = __conectarse()
        cursor = cnx.cursor()
        cursor.execute(
            "UPDATE comercial.ventas SET estado_declaracion = %s WHERE id_venta = %s",
            (estado, id)
        )
        cnx.commit()
        log.debug(f'[DB] update_no_200 id={id} estado={estado}')
    finally:
        if cnx:
            cursor.close()
            cnx.close()
