# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based panoramic image annotation tool designed for microbiological susceptibility testing. The application provides a GUI for annotating 120-well plates (12×10 grid) with precise navigation and comprehensive annotation capabilities.

## Common Development Commands

### Running the Application

**GUI Application:**
```bash
# Using the launcher script (recommended)
python run_gui.py

# Direct launch
python src/ui/panoramic_annotation_gui.py
```

**CLI Application:**
```bash
python run_cli.py --help
```

### Testing

**Unit Tests:**
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run specific test
python -m pytest tests/unit/test_annotation.py
```

**Demo Testing:**
```bash
# Run the main demo
python tools/demo/demo.py
```

### Building and Packaging

**Build Executable:**
```bash
# Using the automated build script
python build.py

# Using PyInstaller directly
pyinstaller gui.spec
```

**Virtual Environment Setup:**
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Architecture Overview

### Core Components

**UI Layer (`src/ui/`):**
- `panoramic_annotation_gui.py` - Main GUI application with Tkinter
- `enhanced_annotation_panel.py` - Advanced annotation interface
- `hole_config_panel.py` - Configuration panel for individual holes
- `batch_import_dialog.py` - Batch processing interface
- `hole_manager.py` - Manages hole navigation and state

**Business Logic (`src/services/`):**
- `panoramic_image_service.py` - Image loading and processing
- `annotation_engine.py` - Core annotation logic
- `config_file_service.py` - Configuration file management
- `image_processor.py` - Image enhancement and processing
- `model_suggestion_import_service.py` - AI model integration

**Data Models (`src/models/`):**
- `panoramic_annotation.py` - Main annotation data structure
- `enhanced_annotation.py` - Extended annotation features
- `simple_panoramic_annotation.py` - Lightweight annotation model
- `batch_job.py` - Batch processing job management
- `dataset.py` - Dataset management
- `annotation.py` - Base annotation model

**Core Utilities (`src/core/`):**
- `config.py` - Application configuration
- `logger.py` - Structured logging
- `exceptions.py` - Custom exceptions

**CLI Interface (`src/cli/`):**
- `main.py` - Command-line interface entry point

### Key Design Patterns

**Modular Architecture:**
- Clear separation between UI, business logic, and data models
- Service-oriented design for loose coupling
- Model-View-Controller pattern in GUI components

**Annotation System:**
- 12×10 grid layout representing microbiological plates
- Support for growth levels (negative, weak, positive)
- Microbe classification (bacteria and fungi)
- Auto-save functionality with JSON persistence

**Image Processing:**
- Panoramic image display with precise navigation
- Image enhancement for better visibility
- Support for multiple image formats (PNG, JPG, JPEG, BMP)

## Important File Notes

**Launcher Scripts:**
- `run_gui.py` - Main GUI launcher (may be corrupted, use direct launch)
- `run_cli.py` - CLI launcher (may be corrupted, use direct launch)
- `build.py` - Build script for creating executables

**Configuration:**
- `requirements.txt` - Python dependencies
- `gui.spec` - PyInstaller configuration for GUI
- `tkinter_hook.py` - Custom PyInstaller hooks for Tkinter

**Release Artifacts:**
- `release/` directory contains pre-built executables
- `PanoramicAnnotationTool.exe` - GUI executable (69.5 MB)
- `annotation-cli.exe` - CLI executable (74.7 MB)

## Development Environment Setup

1. **Virtual Environment:** Always use a virtual environment for dependency management
2. **Dependencies:** Install from `requirements.txt` which includes Pillow, OpenCV, NumPy, PyYAML, and PyInstaller
3. **Running:** Use direct launch (`python src/ui/panoramic_annotation_gui.py`) if launcher scripts are corrupted
4. **Building:** Use `build.py` or PyInstaller with the provided spec files

## Testing Strategy

- Unit tests in `tests/unit/` for core functionality
- Demo scripts in `tools/demo/` for manual testing
- Executable testing using pre-built binaries in `release/` directory

## Packaging and Distribution

The project supports creating standalone executables using PyInstaller. The `release/` directory contains pre-built Windows executables that don't require Python installation.