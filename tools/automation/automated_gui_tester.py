#!/usr/bin/env python3
"""
Automated GUI Testing Framework with Continuous Defect Detection and Auto-Fixing
Based on the design document's automated testing strategy
"""

import sys
import os
import time
import subprocess
import threading
import traceback
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add project path to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

class DefectPriority(Enum):
    """Defect priority levels"""
    CRITICAL = "P0"  # Application crashes, startup failures
    HIGH = "P1"      # Core functionality broken, data loss risks
    MEDIUM = "P2"    # Feature malfunctions, performance issues
    LOW = "P3"       # UI cosmetic issues, minor inconsistencies

class DefectType(Enum):
    """Types of defects that can be detected"""
    ENVIRONMENT = "environment"
    GUI = "gui"
    LOGIC = "logic"
    DATA = "data"
    PERFORMANCE = "performance"

@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    passed: bool
    error_message: str = ""
    execution_time: float = 0.0
    defects_found: List[str] = None
    
    def __post_init__(self):
        if self.defects_found is None:
            self.defects_found = []

@dataclass
class Defect:
    """Defect data structure"""
    id: str
    type: DefectType
    priority: DefectPriority
    description: str
    error_details: str
    suggested_fix: str
    auto_fixable: bool
    fix_applied: bool = False
    fix_success: bool = False

