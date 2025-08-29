# Environment Setup Steps

This guide provides the exact steps to prepare the GUI environment for testing.

## Required Steps (In Order)

### Step 1: Navigate to Project Directory
```cmd
cd .\batch_annotation_tool\
```

**What this does:**
- Changes to the batch_annotation_tool directory
- Sets the working directory where all scripts and the virtual environment are located

### Step 2: Activate Virtual Environment
```cmd
venv\Scripts\activate
```

**What this does:**
- Activates the pre-configured Python virtual environment
- Sets up the Python path and dependencies
- Prepares the environment for GUI testing

**Expected result:**
- Your command prompt should show `(venv)` prefix
- Python executable now points to the virtual environment

### Step 3: Verify Environment Setup
```cmd
python verify_activation.py
```

**What this checks:**
- ✅ Virtual environment is properly activated
- ✅ Required Python packages are available
- ✅ GUI modules can be imported
- ✅ Environment is ready for GUI launch

### Step 4: Launch GUI
```cmd
python start_gui.py
```

**Alternative launch methods:**
```cmd
python launch_gui.py
python launch_panoramic_gui.py
```

## Complete Workflow Example

Open Command Prompt or PowerShell and run:

```cmd
# Step 1: Navigate to project
cd .\batch_annotation_tool\

# Step 2: Activate environment
venv\Scripts\activate

# Step 3: Verify setup (optional but recommended)
python verify_activation.py

# Step 4: Launch GUI
python start_gui.py
```

## Visual Confirmation

After each step, you should see:

**After Step 1 (cd .\batch_annotation_tool\):**
```
PS D:\dev\annotation_tools\batch_annotation_tool>
```

**After Step 2 (venv\Scripts\activate):**
```
(venv) PS D:\dev\annotation_tools\batch_annotation_tool>
```

**After Step 3 (verify_activation.py):**
```
✅ Virtual environment is properly activated!
✅ GUI modules can be imported
🎉 GUI is ready to launch!
```

## Troubleshooting

### If Step 1 Fails
- Make sure you're starting from the correct parent directory
- Check that `batch_annotation_tool` directory exists
- Use `ls` or `dir` to see available directories

### If Step 2 Fails
- Check that `venv` directory exists in `batch_annotation_tool`
- Verify `venv\Scripts\activate` file exists
- Try using full path: `.\venv\Scripts\activate`

### If Step 3 Shows Errors
- Run the comprehensive test: `python test_gui_environment_setup.py`
- Check for missing dependencies: `pip install -e .`
- Verify you're in the correct directory

### If Step 4 Fails
- Check console output for specific error messages
- Ensure all previous steps completed successfully
- Try alternative launchers

## Automated Setup Script

For convenience, you can also use the automated setup:

```cmd
cd .\batch_annotation_tool\
start_gui.bat
```

This script automatically handles environment activation and GUI launch.

## Memory Aid

Remember the sequence:
1. **CD** (Change Directory) → `cd .\batch_annotation_tool\`
2. **ACTIVATE** (Virtual Environment) → `venv\Scripts\activate`
3. **VERIFY** (Environment Check) → `python verify_activation.py`
4. **LAUNCH** (GUI Application) → `python start_gui.py`