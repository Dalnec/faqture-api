import json
from flask import Flask, render_template, request, redirect, url_for, jsonify
from base.comercial.db import (
    check_connection, read_empresa_full, update_empresa,
    get_connection
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
