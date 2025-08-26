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
    PORES = "pores"
    ARTIFACTS = "artifacts"
    EDGE_BLUR = "edge_blur"
    CONTAMINATION = "contamination"
    SCRATCHES = "scratches"

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
            label_parts.append(f"带{interference_str}")
        
        return "_".join(label_parts)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'growth_level': self.growth_level,
            'growth_pattern': self.growth_pattern,
            'interference_factors': list(self.interference_factors),
            'confidence': self.confidence
        }
    
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
            InterferenceType.EDGE_BLUR: tk.BooleanVar(),
            InterferenceType.CONTAMINATION: tk.BooleanVar(),
            InterferenceType.SCRATCHES: tk.BooleanVar()
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
        self.main_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 0))
        
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
        
        patterns = [
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
        
        for text, value in patterns:
            btn = ttk.Radiobutton(pattern_frame, text=text, variable=self.current_growth_pattern, 
                                 value=value, command=self.on_pattern_change)
            btn.pack(side=tk.LEFT, padx=5)
            self.pattern_buttons[value] = btn
    
    def create_interference_section(self):
        """创建干扰因素选择"""
        interference_frame = ttk.LabelFrame(self.main_frame, text="干扰因素")
        interference_frame.pack(fill=tk.X, padx=5, pady=2)
        
        interferences = [
            ("气孔", InterferenceType.PORES),
            ("伪影", InterferenceType.ARTIFACTS),
            ("边缘模糊", InterferenceType.EDGE_BLUR),
            ("污染", InterferenceType.CONTAMINATION),
            ("划痕", InterferenceType.SCRATCHES)
        ]
        
        for text, factor in interferences:
            cb = ttk.Checkbutton(interference_frame, text=text, 
                               variable=self.interference_vars[factor],
                               command=self.on_interference_change)
            cb.pack(side=tk.LEFT, padx=5)
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
        """创建预览和操作区域"""
        preview_frame = ttk.LabelFrame(self.main_frame, text="当前标注")
        preview_frame.pack(fill=tk.X, padx=5, pady=2)
        
        self.preview_label = ttk.Label(preview_frame, text="阴性", font=("Arial", 10, "bold"))
        self.preview_label.pack(pady=5)
        
        # 快捷操作按钮
        btn_frame = ttk.Frame(preview_frame)
        btn_frame.pack(fill=tk.X, pady=2)
        
        ttk.Button(btn_frame, text="快速阴性", command=self.quick_negative).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="快速阳性", command=self.quick_positive).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="重置", command=self.reset_annotation).pack(side=tk.RIGHT, padx=2)
    
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
        
        # 定义每个生长级别对应的模式选项
        pattern_options = {
            "negative": ["clean"],
            "weak_growth": ["small_dots", "light_gray", "irregular_areas"],
            "positive": ["clustered", "scattered", "heavy_growth"] if microbe_type == "bacteria" 
                       else ["focal", "diffuse", "heavy_growth"]
        }
        
        # 获取当前级别的可用选项
        available_patterns = pattern_options.get(growth_level, [])
        
        # 更新按钮显示状态
        for pattern_value, btn in self.pattern_buttons.items():
            if pattern_value in available_patterns:
                btn.config(state="normal")
                btn.pack(side=tk.LEFT, padx=5)
            else:
                btn.config(state="disabled")
                btn.pack_forget()  # 隐藏不可用的选项
        
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
        growth_level = self.current_growth_level.get()
        growth_pattern = self.current_growth_pattern.get()
        confidence = self.current_confidence.get()
        
        # 获取选中的干扰因素
        interferences = []
        for factor, var in self.interference_vars.items():
            if var.get():
                interferences.append(factor)
        
        # 构建预览文本
        preview_text = f"{growth_level}"
        if growth_pattern and growth_level != "negative":
            preview_text += f" ({growth_pattern})"
        
        if interferences:
            interference_text = ", ".join(interferences)
            preview_text += f" + {interference_text}"
        
        preview_text += f" [{confidence:.2f}]"
        
        self.preview_label.config(text=preview_text)
    
    def on_microbe_type_change(self):
        """微生物类型改变"""
        self.update_preview()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_growth_level_change(self):
        """生长级别改变"""
        self.update_pattern_options()
        self.update_interference_options()
        self.update_preview()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_pattern_change(self):
        """生长模式改变"""
        self.update_interference_options()
        self.update_preview()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_interference_change(self):
        """干扰因素改变"""
        self.update_preview()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def on_confidence_change(self, value):
        """置信度改变"""
        confidence = float(value)
        self.confidence_label.config(text=f"{confidence:.2f}")
        self.update_preview()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
         
    def get_current_feature_combination(self):
        """获取当前特征组合"""
        try:
            print("开始获取特征组合...")
            interference_factors = set()
            for factor, var in self.interference_vars.items():
                if var.get():
                    interference_factors.add(factor)
            
            print(f"growth_level: {self.current_growth_level.get()}")
            print(f"growth_pattern: {self.current_growth_pattern.get()}")
            print(f"interference_factors: {interference_factors}")
            print(f"confidence: {self.current_confidence.get()}")
            
            combination = FeatureCombination(
                growth_level=self.current_growth_level.get(),
                growth_pattern=self.current_growth_pattern.get(),
                interference_factors=interference_factors,
                confidence=self.current_confidence.get()
            )
            
            print(f"特征组合创建成功: {combination}")
            print(f"to_label 类型: {type(combination.to_label)}")
            print(f"to_label 值: {combination.to_label}")
            
            return combination
        except Exception as e:
            print(f"获取特征组合时出错: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def set_feature_combination(self, combination):
        """设置特征组合"""
        self.current_growth_level.set(combination.growth_level)
        self.current_growth_pattern.set(combination.growth_pattern)
        self.current_confidence.set(combination.confidence)
        
        # 重置干扰因素
        for var in self.interference_vars.values():
            var.set(False)
        
        # 设置干扰因素
        for factor in combination.interference_factors:
            if factor in self.interference_vars:
                self.interference_vars[factor].set(True)
        
        self.update_pattern_options()
        self.update_interference_options()
        self.update_preview()
    
    def quick_negative(self):
        """快速设置为阴性"""
        combination = FeatureCombination(
            growth_level=GrowthLevel.NEGATIVE,
            growth_pattern=GrowthPattern.CLEAN,
            confidence=1.0
        )
        self.set_feature_combination(combination)
    
    def quick_positive(self):
        """快速设置为阳性"""
        combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.HEAVY_GROWTH,
            confidence=1.0
        )
        self.set_feature_combination(combination)
    
    def reset_annotation(self):
        """重置标注"""
        self.current_growth_level.set("negative")
        self.current_growth_pattern.set("")
        self.current_confidence.set(1.0)
        
        for var in self.interference_vars.values():
            var.set(False)
        
        self.update_pattern_options()
        self.update_interference_options()
        self.update_preview()
    
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
