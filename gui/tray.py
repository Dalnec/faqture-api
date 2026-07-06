import os
import sys
import threading
import webbrowser
import pystray
from PIL import Image, ImageDraw
from logger import get_logger

log = get_logger()

TRAY_PORT = 5555
_web_running = False
_web_thread = None
_web_server = None


def _create_icon(color='green'):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if color == 'green':
        fill = (34, 197, 94, 255)
    elif color == 'yellow':
        fill = (234, 179, 8, 255)
    else:
        fill = (239, 68, 68, 255)
    draw.ellipse([8, 8, 56, 56], fill=fill)
    draw.text((18, 16), 'F', fill=(255, 255, 255, 255))
    return img


def _open_dashboard(icon, item):
    webbrowser.open(f'http://127.0.0.1:{TRAY_PORT}')


def _show_status(icon, item):
    from base.comercial.db import check_connection
    icon.icon = _create_icon('yellow')
    icon.title = 'Faqture - Verificando conexion...'
    try:
        ok = check_connection()
        if ok:
            icon.icon = _create_icon('green')
            icon.title = 'Faqture - DB: Conectado'
        else:
            icon.icon = _create_icon('red')
            icon.title = 'Faqture - DB: Desconectado'
    except Exception:
        icon.icon = _create_icon('red')
        icon.title = 'Faqture - DB: Error de conexion'
    import time
    time.sleep(5)


def _start_web(icon, item):
    global _web_running, _web_thread, _web_server
    if _web_running:
        return
    try:
        from gui.dashboard import app
        from werkzeug.serving import make_server
        _web_running = True
        _web_server = make_server('127.0.0.1', TRAY_PORT, app)
        _web_thread = threading.Thread(target=_web_server.serve_forever, daemon=True)
        _web_thread.start()
        icon.title = f'Faqture - Servidor activo en :{TRAY_PORT}'
        log.info(f'[GUI] Dashboard iniciado en http://127.0.0.1:{TRAY_PORT}')
    except Exception as e:
        _web_running = False
        log.error(f'[GUI] Error iniciando servidor: {e}')


def _stop_web(icon, item):
    global _web_running, _web_server
    if not _web_running or _web_server is None:
        return
    try:
        _web_server.shutdown()
        _web_running = False
        _web_server = None
        icon.title = 'Faqture - Servidor detenido'
        log.info('[GUI] Dashboard detenido')
    except Exception as e:
        log.error(f'[GUI] Error deteniendo servidor: {e}')


def _on_exit(icon, item):
    global _web_running, _web_server
    if _web_running and _web_server:
        try:
            _web_server.shutdown()
        except Exception:
            pass
    icon.stop()
    os._exit(0)


def update_tray_icon(icon, connected):
    color = 'green' if connected else 'red'
    icon.icon = _create_icon(color)


def run_tray():
    from gui.dashboard import set_status
    from base.comercial.db import check_connection

    def _is_web_running(item):
        return _web_running

    def _is_web_stopped(item):
        return not _web_running

    icon = pystray.Icon(
        'Faqture',
        icon=_create_icon('red'),
        title='Faqture - Verificando...',
        menu=pystray.Menu(
            pystray.MenuItem('Estado de Conexion', _show_status, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Abrir Dashboard', _open_dashboard),
            pystray.MenuItem('Iniciar Servidor Web', _start_web, visible=_is_web_stopped),
            pystray.MenuItem('Detener Servidor Web', _stop_web, visible=_is_web_running),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('Salir', _on_exit),
        ),
    )

    def health_checker():
        while True:
            try:
                ok = check_connection()
                set_status(db_ok=ok, api_ok=ok)
                update_tray_icon(icon, ok)
                status_text = 'Conectado' if ok else 'Desconectado'
                icon.title = f'Faqture - DB: {status_text}'
            except Exception:
                set_status(db_ok=False, api_ok=False)
                update_tray_icon(icon, False)
                icon.title = 'Faqture - DB: Error'
            import time
            time.sleep(30)

    threading.Thread(target=health_checker, daemon=True).start()

    log.info('[GUI] Tray icon iniciado. Use el menu para iniciar el servidor web.')
    icon.run()
