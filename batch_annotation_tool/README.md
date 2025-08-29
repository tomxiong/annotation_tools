# Panoramic Image Annotation Tool

A specialized GUI application for annotating panoramic images in microbiological susceptibility testing. The tool provides precise navigation through 120-well plates (12×10 grid) and comprehensive annotation capabilities.

## 📂 Project Structure

After cleanup, the project has a clean, organized structure:

```
batch_annotation_tool/           # Project root
├── src/                        # Core source code
│   ├── ui/
│   │   └── panoramic_annotation_gui.py  # ⭐ Main GUI application
│   ├── services/               # Image and configuration services
│   ├── models/                 # Data models and annotations
│   └── core/                   # Core utilities (config, logger)
├── tools/                      # Development utilities
│   ├── launchers/              # GUI startup scripts
│   ├── testing/                # Test utilities
│   ├── cli/                    # CLI tools
│   ├── demo/                   # Demo scripts
│   └── build/                  # Build scripts
├── docs/                       # Documentation
├── archive/                    # Archived files and reports
├── tests/                      # Unit tests
├── venv/                       # Python virtual environment
├── README.md                   # This file
└── INSTALL.md                  # Installation guide
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Navigate to project directory
cd batch_annotation_tool

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e .
```

### 2. Launch the GUI Application

#### Method 1: Direct Launch (Recommended)
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Launch the main GUI
python src/ui/panoramic_annotation_gui.py
```

#### Method 2: Using Launcher Scripts
```bash
# Windows
tools\launchers\start_gui.bat

# Linux/Mac
./tools/launchers/start_gui.sh
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

- **tools/testing/**: Testing utilities and verification scripts
- **tools/launchers/**: GUI startup scripts for different environments
- **tools/cli/**: Command-line interface tools
- **tools/demo/**: Demo scripts and examples
- **tools/build/**: Build and setup scripts

## 📖 Documentation

Detailed documentation is available in the `docs/` directory:

- Installation guide: `INSTALL.md`
- Project documentation: `docs/`
- Cleanup reports: `final_cleanup_report.md`

## 🧪 Testing

```bash
# Run unit tests
python -m pytest tests/unit

# Run GUI verification
python tools/testing/final_verification.py
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
   - 确保从项目根目录 `batch_annotation_tool` 运行 `python run_gui.py`
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
cd batch_annotation_tool
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

**我又完成一项光荣的任务** 🎉