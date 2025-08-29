#!/usr/bin/env python3
"""
Quick GUI Environment Validator
===============================

A simple script to quickly validate that the GUI environment is properly set up.
This script performs essential checks to ensure the GUI can be launched successfully.

Usage:
    python quick_env_check.py

"""

import os
import sys
import traceback
from pathlib import Path

def check_environment():
    """Perform quick environment validation"""
    print("🔍 Quick GUI Environment Check")
    print("=" * 40)
    
    # 1. Check if we're in the right directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    expected_files = ["start_gui.py", "venv", "src"]
    missing_files = []
    
    for file in expected_files:
        if os.path.exists(file):
            print(f"✅ Found: {file}")
        else:
            print(f"❌ Missing: {file}")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Warning: Missing files/directories: {', '.join(missing_files)}")
        print("Make sure you're running this script from the batch_annotation_tool directory")
        return False
    
    # 2. Check virtual environment
    venv_python = Path("venv/Scripts/python.exe") if os.name == 'nt' else Path("venv/bin/python")
    if venv_python.exists():
        print(f"✅ Virtual environment Python: {venv_python}")
    else:
        print(f"❌ Virtual environment Python not found: {venv_python}")
        return False
    
    # 3. Check if we can import the GUI module
    print("\n🧪 Testing module imports...")
    
    # Add src to path
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    try:
        # Test basic GUI import
        from ui.panoramic_annotation_gui import main
        print("✅ GUI module import successful")
        
        # Test tkinter (GUI framework)
        import tkinter
        print("✅ tkinter (GUI framework) available")
        
        # Test PIL (image processing)
        from PIL import Image
        print("✅ PIL (image processing) available")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n💡 Try running: pip install -e .")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def provide_startup_commands():
    """Provide platform-specific startup commands"""
    print("\n🚀 Startup Commands")
    print("=" * 40)
    
    if os.name == 'nt':  # Windows
        print("Windows Commands:")
        print("  1. Activate environment: venv\\Scripts\\activate")
        print("  2. Install dependencies: pip install -e .")
        print("  3. Launch GUI: python start_gui.py")
        print("\nOr use automated script:")
        print("  start_gui.bat")
    else:  # Unix/Linux/macOS
        print("Unix/Linux/macOS Commands:")
        print("  1. Activate environment: source venv/bin/activate")
        print("  2. Install dependencies: pip install -e .")
        print("  3. Launch GUI: python start_gui.py")
        print("\nOr use automated script:")
        print("  ./start_gui.sh")

def main():
    """Main function"""
    try:
        success = check_environment()
        
        if success:
            print("\n🎉 Environment check passed!")
            print("You should be able to launch the GUI with: python start_gui.py")
        else:
            print("\n⚠️  Environment check failed!")
            print("Please fix the issues above before launching the GUI.")
        
        provide_startup_commands()
        
    except Exception as e:
        print(f"\n❌ Error during environment check: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()