#!/usr/bin/env python3
"""
Cleanup Migration Script - Keep Only panoramic_annotation_gui.py
Archive refactored variants and organize utility files
"""

import os
import shutil
from pathlib import Path
import datetime

def create_backup():
    """Create a full backup before migration"""
    project_root = Path.cwd()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = project_root / f"backup_before_cleanup_{timestamp}"
    
    print(f"🔒 Creating backup at: {backup_dir}")
    
    # Create backup of critical directories
    for src_dir in ["src", "tests"]:
        if Path(src_dir).exists():
            shutil.copytree(src_dir, backup_dir / src_dir)
    
    # Backup important root files
    root_files = ["*.py", "*.md", "*.bat", "*.sh"]
    for pattern in root_files:
        for file_path in project_root.glob(pattern):
            if file_path.is_file():
                shutil.copy2(file_path, backup_dir / file_path.name)
    
    print(f"✅ Backup created successfully")
    return backup_dir

def archive_files():
    """Archive unnecessary files according to the analysis"""
    project_root = Path.cwd()
    
    # Files to archive (move to archive for safety)
    ARCHIVE_MAP = {
        # Refactored GUI variants
        "archive/refactored_variants/": [
            "src/ui/panoramic_annotation_gui_refactored.py",
            "src/ui/panoramic_annotation_gui_mixin.py"
        ],
        
        # Refactored-only components  
        "archive/refactored_components/": [
            "src/ui/navigation_controller.py",
            "src/ui/annotation_manager.py", 
            "src/ui/image_display_controller.py",
            "src/ui/event_handlers.py",
            "src/ui/ui_components.py",
            "src/ui/panoramic_navigation_methods.py"
        ],
        
        # Mixin files
        "archive/mixin_variants/": [
            "src/ui/mixins/navigation_mixin.py",
            "src/ui/mixins/annotation_mixin.py",
            "src/ui/mixins/image_mixin.py", 
            "src/ui/mixins/event_mixin.py",
            "src/ui/mixins/ui_mixin.py",
            "src/ui/mixins/__init__.py"
        ],
        
        # Refactored-specific tests and launchers
        "archive/refactored_tests/": [
            "src/ui/test_refactored_gui.py",
            "src/ui/start_refactored_gui.py",
            "src/ui/test_panoramic_gui.py",
            "test_gui_launch.py",
            "start_gui_mixin.py", 
            "test_mixin_import.py"
        ],
        
        # Refactoring documentation
        "archive/refactored_docs/": [
            "src/ui/refactoring_guide.md",
            "src/ui/integration_guide.md", 
            "REFACTOR_SUMMARY.md"
        ],
        
        # General testing files
        "tools/testing/": [
            "simple_gui_tester.py",
            "comprehensive_gui_tester.py",
            "test_gui_environment_setup.py",
            "test_gui_with_functionality_check.py",
            "test_gui_launch_methods.py"
        ],
        
        # Launcher scripts
        "tools/launchers/": [
            "launch_panoramic_gui.py",
            "start_panoramic_gui.py",
            "launch_gui.py",
            "run_gui.py", 
            "final_gui_launcher.py",
            "panoramic_annotation_tool.py"
        ],
        
        # Validation tools
        "tools/validation/": [
            "check_setup_sequence.py",
            "quick_env_check.py",
            "verify_activation.py",
            "verify_repair.py",
            "dependency_fixer.py"
        ],
        
        # Automation tools
        "tools/automation/": [
            "automated_functionality_tester.py",
            "automated_gui_tester.py",
            "automated_sync_repair.py",
            "image_loading_tester.py",
            "validate_functionality_framework.py"
        ],
        
        # Demo scripts
        "tools/demo/": [
            "demo.py",
            "demo_closed_loop_testing.py",
            "defect_simulation_demo.py",
            "quick_closed_loop_demo.py"
        ],
        
        # Debug tools
        "tools/debug/": [
            "debug_enhanced_data.py",
            "simple_enhanced_data_test.py"
        ],
        
        # Temporary test files
        "archive/temp_tests/": [
            "test_annotation_source.py",
            "test_annotation_sync.py",
            "test_annotation_sync_verification.py",
            "test_current_hole_refresh_fix.py",
            "test_default_pattern_ui.py",
            "test_enhanced_annotation_final_fix.py",
            "test_enhanced_data_tracking.py",
            "test_enhanced_restoration_fix.py",
            "test_enhanced_save_restore.py",
            "test_enhanced_sync_fixes.py",
            "test_final_sync_fixes.py",
            "test_final_timestamp_fix.py",
            "test_json_enhanced_data_persistence.py",
            "test_label_generation_fix.py",
            "test_logging_cleanup.py",
            "test_new_features.py",
            "test_timestamp_and_default_pattern_fixes.py",
            "test_timestamp_preservation.py",
            "validate_sync_fixes.py"
        ],
        
        # Documentation
        "docs/": [
            "ANNOTATION_LIFECYCLE_ANALYSIS.md",
            "ANNOTATION_SYNC_FINAL_FIXES.md",
            "ANNOTATION_SYNC_FINAL_SOLUTION.md",
            "ANNOTATION_SYNC_FIXES.md",
            "ANNOTATION_SYNC_FIXES_ROUND2.md",
            "COMPLETE_JSON_PERSISTENCE_FIX.md",
            "CURRENT_HOLE_STATE_REFRESH_FIX.md",
            "DATA_ORGANIZATION.md",
            "DEFAULT_PATTERN_UI_DISPLAY_FIX.md",
            "ENHANCED_ANNOTATION_RESTORATION_FIX.md",
            "ENHANCED_DISTINGUISHABLE_DEFAULT_PATTERNS.md",
            "ENVIRONMENT_SETUP_STEPS.md",
            "FUNCTIONALITY_TESTING_GUIDE.md",
            "GUI_ENVIRONMENT_SETUP_GUIDE.md",
            "JSON_ENHANCED_DATA_PERSISTENCE_FIX.md",
            "LOGGING_CLEANUP_SUMMARY.md",
            "METHOD_PROPERTY_CONFLICT_FIX.md",
            "README_GUI_STARTUP.md",
            "STARTUP_GUIDE.md",
            "TIMESTAMP_AND_DEFAULT_PATTERN_FIXES.md"
        ]
    }
    
    moved_count = 0
    
    for target_dir, files in ARCHIVE_MAP.items():
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
    
    # Clean up empty directories
    cleanup_empty_dirs()
    
    print(f"\n📊 Migration Summary: {moved_count} files moved")
    return moved_count

