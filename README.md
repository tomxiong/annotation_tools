# Panoramic Image Annotation Tool

A specialized GUI application for annotating panoramic images in microbiological susceptibility testing. The tool provides precise navigation through 120-well plates (12×10 grid) and comprehensive annotation capabilities.

## 📦 Packaging and Distribution

The project includes comprehensive packaging capabilities for creating standalone executables:

### Pre-built Executables
- **Location**: `release/` directory
- **GUI Version**: `PanoramicAnnotationTool.exe` (69.5 MB)
- **CLI Version**: `annotation-cli.exe` (74.7 MB)
- **Usage**: Run directly without Python environment

### Building from Source
Complete packaging tools are available in the `package/` directory:
- **PACKAGING_GUIDE.md**: Detailed packaging instructions
- **fixed_gui.spec**: PyInstaller configuration for GUI
- **fixed_build.py**: Automated build script
- **hook-tkinter.py**: Custom PyInstaller hooks

### Build Commands
```bash
# Using the automated build script
python build.py

# Using PyInstaller directly
pyinstaller gui.spec
```

### Distribution Features
- **Standalone**: No Python installation required
- **Cross-platform**: Windows executable with proper dependencies
- **Optimized**: UPX compression for smaller file size
- **Complete**: Includes all necessary libraries and resources

## 📂 Project Structure

After cleanup, the project has a clean, organized structure:

```
/                              # Project root
├── src/                        # Core source code
│   ├── ui/
│   │   └── panoramic_annotation_gui.py  # ⭐ Main GUI application
│   ├── services/               # Image and configuration services
│   ├── models/                 # Data models and annotations
│   └── core/                   # Core utilities (config, logger)
├── gui.spec                    # PyInstaller configuration for GUI
├── build.py                    # Automated build script
├── tkinter_hook.py             # Custom PyInstaller hooks
├── tools/                      # Development utilities
│   └── demo/                   # Demo scripts and examples
├── docs/                       # Documentation
├── archive/                    # Archived files and samples
│   ├── batch_files/            # Batch processing scripts
│   └── json_files/             # Sample JSON files
├── tests/                      # Unit tests
├── release/                    # Pre-built executables
│   ├── PanoramicAnnotationTool.exe  # GUI executable
│   ├── annotation-cli.exe      # CLI executable
│   └── README.txt              # Release notes
├── run_gui.py                  # Main GUI launcher
├── run_cli.py                  # CLI launcher
├── requirements.txt            # Project dependencies
├── README.md                   # This file
└── INSTALL.md                  # Installation guide
```

## 🚀 Quick Start

### Option 1: Using Pre-built Executables (Recommended for End Users)

```bash
# Navigate to release directory
cd annotation_tools/release

# Run GUI version (double-click in Windows Explorer)
PanoramicAnnotationTool.exe

# Run CLI version
annotation-cli.exe --help
```

### Option 2: Running from Source (Developers)

#### Environment Setup
```bash
# Navigate to project directory
cd annotation_tools

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

#### Launch the GUI Application
```bash
# Using the launcher script (recommended)
python run_gui.py

# Direct launch
python src/ui/panoramic_annotation_gui.py
```

#### Launch the CLI Application
```bash
python run_cli.py --help
```

### 3. Using the Application

1. **Set Panoramic Directory**: Choose the directory containing your panoramic images
2. **Load Data**: Click "Load Data" to scan for image files
3. **Navigate**: Use arrow keys or click holes to navigate through the 12×10 grid
4. **Annotate**: Select growth levels and microbe types for each hole
5. **Save**: Annotations are automatically saved or use "Save Annotations" button

## 📋 Key Features

### Core Functionality
- **Panoramic Image Display**: View full 12×10 hole layout
- **Precise Navigation**: Navigate to specific holes by coordinates or sequence
- **Multi-level Annotation**: Support for growth levels (negative, weak, positive)
- **Microbe Classification**: Bacteria and fungi annotation support
- **Auto-save**: Automatic annotation persistence
- **Batch Operations**: Annotate entire rows or columns at once

### Data Management
- **Multiple Formats**: Support for various image formats
- **Configuration Import**: Import existing annotation configurations
- **Export Options**: Export training data and annotations
- **Statistics**: Real-time annotation progress tracking

## 🔧 Development Tools

The project includes organized development utilities:

### Core Tools
- **run_gui.py**: Main GUI launcher script
- **run_cli.py**: CLI launcher script
- **requirements.txt**: Project dependencies

### Packaging Tools
- **gui.spec**: PyInstaller configuration for GUI
- **build.py**: Automated build script
- **tkinter_hook.py**: Custom PyInstaller hooks
- **docs/PACKAGING_GUIDE.md**: Comprehensive packaging guide

### Demo and Examples (`tools/demo/`)
- **demo.py**: Main demo script
- **examples/**: Quick start examples
- **run_demo.bat/sh**: Demo launchers

### Testing (`tests/`)
- **unit/**: Unit tests for core functionality

## 📖 Documentation

### Core Documentation
- **Installation guide**: `INSTALL.md`
- **Project README**: `README.md` (this file)
- **Development environment**: `DEVELOPMENT_ENVIRONMENT.md`

### Packaging Documentation (`package/`)
- **PACKAGING_GUIDE.md**: Comprehensive packaging guide
- Build configurations and scripts

### Additional Documentation (`docs/`)
- **ENVIRONMENT_SETUP_STEPS.md**: Environment setup guide
- **FUNCTIONALITY_TESTING_GUIDE.md**: Testing procedures
- **GUI_ENVIRONMENT_SETUP_GUIDE.md**: GUI setup guide
- **STARTUP_GUIDE.md**: Application startup guide
- **batch_annotation_solution.md**: Batch processing documentation

### Archived Documentation (`archive/`)
- Historical documents and analysis reports
- Sample files and batch processing scripts

## 🧪 Testing

### Unit Tests
```bash
# Run all unit tests
python -m pytest tests/unit/

