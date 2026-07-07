import threading
import psycopg2
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from logger import get_logger
from config import CONFIG

log = get_logger()

_pool = None
_pool_lock = threading.Lock()


def init_pool():
    global _pool
    with _pool_lock:
        if _pool is not None:
            return
        try:
            _pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                database=CONFIG.db_name,
                user=CONFIG.db_user,
                password=CONFIG.db_pass,
                host=CONFIG.db_host,
                port=CONFIG.db_port,
            )
            log.info(f'[DB] Pool inicializado | {CONFIG.db_host}:{CONFIG.db_port}/{CONFIG.db_name}')
        except psycopg2.Error as error:
            log.error(f'[DB] Fallo al crear pool | {error}')
            raise


def close_pool():
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.closeall()
            _pool = None
            log.info('[DB] Pool cerrado')


def check_connection() -> bool:
    try:
        with get_connection() as cnx:
            with cnx.cursor() as cursor:
                cursor.execute("SELECT 1")
        return True
    except Exception:
        return False


@contextmanager
def get_connection():
    if _pool is None:
        init_pool()
    cnx = _pool.getconn()
    try:
        yield cnx
    finally:
        _pool.putconn(cnx)


def update_venta_pgsql(estado, obs, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.ventas SET estado_declaracion = %s, observaciones_declaracion = %s WHERE id_venta = %s",
                (estado, obs, id)
            )
        cnx.commit()
        log.debug(f'[DB] update_venta id={id} estado={estado}')


def update_venta_pgsql_external_id(estado, obs, external_id, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.ventas SET estado_declaracion = %s, observaciones_declaracion = %s, external_id=%s WHERE id_venta = %s",
                (estado, obs, external_id, id)
            )
        cnx.commit()
        log.debug(f'[DB] update_venta_external id={id} external_id={external_id}')


def read_empresa_pgsql():
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute("SELECT efactur_empresa, efactur_url FROM comercial.empresa WHERE id_empresa=%s", (1,))
            convenio = cursor.fetchone()
            log.debug(f'[DB] read_empresa url={convenio[1] if convenio else "N/A"}')
            return convenio


def read_empresa_full():
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "SELECT efactur_empresa, efactur_url, direccion, telefono FROM comercial.empresa WHERE id_empresa=%s",
                (1,)
            )
            return cursor.fetchone()


def update_empresa(efactur_empresa, efactur_url):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.empresa SET efactur_empresa=%s, efactur_url=%s WHERE id_empresa=1",
                (efactur_empresa, efactur_url)
            )
        cnx.commit()
        log.info('[DB] Empresa actualizada')


def update_anulados_pgsql(estado, estado_anulado, ext_id, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.ventas SET estado_declaracion = %s, estado_declaracion_anulado=%s, observaciones_declaracion = %s WHERE id_venta = %s",
                (estado, estado_anulado, ext_id, id)
            )
        cnx.commit()
        log.debug(f'[DB] update_anulado id={id} estado={estado}')


def update_rechazados_pgsql(estado, ext_id, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.ventas SET estado_declaracion = %s, estado_declaracion_anulado=%s WHERE id_venta = %s",
                (estado, ext_id, id)
            )
        cnx.commit()
        log.debug(f'[DB] update_rechazado id={id} estado={estado}')


def update_notaCredito_pgsql(ext_id, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.notas_credito_debito SET observaciones_declaracion = %s, estado_declaracion='PROCESADO' WHERE id_notas_credito_debito = %s",
                (ext_id, id)
            )
        cnx.commit()
        log.debug(f'[DB] update_notaCredito id={id}')


def update_guia_pgsql(data, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.guia SET motivo_anulado=%s, estado_declaracion=%s WHERE id_guia=%s",
                (data, 'PROCESADO', id)
            )
        cnx.commit()
        log.debug(f'[DB] update_guia id={id}')


def update_no_200(estado, id):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(
                "UPDATE comercial.ventas SET estado_declaracion = %s WHERE id_venta = %s",
                (estado, id)
            )
        cnx.commit()
        log.debug(f'[DB] update_no_200 id={id} estado={estado}')


def read_ventas_list(estado=None, serie=None, fecha=None):
    conditions = ["V.num_serie NOT IN ('PRE')"]
    params = []
    if estado:
        conditions.append("V.estado_declaracion = %s")
        params.append(estado)
    if serie:
        conditions.append("V.num_serie = %s")
        params.append(serie)
    if fecha:
        conditions.append("DATE(V.fecha_hora) = %s")
        params.append(fecha)
    where = " AND ".join(conditions)
    sql = f"""
        SELECT V.id_venta, V.num_serie, V.num_documento,
               C.ruc, C.nombres_cliente, V.monto_venta,
               V.estado_declaracion, V.observaciones_declaracion,
               V.fecha_hora, V.external_id,
               TD.codigo_sunat
        FROM comercial.ventas V
            LEFT JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
            LEFT JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = V.id_tipodocumento
        WHERE {where}
        ORDER BY V.fecha_hora DESC
        LIMIT 200
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql, params)
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]


def read_notas_credito_list(estado=None):
    conditions = ["1=1"]
    params = []
    if estado:
        conditions.append("N.estado_declaracion = %s")
        params.append(estado)
    where = " AND ".join(conditions)
    sql = f"""
        SELECT N.id_notas_credito_debito, N.serie, N.numero,
               N.estado_declaracion, N.observaciones_declaracion,
               N.fecha, N.motivo, N.persona,
               V.num_serie AS serie_ref, V.num_documento AS numero_ref
        FROM comercial.notas_credito_debito N
            LEFT JOIN comercial.ventas V ON V.id_venta = N.id_referencia
        WHERE {where}
        ORDER BY N.id_notas_credito_debito DESC
        LIMIT 200
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql, params)
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]


def read_guias_list(estado=None):
    conditions = ["1=1"]
    params = []
    if estado:
        conditions.append("G.estado_declaracion = %s")
        params.append(estado)
    where = " AND ".join(conditions)
    sql = f"""
        SELECT G.id_guia, G.serie, G.numero,
               G.estado_declaracion, G.motivo_anulado,
               G.fecha_emision, G.destinatario
        FROM comercial.guia G
        WHERE {where}
        ORDER BY G.id_guia DESC
        LIMIT 200
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql, params)
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]


def read_anulados_list():
    sql = """
        SELECT V.id_venta, V.num_serie, V.num_documento,
               C.ruc, C.nombres_cliente, V.monto_venta,
               V.estado_declaracion, V.estado_declaracion_anulado,
               V.observaciones_declaracion, V.fecha_hora
        FROM comercial.ventas V
            LEFT JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
        WHERE V.estado_declaracion_anulado IS NOT NULL
            AND V.estado_declaracion_anulado != ''
        ORDER BY V.fecha_hora DESC
        LIMIT 200
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql)
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, row)) for row in cursor.fetchall()]
