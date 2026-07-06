import os
import sys
import threading
import webbrowser
import pystray
from PIL import Image, ImageDraw
from logger import get_logger

log = get_logger()

TRAY_PORT = 5555


def _create_icon(color='green'):
    img = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if color == 'green':
        fill = (34, 197, 94, 255)
    else:
        fill = (239, 68, 68, 255)
    draw.ellipse([8, 8, 56, 56], fill=fill)
    draw.text((18, 16), 'F', fill=(255, 255, 255, 255))
    return img


def _open_dashboard(icon, item):
    webbrowser.open(f'http://127.0.0.1:{TRAY_PORT}')


def _on_exit(icon, item):
    icon.stop()
    os._exit(0)


def update_tray_icon(icon, connected):
    color = 'green' if connected else 'red'
    icon.icon = _create_icon(color)


def run_tray():
    from gui.dashboard import run_dashboard, set_status
    from base.comercial.db import check_connection

    icon = pystray.Icon(
        'Faqture',
        icon=_create_icon('red'),
        title='Faqture - Verificando...',
        menu=pystray.Menu(
            pystray.MenuItem('Abrir Dashboard', _open_dashboard, default=True),
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
                icon.title = f'Faqture - {status_text}'
            except Exception as e:
                set_status(db_ok=False, api_ok=False)
                update_tray_icon(icon, False)
                icon.title = 'Faqture - Error'
            import time
            time.sleep(30)

    threading.Thread(target=health_checker, daemon=True).start()
    threading.Thread(target=run_dashboard, kwargs={'port': TRAY_PORT}, daemon=True).start()

    log.info(f'[GUI] Dashboard en http://127.0.0.1:{TRAY_PORT}')
    icon.run()
