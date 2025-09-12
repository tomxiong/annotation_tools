# 功能简化计划

基于现有功能，需要从需求方去精简设计：

## 1. 全景图和切片图文件名和目录结构仅支持子目录模式

**目标**：去掉对于非子目录模式的相关实现

**当前实现**：
- `DataManager` 支持两种模式：
  - 子目录模式：`<全景图>/hole_<num>.png`
  - 独立模式：`<全景图>_hole_<num>.png`

**需要移除的功能**：
- `data_manager.py` 中的 `_scan_independent_slices()` 方法
- 独立路径模式的扫描逻辑
- 相关的配置选项和UI选择

**影响的文件**：
- `src/ui/modules/data_manager.py`
- `src/models/panoramic_annotation.py` (文件名解析逻辑)

## 2. 标注直接使用增强标注代替基础标注

**目标**：如果读取的切片有cfg时其增强属性为默认即可，减少负担

**当前实现**：
- 有基础标注 (`PanoramicAnnotation`) 和增强标注 (`EnhancedPanoramicAnnotation`) 两套系统
- GUI中有基础标注面板和增强标注面板的切换

**需要简化的功能**：
- 默认使用增强标注
- 读取CFG文件时自动设置增强属性默认值
- 简化标注创建流程

**影响的文件**：
- `src/ui/panoramic_annotation_gui.py` (标注创建和同步逻辑)
- `src/models/enhanced_annotation.py` (默认值设置)
- `src/services/config_service.py` (CFG读取逻辑)

## 3. 去掉导出训练数据和批量导入的按钮和功能

**目标**：精简后要保证各项其他功能仍可用

**需要移除的功能**：

### 导出训练数据
- 工具栏中的"导出训练数据"按钮
- `export_training_data()` 方法
- 相关的数据导出逻辑

### 批量导入
- 工具栏中的"批量导入"按钮
- `batch_import_annotations()` 方法
- `batch_import_dialog.py` 文件
- 批量导入对话框

**影响的文件**：
- `src/ui/panoramic_annotation_gui.py`
- `src/ui/batch_import_dialog.py` (删除)
- `src/ui/modules/ui_builder.py`
- `src/ui/modules/data_manager.py`
- `src/ui/modules/dialog_factory.py`
- `src/ui/controllers/` 下的相关控制器文件

## 实施步骤

### 步骤1：移除批量导入和导出训练数据功能
1. 删除工具栏按钮
2. 删除相关方法
3. 删除batch_import_dialog.py文件
4. 清理相关导入语句

### 步骤2：简化目录结构支持
1. 修改DataManager只支持子目录模式
2. 更新文件扫描逻辑
3. 更新文件名解析逻辑

### 步骤3：增强标注替代基础标注
1. 修改默认标注创建逻辑
2. 简化CFG读取时的增强属性设置
3. 更新UI展示逻辑

### 步骤4：测试验证
1. 验证其他功能仍可正常使用
2. 测试标注创建和保存
3. 测试图像导航和显示
4. 测试配置文件读取

## 风险评估

- **低风险**：移除批量导入和导出功能不影响核心标注功能
- **中风险**：目录结构简化可能影响现有数据兼容性
- **低风险**：增强标注替代不会破坏现有标注数据
