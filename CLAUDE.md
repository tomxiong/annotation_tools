# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based panoramic image annotation tool designed for microbiological susceptibility testing. The application provides a modern, modular GUI for annotating 120-well plates (12×10 grid) with precise navigation and comprehensive annotation capabilities.

**Key Features:**
- **Modular Architecture**: Event-driven, component-based design with clear separation of concerns
- **Advanced UI**: Modern Tkinter-based interface with MVC pattern implementation
- **Real-time Processing**: Efficient image processing with OpenCV and PIL
- **Batch Operations**: Support for bulk annotation and data import/export
- **Model Integration**: AI model suggestion import capabilities
- **Cross-platform**: Windows executable distribution with PyInstaller

## Common Development Commands

### Running the Application

**GUI Application (Modern Architecture):**
```bash
# Using the launcher script (recommended)
python run_gui.py

# Direct launch of main application
python src/ui/main/app.py

# Legacy GUI (deprecated)
python src/ui/panoramic_annotation_gui.py
```

**CLI Application:**
```bash
# CLI is currently disabled in build process
python run_cli.py --help
```

### Testing

**Unit Tests:**
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run specific test
python -m pytest tests/unit/test_annotation.py

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html
```

**Architecture Validation Tests:**
```bash
# Quick architecture validation
python -c "
from src.core.config import get_config
from src.core.logger import get_logger
from src.ui.utils.event_bus import EventBus, EventType
print('✅ Core systems validated')
"

# Full component test
python -c "
from src.ui.models.ui_state import UIStateManager
from src.services.panoramic_image_service import PanoramicImageService
from src.services.annotation_engine import AnnotationEngine
print('✅ All components importable')
"
```

**Demo Testing:**
```bash
# Run the main demo
python tools/demo/demo.py

# Run quick start examples
python tools/demo/examples/quick_start.py
```

### Building and Packaging

**Build Executable:**
```bash
# Using the automated build script (recommended)
python build.py

# Using PyInstaller directly
pyinstaller gui.spec

# Clean build with debug info
python build.py --clean --debug
```

**Virtual Environment Setup:**
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install pytest pytest-cov black flake8 mypy
```

