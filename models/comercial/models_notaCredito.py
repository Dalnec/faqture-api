from base.comercial.db import __conectarse


class Venta:
    tipo_venta = None
    serie_documento = None
    numero_documento = None
    fecha_venta = None
    nombre_cliente = None
    documento_cliente = None
    direccion_cliente = None
    codigo_cliente = None
    vendedor = None
    total_venta = None
    codigo_tipo_documento = None
    id_venta = None
    codigo_tipo_documento_identidad = None
    forma_pago = None
    punto_venta = None
    motivo_o_sustento_de_nota = None
    external_id = None
    codigo_tipo_nota = None
    detalle_ventas = []

    def __str__(self):
        return "{} - {} {}".format(self.tipo_venta, self.serie_documento, self.detalle_ventas)

class DetalleVenta:
    def __init__(self, codigo_producto, nombre_producto, cantidad, precio_producto, unidad_medida):
        self.codigo_producto = codigo_producto
        self.nombre_producto = nombre_producto
        self.cantidad = float(cantidad)
        self.precio_producto = float(precio_producto)
        self.unidad_medida = unidad_medida

    def __str__(self):
        return self.nombre_producto


def leer_db_notaCredito():
    cnx = __conectarse()
    cursor = cnx.cursor()
    lista_ventas = []

    sql_header = """
            SELECT N.id_notas_credito_debito, N.serie, N.numero, N.fecha, N.codigo_motivo,
                N.motivo, V.observaciones_declaracion as observaciones_declaracion_venta,
				case when C.dni !='' then C.dni when C.ruc !='' then C.ruc else '00000000' end cliente_numero_de_documento, 
				N.persona, N.direccion, N.id_puntodeventa, TD.codigo_sunat,
				case when C.ruc !='' then '6' when C.dni !='' then '1'  else '0' end cliente_tipo_de_documento,
                V.num_serie, V.num_documento
            FROM comercial.notas_credito_debito N,
                comercial.ventas V,
				comercial.cliente C,
				comercial.tipodocumento TD
            WHERE N.id_referencia = V.id_venta
                AND N.estado_declaracion = 'PENDIENTE'
                AND N.observaciones_declaracion = ''
				AND C.codigo_cliente = V.codigo_cliente
				AND TD.id_tipodocumento = V.id_tipodocumento
            ORDER BY N.id_notas_credito_debito
        """

    sql_detail = """
            SELECT D.codigo_producto, D.descripcion, D.cantidad, D.precio_unitario
            FROM comercial.detalle_notas_credito_debito AS D
            WHERE id_notas_credito_debito = {}
        """
    cursor.execute(sql_header)
    for row in cursor.fetchall():
        venta = Venta()

        venta.id_venta = row[0]
        venta.serie_documento = row[1]
        venta.numero_documento = row[2]
        venta.fecha_venta = row[3]
        venta.codigo_tipo_nota = row[4]
        venta.motivo_o_sustento_de_nota = row[5]
        venta.external_id = row[6]    
        venta.documento_cliente = row[7]
        venta.nombre_cliente = row[8]
        venta.direccion_cliente = row[9] if row[9] != None else ''
        
        venta.forma_pago = ''
        venta.punto_venta = row[10]
        
        venta.codigo_tipo_documento = row[11]
        venta.codigo_tipo_documento_identidad = row[12]
        venta.serie_venta = row[13]
        venta.numero_venta = row[14]
        
        detalle_ventas = []
        total = 0.0
        cursor.execute(sql_detail.format(venta.id_venta))
        for deta in cursor.fetchall():
            detalle_ventas.append(DetalleVenta(deta[0],
                                            deta[1], deta[2], deta[3], "UND"))            
            total += float(deta[2] * deta[3])

        venta.total_venta = total  
        venta.detalle_ventas = detalle_ventas
        lista_ventas.append(venta)
    
    cursor.close()
    cnx.close()
    return _generate_lista(lista_ventas)

