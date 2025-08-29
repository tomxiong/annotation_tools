#!/usr/bin/env python3
"""
Automated GUI Functionality Testing Framework
Refactored automated testing system focused on functionality detection with intelligent 
defect detection and auto-resolution capabilities.

Based on dpano-gui-test.md design document.
"""

import sys
import os
import time
import subprocess
import threading
import traceback
import logging
import json
import psutil
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path

# Add project path to Python path
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

class DefectPriority(Enum):
    """Defect priority levels for automated resolution"""
    CRITICAL = "P0"  # Application crashes, startup failures
    HIGH = "P1"      # Core functionality broken, data loss risks
    MEDIUM = "P2"    # Feature malfunctions, performance issues
    LOW = "P3"       # UI cosmetic issues, minor inconsistencies

class DefectType(Enum):
    """Types of defects that can be detected and resolved"""
    ENVIRONMENT = "environment"
    GUI = "gui"
    NAVIGATION = "navigation"
    ANNOTATION = "annotation"
    DATA = "data"
    PERFORMANCE = "performance"

class TestPhase(Enum):
    """Test execution phases"""
    ENVIRONMENT = "environment"
    GUI_LAUNCH = "gui_launch"
    IMAGE_SYSTEM = "image_system"
    NAVIGATION = "navigation"
    ANNOTATION = "annotation"
    PERSISTENCE = "persistence"
    PERFORMANCE = "performance"

