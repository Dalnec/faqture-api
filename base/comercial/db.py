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


def _serialize_row(row):
    for k, v in row.items():
        if hasattr(v, 'isoformat'):
            row[k] = v.isoformat()
        elif isinstance(v, (int, float, str, bool, type(None))):
            pass
        else:
            row[k] = str(v)
    return row


def read_ventas_list(estado=None, serie=None, fecha=None, page=1, per_page=100):
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
    offset = (page - 1) * per_page

    count_sql = f"""
        SELECT COUNT(*)
        FROM comercial.ventas V
            LEFT JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
            LEFT JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = V.id_tipodocumento
        WHERE {where}
    """
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
        LIMIT %s OFFSET %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]
            cursor.execute(sql, params + [per_page, offset])
            cols = [d[0] for d in cursor.description]
            docs = [_serialize_row(dict(zip(cols, row))) for row in cursor.fetchall()]
    return docs, total


def read_notas_credito_list(estado=None, page=1, per_page=100):
    conditions = ["1=1"]
    params = []
    if estado:
        conditions.append("N.estado_declaracion = %s")
        params.append(estado)
    where = " AND ".join(conditions)
    offset = (page - 1) * per_page

    count_sql = f"""
        SELECT COUNT(*)
        FROM comercial.notas_credito_debito N
            LEFT JOIN comercial.ventas V ON V.id_venta = N.id_referencia
        WHERE {where}
    """
    sql = f"""
        SELECT N.id_notas_credito_debito, N.serie, N.numero,
               N.estado_declaracion, N.observaciones_declaracion,
               N.fecha, N.motivo, N.persona,
               V.num_serie AS serie_ref, V.num_documento AS numero_ref
        FROM comercial.notas_credito_debito N
            LEFT JOIN comercial.ventas V ON V.id_venta = N.id_referencia
        WHERE {where}
        ORDER BY N.id_notas_credito_debito DESC
        LIMIT %s OFFSET %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]
            cursor.execute(sql, params + [per_page, offset])
            cols = [d[0] for d in cursor.description]
            docs = [_serialize_row(dict(zip(cols, row))) for row in cursor.fetchall()]
    return docs, total


def read_guias_list(estado=None, page=1, per_page=100):
    conditions = ["1=1"]
    params = []
    if estado:
        conditions.append("G.estado_declaracion = %s")
        params.append(estado)
    where = " AND ".join(conditions)
    offset = (page - 1) * per_page

    count_sql = f"""
        SELECT COUNT(*)
        FROM comercial.guia G
        WHERE {where}
    """
    sql = f"""
        SELECT G.id_guia, G.serie, G.numero,
               G.estado_declaracion, G.motivo_anulado,
               G.fecha_emision, G.destinatario
        FROM comercial.guia G
        WHERE {where}
        ORDER BY G.id_guia DESC
        LIMIT %s OFFSET %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(count_sql, params)
            total = cursor.fetchone()[0]
            cursor.execute(sql, params + [per_page, offset])
            cols = [d[0] for d in cursor.description]
            docs = [_serialize_row(dict(zip(cols, row))) for row in cursor.fetchall()]
    return docs, total


def read_anulados_list(page=1, per_page=100):
    offset = (page - 1) * per_page
    count_sql = """
        SELECT COUNT(*)
        FROM comercial.ventas V
            LEFT JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
        WHERE V.estado_declaracion_anulado IS NOT NULL
            AND V.estado_declaracion_anulado != ''
    """
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
        LIMIT %s OFFSET %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(count_sql)
            total = cursor.fetchone()[0]
            cursor.execute(sql, [per_page, offset])
            cols = [d[0] for d in cursor.description]
            docs = [_serialize_row(dict(zip(cols, row))) for row in cursor.fetchall()]
    return docs, total


