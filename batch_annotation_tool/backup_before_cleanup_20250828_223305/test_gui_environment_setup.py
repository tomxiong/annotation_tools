#!/usr/bin/env python3
"""
GUI Environment Setup Test Script
=================================

This script tests the environment setup for the Panoramic Image Annotation Tool GUI.
It validates the virtual environment, dependencies, and GUI launch capabilities.

Usage:
    python test_gui_environment_setup.py

Features:
- Virtual environment validation
- Dependency checking
- GUI launch testing
- Cross-platform compatibility testing
- Environment recovery procedures
"""

import os
import sys
import subprocess
import platform
import traceback
from pathlib import Path
import importlib.util


class Colors:
    """Console color codes for better output readability"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def green(cls, text):
        return f"{cls.GREEN}{text}{cls.END}"
    
    @classmethod
    def red(cls, text):
        return f"{cls.RED}{text}{cls.END}"
    
    @classmethod
    def yellow(cls, text):
        return f"{cls.YELLOW}{text}{cls.END}"
    
    @classmethod
    def blue(cls, text):
        return f"{cls.BLUE}{text}{cls.END}"
    
    @classmethod
    def bold(cls, text):
        return f"{cls.BOLD}{text}{cls.END}"


class GUIEnvironmentTester:
    """Comprehensive GUI environment testing class"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.absolute()
        self.venv_path = self.project_root / "venv"
        self.src_path = self.project_root / "src"
        self.is_windows = platform.system() == "Windows"
        self.python_exe = self._get_python_executable()
        self.test_results = {
            'environment': [],
            'dependencies': [],
            'gui_launch': [],
            'functionality': []
        }
    
    def _get_python_executable(self):
        """Get the correct Python executable path for the current platform"""
        if self.is_windows:
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def _get_activation_script(self):
        """Get the correct activation script for the current platform"""
        if self.is_windows:
            return self.venv_path / "Scripts" / "activate.bat"
        else:
            return self.venv_path / "bin" / "activate"
    
    def print_header(self, title):
        """Print a formatted header"""
        print(f"\n{Colors.bold('=' * 60)}")
        print(f"{Colors.bold(title.center(60))}")
        print(f"{Colors.bold('=' * 60)}")
    
    def print_test_result(self, test_name, success, message="", details=""):
        """Print formatted test result"""
        status = Colors.green("✓ PASS") if success else Colors.red("✗ FAIL")
        print(f"{status} {test_name}")
        if message:
            print(f"    {message}")
        if details:
            print(f"    {Colors.yellow('Details:')} {details}")
    
    def test_environment_structure(self):
        """Test 1: Validate directory structure and virtual environment"""
        self.print_header("ENVIRONMENT STRUCTURE VALIDATION")
        
        tests = [
            ("Project root directory", self.project_root.exists()),
            ("Virtual environment directory", self.venv_path.exists()),
            ("Source code directory", self.src_path.exists()),
            ("Python executable in venv", self.python_exe.exists()),
            ("Activation script exists", self._get_activation_script().exists()),
            ("GUI launcher exists", (self.project_root / "start_gui.py").exists()),
            ("UI modules directory", (self.src_path / "ui").exists()),
        ]
        
        for test_name, result in tests:
            self.print_test_result(test_name, result)
            self.test_results['environment'].append((test_name, result))
        
        return all(result for _, result in tests)
    
    def test_python_version(self):
        """Test 2: Validate Python version in virtual environment"""
        self.print_header("PYTHON VERSION VALIDATION")
        
        try:
            # Test Python version
            result = subprocess.run(
                [str(self.python_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                self.print_test_result(
                    "Python version check", 
                    True, 
                    f"Version: {version_output}"
                )
                
                # Check if version is 3.8+
                version_parts = version_output.split()
                if len(version_parts) >= 2:
                    version_str = version_parts[1]
                    major, minor = map(int, version_str.split('.')[:2])
                    is_compatible = major == 3 and minor >= 8
                    self.print_test_result(
                        "Python version compatibility (3.8+)", 
                        is_compatible,
                        f"Detected: Python {major}.{minor}"
                    )
                    self.test_results['environment'].append(("Python version", is_compatible))
                    return is_compatible
                else:
                    self.print_test_result("Python version parsing", False, "Could not parse version")
                    return False
            else:
                self.print_test_result(
                    "Python executable test", 
                    False, 
                    f"Error: {result.stderr}"
                )
                return False
                
        except subprocess.TimeoutExpired:
            self.print_test_result("Python version check", False, "Timeout expired")
            return False
        except Exception as e:
            self.print_test_result("Python version check", False, f"Exception: {e}")
            return False
    
    def test_package_installation(self):
        """Test 3: Check if the batch-annotation-tool package is installed"""
        self.print_header("PACKAGE INSTALLATION VALIDATION")
        
        try:
            result = subprocess.run(
                [str(self.python_exe), "-m", "pip", "list"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = result.stdout
                has_batch_tool = "batch-annotation-tool" in packages
                
                self.print_test_result(
                    "batch-annotation-tool package installed", 
                    has_batch_tool,
                    "Found in pip list" if has_batch_tool else "Not found in pip list"
                )
                
                # Check for key dependencies
                dependencies = ["Pillow", "PyYAML", "click"]
                for dep in dependencies:
                    has_dep = dep.lower() in packages.lower()
                    self.print_test_result(
                        f"Dependency: {dep}", 
                        has_dep,
                        "Installed" if has_dep else "Missing"
                    )
                    self.test_results['dependencies'].append((dep, has_dep))
                
                return has_batch_tool
            else:
                self.print_test_result("Package list check", False, f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.print_test_result("Package installation check", False, "Timeout expired")
            return False
        except Exception as e:
            self.print_test_result("Package installation check", False, f"Exception: {e}")
            return False
    
    def test_module_imports(self):
        """Test 4: Test importing key GUI modules"""
        self.print_header("MODULE IMPORT VALIDATION")
        
        # Add src to Python path for testing
        original_path = sys.path.copy()
        if str(self.src_path) not in sys.path:
            sys.path.insert(0, str(self.src_path))
        
        modules_to_test = [
            ("tkinter", "GUI framework"),
            ("PIL", "Image processing"),
            ("yaml", "Configuration files"),
            ("ui.panoramic_annotation_gui", "Main GUI module"),
            ("models.panoramic_annotation", "Annotation data model"),
            ("services.panoramic_image_service", "Image service"),
            ("core.config", "Configuration management"),
        ]
        
        for module_name, description in modules_to_test:
            try:
                if module_name.startswith("ui.") or module_name.startswith("models.") or \
                   module_name.startswith("services.") or module_name.startswith("core."):
                    # For local modules, check file existence first
                    module_path = self.src_path / module_name.replace(".", "/") + ".py"
                    if module_path.exists():
                        spec = importlib.util.spec_from_file_location(module_name, module_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            success = True
                        else:
                            success = False
                    else:
                        success = False
                else:
                    # For standard library and installed packages
                    __import__(module_name)
                    success = True
                
                self.print_test_result(
                    f"Import {module_name}", 
                    success, 
                    f"{description} - Available"
                )
                
            except ImportError as e:
                self.print_test_result(
                    f"Import {module_name}", 
                    False, 
                    f"{description} - Import Error: {str(e)}"
                )
            except Exception as e:
                self.print_test_result(
                    f"Import {module_name}", 
                    False, 
                    f"{description} - Error: {str(e)}"
                )
        
        # Restore original path
        sys.path = original_path
    
    def test_gui_launch_methods(self):
        """Test 5: Test different GUI launch methods"""
        self.print_header("GUI LAUNCH METHODS VALIDATION")
        
        launch_methods = [
            ("start_gui.py", "Primary GUI launcher"),
            ("launch_gui.py", "Enhanced GUI launcher"),
            ("launch_panoramic_gui.py", "Panoramic-specific launcher"),
            ("run_gui.py", "Simple GUI launcher"),
        ]
        
        for script_name, description in launch_methods:
            script_path = self.project_root / script_name
            
            if script_path.exists():
                try:
                    # Test if the script can be loaded and parsed
                    with open(script_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    # Compile to check for syntax errors
                    compile(code, str(script_path), 'exec')
                    
                    self.print_test_result(
                        f"Launch script: {script_name}", 
                        True, 
                        f"{description} - Syntax OK"
                    )
                    
                except SyntaxError as e:
                    self.print_test_result(
                        f"Launch script: {script_name}", 
                        False, 
                        f"{description} - Syntax Error: {e}"
                    )
                except Exception as e:
                    self.print_test_result(
                        f"Launch script: {script_name}", 
                        False, 
                        f"{description} - Error: {e}"
                    )
            else:
                self.print_test_result(
                    f"Launch script: {script_name}", 
                    False, 
                    f"{description} - File not found"
                )
    
    def test_startup_scripts(self):
        """Test 6: Test platform-specific startup scripts"""
        self.print_header("STARTUP SCRIPTS VALIDATION")
        
        if self.is_windows:
            scripts = [
                ("start_gui.bat", "Windows GUI startup script"),
                ("start_cli.bat", "Windows CLI startup script"),
            ]
        else:
            scripts = [
                ("start_gui.sh", "Unix GUI startup script"), 
                ("start_cli.sh", "Unix CLI startup script"),
            ]
        
        for script_name, description in scripts:
            script_path = self.project_root / script_name
            
            if script_path.exists():
                try:
                    with open(script_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic validation - check for key commands
                    has_venv_check = "venv" in content
                    has_python_call = "python" in content
                    
                    is_valid = has_venv_check and has_python_call
                    
                    self.print_test_result(
                        f"Startup script: {script_name}", 
                        is_valid, 
                        f"{description} - {'Valid structure' if is_valid else 'Invalid structure'}"
                    )
                    
                except Exception as e:
                    self.print_test_result(
                        f"Startup script: {script_name}", 
                        False, 
                        f"{description} - Read Error: {e}"
                    )
            else:
                self.print_test_result(
                    f"Startup script: {script_name}", 
                    False, 
                    f"{description} - File not found"
                )
    
    def test_gui_dry_run(self):
        """Test 7: Perform a dry run of GUI startup without actually launching the GUI"""
        self.print_header("GUI DRY RUN TEST")
        
        try:
            # Add src to path
            if str(self.src_path) not in sys.path:
                sys.path.insert(0, str(self.src_path))
            
            # Try to import the main GUI function
            from ui.panoramic_annotation_gui import main
            
            self.print_test_result(
                "GUI main function import", 
                True, 
                "Successfully imported GUI main function"
            )
            
            # Note: We don't actually call main() to avoid launching the GUI
            # Instead, we just verify that it can be imported
            
            return True
            
        except ImportError as e:
            self.print_test_result(
                "GUI main function import", 
                False, 
                f"Import failed: {e}"
            )
            return False
        except Exception as e:
            self.print_test_result(
                "GUI main function import", 
                False, 
                f"Unexpected error: {e}"
            )
            return False
    
    def suggest_fixes(self):
        """Suggest fixes for common issues"""
        self.print_header("ENVIRONMENT SETUP SUGGESTIONS")
        
        if not self.venv_path.exists():
            print(f"{Colors.yellow('⚠ SUGGESTION:')} Virtual environment not found.")
            print(f"   Run: {Colors.blue('python -m venv venv')}")
        
        if not self.python_exe.exists():
            print(f"{Colors.yellow('⚠ SUGGESTION:')} Python executable not found in venv.")
            print(f"   Recreate venv: {Colors.blue('python -m venv venv')}")
        
        print(f"\n{Colors.yellow('💡 ENVIRONMENT SETUP COMMANDS:')}")
        if self.is_windows:
            print(f"   1. {Colors.blue('venv\\Scripts\\activate')}")
            print(f"   2. {Colors.blue('pip install -e .')}")
            print(f"   3. {Colors.blue('python start_gui.py')}")
        else:
            print(f"   1. {Colors.blue('source venv/bin/activate')}")
            print(f"   2. {Colors.blue('pip install -e .')}")
            print(f"   3. {Colors.blue('python start_gui.py')}")
        
        print(f"\n{Colors.yellow('🚀 ALTERNATIVE LAUNCH METHODS:')}")
        print(f"   - Use automated scripts: {Colors.blue('start_gui.bat' if self.is_windows else './start_gui.sh')}")
        print(f"   - Enhanced launcher: {Colors.blue('python launch_gui.py')}")
        print(f"   - Panoramic launcher: {Colors.blue('python launch_panoramic_gui.py')}")
    
    def generate_recovery_script(self):
        """Generate a recovery script for environment issues"""
        self.print_header("RECOVERY SCRIPT GENERATION")
        
        if self.is_windows:
            recovery_content = """@echo off
echo GUI Environment Recovery Script
echo ================================

echo Cleaning up existing environment...
if exist venv rmdir /s /q venv

echo Creating new virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\\Scripts\\activate

echo Installing dependencies...
pip install --upgrade pip
pip install -e .

echo Testing GUI import...
python -c "import sys; sys.path.insert(0, 'src'); from ui.panoramic_annotation_gui import main; print('GUI import successful')"

echo Recovery complete! You can now run:
echo   python start_gui.py
pause
"""
            recovery_file = self.project_root / "recover_environment.bat"
        else:
            recovery_content = """#!/bin/bash
echo "GUI Environment Recovery Script"
echo "================================"

echo "Cleaning up existing environment..."
if [ -d "venv" ]; then rm -rf venv; fi

echo "Creating new virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -e .

echo "Testing GUI import..."
python -c "import sys; sys.path.insert(0, 'src'); from ui.panoramic_annotation_gui import main; print('GUI import successful')"

echo "Recovery complete! You can now run:"
echo "  python start_gui.py"
"""
            recovery_file = self.project_root / "recover_environment.sh"
        
        try:
            with open(recovery_file, 'w', encoding='utf-8') as f:
                f.write(recovery_content)
            
            if not self.is_windows:
                # Make script executable on Unix systems
                os.chmod(recovery_file, 0o755)
            
            self.print_test_result(
                "Recovery script generation", 
                True, 
                f"Created: {recovery_file.name}"
            )
            
            return True
            
        except Exception as e:
            self.print_test_result(
                "Recovery script generation", 
                False, 
                f"Error: {e}"
            )
            return False
    
    def print_summary(self):
        """Print a comprehensive test summary"""
        self.print_header("TEST SUMMARY REPORT")
        
        total_tests = sum(len(category) for category in self.test_results.values())
        passed_tests = sum(
            sum(1 for _, result in category if result) 
            for category in self.test_results.values()
        )
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {Colors.green(str(passed_tests))}")
        print(f"Failed: {Colors.red(str(total_tests - passed_tests))}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A")
        
        if passed_tests == total_tests:
            print(f"\n{Colors.green('🎉 ALL TESTS PASSED! Environment is ready for GUI testing.')}")
        else:
            print(f"\n{Colors.yellow('⚠ Some tests failed. Check the suggestions above.')}")
    
    def run_all_tests(self):
        """Run all environment tests"""
        print(f"{Colors.bold('GUI Environment Setup Test')}")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Project Root: {self.project_root}")
        print(f"Python Executable: {self.python_exe}")
        
        # Run all test categories
        self.test_environment_structure()
        self.test_python_version()
        self.test_package_installation()
        self.test_module_imports()
        self.test_gui_launch_methods()
        self.test_startup_scripts()
        self.test_gui_dry_run()
        
        # Generate helpful output
        self.suggest_fixes()
        self.generate_recovery_script()
        self.print_summary()


def main():
    """Main entry point for the test script"""
    try:
        tester = GUIEnvironmentTester()
        tester.run_all_tests()
        
    except KeyboardInterrupt:
        print(f"\n{Colors.yellow('Test interrupted by user')}")
    except Exception as e:
        print(f"\n{Colors.red('Unexpected error during testing:')}")
        print(f"{Colors.red(str(e))}")
        traceback.print_exc()


if __name__ == "__main__":
    main()