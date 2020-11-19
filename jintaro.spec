block_cipher = None

a = Analysis(['jintaro.spec.py'],
             binaries=[],
             datas=[],
             hiddenimports=[
                 "pyexcel_io.readers.csv_in_file",
                 "pyexcel_io.readers.csv_in_memory",
                 "pyexcel_io.readers.csv_content",
                 "pyexcel_io.readers.csvz",
                 "pyexcel_io.writers.csv_in_file",
                 "pyexcel_io.writers.csv_in_memory",
                 "pyexcel_io.writers.csvz_writer",
                 "pyexcel_io.database.importers.django",
                 "pyexcel_io.database.importers.sqlalchemy",
                 "pyexcel_io.database.exporters.django",
                 "pyexcel_io.database.exporters.sqlalchemy",
                 "pyexcel_xlsx",
                 "pyexcel_xlsx.xlsxr",
                 "pyexcel_xlsx.xlsxw",
                 "pyexcel_odsr",
                 "pyexcel_odsr.odsr",
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas, [],
          name='jintaro',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True)