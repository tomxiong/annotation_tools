# 全景标注工具启动指南

本文档说明如何启动全景标注工具的不同版本。

## 🚀 推荐启动方式

### 方式1：使用主启动脚本（推荐）
```bash
cd batch_annotation_tool
python start_gui.py
```

这个脚本会自动选择最佳的GUI版本：
1. 优先尝试启动重构版本（模块化架构）
2. 如果重构版本不可用，回退到原始版本
3. 自动检测并报告启动状态

### 方式2：直接启动重构版本
```bash
cd batch_annotation_tool/src/ui
python start_refactored_gui.py
```

### 方式3：启动原始版本
```bash
cd batch_annotation_tool/src/ui
python panoramic_annotation_gui.py
```

## 📋 版本对比

### 重构版本（推荐）
- ✅ 模块化架构，易于维护
- ✅ 代码分离，职责明确
- ✅ 完整的全景图导航功能
- ✅ 更好的扩展性
- 📁 文件结构：
  - `panoramic_annotation_gui_refactored.py` - 主GUI类
  - `navigation_controller.py` - 导航控制
  - `annotation_manager.py` - 标注管理
  - `image_display_controller.py` - 图像显示
  - `event_handlers.py` - 事件处理
  - `ui_components.py` - UI组件

### 原始版本（兼容性）
- ✅ 单文件架构，简单直接
- ✅ 集成了全景图导航功能
- ✅ 保持向后兼容
- ⚠️ 代码较大，维护困难
- 📁 文件结构：
  - `panoramic_annotation_gui.py` - 单一大文件

## 🔧 测试和调试

### 测试所有版本
```bash
cd batch_annotation_tool/src/ui
python test_panoramic_gui.py
```

这个脚本会：
1. 测试原始GUI版本
2. 测试重构GUI版本
3. 检查全景图导航功能
4. 启动可用的版本

### 调试模式启动
如果遇到问题，可以使用详细的启动脚本：
```bash
cd batch_annotation_tool/src/ui
python start_refactored_gui.py
```

这会显示详细的启动信息和组件检查结果。

## 🎯 全景图导航功能

两个版本都包含完整的全景图导航功能：

### UI组件
- **上一个全景图按钮** (◀ 上一全景)
- **全景图下拉列表** - 显示所有可用的全景图ID
- **下一个全景图按钮** (下一全景 ▶)

### 功能特性
- 🔄 循环导航（从最后一个到第一个）
- 💾 自动保存当前标注
- 🎯 自动加载目标全景图的第一个孔位
- 📋 下拉列表直接选择任意全景图

### 导航面板布局
1. **全景图导航** - 全景图级别的切换
2. **方向导航** - 基于孔位二维布局（上下左右）
3. **序列导航** - 基于切片文件列表顺序

## 🛠️ 故障排除

### 常见问题

1. **导入错误**
   ```
   ImportError: No module named 'xxx'
   ```
   - 确保在正确的目录中运行
   - 检查Python路径设置

2. **属性错误**
   ```
   AttributeError: 'PanoramicAnnotationGUI' object has no attribute 'go_prev_panoramic'
   ```
   - 使用更新后的版本
   - 运行测试脚本检查功能完整性

3. **文件缺失**
   - 确保所有必要的模块文件都存在
   - 使用 `start_refactored_gui.py` 检查文件完整性

### 获取帮助

如果遇到问题：
1. 运行测试脚本检查状态
2. 查看启动脚本的详细输出
3. 检查错误日志和堆栈跟踪

## 📝 开发说明

### 添加新功能
- 重构版本：在相应的控制器模块中添加
- 原始版本：在主GUI类中添加

### 修改UI
- 重构版本：修改 `ui_components.py`
- 原始版本：修改主GUI类的相关方法

### 扩展导航功能
- 重构版本：修改 `navigation_controller.py`
- 原始版本：在主GUI类中添加方法