"""
增强标注面板
支持复合特征标注，如"阴性带气孔"等复杂标注场景
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Set, List

# 模型导入
from src.models.enhanced_annotation import InterferenceType

# 日志导入
try:
    from src.utils.logger import log_debug, log_info, log_warning, log_error
except ImportError:
    # 如果日志模块不可用，使用print作为后备
    def log_debug(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_info(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_warning(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)
    def log_error(msg, category=""):
        print(f"[{category}] {msg}" if category else msg)

# 简化的枚举类定义
class GrowthLevel:
    NEGATIVE = "negative"
    WEAK_GROWTH = "weak_growth"
    POSITIVE = "positive"


class GrowthPattern:
    # 阴性模式
    CLEAN = "clean"              # 无干扰的阴性
    
    # 弱生长模式
    SMALL_DOTS = "small_dots"    # 较小的点状弱生长
    LIGHT_GRAY = "light_gray"    # 整体较淡的灰色弱生长
    IRREGULAR_AREAS = "irregular_areas"  # 不规则淡区域弱生长
    
    # 阳性模式
    CLUSTERED = "clustered"      # 聚集型生长
    SCATTERED = "scattered"      # 分散型生长
    HEAVY_GROWTH = "heavy_growth"  # 重度生长
    FOCAL = "focal"              # 聚焦性生长（真菌）
    DIFFUSE = "diffuse"          # 弥漫性生长（真菌）
    
    # 系统默认模式（可区分的默认值）
    DEFAULT_POSITIVE = "default_positive"    # 阳性系统默认（区分于手动选择）
    DEFAULT_WEAK = "default_weak_growth"     # 弱生长系统默认（区分于手动选择）
    DEFAULT_NEGATIVE = "clean"               # 阴性系统默认（与clean相同，因为阴性本身就是清亮）

class FeatureCombination:
    def __init__(self, growth_level=GrowthLevel.NEGATIVE, growth_pattern=GrowthPattern.CLEAN, 
                 interference_factors=None, confidence=1.0):
        self.growth_level = growth_level
        self.growth_pattern = growth_pattern
        self.interference_factors = interference_factors or set()
        self.confidence = confidence
    
    @property
    def to_label(self):
        """生成标注标签"""
        label_parts = [self.growth_level]
        
        if self.growth_pattern and self.growth_pattern != GrowthPattern.CLEAN:
            label_parts.append(self.growth_pattern)
        
        if self.interference_factors:
            # 转换枚举对象为字符串
            interference_strs = []
            for factor in self.interference_factors:
                if hasattr(factor, 'value'):
                    interference_strs.append(factor.value)
                else:
                    interference_strs.append(str(factor))
            interference_str = "+".join(sorted(interference_strs))
            label_parts.append(f"with_{interference_str}")  # Use English instead of Chinese
        
        return "_".join(label_parts)
    
    def to_dict(self):
        """转换为字典"""
        # 转换枚举对象为字符串
        interference_factors = []
        for factor in self.interference_factors:
            if hasattr(factor, 'value'):
                interference_factors.append(factor.value)
            else:
                interference_factors.append(str(factor))
        
        return {
            'growth_level': self.growth_level,
            'growth_pattern': self.growth_pattern,
            'interference_factors': interference_factors,
            'confidence': self.confidence
        }
    
    @staticmethod
    def get_distinguishable_default_pattern(growth_level: str) -> str:
        """
        获取可区分的默认生长模式
        这些默认值与手动选择的模式不同，可以让用户区分系统生成和手动选择
        
        Args:
            growth_level: 生长级别 ('positive', 'weak_growth', 'negative')
            
        Returns:
            可区分的默认模式字符串
        """
        if growth_level == "positive":
            # 阳性默认为专用默认模式，区分于手动的clustered/scattered/heavy_growth
            return GrowthPattern.DEFAULT_POSITIVE
        elif growth_level == "weak_growth":
            # 弱生长默认为专用默认模式，区分于手动的small_dots/light_gray/irregular_areas
            return GrowthPattern.DEFAULT_WEAK
        else:  # negative
            # 阴性默认为清亮（阴性本身就应该是清亮的）
            return GrowthPattern.DEFAULT_NEGATIVE
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建"""
        return cls(
            growth_level=data.get('growth_level', GrowthLevel.NEGATIVE),
            growth_pattern=data.get('growth_pattern', GrowthPattern.CLEAN),
            interference_factors=set(data.get('interference_factors', [])),
            confidence=data.get('confidence', 1.0)
        )

