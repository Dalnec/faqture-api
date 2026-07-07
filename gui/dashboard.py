import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from base.comercial.db import (
    check_connection, read_empresa_full, update_empresa, get_connection,
    read_ventas_list, read_notas_credito_list, read_guias_list, read_anulados_list,
    update_venta_pgsql
)
from logger import get_logger

log = get_logger()

app = Flask(__name__, template_folder='templates')

_db_status = False
_api_status = False


def set_status(db_ok: bool, api_ok: bool):
    global _db_status, _api_status
    _db_status = db_ok
    _api_status = api_ok


@app.route('/')
def dashboard():
    empresa = read_empresa_full()
    doc_stats = _get_doc_stats()
    return render_template(
        'dashboard.html',
        db_status=_db_status,
        api_status=_api_status,
        empresa=empresa,
        stats=doc_stats,
    )


@app.route('/empresa', methods=['GET'])
def empresa_page():
    empresa = read_empresa_full()
    return render_template('empresa.html', empresa=empresa, saved=False)


@app.route('/empresa', methods=['POST'])
def empresa_save():
    token = request.form.get('efactur_empresa', '').strip()
    url = request.form.get('efactur_url', '').strip()
    if not token or not url:
        return render_template('empresa.html', empresa=(token, url, '', ''), saved=False, error='Token y URL son obligatorios')
    try:
        update_empresa(token, url)
        return render_template('empresa.html', empresa=(token, url, '', ''), saved=True)
    except Exception as e:
        log.error(f'[DASHBOARD] Error guardando empresa: {e}')
        return render_template('empresa.html', empresa=(token, url, '', ''), saved=False, error=str(e))


@app.route('/documents')
def documents_page():
    tab = request.args.get('tab', 'ventas')
    estado = request.args.get('estado', None)
    serie = request.args.get('serie', None)
    fecha = request.args.get('fecha', None)
    return render_template(
        'documents.html',
        tab=tab,
        estado=estado,
        serie=serie,
        fecha=fecha,
    )


@app.route('/api/documents')
def api_documents():
    doc_type = request.args.get('type', 'ventas')
    estado = request.args.get('estado', None)
    serie = request.args.get('serie', None)
    fecha = request.args.get('fecha', None)
    try:
        if doc_type == 'ventas':
            docs = read_ventas_list(estado=estado, serie=serie, fecha=fecha)
        elif doc_type == 'notas_credito':
            docs = read_notas_credito_list(estado=estado)
        elif doc_type == 'guias':
            docs = read_guias_list(estado=estado)
        elif doc_type == 'anulados':
            docs = read_anulados_list()
        else:
            docs = []
        for doc in docs:
            for k, v in doc.items():
                if hasattr(v, 'isoformat'):
                    doc[k] = v.isoformat()
                elif isinstance(v, (int, float, str, bool, type(None))):
                    pass
                else:
                    doc[k] = str(v)
        return jsonify({'documents': docs, 'count': len(docs)})
    except Exception as e:
        log.error(f'[DASHBOARD] Error listando documentos: {e}')
        return jsonify({'documents': [], 'count': 0, 'error': str(e)})


@app.route('/api/documents/<int:doc_id>/status', methods=['PUT'])
def api_update_status(doc_id):
    data = request.get_json()
    nuevo_estado = data.get('estado')
    if not nuevo_estado:
        return jsonify({'error': 'Estado requerido'}), 400
    try:
        update_venta_pgsql(nuevo_estado, '', doc_id)
        return jsonify({'success': True})
    except Exception as e:
        log.error(f'[DASHBOARD] Error actualizando estado: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def api_status():
    return jsonify({
        'db': _db_status,
        'api': _api_status,
    })


def _get_doc_stats():
    try:
        with get_connection() as cnx:
            with cnx.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        estado_declaracion,
                        COUNT(*) as total
                    FROM comercial.ventas
                    GROUP BY estado_declaracion
                """)
                rows = cursor.fetchall()
                stats = {row[0]: row[1] for row in rows}
                stats['total'] = sum(stats.values())
                return stats
    except Exception as e:
        log.warning(f'[DASHBOARD] Error consultando documentos: {e}')
        return {'total': 0}


def run_dashboard(host='127.0.0.1', port=5555):
    app.run(host=host, port=port, debug=False, use_reloader=False)
