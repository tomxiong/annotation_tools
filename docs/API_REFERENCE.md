# PanoramicAnnotationGUI API 参考文档

## 类概览

### PanoramicAnnotationGUI
**主控制器类** - 负责整个应用的界面管理和数据流控制

```python
class PanoramicAnnotationGUI:
    """全景图像标注工具主界面"""
    
    def __init__(self, root: tk.Tk)
    # 初始化主界面，设置所有服务和组件
```

## 核心API方法

### 1. 界面构建方法
```python
def create_widgets(self) -> None
    """创建主界面组件"""

def create_toolbar(self, parent) -> None
    """创建顶部工具栏"""

def create_panoramic_panel(self, parent) -> None
    """创建左侧全景图显示面板"""

def create_slice_panel(self, parent) -> None
    """创建右侧切片显示和控制面板"""

def create_navigation_panel(self, parent) -> None
    """创建导航控制面板"""

def create_annotation_panel(self, parent) -> None
    """创建标注控制面板"""

def create_status_bar(self, parent) -> None
    """创建底部状态栏"""
```

### 2. 数据管理方法
```python
def load_data(self) -> None
    """加载全景图数据 - 扫描目录并构建文件列表"""

def select_panoramic_directory(self) -> None
    """选择全景图目录并自动加载数据"""

def load_current_slice(self) -> None
    """加载当前孔位的切片图像"""

def load_panoramic_image(self) -> None
    """加载并显示当前全景图"""

def load_existing_annotation(self) -> None
    """加载已有的标注数据"""

def load_config_annotations(self) -> None
    """从CFG配置文件加载标注数据"""
```

### 3. 导航控制方法
```python
def go_first_hole(self) -> None
    """跳转到第一个孔位"""

def go_last_hole(self) -> None
    """跳转到最后一个孔位"""

def go_prev_hole(self) -> None
    """跳转到上一个孔位"""

def go_next_hole(self) -> None
    """跳转到下一个孔位"""

def navigate_to_hole(self, hole_number: int) -> None
    """导航到指定孔位号"""

def go_prev_panoramic(self) -> None
    """切换到上一张全景图"""

def go_next_panoramic(self) -> None
    """切换到下一张全景图"""

def go_to_panoramic(self, panoramic_id: str) -> None
    """切换到指定全景图"""
```

### 4. 标注操作方法
```python
def save_current_annotation(self) -> None
    """保存当前标注并跳转到下一个孔位"""

def skip_current(self) -> None
    """跳过当前孔位，不保存标注"""

def clear_current_annotation(self) -> None
    """清除当前孔位的标注"""

def save_annotations(self) -> None
    """保存所有标注到JSON文件"""

def load_annotations(self) -> None
    """从JSON文件加载标注"""

def batch_import_annotations(self) -> None
    """显示批量导入对话框"""

def export_training_data(self) -> None
    """导出训练数据"""

def import_model_suggestions(self) -> None
    """导入模型预测建议"""
```

### 5. 视图模式方法
```python
def get_current_view_mode(self) -> ViewMode
    """获取当前视图模式"""

def set_view_mode(self, mode: ViewMode) -> None
    """设置视图模式"""

def add_view_change_callback(self, callback: Callable[[ViewMode], None]) -> None
    """添加视图模式变更回调"""

def remove_view_change_callback(self, callback: Callable[[ViewMode], None]) -> None
    """移除视图模式变更回调"""

def on_view_mode_changed(self, view_mode: ViewMode) -> None
    """视图模式变更事件处理"""
```

### 6. 事件处理方法
```python
def setup_bindings(self) -> None
    """设置键盘快捷键和窗口事件"""

def on_panoramic_click(self, event) -> None
    """全景图鼠标点击事件处理"""

def on_enhanced_annotation_change(self, annotation_data=None) -> None
    """增强标注变化回调"""

def on_window_resize(self, event) -> None
    """窗口尺寸变化事件处理"""

# 键盘事件处理方法
def on_key_left(self, event) -> None
def on_key_right(self, event) -> None
def on_key_up(self, event) -> None
def on_key_down(self, event) -> None
def on_key_space(self, event) -> None
def on_key_return(self, event) -> None
```

### 7. 状态管理方法
```python
def update_status(self, message: str) -> None
    """更新状态栏消息"""

def update_statistics(self) -> None
    """更新统计信息显示"""

def update_progress(self) -> None
    """更新导航进度显示"""

def update_slice_info_display(self) -> None
    """更新切片信息显示"""

def sync_debug_logging_state(self) -> None
    """同步调试日志状态到UI"""
```