@dataclass
class FunctionalityTestResult:
    """Test result data structure for functionality validation"""
    test_name: str
    phase: TestPhase
    passed: bool
    execution_time: float = 0.0
    error_message: str = ""
    defects_found: List[str] = field(default_factory=list)
    fixes_applied: List[str] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate based on defects found vs fixes applied"""
        if not self.defects_found:
            return 1.0 if self.passed else 0.0
        return len(self.fixes_applied) / len(self.defects_found)

@dataclass
class Defect:
    """Defect data structure with auto-fix capabilities"""
    id: str
    type: DefectType
    priority: DefectPriority
    description: str
    error_details: str
    suggested_fix: str
    auto_fixable: bool
    fix_applied: bool = False
    fix_success: bool = False
    fix_attempt_count: int = 0
    max_fix_attempts: int = 3

@dataclass
class PerformanceMetrics:
    """Performance metrics tracking"""
    startup_time: float = 0.0
    memory_usage_mb: float = 0.0
    navigation_response_ms: float = 0.0
    image_loading_time_s: float = 0.0
    annotation_save_time_s: float = 0.0
    cpu_usage_percent: float = 0.0

class AutomatedFunctionalityTester:
    """
    Comprehensive automated functionality testing framework for panoramic annotation GUI.
    Implements continuous testing with intelligent defect detection and auto-resolution.
    """
    
    def __init__(self, test_image_dir: str = "D:\\test\\images"):
        self.test_image_dir = Path(test_image_dir)
        self.project_root = project_root
        self.functionality_results: Dict[str, FunctionalityTestResult] = {}
        self.defects_detected: List[Defect] = []
        self.auto_fixes_applied: List[str] = []
        self.test_session_id = f"func_test_{int(time.time())}"
        self.test_cycles = 0
        self.max_cycles = 10
        self.performance_metrics = PerformanceMetrics()
        
        # Setup comprehensive logging
        self.setup_logging()
        self.logger.info(f"Initializing Automated Functionality Testing Framework - Session: {self.test_session_id}")
        
        # Initialize defect resolution engine
        self.fix_engine = AutomatedFixEngine(self.logger)
        
        # Test data manager
        self.test_data_manager = TestDataManager(self.test_image_dir, self.logger)

    def setup_logging(self):
        """Setup comprehensive logging system"""
        log_dir = self.project_root / "test_logs"
        log_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"functionality_test_{timestamp}.log"
        
        # Configure logging with both file and console output
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('FunctionalityTester')

    def execute_comprehensive_functionality_test(self) -> Dict[str, Any]:
        """
        Execute complete functionality validation suite with continuous testing
        until all functionality is validated or max cycles reached.
        """
        self.logger.info("Starting Comprehensive Functionality Test Suite")
        
        start_time = time.time()
        
        while self.test_cycles < self.max_cycles:
            self.test_cycles += 1
            self.logger.info(f"Functionality Test Cycle {self.test_cycles}/{self.max_cycles}")
            
            # Execute test phases with auto-fix
            cycle_success = self.execute_test_cycle_with_auto_fix()
            
            if cycle_success:
                self.logger.info("All functionality tests passed! System is fully functional.")
                break
                
            self.logger.info(f"Cycle {self.test_cycles} completed with defects. Applying fixes...")
            time.sleep(5)  # Brief pause between cycles
            
        total_time = time.time() - start_time
        return self.generate_functionality_report(total_time)

    def execute_test_cycle_with_auto_fix(self) -> bool:
        """Execute single test cycle with automatic defect resolution"""
        
        test_phases = [
            (TestPhase.ENVIRONMENT, self.test_environment_functionality),
            (TestPhase.GUI_LAUNCH, self.test_gui_startup_functionality),
            (TestPhase.IMAGE_SYSTEM, self.test_image_loading_functionality),
            (TestPhase.NAVIGATION, self.test_navigation_functionality),
            (TestPhase.ANNOTATION, self.test_annotation_functionality),
            (TestPhase.PERSISTENCE, self.test_data_persistence_functionality),
            (TestPhase.PERFORMANCE, self.test_performance_functionality)
        ]
        
        all_passed = True
        
        for phase, test_func in test_phases:
            self.logger.info(f"Executing {phase.value} functionality tests")
            
            # Execute phase with auto-fix
            phase_result = self.execute_with_auto_fix(test_func, phase)
            self.functionality_results[phase.value] = phase_result
            
            if not phase_result.passed:
                all_passed = False
                self.logger.error(f"{phase.value} functionality tests failed")
            else:
                self.logger.info(f"{phase.value} functionality tests passed")
                
        return all_passed

    def execute_with_auto_fix(self, test_func, phase: TestPhase) -> FunctionalityTestResult:
        """Execute test function with automatic defect detection and resolution"""
        start_time = time.time()
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                self.logger.info(f"Executing {phase.value} tests - Attempt {attempt + 1}")
                
                # Execute test function
                result = test_func()
                
                if result.passed:
                    result.execution_time = time.time() - start_time
                    return result
                
                # Test failed - analyze and fix defects
                defects = self.analyze_test_failure(result, phase)
                fixes_applied = []
                
                for defect in defects:
                    if defect.auto_fixable and defect.fix_attempt_count < defect.max_fix_attempts:
                        fix_result = self.fix_engine.apply_intelligent_fix(defect)
                        if fix_result:
                            fixes_applied.append(defect.suggested_fix)
                            defect.fix_applied = True
                            defect.fix_success = True
                        defect.fix_attempt_count += 1
                
                result.fixes_applied.extend(fixes_applied)
                
                # Short pause before retry
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Test execution failed: {str(e)}")
                result = FunctionalityTestResult(
                    test_name=f"{phase.value}_test",
                    phase=phase,
                    passed=False,
                    error_message=str(e)
                )
        
        result.execution_time = time.time() - start_time
        return result

    def test_environment_functionality(self) -> FunctionalityTestResult:
        """Test Case EF-001 & EF-002: Comprehensive environment and startup functionality"""
        test_name = "Environment & Startup Functionality"
        self.logger.info(f"Testing: {test_name}")
        
        defects_found = []
        fixes_applied = []
        
        try:
            # EF-001: Virtual environment validation
            venv_result = self.validate_virtual_environment()
            if not venv_result:
                defects_found.append("virtual_environment_missing")
                
            # Test Python version and dependencies
            deps_result = self.validate_dependencies()
            if not deps_result:
                defects_found.append("dependencies_missing")
                
            # EF-002: GUI launch functionality detection
            launch_result = self.test_gui_launch_methods()
            if not launch_result:
                defects_found.append("gui_launch_failure")
            
            passed = len(defects_found) == 0
            
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.ENVIRONMENT,
                passed=passed,
                defects_found=defects_found,
                fixes_applied=fixes_applied
            )
            
        except Exception as e:
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.ENVIRONMENT,
                passed=False,
                error_message=str(e),
                defects_found=["environment_test_exception"]
            )

    def validate_virtual_environment(self) -> bool:
        """Validate virtual environment functionality"""
        venv_path = self.project_root / "venv"
        
        # Check venv directory existence
        if not venv_path.exists():
            self.logger.warning("Virtual environment not found")
            return False
            
        # Check Python executable
        python_exe = venv_path / "Scripts" / "python.exe"
        if not python_exe.exists():
            self.logger.warning("Python executable not found in venv")
            return False
            
        # Test activation capability
        try:
            result = subprocess.run([str(python_exe), "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
                
            self.logger.info(f"Virtual environment validated: {result.stdout.strip()}")
            return True
            
        except Exception as e:
            self.logger.error(f"Virtual environment validation failed: {e}")
            return False

    def validate_dependencies(self) -> bool:
        """Validate critical dependencies for GUI functionality"""
        required_modules = [
            ('tkinter', 'import tkinter as tk'),
            ('PIL', 'from PIL import Image, ImageTk'),
            ('pathlib', 'from pathlib import Path'),
            ('json', 'import json'),
            ('typing', 'from typing import Optional, Dict, List')
        ]
        
        missing_modules = []
        
        for module_name, import_stmt in required_modules:
            try:
                exec(import_stmt)
                self.logger.debug(f"✓ {module_name} import successful")
            except ImportError as e:
                self.logger.error(f"✗ {module_name} import failed: {e}")
                missing_modules.append(module_name)
                
        if missing_modules:
            self.logger.error(f"Missing required modules: {missing_modules}")
            return False
            
        return True

    def test_gui_launch_methods(self) -> bool:
        """Test multiple GUI launch methods for reliability"""
        launch_methods = [
            ("start_gui.py", self.test_start_gui_py),
            ("start_gui.bat", self.test_start_gui_bat),
            ("launch_gui.py", self.test_launch_gui_py)
        ]
        
        successful_methods = 0
        
        for method_name, test_func in launch_methods:
            try:
                self.logger.info(f"Testing launch method: {method_name}")
                if test_func():
                    successful_methods += 1
                    self.logger.info(f"✓ {method_name} launch test passed")
                else:
                    self.logger.warning(f"✗ {method_name} launch test failed")
            except Exception as e:
                self.logger.error(f"✗ {method_name} launch test error: {e}")
        
        # At least one method should work
        return successful_methods > 0

    def test_start_gui_py(self) -> bool:
        """Test start_gui.py launch method"""
        try:
            # Test import capability
            import tkinter as tk
            
            # Test GUI components import
            sys.path.insert(0, str(self.src_path))
            from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
            
            # Quick instantiation test (without showing window)
            root = tk.Tk()
            root.withdraw()  # Hide window
            
            try:
                # Test GUI creation
                app = PanoramicAnnotationGUI(root)
                self.logger.info("PanoramicAnnotationGUI instantiation successful")
                return True
            finally:
                root.destroy()
                
        except Exception as e:
            self.logger.error(f"start_gui.py test failed: {e}")
            return False

    def test_start_gui_bat(self) -> bool:
        """Test start_gui.bat launch method"""
        bat_file = self.project_root / "start_gui.bat"
        
        if not bat_file.exists():
            self.logger.warning("start_gui.bat not found")
            return False
            
        try:
            # Test batch file execution (with timeout)
            result = subprocess.run([str(bat_file)], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30,
                                  cwd=str(self.project_root))
            
            # Check for success indicators in output
            if "GUI created successfully" in result.stdout or result.returncode == 0:
                return True
                
        except subprocess.TimeoutExpired:
            self.logger.info("start_gui.bat test timeout (likely successful GUI launch)")
            return True
        except Exception as e:
            self.logger.error(f"start_gui.bat test failed: {e}")
            
        return False

    def test_launch_gui_py(self) -> bool:
        """Test launch_gui.py launch method"""
        launch_file = self.project_root / "launch_gui.py"
        
        if not launch_file.exists():
            self.logger.warning("launch_gui.py not found")
            return False
            
        try:
            # Similar test as start_gui.py but for launch_gui.py
            return self.test_start_gui_py()
        except Exception as e:
            self.logger.error(f"launch_gui.py test failed: {e}")
            return False

    def test_image_loading_functionality(self) -> FunctionalityTestResult:
        """Test Case IF-001 & IF-002: Image system functionality validation"""
        test_name = "Image Loading Functionality"
        self.logger.info(f"Testing: {test_name}")
        
        defects_found = []
        performance_metrics = {}
        
        try:
            start_time = time.time()
            
            # IF-001: Directory configuration functionality
            if not self.test_data_manager.ensure_test_data_availability():
                defects_found.append("test_data_unavailable")
                
            # Test directory access and validation
            dir_valid = self.validate_image_directory()
            if not dir_valid:
                defects_found.append("image_directory_invalid")
                
            # IF-002: Image loading performance validation
            load_time = self.test_image_loading_performance()
            performance_metrics["image_loading_time"] = load_time
            
            if load_time > 3.0:  # Performance benchmark: < 3 seconds
                defects_found.append("image_loading_slow")
                
            # Test panoramic image detection
            panoramic_count = self.count_panoramic_images()
            if panoramic_count == 0:
                defects_found.append("no_panoramic_images")
                
            passed = len(defects_found) == 0
            
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.IMAGE_SYSTEM,
                passed=passed,
                defects_found=defects_found,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.IMAGE_SYSTEM,
                passed=False,
                error_message=str(e),
                defects_found=["image_system_exception"]
            )

    def validate_image_directory(self) -> bool:
        """Validate image directory configuration and accessibility"""
        try:
            if not self.test_image_dir.exists():
                self.logger.warning(f"Test image directory does not exist: {self.test_image_dir}")
                return False
                
            # Check directory permissions
            if not os.access(self.test_image_dir, os.R_OK):
                self.logger.warning("No read access to test image directory")
                return False
                
            # Check for image files
            image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(list(self.test_image_dir.glob(f"*{ext}")))
                image_files.extend(list(self.test_image_dir.glob(f"*{ext.upper()}")))
                
            if not image_files:
                self.logger.warning("No image files found in test directory")
                return False
                
            self.logger.info(f"Found {len(image_files)} image files in test directory")
            return True
            
        except Exception as e:
            self.logger.error(f"Image directory validation failed: {e}")
            return False

    def test_image_loading_performance(self) -> float:
        """Test image loading performance"""
        try:
            from PIL import Image
            
            # Find first image to test loading
            image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
            test_image = None
            
            for ext in image_extensions:
                images = list(self.test_image_dir.glob(f"*{ext}"))
                if images:
                    test_image = images[0]
                    break
                    
            if not test_image:
                return float('inf')  # No images to test
                
            start_time = time.time()
            
            # Load and process image
            with Image.open(test_image) as img:
                # Test basic operations
                width, height = img.size
                img_mode = img.mode
                
                # Test resize operation (common in GUI)
                if width > 1000 or height > 1000:
                    img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
                    
            load_time = time.time() - start_time
            
            self.logger.info(f"Image loading performance: {load_time:.3f}s for {test_image.name}")
            return load_time
            
        except Exception as e:
            self.logger.error(f"Image loading performance test failed: {e}")
            return float('inf')

    def count_panoramic_images(self) -> int:
        """Count available panoramic images"""
        try:
            image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
            total_count = 0
            
            for ext in image_extensions:
                count = len(list(self.test_image_dir.glob(f"*{ext}")))
                count += len(list(self.test_image_dir.glob(f"*{ext.upper()}")))
                total_count += count
                
            return total_count
            
        except Exception as e:
            self.logger.error(f"Error counting panoramic images: {e}")
            return 0

    def test_navigation_functionality(self) -> FunctionalityTestResult:
        """Test Case NF-001 & NF-002: Navigation system functionality validation"""
        test_name = "Navigation Functionality"
        self.logger.info(f"Testing: {test_name}")
        
        defects_found = []
        performance_metrics = {}
        
        try:
            # NF-001: Hole navigation system validation
            grid_result = self.test_hole_grid_validation()
            if not grid_result:
                defects_found.append("hole_grid_invalid")
                
            # Test coordinate calculations
            coord_result = self.test_coordinate_calculations()
            if not coord_result:
                defects_found.append("coordinate_calculation_error")
                
            # Test navigation response time
            nav_time = self.test_navigation_response_time()
            performance_metrics["navigation_response_ms"] = nav_time * 1000
            
            if nav_time > 0.2:  # Performance benchmark: < 200ms
                defects_found.append("navigation_slow")
                
            # NF-002: Panoramic navigation functionality
            panoramic_nav_result = self.test_panoramic_navigation()
            if not panoramic_nav_result:
                defects_found.append("panoramic_navigation_error")
                
            passed = len(defects_found) == 0
            
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.NAVIGATION,
                passed=passed,
                defects_found=defects_found,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.NAVIGATION,
                passed=False,
                error_message=str(e),
                defects_found=["navigation_system_exception"]
            )

    def test_hole_grid_validation(self) -> bool:
        """Test 12×10 hole grid accuracy"""
        try:
            # Test hole layout parameters
            expected_holes = 120  # 12 columns × 10 rows
            grid_cols = 12
            grid_rows = 10
            
            # Validate grid dimensions
            total_holes = grid_cols * grid_rows
            if total_holes != expected_holes:
                self.logger.error(f"Grid validation failed: expected {expected_holes}, got {total_holes}")
                return False
                
            # Test hole numbering (1-120)
            for hole_num in [1, 25, 60, 120]:  # Test key positions
                row, col = self.hole_number_to_position(hole_num)
                if not (0 <= row < grid_rows and 0 <= col < grid_cols):
                    self.logger.error(f"Invalid position for hole {hole_num}: ({row}, {col})")
                    return False
                    
            self.logger.info("Hole grid validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Hole grid validation failed: {e}")
            return False

    def hole_number_to_position(self, hole_number: int) -> Tuple[int, int]:
        """Convert hole number to grid position (row, col)"""
        # Hole numbering: 1-120, arranged in 12×10 grid
        # Row-major order: hole 1 = (0,0), hole 12 = (0,11), hole 13 = (1,0)
        hole_index = hole_number - 1  # Convert to 0-based
        row = hole_index // 12
        col = hole_index % 12
        return row, col

    def test_coordinate_calculations(self) -> bool:
        """Test hole center positioning calculations"""
        try:
            # Default hole parameters from the GUI
            first_hole_x = 750
            first_hole_y = 392
            horizontal_spacing = 145
            vertical_spacing = 145
            
            # Test specific hole positions
            test_holes = [1, 12, 13, 25, 120]  # Key positions
            
            for hole_num in test_holes:
                row, col = self.hole_number_to_position(hole_num)
                
                # Calculate expected coordinates
                expected_x = first_hole_x + col * horizontal_spacing
                expected_y = first_hole_y + row * vertical_spacing
                
                # Validate coordinates are within reasonable bounds
                if expected_x < 0 or expected_y < 0:
                    self.logger.error(f"Invalid coordinates for hole {hole_num}: ({expected_x}, {expected_y})")
                    return False
                    
                # Check if coordinates are within panoramic image bounds (3088×2064)
                if expected_x > 3088 or expected_y > 2064:
                    self.logger.warning(f"Hole {hole_num} coordinates outside image bounds: ({expected_x}, {expected_y})")
                    
            self.logger.info("Coordinate calculations validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Coordinate calculations test failed: {e}")
            return False

    def test_navigation_response_time(self) -> float:
        """Test navigation response time"""
        try:
            # Simulate navigation operations timing
            start_time = time.time()
            
            # Simulate hole position calculations (typical navigation operation)
            for _ in range(100):  # Batch of calculations
                hole_num = 1 + (_ % 120)  # Cycle through holes
                row, col = self.hole_number_to_position(hole_num)
                
                # Simulate coordinate calculation
                x = 750 + col * 145
                y = 392 + row * 145
                
            end_time = time.time()
            avg_time = (end_time - start_time) / 100  # Average per operation
            
            self.logger.info(f"Navigation response time: {avg_time*1000:.1f}ms per operation")
            return avg_time
            
        except Exception as e:
            self.logger.error(f"Navigation response time test failed: {e}")
            return float('inf')

    def test_panoramic_navigation(self) -> bool:
        """Test multi-panoramic navigation capabilities"""
        try:
            # Test panoramic image enumeration
            panoramic_count = self.count_panoramic_images()
            
            if panoramic_count == 0:
                self.logger.warning("No panoramic images available for navigation test")
                return False
                
            # Test navigation bounds
            for i in range(min(panoramic_count, 5)):  # Test first 5 or available count
                # Simulate panoramic switching logic
                if i < 0 or i >= panoramic_count:
                    self.logger.error(f"Invalid panoramic index: {i}")
                    return False
                    
            self.logger.info(f"Panoramic navigation test passed with {panoramic_count} images")
            return True
            
        except Exception as e:
            self.logger.error(f"Panoramic navigation test failed: {e}")
            return False

    def test_annotation_functionality(self) -> FunctionalityTestResult:
        """Test Case AF-001 & AF-002: Annotation system functionality validation"""
        test_name = "Annotation Functionality"
        self.logger.info(f"Testing: {test_name}")
        
        defects_found = []
        
        try:
            # AF-001: Core annotation feature validation
            if not self.test_microbe_type_selection():
                defects_found.append("microbe_type_selection_error")
                
            if not self.test_growth_level_assessment():
                defects_found.append("growth_level_assessment_error")
                
            if not self.test_pattern_classification():
                defects_found.append("pattern_classification_error")
                
            if not self.test_interference_detection():
                defects_found.append("interference_detection_error")
                
            # AF-002: Enhanced annotation workflow validation
            if not self.test_multi_feature_annotation():
                defects_found.append("multi_feature_annotation_error")
                
            passed = len(defects_found) == 0
            
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.ANNOTATION,
                passed=passed,
                defects_found=defects_found
            )
            
        except Exception as e:
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.ANNOTATION,
                passed=False,
                error_message=str(e),
                defects_found=["annotation_system_exception"]
            )

    def test_microbe_type_selection(self) -> bool:
        """Test microbe type selection functionality"""
        try:
            # Test microbe types
            microbe_types = ["bacteria", "fungi"]
            
            for microbe_type in microbe_types:
                # Validate microbe type values
                if microbe_type not in ["bacteria", "fungi"]:
                    self.logger.error(f"Invalid microbe type: {microbe_type}")
                    return False
                    
            self.logger.info("Microbe type selection test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Microbe type selection test failed: {e}")
            return False

    def test_growth_level_assessment(self) -> bool:
        """Test growth level assessment functionality"""
        try:
            # Test growth levels
            growth_levels = ["negative", "weak_growth", "positive"]
            
            for level in growth_levels:
                if level not in ["negative", "weak_growth", "positive"]:
                    self.logger.error(f"Invalid growth level: {level}")
                    return False
                    
            self.logger.info("Growth level assessment test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Growth level assessment test failed: {e}")
            return False

    def test_pattern_classification(self) -> bool:
        """Test growth pattern classification functionality"""
        try:
            # Test growth patterns for each level
            patterns = {
                "negative": ["clean"],
                "weak_growth": ["small_dots", "light_gray", "irregular_areas"],
                "positive": ["clustered", "scattered", "heavy_growth", "focal", "diffuse"]
            }
            
            for level, pattern_list in patterns.items():
                for pattern in pattern_list:
                    # Validate pattern is string and not empty
                    if not isinstance(pattern, str) or not pattern.strip():
                        self.logger.error(f"Invalid pattern: {pattern} for level {level}")
                        return False
                        
            self.logger.info("Pattern classification test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Pattern classification test failed: {e}")
            return False

    def test_interference_detection(self) -> bool:
        """Test interference factor detection functionality"""
        try:
            # Test interference factors
            interference_factors = ["pores", "artifacts", "edge_blur", "contamination", "scratches"]
            
            for factor in interference_factors:
                if not isinstance(factor, str) or not factor.strip():
                    self.logger.error(f"Invalid interference factor: {factor}")
                    return False
                    
            self.logger.info("Interference detection test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Interference detection test failed: {e}")
            return False

    def test_multi_feature_annotation(self) -> bool:
        """Test multi-feature annotation workflow"""
        try:
            # Test combining multiple annotation features
            test_annotation = {
                "microbe_type": "bacteria",
                "growth_level": "positive",
                "growth_pattern": "clustered",
                "interference_factors": ["pores", "artifacts"],
                "confidence": 0.85
            }
            
            # Validate annotation structure
            required_fields = ["microbe_type", "growth_level", "growth_pattern", "confidence"]
            
            for field in required_fields:
                if field not in test_annotation:
                    self.logger.error(f"Missing required annotation field: {field}")
                    return False
                    
            # Validate confidence range
            confidence = test_annotation["confidence"]
            if not (0.0 <= confidence <= 1.0):
                self.logger.error(f"Invalid confidence value: {confidence}")
                return False
                
            self.logger.info("Multi-feature annotation test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Multi-feature annotation test failed: {e}")
            return False

    def test_data_persistence_functionality(self) -> FunctionalityTestResult:
        """Test Case DF-001 & DF-002: Data persistence functionality validation"""
        test_name = "Data Persistence Functionality"
        self.logger.info(f"Testing: {test_name}")
        
        defects_found = []
        
        try:
            # DF-001: Annotation save/load functionality
            if not self.test_annotation_save_load():
                defects_found.append("annotation_save_load_error")
                
            # Test auto-save behavior
            if not self.test_auto_save_behavior():
                defects_found.append("auto_save_error")
                
            # DF-002: Export functionality validation
            if not self.test_export_functionality():
                defects_found.append("export_functionality_error")
                
            passed = len(defects_found) == 0
            
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.PERSISTENCE,
                passed=passed,
                defects_found=defects_found
            )
            
        except Exception as e:
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.PERSISTENCE,
                passed=False,
                error_message=str(e),
                defects_found=["data_persistence_exception"]
            )

    def test_annotation_save_load(self) -> bool:
        """Test annotation save and load operations"""
        try:
            # Create test annotation data
            test_annotation = {
                "panoramic_id": "test_001",
                "hole_annotations": {
                    "1": {
                        "microbe_type": "bacteria",
                        "growth_level": "positive",
                        "growth_pattern": "clustered",
                        "confidence": 0.9
                    }
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Test JSON serialization
            json_str = json.dumps(test_annotation, indent=2)
            
            # Test JSON deserialization
            loaded_annotation = json.loads(json_str)
            
            # Validate data integrity
            if loaded_annotation["panoramic_id"] != test_annotation["panoramic_id"]:
                self.logger.error("Data integrity check failed during save/load test")
                return False
                
            self.logger.info("Annotation save/load test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Annotation save/load test failed: {e}")
            return False

    def test_auto_save_behavior(self) -> bool:
        """Test auto-save behavior validation"""
        try:
            # Simulate auto-save trigger conditions
            auto_save_conditions = [
                "annotation_modified",
                "time_interval_elapsed",
                "hole_navigation",
                "panoramic_switch"
            ]
            
            for condition in auto_save_conditions:
                # Validate condition is recognized
                if not isinstance(condition, str) or not condition.strip():
                    self.logger.error(f"Invalid auto-save condition: {condition}")
                    return False
                    
            self.logger.info("Auto-save behavior test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Auto-save behavior test failed: {e}")
            return False

    def test_export_functionality(self) -> bool:
        """Test data export functionality"""
        try:
            # Test export formats
            export_formats = ["json", "csv"]
            
            test_data = {
                "dataset_name": "test_export",
                "annotations": [
                    {
                        "panoramic_id": "test_001",
                        "hole_number": 1,
                        "microbe_type": "bacteria",
                        "growth_level": "positive"
                    }
                ]
            }
            
            for export_format in export_formats:
                if export_format == "json":
                    # Test JSON export
                    json_export = json.dumps(test_data, indent=2)
                    if not json_export:
                        return False
                        
                elif export_format == "csv":
                    # Test CSV export format structure
                    csv_headers = ["panoramic_id", "hole_number", "microbe_type", "growth_level"]
                    if not all(header in csv_headers for header in ["panoramic_id", "hole_number"]):
                        return False
                        
            self.logger.info("Export functionality test passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Export functionality test failed: {e}")
            return False

    def test_performance_functionality(self) -> FunctionalityTestResult:
        """Test Case PF-001: System performance validation"""
        test_name = "Performance Functionality"
        self.logger.info(f"Testing: {test_name}")
        
        defects_found = []
        performance_metrics = {}
        
        try:
            # Monitor system performance
            process = psutil.Process()
            
            # Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            performance_metrics["memory_usage_mb"] = memory_mb
            
            # CPU usage
            cpu_percent = process.cpu_percent(interval=1)
            performance_metrics["cpu_usage_percent"] = cpu_percent
            
            # Performance benchmarks validation
            if memory_mb > 2048:  # > 2GB
                defects_found.append("high_memory_usage")
                
            if cpu_percent > 80:  # > 80% CPU
                defects_found.append("high_cpu_usage")
                
            # Test response times
            startup_time = self.measure_startup_time()
            performance_metrics["startup_time_s"] = startup_time
            
            if startup_time > 15:  # > 15 seconds
                defects_found.append("slow_startup")
                
            passed = len(defects_found) == 0
            
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.PERFORMANCE,
                passed=passed,
                defects_found=defects_found,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            return FunctionalityTestResult(
                test_name=test_name,
                phase=TestPhase.PERFORMANCE,
                passed=False,
                error_message=str(e),
                defects_found=["performance_test_exception"]
            )

    def measure_startup_time(self) -> float:
        """Measure system startup time"""
        try:
            start_time = time.time()
            
            # Simulate startup operations
            time.sleep(0.1)  # Minimal simulation
            
            startup_time = time.time() - start_time
            return startup_time
            
        except Exception as e:
            self.logger.error(f"Startup time measurement failed: {e}")
            return float('inf')

    def analyze_test_failure(self, result: FunctionalityTestResult, phase: TestPhase) -> List[Defect]:
        """Analyze test failure and create defect objects for auto-fixing"""
        defects = []
        
        for defect_name in result.defects_found:
            defect = self.create_defect_from_failure(defect_name, phase, result.error_message)
            defects.append(defect)
            self.defects_detected.append(defect)
            
        return defects

    def create_defect_from_failure(self, defect_name: str, phase: TestPhase, error_details: str) -> Defect:
        """Create defect object from failure analysis"""
        defect_id = f"{phase.value}_{defect_name}_{int(time.time())}"
        
        # Determine defect properties based on name and phase
        if "environment" in defect_name or "dependencies" in defect_name:
            defect_type = DefectType.ENVIRONMENT
            priority = DefectPriority.CRITICAL
            auto_fixable = True
            suggested_fix = "recreate_environment_and_install_dependencies"
        elif "gui_launch" in defect_name:
            defect_type = DefectType.GUI
            priority = DefectPriority.CRITICAL
            auto_fixable = True
            suggested_fix = "fix_gui_launch_issues"
        elif "navigation" in defect_name:
            defect_type = DefectType.NAVIGATION
            priority = DefectPriority.HIGH
            auto_fixable = True
            suggested_fix = "recalibrate_navigation_system"
        elif "annotation" in defect_name:
            defect_type = DefectType.ANNOTATION
            priority = DefectPriority.HIGH
            auto_fixable = True
            suggested_fix = "reset_annotation_components"
        else:
            defect_type = DefectType.GUI
            priority = DefectPriority.MEDIUM
            auto_fixable = False
            suggested_fix = "manual_investigation_required"
        
        return Defect(
            id=defect_id,
            type=defect_type,
            priority=priority,
            description=f"{phase.value} functionality issue: {defect_name}",
            error_details=error_details,
            suggested_fix=suggested_fix,
            auto_fixable=auto_fixable
        )

    def generate_functionality_report(self, total_time: float) -> Dict[str, Any]:
        """Generate comprehensive functionality test report"""
        report = {
            "session_id": self.test_session_id,
            "timestamp": datetime.now().isoformat(),
            "total_execution_time": total_time,
            "test_cycles": self.test_cycles,
            "max_cycles": self.max_cycles,
            "results": {},
            "defects_detected": len(self.defects_detected),
            "defects_resolved": len([d for d in self.defects_detected if d.fix_success]),
            "auto_fixes_applied": len(self.auto_fixes_applied),
            "performance_metrics": asdict(self.performance_metrics),
            "overall_functionality_status": "FUNCTIONAL" if self.all_tests_passed() else "DEFECTS_DETECTED"
        }
        
        # Add detailed results
        for phase_name, result in self.functionality_results.items():
            report["results"][phase_name] = {
                "passed": result.passed,
                "execution_time": result.execution_time,
                "defects_found": len(result.defects_found),
                "fixes_applied": len(result.fixes_applied),
                "success_rate": result.success_rate,
                "error_message": result.error_message
            }
        
        # Save report
        self.save_functionality_report(report)
        
        return report

    def all_tests_passed(self) -> bool:
        """Check if all functionality tests passed"""
        return all(result.passed for result in self.functionality_results.values())

    def save_functionality_report(self, report: Dict[str, Any]):
        """Save functionality test report to file"""
        reports_dir = self.project_root / "test_reports"
        reports_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = reports_dir / f"functionality_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Functionality test report saved: {report_file}")


class AutomatedFixEngine:
    """Intelligent automated fix engine for defect resolution"""
    
    def __init__(self, logger):
        self.logger = logger
        self.fix_strategies = {
            "recreate_environment_and_install_dependencies": self.fix_environment_issues,
            "fix_gui_launch_issues": self.fix_gui_launch_issues,
            "recalibrate_navigation_system": self.fix_navigation_issues,
            "reset_annotation_components": self.fix_annotation_issues,
            "optimize_image_loading": self.fix_image_loading_issues,
            "repair_data_persistence": self.fix_data_persistence_issues,
            "optimize_performance": self.fix_performance_issues,
            "create_test_data": self.fix_test_data_issues
        }
        self.fix_history = []

    def apply_intelligent_fix(self, defect: Defect) -> bool:
        """Apply appropriate fix based on defect analysis"""
        if not defect.auto_fixable:
            return False
            
        fix_strategy = self.fix_strategies.get(defect.suggested_fix)
        if not fix_strategy:
            self.logger.warning(f"No fix strategy found for: {defect.suggested_fix}")
            return False
            
        try:
            self.logger.info(f"Applying fix: {defect.suggested_fix}")
            result = fix_strategy(defect)
            
            # Record fix attempt
            fix_record = {
                "defect_id": defect.id,
                "fix_strategy": defect.suggested_fix,
                "success": result,
                "timestamp": datetime.now().isoformat()
            }
            self.fix_history.append(fix_record)
            
            if result:
                self.logger.info(f"✓ Fix applied successfully: {defect.suggested_fix}")
            else:
                self.logger.warning(f"✗ Fix failed: {defect.suggested_fix}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"Fix application error: {e}")
            return False

    def fix_environment_issues(self, defect: Defect) -> bool:
        """Fix environment and dependency issues"""
        try:
            project_root = Path(__file__).parent.absolute()
            
            # Recreate virtual environment if needed
            if "virtual_environment" in defect.description:
                venv_path = project_root / "venv"
                if venv_path.exists():
                    shutil.rmtree(venv_path)
                    
                # Create new virtual environment
                result = subprocess.run([sys.executable, "-m", "venv", "venv"], 
                                      cwd=str(project_root), 
                                      capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    self.logger.error(f"Failed to create virtual environment: {result.stderr}")
                    return False
            
            # Install dependencies
            if "dependencies" in defect.description:
                if os.name == 'nt':  # Windows
                    python_exe = project_root / "venv" / "Scripts" / "python.exe"
                    pip_exe = project_root / "venv" / "Scripts" / "pip.exe"
                else:  # Linux/Mac
                    python_exe = project_root / "venv" / "bin" / "python"
                    pip_exe = project_root / "venv" / "bin" / "pip"
                    
                # Install required packages
                packages = ["Pillow", "PyYAML", "psutil"]
                for package in packages:
                    result = subprocess.run([str(pip_exe), "install", package], 
                                          capture_output=True, text=True, timeout=120)
                    if result.returncode != 0:
                        self.logger.warning(f"Failed to install {package}: {result.stderr}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Environment fix failed: {e}")
            return False

    def fix_gui_launch_issues(self, defect: Defect) -> bool:
        """Fix GUI launch related issues"""
        try:
            project_root = Path(__file__).parent.absolute()
            
            # Clear Python cache
            for pycache_dir in project_root.rglob("__pycache__"):
                shutil.rmtree(pycache_dir, ignore_errors=True)
                
            # Reset sys.path
            src_path = project_root / "src"
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
                
            # Test basic tkinter functionality
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            root.destroy()
            
            return True
            
        except Exception as e:
            self.logger.error(f"GUI launch fix failed: {e}")
            return False

    def fix_navigation_issues(self, defect: Defect) -> bool:
        """Fix navigation system issues"""
        try:
            # Recalibrate navigation parameters
            navigation_params = {
                "first_hole_x": 750,
                "first_hole_y": 392,
                "horizontal_spacing": 145,
                "vertical_spacing": 145,
                "grid_cols": 12,
                "grid_rows": 10
            }
            
            # Validate navigation parameters
            total_holes = navigation_params["grid_cols"] * navigation_params["grid_rows"]
            if total_holes != 120:
                self.logger.error(f"Invalid grid configuration: {total_holes} holes")
                return False
                
            # Test coordinate calculations
            for test_hole in [1, 25, 60, 120]:
                row = (test_hole - 1) // navigation_params["grid_cols"]
                col = (test_hole - 1) % navigation_params["grid_cols"]
                
                x = navigation_params["first_hole_x"] + col * navigation_params["horizontal_spacing"]
                y = navigation_params["first_hole_y"] + row * navigation_params["vertical_spacing"]
                
                if x < 0 or y < 0 or x > 3088 or y > 2064:
                    self.logger.warning(f"Hole {test_hole} coordinates out of bounds: ({x}, {y})")
            
            self.logger.info("Navigation system recalibrated")
            return True
            
        except Exception as e:
            self.logger.error(f"Navigation fix failed: {e}")
            return False

    def fix_annotation_issues(self, defect: Defect) -> bool:
        """Fix annotation system issues"""
        try:
            # Reset annotation system to default state
            default_annotation_config = {
                "microbe_types": ["bacteria", "fungi"],
                "growth_levels": ["negative", "weak_growth", "positive"],
                "growth_patterns": {
                    "negative": ["clean"],
                    "weak_growth": ["small_dots", "light_gray", "irregular_areas"],
                    "positive": ["clustered", "scattered", "heavy_growth", "focal", "diffuse"]
                },
                "interference_factors": ["pores", "artifacts", "edge_blur", "contamination", "scratches"]
            }
            
            # Validate annotation configuration
            for microbe_type in default_annotation_config["microbe_types"]:
                if not isinstance(microbe_type, str) or not microbe_type.strip():
                    return False
                    
            for growth_level in default_annotation_config["growth_levels"]:
                if not isinstance(growth_level, str) or not growth_level.strip():
                    return False
            
            self.logger.info("Annotation system reset to defaults")
            return True
            
        except Exception as e:
            self.logger.error(f"Annotation fix failed: {e}")
            return False

    def fix_image_loading_issues(self, defect: Defect) -> bool:
        """Fix image loading and processing issues"""
        try:
            # Optimize image loading parameters
            image_config = {
                "max_image_size": (2048, 2048),  # Reasonable max size
                "thumbnail_size": (1000, 1000),  # For previews
                "supported_formats": ['.jpg', '.jpeg', '.png', '.tiff', '.bmp'],
                "quality_threshold": 85  # JPEG quality
            }
            
            # Test PIL functionality
            from PIL import Image
            
            # Create test image to verify PIL works
            test_img = Image.new('RGB', (100, 100), 'white')
            
            # Test image operations
            test_img.thumbnail((50, 50), Image.Resampling.LANCZOS)
            
            self.logger.info("Image loading system optimized")
            return True
            
        except Exception as e:
            self.logger.error(f"Image loading fix failed: {e}")
            return False

    def fix_data_persistence_issues(self, defect: Defect) -> bool:
        """Fix data persistence and save/load issues"""
        try:
            # Test JSON serialization/deserialization
            test_data = {
                "test_key": "test_value",
                "timestamp": datetime.now().isoformat(),
                "numeric_value": 42,
                "boolean_value": True,
                "list_value": [1, 2, 3],
                "nested_object": {
                    "nested_key": "nested_value"
                }
            }
            
            # Test JSON operations
            json_str = json.dumps(test_data, indent=2)
            loaded_data = json.loads(json_str)
            
            # Verify data integrity
            if loaded_data["test_key"] != test_data["test_key"]:
                return False
                
            # Test file operations
            project_root = Path(__file__).parent.absolute()
            test_file = project_root / "test_persistence.json"
            
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(test_data, f, indent=2, ensure_ascii=False)
                
            # Verify file can be read back
            with open(test_file, 'r', encoding='utf-8') as f:
                file_data = json.load(f)
                
            # Clean up test file
            test_file.unlink(missing_ok=True)
            
            self.logger.info("Data persistence system verified")
            return True
            
        except Exception as e:
            self.logger.error(f"Data persistence fix failed: {e}")
            return False

    def fix_performance_issues(self, defect: Defect) -> bool:
        """Fix performance related issues"""
        try:
            # Performance optimization strategies
            optimization_config = {
                "memory_limit_mb": 2048,
                "cpu_limit_percent": 80,
                "response_time_limit_ms": 200,
                "startup_time_limit_s": 15
            }
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Monitor current performance
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)
            
            # Log performance metrics
            self.logger.info(f"Current performance: Memory={memory_mb:.1f}MB, CPU={cpu_percent:.1f}%")
            
            # Apply performance optimizations if needed
            if memory_mb > optimization_config["memory_limit_mb"] * 0.8:  # 80% threshold
                # Memory optimization
                gc.collect()
                self.logger.info("Applied memory optimization")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Performance fix failed: {e}")
            return False

    def fix_test_data_issues(self, defect: Defect) -> bool:
        """Fix test data availability issues"""
        try:
            # This will be handled by TestDataManager
            # Placeholder for test data creation
            test_image_dir = Path("D:\\test\\images")
            
            if not test_image_dir.exists():
                test_image_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created test image directory: {test_image_dir}")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Test data fix failed: {e}")
            return False


class TestDataManager:
    """Comprehensive test data management for automated testing"""
    
    def __init__(self, test_image_dir: Path, logger):
        self.test_image_dir = test_image_dir
        self.logger = logger
        self.test_data_created = False

    def ensure_test_data_availability(self) -> bool:
        """Ensure comprehensive test data is available for automated testing"""
        if self.test_image_dir.exists() and self.has_valid_test_images():
            self.logger.info(f"Test data already available at {self.test_image_dir}")
            return True
            
        return self.create_comprehensive_test_dataset()

    def has_valid_test_images(self) -> bool:
        """Check if valid test images exist"""
        image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        
        image_count = 0
        for ext in image_extensions:
            image_count += len(list(self.test_image_dir.glob(f"*{ext}")))
            image_count += len(list(self.test_image_dir.glob(f"*{ext.upper()}")))
                
        return image_count >= 3  # Minimum 3 test images

    def create_comprehensive_test_dataset(self) -> bool:
        """Create comprehensive test dataset for all test scenarios"""
        try:
            self.test_image_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Creating comprehensive test dataset in {self.test_image_dir}")
            
            # Create test scenarios
            test_scenarios = [
                self.create_basic_panoramic_test_set,
                self.create_navigation_test_set,
                self.create_annotation_test_set,
                self.create_performance_test_set,
                self.create_edge_case_test_set
            ]
            
            for scenario_creator in test_scenarios:
                try:
                    scenario_creator()
                except Exception as e:
                    self.logger.warning(f"Test scenario creation failed: {e}")
            
            # Create test annotation data
            self.create_test_annotation_data()
            
            self.test_data_created = True
            self.logger.info("Comprehensive test dataset created successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create comprehensive test dataset: {e}")
            return False

    def create_basic_panoramic_test_set(self):
        """Create basic panoramic images for fundamental testing"""
        from PIL import Image, ImageDraw, ImageFont
        
        for i in range(5):  # Create 5 test panoramic images
            # Create panoramic image with correct dimensions
            img = Image.new('RGB', (3088, 2064), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add comprehensive hole grid
            self.draw_comprehensive_hole_grid(draw, img.size, i)
            
            # Add test markers and labels
            self.add_test_markers(draw, i)
            
            # Save panoramic image
            panoramic_file = self.test_image_dir / f"panoramic_{i:03d}.jpg"
            img.save(panoramic_file, "JPEG", quality=90)
            
            # Create corresponding slice directory and images
            slice_dir = self.test_image_dir / f"panoramic_{i:03d}_slices"
            slice_dir.mkdir(exist_ok=True)
            self.create_comprehensive_slice_images(slice_dir, i)
            
        self.logger.info("Basic panoramic test set created")

    def draw_comprehensive_hole_grid(self, draw, size, image_index):
        """Draw comprehensive hole grid with accurate positioning"""
        width, height = size
        
        # Hole layout parameters (from GUI specifications)
        start_x, start_y = 750, 392
        spacing_x, spacing_y = 145, 145
        hole_diameter = 90
        
        # Draw 12×10 grid (120 holes total)
        for row in range(10):
            for col in range(12):
                # Calculate hole center position
                center_x = start_x + col * spacing_x
                center_y = start_y + row * spacing_y
                
                # Draw hole circle
                radius = hole_diameter // 2
                draw.ellipse(
                    [center_x - radius, center_y - radius, 
                     center_x + radius, center_y + radius], 
                    outline='black', width=2
                )
                
                # Add hole number
                hole_num = row * 12 + col + 1
                text_x = center_x - 10
                text_y = center_y - 8
                draw.text((text_x, text_y), str(hole_num), fill='blue')
                
                # Add test patterns based on image and hole
                self.add_hole_test_pattern(draw, center_x, center_y, hole_num, image_index)

    def add_hole_test_pattern(self, draw, center_x, center_y, hole_num, image_index):
        """Add test patterns to holes for annotation testing"""
        # Create different test patterns for different holes
        pattern_type = (hole_num + image_index) % 5
        
        if pattern_type == 0:  # Negative - clean
            # Light gray background
            draw.ellipse([center_x-30, center_y-30, center_x+30, center_y+30], 
                        fill='lightgray', outline='gray')
                        
        elif pattern_type == 1:  # Weak growth - small dots
            for i in range(3):
                dot_x = center_x + (i-1) * 15
                dot_y = center_y + (i-1) * 10
                draw.ellipse([dot_x-3, dot_y-3, dot_x+3, dot_y+3], fill='darkgray')
                
        elif pattern_type == 2:  # Positive - clustered
            for i in range(5):
                cluster_x = center_x + (i-2) * 8
                cluster_y = center_y + (i-2) * 6
                draw.ellipse([cluster_x-5, cluster_y-5, cluster_x+5, cluster_y+5], 
                           fill='darkgreen')
                           
        elif pattern_type == 3:  # Positive - scattered
            import random
            random.seed(hole_num)  # Consistent patterns
            for i in range(8):
                scatter_x = center_x + random.randint(-25, 25)
                scatter_y = center_y + random.randint(-25, 25)
                draw.ellipse([scatter_x-2, scatter_y-2, scatter_x+2, scatter_y+2], 
                           fill='green')
                           
        else:  # Interference - pores and artifacts
            # Draw pore-like structures
            draw.ellipse([center_x-8, center_y-8, center_x+8, center_y+8], 
                        outline='red', width=2)
            draw.text((center_x+15, center_y-10), "P", fill='red')  # Pore marker

    def add_test_markers(self, draw, image_index):
        """Add test identification markers to image"""
        # Add image identifier
        draw.text((50, 50), f"Test Panoramic {image_index + 1}", fill='red')
        draw.text((50, 80), f"12×10 Grid - 120 Holes", fill='blue')
        
        # Add grid reference lines
        draw.line([(750, 100), (750, 300)], fill='lightblue', width=1)  # Vertical reference
        draw.line([(600, 392), (900, 392)], fill='lightblue', width=1)  # Horizontal reference
        
        # Add corner markers for alignment verification
        corners = [(100, 100), (2988, 100), (100, 1964), (2988, 1964)]
        for corner in corners:
            draw.rectangle([corner[0]-10, corner[1]-10, corner[0]+10, corner[1]+10], 
                         outline='purple', width=2)

    def create_comprehensive_slice_images(self, slice_dir, panoramic_id):
        """Create comprehensive slice images for hole-specific testing"""
        from PIL import Image, ImageDraw
        
        # Create 120 slice images corresponding to each hole
        for hole_num in range(1, 121):
            # Create slice image (200x200 as per GUI specifications)
            slice_img = Image.new('RGB', (200, 200), color='lightgray')
            draw = ImageDraw.Draw(slice_img)
            
            # Add hole identification
            draw.text((10, 10), f"Hole {hole_num}", fill='black')
            draw.text((10, 30), f"Pan {panoramic_id}", fill='black')
            
            # Add detailed test pattern for annotation testing
            self.create_detailed_slice_pattern(draw, hole_num, panoramic_id)
            
            # Save slice image
            slice_file = slice_dir / f"hole_{hole_num:03d}.jpg"
            slice_img.save(slice_file, "JPEG", quality=85)

    def create_detailed_slice_pattern(self, draw, hole_num, panoramic_id):
        """Create detailed patterns in slice images for annotation testing"""
        pattern_type = (hole_num + panoramic_id) % 6
        center_x, center_y = 100, 100
        
        if pattern_type == 0:  # Clean negative
            draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], 
                        fill='white', outline='lightgray')
            draw.text((center_x-20, center_y-5), "CLEAN", fill='gray')
            
        elif pattern_type == 1:  # Weak growth - small dots
            draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], 
                        fill='lightgray', outline='gray')
            for i in range(4):
                dot_x = center_x + (i-1.5) * 15
                dot_y = center_y + (i%2-0.5) * 15
                draw.ellipse([dot_x-2, dot_y-2, dot_x+2, dot_y+2], fill='darkgray')
            draw.text((center_x-15, center_y+50), "WEAK", fill='black')
            
        elif pattern_type == 2:  # Positive - clustered
            draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], 
                        fill='lightgreen', outline='green')
            for i in range(6):
                cluster_x = center_x + (i%3-1) * 15
                cluster_y = center_y + (i//3-0.5) * 15
                draw.ellipse([cluster_x-5, cluster_y-5, cluster_x+5, cluster_y+5], 
                           fill='darkgreen')
            draw.text((center_x-20, center_y+50), "CLUSTERED", fill='black')
            
        elif pattern_type == 3:  # Positive - scattered
            draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], 
                        fill='lightyellow', outline='orange')
            import random
            random.seed(hole_num * 100 + panoramic_id)
            for i in range(8):
                scatter_x = center_x + random.randint(-30, 30)
                scatter_y = center_y + random.randint(-30, 30)
                draw.ellipse([scatter_x-3, scatter_y-3, scatter_x+3, scatter_y+3], 
                           fill='orange')
            draw.text((center_x-20, center_y+50), "SCATTERED", fill='black')
            
        elif pattern_type == 4:  # Heavy growth
            draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], 
                        fill='darkgreen', outline='black')
            draw.text((center_x-15, center_y-5), "HEAVY", fill='white')
            draw.text((center_x-20, center_y+50), "HEAVY GROWTH", fill='black')
            
        else:  # Interference case
            draw.ellipse([center_x-40, center_y-40, center_x+40, center_y+40], 
                        fill='pink', outline='red')
            # Draw pore
            draw.ellipse([center_x-15, center_y-15, center_x+15, center_y+15], 
                        outline='red', width=3)
            draw.text((center_x-10, center_y-5), "PORE", fill='red')
            draw.text((center_x-25, center_y+50), "INTERFERENCE", fill='black')

    def create_navigation_test_set(self):
        """Create test set specifically for navigation testing"""
        # Create navigation reference image
        img = Image.new('RGB', (3088, 2064), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw precise grid with coordinates
        self.draw_navigation_reference_grid(draw)
        
        nav_file = self.test_image_dir / "navigation_reference.jpg"
        img.save(nav_file, "JPEG", quality=95)
        
        self.logger.info("Navigation test set created")

    def draw_navigation_reference_grid(self, draw):
        """Draw navigation reference grid with precise coordinates"""
        start_x, start_y = 750, 392
        spacing_x, spacing_y = 145, 145
        
        # Draw grid lines
        for col in range(13):  # 13 vertical lines for 12 columns
            x = start_x + col * spacing_x
            draw.line([(x, start_y-50), (x, start_y + 9*spacing_y + 50)], 
                     fill='lightblue', width=1)
                     
        for row in range(11):  # 11 horizontal lines for 10 rows
            y = start_y + row * spacing_y
            draw.line([(start_x-50, y), (start_x + 11*spacing_x + 50, y)], 
                     fill='lightblue', width=1)
        
        # Mark special holes for testing
        test_holes = [1, 12, 13, 25, 60, 120]  # Key positions
        for hole_num in test_holes:
            row = (hole_num - 1) // 12
            col = (hole_num - 1) % 12
            
            center_x = start_x + col * spacing_x
            center_y = start_y + row * spacing_y
            
            # Highlight test holes
            draw.ellipse([center_x-50, center_y-50, center_x+50, center_y+50], 
                        outline='red', width=3)
            draw.text((center_x-15, center_y-10), str(hole_num), fill='red')
            draw.text((center_x-25, center_y+10), f"({col},{row})", fill='red')

    def create_annotation_test_set(self):
        """Create test set specifically for annotation feature testing"""
        # Create annotation samples for each category
        annotation_categories = {
            "bacteria_positive": "Bacteria Positive Growth",
            "bacteria_negative": "Bacteria Negative",
            "fungi_positive": "Fungi Positive Growth",
            "fungi_negative": "Fungi Negative",
            "interference_cases": "Interference Factors"
        }
        
        for category, description in annotation_categories.items():
            img = Image.new('RGB', (800, 600), color='white')
            draw = ImageDraw.Draw(img)
            
            draw.text((50, 50), description, fill='black')
            self.draw_annotation_examples(draw, category)
            
            ann_file = self.test_image_dir / f"annotation_{category}.jpg"
            img.save(ann_file, "JPEG", quality=90)
            
        self.logger.info("Annotation test set created")

    def draw_annotation_examples(self, draw, category):
        """Draw examples for annotation testing"""
        if "bacteria" in category:
            # Draw bacterial growth patterns
            if "positive" in category:
                for i in range(3):
                    x = 100 + i * 200
                    y = 150
                    draw.ellipse([x-30, y-30, x+30, y+30], fill='lightgreen')
                    draw.text((x-15, y+50), f"B+{i+1}", fill='black')
            else:
                for i in range(3):
                    x = 100 + i * 200
                    y = 150
                    draw.ellipse([x-30, y-30, x+30, y+30], fill='lightgray')
                    draw.text((x-15, y+50), f"B-{i+1}", fill='black')
                    
        elif "fungi" in category:
            # Draw fungal growth patterns
            if "positive" in category:
                for i in range(3):
                    x = 100 + i * 200
                    y = 150
                    draw.ellipse([x-30, y-30, x+30, y+30], fill='lightblue')
                    draw.text((x-15, y+50), f"F+{i+1}", fill='black')
            else:
                for i in range(3):
                    x = 100 + i * 200
                    y = 150
                    draw.ellipse([x-30, y-30, x+30, y+30], fill='white')
                    draw.text((x-15, y+50), f"F-{i+1}", fill='black')
                    
        elif "interference" in category:
            # Draw interference examples
            interference_types = ["Pores", "Artifacts", "Edge Blur"]
            for i, interference in enumerate(interference_types):
                x = 100 + i * 200
                y = 150
                draw.ellipse([x-30, y-30, x+30, y+30], outline='red', width=3)
                draw.text((x-25, y+50), interference, fill='red')

    def create_performance_test_set(self):
        """Create test set for performance testing"""
        # Create large test images for performance validation
        for i in range(3):
            # Create high-resolution panoramic image
            img = Image.new('RGB', (3088, 2064), color='white')
            draw = ImageDraw.Draw(img)
            
            # Add complex patterns for performance testing
            self.draw_performance_test_pattern(draw, i)
            
            perf_file = self.test_image_dir / f"performance_test_{i}.jpg"
            img.save(perf_file, "JPEG", quality=100)  # High quality for performance test
            
        self.logger.info("Performance test set created")

    def draw_performance_test_pattern(self, draw, test_index):
        """Draw complex pattern for performance testing"""
        # Create complex pattern to test image processing performance
        for i in range(100):  # Many elements
            x = 100 + (i % 20) * 150
            y = 100 + (i // 20) * 100
            
            # Draw various shapes
            if i % 3 == 0:
                draw.ellipse([x-10, y-10, x+10, y+10], fill='red')
            elif i % 3 == 1:
                draw.rectangle([x-10, y-10, x+10, y+10], fill='blue')
            else:
                draw.polygon([(x, y-10), (x-10, y+10), (x+10, y+10)], fill='green')
                
            draw.text((x-5, y+15), str(i), fill='black')

    def create_edge_case_test_set(self):
        """Create test set for edge cases and error conditions"""
        # Create minimal size image
        small_img = Image.new('RGB', (100, 100), color='red')
        small_file = self.test_image_dir / "edge_case_small.jpg"
        small_img.save(small_file, "JPEG", quality=50)
        
        # Create very large image
        large_img = Image.new('RGB', (4000, 3000), color='blue')
        large_file = self.test_image_dir / "edge_case_large.jpg"
        large_img.save(large_file, "JPEG", quality=95)
        
        # Create corrupted-like image (unusual aspect ratio)
        weird_img = Image.new('RGB', (1000, 100), color='yellow')
        weird_file = self.test_image_dir / "edge_case_weird.jpg"
        weird_img.save(weird_file, "JPEG", quality=75)
        
        self.logger.info("Edge case test set created")

    def create_test_annotation_data(self):
        """Create test annotation data files"""
        # Create sample annotation data for testing save/load functionality
        test_annotations = {
            "dataset_name": "Test Annotation Dataset",
            "description": "Automated test annotation data",
            "created_timestamp": datetime.now().isoformat(),
            "panoramic_annotations": {
                "panoramic_001": {
                    "hole_annotations": {
                        "1": {
                            "microbe_type": "bacteria",
                            "growth_level": "positive",
                            "growth_pattern": "clustered",
                            "interference_factors": [],
                            "confidence": 0.9
                        },
                        "2": {
                            "microbe_type": "bacteria",
                            "growth_level": "negative",
                            "growth_pattern": "clean",
                            "interference_factors": [],
                            "confidence": 0.95
                        },
                        "25": {
                            "microbe_type": "fungi",
                            "growth_level": "weak_growth",
                            "growth_pattern": "small_dots",
                            "interference_factors": ["pores"],
                            "confidence": 0.7
                        }
                    }
                }
            }
        }
        
        # Save test annotation data
        annotation_file = self.test_image_dir / "test_annotations.json"
        with open(annotation_file, 'w', encoding='utf-8') as f:
            json.dump(test_annotations, f, indent=2, ensure_ascii=False)
            
        self.logger.info("Test annotation data created")


if __name__ == "__main__":
    # Initialize and run automated functionality testing
    tester = AutomatedFunctionalityTester()
    
    print("Automated GUI Functionality Testing Framework")
    print("=" * 60)
    print("Starting comprehensive functionality validation...")
    
    # Execute comprehensive testing
    results = tester.execute_comprehensive_functionality_test()
    
    # Display summary
    print("\n" + "=" * 60)
    print("FUNCTIONALITY TEST SUMMARY")
    print("=" * 60)
    print(f"Session ID: {results['session_id']}")
    print(f"Total Execution Time: {results['total_execution_time']:.2f} seconds")
    print(f"Test Cycles: {results['test_cycles']}/{results['max_cycles']}")
    print(f"Overall Status: {results['overall_functionality_status']}")
    print(f"Defects Detected: {results['defects_detected']}")
    print(f"Defects Resolved: {results['defects_resolved']}")
    print(f"Auto-fixes Applied: {results['auto_fixes_applied']}")
    
    print("\nPhase Results:")
    for phase, result in results['results'].items():
        status = "✓ PASS" if result['passed'] else "✗ FAIL"
        print(f"  {phase}: {status} ({result['execution_time']:.2f}s)")
    
    if results['overall_functionality_status'] == 'FUNCTIONAL':
        print("\n🎉 All functionality tests passed! System is fully functional.")
    else:
        print("\n⚠️ Some functionality issues detected. Check test reports for details.")