def _generate_lista(ventas):
    
    header_dics = []
    for venta in ventas:
        #codigo_tipo_documento = '07' # Nota de Credito 
        codigo_tipo_moneda = 'PEN'
        header_dic = {}

        # Opcionales
        header_dic['id_venta'] = int(venta.id_venta)
        header_dic['informacion_adicional'] = "Forma de pago:"+ venta.forma_pago +"|Caja: "+ venta.punto_venta

        # Creamos el cuerpo del pse
        header_dic['serie_documento'] = venta.serie_documento
        header_dic['numero_documento'] = int(venta.numero_documento)
        header_dic['fecha_de_emision'] = venta.fecha_venta.strftime('%Y-%m-%d')
        header_dic['hora_de_emision'] = venta.fecha_venta.strftime('%H:%M:%S')
        header_dic['codigo_tipo_documento'] = '07' # venta.codigo_tipo_documento
        header_dic['codigo_tipo_nota'] = venta.codigo_tipo_nota
        header_dic['motivo_o_sustento_de_nota'] = venta.motivo_o_sustento_de_nota
        header_dic['codigo_tipo_moneda'] = codigo_tipo_moneda
        header_dic['numero_orden_de_compra'] = ''
        
        # if venta.external_id:            
        #     # Con external_id
        #     documento_afectado = {}
        #     documento_afectado['external_id'] = venta.external_id
        #     header_dic['documento_afectado'] = documento_afectado
        # else:        
        # Sin external_id
        documento_afectado = {}
        documento_afectado['serie_documento'] = venta.serie_venta
        documento_afectado['numero_documento'] = int(venta.numero_venta)
        documento_afectado['codigo_tipo_documento'] = venta.codigo_tipo_documento
        header_dic['documento_afectado'] = documento_afectado
        
        # totales
        datos_totales = {}
        datos_totales['total_exportacion'] = 0
        datos_totales['total_operaciones_gravadas'] = 0
        datos_totales['total_operaciones_inafectas'] = 0
        datos_totales['total_operaciones_exoneradas'] = venta.total_venta
        datos_totales['total_operaciones_gratuitas'] = 0
        datos_totales['total_igv'] = 0
        datos_totales['total_impuestos'] = 0
        datos_totales['total_valor'] = venta.total_venta
        datos_totales['total_venta'] = venta.total_venta

        header_dic['totales'] = datos_totales

        # datos del cliente
        datos_del_cliente = {}
        datos_del_cliente['codigo_tipo_documento_identidad'] = venta.codigo_tipo_documento_identidad
        datos_del_cliente['numero_documento'] = venta.documento_cliente #if len(venta.documento_cliente) > 0  else '99999999' 
        datos_del_cliente['apellidos_y_nombres_o_razon_social'] = venta.nombre_cliente
        datos_del_cliente['codigo_pais'] = 'PE'
        datos_del_cliente['ubigeo'] = ''
        datos_del_cliente['direccion'] = venta.direccion_cliente
        datos_del_cliente['correo_electronico'] = ''
        datos_del_cliente['telefono'] = ''

        header_dic['datos_del_cliente_o_receptor'] = datos_del_cliente
        
        lista_items = []
        for deta in venta.detalle_ventas:
            item = {}
            item['codigo_interno'] = deta.codigo_producto
            item['descripcion'] = deta.nombre_producto
            item['codigo_producto_sunat'] = ''
            item['unidad_de_medida'] = 'NIU'
            item['cantidad'] = deta.cantidad
            item["valor_unitario"] = deta.precio_producto
            item['codigo_tipo_precio'] = '01'
            item['precio_unitario'] = deta.precio_producto
            item['codigo_tipo_afectacion_igv'] = '20'
            item['total_base_igv'] = round(deta.cantidad * deta.precio_producto, 3)
            item['porcentaje_igv'] = 18
            item['total_igv'] = 0
            item['total_impuestos'] = 0
            item['total_valor_item'] = round(deta.cantidad * deta.precio_producto, 3)
            item['total_item'] = round(deta.cantidad * deta.precio_producto, 3)
            lista_items.append(item)

        header_dic['items'] = lista_items
        header_dics.append(header_dic)

    return header_dics