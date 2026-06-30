from base.comercial.db import get_connection


class Guia:
    def __init__(self):
        self.id_guia = None
        self.serie_documento = None
        self.numero_documento = None
        self.fecha_guia = None
        self.codigo_tipo_documento = None
        self.ubigeo_emisor = None
        self.direccion_emisor = None
        self.telefono_emisor = None
        self.codigo_tipo_documento_identidad = None
        self.documento_cliente = None
        self.nombre_cliente = None
        self.ubigeo_cliente = None
        self.direccion_cliente = None
        self.email_cliente = None
        self.telefono_cliente = None
        self.fecha_traslado = None
        self.num_bultos = None
        self.ubigeo_partida = None
        self.direccion_partida = None
        self.ubigeo_llegada = None
        self.direccion_llegada = None
        self.ruc_transportista = None
        self.transporte = None
        self.num_licencia = None
        self.placa_vehiculo = None
        self.cod_empleado = None
        self.punto_venta = None
        self.dni_chofer = None
        self.chofer = None
        self.tipo_transporte = None
        self.peso = None
        self.codigo_motivo_traslado = None
        self.descripcion_motivo_traslado = None
        self.observaciones = None
        self.detalle_guias = []

    def __str__(self):
        return "{} - {} {}".format(self.codigo_tipo_documento, self.serie_documento, self.detalle_guias)


class DetalleGuia:
    def __init__(self, codigo_producto, nombre_producto, cantidad, unidad_medida, monto):
        self.codigo_producto = codigo_producto
        self.nombre_producto = nombre_producto
        self.cantidad = float(cantidad)
        self.unidad_medida = unidad_medida
        self.monto = float(monto)

    def __str__(self):
        return self.nombre_producto


def leer_db_guia():
    sql_header = """
    SELECT
        G.id_guia,
        G.num_serie,
        G.num_documento,
        G.fecha_hora,
        TD.codigo_sunat,
        'UBIGEOEmisor' AS UBIGEO,
        E.direccion,
        E.telefono,
        CASE
            WHEN G.ruccliente <> '' THEN '6'
            WHEN G.dni_cliente <> '' THEN '1'
            ELSE '0'
        END AS cliente_tipo_de_documento,
        CASE
            WHEN G.dni_cliente <> '' THEN G.dni_cliente
            WHEN G.ruccliente <> '' THEN G.ruccliente
            ELSE '00000000'
        END AS cliente_numero_de_documento,
        G.nombre_representante,
        'UbigeoCliente' AS ubigeoCliente,
        G.direccionllegada,
        C.email,
        CASE WHEN C.telefono != '' AND C.celular != '' THEN C.telefono || ' - ' || C.celular WHEN C.telefono != '' THEN C.telefono WHEN C.celular != '' THEN C.celular ELSE '' END telefono_cliente,
        G.fecha_traslado,
        G.num_bultos,
        G.ubigeo_partida,
        G.direccionpartida,
        G.ubigeo_llegada,
        G.ructrasnporte,
        G.transporte,
        G.licencia,
        G.placa,
        G.cod_empleado,
        G.id_puntodeventa,
        G.dni_chofer,
        G.chofer,
        G.tipo_transporte,
        G.peso,
        TG.codigo,
        TG.descripcion,
        G.descripcion_motivo_otros as observaciones
    FROM comercial.guia G
    INNER JOIN comercial.empresa E ON E.id_empresa = G.id_empresa
    INNER JOIN comercial.tipodocumento TD ON TD.id_tipodocumento = G.id_tipo_documento_guia
    INNER JOIN comercial.tipo_guia TG ON TG.id_tipo_guia = G.id_tipo_guia
    INNER JOIN comercial.cliente C
        ON  (G.ruccliente <> '' AND C.ruc = G.ruccliente)
        OR  (G.dni_cliente <> '' AND C.dni = G.dni_cliente)
    WHERE G.estado = 'A' AND G.tipo_transporte IS NOT NULL AND G.estado_declaracion = 'NO DECLARAR'
    ORDER BY G.fecha_hora
    LIMIT 5
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
    WHERE id_guia = %s
    """

    with get_connection() as cnx:
        with cnx.cursor() as cursor:
            cursor.execute(sql_header)
            lista_guias = []

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
                guia.dni_chofer = row[26]
                guia.chofer = row[27]
                guia.tipo_transporte = row[28]
                guia.peso = row[29]
                guia.codigo_motivo_traslado = row[30]
                guia.descripcion_motivo_traslado = row[31]
                guia.observaciones = row[32]

                cursor.execute(sql_detail, (guia.id_guia,))
                for deta in cursor.fetchall():
                    guia.detalle_guias.append(DetalleGuia(deta[2], deta[3], deta[4], 'NIU', deta[6]))
                lista_guias.append(guia)

    return _generate_lista(lista_guias)


