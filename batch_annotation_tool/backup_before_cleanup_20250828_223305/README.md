# 批量标注工具 MVP

基于AI的图像批量标注解决方案，支持YOLO模型集成和多种导出格式。

## 📂 项目结构

> **重要说明**: `batch_annotation_tool` 是项目的根目录，所有命令都应该在这个目录下运行。项目使用虚拟环境（`venv`）来隔离依赖项。

```
batch_annotation_tool/           # 主项目目录
├── src/                        # 源代码
│   ├── core/                   # 核心功能
│   ├── models/                 # 数据模型
│   ├── services/               # 业务服务
│   ├── cli/                    # 命令行接口
│   └── ui/                     # 用户界面
├── tests/                      # 测试用例
├── config/                     # 配置文件
├── venv/                       # 虚拟环境（安装后生成）
├── run_gui.py                  # GUI启动脚本
├── run_cli.py                  # CLI启动脚本
└── setup.py                    # 安装配置
```

## 🚀 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd batch_annotation_tool

# 创建并激活虚拟环境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安装项目依赖
pip install -e .
```

### 2. 运行应用程序

#### 使用启动脚本（推荐）

**运行GUI界面：**
```bash
# Windows
start_gui.bat

# Linux/Mac
./start_gui.sh
```

**运行命令行工具：**
```bash
# Windows
start_cli.bat init my_project

# Linux/Mac
./start_cli.sh init my_project
```

> **注意**: 项目中包含多个启动文件（run_gui.py、launch_gui.py、panoramic_annotation_tool.py），请参阅 [启动指南](STARTUP_GUIDE.md) 了解它们的区别和用途。

#### 手动运行

**运行GUI界面：**
```bash
# 确保已激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 运行GUI
python run_gui.py
```

**运行命令行工具：**
```bash
# 确保已激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 运行CLI
python run_cli.py init my_project
```

### 3. 运行示例和演示

#### 快速开始示例

```bash
# Windows
run_example.bat

# Linux/Mac
./run_example.sh
```

这将运行一个简单的示例，展示批量标注工具的基本功能，并在 `demo_output` 目录中生成示例输出文件。

#### 功能演示

```bash
# Windows
run_demo.bat

# Linux/Mac
./run_demo.sh
```

您还可以使用参数初始化项目：

```bash
# Windows
run_demo.bat init my_project

# Linux/Mac
./run_demo.sh init my_project
```

#### 批量标注工具

```bash
# Windows
run_batch.bat [命令] [参数]

# Linux/Mac
./run_batch.sh [命令] [参数]
```

例如：

```bash
# 初始化项目
run_batch.bat init my_project

