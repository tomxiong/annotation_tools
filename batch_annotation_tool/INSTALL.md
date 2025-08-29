# Installation Guide

This document provides detailed installation and environment setup instructions for the Panoramic Image Annotation Tool.

## System Requirements

- Python 3.8 or higher
- Operating System: Windows 10/11, macOS, Linux
- At least 4GB RAM (8GB or more recommended)
- Display resolution: 1600x1100 minimum

## Installation Steps

### 1. Clone or Download Project

```bash
git clone https://github.com/your-username/batch_annotation_tool.git
cd batch_annotation_tool
```

### 2. Create and Activate Virtual Environment

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -e .
```

This will install all required dependencies for the project.

### 4. Verify Installation

```bash
# Run verification test
python tools/testing/final_verification.py

# Run unit tests
python -m pytest tests/unit
```

## Running the Application

### Launch GUI Application

```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Launch the main GUI
python src/ui/panoramic_annotation_gui.py
```

### Alternative Launch Methods

```bash
# Using launcher scripts
python tools/launchers/start_gui.py

# Or platform-specific scripts
tools\launchers\start_gui.bat    # Windows
./tools/launchers/start_gui.sh   # Linux/Mac
```

## Project Structure After Installation

After successful installation, your project structure should look like:

```
batch_annotation_tool/
├── src/                    # Core source code
│   ├── ui/
│   │   └── panoramic_annotation_gui.py  # Main application
│   ├── services/           # Core services
│   ├── models/             # Data models
│   └── core/               # Utilities
├── tools/                  # Development tools
├── docs/                   # Documentation
├── tests/                  # Unit tests
├── venv/                   # Virtual environment
├── README.md               # Project overview
└── INSTALL.md              # This file
```

## Troubleshooting

### Import Errors

If you encounter `ModuleNotFoundError` or `ImportError`:

1. **Ensure virtual environment is activated**
   ```bash
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

2. **Reinstall dependencies**
   ```bash
   pip install -e .
   ```

3. **Verify you're in the correct directory**
   - Should be in the `batch_annotation_tool` directory
   - Check that `src/ui/panoramic_annotation_gui.py` exists

### GUI Won't Launch

If the GUI doesn't start:

1. **Check Python version**
   ```bash
   python --version  # Should be 3.8+
   ```

2. **Test tkinter installation**
   ```bash
   python -c "import tkinter; print('tkinter works')"
   ```

3. **Run verification script**
   ```bash
   python tools/testing/final_verification.py
   ```

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Clean reinstall
pip uninstall batch-annotation-tool
pip install -e . --upgrade --force-reinstall
```

### File Path Issues

If you encounter path-related errors:

1. **Always run from project root**
   - Ensure you're in `batch_annotation_tool/` directory
   - Use absolute paths: `python src/ui/panoramic_annotation_gui.py`

2. **Check file permissions** (Linux/Mac)
   ```bash
   chmod +x tools/launchers/*.sh
   ```

### Performance Issues

For better performance:

1. **Close other applications** to free up memory
2. **Use SSD storage** for image directories if possible
3. **Ensure sufficient disk space** for annotation files

## Verification Checklist

After installation, verify these components:

- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list` shows `batch-annotation-tool`)
- [ ] Main GUI file exists: `src/ui/panoramic_annotation_gui.py`
- [ ] Can import core modules: `python -c "from ui.panoramic_annotation_gui import PanoramicAnnotationGUI"`
- [ ] GUI launches without errors
- [ ] All essential directories present: `src/`, `tools/`, `docs/`, `tests/`

## Getting Help

If you continue to experience issues:

1. **Check documentation** in `docs/` directory
2. **Review cleanup reports** for recent changes
3. **Run diagnostic tools** in `tools/testing/`
4. **Check archived files** in `archive/` if needed

## Uninstall

To remove the application:

1. **Deactivate virtual environment**
   ```bash
   deactivate
   ```

2. **Remove project directory**
   ```bash
   # Backup any important data first
   rm -rf batch_annotation_tool/  # Linux/Mac
   # or delete folder manually on Windows
   ```

Note: The project structure has been recently cleaned and organized. Previous installation methods may no longer apply.