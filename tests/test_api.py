import json
import pytest
from unittest.mock import patch, MagicMock


class TestApiClientHandleSend:
    """Test ApiClient._handle_send with mocked dependencies."""

    def _make_client(self):
        with patch('api.api.read_empresa_pgsql', return_value=('test-token', 'http://test.api')):
            from api.api import ApiClient
            return ApiClient()

    def test_send_success_calls_update_success(self):
        client = self._make_client()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({
            'success': True,
            'data': {
                'cod_sale': 'F001-123',
                'filename': 'file.pdf',
                'state': 'ACEPTADO',
                'external_id': 'ext-123'
            }
        }).encode()

        items = [{'id_venta': 1, 'serie_documento': 'F001', 'numero_documento': '123'}]
        update_success = MagicMock()
        update_error = MagicMock()

        with patch.object(client, '_request', return_value=(mock_response, 50)):
            client._handle_send(
                items=items,
                process_name='TEST',
                get_id=lambda v: v.get('id_venta', '?'),
                get_ref=lambda v: f"{v.get('serie_documento')}-{v.get('numero_documento')}",
                method='POST',
                update_success=update_success,
                update_error=update_error,
            )

        update_success.assert_called_once()
        update_error.assert_not_called()

    def test_send_error_calls_update_error(self):
        client = self._make_client()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.content = json.dumps({
            'success': False,
            'message': 'Validation error'
        }).encode()

        items = [{'id_venta': 1, 'serie_documento': 'F001', 'numero_documento': '123'}]
        update_success = MagicMock()
        update_error = MagicMock()

        with patch.object(client, '_request', return_value=(mock_response, 50)):
            client._handle_send(
                items=items,
                process_name='TEST',
                get_id=lambda v: v.get('id_venta', '?'),
                get_ref=lambda v: '',
                method='POST',
                update_success=update_success,
                update_error=update_error,
            )

        update_success.assert_not_called()
        update_error.assert_called_once()

    def test_send_connection_error_logs_warning(self):
        import requests as req_lib
        client = self._make_client()

        items = [{'id_venta': 1, 'serie_documento': 'F001', 'numero_documento': '123'}]
        update_success = MagicMock()
        update_error = MagicMock()

        with patch.object(client, '_request', side_effect=req_lib.ConnectionError('fail')):
            client._handle_send(
                items=items,
                process_name='TEST',
                get_id=lambda v: v.get('id_venta', '?'),
                get_ref=lambda v: '',
                method='POST',
                update_success=update_success,
                update_error=update_error,
            )

        update_success.assert_not_called()
        update_error.assert_not_called()

    def test_send_empty_items_does_nothing(self):
        client = self._make_client()
        update_success = MagicMock()
        update_error = MagicMock()

        client._handle_send(
            items=[],
            process_name='TEST',
            get_id=lambda v: v.get('id_venta'),
            get_ref=lambda v: '',
            method='POST',
            update_success=update_success,
            update_error=update_error,
        )

        update_success.assert_not_called()
        update_error.assert_not_called()
