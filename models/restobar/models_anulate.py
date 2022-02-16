from base.restobar.db import __conectarse

class Venta:
    id_venta = None
    fecha_venta = None
    codigo_tipo_proceso = None
    external_id = None
    motivo_anulacion = None

    def __str__(self):
        # ver para que sirve
        return "{}, {}".format(self.fecha_venta, self.codigo_tipo_proceso)


def r_leer_db_anulados():
    cnx = __conectarse()
    cursor = cnx.cursor()
    lista_ventas_anulados = []

    sql_header = """
            SELECT                 
                ventas.id_venta,
                ventas.fecha_hora,
                documento.codigo_sunat,              
                ventas.observaciones_declaracion,
                'Error en documento' as motivo_anulacion,
                ventas.codigo_cliente
            FROM
                gulash.ventas,
                gulash.documento
            WHERE
                documento.id_documento = ventas.id_documento AND
                ventas.estado = 'I' AND
                ventas.estado_declaracion_anulado = '' AND
                ventas.estado_declaracion = 'PROCESADO' AND
                documento.codigo_sunat in ('01','03') AND
                ventas.observaciones_declaracion != ''
            ORDER BY ventas.fecha_hora
        """
    cursor.execute(sql_header)

    for row in cursor.fetchall():
        venta = Venta()

        venta.id_venta = row[0]
        venta.fecha_venta = row[1]
        venta.codigo_tipo_proceso = row[2]
        venta.external_id = row[3]
        venta.motivo_anulacion = row[4]

        lista_ventas_anulados.append(venta)

    cursor.close()
    cnx.close()
    return lista_ventas_anulados