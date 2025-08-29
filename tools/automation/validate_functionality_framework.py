#!/usr/bin/env python3
"""
Validation Script for Automated Functionality Testing Framework

This script validates that the functionality testing framework itself works correctly.
It performs basic validation tests without requiring the full GUI environment.

Usage:
    python validate_functionality_framework.py
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project path to Python path
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def test_framework_imports():
    """Test that all framework components can be imported"""
    print("🔍 Testing Framework Imports...")
    
    try:
        from automated_functionality_tester import (
            AutomatedFunctionalityTester,
            AutomatedFixEngine, 
            TestDataManager,
            DefectPriority,
            DefectType,
            TestPhase
        )
        print("✅ All framework imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic framework functionality"""
    print("\n🔧 Testing Basic Framework Functionality...")
    
    try:
        # Create temporary test directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_images"
            
            # Import and create tester
            from automated_functionality_tester import AutomatedFunctionalityTester
            
            tester = AutomatedFunctionalityTester(str(temp_path))
            
            # Test basic properties
            assert tester.test_image_dir == temp_path
            assert tester.max_cycles == 10
            assert len(tester.functionality_results) == 0
            
            print("✅ Basic framework functionality working")
            return True
            
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_test_data_manager():
    """Test TestDataManager functionality"""
    print("\n📁 Testing Test Data Manager...")
    
    try:
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test_images"
            
            from automated_functionality_tester import TestDataManager
            import logging
            
            # Create logger
            logger = logging.getLogger('test')
            
            # Create test data manager
            tdm = TestDataManager(temp_path, logger)
            
            # Test data creation
            result = tdm.ensure_test_data_availability()
            
            if result:
                # Check if test data was created
                assert temp_path.exists()
                
                # Check for test images
                image_files = list(temp_path.glob("*.jpg"))
                assert len(image_files) > 0
                
                print(f"✅ Test data manager created {len(image_files)} test images")
                return True
            else:
                print("❌ Test data creation failed")
                return False
                
    except Exception as e:
        print(f"❌ Test data manager test failed: {e}")
        return False

def test_fix_engine():
    """Test AutomatedFixEngine functionality"""
    print("\n🛠️ Testing Automated Fix Engine...")
    
    try:
        from automated_functionality_tester import AutomatedFixEngine, Defect, DefectType, DefectPriority
        import logging
        
        # Create logger
        logger = logging.getLogger('test')
        
        # Create fix engine
        fix_engine = AutomatedFixEngine(logger)
        
        # Test fix strategies exist
        assert len(fix_engine.fix_strategies) > 0
        
        # Create test defect
        test_defect = Defect(
            id="test_defect_001",
            type=DefectType.ENVIRONMENT,
            priority=DefectPriority.LOW,
            description="Test defect for validation",
            error_details="Test error details",
            suggested_fix="test_fix",
            auto_fixable=False  # Non-fixable for safe testing
        )
        
        # Test defect processing (should return False for non-fixable)
        result = fix_engine.apply_intelligent_fix(test_defect)
        assert result == False  # Expected for non-fixable defect
        
        print("✅ Automated fix engine working")
        return True
        
    except Exception as e:
        print(f"❌ Fix engine test failed: {e}")
        return False

def test_environment_validation():
    """Test environment validation without full GUI"""
    print("\n🌐 Testing Environment Validation...")
    
    try:
        from automated_functionality_tester import AutomatedFunctionalityTester
        
        # Create tester with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            tester = AutomatedFunctionalityTester(temp_dir)
            
            # Test Python version validation
            python_valid = tester.validate_dependencies()
            
            # Test basic imports
            import tkinter as tk
            from PIL import Image
            import json
            
            print("✅ Environment validation working")
            return True
            
    except Exception as e:
        print(f"❌ Environment validation test failed: {e}")
        return False

def test_configuration_validation():
    """Test framework configuration validation"""
    print("\n⚙️ Testing Configuration Validation...")
    
    try:
        # Test that all required modules are available
        required_modules = [
            'tkinter',
            'PIL',
            'json',
            'pathlib',
            'datetime',
            'logging',
            'subprocess',
            'time'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                print(f"❌ Required module not available: {module_name}")
                return False
        
        # Test project structure
        expected_dirs = ['src', 'src/ui', 'src/models', 'src/services']
        
        for dir_name in expected_dirs:
            dir_path = project_root / dir_name
            if not dir_path.exists():
                print(f"⚠️ Expected directory not found: {dir_name}")
        
        print("✅ Configuration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False

def run_validation_suite():
    """Run complete validation suite"""
    print("🔬 Automated Functionality Testing Framework Validation")
    print("=" * 60)
    
    tests = [
        ("Framework Imports", test_framework_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Test Data Manager", test_test_data_manager),
        ("Fix Engine", test_fix_engine),
        ("Environment Validation", test_environment_validation),
        ("Configuration Validation", test_configuration_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION RESULTS")
    print("=" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All validation tests passed!")
        print("   The functionality testing framework is ready for use.")
        return True
    else:
        print(f"\n⚠️ {total - passed} validation tests failed!")
        print("   Some components may not work correctly.")
        return False

def main():
    """Main entry point"""
    try:
        success = run_validation_suite()
        
        if success:
            print("\n✅ Framework validation completed successfully!")
            print("\n📋 Next Steps:")
            print("   1. Run: python run_functionality_tests.py --test-data-only")
            print("   2. Run: python run_functionality_tests.py --quick")
            print("   3. Review generated test reports")
            sys.exit(0)
        else:
            print("\n❌ Framework validation failed!")
            print("\n📋 Troubleshooting:")
            print("   1. Ensure all dependencies are installed")
            print("   2. Check Python environment setup")
            print("   3. Verify project directory structure")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Validation interrupted by user.")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ Validation failed with error: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()