def _generate_lista(guias):
    header_dics = []
    for guia in guias:
        codigo_pais = 'PE'
        header_dic = {}

        header_dic['id_venta'] = guia.id_guia
        header_dic['informacion_adicional'] = "Usuario:" + guia.cod_empleado + "|Caja: " + guia.punto_venta
        header_dic['serie_documento'] = '%s' % guia.serie_documento
        header_dic['numero_documento'] = int(guia.numero_documento)
        header_dic['fecha_de_emision'] = guia.fecha_guia.strftime('%Y-%m-%d')
        header_dic['hora_de_emision'] = guia.fecha_guia.strftime('%H:%M:%S')
        header_dic['codigo_tipo_documento'] = guia.codigo_tipo_documento

        datos_del_emisor = {}
        datos_del_emisor['codigo_pais'] = codigo_pais
        datos_del_emisor['ubigeo'] = '220101'
        datos_del_emisor['direccion'] = guia.direccion_emisor
        datos_del_emisor['correo_electronico'] = ''
        datos_del_emisor['telefono'] = guia.telefono_emisor
        datos_del_emisor['codigo_del_domicilio_fiscal'] = '0000'
        header_dic['datos_del_emisor'] = datos_del_emisor

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

        header_dic['observaciones'] = guia.observaciones
        header_dic['codigo_modo_transporte'] = '01' if guia.tipo_transporte == 'TRANSPORTE PUBLICO' else '02'
        header_dic['codigo_motivo_traslado'] = guia.codigo_motivo_traslado
        header_dic['descripcion_motivo_traslado'] = guia.descripcion_motivo_traslado
        header_dic['fecha_de_traslado'] = guia.fecha_traslado.strftime('%Y-%m-%d')
        header_dic['codigo_de_puerto'] = ''
        header_dic['indicador_de_transbordo'] = False
        header_dic['unidad_peso_total'] = 'KGM'
        header_dic['peso_total'] = str(guia.peso)
        header_dic['numero_de_bultos'] = guia.num_bultos
        header_dic['numero_de_contenedor'] = ''

        direccion_partida = {}
        direccion_partida['ubigeo'] = '220101'
        direccion_partida['direccion'] = guia.direccion_partida
        direccion_partida['codigo_del_domicilio_fiscal'] = '0000'
        header_dic['direccion_partida'] = direccion_partida

        direccion_llegada = {}
        direccion_llegada['ubigeo'] = '220101'
        direccion_llegada['direccion'] = guia.direccion_llegada
        direccion_llegada['codigo_del_domicilio_fiscal'] = '0000'
        header_dic['direccion_llegada'] = direccion_llegada

        if guia.tipo_transporte == 'TRANSPORTE PUBLICO':
            transportista = {}
            transportista['codigo_tipo_documento_identidad'] = '6'
            transportista['numero_documento'] = guia.ruc_transportista
            transportista['apellidos_y_nombres_o_razon_social'] = guia.transporte
            transportista['numero_mtc'] = f'X{guia.ruc_transportista}'
            header_dic['transportista'] = transportista
        else:
            chofer = {}
            chofer['codigo_tipo_documento_identidad'] = '1'
            chofer['numero_documento'] = guia.dni_chofer
            chofer['nombres'] = guia.chofer.split(',')[1]
            chofer['apellidos'] = guia.chofer.split(',')[0]
            chofer['numero_licencia'] = guia.num_licencia
            header_dic['chofer'] = chofer
            header_dic['numero_de_placa'] = guia.placa_vehiculo

        lista_items = []
        for deta in guia.detalle_guias:
            item = {}
            item['codigo_interno'] = deta.codigo_producto
            item['descripcion'] = deta.nombre_producto
            item['unidad_de_medida'] = 'NIU'
            item['cantidad'] = round(deta.cantidad, 2)
            lista_items.append(item)

        header_dic['items'] = lista_items
        header_dics.append(header_dic)

    return header_dics
