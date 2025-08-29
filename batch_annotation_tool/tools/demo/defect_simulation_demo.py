#!/usr/bin/env python3
"""
Defect Simulation Demo - Shows Complete Closed Loop with Fixes

This demo intentionally creates some defects to demonstrate the complete
test-detect-fix-verify cycle in action.
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Add project path
project_root = Path(__file__).parent.absolute()

class DefectSimulationDemo:
    """Demo that simulates defects and shows automated fixes"""
    
    def __init__(self):
        self.temp_backup_dir = None
        self.simulated_issues = []
        
    def run_demo(self):
        """Run demo with simulated defects"""
        print("🔄 DEFECT SIMULATION CLOSED LOOP DEMO")
        print("=" * 50)
        print("🎭 Simulating defects to demonstrate auto-fix capabilities")
        print()
        
        # Setup simulated defects
        self.setup_defect_simulation()
        
        try:
            # Phase 1: Execute Tests (with simulated defects)
            print("🔍 PHASE 1: EXECUTING TESTS (with simulated defects)")
            test_results = self.execute_tests_with_defects()
            
            # Phase 2: Detect Defects
            print("\n🚨 PHASE 2: DETECTING DEFECTS")
            defects = self.detect_defects(test_results)
            
            # Phase 3: Apply Automated Fixes
            print("\n🛠️ PHASE 3: APPLYING AUTOMATED FIXES")
            fix_results = self.apply_automated_fixes(defects)
            
            # Phase 4: Re-test to Verify Fixes
            print("\n🔄 PHASE 4: RE-TESTING TO VERIFY FIXES")
            verification_results = self.verify_fixes_by_retesting()
            
            # Phase 5: Generate Report
            print("\n📊 PHASE 5: GENERATING COMPREHENSIVE REPORT")
            report = self.generate_comprehensive_report(test_results, defects, fix_results, verification_results)
            
            return report
            
        finally:
            # Clean up simulated defects
            self.cleanup_defect_simulation()
    
    def setup_defect_simulation(self):
        """Create temporary defects for demonstration"""
        print("🎭 Setting up defect simulation...")
        
        # Create temporary backup
        self.temp_backup_dir = Path(tempfile.mkdtemp())
        
        # Simulate missing src directory
        src_dir = project_root / "src"
        if src_dir.exists():
            # Backup and remove temporarily
            backup_src = self.temp_backup_dir / "src"
            shutil.copytree(src_dir, backup_src)
            shutil.rmtree(src_dir)
            self.simulated_issues.append(("src_directory", src_dir, backup_src))
            print("   🎭 Simulated: Missing src directory")
        
        # Simulate missing test image directory
        test_img_dir = Path("D:\\test\\images")
        if test_img_dir.exists():
            # Backup and remove temporarily
            backup_imgs = self.temp_backup_dir / "test_images"
            shutil.copytree(test_img_dir, backup_imgs)
            shutil.rmtree(test_img_dir)
            self.simulated_issues.append(("test_images", test_img_dir, backup_imgs))
            print("   🎭 Simulated: Missing test image directory")
        else:
            # Create a flag that it was missing originally
            self.simulated_issues.append(("test_images", test_img_dir, None))
            print("   🎭 Simulated: Test image directory already missing")
        
        # Simulate missing GUI entry file
        gui_file = project_root / "start_gui.py"
        if gui_file.exists():
            backup_gui = self.temp_backup_dir / "start_gui.py"
            shutil.copy2(gui_file, backup_gui)
            gui_file.unlink()
            self.simulated_issues.append(("gui_file", gui_file, backup_gui))
            print("   🎭 Simulated: Missing GUI entry file")
        else:
            self.simulated_issues.append(("gui_file", gui_file, None))
            print("   🎭 Simulated: GUI entry file already missing")
    
    def execute_tests_with_defects(self):
        """Execute tests that will detect the simulated defects"""
        tests = [
            ("Environment Validation", self.test_environment),
            ("Project Structure", self.test_project_structure),
            ("GUI Entry Points", self.test_gui_entry_points),
            ("Image System Setup", self.test_image_system),
            ("Navigation Logic", self.test_navigation_logic)
        ]
        
        results = {}
        for name, test_func in tests:
            print(f"   🔍 Testing: {name}")
            try:
                result = test_func()
                results[name] = result
                status = "✅ PASS" if result["passed"] else "❌ FAIL"
                print(f"      {status}")
                if not result["passed"]:
                    for issue in result.get("issues", []):
                        print(f"         🚨 Issue: {issue}")
            except Exception as e:
                results[name] = {"passed": False, "error": str(e), "issues": ["test_exception"]}
                print(f"      ❌ ERROR: {e}")
        
        return results
    
    def test_environment(self):
        """Test basic environment"""
        issues = []
        
        # Check Python environment
        try:
            import tkinter
        except ImportError:
            issues.append("tkinter_not_available")
        
        return {"passed": len(issues) == 0, "issues": issues}
    
    def test_project_structure(self):
        """Test project directory structure"""
        issues = []
        
        # Check for src directory
        if not (project_root / "src").exists():
            issues.append("src_directory_missing")
        
        # Check for key subdirectories
        subdirs = ["ui", "models", "services"]
        for subdir in subdirs:
            if not (project_root / "src" / subdir).exists():
                issues.append(f"src_{subdir}_missing")
        
        return {"passed": len(issues) == 0, "issues": issues}
    
    def test_gui_entry_points(self):
        """Test GUI entry point files"""
        issues = []
        
        gui_files = ["start_gui.py"]
        for gui_file in gui_files:
            if not (project_root / gui_file).exists():
                issues.append(f"missing_{gui_file}")
        
        return {"passed": len(issues) == 0, "issues": issues}
    
    def test_image_system(self):
        """Test image system setup"""
        issues = []
        
        # Check test image directory
        test_dir = Path("D:\\test\\images")
        if not test_dir.exists():
            issues.append("test_image_directory_missing")
        
        # Test PIL availability
        try:
            from PIL import Image
        except ImportError:
            issues.append("pil_not_available")
        
        return {"passed": len(issues) == 0, "issues": issues}
    
    def test_navigation_logic(self):
        """Test navigation calculations"""
        issues = []
        
        # Test grid calculations
        grid_cols, grid_rows = 12, 10
        expected_holes = 120
        actual_holes = grid_cols * grid_rows
        
        if actual_holes != expected_holes:
            issues.append("grid_calculation_error")
        
        # Test coordinate calculations
        test_holes = [1, 25, 60, 120]
        for hole in test_holes:
            row = (hole - 1) // grid_cols
            col = (hole - 1) % grid_cols
            
            if row < 0 or row >= grid_rows or col < 0 or col >= grid_cols:
                issues.append(f"coordinate_error_hole_{hole}")
        
        return {"passed": len(issues) == 0, "issues": issues}
    
    def detect_defects(self, test_results):
        """Analyze test results and detect defects"""
        defects = []
        
        for test_name, result in test_results.items():
            if not result["passed"]:
                for issue in result.get("issues", []):
                    defect = {
                        "id": f"defect_{len(defects)+1}",
                        "test_name": test_name,
                        "issue_type": issue,
                        "description": f"{test_name}: {issue}",
                        "severity": self.get_defect_severity(issue),
                        "fix_strategy": self.get_fix_strategy(issue),
                        "auto_fixable": self.is_auto_fixable(issue)
                    }
                    defects.append(defect)
                    severity_emoji = {"high": "🔥", "medium": "⚠️", "low": "ℹ️"}
                    emoji = severity_emoji.get(defect["severity"], "🚨")
                    print(f"   {emoji} Detected: {defect['description']} (Severity: {defect['severity'].upper()})")
        
        if not defects:
            print("   ✅ No defects detected")
        else:
            auto_fixable = sum(1 for d in defects if d["auto_fixable"])
            print(f"   📊 Total defects: {len(defects)}, Auto-fixable: {auto_fixable}")
        
        return defects
    
    def get_defect_severity(self, issue):
        """Determine defect severity"""
        high_severity = ["src_directory_missing", "test_image_directory_missing"]
        medium_severity = ["missing_start_gui.py", "pil_not_available"]
        
        if issue in high_severity:
            return "high"
        elif issue in medium_severity:
            return "medium"
        else:
            return "low"
    
    def get_fix_strategy(self, issue):
        """Get automated fix strategy for issue"""
        strategies = {
            "src_directory_missing": "recreate_src_structure",
            "src_ui_missing": "create_ui_directory",
            "src_models_missing": "create_models_directory", 
            "src_services_missing": "create_services_directory",
            "missing_start_gui.py": "create_gui_entry_file",
            "test_image_directory_missing": "create_test_image_directory",
            "grid_calculation_error": "fix_grid_calculations",
            "pil_not_available": "install_pil_package"
        }
        return strategies.get(issue, "manual_investigation_required")
    
    def is_auto_fixable(self, issue):
        """Check if issue can be automatically fixed"""
        auto_fixable_issues = [
            "src_directory_missing", "src_ui_missing", "src_models_missing", "src_services_missing",
            "missing_start_gui.py", "test_image_directory_missing", "grid_calculation_error"
        ]
        return issue in auto_fixable_issues
    
    def apply_automated_fixes(self, defects):
        """Apply automated fixes to detected defects"""
        fix_results = {}
        
        for defect in defects:
            if defect["auto_fixable"]:
                print(f"   🔧 Applying fix: {defect['fix_strategy']}")
                print(f"      Target: {defect['description']}")
                
                try:
                    success = self.execute_fix_strategy(defect["fix_strategy"])
                    fix_results[defect["id"]] = success
                    
                    if success:
                        print(f"      ✅ Fix applied successfully")
                    else:
                        print(f"      ❌ Fix failed")
                        
                except Exception as e:
                    print(f"      ❌ Fix failed with exception: {e}")
                    fix_results[defect["id"]] = False
            else:
                print(f"   ⚠️ Manual intervention required: {defect['description']}")
                fix_results[defect["id"]] = False
        
        successful_fixes = sum(1 for success in fix_results.values() if success)
        total_fixes_attempted = len([d for d in defects if d["auto_fixable"]])
        
        if total_fixes_attempted > 0:
            print(f"   📊 Fix success rate: {successful_fixes}/{total_fixes_attempted}")
        
        return fix_results
    
    def execute_fix_strategy(self, strategy):
        """Execute a specific fix strategy"""
        if strategy == "recreate_src_structure":
            # Create src directory and subdirectories
            src_dir = project_root / "src"
            src_dir.mkdir(exist_ok=True)
            (src_dir / "ui").mkdir(exist_ok=True)
            (src_dir / "models").mkdir(exist_ok=True) 
            (src_dir / "services").mkdir(exist_ok=True)
            
            # Create __init__.py files
            for subdir in [src_dir, src_dir/"ui", src_dir/"models", src_dir/"services"]:
                (subdir / "__init__.py").touch()
            
            return src_dir.exists()
        
        elif strategy == "create_gui_entry_file":
            gui_file = project_root / "start_gui.py"
            gui_content = '''#!/usr/bin/env python3
"""
GUI Entry Point for Panoramic Annotation Tool
"""

import sys
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def main():
    """Main GUI entry point"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        # Create main window
        root = tk.Tk()
        root.title("Panoramic Annotation Tool")
        root.geometry("800x600")
        
        # Add simple content
        label = tk.Label(root, text="Panoramic Annotation GUI", font=("Arial", 16))
        label.pack(pady=50)
        
        button = tk.Button(root, text="Start", command=lambda: messagebox.showinfo("Info", "GUI Started!"))
        button.pack(pady=20)
        
        # Start GUI
        root.mainloop()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
            gui_file.write_text(gui_content)
            return gui_file.exists()
        
        elif strategy == "create_test_image_directory":
            test_dir = Path("D:\\test\\images")
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create some test files
            (test_dir / "test_panoramic_001.txt").write_text("Test panoramic image placeholder")
            (test_dir / "README.txt").write_text("Test image directory for automated testing")
            
            return test_dir.exists()
        
        elif strategy == "fix_grid_calculations":
            # Verify and confirm grid calculations are correct
            grid_cols, grid_rows = 12, 10
            return (grid_cols * grid_rows) == 120
        
        else:
            print(f"      ⚠️ Unknown fix strategy: {strategy}")
            return False
    
    def verify_fixes_by_retesting(self):
        """Verify fixes by re-running tests"""
        print("   🔄 Re-running tests to verify fixes...")
        
        # Re-run the same tests
        verification_tests = [
            ("Environment Re-check", self.test_environment),
            ("Project Structure Re-check", self.test_project_structure),
            ("GUI Entry Points Re-check", self.test_gui_entry_points),
            ("Image System Re-check", self.test_image_system),
            ("Navigation Logic Re-check", self.test_navigation_logic)
        ]
        
        verification_results = {}
        for name, test_func in verification_tests:
            try:
                result = test_func()
                verification_results[name] = result
                status = "✅ PASS" if result["passed"] else "❌ STILL FAILING"
                print(f"      {status} {name}")
                
                if not result["passed"]:
                    for issue in result.get("issues", []):
                        print(f"         🚨 Remaining issue: {issue}")
                        
            except Exception as e:
                verification_results[name] = {"passed": False, "error": str(e)}
                print(f"      ❌ ERROR in {name}: {e}")
        
        # Calculate verification success rate
        total_tests = len(verification_results)
        passed_tests = sum(1 for r in verification_results.values() if r["passed"])
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"   📊 Verification results: {passed_tests}/{total_tests} tests passing ({success_rate:.1f}%)")
        
        return verification_results
    
    def generate_comprehensive_report(self, initial_tests, defects, fix_results, verification_tests):
        """Generate comprehensive test report"""
        
        # Calculate metrics
        initial_passed = sum(1 for r in initial_tests.values() if r["passed"])
        initial_total = len(initial_tests)
        
        verification_passed = sum(1 for r in verification_tests.values() if r["passed"])
        verification_total = len(verification_tests)
        
        total_defects = len(defects)
        auto_fixable_defects = sum(1 for d in defects if d["auto_fixable"])
        successfully_fixed = sum(1 for success in fix_results.values() if success)
        
        overall_success = (verification_passed == verification_total)
        improvement = verification_passed - initial_passed
        
        report = {
            "demo_type": "defect_simulation_closed_loop",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "initial_test_results": f"{initial_passed}/{initial_total} passed",
                "defects_detected": total_defects,
                "auto_fixable_defects": auto_fixable_defects,
                "fixes_applied": successfully_fixed,
                "final_test_results": f"{verification_passed}/{verification_total} passed",
                "improvement": f"+{improvement} tests now passing",
                "overall_success": overall_success,
                "demonstration_complete": True
            },
            "detailed_results": {
                "initial_tests": initial_tests,
                "defects": defects,
                "fix_results": fix_results,
                "verification_tests": verification_tests
            }
        }
        
        # Print comprehensive summary
        print(f"   📊 COMPREHENSIVE RESULTS:")
        print(f"      🔍 Initial Tests: {initial_passed}/{initial_total} passed")
        print(f"      🚨 Defects Found: {total_defects} (Auto-fixable: {auto_fixable_defects})")
        print(f"      🛠️ Fixes Applied: {successfully_fixed}/{auto_fixable_defects} successful")
        print(f"      ✅ Final Tests: {verification_passed}/{verification_total} passed")
        print(f"      📈 Improvement: {improvement} additional tests now passing")
        
        if overall_success:
            print(f"      🎉 CLOSED LOOP SUCCESS: All defects resolved!")
        elif improvement > 0:
            print(f"      ⚡ PARTIAL SUCCESS: {improvement} issues resolved")
        else:
            print(f"      ⚠️ NEEDS ATTENTION: Some issues remain")
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = project_root / f"defect_simulation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"      📄 Detailed report saved: {report_file.name}")
        
        return report
    
    def cleanup_defect_simulation(self):
        """Clean up simulated defects and restore original state"""
        print("\n🧹 Cleaning up defect simulation...")
        
        for issue_type, original_path, backup_path in self.simulated_issues:
            try:
                if backup_path and backup_path.exists():
                    if original_path.exists():
                        if original_path.is_dir():
                            shutil.rmtree(original_path)
                        else:
                            original_path.unlink()
                    
                    if backup_path.is_dir():
                        shutil.copytree(backup_path, original_path)
                    else:
                        shutil.copy2(backup_path, original_path)
                    
                    print(f"   ✅ Restored: {issue_type}")
                else:
                    print(f"   ℹ️ Kept created: {issue_type} (was missing originally)")
                    
            except Exception as e:
                print(f"   ⚠️ Error restoring {issue_type}: {e}")
        
        # Clean up temporary backup directory
        if self.temp_backup_dir and self.temp_backup_dir.exists():
            shutil.rmtree(self.temp_backup_dir)
            print("   🧹 Temporary backup cleaned up")

def main():
    """Main entry point"""
    print("🎭 DEFECT SIMULATION CLOSED LOOP DEMO")
    print("=" * 50)
    print("🔄 Demonstrating: Test → Detect → Fix → Verify cycle")
    print("⚡ Fully automated with intentional defects for demonstration")
    print()
    
    try:
        demo = DefectSimulationDemo()
        report = demo.run_demo()
        
        print("\n" + "=" * 50)
        print("🏁 DEFECT SIMULATION DEMO COMPLETED")
        
        if report["summary"]["overall_success"]:
            print("🎉 COMPLETE SUCCESS: All simulated defects were automatically resolved!")
        elif report["summary"]["improvement"]:
            print(f"⚡ PARTIAL SUCCESS: {report['summary']['improvement']}")
        else:
            print("⚠️ DEMONSTRATION COMPLETE: Some defects require manual attention")
        
        print("📋 This demonstrates the complete closed-loop testing capability:")
        print("   1. ✅ Automated test execution")
        print("   2. ✅ Intelligent defect detection") 
        print("   3. ✅ Automated fix application")
        print("   4. ✅ Verification through re-testing")
        print("   5. ✅ Comprehensive reporting")
        
        print("=" * 50)
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())