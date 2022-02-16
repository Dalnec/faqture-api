from base.comercial.db import __conectarse

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

def leer_db_anulados():
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
                ventas.estado_declaracion = 'PROCESADO' AND
                tipodocumento.codigo_sunat in ('01','03')      
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
    return lista_ventas_anulados