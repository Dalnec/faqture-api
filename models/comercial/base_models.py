class Venta:
    def __init__(self):
        self.serie_documento = None
        self.numero_documento = None
        self.fecha_venta = None
        self.nombre_cliente = None
        self.documento_cliente = None
        self.direccion_cliente = None
        self.codigo_cliente = None
        self.vendedor = None
        self.total_venta = None
        self.codigo_tipo_documento = None
        self.id_venta = None
        self.codigo_tipo_documento_identidad = None
        self.forma_pago = None
        self.punto_venta = None
        self.descuentos = None
        self.total_descuentos = None
        self.igv = None
        self.total_gratuito = None
        self.sumSubtotales = None
        self.numero_placa = None
        self.total_bolsa_plastica = 0
        self.codigo_condicion_de_pago = None
        self.detalle_ventas = []

    def __str__(self):
        return "{} - {} {}".format(self.codigo_tipo_documento, self.serie_documento, self.detalle_ventas)


class DetalleVenta:
    def __init__(self, codigo_producto, nombre_producto, cantidad, precio_producto,
                 unidad_medida, total_impuestos_bolsa_plastica,
                 desc_individual, desc_porcentaje, sub_total,
                 monto_total, igv, igv_descuento, descuento_total):
        self.codigo_producto = codigo_producto
        self.nombre_producto = nombre_producto
        self.cantidad = float(cantidad)
        self.precio_producto = float(precio_producto)
        self.unidad_medida = unidad_medida
        self.total_impuestos_bolsa_plastica = float(total_impuestos_bolsa_plastica)
        self.desc_individual = float(desc_individual)
        self.desc_porcentaje = float(desc_porcentaje)
        self.sub_total = float(sub_total)
        self.monto_total = float(monto_total)
        self.igv = float(igv)
        self.igv_descuento = float(igv_descuento) if igv_descuento else 0.0
        self.descuento_total = float(descuento_total)

    def __str__(self):
        return self.nombre_producto
