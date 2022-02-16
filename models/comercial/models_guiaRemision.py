from base.comercial.db import __conectarse

class Guia:    
    id_guia = None
    serie_documento = None
    numero_documento = None
    fecha_guia = None
    codigo_tipo_documento = None
    ubigeo_emisor = None
    direccion_emisor = None
    telefono_emisor = None
    codigo_tipo_documento_identidad = None
    documento_cliente = None
    nombre_cliente = None
    ubigeo_cliente = None
    direccion_cliente = None
    email_cliente = None
    telefono_cliente = None
    fecha_traslado = None
    num_bultos = None
    ubigeo_partida = None
    direccion_partida = None
    ubigeo_llegada = None
    direccion_llegada = None
    ruc_transportista = None
    transporte = None
    num_licencia = None
    placa_vehiculo = None
    cod_empleado = None
    punto_venta = None
    
    detalle_guias = []

    def __str__(self):
        return "{} - {} {}".format(self.codigo_tipo_documento, self.serie_documento, self.detalle_guias)


class DetalleGuia:
    def __init__(self, codigo_producto, nombre_producto, cantidad, unidad_medida, monto):
        self.codigo_producto = codigo_producto
        self.nombre_producto = nombre_producto
        self.cantidad = float(cantidad)
        #self.precio_producto = float(precio_producto)
        self.unidad_medida = unidad_medida
        self.monto = float(monto)

    def __str__(self):
        return self.nombre_producto

def leer_db_guia():
    cnx = __conectarse()
    cursor = cnx.cursor()
    lista_guias = []

    sql_header = """
    SELECT G.id_guia, 
        split_part(G.num_documento::TEXT,'-', 1) serie,
        split_part(G.num_documento::TEXT,'-', 2) num,
        G.fecha_hora,
        TD.codigo_sunat,  
        'UBIGEOEmisor' AS UBIGEO,
        E.direccion, 
        E.telefono,
        case when G.ruccliente !='' then '6' when G.dni_cliente !='' then '1'  else '0' end cliente_tipo_de_documento,         
        case when G.dni_cliente !='' then G.dni_cliente when G.ruccliente !='' then G.ruccliente else '00000000' end cliente_numero_de_documento,
        G.nombre_representante,
        'UbigeoCliente' AS ubigeoCliente,
        G.direccionllegada,
        C.email,
        case when C.telefono !='' and C.celular !='' then C.telefono || ' - ' || C.celular when C.telefono !='' then C.telefono when C.celular !='' then C.celular  else '' end telefono_cliente,
        G.fecha_traslado,
        G.num_bultos,
        'UbigeoPartida' as ubigeoPartida,
        G.direccionpartida,
        'UbigeoLLegada' as ubigeoLLegada,
        G.ructrasnporte,
        G.transporte,
        G.licencia,
        G.placa,
        G.cod_empleado,
        G.id_puntodeventa
    FROM comercial.guia G
    INNER JOIN comercial.empresa E ON E.id_empresa = G.id_empresa
    INNER JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = G.id_tipo_documento_guia
    INNER JOIN comercial.tipodocumento ON tipodocumento.id_tipodocumento = G.id_tipodocumento
    INNER JOIN comercial.cliente C ON C.nombres_cliente = G.nombre_representante
    WHERE G.estado = 'A' AND razonsocial = ''
    ORDER BY fecha_hora
    """
    sql_detail = """
    SELECT id_detalle_guia, 
        id_guia, 
        codigo_producto,
        descripcion,
        cantidad,
        unidad_medida,
        monto
    FROM comercial.detalle_guia
    WHERE
        id_guia = {}
    """
    cursor.execute(sql_header)

    for row in cursor.fetchall():
        guia = Guia()
        guia.id_guia = int(row[0])
        guia.serie_documento = row[1]
        guia.numero_documento = row[2]
        guia.fecha_guia = row[3]
        guia.codigo_tipo_documento = row[4]
        guia.ubigeo_emisor = row[5]
        guia.direccion_emisor = row[6]
        guia.telefono_emisor = row[7]
        guia.codigo_tipo_documento_identidad = row[8]
        guia.documento_cliente = row[9]
        guia.nombre_cliente = row[10]
        guia.ubigeo_cliente = row[11]
        guia.direccion_cliente = row[12]
        guia.email_cliente = row[13]
        guia.telefono_cliente = row[14]
        guia.fecha_traslado = row[15]
        guia.num_bultos = row[16]
        guia.ubigeo_partida = row[17]
        guia.direccion_partida = row[18]
        guia.ubigeo_llegada = row[19]
        guia.direccion_llegada = row[12]
        guia.ruc_transportista = row[20]
        guia.transporte = row[21]
        guia.num_licencia = row[22]
        guia.placa_vehiculo = row[23]
        guia.cod_empleado = row[24]
        guia.punto_venta = row[25]
        detalle_guia = []
        cursor.execute(sql_detail.format(guia.id_guia))
        for deta in cursor.fetchall():
            detalle_guia.append(DetalleGuia(deta[2], deta[3], deta[4], 'NIU', deta[6]))
        guia.detalle_guias = detalle_guia
        lista_guias.append(guia)
    
    cursor.close()
    cnx.close()
    return _generate_lista(lista_guias)

