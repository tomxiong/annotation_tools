# Cleanup Migration Report

**Date:** 2025-08-28 22:33:06
**Backup Location:** D:\dev\annotation_tools\batch_annotation_tool\backup_before_cleanup_20250828_223305
**Files Moved:** 89

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

A full backup was created at `D:\dev\annotation_tools\batch_annotation_tool\backup_before_cleanup_20250828_223305` before migration.
If you need to restore any files, they can be found there.
