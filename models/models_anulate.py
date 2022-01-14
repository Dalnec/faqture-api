from base.db import __conectarse

class Venta:
    id_venta = None
    fecha_venta = None
    codigo_tipo_proceso = None
    external_id = None
    motivo_anulacion = None
    serie = None
    numero = None

    def __str__(self):
        return "{}, {}".format(self.fecha_venta, self.codigo_tipo_proceso)

def leer_db_fanulados():
    cnx = __conectarse()
    cursor = cnx.cursor()
    lista_ventas_anulados = []

    sql_header = """
            SELECT                 
                ventas.id_venta,
                ventas.fecha_hora,
                tipodocumento.codigo_sunat,              
                ventas.observaciones_declaracion,
                ventas.motivo_anulacion,
                ventas.codigo_cliente,
                ventas.external_id,
                ventas.num_serie,
                ventas.num_documento
            FROM
                comercial.ventas,
                comercial. tipodocumento
            WHERE
                ventas.id_tipodocumento = tipodocumento.id_tipodocumento AND
                ventas.estado_declaracion_anulado = 'PENDIENTE' AND
                ventas.codigo_cliente = 'ANULADO' AND
                ventas.estado_declaracion = 'ANULADO' AND
                tipodocumento.codigo_sunat = '01' AND
                ventas.external_id != ''                
            ORDER BY ventas.fecha_hora
        """   
    cursor.execute(sql_header)

    for row in cursor.fetchall():
        venta = Venta()
        
        venta.id_venta = row[0]
        venta.fecha_venta = row[1]
        venta.codigo_tipo_proceso = row[2]
        venta.external_id = row[6]
        venta.motivo_anulacion = row[4]
        venta.serie = row[7]
        venta.numero = row[8]

        lista_ventas_anulados.append(venta)
    
    cursor.close()
    cnx.close()
    return _generate_lista_anulados(lista_ventas_anulados)

def leer_db_banulados():
    cnx = __conectarse()
    cursor = cnx.cursor()
    lista_ventas_anulados = []

    sql_header = """
            SELECT                 
                ventas.id_venta,
                ventas.fecha_hora,
                tipodocumento.codigo_sunat,              
                ventas.estado_declaracion_anulado,
                ventas.motivo_anulacion,
                ventas.codigo_cliente,
                ventas.external_id,
                ventas.num_serie,
                ventas.num_documento
            FROM
                comercial.ventas,
                comercial. tipodocumento
            WHERE
                ventas.id_tipodocumento = tipodocumento.id_tipodocumento AND
                ventas.codigo_cliente = 'ANULADO' AND
                ventas.estado_declaracion_anulado = 'PENDIENTE' AND
                ventas.estado_declaracion = 'ANULADO' AND
                tipodocumento.codigo_sunat = '03' AND
                ventas.external_id != ''
            ORDER BY ventas.fecha_hora
        """   
    cursor.execute(sql_header)

    for row in cursor.fetchall():
        venta = Venta()
        
        venta.id_venta = row[0]
        venta.fecha_venta = row[1]
        venta.codigo_tipo_proceso = row[2]
        venta.external_id = row[6]
        venta.motivo_anulacion = row[4]
        venta.serie = row[7]
        venta.numero = row[8]

        lista_ventas_anulados.append(venta)
    
    cursor.close()
    cnx.close()
    return _generate_lista_anulados(lista_ventas_anulados)

def _generate_lista_anulados(ventas_anulados):
    
    header_dics = []
    for venta in ventas_anulados:
        header_dic = {}
        header_dic['id_venta'] = int(venta.id_venta)
        header_dic['documento'] = "{}-{}".format(venta.serie, venta.numero)
        # Creamos el cuerpo del pse
        header_dic['fecha_de_emision_de_documentos'] = venta.fecha_venta.strftime('%Y-%m-%d')
        if int(venta.codigo_tipo_proceso) == 3:
            header_dic['codigo_tipo_proceso'] = "3"
        # documentos verificar [] no los estoy incluyendo
        docs = []
        documents = {}
        documents['external_id'] = venta.external_id
        documents['motivo_anulacion'] = venta.motivo_anulacion
        docs.append(documents)

        header_dic['documentos'] = docs

        header_dics.append(header_dic)
    return header_dics