def _generate_lista(guias):
    
    header_dics = []
    for guia in guias:
        codigo_pais = 'PE'
        header_dic = {}

        # Opcionales
        header_dic['id_guia'] = guia.id_guia
        header_dic['informacion_adicional'] = "Usuario:"+ guia.cod_empleado +"|Caja: "+ guia.punto_venta
        # Creamos el cuerpo del pse
        header_dic['serie_documento'] = 'T%s' % guia.serie_documento
        header_dic['numero_documento'] = int(guia.numero_documento)
        header_dic['fecha_de_emision'] = guia.fecha_guia.strftime('%Y-%m-%d')
        header_dic['hora_de_emision'] = guia.fecha_guia.strftime('%H:%M:%S')
        header_dic['codigo_tipo_documento'] = guia.codigo_tipo_documento
        # datos del emisor
        datos_del_emisor = {}
        datos_del_emisor['codigo_pais'] = codigo_pais
        datos_del_emisor['ubigeo'] = '220101'
        datos_del_emisor['direccion'] = guia.direccion_emisor
        datos_del_emisor['correo_electronico'] = ''
        datos_del_emisor['telefono'] = guia.telefono_emisor
        datos_del_emisor['codigo_del_domicilio_fiscal'] = '0000'
        header_dic['datos_del_emisor'] = datos_del_emisor
        # datos del cliente o receptor
        datos_del_cliente_o_receptor = {}
        datos_del_cliente_o_receptor['codigo_tipo_documento_identidad'] = guia.codigo_tipo_documento_identidad
        datos_del_cliente_o_receptor['numero_documento'] = guia.documento_cliente
        datos_del_cliente_o_receptor['apellidos_y_nombres_o_razon_social'] = guia.nombre_cliente
        datos_del_cliente_o_receptor['codigo_pais'] = 'PE'
        datos_del_cliente_o_receptor['ubigeo'] = ''
        datos_del_cliente_o_receptor['direccion'] = guia.direccion_cliente
        datos_del_cliente_o_receptor['correo_electronico'] = guia.email_cliente
        datos_del_cliente_o_receptor['telefono'] = guia.telefono_cliente
        header_dic['datos_del_cliente_o_receptor'] = datos_del_cliente_o_receptor
        # continua cuerpo del pse
        header_dic['observaciones'] = 'aaaaaaaaaa'
        header_dic['codigo_modo_transporte'] = '01'
        header_dic['codigo_motivo_traslado'] = '01'
        header_dic['descripcion_motivo_traslado'] = 'mmmmmmmmmmmmmmmmmmmmmmm'
        header_dic['fecha_de_traslado'] = guia.fecha_traslado.strftime('%Y-%m-%d')
        header_dic['codigo_de_puerto'] = ''
        header_dic['indicador_de_transbordo'] = False
        header_dic['unidad_peso_total'] = 'KGM'
        header_dic['peso_total'] = 0
        header_dic['numero_de_bultos'] = guia.num_bultos
        header_dic['numero_de_contenedor'] = ''
        # direccion partida
        direccion_partida = {}
        direccion_partida['ubigeo'] = '220101'
        direccion_partida['direccion'] = guia.direccion_partida
        header_dic['direccion_partida'] = direccion_partida
        # direccion llegada
        direccion_llegada = {}
        direccion_llegada['ubigeo'] = '220101'
        direccion_llegada['direccion'] = guia.direccion_llegada
        header_dic['direccion_llegada'] = direccion_llegada
        # transportista
        transportista = {}
        transportista['codigo_tipo_documento_identidad'] = '6'
        transportista['numero_documento'] = guia.ruc_transportista
        transportista['apellidos_y_nombres_o_razon_social'] = guia.transporte
        header_dic['transportista'] = transportista
        # chofer   
        chofer = {}
        chofer['codigo_tipo_documento_identidad'] = '1'
        chofer['numero_documento'] = guia.num_licencia
        header_dic['chofer'] = chofer
        # continua cuerpo del pse
        header_dic['numero_de_placa'] = guia.placa_vehiculo

        # lista de items
        lista_items = []
        for deta in guia.detalle_guias:
            item = {}
            #precio_producto = deta.monto / deta.cantidad
            item['codigo_interno'] = deta.codigo_producto
            #item['descripcion'] = deta.nombre_producto
            #item['codigo_producto_sunat'] = ''
            #item['codigo_producto_gsl'] = ''
            #item['unidad_de_medida'] = 'NIU'
            item['cantidad'] = round(deta.cantidad, 2)
            #item["valor_unitario"] = round(precio_producto, 2)
            #item['codigo_tipo_precio'] = '01'
            #item['precio_unitario'] = precio_producto
            #item['codigo_tipo_afectacion_igv'] = '20' #if deta.igv == 0 else '10'
            #item['total_base_igv'] = deta.monto #if deta.igv == 0 else round(deta.monto_total/1.18, 2)
            #item['porcentaje_igv'] = 18
            #item['total_igv'] = 0 #if deta.igv == 0 else round(deta.monto_total - (deta.monto_total/1.18), 2) 
            #item['total_impuestos_bolsa_plastica'] = deta.total_impuestos_bolsa_plastica
            #item['total_impuestos'] = 0 #if deta.igv == 0 else round(deta.monto_total - (deta.monto_total/1.18), 2)
            #item['total_valor_item'] = deta.monto #if deta.igv == 0 else round(deta.monto_total/1.18, 2)#(deta.cantidad * deta.precio_producto)
            #item['total_item'] = deta.monto
            lista_items.append(item)

        header_dic['items'] = lista_items
        header_dics.append(header_dic)

    return header_dics