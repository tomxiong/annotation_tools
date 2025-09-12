# 起始点调整坐标缓存问题修复报告

## 🔍 问题发现

用户反馈：修改起始点后，切换全景图时，界面上有多个框有的按照新的起始点，有的按照旧起始点。

## 🎯 根本原因分析

通过深入分析绘制框图的坐标获取流程，发现问题根源在于**坐标缓存机制**：

### 问题链路
```
用户设置起始坐标 → HoleManager.update_positioning_params() → 更新first_hole_x/y
                                                      ↓
画布调整 → HoleManager.adjust_coordinates_for_canvas() → 用original_first_hole_x/y重新计算
                                                      ↓
                                               覆盖用户设置！
```

### 具体问题代码
```python
# 在 adjust_coordinates_for_canvas 方法中：
def adjust_coordinates_for_canvas(self, canvas_width, canvas_height, img_width, img_height):
    # ... 计算缩放比例 ...
    
    # ❌ 问题：总是用原始坐标重新计算，覆盖了用户设置
    self.first_hole_x = int(self.original_first_hole_x * scale)
    self.first_hole_y = int(self.original_first_hole_y * scale)
```

## 🔧 修复方案

### 修复思路
当用户手动设置起始坐标时，同时更新原始坐标，确保画布调整时使用更新后的原始坐标进行缩放。

### 修复代码
```python
# 修改 HoleManager.update_positioning_params 方法
def update_positioning_params(self, first_hole_x=None, first_hole_y=None, ...):
    if first_hole_x is not None:
        self.first_hole_x = first_hole_x
        # ✅ 新增：同时更新原始坐标，防止被画布调整覆盖
        if hasattr(self, 'current_scale') and self.current_scale > 0:
            self.original_first_hole_x = int(first_hole_x / self.current_scale)
        else:
            self.original_first_hole_x = first_hole_x
    
    if first_hole_y is not None:
        self.first_hole_y = first_hole_y
        # ✅ 新增：同时更新原始坐标，防止被画布调整覆盖
        if hasattr(self, 'current_scale') and self.current_scale > 0:
            self.original_first_hole_y = int(first_hole_y / self.current_scale)
        else:
            self.original_first_hole_y = first_hole_y
```

## 📊 测试验证

### 测试场景
1. **基础功能测试**: 用户手动设置起始坐标
2. **画布调整测试**: 窗口大小变化时坐标保持比例
3. **切换全景图测试**: 不同类型全景图切换时坐标一致性
4. **逻辑分离测试**: 起始孔编号与起始坐标独立管理

### 测试结果
```
✅ 用户设置的起始坐标在画布调整时保持了正确的比例
✅ 起始孔编号和起始坐标独立管理
✅ 起始孔编号根据全景图类型自动调整
✅ 起始坐标保持用户自定义值不变
```

## 🎉 修复效果

### 修复前
- ❌ 用户设置起始坐标后，切换全景图或调整窗口大小会恢复到默认坐标
- ❌ 界面显示不一致，部分框按新坐标，部分按旧坐标

### 修复后
- ✅ 用户设置的起始坐标在任何情况下都能保持正确比例
- ✅ 切换全景图时坐标显示完全一致
- ✅ 窗口大小变化时坐标按比例正确缩放

## 🔍 相关概念澄清

### 逻辑分离确认
经过分析确认，以下两个概念是完全独立的：

1. **起始孔编号** (`start_hole`)
   - 根据全景图类型自动设置
   - SE类型：从第5个孔开始
   - 普通类型：从第1个孔开始
   - **不受用户坐标调整影响**

2. **起始坐标** (`first_hole_x/y`)
   - 第一个孔在图像中的物理位置
   - 用户可手动调整以校正仪器拍摄偏差
   - **不受全景图类型切换影响**

## 📝 技术要点

### 坐标系统架构
```
原始坐标系 (3088x2064) → 缩放 → 显示坐标系 (canvas size)
      ↑                           ↓
  用户设置更新              实际绘制使用
```

### 缓存更新策略
- **设置时**: 用户坐标 → 原始坐标 (反向缩放)
- **显示时**: 原始坐标 → 显示坐标 (正向缩放)
- **一致性**: 确保设置和显示使用相同的坐标基准

## 🏆 结论

通过深入分析绘制框图的坐标获取流程，准确定位了坐标缓存覆盖问题，并实现了用户设置坐标的持久化保存。修复后的系统能够：

1. **保持用户设置**: 手动调整的起始坐标在任何情况下都不会丢失
2. **正确缩放**: 在不同画布尺寸下按正确比例显示
3. **逻辑清晰**: 起始孔编号和起始坐标各司其职，互不干扰

这次修复不仅解决了用户反馈的问题，还提升了系统的整体稳定性和用户体验。
