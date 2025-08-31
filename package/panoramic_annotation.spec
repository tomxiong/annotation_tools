# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 分析主程序需要的隐藏导入
hidden_imports = [
    'PIL._tkinter_finder',
    'cv2',
    'numpy',
    'yaml',
    'PIL.Image',
    'PIL.ImageTk', 
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'tkinter.colorchooser'
]

# 收集数据文件
datas = [
    ('src', 'src'),
    ('config', 'config'),
    ('docs', 'docs'),
    ('logs', 'logs')
]

# 排除不需要的模块
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
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

# 创建可执行文件
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='全景图像标注工具',
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
    entitlements_file=None,
    icon=None,
    version='version.txt' if os.path.exists('version.txt') else None
)

# 如果需要创建目录版本而不是单文件版本，取消下面的注释
"""
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='全景图像标注工具'
)
"""