class EnhancedAnnotationPanel:
    """
    增强标注面板类
    提供复合特征标注界面
    """
    
    def __init__(self, parent: tk.Widget, on_annotation_change: Optional[Callable] = None):
        self.parent = parent
        self.on_annotation_change = on_annotation_change
        
        # 视图模式相关状态
        self.current_view_mode = None
        self.current_hole_manager = None
        self.current_slice_index = None
        
        # 当前标注状态
        self.current_microbe_type = tk.StringVar(value="bacteria")
        self.current_growth_level = tk.StringVar(value="negative")
        self.current_growth_pattern = tk.StringVar(value="")
        self.current_confidence = tk.DoubleVar(value=0.95)
        self.confidence_var = tk.IntVar(value=95)  # 置信度变量，用于模型建议
        
        # 干扰因素状态
        self.interference_vars = {
            InterferenceType.PORES: tk.BooleanVar(),
            InterferenceType.ARTIFACTS: tk.BooleanVar(),
            InterferenceType.DEBRIS: tk.BooleanVar(),
            InterferenceType.CONTAMINATION: tk.BooleanVar()
        }
        
        # 界面组件
        self.pattern_buttons = {}
        self.interference_checkboxes = {}
        
        # 创建界面
        self.create_widgets()
        self.setup_bindings()
        self.update_pattern_options()
    
    def create_widgets(self):
        """创建界面组件"""
        # 主框架
        self.main_frame = ttk.LabelFrame(self.parent, text="增强标注控制")
        self.main_frame.pack(fill=tk.X, pady=(0, 0))
        
        # 微生物类型
        self.create_microbe_type_section()
        
        # 生长级别
        self.create_growth_level_section()
        
        # 生长模式
        self.create_growth_pattern_section()
        
        # 干扰因素
        self.create_interference_section()
        
        # 置信度
        self.create_confidence_section()
        
        # 预览和操作
        self.create_preview_section()
    
    def create_microbe_type_section(self):
        """创建微生物类型选择"""
        type_frame = ttk.LabelFrame(self.main_frame, text="微生物类型")
        type_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Radiobutton(type_frame, text="细菌", variable=self.current_microbe_type, 
                       value="bacteria").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="真菌", variable=self.current_microbe_type, 
                       value="fungi").pack(side=tk.LEFT, padx=5)
    
    def create_growth_level_section(self):
        """创建生长级别选择"""
        level_frame = ttk.LabelFrame(self.main_frame, text="生长级别")
        level_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Radiobutton(level_frame, text="阴性", variable=self.current_growth_level, 
                       value="negative", command=self.on_growth_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="弱生长", variable=self.current_growth_level, 
                       value="weak_growth", command=self.on_growth_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="阳性", variable=self.current_growth_level, 
                       value="positive", command=self.on_growth_level_change).pack(side=tk.LEFT, padx=5)
    
    def create_growth_pattern_section(self):
        """创建生长模式选择"""
        pattern_frame = ttk.LabelFrame(self.main_frame, text="生长模式")
        pattern_frame.pack(fill=tk.X, padx=5, pady=2)
        
        # 系统默认模式（放在前面，优先显示）
        default_patterns = [
            ("阳性", "default_positive"),
            ("弱生长", "default_weak_growth")
        ]
        
        # 手动选择模式（放在后面）
        manual_patterns = [
            ("清亮", "clean"),
            ("中心小点", "small_dots"),
            ("浅灰色", "light_gray"),
            ("不规则区域", "irregular_areas"),
            ("聚集型", "clustered"),
            ("分散型", "scattered"),
            ("重度生长", "heavy_growth"),
            ("聚焦性", "focal"),
            ("弥漫性", "diffuse")
        ]
        
        # 创建系统默认按钮（优先显示，使用特殊标识）
        for text, value in default_patterns:
            btn = ttk.Radiobutton(pattern_frame, text=f"[默认] {text}", variable=self.current_growth_pattern, 
                                 value=value, command=self.on_pattern_change)
            btn.pack(side=tk.LEFT, padx=2)
            self.pattern_buttons[value] = btn
            log_debug(f"创建默认模式按钮: {text} -> {value}", "UI")
        
        # 添加分隔线
        #separator = ttk.Separator(pattern_frame, orient='vertical')
        #separator.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 创建手动选择按钮
        for text, value in manual_patterns:
            btn = ttk.Radiobutton(pattern_frame, text=text, variable=self.current_growth_pattern, 
                                 value=value, command=self.on_pattern_change)
            btn.pack(side=tk.LEFT, padx=2)
            self.pattern_buttons[value] = btn
        
        log_debug(f"所有模式按钮已创建: {list(self.pattern_buttons.keys())}", "UI")
    
    def create_interference_section(self):
        """创建干扰因素选择"""
        interference_frame = ttk.LabelFrame(self.main_frame, text="干扰因素")
        interference_frame.pack(fill=tk.X, padx=5, pady=2)
        
        interferences = [
            ("气孔", InterferenceType.PORES),
            ("气孔重叠", InterferenceType.ARTIFACTS),
            ("杂质", InterferenceType.DEBRIS),
            ("污染", InterferenceType.CONTAMINATION)
        ]
        
        for text, factor in interferences:
            cb = ttk.Checkbutton(interference_frame, text=text, 
                               variable=self.interference_vars[factor],
                               command=self.on_interference_change)
            cb.pack(side=tk.LEFT, padx=3)
            self.interference_checkboxes[factor] = cb
    
    def create_confidence_section(self):
        """创建置信度控制"""
        conf_frame = ttk.LabelFrame(self.main_frame, text="置信度")
        conf_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.confidence_scale = ttk.Scale(conf_frame, from_=0.0, to=1.0, 
                                        variable=self.current_confidence,
                                        orient=tk.HORIZONTAL,
                                        command=self.on_confidence_change)
        self.confidence_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.confidence_label = ttk.Label(conf_frame, text="0.95")
        self.confidence_label.pack(side=tk.RIGHT, padx=5)
    
    def create_preview_section(self):
        """移除预览区域，因为已合并到切片面板"""
        # 预览功能已移到主界面的切片面板中
        pass
    
    def setup_bindings(self):
        """设置事件绑定"""
        # 绑定变量变化事件
        self.current_microbe_type.trace('w', lambda *args: self.on_microbe_type_change())
        self.current_growth_level.trace('w', lambda *args: self.on_growth_level_change())
        self.current_growth_pattern.trace('w', lambda *args: self.on_pattern_change())
        
    def update_pattern_options(self, preserve_current=False):
        """更新生长模式选项
        
        Args:
            preserve_current: 是否保持当前选择不变（用于加载模型建议时）
        """
        growth_level = self.current_growth_level.get()
        microbe_type = self.current_microbe_type.get()
        
        # 定义每个生长级别对应的模式选项（默认值排在第一位）
        pattern_options = {
            "negative": ["clean"],
            "weak_growth": ["default_weak_growth", "small_dots", "light_gray", "irregular_areas"],
            "positive": (["default_positive", "clustered", "scattered", "heavy_growth"] if microbe_type == "bacteria" 
                       else ["default_positive", "focal", "diffuse", "heavy_growth"])
        }
        
        # 获取当前级别的可用选项
        available_patterns = pattern_options.get(growth_level, [])
        log_debug(f"生长级别: {growth_level}, 可用模式: {available_patterns}, 保持当前选择: {preserve_current}", "UI")
        
        # 更新按钮显示状态
        visible_count = 0
        for pattern_value, btn in self.pattern_buttons.items():
            if pattern_value in available_patterns:
                btn.config(state="normal")
                btn.pack(side=tk.LEFT, padx=5)
                visible_count += 1
            else:
                btn.config(state="disabled")
                btn.pack_forget()  # 隐藏不可用的选项
        
        log_debug(f"显示模式按钮数量: {visible_count}/{len(self.pattern_buttons)}", "UI")
        
        # 只有在不保持当前选择时才重置
        if not preserve_current:
            # 重置当前选择到第一个可用选项
            if available_patterns:
                current_pattern = self.current_growth_pattern.get()
                if current_pattern not in available_patterns:
                    log_debug(f"当前模式 {current_pattern} 不在可用列表中，重置为 {available_patterns[0]}", "UI")
                    self.current_growth_pattern.set(available_patterns[0])
            else:
                self.current_growth_pattern.set("")
        else:
            log_debug(f"保持当前模式选择: {self.current_growth_pattern.get()}", "UI")
    
    def update_interference_options(self):
        """更新干扰因素选项"""
        # 所有干扰因素都可用
        pass
    
    def update_preview(self):
        """更新预览显示"""
        # 预览功能已移到主界面的切片面板中
        # 只需要触发回调，让主界面更新显示
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_microbe_type_change(self):
        """微生物类型改变"""
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_growth_level_change(self):
        """生长级别改变"""
        self.update_pattern_options()
        self.update_interference_options()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_pattern_change(self):
        """生长模式改变"""
        self.update_interference_options()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_interference_change(self):
        """干扰因素改变"""
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_confidence_change(self, value):
        """置信度改变"""
        confidence = float(value)
        self.confidence_label.config(text=f"{confidence:.2f}")
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
         
    def get_current_feature_combination(self):
        """获取当前特征组合"""
        try:
            # Only log when there's a significant change or error
            interference_factors = set()
            for factor, var in self.interference_vars.items():
                if var.get():
                    interference_factors.add(factor)
            
            growth_level = self.current_growth_level.get()
            growth_pattern = self.current_growth_pattern.get()
            confidence = self.current_confidence.get()
            
            # Create combination silently for normal operations
            combination = FeatureCombination(
                growth_level=growth_level,
                growth_pattern=growth_pattern,
                interference_factors=interference_factors,
                confidence=confidence
            )
            
            # Only log if this is a new or changed combination
            # 转换枚举对象为字符串用于状态比较和日志记录
            interference_factor_strs = []
            for factor in interference_factors:
                if hasattr(factor, 'value'):
                    interference_factor_strs.append(factor.value)
                else:
                    interference_factor_strs.append(str(factor))
            
            current_state = (growth_level, growth_pattern, tuple(sorted(interference_factor_strs)), confidence)
            if not hasattr(self, '_last_combination_state') or self._last_combination_state != current_state:
                log_debug(f"特征组合: {growth_level}{'_' + growth_pattern if growth_pattern else ''}{'+' + '+'.join(sorted(interference_factor_strs)) if interference_factor_strs else ''} [{confidence:.2f}]", "ANNOTATION")
                self._last_combination_state = current_state
            
            return combination
        except Exception as e:
            log_error(f"获取特征组合时出错: {e}", "ERROR")
            import traceback
            log_error(f"异常详情: {traceback.format_exc()}", "ERROR")
            raise
    
    def set_feature_combination(self, combination):
        """设置特征组合"""
        try:
            # 处理生长级别 - 可能是枚举或字符串
            growth_level = combination.growth_level
            if hasattr(growth_level, 'value'):
                growth_level = growth_level.value
            self.current_growth_level.set(growth_level)
            
            # 处理生长模式 - 可能是枚举或字符串
            growth_pattern = combination.growth_pattern
            if growth_pattern is not None:
                if hasattr(growth_pattern, 'value'):
                    growth_pattern = growth_pattern.value
                self.current_growth_pattern.set(growth_pattern)
            else:
                self.current_growth_pattern.set("")
            
            # 设置置信度
            self.current_confidence.set(combination.confidence)
            
                        
            # 重置干扰因素
            for var in self.interference_vars.values():
                var.set(False)
            
            # 设置干扰因素 - 增强处理逻辑
            interference_count = 0
            for factor in combination.interference_factors:
                                
                # 情况1: 直接匹配面板中的干扰因素变量
                if factor in self.interference_vars:
                    self.interference_vars[factor].set(True)
                    interference_count += 1
                                    
                # 情况2: 处理枚举类型的干扰因素
                elif hasattr(factor, 'value'):
                    factor_value = factor.value
                                        
                    # 尝试匹配面板中的变量
                    for panel_var_key, panel_var in self.interference_vars.items():
                        panel_var_value = panel_var_key.value if hasattr(panel_var_key, 'value') else panel_var_key
                        if panel_var_value == factor_value:
                            panel_var.set(True)
                            interference_count += 1
                            break
                
                # 情况3: 处理字符串类型的干扰因素
                elif isinstance(factor, str):
                    # 尝试映射到面板变量
                    for panel_var_key, panel_var in self.interference_vars.items():
                        panel_var_value = panel_var_key.value if hasattr(panel_var_key, 'value') else panel_var_key
                        if panel_var_value == factor:
                            panel_var.set(True)
                            interference_count += 1
                            break
            
                        
            self.update_pattern_options()
            self.update_interference_options()
            
                        
        except Exception as e:
            log_error(f"设置特征组合失败: {e}", "ERROR")
            import traceback
            log_error(f"异常详情: {traceback.format_exc()}", "ERROR")
            # 回退到默认状态
            self.reset_annotation()
    
    # 暂时移除快速阳性和快速阴性功能
