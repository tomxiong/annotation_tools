#!/usr/bin/env python3
"""
Main Test Runner for Panoramic Annotation GUI Functionality Testing

This script provides an easy-to-use interface for running comprehensive
automated functionality tests for the panoramic annotation GUI system.

Usage:
    python run_functionality_tests.py
    python run_functionality_tests.py --quick
    python run_functionality_tests.py --test-data-only
    python run_functionality_tests.py --report-only
"""

import argparse
import sys
import os
import time
import json
from pathlib import Path
from datetime import datetime

# Add project path to Python path
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import the automated functionality tester
from automated_functionality_tester import AutomatedFunctionalityTester


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Panoramic Annotation GUI Testing Framework                ║
║                          Automated Functionality Tester                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔬 Comprehensive functionality detection and validation system
🛠  Intelligent defect detection with auto-resolution capabilities  
📊 Performance monitoring and optimization
🎯 Test data management for panoramic image library
"""
    print(banner)


def run_quick_tests(test_image_dir: str = "D:\\test\\images"):
    """Run quick functionality tests (limited cycles)"""
    print("🚀 Running Quick Functionality Tests")
    print("=" * 60)
    
    tester = AutomatedFunctionalityTester(test_image_dir)
    tester.max_cycles = 3  # Limit cycles for quick test
    
    start_time = time.time()
    results = tester.execute_comprehensive_functionality_test()
    end_time = time.time()
    
    print_test_summary(results, end_time - start_time, "Quick Test")
    return results


def run_comprehensive_tests(test_image_dir: str = "D:\\test\\images"):
    """Run comprehensive functionality tests (full cycles)"""
    print("🔍 Running Comprehensive Functionality Tests")
    print("=" * 60)
    
    tester = AutomatedFunctionalityTester(test_image_dir)
    tester.max_cycles = 10  # Full testing cycles
    
    start_time = time.time()
    results = tester.execute_comprehensive_functionality_test()
    end_time = time.time()
    
    print_test_summary(results, end_time - start_time, "Comprehensive Test")
    return results


def create_test_data_only(test_image_dir: str = "D:\\test\\images"):
    """Create test data without running tests"""
    print("📁 Creating Test Data Only")
    print("=" * 60)
    
    tester = AutomatedFunctionalityTester(test_image_dir)
    
    # Just ensure test data availability
    data_created = tester.test_data_manager.ensure_test_data_availability()
    
    if data_created:
        print(f"✅ Test data successfully created/verified at: {test_image_dir}")
        
        # List created files
        test_dir = Path(test_image_dir)
        if test_dir.exists():
            files = list(test_dir.glob("*"))
            print(f"\n📋 Created files ({len(files)} total):")
            for file in sorted(files)[:10]:  # Show first 10 files
                print(f"   📄 {file.name}")
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more files")
    else:
        print(f"❌ Failed to create test data at: {test_image_dir}")
    
    return data_created


def generate_report_only():
    """Generate report from existing test results"""
    print("📊 Generating Report from Existing Results")
    print("=" * 60)
    
    reports_dir = project_root / "test_reports"
    
    if not reports_dir.exists():
        print("❌ No test reports directory found. Run tests first.")
        return False
    
    # Find latest report
    report_files = list(reports_dir.glob("functionality_test_report_*.json"))
    
    if not report_files:
        print("❌ No test reports found. Run tests first.")
        return False
    
    latest_report = max(report_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(latest_report, 'r', encoding='utf-8') as f:
            results = json.load(f)
        
        print(f"📋 Report from: {latest_report.name}")
        print_test_summary(results, results.get('total_execution_time', 0), "Report")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to load report: {e}")
        return False


def print_test_summary(results: dict, execution_time: float, test_type: str):
    """Print comprehensive test summary"""
    print(f"\n{'='*60}")
    print(f"🎯 {test_type.upper()} RESULTS SUMMARY")
    print(f"{'='*60}")
    
    # Basic information
    print(f"📅 Session ID: {results.get('session_id', 'N/A')}")
    print(f"⏱️  Total Execution Time: {execution_time:.2f} seconds")
    print(f"🔄 Test Cycles: {results.get('test_cycles', 0)}/{results.get('max_cycles', 0)}")
    print(f"🎭 Overall Status: {results.get('overall_functionality_status', 'UNKNOWN')}")
    
    # Defect information
    defects_detected = results.get('defects_detected', 0)
    defects_resolved = results.get('defects_resolved', 0)
    auto_fixes = results.get('auto_fixes_applied', 0)
    
    print(f"\n🔧 DEFECT ANALYSIS:")
    print(f"   🚨 Defects Detected: {defects_detected}")
    print(f"   ✅ Defects Resolved: {defects_resolved}")
    print(f"   🛠️  Auto-fixes Applied: {auto_fixes}")
    
    if defects_detected > 0:
        resolution_rate = (defects_resolved / defects_detected) * 100
        print(f"   📊 Resolution Rate: {resolution_rate:.1f}%")
    
    # Phase results
    print(f"\n📋 PHASE RESULTS:")
    phase_results = results.get('results', {})
    
    for phase, result in phase_results.items():
        status = "✅ PASS" if result.get('passed', False) else "❌ FAIL"
        exec_time = result.get('execution_time', 0)
        defects = result.get('defects_found', 0)
        fixes = result.get('fixes_applied', 0)
        success_rate = result.get('success_rate', 0) * 100
        
        print(f"   {status} {phase.replace('_', ' ').title()}")
        print(f"      ⏱️  Time: {exec_time:.2f}s | 🚨 Defects: {defects} | 🛠️  Fixes: {fixes} | 📊 Success: {success_rate:.1f}%")
    
    # Performance metrics
    perf_metrics = results.get('performance_metrics', {})
    if perf_metrics:
        print(f"\n⚡ PERFORMANCE METRICS:")
        
        memory_mb = perf_metrics.get('memory_usage_mb', 0)
        if memory_mb > 0:
            print(f"   💾 Memory Usage: {memory_mb:.1f} MB")
        
        cpu_percent = perf_metrics.get('cpu_usage_percent', 0)
        if cpu_percent > 0:
            print(f"   💻 CPU Usage: {cpu_percent:.1f}%")
        
        startup_time = perf_metrics.get('startup_time_s', 0)
        if startup_time > 0:
            print(f"   🚀 Startup Time: {startup_time:.1f}s")
    
    # Overall assessment
    overall_status = results.get('overall_functionality_status', 'UNKNOWN')
    
    if overall_status == 'FUNCTIONAL':
        print(f"\n🎉 ASSESSMENT: System is fully functional!")
        print("   All functionality tests passed successfully.")
        print("   The panoramic annotation GUI is ready for use.")
    elif overall_status == 'DEFECTS_DETECTED':
        print(f"\n⚠️ ASSESSMENT: Some issues detected but may be resolved.")
        print("   Check individual phase results for details.")
        print("   Consider running tests again or manual investigation.")
    else:
        print(f"\n❓ ASSESSMENT: Test status unclear.")
        print("   Check test logs for more information.")
    
    # Next steps
    print(f"\n📋 NEXT STEPS:")
    if overall_status == 'FUNCTIONAL':
        print("   ✅ System ready for production use")
        print("   📊 Consider performance monitoring")
        print("   🔄 Run periodic functionality checks")
    else:
        print("   🔍 Review detailed test logs")
        print("   🛠️  Apply manual fixes if needed")
        print("   🔄 Re-run tests after fixes")
    
    # File locations
    print(f"\n📁 FILES GENERATED:")
    logs_dir = project_root / "test_logs"
    reports_dir = project_root / "test_reports"
    
    if logs_dir.exists():
        print(f"   📝 Test Logs: {logs_dir}")
    if reports_dir.exists():
        print(f"   📊 Test Reports: {reports_dir}")
    
    print(f"{'='*60}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automated Functionality Testing for Panoramic Annotation GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_functionality_tests.py                    # Run comprehensive tests
  python run_functionality_tests.py --quick            # Run quick tests (3 cycles)
  python run_functionality_tests.py --test-data-only   # Create test data only
  python run_functionality_tests.py --report-only      # Generate report from existing results
  python run_functionality_tests.py --test-dir "C:\\custom\\path"  # Use custom test directory
        """
    )
    
    parser.add_argument(
        '--quick', 
        action='store_true',
        help='Run quick tests with limited cycles (faster)'
    )
    
    parser.add_argument(
        '--test-data-only',
        action='store_true', 
        help='Create test data only, skip running tests'
    )
    
    parser.add_argument(
        '--report-only',
        action='store_true',
        help='Generate report from existing test results'
    )
    
    parser.add_argument(
        '--test-dir',
        type=str,
        default="D:\\test\\images",
        help='Test image directory path (default: D:\\test\\images)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    try:
        # Determine test mode
        if args.report_only:
            success = generate_report_only()
            
        elif args.test_data_only:
            success = create_test_data_only(args.test_dir)
            
        elif args.quick:
            results = run_quick_tests(args.test_dir)
            success = results.get('overall_functionality_status') == 'FUNCTIONAL'
            
        else:
            results = run_comprehensive_tests(args.test_dir)
            success = results.get('overall_functionality_status') == 'FUNCTIONAL'
        
        # Exit with appropriate code
        if success:
            print("\n✅ Testing completed successfully!")
            sys.exit(0)
        else:
            print("\n⚠️ Testing completed with issues detected.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Testing interrupted by user.")
        sys.exit(2)
        
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()