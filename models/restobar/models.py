
from base.restobar.db import __conectarse
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
date_header = config['MODELS']['DATE_HEADER']
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
    email = None
    telefono = None
    delivery_telefono = None
    total_bolsa_plastica = None
    total_descuento = None
    total_efectivo = None
    detalle_ventas = []

    def __str__(self):
        return "{} - {} {}".format(self.tipo_venta, self.serie_documento, self.detalle_ventas)


class DetalleVenta:
    def __init__(self, codigo_producto, nombre_producto, cantidad, precio_producto, unidad_medida, total_impuestos_bolsa_plastica, descuento):
        #self.posicion = posicion
        self.codigo_producto = codigo_producto
        self.nombre_producto = nombre_producto
        self.cantidad = float(cantidad)
        self.precio_producto = float(precio_producto)
        self.unidad_medida = unidad_medida
        self.total_impuestos_bolsa_plastica = float(total_impuestos_bolsa_plastica)
        self.descuento = float(descuento)

    def __str__(self):
        return self.nombre_producto


def r_leer_db_access():
    cnx = __conectarse()
    cursor = cnx.cursor()
    lista_ventas = []

    sql_header = """
            SELECT DISTINCT
                ventas.id_venta, 
                ventas.num_serie, 
                ventas.num_documento, 
                ventas.fecha_hora,
                '0101' codigo_tipo_operacion,
                documento.codigo_sunat codigo_tipo_documento, 
                'PEN' codigo_tipo_moneda,
                ventas.fecha_hora,
                case when cliente.ruc !='' then '6' when cliente.dni !='' then '1'  else '0' end codigo_tipo_documento_identidad,
                case when cliente.dni !='' then  cliente.dni when cliente.ruc !='' then cliente.ruc else '00000000' end numero_de_documento, 	
                cliente.nombres,
                'PE' codigo_pais,
                '' ubigeo, 
                cliente.direccion, 
                cliente.email,  
                cliente.telefono,  
                cliente.delivery_telefono,  
                0.00 total_exportacion,
                0.00 total_operaciones_gravada,
                0.00 total_operaciones_inafectas,
                ventas.monto_venta total_operaciones_exoneradas,
                ( case when( select sum(dv.impuesto_icbper) from gulash.detalle_venta dv where dv.id_venta= ventas.id_venta and dv.impuesto_icbper != 0) is null then 0 else (select sum(dv.impuesto_icbper) from gulash.detalle_venta dv where dv.id_venta= ventas.id_venta and dv.impuesto_icbper != 0) end ) total_impuestos_bolsas,                
                0.00 total_igv,
                0.00 total_impuestos,
                ventas.monto_venta total_valor, 
                ventas.monto_venta+ ( case when( select sum(dv.impuesto_icbper) from gulash.detalle_venta dv where dv.id_venta= ventas.id_venta and dv.impuesto_icbper != 0) is null then 0 else (select sum(dv.impuesto_icbper) from gulash.detalle_venta dv where dv.id_venta= ventas.id_venta and dv.impuesto_icbper != 0) end ) total_venta,
                medio_pago.descripcion informacion_adicional,
                ventas.monto_efectivo,
                ventas.descuento
            FROM 
                gulash.ventas
                INNER JOIN gulash.detalle_venta ON ventas.id_venta = detalle_venta.id_venta
                INNER JOIN gulash.documento ON documento.id_documento = ventas.id_documento
                INNER JOIN gulash.cliente ON cliente.codigo_cliente = ventas.codigo_cliente
                INNER JOIN gulash.producto_venta ON producto_venta.cod_producto_venta = detalle_venta.cod_producto_venta
                INNER JOIN gulash.medio_pago ON medio_pago.id_medio_pago = ventas.id_medio_pago
                
            WHERE   
                documento.estado='A' AND 
                documento.electronico='S' AND
                ventas.estado in ('A', 'I') AND
                ventas.estado_declaracion = 'PENDIENTE' AND
                ventas.estado_declaracion_anulado = '' AND
                ventas.fecha_hora >= '{}'
                --ventas.fecha_hora = '2020-08-19 17:03:00'
            ORDER BY id_venta
        """

    sql_detail = """
            Select distinct
                detalle_venta.cod_producto_venta codigo_interno,
                detalle_venta.descripcion descripcion,
                '' codigo_producto_sunat,
                'NIU' unidad_de_medida,
                cantidad cantidad,
                precio valor_unitario,
                '01' codigo_tipo_precio,
                precio precio_unitario,
                20 codigo_tipo_afectacion_igv,
                0 total_base_igv,
                18 porcentaje_igv,
                0.00 total_igv,
                impuesto_icbper total_impuestos_bolsa_plastica,
                '18' total_impuestos,
                cantidad*precio total_valor_item,
                cantidad*precio total_item,
                detalle_venta.descuento

            FROM gulash.detalle_venta
                inner join gulash.ventas ON detalle_venta.id_venta=ventas.id_venta
            WHERE 
                ventas.id_venta= {}
        """
    cursor.execute(sql_header.format(date_header))

    for row in cursor.fetchall():
        venta = Venta()
        venta.id_venta = row[0]        
        venta.serie_documento = row[1]        
        venta.numero_documento = row[2]
        venta.fecha_venta = row[3]
        venta.codigo_tipo_documento = row[5]
        venta.codigo_tipo_documento_identidad = row[8]
        venta.documento_cliente = row[9]
        venta.nombre_cliente = row[10]
        venta.direccion_cliente = row[13] if row[13] != None else ''
        venta.email = row[14]
        venta.telefono = row[15]
        venta.delivery_telefono = row[16]
        venta.total_bolsa_plastica = row[21]        
        venta.total_venta = row[25]
        venta.forma_pago = row[26]
        venta.total_descuentos = 0
        venta.total_efectivo = row[27]
        venta.descuentos = row[28]

        '''venta.tipo_venta = row[3]
        venta.codigo_cliente = row[9]
        venta.vendedor = row[10]
        venta.punto_venta = row[14]'''

        detalle_ventas = []
        cursor.execute(sql_detail.format(venta.id_venta))
        for deta in cursor.fetchall():  #codigo_producto, nombre_producto, cantidad, precio_producto, unidad_medida, total_impuestos_bolsa_plastica
            detalle_ventas.append(DetalleVenta(deta[0], deta[1], deta[4], deta[5], "UND", deta[12], deta[16]))
            venta.total_descuentos += deta[16]
        venta.detalle_ventas = detalle_ventas
        lista_ventas.append(venta)
    
    cursor.close()
    cnx.close()
    return _generate_lista(lista_ventas)

