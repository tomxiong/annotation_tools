---
applyTo: "**"
---

# Panoramic Annotation Tool - AI Agent Instructions

## Project Overview

A specialized Python/Tkinter GUI application for annotating 120-well plates (12×10 grid) in microbiological susceptibility testing. The project uses a mixed Chinese/English codebase with comprehensive logging and error handling.

## Critical Architecture Patterns

### Import Strategy with Fallbacks
The codebase uses a defensive import pattern throughout:
```python
try:
    from src.utils.logger import log_debug, log_error
except ImportError as e:
    # Always provide fallback logging
    def log_debug(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
```
**Key Rule**: When adding imports, always include ImportError handling with fallback implementations.

### 12×10 Grid Domain Logic
- **Grid Layout**: 12 columns × 10 rows = 120 holes total
- **Hole Numbering**: 1-120 (not 0-indexed)
- **Navigation**: `current_hole_number` is the primary navigation state
- **Data Structure**: `{panoramic_id}_{hole_number}` as unique keys

### Logging Categories
Use specific logging categories for debugging:
- `log_debug("message", "NAV")` - Navigation operations
- `log_debug("message", "ANN")` - Annotation operations  
- `log_debug("message", "IMG")` - Image processing
- `log_debug("message", "UI")` - UI state changes

## Essential Development Workflows

### Running the Application
```bash
# Primary launch method
python run_gui.py

# Direct launch (fallback)
python src/ui/panoramic_annotation_gui.py
```

### Building Executables
```bash
# Automated build with all dependencies
python build.py

# Manual PyInstaller (for debugging)
pyinstaller gui.spec
```

### Testing Strategy
```bash
# Run unit tests
python -m pytest tests/unit/

# Architecture validation (quick check)
python -c "
from src.core.config import get_config
from src.services.panoramic_image_service import PanoramicImageService
print('✅ Core components validated')
"
```

## Project-Specific Conventions

### Configuration Management
- **Main Config**: `config/app.yaml` - YAML-based hierarchical config
- **Grid Settings**: `grid_cols: 10`, `grid_rows: 12` (immutable business rules)
- **Growth Levels**: `[negative, weak, positive]` (3-level classification)

### Data Models Architecture
- **Base**: `Annotation` → **Extended**: `PanoramicAnnotation` → **Enhanced**: `EnhancedAnnotation`
- **Services**: Business logic in `src/services/` (image, config, suggestions)
- **Models**: Pure data structures in `src/models/` with validation

### Error Handling Pattern
Always handle missing dependencies gracefully:
```python
# Pattern used throughout codebase
try:
    from src.specific.module import functionality
except ImportError as e:
    print(f"模块导入失败: {e}")  # Chinese error messages common
    sys.exit(1)  # Or provide fallback
```

## Integration Points

### PyInstaller Packaging
- **Hidden Imports**: Extensive tkinter module collection in `gui.spec`
- **Data Bundling**: `--add-data=src;src` pattern for source inclusion
- **Dependencies**: PIL, OpenCV, NumPy, PyYAML (core stack)

### File Structure Awareness
- **Entry Points**: `run_gui.py`, `run_cli.py` (CLI disabled in build)
- **Core Services**: Single responsibility services in `src/services/`
- **Archive Pattern**: `archive/` contains historical implementations and debug scripts
- **Release Artifacts**: Pre-built executables in `release/` (~70MB GUI)

### Debug Script Workflow
1. Create debug scripts in `archive/debug_scripts/` during development
2. Summarize findings to markdown in `docs/`
3. Remove debug scripts after feature completion
4. This prevents code bloat while maintaining investigation history

## Key Files for Understanding

- `src/ui/panoramic_annotation_gui.py` - Main 6K+ line GUI implementation
- `src/services/panoramic_image_service.py` - Image processing and display logic
- `src/models/panoramic_annotation.py` - Core data model with 12×10 grid logic
- `config/app.yaml` - Business rules and application configuration
- `build.py` - Complete packaging workflow with dependency management