# Run specific test
python -m pytest tests/unit/test_annotation.py
```

### Demo Testing
```bash
# Run the main demo
python tools/demo/demo.py

# Run quick start examples
python tools/demo/examples/quick_start.py
```

### Executable Testing
```bash
# Test pre-built GUI executable
cd release
PanoramicAnnotationTool.exe

# Test pre-built CLI executable
annotation-cli.exe --help
```

## 🔧 Configuration

The application supports various configuration options:

- **Directory Modes**: Subdirectory mode or independent path mode
- **Navigation**: Centered navigation or traditional mode
- **Auto-save**: Configurable automatic annotation saving
- **Image Enhancement**: Automatic image processing for better visibility

## 📊 Data Formats

### Input
- **Images**: PNG, JPG, JPEG, BMP formats
- **Configuration**: .cfg files for importing existing annotations
- **Directory Structure**: Flexible panoramic/slice organization

### Output
- **JSON**: Native annotation format
- **Training Data**: Export for machine learning
- **Statistics**: Annotation progress and summaries

## 🤝 Contributing

The project follows a clean, organized structure:

1. **Core Code**: All essential functionality in `src/`
2. **Development Tools**: Organized utilities in `tools/`
3. **Documentation**: Comprehensive docs in `docs/`
4. **Testing**: Unit tests and verification tools

## 📝 License

This project is developed for microbiological susceptibility testing applications.

## 🆘 Support

For issues or questions:

1. Check the `docs/` directory for detailed documentation
2. Review `INSTALL.md` for setup instructions
3. Use verification tools in `tools/testing/` to diagnose issues
4. Check archived documentation in `archive/` if needed

---

**Note**: This project has been cleaned and organized. Previous variants and temporary files are archived in the `archive/` directory for reference.

1. **模型加载失败**
   - 确保模型文件存在且路径正确
   - 检查是否安装了 `ultralytics` 包

2. **图像处理失败**
   - 检查图像文件格式是否支持
   - 确保图像文件未损坏

3. **配置文件错误**
   - 验证YAML语法是否正确
   - 检查文件路径是否存在

4. **GUI启动失败**
   - 确保已激活虚拟环境 `venv\Scripts\activate`
   - 确保从项目根目录运行 `python run_gui.py`
   - 检查是否安装了所有依赖 `pip install -e .`
   - 查看错误信息，常见错误包括导入错误和模块未找到

5. **相对导入错误**
   - 确保从正确的目录运行脚本
   - 不要直接运行 `python src/ui/panoramic_annotation_gui.py`，应使用 `python run_gui.py`

### 日志查看
```bash
# 确保已激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

tail -f logs/batch_annotation.log  # Linux/Mac
# Windows可以使用: type logs\batch_annotation.log
```

### 虚拟环境使用说明

```bash
# 创建虚拟环境（仅首次设置需要）
cd annotation_tools
python -m venv venv

# 激活虚拟环境（每次使用前都需要）
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装依赖（仅首次设置或更新依赖时需要）
pip install -e .

# 运行GUI
python run_gui.py

# 运行CLI
python run_cli.py

# 退出虚拟环境
deactivate
```

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

---