def _generate_lista(ventas):
    
    header_dics = []
    for venta in ventas:
        codigo_tipo_operacion = '0101'
        codigo_tipo_moneda = 'PEN'
        header_dic = {}

        # opcionales
        header_dic['id_venta'] = int(venta.id_venta)
        header_dic['informacion_adicional'] = "Forma de pago:"+ venta.forma_pago #+"|Caja: "+ venta.punto_venta
        # Creamos el cuerpo del pse
        header_dic['serie_documento'] = venta.serie_documento
        header_dic['numero_documento'] = int(venta.numero_documento)
        header_dic['fecha_de_emision'] = venta.fecha_venta.strftime('%Y-%m-%d')
        header_dic['hora_de_emision'] = venta.fecha_venta.strftime('%H:%M:%S')
        header_dic['codigo_tipo_operacion'] = codigo_tipo_operacion
        header_dic['codigo_tipo_documento'] = venta.codigo_tipo_documento
        header_dic['codigo_tipo_moneda'] = codigo_tipo_moneda
        header_dic['fecha_de_vencimiento'] = venta.fecha_venta.strftime(
            '%Y-%m-%d')
        header_dic['numero_orden_de_compra'] = ''

        # datos del cliente
        datos_del_cliente = {}
        datos_del_cliente['codigo_tipo_documento_identidad'] = venta.codigo_tipo_documento_identidad
        datos_del_cliente['numero_documento'] = venta.documento_cliente
        datos_del_cliente['apellidos_y_nombres_o_razon_social'] = venta.nombre_cliente
        datos_del_cliente['codigo_pais'] = 'PE'
        datos_del_cliente['ubigeo'] = ''
        datos_del_cliente['direccion'] = venta.direccion_cliente
        datos_del_cliente['correo_electronico'] = ''
        datos_del_cliente['telefono'] = ''

        header_dic['datos_del_cliente_o_receptor'] = datos_del_cliente
        # descuentos Total
        if venta.total_descuentos != 0:
            descT = []
            descuentosT = {}
            descuentosT['codigo'] = '03'
            descuentosT['descripcion'] = "Descuentos globales que no afectan la base imponible del IGV/IVAP"
            descuentosT['factor'] = round(float(venta.total_descuentos) / float(venta.total_venta),5)
            descuentosT['monto'] = float(venta.total_descuentos)
            descuentosT['base'] = float(venta.total_venta)
            descT.append(descuentosT)
            header_dic['descuentos'] = descT

        # totales
        datos_totales = {}
        if venta.total_descuentos != 0: 
            datos_totales['total_descuentos'] = round(float(venta.total_descuentos),2)        
            datos_totales['subtotal_venta'] = float(venta.total_venta) - float(venta.total_bolsa_plastica)
        datos_totales['total_exportacion'] = 0
        datos_totales['total_operaciones_gravadas'] = 0
        datos_totales['total_operaciones_inafectas'] = 0
        datos_totales['total_operaciones_exoneradas'] = float(venta.total_venta) - float(venta.total_bolsa_plastica)
        datos_totales['total_operaciones_gratuitas'] = 0
        datos_totales['total_impuestos_bolsa_plastica'] = float(venta.total_bolsa_plastica)
        datos_totales['total_igv'] = 0
        datos_totales['total_impuestos'] = 0
        datos_totales['total_valor'] = float(venta.total_venta) - float(venta.total_bolsa_plastica)#float(venta.total_venta) - round(float(venta.total_descuentos),2)
        datos_totales['total_venta'] = float(venta.total_venta) - round(float(venta.total_descuentos),2)

        header_dic['totales'] = datos_totales        
        
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
                
            total_item = float(deta.cantidad * deta.precio_producto)
            # descuentos por item
            '''if venta.total_descuentos != 0:
                desc = []
                descuentos = {}
                descuentos['codigo'] = '00'
                descuentos['descripcion'] = "Descuento Lineal"
                descuentos['factor'] = round((deta.descuento / total_item), 2)
                descuentos['monto'] = deta.descuento
                descuentos['base'] = total_item
                desc.append(descuentos)
                item['descuentos'] = desc'''
            
            item['total_base_igv'] = total_item
            item['porcentaje_igv'] = 18
            item['total_igv'] = 0
            item['total_impuestos_bolsa_plastica'] = deta.total_impuestos_bolsa_plastica
            item['total_impuestos'] = 0
            item['total_valor_item'] = total_item
            item['total_item'] = total_item
            lista_items.append(item)

        header_dic['items'] = lista_items
        header_dics.append(header_dic)

    return header_dics