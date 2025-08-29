#!/usr/bin/env python3
"""
Step-by-Step Environment Verification
====================================

This script verifies that you have followed the correct setup sequence:
1. cd .\batch_annotation_tool\
2. venv\Scripts\activate

Usage:
    python check_setup_sequence.py

"""

import sys
import os
from pathlib import Path
import platform

def print_header(title):
    """Print formatted header"""
    print(f"\n{'=' * 60}")
    print(f"{title.center(60)}")
    print(f"{'=' * 60}")

def check_step1_directory():
    """Check if we're in the correct directory (Step 1)"""
    print_header("STEP 1: Directory Check")
    
    current_dir = Path.cwd()
    expected_dir_name = "batch_annotation_tool"
    
    print(f"📁 Current working directory: {current_dir}")
    print(f"📁 Expected directory name: {expected_dir_name}")
    
    is_correct_dir = current_dir.name == expected_dir_name
    
    if is_correct_dir:
        print("✅ SUCCESS: You are in the correct directory!")
        print("   Step 1 completed: cd .\batch_annotation_tool\\")
    else:
        print("❌ ERROR: Wrong directory!")
        print(f"   Expected to be in: {expected_dir_name}")
        print(f"   Currently in: {current_dir.name}")
        print("\n💡 Solution:")
        print("   Run: cd .\batch_annotation_tool\\")
        return False
    
    # Check for required files/directories
    required_items = ["venv", "start_gui.py", "src"]
    missing_items = []
    
    print("\n🔍 Checking required files and directories:")
    for item in required_items:
        if Path(item).exists():
            print(f"✅ Found: {item}")
        else:
            print(f"❌ Missing: {item}")
            missing_items.append(item)
    
    if missing_items:
        print(f"\n⚠️  Warning: Missing items: {', '.join(missing_items)}")
        return False
    
    return True

def check_step2_venv_activation():
    """Check if virtual environment is activated (Step 2)"""
    print_header("STEP 2: Virtual Environment Activation Check")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    print(f"🐍 Python executable: {sys.executable}")
    print(f"🐍 Python version: {sys.version.split()[0]}")
    print(f"🔧 Virtual environment active: {'✅ YES' if in_venv else '❌ NO'}")
    
    if not in_venv:
        print("\n❌ ERROR: Virtual environment is not activated!")
        print("💡 Solution:")
        print("   1. Make sure you're in batch_annotation_tool directory")
        print("   2. Run: venv\\Scripts\\activate")
        print("   3. You should see (venv) in your command prompt")
        return False
    
    # Check if we're using the project's venv
    current_dir = Path.cwd()
    if platform.system() == "Windows":
        expected_python = current_dir / "venv" / "Scripts" / "python.exe"
    else:
        expected_python = current_dir / "bin" / "python"
    
    using_project_venv = str(expected_python) in sys.executable or expected_python.samefile(Path(sys.executable))
    
    print(f"📂 Using project venv: {'✅ YES' if using_project_venv else '❌ NO'}")
    
    if not using_project_venv:
        print("\n⚠️  Warning: Not using the project's virtual environment!")
        print("💡 Make sure you activated the venv from the correct directory:")
        print("   venv\\Scripts\\activate")
        return False
    
    print("\n✅ SUCCESS: Virtual environment is properly activated!")
    print("   Step 2 completed: venv\\Scripts\\activate")
    return True

def check_environment_readiness():
    """Check if environment is ready for GUI launch"""
    print_header("ENVIRONMENT READINESS CHECK")
    
    # Add src to Python path
    src_path = Path("src")
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    checks = [
        ("tkinter available", lambda: __import__("tkinter")),
        ("PIL available", lambda: __import__("PIL")),
        ("yaml available", lambda: __import__("yaml")),
        ("GUI module importable", lambda: __import__("ui.panoramic_annotation_gui")),
        ("start_gui.py exists", lambda: Path("start_gui.py").exists()),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            if callable(result):
                result = True
            print(f"✅ {check_name}")
            passed += 1
        except Exception as e:
            print(f"❌ {check_name}: {e}")
    
    success_rate = (passed / total) * 100
    print(f"\n📊 Environment Readiness: {passed}/{total} ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 Environment is fully ready for GUI testing!")
        return True
    else:
        print("⚠️  Some environment issues detected.")
        if passed < total // 2:
            print("💡 Try running: pip install -e .")
        return False

def provide_next_steps(all_checks_passed):
    """Provide next steps based on verification results"""
    print_header("NEXT STEPS")
    
    if all_checks_passed:
        print("🚀 Your environment is properly set up!")
        print("\nYou can now launch the GUI:")
        print("   python start_gui.py")
        print("\nAlternative launch methods:")
        print("   python launch_gui.py")
        print("   python launch_panoramic_gui.py")
        print("   start_gui.bat")
        
        print("\n🧪 Additional testing options:")
        print("   python quick_env_check.py")
        print("   python test_gui_environment_setup.py")
        print("   python test_gui_launch_methods.py")
        print("   run_all_tests.bat")
    else:
        print("❌ Setup incomplete. Please fix the issues above.")
        print("\n🔄 Complete setup sequence:")
        print("   1. cd .\\batch_annotation_tool\\")
        print("   2. venv\\Scripts\\activate")
        print("   3. pip install -e . (if needed)")
        print("   4. python start_gui.py")

def main():
    """Main verification function"""
    print("Step-by-Step Environment Setup Verification")
    print(f"Platform: {platform.system()}")
    print(f"Time: {Path(__file__).stat().st_mtime}")
    
    # Run verification steps
    step1_ok = check_step1_directory()
    step2_ok = check_step2_venv_activation() if step1_ok else False
    env_ok = check_environment_readiness() if step2_ok else False
    
    all_ok = step1_ok and step2_ok and env_ok
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    print(f"Step 1 (Directory): {'✅ PASS' if step1_ok else '❌ FAIL'}")
    print(f"Step 2 (Activation): {'✅ PASS' if step2_ok else '❌ FAIL'}")
    print(f"Environment Ready: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"Overall Result: {'🎉 SUCCESS' if all_ok else '⚠️ NEEDS ATTENTION'}")
    
    provide_next_steps(all_ok)

if __name__ == "__main__":
    main()