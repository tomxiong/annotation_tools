# 启动指南

本文档说明了批量标注工具中各种启动脚本的用途和区别。

> **相关文档**:
> - [README.md](README.md) - 项目主要文档
> - [INSTALL.md](INSTALL.md) - 安装指南
> - [DATA_ORGANIZATION.md](DATA_ORGANIZATION.md) - 数据集组织与标注规范

## 重要说明：项目环境

### 项目目录结构

`batch_annotation_tool` 是项目的根目录，所有命令都应该在这个目录下运行。当使用IDE或其他工具打开项目时，应该将 `batch_annotation_tool` 设置为工作目录。

### 虚拟环境

项目使用Python虚拟环境来隔离依赖项。虚拟环境位于项目根目录下的 `venv` 文件夹中。

- **激活虚拟环境**:
  - Windows: `venv\Scripts\activate`
  - Linux/Mac: `source venv/bin/activate`

- **退出虚拟环境**:
  - 任何系统: `deactivate`

> **注意**: 所有启动脚本都会自动检查虚拟环境是否存在，如果不存在则创建，然后激活环境并安装依赖。但如果您手动运行Python文件，则需要先激活虚拟环境。

## 推荐的启动方式

### 使用启动脚本（最简单）

这些脚本会自动处理虚拟环境和依赖安装：

- **Windows用户**:
  - `start_gui.bat` - 启动图形界面
  - `start_cli.bat` - 启动命令行工具
  - `run_example.bat` - 运行快速开始示例
  - `run_demo.bat` - 运行功能演示
  - `run_batch.bat` - 运行批量标注工具

- **Linux/Mac用户**:
  - `./start_gui.sh` - 启动图形界面
  - `./start_cli.sh` - 启动命令行工具
  - `./run_example.sh` - 运行快速开始示例
  - `./run_demo.sh` - 运行功能演示
  - `./run_batch.sh` - 运行批量标注工具

> **提示**: 
> - 演示脚本可以使用参数，例如 `run_demo.bat init my_project` 或 `./run_demo.sh init my_project` 来初始化项目
> - 批量标注工具也支持参数传递，例如 `run_batch.bat process data/ output/` 或 `./run_batch.sh process data/ output/`

## 启动文件说明

项目中包含多个启动文件，它们的用途如下：

### 启动脚本（自动处理环境）

1. **`start_gui.bat`/`start_gui.sh`**
   - 启动图形用户界面
   - 自动创建和激活虚拟环境
   - 自动安装依赖

2. **`start_cli.bat`/`start_cli.sh`**
   - 启动命令行工具
   - 自动创建和激活虚拟环境
   - 自动安装依赖

3. **`run_example.bat`/`run_example.sh`**
   - 运行快速开始示例
   - 自动创建和激活虚拟环境
   - 自动安装依赖

4. **`run_demo.bat`/`run_demo.sh`**
   - 运行功能演示
   - 支持参数传递（如 `run_demo.bat init my_project`）
   - 自动创建和激活虚拟环境
   - 自动安装依赖

### 核心启动文件

### 1. `run_gui.py`

- **用途**: 简化的GUI启动脚本
- **特点**: 
  - 简单直接，仅包含基本启动逻辑
  - 适合已经设置好环境的用户
- **使用方式**: 
  ```bash
  # 激活虚拟环境后
  python run_gui.py
  ```

### 2. `launch_gui.py`

- **用途**: 增强版GUI启动脚本
- **特点**: 
  - 包含依赖检查功能
  - 提供更详细的错误信息
  - 适合初次使用的用户
- **使用方式**: 
  ```bash
  # 激活虚拟环境后
  python launch_gui.py
  ```

### 3. `panoramic_annotation_tool.py`

- **用途**: 全功能GUI启动脚本
- **特点**: 
  - 包含完整的依赖检查和错误处理
  - 尝试多种导入方式，提高兼容性
  - 适合在不同环境下使用
- **使用方式**: 
  ```bash
  # 激活虚拟环境后
  python panoramic_annotation_tool.py
  ```

### 4. `run_cli.py`

- **用途**: 命令行工具启动脚本
- **特点**: 
  - 提供命令行界面
  - 支持批处理操作
- **使用方式**: 
  ```bash
  # 激活虚拟环境后
  python run_cli.py [命令] [参数]
  ```

### 5. `demo.py`

- **用途**: 功能演示脚本
- **特点**: 
  - 展示核心功能
  - 支持初始化项目
  - 生成示例数据和输出
- **使用方式**: 
  ```bash
  # 激活虚拟环境后
  python demo.py  # 运行演示
  python demo.py init my_project  # 初始化项目
  ```

### 6. `batch_annotation.py`

- **用途**: 批量标注工具入口点
- **特点**: 
  - 解决相对导入问题
  - 直接调用CLI主函数
  - 支持所有CLI命令和参数
- **使用方式**: 
  ```bash
  # 激活虚拟环境后
  python batch_annotation.py [命令] [参数]
  python batch_annotation.py init my_project
  python batch_annotation.py process data/ output/
  ```

## 故障排除

如果遇到启动问题：

1. 确保已激活虚拟环境：
   ```bash
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

2. 确保已安装所有依赖：
   ```bash
   pip install -e .
   ```

3. 检查是否从正确的目录运行脚本（应在 `batch_annotation_tool` 目录下）

4. 如果遇到导入错误，尝试使用 `panoramic_annotation_tool.py`，它有更强的兼容性

## 推荐使用顺序

如果您不确定使用哪个启动文件，建议按以下顺序尝试：

1. 首先使用 `start_gui.bat`/`start_gui.sh`（自动处理环境）
2. 如果遇到问题，尝试 `panoramic_annotation_tool.py`（最兼容）
3. 如果需要更简单的启动，使用 `run_gui.py`（最简洁）
4. 如果需要命令行功能，使用 `start_cli.bat`/`start_cli.sh`（自动处理环境）