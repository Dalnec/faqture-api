import time
from base.comercial.db import get_connection
from config import CONFIG
from models.comercial.base_models import Venta, DetalleVenta

date_header = CONFIG.date_header

SQL_HEADER = """
    SELECT DISTINCT
        V.id_venta,
        V.num_serie,
        V.num_documento,
        V.fecha_hora,
        TD.codigo_sunat,
        CASE WHEN C.ruc != '' THEN '6' WHEN C.dni != '' THEN '1' ELSE '0' END cliente_tipo_de_documento,
        CASE WHEN C.dni != '' THEN C.dni WHEN C.ruc != '' THEN C.ruc ELSE '00000000' END cliente_numero_de_documento,
        C.nombres_cliente,
        D.direccion,
        (CASE WHEN (SELECT SUM(dv.monto_impuesto_bolsas) FROM comercial.detalle_venta dv WHERE dv.id_venta = V.id_venta AND dv.monto_impuesto_bolsas != 0) IS NULL THEN 0 ELSE (SELECT SUM(dv.monto_impuesto_bolsas) FROM comercial.detalle_venta dv WHERE dv.id_venta = V.id_venta AND dv.monto_impuesto_bolsas != 0) END) + V.monto_venta total,
        V.cod_empleado,
        MP.descripcion AS forma_pago,
        V.id_puntodeventa,
        V.descuento,
        V.igv,
        V.id_tipopago,
        V.numero_placa
    FROM comercial.ventas V
        INNER JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = V.id_tipodocumento
        INNER JOIN comercial.cliente C ON C.codigo_cliente = V.codigo_cliente_anulado
        INNER JOIN comercial.direcciones D ON D.id_direcciones = V.id_direcciones
        INNER JOIN comercial.metodo_pago MP ON MP.id_metodo_pago = V.id_metodo_pago
    WHERE V.estado_declaracion = ANY(%s)
        AND V.num_serie NOT IN ('PRE')
        AND TD.codigo_sunat = ANY(%s)
        AND V.fecha_hora >= %s
    ORDER BY V.fecha_hora
"""

SQL_DETAIL = """
    SELECT
        P.codigo_producto codigo,
        DV.descripcion,
        DV.cantidad,
        DV.monto precio_unitario,
        CASE WHEN P.impuesto_bolsas = 'TRUE' THEN (SELECT parametros.valor::DECIMAL FROM comercial.parametros WHERE id_parametros = 72) * DV.cantidad ELSE 0 END impuesto_bolsas,
        DV.descuento_individual,
        porcentaje_descuento,
        (DV.cantidad * DV.monto) sub_total,
        monto_total,
        DV.igv,
        DV.igv_descuento,
        DV.descuento_total
    FROM comercial.detalle_venta DV
        INNER JOIN comercial.producto P ON P.codigo_producto = DV.codigo_producto
        INNER JOIN comercial.ventas V ON V.id_venta = DV.id_venta
    WHERE V.id_venta = %s
"""


def leer_db(filtro_estados, filtro_sunat, descuento_codigo, descuento_desc, redondear_cantidad=False):
    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(SQL_HEADER, (list(filtro_estados), list(filtro_sunat), date_header))
            lista_ventas = []

            for row in cursor.fetchall():
                venta = Venta()
                venta.id_venta = row[0]
                venta.serie_documento = row[1]
                venta.numero_documento = row[2]
                venta.fecha_venta = row[3]
                venta.codigo_tipo_documento = row[4]
                venta.codigo_tipo_documento_identidad = row[5]
                venta.documento_cliente = row[6]
                venta.nombre_cliente = row[7]
                venta.direccion_cliente = row[8] if row[8] is not None else ''
                venta.total_venta = float(row[9])
                venta.vendedor = row[10]
                venta.forma_pago = row[11]
                venta.punto_venta = row[12]
                venta.descuentos = float(row[13])
                venta.igv = float(row[14])
                venta.codigo_condicion_de_pago = row[15]
                venta.total_bolsa_plastica = 0
                venta.total_descuentos = 0
                venta.total_gratuito = 0
                venta.sumSubtotales = 0
                venta.numero_placa = row[16]

                cursor.execute(SQL_DETAIL, (venta.id_venta,))
                for deta in cursor.fetchall():
                    venta.detalle_ventas.append(
                        DetalleVenta(deta[0], deta[1], deta[2], deta[3], "UND", deta[4],
                                     deta[5], deta[6], deta[7], deta[8], deta[9], deta[10], deta[11])
                    )
                    venta.total_bolsa_plastica += float(deta[4])
                    venta.total_descuentos += float(deta[5])
                    venta.sumSubtotales += float(deta[2]) * float(deta[3])
                    if deta[8] == 0:
                        venta.total_gratuito += float(deta[2]) * float(deta[3])

                lista_ventas.append(venta)

    return _generate_lista(lista_ventas, descuento_codigo, descuento_desc, redondear_cantidad)


