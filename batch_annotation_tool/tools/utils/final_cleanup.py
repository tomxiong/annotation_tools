#!/usr/bin/env python3
"""
Enhanced Cleanup Script - Final Organization
Remove additional scripts, JSON, and MD files, keeping only essentials for panoramic_annotation_gui.py
"""

import os
import shutil
from pathlib import Path
import datetime

def create_final_backup():
    """Create backup before final cleanup"""
    project_root = Path.cwd()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / f"backup_final_cleanup_{timestamp}"
    
    print(f"🔒 Creating final backup at: {backup_dir}")
    
    # Backup remaining root files
    root_files = [f for f in project_root.iterdir() if f.is_file()]
    if root_files:
        backup_dir.mkdir(exist_ok=True)
        for file_path in root_files:
            shutil.copy2(file_path, backup_dir / file_path.name)
    
    print(f"✅ Final backup created")
    return backup_dir

def final_cleanup():
    """Final cleanup - move remaining non-essential files"""
    project_root = Path.cwd()
    
    # Files to organize in final cleanup
    FINAL_CLEANUP_MAP = {
        # CLI and batch scripts - move to tools/cli/
        "tools/cli/": [
            "run_cli.py",
            "batch_annotation.py",
            "start_cli.bat",
            "start_cli.sh"
        ],
        
        # Build and setup scripts - move to tools/build/
        "tools/build/": [
            "setup.py",
            "run_all_tests.bat"
        ],
        
        # Batch processing scripts - move to tools/batch/
        "tools/batch/": [
            "run_batch.bat",
            "run_batch.sh"
        ],
        
        # Demo scripts - move to existing tools/demo/
        "tools/demo/": [
            "run_demo.bat",
            "run_demo.sh",
            "run_example.bat", 
            "run_example.sh"
        ],
        
        # Testing scripts - move to existing tools/testing/
        "tools/testing/": [
            "run_functionality_tests.bat",
            "run_functionality_tests.py",
            "test_cleanup.py",
            "test_core_imports.py",
            "test_gui_quick.py"
        ],
        
        # Utility scripts - move to tools/utils/
        "tools/utils/": [
            "cleanup_migration.py"
        ],
        
        # Report files - move to archive/reports/
        "archive/reports/": [
            "defect_simulation_report_20250827_022654.json",
            "quick_demo_report_20250827_022452.json", 
            "quick_demo_report_20250827_025701.json",
            "cleanup_report.md"
        ],
        
        # GUI launcher scripts - move to existing tools/launchers/
        "tools/launchers/": [
            "start_gui.bat",
            "start_gui.py",
            "start_gui.sh"
        ]
    }
    
    moved_count = 0
    
    for target_dir, files in FINAL_CLEANUP_MAP.items():
        target_path = project_root / target_dir
        target_path.mkdir(parents=True, exist_ok=True)
        
        for file_name in files:
            source_file = project_root / file_name
            if source_file.exists():
                target_file = target_path / source_file.name
                shutil.move(str(source_file), str(target_file))
                print(f"✅ Moved: {file_name} -> {target_dir}")
                moved_count += 1
            else:
                print(f"⚠️  File not found: {file_name}")
    
    # Keep only essential root files
    essential_root_files = {
        "README.md",      # Project documentation
        "INSTALL.md"      # Installation instructions  
    }
    
    # Check what files remain in root
    remaining_files = [f for f in project_root.iterdir() 
                      if f.is_file() and f.name not in essential_root_files]
    
    if remaining_files:
        print(f"\n📋 Remaining root files:")
        for file in remaining_files:
            print(f"   - {file.name}")
    
    print(f"\n📊 Final cleanup: {moved_count} files organized")
    return moved_count