def read_venta_payload(id_venta):
    sql_header = """
        SELECT V.id_venta, V.num_serie, V.num_documento,
               V.fecha_hora, TD.codigo_sunat,
               CASE WHEN C.ruc != '' THEN '6' WHEN C.dni != '' THEN '1' ELSE '0' END cliente_tipo_de_documento,
               CASE WHEN C.dni != '' THEN C.dni WHEN C.ruc != '' THEN C.ruc ELSE '00000000' END cliente_numero_de_documento,
               C.nombres_cliente, D.direccion,
               V.monto_venta, V.cod_empleado,
               MP.descripcion AS forma_pago, V.id_puntodeventa,
               V.descuento, V.igv, V.id_tipopago, V.numero_placa,
               V.estado_declaracion, V.observaciones_declaracion, V.external_id
        FROM comercial.ventas V
            LEFT JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = V.id_tipodocumento
            LEFT JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
            LEFT JOIN comercial.direcciones D ON D.id_direcciones = V.id_direcciones
            LEFT JOIN comercial.metodo_pago MP ON MP.id_metodo_pago = V.id_metodo_pago
        WHERE V.id_venta = %s
    """
    sql_detail = """
        SELECT P.codigo_producto, DV.descripcion, DV.cantidad, DV.monto,
               DV.igv, DV.descuento_individual
        FROM comercial.detalle_venta DV
            LEFT JOIN comercial.producto P ON P.codigo_producto = DV.codigo_producto
        WHERE DV.id_venta = %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql_header, (id_venta,))
            row = cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            header = dict(zip(cols, row))

            cursor.execute(sql_detail, (id_venta,))
            detail_cols = [d[0] for d in cursor.description]
            details = [dict(zip(detail_cols, drow)) for drow in cursor.fetchall()]

    return {'header': _serialize_row(header), 'details': [_serialize_row(d) for d in details]}


def read_nota_credito_payload(id_nc):
    sql_header = """
        SELECT N.id_notas_credito_debito, N.serie, N.numero, N.fecha,
               N.codigo_motivo, N.motivo, N.persona, N.direccion,
               N.estado_declaracion, N.observaciones_declaracion,
               V.num_serie AS serie_ref, V.num_documento AS numero_ref,
               TD.codigo_sunat, V.id_tipodocumento
        FROM comercial.notas_credito_debito N
            LEFT JOIN comercial.ventas V ON V.id_venta = N.id_referencia
            LEFT JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = V.id_tipodocumento
        WHERE N.id_notas_credito_debito = %s
    """
    sql_detail = """
        SELECT D.codigo_producto, D.descripcion, D.cantidad, D.precio_unitario
        FROM comercial.detalle_notas_credito_debito D
        WHERE D.id_notas_credito_debito = %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql_header, (id_nc,))
            row = cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            header = dict(zip(cols, row))

            cursor.execute(sql_detail, (id_nc,))
            detail_cols = [d[0] for d in cursor.description]
            details = [dict(zip(detail_cols, drow)) for drow in cursor.fetchall()]

    return {'header': _serialize_row(header), 'details': [_serialize_row(d) for d in details]}


def read_guia_payload(id_guia):
    sql_header = """
        SELECT G.id_guia, G.serie AS num_serie, G.numero AS num_documento,
               G.fecha_emision AS fecha_hora, TD.codigo_sunat,
               E.direccion AS direccion_emisor, E.telefono AS telefono_emisor,
               CASE WHEN C.ruc != '' THEN '6' WHEN C.dni != '' THEN '1' ELSE '0' END cliente_tipo_de_documento,
               CASE WHEN C.dni != '' THEN C.dni WHEN C.ruc != '' THEN C.ruc ELSE '00000000' END cliente_numero_de_documento,
               C.nombres_cliente, G.direccionllegada AS direccion_cliente,
               G.email AS email_cliente, G.telefono AS telefono_cliente,
               G.fecha_traslado, G.num_bultos, G.ubigeo_partida,
               G.direccionpartida, G.ubigeo_llegada, G.direccionllegada,
               G.ructrasnporte, G.transporte, G.licencia, G.placa,
               G.cod_empleado, G.id_puntodeventa,
               G.dni_chofer, G.chofer, G.tipo_transporte, G.peso,
               TG.codigo AS codigo_motivo_traslado, TG.descripcion AS descripcion_motivo_traslado,
               G.observaciones, G.estado_declaracion
        FROM comercial.guia G
            LEFT JOIN comercial.empresa E ON E.id_empresa = 1
            LEFT JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = G.id_tipodocumento
            LEFT JOIN comercial.cliente C ON C.codigo_cliente = G.codigo_cliente
            LEFT JOIN comercial.tipo_guia TG ON TG.id_tipo_guia = G.id_tipo_guia
        WHERE G.id_guia = %s
    """
    sql_detail = """
        SELECT D.codigo_producto, D.descripcion, D.cantidad, D.unidad_medida, D.monto
        FROM comercial.detalle_guia D
        WHERE D.id_guia = %s
    """
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql_header, (id_guia,))
            row = cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            header = dict(zip(cols, row))

            cursor.execute(sql_detail, (id_guia,))
            detail_cols = [d[0] for d in cursor.description]
            details = [dict(zip(detail_cols, drow)) for drow in cursor.fetchall()]

    return {'header': _serialize_row(header), 'details': [_serialize_row(d) for d in details]}


def read_venta_by_id(id_venta):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute("""
                SELECT V.id_venta, V.num_serie, V.num_documento,
                       C.ruc, C.nombres_cliente, V.monto_venta,
                       V.estado_declaracion, V.observaciones_declaracion,
                       V.fecha_hora, V.external_id, TD.codigo_sunat
                FROM comercial.ventas V
                    LEFT JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
                    LEFT JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = V.id_tipodocumento
                WHERE V.id_venta = %s
            """, (id_venta,))
            row = cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            return _serialize_row(dict(zip(cols, row)))
