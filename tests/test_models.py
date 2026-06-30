import pytest
from datetime import datetime
from models.comercial.base_models import Venta, DetalleVenta


def _make_venta(**kwargs):
    """Helper to create a Venta with defaults."""
    v = Venta()
    v.id_venta = kwargs.get('id_venta', 1)
    v.serie_documento = kwargs.get('serie_documento', 'F001')
    v.numero_documento = kwargs.get('numero_documento', 100)
    v.fecha_venta = kwargs.get('fecha_venta', datetime(2025, 6, 15, 10, 30, 0))
    v.codigo_tipo_documento = kwargs.get('codigo_tipo_documento', '01')
    v.codigo_tipo_documento_identidad = kwargs.get('codigo_tipo_documento_identidad', '6')
    v.documento_cliente = kwargs.get('documento_cliente', '20123456789')
    v.nombre_cliente = kwargs.get('nombre_cliente', 'Test Client')
    v.direccion_cliente = kwargs.get('direccion_cliente', 'Av. Test 123')
    v.total_venta = kwargs.get('total_venta', 100.0)
    v.vendedor = kwargs.get('vendedor', '1')
    v.forma_pago = kwargs.get('forma_pago', 'CONTADO')
    v.punto_venta = kwargs.get('punto_venta', 'CAJA01')
    v.descuentos = kwargs.get('descuentos', 0.0)
    v.total_descuentos = kwargs.get('total_descuentos', 0)
    v.igv = kwargs.get('igv', 18.0)
    v.total_gratuito = kwargs.get('total_gratuito', 0)
    v.sumSubtotales = kwargs.get('sumSubtotales', 100.0)
    v.numero_placa = kwargs.get('numero_placa', None)
    v.total_bolsa_plastica = kwargs.get('total_bolsa_plastica', 0)
    v.codigo_condicion_de_pago = kwargs.get('codigo_condicion_de_pago', 1)
    v.detalle_ventas = kwargs.get('detalle_ventas', [])
    return v


def _make_detalle(**kwargs):
    return DetalleVenta(
        codigo_producto=kwargs.get('codigo_producto', 'P001'),
        nombre_producto=kwargs.get('nombre_producto', 'Producto Test'),
        cantidad=kwargs.get('cantidad', 2),
        precio_producto=kwargs.get('precio_producto', 50.0),
        unidad_medida=kwargs.get('unidad_medida', 'UND'),
        total_impuestos_bolsa_plastica=kwargs.get('total_impuestos_bolsa_plastica', 0),
        desc_individual=kwargs.get('desc_individual', 0),
        desc_porcentaje=kwargs.get('desc_porcentaje', 0),
        sub_total=kwargs.get('sub_total', 100.0),
        monto_total=kwargs.get('monto_total', 100.0),
        igv=kwargs.get('igv', 18.0),
        igv_descuento=kwargs.get('igv_descuento', 0),
        descuento_total=kwargs.get('descuento_total', 0),
    )


