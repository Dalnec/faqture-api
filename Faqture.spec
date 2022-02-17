# -*- mode: python ; coding: utf-8 -*-

block_cipher = None
added_files = [( 'models/*.*', 'kulami' ),
         ( 'base/*.*', 'base' ),
         ( 'api/*.*', 'pseapi' )         
         ]

a = Analysis(['main.py'],
             pathex=['D:\\TSI\\Faqture_Code\\faqture-api'],
             binaries=[],
             datas=added_files,
             hiddenimports=['google-api-python-client'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='Faqture',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True, 
          icon='')
