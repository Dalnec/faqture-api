# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

added_files = [
    ('models', 'models'),
    ('base', 'base'),
    ('api', 'api'),
]

a = Analysis(
    ['main.py'],
    pathex=[os.getcwd()],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        'psycopg2',
        'psycopg2._psycopg',
        'configparser',
        'logging.handlers',
        'json',
        'google-api-python-client',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='faqture',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon='logo.ico',
)