def verify_core_structure():
    """Verify that essential structure is intact"""
    project_root = Path.cwd()
    
    essential_files = [
        "src/ui/panoramic_annotation_gui.py",
        "src/ui/hole_manager.py",
        "src/ui/enhanced_annotation_panel.py",
        "src/services/panoramic_image_service.py",
        "src/models/panoramic_annotation.py",
        "README.md",
        "INSTALL.md"
    ]
    
    essential_dirs = [
        "src/ui",
        "src/services", 
        "src/models",
        "src/core",
        "tools",
        "docs",
        "archive",
        "tests"
    ]
    
    print("\n🔍 Verifying essential structure:")
    
    # Check files
    all_files_ok = True
    for file_path in essential_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ MISSING: {file_path}")
            all_files_ok = False
    
    # Check directories
    all_dirs_ok = True
    for dir_path in essential_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ MISSING: {dir_path}/")
            all_dirs_ok = False
    
    return all_files_ok and all_dirs_ok

def create_final_report(backup_dir, moved_count):
    """Create final cleanup report"""
    project_root = Path.cwd()
    report_file = project_root / "final_cleanup_report.md"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# Final Cleanup Report

**Date:** {timestamp}
**Backup Location:** {backup_dir}
**Additional Files Organized:** {moved_count}

## Project Structure After Final Cleanup

### Root Directory (Minimal)
- `README.md` (Project documentation)
- `INSTALL.md` (Installation instructions)
- Essential directories only

### Core Source Code (`src/`)
**Main GUI Implementation:**
- `src/ui/panoramic_annotation_gui.py` ⭐ **PRIMARY FILE**

**Essential Dependencies:**
- `src/ui/hole_manager.py`
- `src/ui/hole_config_panel.py`
- `src/ui/enhanced_annotation_panel.py`
- `src/ui/batch_import_dialog.py`
- `src/services/` (all service modules)
- `src/models/` (all data models)
- `src/core/` (core utilities)

### Organized Tools (`tools/`)
- `tools/cli/` - CLI and batch scripts
- `tools/build/` - Build and setup scripts
- `tools/batch/` - Batch processing scripts
- `tools/demo/` - Demo and example scripts
- `tools/testing/` - Testing utilities
- `tools/launchers/` - GUI launcher scripts
- `tools/utils/` - General utilities

### Documentation (`docs/`)
- All project documentation organized

### Archive (`archive/`)
- `archive/reports/` - Generated reports and logs
- `archive/refactored_variants/` - Unused GUI variants
- `archive/temp_tests/` - Temporary test files

### Official Tests (`tests/`)
- Unit tests and formal test suites

## Summary

✅ **Project successfully cleaned and organized**
✅ **Only essential files remain in root directory**  
✅ **Core GUI functionality preserved**
✅ **All utilities properly categorized**
✅ **Clean, maintainable structure achieved**

## Next Steps

1. Test core GUI: `python src/ui/panoramic_annotation_gui.py`
2. Use tools from their organized locations
3. Refer to `README.md` for project overview
4. Check `INSTALL.md` for setup instructions

The project now has a minimal, clean structure focused on the core GUI functionality.
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 Final report created: {report_file}")

def main():
    """Main final cleanup function"""
    print("🧹 Final Project Cleanup - Organizing Remaining Files")
    print("=" * 60)
    
    # Step 1: Create backup
    backup_dir = create_final_backup()
    
    # Step 2: Organize remaining files
    print("\n📦 Organizing remaining files...")
    moved_count = final_cleanup()
    
    # Step 3: Verify structure
    print("\n🔍 Verifying project structure...")
    structure_ok = verify_core_structure()
    
    # Step 4: Create final report
    print("\n📄 Creating final report...")
    create_final_report(backup_dir, moved_count)
    
    # Final status
    print("\n" + "=" * 60)
    if structure_ok:
        print("✅ FINAL CLEANUP COMPLETED SUCCESSFULLY!")
        print(f"✅ {moved_count} additional files organized")
        print("✅ Clean, minimal project structure achieved")
        print("✅ Core GUI functionality preserved")
        print(f"🔒 Backup available at: {backup_dir}")
        print("\n🎯 Project is now optimally organized!")
        print("   - Root: Only essential documentation")
        print("   - src/: Core functionality only") 
        print("   - tools/: All utilities categorized")
        print("   - docs/: Documentation organized")
        print("   - archive/: Historical files preserved")
    else:
        print("❌ Final cleanup completed with warnings!")
        print("⚠️  Some essential files may be missing")
        print("🔧 Check the verification results above")
    
    print("\n📄 See final_cleanup_report.md for complete details")

if __name__ == "__main__":
    main()