# 处理图像
run_batch.bat process data/ output/
```

### 2. 初始化项目

```bash
python -m cli.main init my_annotation_project
cd my_annotation_project
```

这将创建以下目录结构：
```
my_annotation_project/
├── config/
│   └── config.yaml      # 配置文件
├── data/               # 输入图像目录
├── models/             # AI模型目录
├── output/             # 输出结果目录
└── logs/               # 日志文件目录
```

### 3. 准备数据

将要标注的图像放入 `data/` 目录：
```bash
cp /path/to/your/images/* data/
```

支持的图像格式：`.jpg`, `.jpeg`, `.png`, `.bmp`

### 4. 批量处理

```bash
# 基础处理（仅图像处理，无AI标注）
python -m cli.main process data/ output/

# 使用AI模型标注（需要模型文件）
python -m cli.main process data/ output/ --model yolo_v8 --model-path models/yolo_v8.pt

# 指定输出格式
python -m cli.main process data/ output/ --format coco --dataset-name my_dataset
```

### 5. 导出结果

```bash
# 导出为COCO格式
python -m cli.main export output/my_dataset.json output/annotations.coco --format coco

# 导出为CSV格式
python -m cli.main export output/my_dataset.json output/annotations.csv --format csv
```

## 📋 命令参考

### init - 初始化项目
```bash
python -m cli.main init <project_dir> [--force]
```
- `project_dir`: 项目目录路径
- `--force`: 强制覆盖现有配置

### process - 批量处理
```bash
python -m cli.main process <input_dir> <output_dir> [options]
```
**参数：**
- `input_dir`: 输入图像目录
- `output_dir`: 输出结果目录

**选项：**
- `--config`: 配置文件路径 (默认: config/config.yaml)
- `--model`: 模型名称 (如: yolo_v8)
- `--model-path`: 模型文件路径
- `--format`: 输出格式 (json/coco/csv)
- `--dataset-name`: 数据集名称

### export - 导出结果
```bash
python -m cli.main export <input_file> <output_file> --format <format>
```
- `input_file`: 输入JSON文件
- `output_file`: 输出文件路径
- `--format`: 导出格式 (json/coco/csv)

### status - 查看状态
```bash
python -m cli.main status <project_dir>
```

## ⚙️ 配置文件

`config/config.yaml` 示例：
```yaml
# 日志配置
logging:
  level: INFO
  file_path: logs/batch_annotation.log
  max_file_size: 10485760  # 10MB
  backup_count: 5

# 处理配置
processing:
  batch_size: 32
  max_workers: 4
  confidence_threshold: 0.5

# 模型配置
models:
  default_model: yolo_v8
  model_path: models/

# 输出配置
output:
  format: coco  # json, coco, csv
  output_dir: output/
```

## 📊 输出格式

### JSON格式
标准的数据集JSON格式，包含完整的标注信息和元数据。

### COCO格式
符合COCO数据集标准的JSON格式，适用于深度学习训练。

### CSV格式
简化的表格格式，包含基本的标注信息：
```csv
image_id,label,bbox_x,bbox_y,bbox_w,bbox_h,confidence
image1.jpg,person,100,200,50,100,0.95
```

## 📁 数据集组织

关于如何组织数据集和标注规范，请参阅 [数据集组织与标注规范](DATA_ORGANIZATION.md) 文档。该文档提供了：

- 推荐的数据集目录结构
- 标注分类体系（主分类和辅助标签）
- 图像预处理建议
- 标注规范和边界案例处理
- 数据划分策略
- 元数据记录格式
- 最佳实践

## 🔧 开发信息

### 项目结构详解
```
batch_annotation_tool/
├── src/
│   ├── core/           # 核心功能
│   │   ├── config.py   # 配置管理
│   │   ├── logger.py   # 日志系统
│   │   └── exceptions.py # 异常定义
│   ├── models/         # 数据模型
│   │   ├── annotation.py # 标注数据模型
│   │   ├── dataset.py  # 数据集模型
│   │   ├── batch_job.py # 批处理作业模型
│   │   ├── panoramic_annotation.py # 全景图标注模型
│   │   └── enhanced_annotation.py # 增强标注模型
│   ├── services/       # 业务服务
│   │   ├── image_processor.py # 图像处理服务
│   │   ├── annotation_engine.py # 标注引擎
│   │   ├── panoramic_image_service.py # 全景图服务
│   │   └── config_file_service.py # 配置文件服务
│   ├── cli/            # 命令行接口
│   │   └── main.py     # CLI主入口
│   └── ui/             # 用户界面
│       ├── panoramic_annotation_gui.py # 全景标注GUI
│       ├── hole_manager.py # 孔位管理器
│       ├── hole_config_panel.py # 孔位配置面板
│       ├── enhanced_annotation_panel.py # 增强标注面板
│       └── batch_import_dialog.py # 批量导入对话框
├── tests/              # 测试用例
├── config/             # 配置文件
├── venv/               # 虚拟环境（安装后生成）
├── run_gui.py          # GUI启动脚本
├── run_cli.py          # CLI启动脚本
└── setup.py            # 安装配置
```

### 运行测试
```bash
# 确保已激活虚拟环境
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

python -m pytest tests/ -v
```

### 测试覆盖率
当前测试覆盖率：91.1% (72/79 测试通过)

## 🤖 AI模型支持

目前支持YOLO系列模型：
- YOLOv8 (推荐)
- YOLOv5
- 自定义YOLO模型

**注意：** 需要安装 `ultralytics` 包来使用YOLO模型：
```bash
pip install ultralytics
```

## 📝 使用示例

### 完整工作流程
```bash
# 1. 创建项目
python -m cli.main init animal_detection
cd animal_detection

# 2. 复制图像到data目录
cp ~/Pictures/animals/* data/

# 3. 下载YOLO模型（可选）
# wget https://github.com/ultralytics/yolov5/releases/download/v6.0/yolov5s.pt -O models/yolo_v5.pt

# 4. 批量处理
python -m cli.main process data/ output/ --dataset-name animals --format coco

# 5. 查看结果
python -m cli.main status .
ls output/
```

### 仅图像处理（无AI标注）
```bash
python -m cli.main process data/ output/ --dataset-name images_only
```

### 自定义配置
```bash
# 修改 config/config.yaml 后运行
python -m cli.main process data/ output/ --config config/custom_config.yaml
```

## 🐛 故障排除

### 常见问题

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