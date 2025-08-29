# GUI Environment Setup and Testing Guide

This guide provides comprehensive instructions for setting up and testing the GUI environment for the Panoramic Image Annotation Tool.

## Quick Start

### Prerequisites Check
- Python 3.8 or higher installed
- Windows 10/11 or Linux/macOS
- At least 500MB free disk space

### 1. Navigate to Project Directory
```bash
cd d:\dev\annotation_tools\batch_annotation_tool
```

### 2. Quick Environment Validation
```bash
python quick_env_check.py
```
This script performs basic validation of your environment setup.

### 3. Launch GUI (Recommended Methods)

#### Method A: Automated Startup (Recommended)
**Windows:**
```cmd
start_gui.bat
```
**Linux/macOS:**
```bash
./start_gui.sh
```

#### Method B: Manual Activation
**Windows:**
```cmd
venv\Scripts\activate
python start_gui.py
```
**Linux/macOS:**
```bash
source venv/bin/activate
python start_gui.py
```

## Comprehensive Testing

### Environment Structure Test
Run the comprehensive environment tester:
```bash
python test_gui_environment_setup.py
```

This script tests:
- Virtual environment structure
- Python version compatibility (3.8+)
- Package installations
- Module import capabilities
- GUI launch methods
- Platform-specific startup scripts

### Launch Method Testing
Test all available GUI launch methods:
```bash
python test_gui_launch_methods.py
```

This script validates:
- Python launcher scripts
- Batch/shell startup scripts  
- Module import capabilities
- Dependency availability
- Provides launch recommendations

## Directory Structure Validation

Your `batch_annotation_tool` directory should contain:

```
batch_annotation_tool/
├── venv/                          # Virtual environment (REQUIRED)
│   ├── Scripts/ (Windows)         # Python executables
│   ├── bin/ (Linux/macOS)         # Python executables  
│   └── Lib/                       # Installed packages
├── src/                           # Source code (REQUIRED)
│   └── ui/                        # GUI modules
│       ├── panoramic_annotation_gui.py
│       └── [other GUI modules]
├── start_gui.py                   # Primary launcher (REQUIRED)
├── start_gui.bat/.sh             # Automated startup scripts
├── launch_gui.py                  # Enhanced launcher
├── quick_env_check.py            # Environment validator
├── test_gui_environment_setup.py # Comprehensive tester
└── test_gui_launch_methods.py    # Launch method tester
```

## Environment Setup Process

### Step 1: Virtual Environment Creation
If `venv` directory doesn't exist:

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Dependency Installation
```bash
pip install --upgrade pip
pip install -e .
```

### Step 3: Environment Validation
```bash
python quick_env_check.py
```

### Step 4: GUI Launch Test
```bash
python start_gui.py
```

## Troubleshooting Common Issues

### Issue 1: Virtual Environment Not Found
**Symptoms:** `venv` directory missing
**Solution:**
```bash
python -m venv venv
# Then activate and install dependencies
```

### Issue 2: Import Errors
**Symptoms:** `ImportError: No module named 'ui.panoramic_annotation_gui'`
**Solutions:**
1. Ensure you're in the `batch_annotation_tool` directory
2. Check that `src/ui/` directory exists
3. Verify `src` is in Python path

### Issue 3: Missing Dependencies
**Symptoms:** `ImportError: No module named 'PIL'` or similar
**Solution:**
```bash
# Activate environment first
pip install -e .
```

### Issue 4: GUI Won't Launch
**Symptoms:** GUI window doesn't appear
**Troubleshooting:**
1. Run `python test_gui_launch_methods.py`
2. Check console for error messages
3. Verify tkinter installation: `python -c "import tkinter"`

### Issue 5: Permission Errors (Linux/macOS)
**Symptoms:** "Permission denied" when running `.sh` scripts
**Solution:**
```bash
chmod +x start_gui.sh
chmod +x run_*.sh
```

## Testing Checklist

### Pre-Launch Checklist
- [ ] In correct directory (`batch_annotation_tool`)
- [ ] Virtual environment exists (`venv/` directory)
- [ ] Python executable available
- [ ] Source code directory exists (`src/`)
- [ ] Launcher scripts present

### Environment Validation Checklist
- [ ] Python version 3.8+ 
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip list` shows batch-annotation-tool)
- [ ] GUI modules importable
- [ ] tkinter available

### Launch Method Checklist
- [ ] `start_gui.py` works
- [ ] Platform startup script works (`.bat`/`.sh`)
- [ ] Alternative launchers work
- [ ] GUI window appears without errors

## Advanced Testing

### Memory and Performance Testing
Monitor resource usage during GUI operation:
```bash
# Run GUI and monitor
python start_gui.py
# Check memory usage in Task Manager (Windows) or htop (Linux)
```

### Cross-Platform Testing
If you have access to multiple platforms:
1. Test on Windows using `.bat` scripts
2. Test on Linux/macOS using `.sh` scripts
3. Verify Python launcher works on all platforms

### Integration Testing
Test with actual image data:
1. Prepare test images in supported formats
2. Launch GUI
3. Load test images
4. Verify annotation functionality

## Recovery Procedures

### Complete Environment Reset
If everything fails, use the generated recovery script:

**Windows:**
```cmd
recover_environment.bat
```

**Linux/macOS:**
```bash
./recover_environment.sh
```

Or manually:
```bash
# Remove existing environment
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Create fresh environment
python -m venv venv
# Activate and install
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
pip install -e .
```

### Selective Fixes

#### Fix 1: Reinstall Dependencies Only
```bash
# Activate environment
pip install --upgrade pip
pip install -e . --force-reinstall
```

#### Fix 2: Reset Python Path
```bash
# In Python, verify path setup
python -c "import sys; print('\n'.join(sys.path))"
```

## Validation Scripts Output

### quick_env_check.py Expected Output
```
🔍 Quick GUI Environment Check
========================================
📁 Current directory: D:\dev\annotation_tools\batch_annotation_tool
✅ Found: start_gui.py
✅ Found: venv
✅ Found: src
✅ Virtual environment Python: venv\Scripts\python.exe

🧪 Testing module imports...
✅ GUI module import successful
✅ tkinter (GUI framework) available
✅ PIL (image processing) available

🎉 Environment check passed!
```

### test_gui_environment_setup.py Expected Output
```
============================================================
                  ENVIRONMENT STRUCTURE VALIDATION
============================================================
✓ PASS Project root directory
✓ PASS Virtual environment directory
✓ PASS Source code directory
✓ PASS Python executable in venv
✓ PASS Activation script exists
✓ PASS GUI launcher exists
✓ PASS UI modules directory

============================================================
                     PYTHON VERSION VALIDATION
============================================================
✓ PASS Python version check - Version: Python 3.8.10
✓ PASS Python version compatibility (3.8+) - Detected: Python 3.8
```

## Support and Additional Resources

### Log Files and Debugging
- Console output provides immediate feedback
- Check Python tracebacks for detailed error information
- Use `--verbose` flag if available in launchers

### Getting Help
1. Run diagnostic scripts first
2. Check error messages carefully
3. Verify you're following the correct platform procedures
4. Ensure all prerequisite software is installed

### Development Mode
For developers working on the GUI:
```bash
# Activate environment
# Run in development mode with detailed output
python -v start_gui.py  # Verbose Python output
```

This comprehensive guide should help you successfully set up and test the GUI environment for the Panoramic Image Annotation Tool.