def cleanup_empty_dirs():
    """Remove empty directories after migration"""
    project_root = Path.cwd()
    
    # Directories that might become empty
    potential_empty_dirs = [
        "src/ui/mixins",
    ]
    
    for dir_path in potential_empty_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            try:
                # Try to remove if empty
                if not any(full_path.iterdir()):
                    full_path.rmdir()
                    print(f"🗑️  Removed empty directory: {dir_path}")
            except OSError:
                pass  # Directory not empty or other error

def verify_core_files():
    """Verify that core files are still in place"""
    project_root = Path.cwd()
    
    core_files = [
        "src/ui/panoramic_annotation_gui.py",
        "src/ui/hole_manager.py",
        "src/ui/hole_config_panel.py",
        "src/ui/enhanced_annotation_panel.py",
        "src/ui/batch_import_dialog.py",
        "src/services/panoramic_image_service.py",
        "src/services/config_file_service.py",
        "src/models/panoramic_annotation.py",
        "src/models/enhanced_annotation.py"
    ]
    
    print("\n🔍 Verifying core files remain in place:")
    all_present = True
    
    for file_path in core_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ MISSING: {file_path}")
            all_present = False
    
    return all_present

def create_summary_report(backup_dir, moved_count):
    """Create a summary report of the cleanup"""
    project_root = Path.cwd()
    report_file = project_root / "cleanup_report.md"
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report_content = f"""# Cleanup Migration Report

**Date:** {timestamp}
**Backup Location:** {backup_dir}
**Files Moved:** {moved_count}

## Core Files Retained

The following core files remain in the `src/` directory:

### Main GUI
- `src/ui/panoramic_annotation_gui.py` (Primary GUI implementation)

### UI Components  
- `src/ui/hole_manager.py`
- `src/ui/hole_config_panel.py`
- `src/ui/enhanced_annotation_panel.py`
- `src/ui/batch_import_dialog.py`

### Services
- `src/services/panoramic_image_service.py`
- `src/services/config_file_service.py`
- `src/services/annotation_engine.py`
- `src/services/image_processor.py`

### Models
- `src/models/panoramic_annotation.py`
- `src/models/enhanced_annotation.py`
- `src/models/annotation.py`
- `src/models/dataset.py`
- `src/models/batch_job.py`

### Core Utilities
- `src/core/config.py`
- `src/core/logger.py`
- `src/core/exceptions.py`

## Archived Files

### Refactored Variants
- Moved to `archive/refactored_variants/`
- Moved to `archive/refactored_components/`
- Moved to `archive/mixin_variants/`

### Tools and Utilities
- Moved to `tools/testing/`
- Moved to `tools/launchers/`
- Moved to `tools/validation/`
- Moved to `tools/automation/`
- Moved to `tools/demo/`
- Moved to `tools/debug/`

### Documentation
- Moved to `docs/`
- Moved to `archive/refactored_docs/`

### Temporary Files
- Moved to `archive/temp_tests/`

## Next Steps

1. Test the main GUI: `python src/ui/panoramic_annotation_gui.py`
2. Update any remaining scripts to reference the correct file paths
3. Review archived files and delete if no longer needed
4. Update documentation to reflect the simplified structure

## Backup

A full backup was created at `{backup_dir}` before migration.
If you need to restore any files, they can be found there.
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"📄 Report created: {report_file}")

def main():
    """Main cleanup function"""
    print("🧹 Starting Panoramic GUI Cleanup Migration")
    print("=" * 60)
    
    # Step 1: Create backup
    backup_dir = create_backup()
    
    # Step 2: Archive files
    print("\n📦 Archiving files...")
    moved_count = archive_files()
    
    # Step 3: Verify core files
    print("\n🔍 Verifying core files...")
    core_intact = verify_core_files()
    
    # Step 4: Create report
    print("\n📄 Creating summary report...")
    create_summary_report(backup_dir, moved_count)
    
    # Final status
    print("\n" + "=" * 60)
    if core_intact:
        print("✅ Cleanup completed successfully!")
        print(f"✅ {moved_count} files archived safely")
        print("✅ Core functionality preserved")
        print(f"🔒 Backup available at: {backup_dir}")
        print("\n🎯 Next: Test the main GUI with:")
        print("   python src/ui/panoramic_annotation_gui.py")
    else:
        print("❌ Cleanup completed with warnings!")
        print("⚠️  Some core files may be missing")
        print("🔧 Check the verification results above")
    
    print("\n📄 See cleanup_report.md for detailed information")

if __name__ == "__main__":
    main()