def leer_db_documentos():
    return leer_db(
        filtro_estados=('PENDIENTE', 'ANULADO'),
        filtro_sunat=('01', '03'),
        descuento_codigo='01',
        descuento_desc="Descuentos que no afectan la base imponible del IGV/IVAP",
    )


def leer_db_notas():
    return leer_db(
        filtro_estados=('NO DECLARAR',),
        filtro_sunat=('80',),
        descuento_codigo='00',
        descuento_desc="Descuento Lineal",
        redondear_cantidad=True,
    )


def _generate_lista(ventas, descuento_codigo, descuento_desc, redondear_cantidad):
    header_dics = []
    for venta in ventas:
        codigo_tipo_moneda = 'PEN'
        header_dic = {}

        header_dic['id_venta'] = int(venta.id_venta)
        header_dic['informacion_adicional'] = "Forma de pago:" + venta.forma_pago + "|Caja: " + venta.punto_venta
        header_dic['serie_documento'] = venta.serie_documento
        header_dic['numero_documento'] = int(venta.numero_documento)
        header_dic['fecha_de_emision'] = venta.fecha_venta.strftime('%Y-%m-%d')
        header_dic['hora_de_emision'] = venta.fecha_venta.strftime('%H:%M:%S')
        header_dic['codigo_tipo_operacion'] = '0101'
        header_dic['codigo_tipo_documento'] = venta.codigo_tipo_documento
        header_dic['codigo_tipo_moneda'] = codigo_tipo_moneda
        header_dic['fecha_de_vencimiento'] = venta.fecha_venta.strftime('%Y-%m-%d')
        header_dic['numero_orden_de_compra'] = ''

        datos_del_cliente = {}
        datos_del_cliente['codigo_tipo_documento_identidad'] = venta.codigo_tipo_documento_identidad
        datos_del_cliente['numero_documento'] = venta.documento_cliente
        datos_del_cliente['apellidos_y_nombres_o_razon_social'] = venta.nombre_cliente
        datos_del_cliente['codigo_pais'] = 'PE'
        datos_del_cliente['ubigeo'] = ""
        datos_del_cliente['direccion'] = venta.direccion_cliente
        datos_del_cliente['correo_electronico'] = ''
        datos_del_cliente['telefono'] = ''
        header_dic['datos_del_cliente_o_receptor'] = datos_del_cliente

        header_dic['codigo_condicion_de_pago'] = '01'
        if venta.codigo_condicion_de_pago == 2:
            header_dic['codigo_condicion_de_pago'] = '02'
            fecha_pago = time.strptime(venta.fecha_venta.strftime('%Y-%m-%d'), '%Y-%m-%d')
            fecha_pago = time.mktime(fecha_pago) + 2592000
            fecha_pago = time.localtime(fecha_pago)
            fecha_pago = time.strftime("%Y-%m-%d", fecha_pago)
            cuotas = [{'fecha': fecha_pago, 'codigo_tipo_moneda': codigo_tipo_moneda, 'monto': venta.total_venta + venta.igv}]
            header_dic['cuotas'] = cuotas

        if venta.descuentos != 0:
            descuentosT = {
                'codigo': descuento_codigo,
                'descripcion': descuento_desc,
                'factor': round(venta.descuentos / venta.sumSubtotales, 5),
                'monto': round(venta.descuentos, 2),
                'base': round(venta.sumSubtotales, 2),
            }
            header_dic['descuentos'] = [descuentosT]

        datos_totales = {}
        if venta.descuentos != 0:
            datos_totales['total_descuentos'] = round(venta.total_descuentos + venta.descuentos, 2)
            datos_totales['subtotal_venta'] = venta.total_venta + venta.descuentos - venta.total_bolsa_plastica
        datos_totales['total_exportacion'] = 0.00
        datos_totales['total_operaciones_gravadas'] = 0.00 if venta.igv == 0 else venta.total_venta + venta.descuentos
        datos_totales['total_operaciones_inafectas'] = 0.00
        datos_totales['total_operaciones_exoneradas'] = venta.total_venta + venta.descuentos - venta.total_bolsa_plastica if venta.igv == 0 else 0.00
        datos_totales['total_operaciones_gratuitas'] = round(venta.total_gratuito, 2)
        datos_totales['total_impuestos_bolsa_plastica'] = venta.total_bolsa_plastica
        datos_totales['total_igv'] = 0.00 if venta.igv == 0 else venta.igv
        datos_totales['total_impuestos'] = 0.00 if venta.igv == 0 else venta.igv + venta.total_bolsa_plastica
        datos_totales['total_valor'] = venta.total_venta if venta.descuentos == 0 else venta.total_venta + venta.descuentos
        datos_totales['total_venta'] = venta.total_venta + venta.igv
        header_dic['totales'] = datos_totales

        lista_items = []
        cont = 0
        for deta in venta.detalle_ventas:
            item = {}
            item['codigo_interno'] = deta.codigo_producto
            item['descripcion'] = deta.nombre_producto
            item['codigo_producto_sunat'] = ''
            item['unidad_de_medida'] = 'NIU'
            item['cantidad'] = round(deta.cantidad, 2) if redondear_cantidad else deta.cantidad
            item['codigo_tipo_precio'] = '01'
            item['precio_unitario'] = deta.precio_producto

            if cont == 0 and venta.numero_placa:
                item['datos_adicionales'] = _datos_adicionales(venta.numero_placa)
                cont += 1

            if deta.desc_individual != 0 and deta.monto_total != 0:
                item['precio_unitario'] = deta.precio_producto - (deta.desc_individual / round(deta.cantidad, 2))
                descuentos = {
                    'codigo': descuento_codigo,
                    'descripcion': descuento_desc,
                    'factor': deta.desc_porcentaje / 100,
                    'monto': deta.desc_individual,
                    'base': deta.sub_total,
                }
                item['descuentos'] = [descuentos]

            if deta.igv == 0 and deta.precio_producto != 0 and deta.monto_total != 0:
                lista_items.append(_detalle_items_exonerada(deta, item))
            elif deta.igv != 0 and deta.precio_producto != 0 and deta.monto_total != 0:
                lista_items.append(_detalle_items_gravado(deta, item))
            else:
                lista_items.append(_detalle_items_gratuito(deta, item))

        header_dic['items'] = lista_items
        header_dics.append(header_dic)

    return header_dics


