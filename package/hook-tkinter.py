# PyInstaller hook for tkinter.ttk
# This ensures that tkinter.ttk is properly included in the package

from PyInstaller.utils.hooks import collect_submodules

# Collect all tkinter submodules
hiddenimports = collect_submodules('tkinter')

# Add specific tkinter components that might be missed
hiddenimports.extend([
    'tkinter.ttk',
    'tkinter.filedialog', 
    'tkinter.messagebox',
    'tkinter.font',
    'tkinter.colorchooser',
    'tkinter.scrolledtext',
    'tkinter.tix'
])