# def quick_negative(self):
#     """快速设置为阴性"""
#     combination = FeatureCombination(
#         growth_level=GrowthLevel.NEGATIVE,
#         growth_pattern=GrowthPattern.CLEAN,
#         confidence=1.0
#     )
#     self.set_feature_combination(combination)
# 
# def quick_positive(self):
#     """快速设置为阳性"""
#     combination = FeatureCombination(
#         growth_level=GrowthLevel.POSITIVE,
#         growth_pattern=GrowthPattern.HEAVY_GROWTH,
#         confidence=1.0
#     )
#     self.set_feature_combination(combination)
    
    def reset_annotation(self):
        """重置标注"""
        self.current_growth_level.set("negative")
        self.current_growth_pattern.set("")
        self.current_confidence.set(1.0)
        
        for var in self.interference_vars.values():
            var.set(False)
        
        self.update_pattern_options()
        self.update_interference_options()
    
    def initialize_with_defaults(self, growth_level: str = "negative", microbe_type: str = "bacteria", reset_interference: bool = True):
        """
        使用可区分的默认值初始化面板
        用于系统初始化或加载没有enhanced_data的标注时
        
        Args:
            growth_level: 生长级别
            microbe_type: 微生物类型
            reset_interference: 是否重置干扰因素，默认为True
        """
        # 设置微生物类型
        self.current_microbe_type.set(microbe_type)
        
        # 设置生长级别
        self.current_growth_level.set(growth_level)
        
        # 获取可区分的默认模式
        default_pattern = FeatureCombination.get_distinguishable_default_pattern(growth_level)
        self.current_growth_pattern.set(default_pattern)
        
        # 根据参数决定是否重置干扰因素
        if reset_interference:
            log_debug(f"重置干扰因素", "INIT")
            for var in self.interference_vars.values():
                var.set(False)
        else:
            log_debug(f"保持现有干扰因素设置", "INIT")
        
        # 设置默认置信度
        self.current_confidence.set(1.0)
        
        # 更新界面选项（保持当前选择不变）
        self.update_pattern_options(preserve_current=True)
        self.update_interference_options()
    
    def initialize_with_pattern(self, growth_level: str = "negative", microbe_type: str = "bacteria", growth_pattern: str = "", reset_interference: bool = True):
        """
        使用指定的生长模式初始化面板
        用于恢复用户之前选择的模式
        
        Args:
            growth_level: 生长级别
            microbe_type: 微生物类型
            growth_pattern: 用户选择的生长模式
            reset_interference: 是否重置干扰因素，默认为True
        """
        # 设置微生物类型
        self.current_microbe_type.set(microbe_type)
        
        # 设置生长级别
        self.current_growth_level.set(growth_level)
        
        # 设置用户指定的生长模式
        if growth_pattern:
            log_debug(f"使用用户指定的生长模式: {growth_pattern}", "INIT")
            self.current_growth_pattern.set(growth_pattern)
        else:
            # 如果没有指定模式，使用可区分的默认模式
            default_pattern = FeatureCombination.get_distinguishable_default_pattern(growth_level)
            self.current_growth_pattern.set(default_pattern)
        
        # 根据参数决定是否重置干扰因素
        if reset_interference:
            log_debug(f"重置干扰因素", "INIT")
            for var in self.interference_vars.values():
                var.set(False)
        else:
            log_debug(f"保持现有干扰因素设置", "INIT")
        
        # 设置默认置信度
        self.current_confidence.set(1.0)
        
        # 更新界面选项
        self.update_pattern_options()
        self.update_interference_options()
    
    def clear_annotation(self):
        """清空标注 - 与reset_annotation相同，为了兼容性"""
        self.reset_annotation()
    
    def get_annotation_data(self):
        """获取标注数据 - 为了兼容性"""
        combination = self.get_current_feature_combination()
        return {
            'has_bacteria': combination.growth_level != 'negative',
            'bacteria_count': 0,
            'bacteria_type': combination.growth_level,
            'has_impurities': len(combination.interference_factors) > 0,
            'impurities_type': ','.join(combination.interference_factors),
            'image_quality': '良好',
            'notes': ''
        }
    
    def set_annotation_data(self, data):
        """设置标注数据 - 为了兼容性"""
        try:
            # 映射生长级别
            if data.get('has_bacteria', False):
                bacteria_type = data.get('bacteria_type', 'positive')
                if bacteria_type in ['negative', 'weak_growth', 'positive']:
                    self.current_growth_level.set(bacteria_type)
                else:
                    self.current_growth_level.set('positive')
            else:
                self.current_growth_level.set('negative')
            
            # 映射干扰因素
            if data.get('has_impurities', False):
                impurities = data.get('impurities_type', '').split(',')
                for factor_name, var in self.interference_vars.items():
                    var.set(factor_name in impurities)
            
            self.update_pattern_options()
            self.update_interference_options()
            self.update_preview()
            
        except Exception as e:
            log_error(f"设置标注数据失败: {e}", "ERROR")
        
    def reset_to_default(self):
        """重置到默认状态"""
        try:
            # 重置微生物类型
            self.current_microbe_type.set("bacteria")
            
            # 重置生长级别
            self.current_growth_level.set("negative")
            
            # 重置生长模式
            self.current_growth_pattern.set("")
            
            # 重置干扰因素
            for var in self.interference_vars.values():
                var.set(False)
            
            # 重置置信度
            self.current_confidence.set(0.95)
            
            # 更新界面
            self.update_pattern_options()
            self.update_interference_options()
            self.update_preview()
            
        except Exception as e:
            log_error(f"重置标注面板失败: {e}", "ERROR")
    
    def get_frame(self) -> ttk.Frame:
        """获取主框架"""
        return self.main_frame
    
    def on_view_mode_changed(self, view_mode, hole_manager=None, slice_index=None):
        """响应视图模式切换"""
        try:
            self.current_view_mode = view_mode
            self.current_hole_manager = hole_manager
            self.current_slice_index = slice_index
            
            log_debug(f"视图模式切换: {view_mode}, 切片索引: {slice_index}", "VIEW_MODE")
            
            # 根据视图模式更新界面状态
            if view_mode == "slice" and hole_manager and slice_index is not None:
                # 切片视图模式 - 启用所有标注功能
                self.main_frame.config(state="normal")
                
                # 尝试加载当前切片的标注数据
                try:
                    slice_annotation = hole_manager.get_slice_annotation(slice_index)
                    if slice_annotation and hasattr(slice_annotation, 'enhanced_data'):
                        enhanced_data = slice_annotation.enhanced_data
                        if enhanced_data:
                            log_debug(f"加载切片 {slice_index} 的增强标注数据", "ANNOTATION")
                            self.set_feature_combination(enhanced_data)
                        else:
                            # 使用默认值初始化
                            self.initialize_with_defaults("negative", "bacteria", True)
                    else:
                        # 使用默认值初始化
                        self.initialize_with_defaults("negative", "bacteria", True)
                except Exception as e:
                     log_warning(f"加载切片标注数据失败: {e}", "ANNOTATION")
                     self.initialize_with_defaults("negative", "bacteria", True)
                     
            elif ((isinstance(view_mode, str) and view_mode in ["model", "模型"]) or 
                  (hasattr(view_mode, 'value') and view_mode.value in ["模型", "model"]) or
                  (hasattr(view_mode, 'name') and view_mode.name == 'MODEL')) and hole_manager and slice_index is not None:
                # 模型视图模式 - 显示模型建议数据
                 
                 try:
                     # 获取模型建议数据
                     log_debug(f"=== 开始切换到模型视图 - 切片 {slice_index} ===", "VIEW_MODE")
                     suggestion = hole_manager.get_hole_suggestion(slice_index)
                     log_debug(f"获取到的建议数据: {suggestion}", "VIEW_MODE")
                     
                     if suggestion:
                         log_debug(f"加载切片 {slice_index} 的模型建议数据", "MODEL")
                         log_debug(f"调用load_model_suggestion前的界面状态:", "VIEW_MODE")
                         log_debug(f"  - 生长级别: {self.current_growth_level.get()}", "VIEW_MODE")
                         log_debug(f"  - 生长模式: {self.current_growth_pattern.get()}", "VIEW_MODE")
                         
                         self.load_model_suggestion(suggestion)
                         
                         log_debug(f"调用load_model_suggestion后的界面状态:", "VIEW_MODE")
                         log_debug(f"  - 生长级别: {self.current_growth_level.get()}", "VIEW_MODE")
                         log_debug(f"  - 生长模式: {self.current_growth_pattern.get()}", "VIEW_MODE")
                     else:
                         log_debug(f"切片 {slice_index} 无模型建议数据", "MODEL")
                         self.initialize_with_defaults("negative", "bacteria", True)
                     
                     log_debug(f"=== 模型视图切换完成 - 切片 {slice_index} ===", "VIEW_MODE")
                 except Exception as e:
                     log_warning(f"加载模型建议数据失败: {e}", "MODEL")
                     import traceback
                     log_error(f"异常详情: {traceback.format_exc()}", "MODEL")
                     self.initialize_with_defaults("negative", "bacteria", True)
                     
            elif ((isinstance(view_mode, str) and view_mode in ["manual", "人工"]) or 
                  (hasattr(view_mode, 'value') and view_mode.value in ["人工", "manual"]) or
                  (hasattr(view_mode, 'name') and view_mode.name == 'MANUAL')) and hole_manager and slice_index is not None:
                # 人工视图模式 - 恢复人工标注数据
                 
                 try:
                     log_debug(f"=== 开始切换到人工视图 - 切片 {slice_index} ===", "VIEW_MODE")
                     self.load_manual_annotation(hole_manager, slice_index)
                     log_debug(f"=== 人工视图切换完成 - 切片 {slice_index} ===", "VIEW_MODE")
                 except Exception as e:
                     log_warning(f"加载人工标注数据失败: {e}", "MANUAL")
                     import traceback
                     log_error(f"异常详情: {traceback.format_exc()}", "MANUAL")
                     self.initialize_with_defaults("negative", "bacteria", True)
                     
            elif view_mode == "overview":
                 # 概览视图模式 - 禁用标注功能或显示汇总信息
                 self.main_frame.config(state="disabled")
                 log_debug("概览模式 - 标注面板已禁用", "VIEW_MODE")
                 
            else:
                 # 其他模式 - 重置到默认状态
                 self.reset_to_default()
                 log_debug("未知视图模式 - 重置标注面板", "VIEW_MODE")
                
        except Exception as e:
             log_error(f"视图模式切换处理失败: {e}", "ERROR")
             import traceback
             log_error(f"异常详情: {traceback.format_exc()}", "ERROR")
     

     
    def reset_to_default(self):
          """重置到默认状态"""
          self.initialize_with_defaults("negative", "bacteria", True)
     
    def load_manual_annotation(self, hole_manager, slice_index):
        """加载人工标注数据到增强标注面板"""
        try:
            log_debug(f"[DEBUG] load_manual_annotation called for slice {slice_index}", "MANUAL")
            log_debug(f"=== 开始加载人工标注数据 ===", "MANUAL")

            # 记录加载前的状态
            log_debug(f"加载前状态 - 生长级别: {self.current_growth_level.get()}", "MANUAL")
            log_debug(f"加载前状态 - 生长模式: {self.current_growth_pattern.get()}", "MANUAL")
            log_debug(f"加载前状态 - 微生物类型: {self.current_microbe_type.get()}", "MANUAL")

            # 获取当前切片的标注数据
            # 注意：HoleManager没有get_slice_annotation方法，这里应该从数据集中获取
            slice_annotation = None
            if hasattr(self, 'current_dataset') and self.current_dataset:
                # 从slice_index获取panoramic_id和hole_number
                if hasattr(self, 'slice_files') and self.slice_files and 0 <= slice_index < len(self.slice_files):
                    current_slice = self.slice_files[slice_index]
                    panoramic_id = current_slice.get('panoramic_id')
                    hole_number = current_slice.get('hole_number')

                    # 从数据集中查找对应的标注数据
                    for annotation in self.current_dataset.annotations:
                        if (annotation.panoramic_id == panoramic_id and
                            annotation.hole_number == hole_number):
                            slice_annotation = annotation
                            break
                else:
                    log_debug("无法获取切片文件信息", "MANUAL")
            log_debug(f"获取到的切片标注: {slice_annotation}", "MANUAL")
            
            if slice_annotation and hasattr(slice_annotation, 'enhanced_data') and slice_annotation.enhanced_data:
                # 有增强标注数据，直接加载
                enhanced_data = slice_annotation.enhanced_data
                log_debug(f"加载切片 {slice_index} 的增强标注数据: {enhanced_data}", "MANUAL")
                self.set_feature_combination(enhanced_data)
            elif slice_annotation:
                # 有基础标注数据，转换为增强标注格式
                log_debug(f"转换基础标注数据为增强格式", "MANUAL")
                
                # 从基础标注数据推断生长级别
                growth_level = "negative"  # 默认值
                if hasattr(slice_annotation, 'has_bacteria') and slice_annotation.has_bacteria:
                    if hasattr(slice_annotation, 'bacteria_type'):
                        bacteria_type = slice_annotation.bacteria_type
                        if bacteria_type in ['negative', 'weak_growth', 'positive']:
                            growth_level = bacteria_type
                        else:
                            growth_level = 'positive'  # 默认为阳性
                    else:
                        growth_level = 'positive'  # 有细菌但无类型信息，默认为阳性
                
                log_debug(f"推断的生长级别: {growth_level}", "MANUAL")
                
                # 设置微生物类型（默认为细菌）
                self.current_microbe_type.set("bacteria")
                
                # 设置生长级别
                self.current_growth_level.set(growth_level)
                
                # 根据生长级别设置默认模式
                default_pattern = FeatureCombination.get_distinguishable_default_pattern(growth_level)
                self.current_growth_pattern.set(default_pattern)
                log_debug(f"设置默认生长模式: {default_pattern}", "MANUAL")
                
                # 处理干扰因素
                for var in self.interference_vars.values():
                    var.set(False)
                
                if hasattr(slice_annotation, 'has_impurities') and slice_annotation.has_impurities:
                    if hasattr(slice_annotation, 'impurities_type') and slice_annotation.impurities_type:
                        impurities = slice_annotation.impurities_type.split(',')
                        log_debug(f"处理干扰因素: {impurities}", "MANUAL")
                        
                        # 映射干扰因素名称到枚举
                        impurity_mapping = {
                            'pores': InterferenceType.PORES,
                            'artifacts': InterferenceType.ARTIFACTS,
                            'debris': InterferenceType.DEBRIS,
                            'contamination': InterferenceType.CONTAMINATION,
                            '气孔': InterferenceType.PORES,
                            '气孔重叠': InterferenceType.ARTIFACTS,
                            '杂质': InterferenceType.DEBRIS,
                            '污染': InterferenceType.CONTAMINATION
                        }
                        
                        for impurity in impurities:
                            impurity = impurity.strip()
                            if impurity in impurity_mapping:
                                enum_factor = impurity_mapping[impurity]
                                if enum_factor in self.interference_vars:
                                    self.interference_vars[enum_factor].set(True)
                                    log_debug(f"设置干扰因素: {impurity} -> {enum_factor}", "MANUAL")
                
                # 设置默认置信度
                self.current_confidence.set(1.0)
                
            else:
                # 无标注数据，使用默认值初始化
                log_debug(f"切片 {slice_index} 无标注数据，使用默认值初始化", "MANUAL")
                self.initialize_with_defaults("negative", "bacteria", True)
            
            # 更新界面选项
            self.update_pattern_options()
            self.update_interference_options()
            
            # 记录加载后的状态
            log_debug(f"加载后状态 - 生长级别: {self.current_growth_level.get()}", "MANUAL")
            log_debug(f"加载后状态 - 生长模式: {self.current_growth_pattern.get()}", "MANUAL")
            log_debug(f"加载后状态 - 微生物类型: {self.current_microbe_type.get()}", "MANUAL")
            
            # 强制更新界面显示
            if hasattr(self, 'main_frame'):
                self.main_frame.update_idletasks()
                log_debug("界面刷新完成", "MANUAL")
            
            log_debug("=== 人工标注数据加载完成 ===", "MANUAL")
            
        except Exception as e:
            log_error(f"加载人工标注数据失败: {e}", "ERROR")
            import traceback
            log_error(f"异常详情: {traceback.format_exc()}", "ERROR")
            # 出错时使用默认值
            self.initialize_with_defaults("negative", "bacteria", True)
    
    def load_model_suggestion(self, suggestion):
         """加载模型建议数据到增强标注面板"""
         try:
             log_debug(f"[DEBUG] load_model_suggestion called", "MODEL")
             log_debug(f"=== 开始加载模型建议数据 ===", "MODEL")
             log_debug(f"完整建议数据: {suggestion}", "MODEL")
             log_debug(f"建议数据类型: {type(suggestion)}", "MODEL")
             
             # 记录加载前的状态
             log_debug(f"加载前状态 - 生长级别: {self.current_growth_level.get()}", "MODEL")
             log_debug(f"加载前状态 - 生长模式: {self.current_growth_pattern.get()}", "MODEL")
             log_debug(f"加载前状态 - 微生物类型: {self.current_microbe_type.get()}", "MODEL")
             
             # 设置微生物类型
             if hasattr(suggestion, 'microbe_type'):
                 microbe_type = suggestion.microbe_type
                 log_debug(f"原始微生物类型数据: {microbe_type}, 类型: {type(microbe_type)}", "MODEL")
                 if microbe_type in ['bacteria', 'fungi', 'virus', 'other']:
                     self.current_microbe_type.set(microbe_type)
                     log_debug(f"设置微生物类型: {microbe_type}", "MODEL")
                 else:
                     log_warning(f"未知的微生物类型: {microbe_type}，保持默认值", "MODEL")
             else:
                 log_debug("建议数据中无microbe_type字段", "MODEL")
             
             # 设置生长级别
             if hasattr(suggestion, 'growth_level'):
                 growth_level = suggestion.growth_level
                 log_debug(f"原始生长级别数据: {growth_level}, 类型: {type(growth_level)}", "MODEL")
                 
                 # 处理可能的字符串或枚举类型
                 if hasattr(growth_level, 'value'):
                     growth_level = growth_level.value
                 elif hasattr(growth_level, 'name'):
                     growth_level = growth_level.name.lower()
                 
                 # 映射模型建议的生长级别到正确的值
                 growth_level_mapping = {
                     'low': 'negative',
                     'medium': 'weak_growth', 
                     'high': 'positive',
                     'negative': 'negative',
                     'weak_growth': 'weak_growth',
                     'positive': 'positive',
                     'weak': 'weak_growth',
                     'strong': 'positive'
                 }
                 
                 # 转换为小写进行匹配
                 growth_level_str = str(growth_level).lower()
                 log_debug(f"处理后的生长级别字符串: {growth_level_str}", "MODEL")
                 
                 if growth_level_str in growth_level_mapping:
                     mapped_level = growth_level_mapping[growth_level_str]
                     log_debug(f"映射后的生长级别: {mapped_level}", "MODEL")
                     log_debug(f"设置前current_growth_level: {self.current_growth_level.get()}", "MODEL")
                     
                     self.current_growth_level.set(mapped_level)
                     log_debug(f"设置后current_growth_level: {self.current_growth_level.get()}", "MODEL")
                     
                     # 立即更新界面选项以确保生长级别变化生效
                     log_debug(f"调用update_pattern_options前...", "MODEL")
                     self.update_pattern_options()
                     log_debug(f"调用update_pattern_options后的生长级别: {self.current_growth_level.get()}", "MODEL")
                     
                     # 禁用强制触发界面刷新
                     # self.main_frame.update()
                     # log_debug("强制界面刷新完成", "MODEL")
                 else:
                     log_warning(f"未知的生长级别: {growth_level_str}，保持默认值", "MODEL")
             else:
                 log_debug("建议数据中无growth_level字段", "MODEL")
             
             # 设置生长模式
             pattern_set = False
             if hasattr(suggestion, 'growth_pattern'):
                 growth_pattern = suggestion.growth_pattern
                 log_debug(f"原始生长模式数据: {growth_pattern}, 类型: {type(growth_pattern)}", "MODEL")
                 log_debug(f"设置前current_growth_pattern: {self.current_growth_pattern.get()}", "MODEL")
                 
                 if isinstance(growth_pattern, list) and growth_pattern:
                     # 如果是列表，取第一个值
                     pattern = growth_pattern[0]
                     log_debug(f"从列表中取第一个值: {pattern}", "MODEL")
                 else:
                     pattern = growth_pattern
                 
                 log_debug(f"处理生长模式: {pattern}", "MODEL")
                 
                 # 映射模型建议的生长模式到正确的值
                 pattern_mapping = {
                     'scattered': 'scattered',
                     'clustered': 'clustered', 
                     'linear': 'irregular_areas',
                     'circular': 'focal'
                 }
                 
                 log_debug(f"可用的模式映射: {list(pattern_mapping.keys())}", "MODEL")
                 
                 if pattern in pattern_mapping:
                     mapped_pattern = pattern_mapping[pattern]
                     self.current_growth_pattern.set(mapped_pattern)
                     log_debug(f"设置生长模式: {pattern} -> {mapped_pattern}", "MODEL")
                     log_debug(f"设置后current_growth_pattern: {self.current_growth_pattern.get()}", "MODEL")
                     pattern_set = True
                 elif pattern in ['clean', 'small_dots', 'light_gray', 'irregular_areas', 'heavy_growth', 'focal', 'diffuse', 'default_positive', 'default_weak_growth']:
                     # 如果已经是正确的值，直接设置
                     self.current_growth_pattern.set(pattern)
                     log_debug(f"直接设置生长模式: {pattern}", "MODEL")
                     log_debug(f"设置后current_growth_pattern: {self.current_growth_pattern.get()}", "MODEL")
                     pattern_set = True
                 else:
                     log_warning(f"未知的生长模式: {pattern}，将使用默认值", "MODEL")
             else:
                 log_debug("建议数据中无growth_pattern字段，将使用默认值", "MODEL")
             
             # 如果没有设置生长模式或设置失败，根据当前生长级别设置默认模式
             if not pattern_set:
                 current_level = self.current_growth_level.get()
                 default_pattern = FeatureCombination.get_distinguishable_default_pattern(current_level)
                 self.current_growth_pattern.set(default_pattern)
                 log_debug(f"设置默认生长模式: {default_pattern} (基于生长级别: {current_level})", "MODEL")
                 log_debug(f"设置默认值后current_growth_pattern: {self.current_growth_pattern.get()}", "MODEL")
             
             # 设置干扰因素
             if hasattr(suggestion, 'interference_factors'):
                 interference_factors = suggestion.interference_factors
                 log_debug(f"原始干扰因素数据: {interference_factors}", "MODEL")
                 log_debug(f"可用的干扰因素枚举: {list(self.interference_vars.keys())}", "MODEL")
                 
                 # 先清空所有干扰因素
                 for var in self.interference_vars.values():
                     var.set(False)
                 log_debug("已清空所有干扰因素", "MODEL")
                 
                 # 设置模型建议的干扰因素
                 if isinstance(interference_factors, list):
                     log_debug(f"处理干扰因素列表，长度: {len(interference_factors)}", "MODEL")
                     for factor in interference_factors:
                         log_debug(f"处理干扰因素: {factor}, 类型: {type(factor)}", "MODEL")
                         self._set_single_interference_factor(factor)
                 elif isinstance(interference_factors, str) and interference_factors:
                     log_debug(f"处理单个干扰因素字符串: {interference_factors}", "MODEL")
                     self._set_single_interference_factor(interference_factors)
                 else:
                     log_debug(f"干扰因素数据类型不支持: {type(interference_factors)}", "MODEL")
             else:
                 log_debug("建议数据中无interference_factors字段", "MODEL")
             
             # 设置置信度
             if hasattr(suggestion, 'confidence'):
                 confidence = suggestion.confidence
                 log_debug(f"原始置信度数据: {confidence}, 类型: {type(confidence)}", "MODEL")
                 if isinstance(confidence, (int, float)) and 0 <= confidence <= 100:
                     self.confidence_var.set(int(confidence))
                     log_debug(f"设置置信度: {confidence}", "MODEL")
                 else:
                     log_warning(f"无效的置信度值: {confidence}，保持默认值", "MODEL")
             else:
                 log_debug("建议数据中无confidence字段", "MODEL")
             
             # 记录加载后的状态
             log_debug(f"加载后状态 - 生长级别: {self.current_growth_level.get()}", "MODEL")
             log_debug(f"加载后状态 - 生长模式: {self.current_growth_pattern.get()}", "MODEL")
             log_debug(f"加载后状态 - 微生物类型: {self.current_microbe_type.get()}", "MODEL")
             
             # 禁用强制更新界面显示
             log_debug("更新界面显示...", "MODEL")
             log_debug(f"更新前界面状态 - 生长级别按钮: {self.current_growth_level.get()}", "MODEL")
             log_debug(f"更新前界面状态 - 生长模式按钮: {self.current_growth_pattern.get()}", "MODEL")
             
             # 检查干扰因素状态
             interference_status = {}
             for factor, var in self.interference_vars.items():
                 interference_status[factor.value if hasattr(factor, 'value') else str(factor)] = var.get()
             log_debug(f"更新前干扰因素状态: {interference_status}", "MODEL")
             
             self.update_pattern_options()
             self.update_interference_options()
             
             # 检查更新后的状态
             log_debug(f"更新后界面状态 - 生长级别按钮: {self.current_growth_level.get()}", "MODEL")
             log_debug(f"更新后界面状态 - 生长模式按钮: {self.current_growth_pattern.get()}", "MODEL")
             
             # 再次检查干扰因素状态
             interference_status_after = {}
             for factor, var in self.interference_vars.items():
                 interference_status_after[factor.value if hasattr(factor, 'value') else str(factor)] = var.get()
             log_debug(f"更新后干扰因素状态: {interference_status_after}", "MODEL")
             
             # 强制触发界面刷新，确保控件状态正确显示
             if hasattr(self, 'main_frame'):
                 self.main_frame.update_idletasks()
                 log_debug("界面刷新完成", "MODEL")

             log_debug("=== 模型建议数据加载完成 ===", "MODEL")
             
         except Exception as e:
             log_error(f"加载模型建议数据失败: {e}", "ERROR")
             import traceback
             log_error(f"异常详情: {traceback.format_exc()}", "ERROR")
             # 出错时使用默认值
             self.initialize_with_defaults("negative", "bacteria", True)
                 
    def _set_single_interference_factor(self, factor):
        """设置单个干扰因素"""
        try:
            log_debug(f"尝试设置干扰因素: {factor}, 类型: {type(factor)}", "MODEL")
            
            # 方法1: 直接匹配枚举对象
            if factor in self.interference_vars:
                self.interference_vars[factor].set(True)
                log_debug(f"直接匹配设置干扰因素: {factor}", "MODEL")
                return True
            
            # 方法2: 处理字符串类型，通过枚举值匹配
            if isinstance(factor, str):
                # 创建字符串到枚举的映射
                string_to_enum = {
                    'pores': InterferenceType.PORES,
                    'artifacts': InterferenceType.ARTIFACTS, 
                    'debris': InterferenceType.DEBRIS,
                    'contamination': InterferenceType.CONTAMINATION,
                    # 添加中文映射
                    '气孔': InterferenceType.PORES,
                    '气孔重叠': InterferenceType.ARTIFACTS,
                    '杂质': InterferenceType.DEBRIS,
                    '污染': InterferenceType.CONTAMINATION
                }
                
                log_debug(f"字符串映射表: {list(string_to_enum.keys())}", "MODEL")
                
                # 尝试直接映射
                if factor in string_to_enum:
                    enum_factor = string_to_enum[factor]
                    if enum_factor in self.interference_vars:
                        self.interference_vars[enum_factor].set(True)
                        log_debug(f"通过字符串映射设置干扰因素: {factor} -> {enum_factor}", "MODEL")
                        return True
                
                # 尝试通过枚举值匹配
                for enum_key, var in self.interference_vars.items():
                    if hasattr(enum_key, 'value') and enum_key.value == factor:
                        var.set(True)
                        log_debug(f"通过枚举值匹配设置干扰因素: {factor} -> {enum_key}", "MODEL")
                        return True
            
            # 方法3: 处理枚举类型
            elif hasattr(factor, 'value'):
                factor_value = factor.value
                for enum_key, var in self.interference_vars.items():
                    if hasattr(enum_key, 'value') and enum_key.value == factor_value:
                        var.set(True)
                        log_debug(f"通过枚举对象设置干扰因素: {factor} -> {enum_key}", "MODEL")
                        return True
            
            log_warning(f"未找到匹配的干扰因素: {factor}", "MODEL")
            return False
            
        except Exception as e:
            log_error(f"设置干扰因素失败: {factor}, 错误: {e}", "MODEL")
            return False