**Development Workflow:**
```bash
# Setup development environment
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Run tests
python -m pytest tests/unit/

# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

## Architecture Overview

### Modern Modular Architecture

The project follows a **component-based, event-driven architecture** with clear separation of concerns:

**🎯 Design Principles:**
- **Event-Driven**: Centralized event bus for loose coupling between components
- **MVC Pattern**: Clear separation between Models, Views, and Controllers
- **Dependency Injection**: Service container for component management
- **Modular Design**: Highly cohesive, loosely coupled modules

### Core Components

**UI Layer (`src/ui/`):**
- **`main/app.py`** - Main application entry point with service container
- **`panoramic_annotation_gui.py`** - Legacy GUI (being phased out)
- **`enhanced_annotation_panel.py`** - Advanced annotation interface
- **`batch_import_dialog.py`** - Batch processing interface

**UI Components (`src/ui/components/`):**
- **`image_canvas.py`** - Image display and interaction canvas
- **`navigation_panel.py`** - Navigation controls and hole selection
- **`annotation_panel.py`** - Annotation editing interface

**UI Controllers (`src/ui/controllers/`):**
- **`main_controller.py`** - Main application controller coordinating all components
- **`image_controller.py`** - Image processing and display controller
- **`annotation_controller.py`** - Annotation logic and state management
- **`ui_manager.py`** - UI state and component coordination
- **`navigation_manager.py`** - Navigation logic and hole management
- **`statistics_manager.py`** - Statistics tracking and reporting
- **`file_manager.py`** - File operations and data persistence

**UI Models & Utils (`src/ui/models/`, `src/ui/utils/`):**
- **`ui_state.py`** - Centralized UI state management
- **`event_bus.py`** - Event system for component communication
- **`base_components.py`** - Base classes for UI components

**Business Logic (`src/services/`):**
- **`panoramic_image_service.py`** - Image loading and processing with Tkinter integration
- **`annotation_engine.py`** - Core annotation logic and validation
- **`config_file_service.py`** - Configuration file management
- **`model_suggestion_import_service.py`** - AI model integration and suggestions
- **`image_processor.py`** - Advanced image processing utilities

**Data Models (`src/models/`):**
- **`panoramic_annotation.py`** - Main panoramic annotation data structure
- **`enhanced_annotation.py`** - Extended annotation with growth patterns
- **`simple_panoramic_annotation.py`** - Lightweight annotation model
- **`annotation.py`** - Base annotation model with validation
- **`batch_job.py`** - Batch processing job management
- **`dataset.py`** - Dataset management and organization

**Core System (`src/core/`):**
- **`app.py`** - Application lifecycle and service management
- **`config.py`** - Configuration management with YAML support
- **`logger.py`** - Structured logging with performance tracking
- **`exceptions.py`** - Custom exception hierarchy
- **`utils.py`** - General utility functions and helpers

**CLI Interface (`src/cli/`):**
- **`main.py`** - Command-line interface (currently disabled in build)

### Key Design Patterns

**🏗️ Architectural Patterns:**
- **Event-Driven Architecture**: Centralized event bus for component communication
- **Model-View-Controller (MVC)**: Clear separation in UI components
- **Dependency Injection**: Service container pattern for loose coupling
- **Observer Pattern**: Event subscription system for reactive updates
- **Factory Pattern**: Component creation and service instantiation

**🎯 Component Design:**
- **Modular UI**: Component-based architecture with reusable parts
- **Service Layer**: Business logic abstraction with clean interfaces
- **Data Models**: Rich domain models with validation and serialization
- **Configuration Management**: Hierarchical configuration with environment support

**🔄 Data Flow Patterns:**
- **Annotation System**: 12×10 grid with growth level classification
- **State Management**: Centralized UI state with reactive updates
- **Image Processing Pipeline**: Multi-stage processing with caching
- **Persistence Layer**: JSON-based storage with migration support

**🛠️ Development Patterns:**
- **Test-Driven Development**: Comprehensive unit test coverage
- **Clean Code**: Descriptive naming and single responsibility principle
- **Error Handling**: Structured exception hierarchy with recovery
- **Logging**: Multi-level logging with performance tracking

## Important File Notes

**Launcher Scripts:**
- `run_gui.py` - Main GUI launcher (modern architecture)
- `run_cli.py` - CLI launcher (currently disabled in build)
- `build.py` - Automated build script with PyInstaller integration

**Configuration Files:**
- `requirements.txt` - Python dependencies (Pillow, OpenCV, NumPy, PyYAML, PyInstaller)
- `gui.spec` - PyInstaller configuration for GUI executable
- `PanoramicAnnotationTool.spec` - Alternative PyInstaller spec
- `tkinter_hook.py` - Custom PyInstaller hooks for Tkinter components
- `config/app.yaml` - Application configuration file

**Project Structure:**
- `src/` - Main source code directory
  - `src/ui/main/app.py` - Modern application entry point
  - `src/ui/controllers/` - MVC controllers (main, image, annotation, ui, etc.)
  - `src/ui/components/` - Reusable UI components (canvas, panels, etc.)
  - `src/ui/models/` - UI state management
  - `src/ui/utils/` - UI utilities (event bus, base components)
  - `src/services/` - Business logic services
  - `src/models/` - Data models and validation
  - `src/core/` - Core system components (config, logger, exceptions, utils)
- `tests/unit/` - Unit tests for all major components
- `tools/demo/` - Demo scripts and examples
- `docs/` - Documentation and guides
- `release/` - Pre-built executables

**Release Artifacts:**
- `release/PanoramicAnnotationTool.exe` - GUI executable (~70MB)
- `release/README.txt` - Release notes and usage instructions

## Development Environment Setup

### 1. Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install core dependencies
pip install -r requirements.txt

# Install development tools (optional)
pip install pytest pytest-cov black flake8 mypy pre-commit
```

### 2. Development Workflow
```bash
# Code formatting
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Run tests with coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### 3. Running the Application
```bash
# Modern architecture (recommended)
python run_gui.py

# Direct launch
python src/ui/main/app.py

