"""
增强标注面板
支持复合特征标注，如"阴性带气孔"等复杂标注场景
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Set, List

# 简化的枚举类定义
class GrowthLevel:
    NEGATIVE = "negative"
    WEAK_GROWTH = "weak_growth"
    POSITIVE = "positive"

class InterferenceType:
    PORES = "气孔"
    ARTIFACTS = "气孔重叠"
    DEBRIS = "杂质"
    CONTAMINATION = "污染"

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
            interference_str = "+".join(sorted(self.interference_factors))
            label_parts.append(f"with_{interference_str}")  # Use English instead of Chinese
        
        return "_".join(label_parts)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'growth_level': self.growth_level,
            'growth_pattern': self.growth_pattern,
            'interference_factors': list(self.interference_factors),
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
        
        # 当前标注状态
        self.current_microbe_type = tk.StringVar(value="bacteria")
        self.current_growth_level = tk.StringVar(value="negative")
        self.current_growth_pattern = tk.StringVar(value="")
        self.current_confidence = tk.DoubleVar(value=0.95)
        
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
            print(f"[UI] 创建默认模式按钮: {text} -> {value}")
        
        # 添加分隔线
        #separator = ttk.Separator(pattern_frame, orient='vertical')
        #separator.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        # 创建手动选择按钮
        for text, value in manual_patterns:
            btn = ttk.Radiobutton(pattern_frame, text=text, variable=self.current_growth_pattern, 
                                 value=value, command=self.on_pattern_change)
            btn.pack(side=tk.LEFT, padx=2)
            self.pattern_buttons[value] = btn
        
        print(f"[UI] 所有模式按钮已创建: {list(self.pattern_buttons.keys())}")
    
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
        
    def update_pattern_options(self):
        """更新生长模式选项"""
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
        print(f"[UI] 生长级别: {growth_level}, 可用模式: {available_patterns}")
        
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
        
        print(f"[UI] 显示模式按钮数量: {visible_count}/{len(self.pattern_buttons)}")
        
        # 重置当前选择到第一个可用选项
        if available_patterns:
            current_pattern = self.current_growth_pattern.get()
            if current_pattern not in available_patterns:
                self.current_growth_pattern.set(available_patterns[0])
        else:
            self.current_growth_pattern.set("")
    
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
            current_state = (growth_level, growth_pattern, tuple(sorted(interference_factors)), confidence)
            if not hasattr(self, '_last_combination_state') or self._last_combination_state != current_state:
                print(f"[ANNOTATION] 特征组合: {growth_level}{'_' + growth_pattern if growth_pattern else ''}{'+' + '+'.join(sorted(interference_factors)) if interference_factors else ''} [{confidence:.2f}]")
                self._last_combination_state = current_state
            
            return combination
        except Exception as e:
            print(f"[ERROR] 获取特征组合时出错: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"[ERROR] 设置特征组合失败: {e}")
            import traceback
            traceback.print_exc()
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
            print(f"[INIT] 重置干扰因素")
            for var in self.interference_vars.values():
                var.set(False)
        else:
            print(f"[INIT] 保持现有干扰因素设置")
        
        # 设置默认置信度
        self.current_confidence.set(1.0)
        
        # 更新界面选项
        self.update_pattern_options()
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
            print(f"[INIT] 使用用户指定的生长模式: {growth_pattern}")
            self.current_growth_pattern.set(growth_pattern)
        else:
            # 如果没有指定模式，使用可区分的默认模式
            default_pattern = FeatureCombination.get_distinguishable_default_pattern(growth_level)
            self.current_growth_pattern.set(default_pattern)
        
        # 根据参数决定是否重置干扰因素
        if reset_interference:
            print(f"[INIT] 重置干扰因素")
            for var in self.interference_vars.values():
                var.set(False)
        else:
            print(f"[INIT] 保持现有干扰因素设置")
        
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
            print(f"设置标注数据失败: {e}")
        
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
            print(f"重置标注面板失败: {e}")
    
    def get_frame(self) -> ttk.Frame:
        """获取主框架"""
        return self.main_frame
