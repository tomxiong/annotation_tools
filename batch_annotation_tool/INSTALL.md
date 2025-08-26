# 安装指南

本文档提供了批量标注工具的详细安装和环境配置说明。

## 系统要求

- Python 3.8 或更高版本
- 操作系统：Windows 10/11, macOS, Linux
- 至少 4GB RAM（推荐 8GB 或更多）
- 如果使用 AI 模型，建议有 NVIDIA GPU

## 安装步骤

### 1. 克隆或下载项目

```bash
git clone https://github.com/your-username/batch_annotation_tool.git
cd batch_annotation_tool
```

### 2. 创建并激活虚拟环境

#### Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -e .
```

这将安装项目所需的所有依赖项。

### 4. 验证安装

```bash
# 运行简单测试
python -m pytest tests/unit
```

## 运行应用程序

有关运行应用程序的详细信息，请参阅 [启动指南](STARTUP_GUIDE.md)。

### 运行GUI界面

```bash
# 确保已激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 从项目根目录运行
python run_gui.py
```

### 运行命令行工具

```bash
# 确保已激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 从项目根目录运行
python run_cli.py
```

> **提示**：推荐使用启动脚本（如 `start_gui.bat`/`start_gui.sh`），它们会自动处理虚拟环境和依赖安装。

## 常见问题

### 导入错误

如果遇到 `ModuleNotFoundError` 或 `ImportError`，请确保：

1. 已激活虚拟环境
2. 已安装所有依赖 `pip install -e .`
3. 从正确的目录运行脚本（应该在 `batch_annotation_tool` 目录下）

### 相对导入错误

如果遇到 `attempted relative import beyond top-level package` 错误：

1. 不要直接运行模块文件（如 `python src/ui/panoramic_annotation_gui.py`）
2. 应该使用提供的启动脚本（如 `python run_gui.py`）

### 依赖冲突

如果遇到依赖冲突，可以尝试：

```bash
pip install -e . --upgrade --force-reinstall
```

## 卸载

如果需要卸载：

1. 退出虚拟环境：`deactivate`
2. 删除项目目录和虚拟环境