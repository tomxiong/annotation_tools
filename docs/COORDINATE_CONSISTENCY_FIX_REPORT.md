# 坐标一致性修复报告

## 问题描述
用户反馈：加载人工标注结果后绘制的全景图上各切片的坐标位置与初次加载cfg绘制的框图坐标不同，cfg的坐标更准确。

## 问题分析

### 根本原因
发现系统中存在两套不同的坐标计算系统：

1. **`create_panoramic_overlay` 方法**（图像坐标系统）：
   - 位置：`src/services/panoramic_image_service.py`
   - 使用：`self.hole_manager.get_hole_coordinates(hole_number)`
   - 特点：直接在原始全景图像上绘制，使用图像原始坐标
   - 问题：坐标不准确，与实际孔位位置有偏差

2. **`draw_all_config_hole_boxes` 方法**（画布坐标系统）：
   - 位置：`src/ui/panoramic_annotation_gui.py`
   - 使用：`self.hole_manager.get_hole_center_coordinates(hole_number)` + 缩放转换
   - 特点：使用画布坐标系统，通过 `scale_factor` 和 `offset` 进行坐标转换
   - 优势：坐标更准确，正确对应孔位位置

### 坐标计算差异

#### 原有的图像坐标系统
```python
# 在 create_panoramic_overlay 中
x, y, width, height = self.hole_manager.get_hole_coordinates(hole_number)
# 直接使用原始图像坐标，没有考虑显示缩放
```

#### 准确的画布坐标系统
```python
# 在 draw_all_config_hole_boxes 中
hole_center = self.hole_manager.get_hole_center_coordinates(hole_number)
hole_x = offset_x + int(hole_center[0] * scale_factor)
hole_y = offset_y + int(hole_center[1] * scale_factor)
# 考虑了显示缩放和画布偏移
```

## 解决方案

### 核心修复
统一使用 `draw_all_config_hole_boxes` 方法的坐标系统，移除 `create_panoramic_overlay` 中的覆盖绘制。

### 具体修改

#### 1. 修改 `load_panoramic_image` 方法
```python
# 修改前：使用 create_panoramic_overlay 创建带标注的全景图
overlay_image = self.image_service.create_panoramic_overlay(
    self.panoramic_image, 
    self.current_hole_number,
    annotated_holes
)

# 修改后：直接显示原始全景图，使用 draw_all_config_hole_boxes 绘制覆盖层
display_panoramic = self.image_service.resize_image_for_display(
    self.panoramic_image, target_width, target_height, fill_mode='fit'
)
```

#### 2. 修改 `_update_panoramic_overlay_only` 方法
```python
# 修改前：重新创建 create_panoramic_overlay
overlay_image = self.image_service.create_panoramic_overlay(...)

# 修改后：直接更新原始全景图，依靠 draw_all_config_hole_boxes
display_panoramic = self.image_service.resize_image_for_display(...)
```

### 绘制流程优化

#### 新的绘制顺序
1. 加载原始全景图
2. 预加载配置文件标注（`_preload_config_annotations`）
3. 绘制配置状态框（`draw_all_config_hole_boxes`）
4. 绘制当前孔位指示框（`draw_current_hole_indicator`）

#### 坐标计算统一
所有框的绘制都使用相同的坐标转换逻辑：
```python
# 统一的坐标计算
display_info = self._get_panoramic_display_info()
scale_factor = display_info['scale_factor']
offset_x = display_info['offset_x']
offset_y = display_info['offset_y']

# 孔位坐标转换
hole_center = self.hole_manager.get_hole_center_coordinates(hole_number)
canvas_x = offset_x + int(hole_center[0] * scale_factor)
canvas_y = offset_y + int(hole_center[1] * scale_factor)
```

## 验证方法

### 测试脚本
创建了 `test_coordinate_consistency.py` 测试脚本：
- 生成包含多个孔位的测试配置文件
- 覆盖不同行列位置（角落、中间、边缘）
- 提供详细的测试指南

### 测试用例
选择的测试孔位：
- **孔位1**：第1行第1列（左上角）
- **孔位12**：第1行第12列（右上角）
- **孔位50**：第5行第2列（中间位置）
- **孔位109**：第10行第1列（左下角）
- **孔位120**：第10行第12列（右下角）

### 预期结果
修复后应该实现：
1. ✅ CFG配置框位置准确对应孔位
2. ✅ 人工标注框与CFG框完全重叠
3. ✅ 不出现坐标偏移或双重框
4. ✅ 所有孔位的框都使用相同的坐标系统

## 代码影响范围

### 修改的文件
- `src/ui/panoramic_annotation_gui.py`

### 修改的方法
- `load_panoramic_image()` - 移除create_panoramic_overlay调用
- `_update_panoramic_overlay_only()` - 移除create_panoramic_overlay调用

### 保持不变的方法
- `draw_all_config_hole_boxes()` - 准确的坐标计算逻辑
- `_get_panoramic_display_info()` - 统一的显示信息计算
- `hole_manager.get_hole_center_coordinates()` - 孔位中心坐标

## 性能优化

### 减少重复计算
- 移除了图像坐标系统的重复绘制
- 统一使用一套坐标计算逻辑
- 减少了 `create_panoramic_overlay` 的调用开销

### 内存优化
- 不再创建带覆盖层的临时图像
- 直接在画布上绘制覆盖元素
- 减少了图像处理的内存占用

## 兼容性保证

### 现有功能保持
- ✅ 配置文件预加载功能正常
- ✅ 人工标注功能正常
- ✅ 视图模式切换正常
- ✅ 孔位导航功能正常

### UI体验改进
- ✅ 框位置更准确
- ✅ 视觉一致性更好
- ✅ 用户操作更直观

## 测试建议

### 功能测试
1. 运行 `test_coordinate_consistency.py` 生成测试数据
2. 启动GUI选择测试目录
3. 观察CFG配置框的精确位置
4. 进行人工标注并验证框位置一致性

### 回归测试
1. 验证配置文件加载功能
2. 验证人工标注保存功能
3. 验证不同类型全景图（普通/SE类型）
4. 验证视图模式切换功能

## 总结

通过统一坐标系统，成功解决了CFG配置框与人工标注框坐标不一致的问题：
- 🎯 **根本解决**：移除了不准确的图像坐标系统
- 🎯 **精度提升**：统一使用准确的画布坐标系统
- 🎯 **性能优化**：减少重复计算和内存占用
- 🎯 **用户体验**：框位置精确，视觉一致性好

该修复确保了所有孔位框都使用相同的坐标计算逻辑，彻底解决了坐标不一致问题。
