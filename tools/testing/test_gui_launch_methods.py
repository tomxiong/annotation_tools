#!/usr/bin/env python3
"""
GUI Launch Method Tester
========================

This script tests different GUI launch methods to ensure they work correctly.
It validates each launcher script and provides comprehensive startup testing.

Usage:
    python test_gui_launch_methods.py

Features:
- Tests all available GUI launchers
- Validates startup script syntax
- Provides launch command suggestions
- Tests activation methods

"""

import os
import sys
import subprocess
import platform
import traceback
from pathlib import Path
import time

class GUILaunchTester:
    """Test different GUI launch methods"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.is_windows = platform.system() == "Windows"
        self.python_exe = self._get_python_executable()
        self.results = {}
    
    def _get_python_executable(self):
        """Get the correct Python executable"""
        if self.is_windows:
            return self.project_root / "venv" / "Scripts" / "python.exe"
        else:
            return self.project_root / "venv" / "bin" / "python"
    
    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'=' * 60}")
        print(f"{title.center(60)}")
        print(f"{'=' * 60}")
    
    def test_python_launcher(self, script_name, description):
        """Test a Python launcher script"""
        script_path = self.project_root / script_name
        
        if not script_path.exists():
            print(f"❌ {script_name}: File not found")
            return False
        
        try:
            # Test syntax by compiling the script
            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, str(script_path), 'exec')
            print(f"✅ {script_name}: Syntax OK - {description}")
            
            # Test if we can import required modules from the script
            if "from ui.panoramic_annotation_gui import main" in code:
                print(f"   → Imports main GUI function")
            
            return True
            
        except SyntaxError as e:
            print(f"❌ {script_name}: Syntax Error - {e}")
            return False
        except Exception as e:
            print(f"❌ {script_name}: Error - {e}")
            return False
    
    def test_batch_script(self, script_name, description):
        """Test a batch/shell script"""
        script_path = self.project_root / script_name
        
        if not script_path.exists():
            print(f"❌ {script_name}: File not found")
            return False
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for essential components
            checks = {
                "venv check": "venv" in content,
                "python call": "python" in content,
                "activation": "activate" in content
            }
            
            all_good = all(checks.values())
            status = "✅" if all_good else "⚠️"
            
            print(f"{status} {script_name}: {description}")
            for check, result in checks.items():
                print(f"   → {check}: {'✅' if result else '❌'}")
            
            return all_good
            
        except Exception as e:
            print(f"❌ {script_name}: Read Error - {e}")
            return False
    
    def test_python_launchers(self):
        """Test all Python launcher scripts"""
        self.print_header("PYTHON LAUNCHER SCRIPTS")
        
        launchers = [
            ("start_gui.py", "Primary GUI launcher with path setup"),
            ("launch_gui.py", "Enhanced launcher with dependency checks"),
            ("launch_panoramic_gui.py", "Panoramic-specific launcher"),
            ("run_gui.py", "Simple GUI launcher"),
            ("panoramic_annotation_tool.py", "Full-featured GUI launcher"),
            ("final_gui_launcher.py", "Advanced launcher with error handling"),
        ]
        
        results = {}
        for script, desc in launchers:
            results[script] = self.test_python_launcher(script, desc)
        
        self.results['python_launchers'] = results
        return results
    
    def test_startup_scripts(self):
        """Test platform-specific startup scripts"""
        self.print_header("STARTUP SCRIPTS")
        
        if self.is_windows:
            scripts = [
                ("start_gui.bat", "Windows GUI startup script"),
                ("start_cli.bat", "Windows CLI startup script"),
                ("run_demo.bat", "Windows demo script"),
                ("run_example.bat", "Windows example script"),
                ("run_batch.bat", "Windows batch processing script"),
            ]
        else:
            scripts = [
                ("start_gui.sh", "Unix GUI startup script"),
                ("start_cli.sh", "Unix CLI startup script"),
                ("run_demo.sh", "Unix demo script"),
                ("run_example.sh", "Unix example script"),
                ("run_batch.sh", "Unix batch processing script"),
            ]
        
        results = {}
        for script, desc in scripts:
            results[script] = self.test_batch_script(script, desc)
        
        self.results['startup_scripts'] = results
        return results
    
    def test_import_capabilities(self):
        """Test if GUI modules can be imported"""
        self.print_header("MODULE IMPORT CAPABILITIES")
        
        # Add src to path
        src_path = self.project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        modules_to_test = [
            ("ui.panoramic_annotation_gui", "Main GUI module"),
            ("ui.panoramic_annotation_gui_refactored", "Refactored GUI module"),
            ("models.panoramic_annotation", "Annotation model"),
            ("services.panoramic_image_service", "Image service"),
            ("core.config", "Configuration management"),
        ]
        
        results = {}
        for module, desc in modules_to_test:
            try:
                __import__(module)
                print(f"✅ {module}: Import successful - {desc}")
                results[module] = True
            except ImportError as e:
                print(f"❌ {module}: Import failed - {e}")
                results[module] = False
            except Exception as e:
                print(f"⚠️ {module}: Unexpected error - {e}")
                results[module] = False
        
        self.results['module_imports'] = results
        return results
    
    def test_dependency_availability(self):
        """Test if required dependencies are available"""
        self.print_header("DEPENDENCY AVAILABILITY")
        
        dependencies = [
            ("tkinter", "GUI framework"),
            ("PIL", "Image processing library"),
            ("yaml", "YAML configuration parser"),
            ("click", "Command-line interface framework"),
            ("pathlib", "Path manipulation"),
            ("json", "JSON processing"),
        ]
        
        results = {}
        for dep, desc in dependencies:
            try:
                __import__(dep)
                print(f"✅ {dep}: Available - {desc}")
                results[dep] = True
            except ImportError:
                print(f"❌ {dep}: Not available - {desc}")
                results[dep] = False
        
        self.results['dependencies'] = results
        return results
    
    def provide_launch_recommendations(self):
        """Provide launch method recommendations"""
        self.print_header("LAUNCH RECOMMENDATIONS")
        
        print("🚀 Recommended Launch Methods (in order of preference):")
        print()
        
        # Check which methods are available and working
        python_results = self.results.get('python_launchers', {})
        script_results = self.results.get('startup_scripts', {})
        
        if self.is_windows:
            print("1. AUTOMATED STARTUP (Recommended for Windows):")
            if script_results.get('start_gui.bat', False):
                print("   ✅ start_gui.bat  (Double-click or run from command prompt)")
            else:
                print("   ❌ start_gui.bat  (Not available or has issues)")
            print()
        else:
            print("1. AUTOMATED STARTUP (Recommended for Unix/Linux):")
            if script_results.get('start_gui.sh', False):
                print("   ✅ ./start_gui.sh  (Run from terminal)")
            else:
                print("   ❌ ./start_gui.sh  (Not available or has issues)")
            print()
        
        print("2. MANUAL ACTIVATION + PYTHON LAUNCHER:")
        if self.is_windows:
            print("   venv\\Scripts\\activate")
        else:
            print("   source venv/bin/activate")
        
        # Recommend best Python launcher
        working_launchers = [k for k, v in python_results.items() if v]
        if working_launchers:
            best_launcher = working_launchers[0]  # First working one
            print(f"   python {best_launcher}")
        else:
            print("   ❌ No working Python launchers found")
        print()
        
        print("3. DIRECT EXECUTION (Advanced users):")
        if self.is_windows:
            print("   venv\\Scripts\\python.exe start_gui.py")
        else:
            print("   venv/bin/python start_gui.py")
        print()
        
        # Troubleshooting section
        print("🔧 TROUBLESHOOTING:")
        print()
        
        if not any(self.results.get('dependencies', {}).values()):
            print("⚠️  Missing dependencies detected:")
            print("   1. Activate virtual environment")
            print("   2. Run: pip install -e .")
            print()
        
        if not any(self.results.get('module_imports', {}).values()):
            print("⚠️  Module import issues detected:")
            print("   1. Ensure you're in the batch_annotation_tool directory")
            print("   2. Check that src/ directory exists and contains UI modules")
            print()
        
        print("🔄 RECOVERY COMMANDS:")
        if self.is_windows:
            print("   # Recreate environment")
            print("   rmdir /s venv")
            print("   python -m venv venv")
            print("   venv\\Scripts\\activate")
            print("   pip install -e .")
        else:
            print("   # Recreate environment")
            print("   rm -rf venv")
            print("   python3 -m venv venv")
            print("   source venv/bin/activate")
            print("   pip install -e .")
    
    def generate_summary(self):
        """Generate a summary of test results"""
        self.print_header("TEST SUMMARY")
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            category_total = len(tests)
            category_passed = sum(1 for result in tests.values() if result)
            
            total_tests += category_total
            passed_tests += category_passed
            
            print(f"{category.replace('_', ' ').title()}: {category_passed}/{category_total}")
        
        print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 Environment is ready for GUI testing!")
        elif success_rate >= 60:
            print("\n⚠️ Environment has some issues but may still work")
        else:
            print("\n❌ Environment needs significant fixes before use")
    
    def run_all_tests(self):
        """Run all launch method tests"""
        print("GUI Launch Method Tester")
        print(f"Platform: {platform.system()}")
        print(f"Working Directory: {self.project_root}")
        
        # Run all test categories
        self.test_python_launchers()
        self.test_startup_scripts()
        self.test_import_capabilities()
        self.test_dependency_availability()
        
        # Provide recommendations and summary
        self.provide_launch_recommendations()
        self.generate_summary()

def main():
    """Main entry point"""
    try:
        tester = GUILaunchTester()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()