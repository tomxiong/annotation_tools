# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Additional hidden imports for tkinter and standard library modules
hidden_imports = [
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox', 
    'tkinter.font',
    'tkinter.colorchooser',
    'tkinter.scrolledtext',
    'PIL._tkinter_finder',
    'cv2',
    'numpy',
    'yaml',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    # Standard library modules that might be missed
    'logging.handlers',
    'logging.config',
    'json',
    'pathlib',
    'datetime',
    'dataclasses',
    'enum',
    'typing',
    'os',
    'sys',
    'threading',
    'subprocess',
    'shutil',
    'tempfile',
    'argparse'
]

# Data files to include
datas = [
    ('src', 'src'),
    ('config', 'config'),
    ('docs', 'docs'),
    ('logs', 'logs')
]

# Modules to exclude
excludes = [
    'matplotlib',
    'scipy',
    'pandas',
    'pytest',
    'unittest',
    'test_*.py',
    'tests'
]

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=['.'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PanoramicAnnotationTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None
)