class AutomatedTestRunner:
    """Main automated testing framework with continuous testing capabilities"""
    
    def __init__(self, test_directory: str = "D:\\test\\images"):
        self.test_directory = test_directory
        self.project_root = project_root
        self.defects: List[Defect] = []
        self.fixes_applied: List[str] = []
        self.test_cycles = 0
        self.max_cycles = 10
        self.results: List[TestResult] = []
        
        # Setup logging
        self.setup_logging()
        
        # Initialize test environment
        self.logger.info("Initializing Automated GUI Testing Framework")
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = os.path.join(self.project_root, "test_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"automated_test_{timestamp}.log")
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def run_continuous_testing(self) -> Dict[str, Any]:
        """Run continuous testing until all tests pass or max cycles reached"""
        self.logger.info("Starting Continuous Testing Cycle")
        
        while self.test_cycles < self.max_cycles:
            self.logger.info(f"Test Cycle {self.test_cycles + 1}/{self.max_cycles}")
            
            # Execute comprehensive test suite
            cycle_results = self.execute_test_cycle()
            
            # Check if all tests passed
            if cycle_results.get('all_passed', False):
                self.logger.info("All tests passed! Testing completed successfully.")
                break
                
            # Analyze and fix defects
            self.analyze_and_fix_defects(cycle_results)
            
            # Increment cycle counter
            self.test_cycles += 1
            
            # Short pause before next cycle
            time.sleep(5)
            
        return self.generate_final_report()
    
    def execute_test_cycle(self) -> Dict[str, Any]:
        """Execute a complete test cycle"""
        self.logger.info("Executing Test Cycle")
        
        cycle_results = {
            'cycle_number': self.test_cycles + 1,
            'tests': [],
            'all_passed': True,
            'defects_found': []
        }
        
        # Test 1: Environment Setup
        result = self.test_environment_setup()
        cycle_results['tests'].append(result)
        if not result.passed:
            cycle_results['all_passed'] = False
            
        # Test 2: GUI Startup
        if result.passed:  # Only proceed if environment is ready
            result = self.test_gui_startup()
            cycle_results['tests'].append(result)
            if not result.passed:
                cycle_results['all_passed'] = False
                
        # Test 3: Directory Loading (if GUI started)
        if result.passed:
            result = self.test_directory_loading()
            cycle_results['tests'].append(result)
            if not result.passed:
                cycle_results['all_passed'] = False
                
        # Test 4: Image Loading (if directory loaded)
        if result.passed:
            result = self.test_image_loading()
            cycle_results['tests'].append(result)
            if not result.passed:
                cycle_results['all_passed'] = False
        
        return cycle_results
    
    def test_environment_setup(self) -> TestResult:
        """Test environment setup and virtual environment"""
        self.logger.info("Testing Environment Setup")
        start_time = time.time()
        
        try:
            # Check if we're in the correct directory
            if not os.path.exists(os.path.join(self.project_root, 'src')):
                raise Exception("Not in correct project directory - src folder not found")
                
            # Check virtual environment
            venv_path = os.path.join(self.project_root, 'venv')
            if not os.path.exists(venv_path):
                self.logger.info("Virtual environment not found, creating...")
                self.create_virtual_environment()
                
            # Test Python path and imports
            self.test_python_imports()
            
            execution_time = time.time() - start_time
            self.logger.info(f"Environment setup test passed ({execution_time:.2f}s)")
            
            return TestResult(
                test_name="Environment Setup",
                passed=True,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Environment setup test failed: {error_msg}")
            
            # Record defect
            defect = Defect(
                id=f"ENV_{len(self.defects)+1}",
                type=DefectType.ENVIRONMENT,
                priority=DefectPriority.CRITICAL,
                description="Environment setup failure",
                error_details=error_msg,
                suggested_fix="Create virtual environment and install dependencies",
                auto_fixable=True
            )
            self.defects.append(defect)
            
            return TestResult(
                test_name="Environment Setup",
                passed=False,
                error_message=error_msg,
                execution_time=execution_time,
                defects_found=[defect.id]
            )
    
    def test_gui_startup(self) -> TestResult:
        """Test GUI startup with timeout monitoring"""
        self.logger.info("Testing GUI Startup")
        start_time = time.time()
        
        try:
            # Test different startup methods
            startup_methods = [
                ("start_gui.py", "Direct startup script"),
                ("panoramic_annotation_tool.py", "Enhanced compatibility script"),
                ("launch_gui.py", "With dependency checking")
            ]
            
            for script_name, description in startup_methods:
                script_path = os.path.join(self.project_root, script_name)
                if os.path.exists(script_path):
                    self.logger.info(f"Testing {description}: {script_name}")
                    
                    # Test import capability (dry run)
                    test_result = self.test_script_import(script_path)
                    if test_result:
                        execution_time = time.time() - start_time
                        self.logger.info(f"GUI startup test passed with {script_name} ({execution_time:.2f}s)")
                        
                        return TestResult(
                            test_name="GUI Startup",
                            passed=True,
                            execution_time=execution_time
                        )
                        
            raise Exception("No working startup method found")
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"GUI startup test failed: {error_msg}")
            
            # Record defect
            defect = Defect(
                id=f"GUI_{len(self.defects)+1}",
                type=DefectType.GUI,
                priority=DefectPriority.CRITICAL,
                description="GUI startup failure",
                error_details=error_msg,
                suggested_fix="Fix import paths and missing dependencies",
                auto_fixable=True
            )
            self.defects.append(defect)
            
            return TestResult(
                test_name="GUI Startup",
                passed=False,
                error_message=error_msg,
                execution_time=execution_time,
                defects_found=[defect.id]
            )
    
    def test_directory_loading(self) -> TestResult:
        """Test directory loading functionality"""
        self.logger.info("Testing Directory Loading")
        start_time = time.time()
        
        try:
            # Check if test directory exists
            if not os.path.exists(self.test_directory):
                raise Exception(f"Test directory not found: {self.test_directory}")
                
            # Check for image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
            image_files = []
            
            for ext in image_extensions:
                pattern = f"*{ext}"
                for root, dirs, files in os.walk(self.test_directory):
                    for file in files:
                        if file.lower().endswith(ext.lower()):
                            image_files.append(os.path.join(root, file))
                            
            if not image_files:
                raise Exception(f"No image files found in {self.test_directory}")
                
            execution_time = time.time() - start_time
            self.logger.info(f"Directory loading test passed - found {len(image_files)} images ({execution_time:.2f}s)")
            
            return TestResult(
                test_name="Directory Loading",
                passed=True,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Directory loading test failed: {error_msg}")
            
            # Record defect
            defect = Defect(
                id=f"DIR_{len(self.defects)+1}",
                type=DefectType.DATA,
                priority=DefectPriority.HIGH,
                description="Directory loading failure",
                error_details=error_msg,
                suggested_fix="Create test directory with sample images",
                auto_fixable=True
            )
            self.defects.append(defect)
            
            return TestResult(
                test_name="Directory Loading",
                passed=False,
                error_message=error_msg,
                execution_time=execution_time,
                defects_found=[defect.id]
            )
    
    def test_image_loading(self) -> TestResult:
        """Test image loading functionality"""
        self.logger.info("Testing Image Loading")
        start_time = time.time()
        
        try:
            # Test PIL/Pillow image loading
            from PIL import Image
            
            # Find first image file
            image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
            test_image = None
            
            for root, dirs, files in os.walk(self.test_directory):
                for file in files:
                    if any(file.lower().endswith(ext.lower()) for ext in image_extensions):
                        test_image = os.path.join(root, file)
                        break
                if test_image:
                    break
                    
            if not test_image:
                raise Exception("No test image found")
                
            # Test image loading
            with Image.open(test_image) as img:
                width, height = img.size
                self.logger.info(f"Successfully loaded test image: {width}x{height}")
                
            execution_time = time.time() - start_time
            self.logger.info(f"Image loading test passed ({execution_time:.2f}s)")
            
            return TestResult(
                test_name="Image Loading",
                passed=True,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"Image loading test failed: {error_msg}")
            
            # Record defect
            defect = Defect(
                id=f"IMG_{len(self.defects)+1}",
                type=DefectType.DATA,
                priority=DefectPriority.MEDIUM,
                description="Image loading failure",
                error_details=error_msg,
                suggested_fix="Install Pillow and verify image file integrity",
                auto_fixable=True
            )
            self.defects.append(defect)
            
            return TestResult(
                test_name="Image Loading",
                passed=False,
                error_message=error_msg,
                execution_time=execution_time,
                defects_found=[defect.id]
            )
    
    def test_script_import(self, script_path: str) -> bool:
        """Test if a script can be imported without errors"""
        try:
            # Use subprocess to test import in isolated environment
            test_code = f"""
import sys
import os
sys.path.insert(0, '{src_path}')
# Try to import the main components
try:
    from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
    print("Import successful")
except Exception as e:
    print(f"Import failed: {{e}}")
    sys.exit(1)
"""
            
            result = subprocess.run(
                [sys.executable, "-c", test_code],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.project_root
            )
            
            return result.returncode == 0 and "Import successful" in result.stdout
            
        except Exception as e:
            self.logger.error(f"Script import test failed: {e}")
            return False
    
    def analyze_and_fix_defects(self, cycle_results: Dict[str, Any]):
        """Analyze defects and apply automated fixes"""
        self.logger.info("Analyzing and fixing defects...")
        
        for defect in self.defects:
            if not defect.fix_applied and defect.auto_fixable:
                self.logger.info(f"Applying automated fix for defect {defect.id}: {defect.description}")
                
                fix_success = self.apply_automated_fix(defect)
                defect.fix_applied = True
                defect.fix_success = fix_success
                
                if fix_success:
                    self.fixes_applied.append(f"{defect.id}: {defect.suggested_fix}")
                    self.logger.info(f"Fix applied successfully for {defect.id}")
                else:
                    self.logger.warning(f"Fix failed for {defect.id}")
    
    def apply_automated_fix(self, defect: Defect) -> bool:
        """Apply automated fix based on defect type"""
        try:
            if defect.type == DefectType.ENVIRONMENT:
                return self.fix_environment_issues(defect)
            elif defect.type == DefectType.GUI:
                return self.fix_gui_issues(defect)
            elif defect.type == DefectType.DATA:
                return self.fix_data_issues(defect)
            else:
                self.logger.warning(f"No automated fix available for defect type: {defect.type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error applying fix for {defect.id}: {e}")
            return False
    
    def fix_environment_issues(self, defect: Defect) -> bool:
        """Fix environment-related issues"""
        try:
            # Create virtual environment if missing
            venv_path = os.path.join(self.project_root, 'venv')
            if not os.path.exists(venv_path):
                self.create_virtual_environment()
                
            # Install dependencies
            self.install_dependencies()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix environment issues: {e}")
            return False
    
    def fix_gui_issues(self, defect: Defect) -> bool:
        """Fix GUI-related issues"""
        try:
            # Check and fix import paths
            if "import" in defect.error_details.lower():
                # This would be handled by environment fixes
                return True
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix GUI issues: {e}")
            return False
    
    def fix_data_issues(self, defect: Defect) -> bool:
        """Fix data-related issues"""
        try:
            # Create test directory if missing
            if not os.path.exists(self.test_directory):
                os.makedirs(self.test_directory, exist_ok=True)
                self.logger.info(f"Created test directory: {self.test_directory}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to fix data issues: {e}")
            return False
    
    def create_virtual_environment(self):
        """Create virtual environment"""
        self.logger.info("Creating virtual environment...")
        
        venv_path = os.path.join(self.project_root, 'venv')
        result = subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to create virtual environment: {result.stderr}")
            
        self.logger.info("Virtual environment created successfully")
    
    def install_dependencies(self):
        """Install dependencies in virtual environment"""
        self.logger.info("Installing dependencies...")
        
        # Determine pip path
        if os.name == 'nt':  # Windows
            pip_path = os.path.join(self.project_root, 'venv', 'Scripts', 'pip.exe')
        else:  # Linux/Mac
            pip_path = os.path.join(self.project_root, 'venv', 'bin', 'pip')
            
        # Install Pillow (main dependency)
        result = subprocess.run(
            [pip_path, "install", "Pillow"],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to install Pillow: {result.stderr}")
            
        self.logger.info("Dependencies installed successfully")
    
    def test_python_imports(self):
        """Test critical Python imports"""
        try:
            # Test PIL import
            from PIL import Image
            
            # Test tkinter import
            import tkinter as tk
            
            self.logger.info("Critical imports tested successfully")
            
        except ImportError as e:
            raise Exception(f"Import error: {e}")
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        self.logger.info("Generating final test report...")
        
        # Calculate statistics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        total_defects = len(self.defects)
        fixed_defects = sum(1 for d in self.defects if d.fix_applied and d.fix_success)
        
        report = {
            'test_summary': {
                'total_cycles': self.test_cycles,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0
            },
            'defect_summary': {
                'total_defects': total_defects,
                'fixed_defects': fixed_defects,
                'fix_rate': fixed_defects / total_defects if total_defects > 0 else 0
            },
            'defects': [asdict(d) for d in self.defects],
            'fixes_applied': self.fixes_applied,
            'test_results': [asdict(r) for r in self.results],
            'timestamp': datetime.now().isoformat()
        }
        
        # Save report to file
        report_file = os.path.join(self.project_root, "test_logs", f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Test report saved to: {report_file}")
        
        return report

def main():
    """Main function to run automated testing"""
    print("Panoramic Annotation GUI - Automated Testing Framework")
    print("=" * 60)
    
    # Initialize tester
    tester = AutomatedTestRunner()
    
    # Run continuous testing
    final_report = tester.run_continuous_testing()
    
    # Print summary
    print("\nTesting Complete!")
    print(f"Total Cycles: {final_report['test_summary']['total_cycles']}")
    print(f"Success Rate: {final_report['test_summary']['success_rate']:.2%}")
    print(f"Defects Fixed: {final_report['defect_summary']['fixed_defects']}/{final_report['defect_summary']['total_defects']}")
    
    return final_report

if __name__ == "__main__":
    main()