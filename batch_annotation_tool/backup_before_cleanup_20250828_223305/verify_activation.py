#!/usr/bin/env python3
"""
Virtual Environment Activation Verification
===========================================

This script verifies that the virtual environment is properly activated
and tests basic GUI functionality.

Usage:
    # After activating venv with: venv\Scripts\activate
    python verify_activation.py

"""

import sys
import os
from pathlib import Path
import platform

def check_virtual_environment():
    """Check if we're running in the virtual environment"""
    print("🔍 Virtual Environment Activation Check")
    print("=" * 50)
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    print(f"📍 Current Python executable: {sys.executable}")
    print(f"📍 Python version: {sys.version}")
    print(f"📍 Virtual environment active: {'✅ YES' if in_venv else '❌ NO'}")
    
    # Check if we're using the project's venv
    current_dir = Path.cwd()
    expected_venv = current_dir / "venv"
    
    if platform.system() == "Windows":
        expected_python = expected_venv / "Scripts" / "python.exe"
    else:
        expected_python = expected_venv / "bin" / "python"
    
    using_project_venv = str(expected_python) in sys.executable
    print(f"📍 Using project venv: {'✅ YES' if using_project_venv else '❌ NO'}")
    
    if not in_venv:
        print("\n⚠️  WARNING: Virtual environment not detected!")
        print("Make sure you've run the activation command:")
        if platform.system() == "Windows":
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        return False
    
    if not using_project_venv:
        print("\n⚠️  WARNING: Not using the project's virtual environment!")
        print("Make sure you're in the batch_annotation_tool directory and using the correct venv.")
        return False
    
    print("\n✅ Virtual environment is properly activated!")
    return True

def test_gui_imports():
    """Test if GUI modules can be imported"""
    print("\n🧪 GUI Module Import Test")
    print("=" * 50)
    
    # Add src to path
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    import_tests = [
        ("tkinter", "GUI framework"),
        ("PIL", "Image processing"),
        ("yaml", "Configuration files"),
        ("ui.panoramic_annotation_gui", "Main GUI module"),
    ]
    
    success_count = 0
    total_tests = len(import_tests)
    
    for module, description in import_tests:
        try:
            __import__(module)
            print(f"✅ {module}: {description}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {module}: {description} - {e}")
        except Exception as e:
            print(f"⚠️ {module}: {description} - Unexpected error: {e}")
    
    success_rate = (success_count / total_tests) * 100
    print(f"\nImport Success Rate: {success_rate:.1f}% ({success_count}/{total_tests})")
    
    return success_count == total_tests

def test_gui_launch_readiness():
    """Test if GUI is ready to launch"""
    print("\n🚀 GUI Launch Readiness Test")
    print("=" * 50)
    
    checks = []
    
    # Check if start_gui.py exists
    start_gui = Path("start_gui.py")
    checks.append(("start_gui.py exists", start_gui.exists()))
    
    # Check if src/ui directory exists
    ui_dir = Path("src/ui")
    checks.append(("UI module directory exists", ui_dir.exists()))
    
    # Check if main GUI file exists
    main_gui = Path("src/ui/panoramic_annotation_gui.py")
    checks.append(("Main GUI module exists", main_gui.exists()))
    
    # Test if we can import the main function
    try:
        if str(Path("src")) not in sys.path:
            sys.path.insert(0, str(Path("src")))
        from ui.panoramic_annotation_gui import main
        checks.append(("GUI main function importable", True))
    except Exception:
        checks.append(("GUI main function importable", False))
    
    # Display results
    passed = 0
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if result:
            passed += 1
    
    all_passed = passed == len(checks)
    print(f"\nReadiness Score: {passed}/{len(checks)}")
    
    if all_passed:
        print("🎉 GUI is ready to launch!")
        print("You can now run: python start_gui.py")
    else:
        print("⚠️ Some issues detected. Please check the failed items above.")
    
    return all_passed

def provide_next_steps():
    """Provide next steps based on test results"""
    print("\n📋 Next Steps")
    print("=" * 50)
    
    print("After successful activation, you can:")
    print("1. 🚀 Launch GUI: python start_gui.py")
    print("2. 🧪 Run environment tests: python quick_env_check.py")
    print("3. 🔧 Run comprehensive tests: python test_gui_environment_setup.py")
    print("4. 📊 Test launch methods: python test_gui_launch_methods.py")
    print("5. 🔄 Run all tests: run_all_tests.bat")
    
    print("\nAlternative launch methods:")
    print("- Enhanced launcher: python launch_gui.py")
    print("- Panoramic launcher: python launch_panoramic_gui.py")
    print("- Automated script: start_gui.bat (Windows)")

def main():
    """Main verification function"""
    print("Virtual Environment Activation Verification")
    print(f"Platform: {platform.system()}")
    print(f"Working Directory: {Path.cwd()}")
    print()
    
    # Run all verification tests
    venv_ok = check_virtual_environment()
    imports_ok = test_gui_imports()
    launch_ok = test_gui_launch_readiness()
    
    # Overall result
    print("\n" + "=" * 50)
    print("OVERALL VERIFICATION RESULT")
    print("=" * 50)
    
    if venv_ok and imports_ok and launch_ok:
        print("🎉 ALL CHECKS PASSED!")
        print("Your environment is properly set up and ready for GUI testing.")
    else:
        print("⚠️ SOME ISSUES DETECTED")
        print("Please review the failed checks above and fix any issues.")
    
    provide_next_steps()

if __name__ == "__main__":
    main()