class TestGenerateLista:
    """Test _generate_lista business logic from ventas.py."""

    def _generate(self, ventas, **kwargs):
        from models.comercial.ventas import _generate_lista
        return _generate_lista(
            ventas,
            descuento_codigo=kwargs.get('descuento_codigo', '01'),
            descuento_desc=kwargs.get('descuento_desc', 'Test discount'),
            redondear_cantidad=kwargs.get('redondear_cantidad', False),
        )

    def test_basic_venta_structure(self):
        detalle = _make_detalle()
        venta = _make_venta(detalle_ventas=[detalle])
        result = self._generate([venta])

        assert len(result) == 1
        item = result[0]
        assert item['id_venta'] == 1
        assert item['serie_documento'] == 'F001'
        assert item['numero_documento'] == 100
        assert item['codigo_tipo_moneda'] == 'PEN'
        assert item['codigo_tipo_operacion'] == '0101'

    def test_cliente_data(self):
        detalle = _make_detalle()
        venta = _make_venta(detalle_ventas=[detalle])
        result = self._generate([venta])

        cliente = result[0]['datos_del_cliente_o_receptor']
        assert cliente['numero_documento'] == '20123456789'
        assert cliente['apellidos_y_nombres_o_razon_social'] == 'Test Client'
        assert cliente['codigo_pais'] == 'PE'

    def test_totales_con_igv(self):
        detalle = _make_detalle(igv=18.0, monto_total=118.0)
        venta = _make_venta(igv=18.0, total_venta=100.0, detalle_ventas=[detalle])
        result = self._generate([venta])

        totales = result[0]['totales']
        assert totales['total_igv'] == 18.0
        assert totales['total_venta'] == 118.0
        assert totales['total_operaciones_gravadas'] == 100.0
        assert totales['total_operaciones_exoneradas'] == 0.0

    def test_totales_sin_igv(self):
        detalle = _make_detalle(igv=0, monto_total=100.0)
        venta = _make_venta(igv=0, total_venta=100.0, detalle_ventas=[detalle])
        result = self._generate([venta])

        totales = result[0]['totales']
        assert totales['total_igv'] == 0.0
        assert totales['total_operaciones_exoneradas'] == 100.0
        assert totales['total_operaciones_gravadas'] == 0.0

    def test_condicion_credito(self):
        detalle = _make_detalle()
        venta = _make_venta(codigo_condicion_de_pago=2, detalle_ventas=[detalle])
        result = self._generate([venta])

        assert result[0]['codigo_condicion_de_pago'] == '02'
        assert 'cuotas' in result[0]
        assert len(result[0]['cuotas']) == 1

    def test_condicion_contado_sin_cuotas(self):
        detalle = _make_detalle()
        venta = _make_venta(codigo_condicion_de_pago=1, detalle_ventas=[detalle])
        result = self._generate([venta])

        assert result[0]['codigo_condicion_de_pago'] == '01'
        assert 'cuotas' not in result[0]

    def test_descuento_global(self):
        detalle = _make_detalle()
        venta = _make_venta(
            descuentos=10.0,
            sumSubtotales=100.0,
            detalle_ventas=[detalle],
        )
        result = self._generate([venta], descuento_codigo='03', descuento_desc='Global')

        assert 'descuentos' in result[0]
        desc = result[0]['descuentos'][0]
        assert desc['codigo'] == '03'
        assert desc['monto'] == 10.0
        assert desc['base'] == 100.0

    def test_placa_genera_datos_adicionales(self):
        detalle = _make_detalle()
        venta = _make_venta(numero_placa='ABC-123', detalle_ventas=[detalle])
        result = self._generate([venta])

        item = result[0]['items'][0]
        assert 'datos_adicionales' in item
        assert item['datos_adicionales'][0]['valor'] == 'ABC-123'

    def test_redondear_cantidad(self):
        detalle = _make_detalle(cantidad=2.567)
        venta = _make_venta(detalle_ventas=[detalle])
        result = self._generate([venta], redondear_cantidad=True)

        assert result[0]['items'][0]['cantidad'] == 2.57

    def test_no_redondear_cantidad_por_defecto(self):
        detalle = _make_detalle(cantidad=2.567)
        venta = _make_venta(detalle_ventas=[detalle])
        result = self._generate([venta], redondear_cantidad=False)

        assert result[0]['items'][0]['cantidad'] == 2.567

    def test_multiple_ventas(self):
        v1 = _make_venta(id_venta=1, detalle_ventas=[_make_detalle()])
        v2 = _make_venta(id_venta=2, detalle_ventas=[_make_detalle()])
        result = self._generate([v1, v2])

        assert len(result) == 2
        assert result[0]['id_venta'] == 1
        assert result[1]['id_venta'] == 2


class TestDetalleItems:
    """Test _detalle_items_* functions."""

    def test_exonerada(self):
        from models.comercial.ventas import _detalle_items_exonerada
        deta = _make_detalle(igv=0, precio_producto=50.0, monto_total=100.0, descuento_total=0)
        item = {}
        result = _detalle_items_exonerada(deta, item)

        assert result['codigo_tipo_afectacion_igv'] == '20'
        assert result['total_igv'] == 0
        assert result['total_item'] == 100.0

    def test_gravado(self):
        from models.comercial.ventas import _detalle_items_gravado
        deta = _make_detalle(igv=18.0, precio_producto=59.0, monto_total=118.0)
        item = {}
        result = _detalle_items_gravado(deta, item)

        assert result['codigo_tipo_afectacion_igv'] == '10'
        assert result['total_item'] == 118.0
        assert result['total_igv'] > 0

    def test_gratuito(self):
        from models.comercial.ventas import _detalle_items_gratuito
        deta = _make_detalle(igv=0, precio_producto=50.0, monto_total=0)
        item = {}
        result = _detalle_items_gratuito(deta, item)

        assert result['codigo_tipo_precio'] == '02'
        assert result['total_item'] == 0
