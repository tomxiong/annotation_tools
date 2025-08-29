#!/usr/bin/env python3
"""
GUI Startup with Functionality Testing Integration

This script integrates functionality testing with the existing GUI startup process.
It can optionally run functionality tests before launching the GUI to ensure 
system reliability.

Usage:
    python test_gui_with_functionality_check.py              # Test then launch GUI
    python test_gui_with_functionality_check.py --skip-test   # Launch GUI directly  
    python test_gui_with_functionality_check.py --test-only   # Run tests only
"""

import sys
import os
import argparse
import time
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import functionality tester
from automated_functionality_tester import AutomatedFunctionalityTester


def run_pre_launch_functionality_check(test_image_dir: str = "D:\\test\\images") -> bool:
    """Run quick functionality check before GUI launch"""
    print("🔍 Running Pre-Launch Functionality Check...")
    print("=" * 50)
    
    try:
        tester = AutomatedFunctionalityTester(test_image_dir)
        tester.max_cycles = 2  # Quick check
        
        # Run essential tests only
        essential_results = tester.execute_test_cycle_with_auto_fix()
        
        if essential_results:
            print("✅ Pre-launch functionality check PASSED")
            print("   System is ready for GUI launch")
            return True
        else:
            print("❌ Pre-launch functionality check FAILED")
            print("   Some issues detected - GUI may not work properly")
            return False
            
    except Exception as e:
        print(f"⚠️ Pre-launch check failed with error: {e}")
        print("   Proceeding with GUI launch anyway...")
        return False


def launch_panoramic_gui():
    """Launch the panoramic annotation GUI"""
    print("\n🚀 Launching Panoramic Annotation GUI...")
    print("=" * 50)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # Create main window
        root = tk.Tk()
        root.title("全景图像标注工具 - 微生物药敏检测")
        
        # Set window size and position
        root.geometry("2400x1300+100+50")
        
        # Create application
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI created successfully!")
        print("\n📋 Quick Setup Guide:")
        print("1. Set panoramic directory to: D:\\test\\images")
        print("2. Click 'Load Data' to load test images") 
        print("3. Test hole navigation (arrow keys or hole number input)")
        print("4. Test annotation features (growth level, microbe type)")
        print("5. Test save/load annotation functionality")
        print("\n🖥️ GUI is now running. Close the window when finished.")
        
        # Start the GUI main loop
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ GUI launch failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_functionality_tests_only(test_image_dir: str = "D:\\test\\images"):
    """Run comprehensive functionality tests without launching GUI"""
    print("🔬 Running Comprehensive Functionality Tests...")
    print("=" * 50)
    
    try:
        tester = AutomatedFunctionalityTester(test_image_dir)
        results = tester.execute_comprehensive_functionality_test()
        
        # Print summary
        overall_status = results.get('overall_functionality_status', 'UNKNOWN')
        defects_detected = results.get('defects_detected', 0)
        defects_resolved = results.get('defects_resolved', 0)
        
        print(f"\n📊 Test Results Summary:")
        print(f"   Status: {overall_status}")
        print(f"   Defects Detected: {defects_detected}")
        print(f"   Defects Resolved: {defects_resolved}")
        
        return overall_status == 'FUNCTIONAL'
        
    except Exception as e:
        print(f"❌ Functionality tests failed: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="GUI Startup with Functionality Testing Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--skip-test',
        action='store_true',
        help='Skip functionality tests and launch GUI directly'
    )
    
    parser.add_argument(
        '--test-only',
        action='store_true',
        help='Run functionality tests only, do not launch GUI'
    )
    
    parser.add_argument(
        '--test-dir',
        type=str,
        default="D:\\test\\images",
        help='Test image directory path (default: D:\\test\\images)'
    )
    
    parser.add_argument(
        '--force-launch',
        action='store_true',
        help='Launch GUI even if functionality tests fail'
    )
    
    args = parser.parse_args()
    
    print("🔬 Panoramic Annotation GUI with Functionality Testing")
    print("=" * 60)
    
    try:
        if args.test_only:
            # Run tests only
            success = run_functionality_tests_only(args.test_dir)
            if success:
                print("\n✅ All functionality tests passed!")
                sys.exit(0)
            else:
                print("\n❌ Some functionality tests failed!")
                sys.exit(1)
                
        elif args.skip_test:
            # Launch GUI directly
            print("⚠️ Skipping functionality tests as requested")
            success = launch_panoramic_gui()
            
        else:
            # Run pre-launch check then launch GUI
            test_passed = run_pre_launch_functionality_check(args.test_dir)
            
            if test_passed or args.force_launch:
                if not test_passed and args.force_launch:
                    print("⚠️ Forcing GUI launch despite test failures")
                    
                success = launch_panoramic_gui()
            else:
                print("\n❌ Pre-launch tests failed!")
                print("   Use --force-launch to launch GUI anyway")
                print("   Or use --test-only to run full diagnostic tests")
                sys.exit(1)
        
        if success:
            print("\n✅ Session completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Session completed with errors!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Session interrupted by user.")
        sys.exit(2)
        
    except Exception as e:
        print(f"\n❌ Session failed with error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()