### 8. 智能设置继承
```python
def get_current_annotation_settings(self) -> dict
    """获取当前标注的设置"""

def apply_annotation_settings(self, settings: dict) -> None
    """应用标注设置到下一个孔位"""

def should_copy_settings(self, current_settings: dict, next_hole_info: dict) -> bool
    """判断是否应该复制设置"""

def get_config_growth_level(self, hole_number: int) -> str
    """获取配置文件中指定孔位的生长级别"""
```

## 重要属性

### 核心数据属性
```python
# 服务和管理器
self.image_service: PanoramicImageService
self.hole_manager: HoleManager
self.config_service: ConfigFileService
self.model_suggestion_service: ModelSuggestionImportService

# 当前状态
self.current_dataset: PanoramicDataset
self.current_panoramic_id: str
self.current_hole_number: int
self.current_slice_index: int
self.current_view_mode: ViewMode

# 文件列表
self.slice_files: List[Dict[str, Any]]
self.panoramic_ids: List[str]

# UI组件引用
self.enhanced_annotation_panel: EnhancedAnnotationPanel
self.hole_config_panel: HoleConfigPanel
self.save_button: ttk.Button
self.skip_button: ttk.Button
self.clear_button: ttk.Button
```

### 配置属性
```python
# 性能配置
self.delay_config: dict = {
    'settings_apply': 30,
    'button_recovery': 150, 
    'quick_recovery': 100,
    'ui_refresh': 50,
    'verification': 100
}

# 功能开关
self.auto_save_enabled: tk.BooleanVar
self.debug_logging_enabled: tk.BooleanVar
self.performance_monitoring_enabled: tk.BooleanVar

# 标注状态
self.current_microbe_type: tk.StringVar
self.current_growth_level: tk.StringVar
self.interference_factors: Dict[str, tk.BooleanVar]
```

## 辅助类API

### ProgressDialog
```python
class ProgressDialog:
    """模态进度对话框"""
    
    def __init__(self, parent, title="正在加载", message="请稍候...")
    def update_progress(self, value: int, message: str = None) -> None
    def close(self) -> None
```

### ViewMode 枚举
```python
class ViewMode(Enum):
    MANUAL = "人工"    # 人工标注模式
    MODEL = "模型"     # 模型预测模式
```

## 回调函数签名

### 视图模式变更回调
```python
def view_change_callback(view_mode: ViewMode) -> None:
    """视图模式变更时被调用"""
    pass
```

### 标注变更回调
```python
def annotation_change_callback(annotation_data: dict = None) -> None:
    """标注内容变更时被调用"""
    pass
```

### 孔位配置回调
```python
def hole_config_callback(config: dict) -> None:
    """孔位配置应用时被调用"""
    pass
```

## 常用代码模式

### 1. 添加视图模式变更监听
```python
def my_view_change_handler(view_mode: ViewMode):
    if view_mode == ViewMode.MODEL:
        # 处理模型模式
        pass
    elif view_mode == ViewMode.MANUAL:
        # 处理人工模式
        pass

# 注册回调
gui.add_view_change_callback(my_view_change_handler)
```

### 2. 程序化导航
```python
# 跳转到特定孔位
gui.navigate_to_hole(25)

# 切换全景图
gui.go_to_panoramic("EB10000026")

# 批量导航
for hole in range(1, 11):
    gui.navigate_to_hole(hole)
    # 处理当前孔位
```

### 3. 获取当前标注状态
```python
# 获取当前标注设置
settings = gui.get_current_annotation_settings()

# 检查特定孔位是否已标注
is_annotated = gui.is_hole_annotated(hole_number=15)

# 获取统计信息
stats = gui.current_dataset.get_statistics()
```

### 4. 自定义标注面板集成
```python
class CustomAnnotationPanel:
    def __init__(self, parent, on_change_callback):
        self.parent = parent
        self.on_change = on_change_callback
        # 构建自定义界面
        
    def on_view_mode_changed(self, view_mode):
        # 响应视图模式变更
        pass

# 集成到主界面
custom_panel = CustomAnnotationPanel(gui.enhanced_annotation_frame, 
                                   gui.on_enhanced_annotation_change)
gui.add_view_change_callback(custom_panel.on_view_mode_changed)
```

## 最佳实践

### 1. 性能优化
```python
# 批量操作时禁用自动保存
gui.auto_save_enabled.set(False)
# 执行批量操作
# ...
# 恢复自动保存
gui.auto_save_enabled.set(True)
```

### 2. 错误处理
```python
try:
    gui.load_data()
except Exception as e:
    gui.log_error(f"数据加载失败: {e}")
    gui.update_status("数据加载失败")
```

### 3. 扩展开发
- 使用回调机制而不是直接修改核心代码
- 遵循现有的命名约定和代码风格
- 添加适当的日志记录和错误处理
- 考虑性能影响，使用延迟更新机制

---

*API文档生成时间: 2025年9月12日*
*基于版本: panoramic_annotation_gui.py (6398行)*