def _detalle_items_exonerada(deta, item):
    item["valor_unitario"] = deta.precio_producto
    item['codigo_tipo_afectacion_igv'] = '20'
    item['total_base_igv'] = deta.monto_total if deta.descuento_total == 0 else (deta.cantidad * deta.precio_producto)
    item['porcentaje_igv'] = 18
    item['total_igv'] = 0
    item['total_impuestos_bolsa_plastica'] = deta.total_impuestos_bolsa_plastica
    item['total_impuestos'] = 0
    item['total_valor_item'] = deta.monto_total if deta.descuento_total == 0 else (deta.cantidad * deta.precio_producto)
    item['total_item'] = deta.monto_total if deta.descuento_total == 0 else (deta.cantidad * deta.precio_producto)
    return item


def _detalle_items_gravado(deta, item):
    item["valor_unitario"] = round((deta.precio_producto - deta.igv), 2)
    item['codigo_tipo_afectacion_igv'] = '10'
    item['total_base_igv'] = round(deta.monto_total / 1.18, 2)
    item['porcentaje_igv'] = 18
    item['total_igv'] = round(deta.monto_total - (deta.monto_total / 1.18), 2)
    item['total_impuestos_bolsa_plastica'] = deta.total_impuestos_bolsa_plastica
    item['total_impuestos'] = round(deta.monto_total - (deta.monto_total / 1.18), 2)
    item['total_valor_item'] = round(deta.monto_total / 1.18, 2)
    item['total_item'] = deta.monto_total
    return item


def _detalle_items_gratuito(deta, item):
    item["valor_unitario"] = 0
    item['codigo_tipo_precio'] = '02'
    item['precio_unitario'] = deta.precio_producto
    item['codigo_tipo_afectacion_igv'] = '21'
    item['total_base_igv'] = deta.cantidad * deta.precio_producto if deta.igv == 0 else round(deta.cantidad * deta.precio_producto / 1.18, 2)
    item['porcentaje_igv'] = 18
    item['total_igv'] = 0 if deta.igv == 0 else round(deta.monto_total - (deta.monto_total / 1.18), 2)
    item['total_impuestos_bolsa_plastica'] = deta.total_impuestos_bolsa_plastica
    item['total_impuestos'] = 0
    item['total_valor_item'] = deta.sub_total
    item['total_item'] = 0
    return item


def _datos_adicionales(numero_placa):
    return [{'codigo': "5010", 'descripcion': "Numero de Placa", 'valor': numero_placa}]