# Legacy GUI (deprecated)
python src/ui/panoramic_annotation_gui.py
```

## Testing Strategy

### Unit Testing
- **Location**: `tests/unit/` directory
- **Coverage**: Core components, models, services, and utilities
- **Framework**: pytest with standard assertions
- **Run Command**: `python -m pytest tests/unit/`

### Architecture Validation
- **Quick Validation**: Inline Python commands for component testing
- **Integration Tests**: Event system and service container validation
- **Performance Tests**: Built into logger with timing decorators

### Manual Testing
- **Demo Scripts**: `tools/demo/` for feature demonstration
- **Executable Testing**: Pre-built binaries in `release/` directory
- **UI Testing**: Interactive testing with the GUI application

### Test Categories
1. **Component Tests**: Individual class and function testing
2. **Integration Tests**: Component interaction and data flow
3. **System Tests**: End-to-end functionality validation
4. **Performance Tests**: Operation timing and resource usage

## Debugging and Maintenance

### Common Issues & Solutions

**1. Import Errors:**
```bash
# Ensure proper Python path
cd /path/to/project
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python run_gui.py
```

**2. Tkinter Issues:**
```bash
# Test Tkinter installation
python -c "import tkinter; print('Tkinter OK')"
python -c "from tkinter import ttk; print('TTK OK')"
```

**3. Event System Debugging:**
```bash
# Test event bus
python -c "
from src.ui.utils.event_bus import EventBus, EventType
bus = EventBus()
print('Event system initialized')
"
```

**4. Configuration Issues:**
```bash
# Validate configuration
python -c "
from src.core.config import get_config
config = get_config()
print(f'Config loaded: {config.database.host}')
"
```

### Maintenance Tasks

**Regular Maintenance:**
- Run unit tests: `pytest tests/unit/`
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Clean build artifacts: `python build.py --clean`
- Check logs: `tail -f logs/*.log`

**Code Quality:**
- Format code: `black src/ tests/`
- Lint code: `flake8 src/ tests/`
- Type check: `mypy src/`

## Packaging and Distribution

### Build Process
```bash
# Standard build
python build.py

# Clean build
python build.py --clean

# Debug build
python build.py --debug
```

### Distribution Artifacts
- **Executable**: `release/PanoramicAnnotationTool.exe` (~70MB)
- **Documentation**: `release/README.txt`
- **Requirements**: No Python installation needed on target system

### PyInstaller Configuration
- **Main Spec**: `gui.spec` - Primary build configuration
- **Hooks**: `tkinter_hook.py` - Tkinter component inclusion
- **Data Files**: Source code and configuration files included
- **Exclusions**: Test files and development dependencies excluded

## Quick Reference

### Component Architecture Map
```
src/
├── ui/
│   ├── main/app.py              # 🚀 Application Entry
│   ├── controllers/             # 🎮 UI Controllers (MVC)
│   │   ├── main_controller.py   # Main coordinator
│   │   ├── image_controller.py  # Image handling
│   │   └── annotation_controller.py # Annotation logic
│   ├── components/              # 🧩 Reusable UI Components
│   │   ├── image_canvas.py      # Image display
│   │   ├── navigation_panel.py  # Navigation controls
│   │   └── annotation_panel.py  # Annotation editor
│   ├── models/ui_state.py       # 📊 UI State Management
│   └── utils/event_bus.py       # 📡 Event System
├── services/                    # 🔧 Business Logic
│   ├── panoramic_image_service.py
│   ├── annotation_engine.py
│   └── config_file_service.py
├── models/                      # 📋 Data Models
│   ├── panoramic_annotation.py
│   └── enhanced_annotation.py
└── core/                        # ⚙️ Core System
    ├── config.py                # Configuration
    ├── logger.py                # Logging
    └── exceptions.py            # Error handling
```

### Development Best Practices

**Code Organization:**
- Keep controllers focused on coordination, not business logic
- Use services for complex business operations
- Maintain clear separation between UI and data layers
- Follow single responsibility principle

**Event System Usage:**
- Use descriptive event names with `EventType` enum
- Include relevant data in event payloads
- Handle events asynchronously when possible
- Document event flow in complex interactions

**Error Handling:**
- Use custom exceptions from `src.core.exceptions`
- Log errors with appropriate severity levels
- Provide user-friendly error messages
- Implement graceful degradation

**Testing:**
- Write unit tests for all new components
- Test event interactions and state changes
- Validate error conditions and edge cases
- Use fixtures for common test data

### Performance Considerations

**Image Processing:**
- Use efficient image formats (PNG preferred)
- Implement lazy loading for large datasets
- Cache processed images when possible
- Optimize canvas redraw operations

**Memory Management:**
- Clean up Tkinter widgets properly
- Use weak references for event listeners
- Implement proper resource disposal
- Monitor memory usage in long-running operations

**UI Responsiveness:**
- Perform heavy operations in background threads
- Use progress indicators for long operations
- Implement virtual scrolling for large datasets
- Optimize event handling to prevent UI blocking