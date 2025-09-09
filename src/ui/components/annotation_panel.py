"""
标注面板组件

提供标注编辑和管理功能，支持多级选项和增强标注
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, List
import logging

from src.ui.utils.base_components import BaseFrameView, ComponentMixin
from src.ui.utils.event_bus import EventBus, EventType, Event, get_event_bus
from src.ui.models.ui_state import UIStateManager, get_ui_state_manager

logger = logging.getLogger(__name__)

# 生长级别枚举
class GrowthLevel:
    NEGATIVE = "negative"
    WEAK_GROWTH = "weak_growth"
    POSITIVE = "positive"

# 生长模式枚举
class GrowthPattern:
    # 阴性模式
    CLEAN = "clean"

    # 弱生长模式
    SMALL_DOTS = "small_dots"
    LIGHT_GRAY = "light_gray"
    IRREGULAR_AREAS = "irregular_areas"

    # 阳性模式
    CLUSTERED = "clustered"
    SCATTERED = "scattered"
    HEAVY_GROWTH = "heavy_growth"
    FOCAL = "focal"
    DIFFUSE = "diffuse"

    # 系统默认模式
    DEFAULT_POSITIVE = "default_positive"
    DEFAULT_WEAK_GROWTH = "default_weak_growth"

# 干扰类型枚举
class InterferenceType:
    PORES = "pores"
    ARTIFACTS = "artifacts"
    DEBRIS = "debris"
    CONTAMINATION = "contamination"

# 特征组合类
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
            interference_strs = []
            for factor in self.interference_factors:
                if hasattr(factor, 'value'):
                    interference_strs.append(factor.value)
                else:
                    interference_strs.append(str(factor))
            interference_str = "+".join(sorted(interference_strs))
            label_parts.append(f"with_{interference_str}")

        return "_".join(label_parts)


class AnnotationPanel(BaseFrameView, ComponentMixin):
    """标注面板组件"""

    def __init__(self, parent: tk.Widget, controller=None):
        super().__init__(parent, controller)

        # 当前选中的孔位
        self.current_hole: Optional[str] = None

        # 标注数据
        self.annotations: Dict[str, Dict[str, Any]] = {}

        # 标注变化回调
        self.on_annotation_change = None

        # 控制变量 - 基础标注
        self.growth_level_var = tk.StringVar()
        self.microbe_type_var = tk.StringVar()
        self.notes_var = tk.StringVar()

        # 控制变量 - 增强标注
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

        # 生长级别选项
        self.growth_levels = [
            "无生长", "微量生长", "轻度生长", "中度生长", "重度生长"
        ]

        # 微生物类型选项
        self.microbe_types = [
            "细菌", "真菌", "酵母菌", "其他"
        ]

        # 生长模式按钮
        self.pattern_buttons = {}

        # 绑定事件总线
        self.event_bus = get_event_bus()
        self.ui_state_manager = get_ui_state_manager()

        # 订阅事件
        self.event_bus.subscribe(EventType.HOLE_SELECTED, self._on_hole_selected)
        self.event_bus.subscribe(EventType.ANNOTATION_UPDATED, self._on_annotation_updated)
    
    def build_ui(self) -> tk.Widget:
        """构建UI界面"""
        self.widget = ttk.Frame(self.parent)

        # 创建主框架
        main_frame = ttk.Frame(self.widget, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 创建当前孔位信息部分
        self._create_current_hole_info(main_frame)

        # 创建分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # 创建增强标注编辑部分
        self._create_enhanced_annotation_editor(main_frame)

        # 创建分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # 创建批量操作部分
        self._create_batch_operations(main_frame)

        # 创建分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # 创建标注列表部分
        self._create_annotation_list(main_frame)

        return self.widget
    
    def _create_current_hole_info(self, parent):
        """创建当前孔位信息"""
        # 标题
        title_label = ttk.Label(parent, text="当前孔位", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))

        # 孔位信息框架
        info_frame = ttk.LabelFrame(parent, text="孔位信息", padding="5")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        # 孔位ID
        self.hole_id_label = ttk.Label(info_frame, text="孔位: 未选择", font=('Arial', 9))
        self.hole_id_label.pack(anchor=tk.W)

        # 孔位坐标
        self.hole_coords_label = ttk.Label(info_frame, text="坐标: -", font=('Arial', 9))
        self.hole_coords_label.pack(anchor=tk.W)

        # 标注状态
        self.annotation_status_label = ttk.Label(info_frame, text="标注状态: 未标注", font=('Arial', 9))
        self.annotation_status_label.pack(anchor=tk.W)

    def _create_microbe_type_section(self, parent):
        """创建微生物类型选择"""
        type_frame = ttk.LabelFrame(parent, text="微生物类型")
        type_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Radiobutton(type_frame, text="细菌", variable=self.microbe_type_var,
                       value="bacteria").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(type_frame, text="真菌", variable=self.microbe_type_var,
                       value="fungi").pack(side=tk.LEFT, padx=5)

    def _create_growth_level_section(self, parent):
        """创建生长级别选择"""
        level_frame = ttk.LabelFrame(parent, text="生长级别")
        level_frame.pack(fill=tk.X, padx=5, pady=2)

        ttk.Radiobutton(level_frame, text="阴性", variable=self.current_growth_level,
                       value="negative", command=self._on_growth_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="弱生长", variable=self.current_growth_level,
                       value="weak_growth", command=self._on_growth_level_change).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(level_frame, text="阳性", variable=self.current_growth_level,
                       value="positive", command=self._on_growth_level_change).pack(side=tk.LEFT, padx=5)

    def _create_growth_pattern_section(self, parent):
        """创建生长模式选择"""
        pattern_frame = ttk.LabelFrame(parent, text="生长模式")
        pattern_frame.pack(fill=tk.X, padx=5, pady=2)

        # 系统默认模式
        default_patterns = [
            ("阳性", "default_positive"),
            ("弱生长", "default_weak_growth")
        ]

        # 手动选择模式
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

        # 创建系统默认按钮
        for text, value in default_patterns:
            btn = ttk.Radiobutton(pattern_frame, text=f"[默认] {text}", variable=self.current_growth_pattern,
                                 value=value, command=self._on_pattern_change)
            btn.pack(side=tk.LEFT, padx=2)
            self.pattern_buttons[value] = btn

        # 创建手动选择按钮
        for text, value in manual_patterns:
            btn = ttk.Radiobutton(pattern_frame, text=text, variable=self.current_growth_pattern,
                                 value=value, command=self._on_pattern_change)
            btn.pack(side=tk.LEFT, padx=2)
            self.pattern_buttons[value] = btn

    def _create_interference_section(self, parent):
        """创建干扰因素选择"""
        interference_frame = ttk.LabelFrame(parent, text="干扰因素")
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
                               command=self._on_interference_change)
            cb.pack(side=tk.LEFT, padx=3)

    def _create_confidence_section(self, parent):
        """创建置信度控制"""
        conf_frame = ttk.LabelFrame(parent, text="置信度")
        conf_frame.pack(fill=tk.X, padx=5, pady=2)

        self.confidence_scale = ttk.Scale(conf_frame, from_=0.0, to=1.0,
                                        variable=self.current_confidence,
                                        orient=tk.HORIZONTAL,
                                        command=self._on_confidence_change)
        self.confidence_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.confidence_label = ttk.Label(conf_frame, text="0.95")
        self.confidence_label.pack(side=tk.RIGHT, padx=5)

    def _create_notes_section(self, parent):
        """创建备注部分"""
        notes_frame = ttk.LabelFrame(parent, text="备注")
        notes_frame.pack(fill=tk.X, padx=5, pady=2)

        self.notes_text = tk.Text(
            notes_frame,
            height=2,
            width=30,
            wrap=tk.WORD
        )
        self.notes_text.pack(fill=tk.X, pady=(2, 0))
        self.notes_text.bind('<KeyRelease>', self._on_annotation_changed)
    
    def _create_enhanced_annotation_editor(self, parent):
        """创建增强标注编辑器"""
        # 标题
        title_label = ttk.Label(parent, text="增强标注编辑", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))

        # 编辑器框架
        editor_frame = ttk.LabelFrame(parent, text="标注内容", padding="5")
        editor_frame.pack(fill=tk.X, pady=(0, 10))

        # 微生物类型
        self._create_microbe_type_section(editor_frame)

        # 生长级别
        self._create_growth_level_section(editor_frame)

        # 生长模式
        self._create_growth_pattern_section(editor_frame)

        # 干扰因素
        self._create_interference_section(editor_frame)

        # 置信度
        self._create_confidence_section(editor_frame)

        # 备注
        self._create_notes_section(editor_frame)

        # 按钮框架
        button_frame = ttk.Frame(editor_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(
            button_frame,
            text="保存标注",
            command=self._save_enhanced_annotation
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="清除标注",
            command=self._clear_enhanced_annotation
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="复制标注",
            command=self._copy_enhanced_annotation
        ).pack(side=tk.LEFT)
    
    def _create_batch_operations(self, parent):
        """创建批量操作"""
        # 标题
        title_label = ttk.Label(parent, text="批量操作", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 批量操作框架
        batch_frame = ttk.LabelFrame(parent, text="批量标注", padding="5")
        batch_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 批量标注选项
        options_frame = ttk.Frame(batch_frame)
        options_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.batch_growth_var = tk.StringVar()
        self.batch_microbe_var = tk.StringVar()
        
        ttk.Label(options_frame, text="批量生长级别:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.batch_growth_combo = ttk.Combobox(
            options_frame,
            textvariable=self.batch_growth_var,
            values=self.growth_levels,
            state='readonly',
            width=12
        )
        self.batch_growth_combo.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(options_frame, text="批量微生物类型:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        
        self.batch_microbe_combo = ttk.Combobox(
            options_frame,
            textvariable=self.batch_microbe_var,
            values=self.microbe_types,
            state='readonly',
            width=12
        )
        self.batch_microbe_combo.grid(row=0, column=3)
        
        # 批量操作按钮
        batch_button_frame = ttk.Frame(batch_frame)
        batch_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            batch_button_frame,
            text="应用到所有孔位",
            command=self._apply_to_all
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            batch_button_frame,
            text="应用到当前行",
            command=self._apply_to_row
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            batch_button_frame,
            text="应用到当前列",
            command=self._apply_to_column
        ).pack(side=tk.LEFT)
    
    def _create_annotation_list(self, parent):
        """创建标注列表"""
        # 标题
        title_label = ttk.Label(parent, text="标注列表", font=('Arial', 10, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 列表框架
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 标注列表
        self.annotation_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            height=6
        )
        self.annotation_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.annotation_listbox.yview)
        
        # 绑定选择事件
        self.annotation_listbox.bind('<<ListboxSelect>>', self._on_annotation_selected)
        
        # 列表按钮
        list_button_frame = ttk.Frame(parent)
        list_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(
            list_button_frame,
            text="删除标注",
            command=self._delete_annotation
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            list_button_frame,
            text="导出标注",
            command=self._export_annotations
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            list_button_frame,
            text="导入标注",
            command=self._import_annotations
        ).pack(side=tk.LEFT)
    
    def setup_layout(self) -> None:
        """设置布局"""
        pass
    
    def bind_events(self) -> None:
        """绑定事件"""
        # 绑定变量变化事件
        self.microbe_type_var.trace('w', self._on_microbe_type_change)
        self.current_growth_level.trace('w', self._on_growth_level_change)
        self.current_growth_pattern.trace('w', self._on_pattern_change)

        # 初始化生长模式选项
        self.update_pattern_options()

    def _on_microbe_type_change(self):
        """微生物类型改变"""
        self.update_pattern_options()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())
    
    def _on_hole_selected(self, event: Event):
        """孔位选择事件"""
        data = event.data
        if data and 'hole_id' in data:
            self.current_hole = data['hole_id']
            self._update_hole_info()
            self._load_annotation()
    
    def _on_annotation_updated(self, event: Event):
        """标注更新事件"""
        data = event.data
        if data and 'hole_id' in data:
            hole_id = data['hole_id']
            if hole_id == self.current_hole:
                self._load_annotation()
            self._update_annotation_list()
    
    def _on_growth_level_change(self, *args):
        """生长级别改变"""
        self.update_pattern_options()
        self.update_interference_options()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())

    def _on_pattern_change(self, *args):
        """生长模式改变"""
        self.update_interference_options()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())

    def _on_interference_change(self):
        """干扰因素改变"""
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())

    def _on_confidence_change(self, value):
        """置信度改变"""
        confidence = float(value)
        self.confidence_label.config(text=f"{confidence:.2f}")
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())

    def _on_annotation_changed(self, event=None):
        """标注内容改变事件"""
        if self.current_hole:
            # 实时更新标注状态
            self._update_annotation_status()

    def _on_microbe_type_change(self, *args):
        """微生物类型改变"""
        self.update_pattern_options()
        if self.on_annotation_change:
            self.on_annotation_change(self.get_current_feature_combination())

    def update_pattern_options(self, preserve_current=False):
        """更新生长模式选项

        Args:
            preserve_current: 是否保持当前选择不变
        """
        growth_level = self.current_growth_level.get()
        microbe_type = self.microbe_type_var.get()

        # 定义每个生长级别对应的模式选项
        pattern_options = {
            "negative": ["clean"],
            "weak_growth": ["default_weak_growth", "small_dots", "light_gray", "irregular_areas"],
            "positive": (["default_positive", "clustered", "scattered", "heavy_growth"] if microbe_type == "bacteria"
                        else ["default_positive", "focal", "diffuse", "heavy_growth"])
        }

        # 获取当前级别的可用选项
        available_patterns = pattern_options.get(growth_level, [])

        # 更新按钮显示状态
        visible_count = 0
        for pattern_value, btn in self.pattern_buttons.items():
            if pattern_value in available_patterns:
                btn.config(state="normal")
                btn.pack(side=tk.LEFT, padx=5)
                visible_count += 1
            else:
                btn.config(state="disabled")
                btn.pack_forget()

        # 只有在不保持当前选择时才重置
        if not preserve_current:
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

    def get_current_feature_combination(self):
        """获取当前特征组合"""
        try:
            # 获取干扰因素
            interference_factors = set()
            for factor, var in self.interference_vars.items():
                if var.get():
                    interference_factors.add(factor)

            growth_level = self.current_growth_level.get()
            growth_pattern = self.current_growth_pattern.get()
            confidence = self.current_confidence.get()

            # 创建特征组合
            combination = FeatureCombination(
                growth_level=growth_level,
                growth_pattern=growth_pattern,
                interference_factors=interference_factors,
                confidence=confidence
            )

            return combination
        except Exception as e:
            logger.error(f"获取特征组合时出错: {e}")
            raise
    
    def _update_hole_info(self):
        """更新孔位信息"""
        if self.current_hole:
            # 解析孔位ID
            row = int(self.current_hole[:2])
            col = int(self.current_hole[2:4])
            
            # 转换为Excel风格坐标
            row_letter = chr(ord('A') + row)
            col_number = col + 1
            
            # 更新标签
            self.hole_id_label.config(text=f"孔位: {row_letter}{col_number}")
            self.hole_coords_label.config(text=f"坐标: ({row}, {col})")
            
            # 更新标注状态
            self._update_annotation_status()
        else:
            self.hole_id_label.config(text="孔位: 未选择")
            self.hole_coords_label.config(text="坐标: -")
            self.annotation_status_label.config(text="标注状态: 未标注")
    
    def _update_annotation_status(self):
        """更新标注状态"""
        if self.current_hole and self.current_hole in self.annotations:
            annotation = self.annotations[self.current_hole]
            status_parts = []
            
            if annotation.get('growth_level'):
                status_parts.append(f"生长: {annotation['growth_level']}")
            
            if annotation.get('microbe_type'):
                status_parts.append(f"类型: {annotation['microbe_type']}")
            
            if annotation.get('notes'):
                status_parts.append("有备注")
            
            if status_parts:
                self.annotation_status_label.config(text=f"标注状态: {', '.join(status_parts)}")
            else:
                self.annotation_status_label.config(text="标注状态: 已选择")
        else:
            self.annotation_status_label.config(text="标注状态: 未标注")
    
    def _load_annotation(self):
        """加载增强标注数据"""
        if self.current_hole and self.current_hole in self.annotations:
            annotation = self.annotations[self.current_hole]

            # 加载增强标注数据
            if 'feature_combination' in annotation:
                # 从特征组合加载
                fc_data = annotation['feature_combination']
                combination = FeatureCombination.from_dict(fc_data)

                # 设置生长级别
                self.current_growth_level.set(combination.growth_level)

                # 设置生长模式
                if combination.growth_pattern:
                    self.current_growth_pattern.set(combination.growth_pattern)
                else:
                    self.current_growth_pattern.set("")

                # 设置置信度
                self.current_confidence.set(combination.confidence)

                # 设置微生物类型
                self.microbe_type_var.set(annotation.get('microbe_type', 'bacteria'))

                # 设置干扰因素
                for var in self.interference_vars.values():
                    var.set(False)

                for factor in combination.interference_factors:
                    factor_key = None
                    if hasattr(factor, 'value'):
                        factor_key = factor
                    elif isinstance(factor, str):
                        # 映射字符串到枚举
                        factor_mapping = {
                            'pores': InterferenceType.PORES,
                            'artifacts': InterferenceType.ARTIFACTS,
                            'debris': InterferenceType.DEBRIS,
                            'contamination': InterferenceType.CONTAMINATION
                        }
                        if factor in factor_mapping:
                            factor_key = factor_mapping[factor]

                    if factor_key and factor_key in self.interference_vars:
                        self.interference_vars[factor_key].set(True)

                # 更新生长模式选项
                self.update_pattern_options(preserve_current=True)

            else:
                # 兼容旧格式
                self.current_growth_level.set(annotation.get('growth_level', 'negative'))
                self.microbe_type_var.set(annotation.get('microbe_type', 'bacteria'))
                self.current_growth_pattern.set("")
                self.current_confidence.set(1.0)

                # 重置干扰因素
                for var in self.interference_vars.values():
                    var.set(False)

                # 更新生长模式选项
                self.update_pattern_options()

            # 加载备注
            self.notes_text.delete(1.0, tk.END)
            self.notes_text.insert(1.0, annotation.get('notes', ''))
        else:
            # 清空控件 - 重置到默认状态
            self.current_growth_level.set("negative")
            self.current_growth_pattern.set("")
            self.current_confidence.set(1.0)
            self.microbe_type_var.set("bacteria")

            # 重置干扰因素
            for var in self.interference_vars.values():
                var.set(False)

            # 清空备注
            self.notes_text.delete(1.0, tk.END)

            # 更新生长模式选项
            self.update_pattern_options()
    
    def _save_enhanced_annotation(self):
        """保存增强标注"""
        if not self.current_hole:
            return

        # 获取当前特征组合
        feature_combination = self.get_current_feature_combination()

        # 获取备注
        notes = self.notes_text.get(1.0, tk.END).strip()

        # 创建增强标注数据
        annotation_data = {
            'growth_level': feature_combination.growth_level,
            'growth_pattern': feature_combination.growth_pattern,
            'interference_factors': [f.value if hasattr(f, 'value') else f for f in feature_combination.interference_factors],
            'confidence': feature_combination.confidence,
            'microbe_type': self.microbe_type_var.get(),
            'notes': notes,
            'feature_combination': feature_combination.to_dict()
        }

        # 保存标注
        self.annotations[self.current_hole] = annotation_data

        # 发布标注保存事件
        self.event_bus.publish(EventType.ANNOTATION_SAVED, {
            'hole_id': self.current_hole,
            'annotation': annotation_data
        })

        # 更新界面
        self._update_annotation_status()
        self._update_annotation_list()

        logger.info(f"Enhanced annotation saved for hole {self.current_hole}")

    def _clear_enhanced_annotation(self):
        """清除增强标注"""
        if not self.current_hole:
            return

        # 清除标注
        if self.current_hole in self.annotations:
            del self.annotations[self.current_hole]

        # 重置界面状态
        self.current_growth_level.set("negative")
        self.current_growth_pattern.set("")
        self.current_confidence.set(1.0)
        self.microbe_type_var.set("bacteria")

        # 重置干扰因素
        for var in self.interference_vars.values():
            var.set(False)

        # 清空备注
        self.notes_text.delete(1.0, tk.END)

        # 更新生长模式选项
        self.update_pattern_options()

        # 发布标注清除事件
        self.event_bus.publish(EventType.ANNOTATION_DELETED, {
            'hole_id': self.current_hole
        })

        # 更新界面
        self._update_annotation_status()
        self._update_annotation_list()

        logger.info(f"Enhanced annotation cleared for hole {self.current_hole}")

    def _copy_enhanced_annotation(self):
        """复制增强标注"""
        if not self.current_hole or self.current_hole not in self.annotations:
            return

        # 复制当前标注到剪贴板
        annotation = self.annotations[self.current_hole]
        import json

        clip_data = json.dumps(annotation, ensure_ascii=False)
        self.widget.clipboard_clear()
        self.widget.clipboard_append(clip_data)

        logger.info(f"Enhanced annotation copied for hole {self.current_hole}")
    
    def _clear_annotation(self):
        """清除标注"""
        if not self.current_hole:
            return
        
        # 清除标注
        if self.current_hole in self.annotations:
            del self.annotations[self.current_hole]
        
        # 清空控件
        self.growth_level_var.set('')
        self.microbe_type_var.set('')
        self.notes_text.delete(1.0, tk.END)
        
        # 发布标注清除事件
        self.event_bus.publish(EventType.ANNOTATION_DELETED, {
            'hole_id': self.current_hole
        })
        
        # 更新界面
        self._update_annotation_status()
        self._update_annotation_list()
        
        logger.info(f"Annotation cleared for hole {self.current_hole}")
    
    def _copy_annotation(self):
        """复制标注"""
        if not self.current_hole or self.current_hole not in self.annotations:
            return
        
        # 复制当前标注到剪贴板
        annotation = self.annotations[self.current_hole]
        import json
        
        clip_data = json.dumps(annotation, ensure_ascii=False)
        self.widget.clipboard_clear()
        self.widget.clipboard_append(clip_data)
        
        logger.info(f"Annotation copied for hole {self.current_hole}")
    
    def _apply_to_all(self):
        """应用到所有孔位"""
        if not self.batch_growth_var.get() and not self.batch_microbe_var.get():
            return
        
        # 批量应用标注
        applied_count = 0
        for hole_id in self.annotations:
            if self.batch_growth_var.get():
                self.annotations[hole_id]['growth_level'] = self.batch_growth_var.get()
            if self.batch_microbe_var.get():
                self.annotations[hole_id]['microbe_type'] = self.batch_microbe_var.get()
            applied_count += 1
        
        # 发布批量应用事件
        self.event_bus.publish(EventType.ANNOTATION_UPDATED, {
            'action': 'batch_apply',
            'applied_count': applied_count
        })
        
        # 更新界面
        if self.current_hole:
            self._load_annotation()
        self._update_annotation_list()
        
        logger.info(f"Batch annotation applied to {applied_count} holes")
    
    def _apply_to_row(self):
        """应用到当前行"""
        if not self.current_hole:
            return
        
        row = self.current_hole[:2]
        applied_count = 0
        
        # 应用到同行的所有孔位
        for hole_id in self.annotations:
            if hole_id.startswith(row):
                if self.batch_growth_var.get():
                    self.annotations[hole_id]['growth_level'] = self.batch_growth_var.get()
                if self.batch_microbe_var.get():
                    self.annotations[hole_id]['microbe_type'] = self.batch_microbe_var.get()
                applied_count += 1
        
        # 发布事件
        self.event_bus.publish(EventType.ANNOTATION_UPDATED, {
            'action': 'batch_apply_row',
            'row': row,
            'applied_count': applied_count
        })
        
        # 更新界面
        if self.current_hole:
            self._load_annotation()
        self._update_annotation_list()
        
        logger.info(f"Batch annotation applied to row {row}, {applied_count} holes")
    
    def _apply_to_column(self):
        """应用到当前列"""
        if not self.current_hole:
            return
        
        col = self.current_hole[2:4]
        applied_count = 0
        
        # 应用到同列的所有孔位
        for hole_id in self.annotations:
            if hole_id.endswith(col):
                if self.batch_growth_var.get():
                    self.annotations[hole_id]['growth_level'] = self.batch_growth_var.get()
                if self.batch_microbe_var.get():
                    self.annotations[hole_id]['microbe_type'] = self.batch_microbe_var.get()
                applied_count += 1
        
        # 发布事件
        self.event_bus.publish(EventType.ANNOTATION_UPDATED, {
            'action': 'batch_apply_column',
            'column': col,
            'applied_count': applied_count
        })
        
        # 更新界面
        if self.current_hole:
            self._load_annotation()
        self._update_annotation_list()
        
        logger.info(f"Batch annotation applied to column {col}, {applied_count} holes")
    
    def _update_annotation_list(self):
        """更新标注列表"""
        self.annotation_listbox.delete(0, tk.END)
        
        for hole_id, annotation in self.annotations.items():
            # 转换孔位ID为Excel风格
            row = int(hole_id[:2])
            col = int(hole_id[2:4])
            row_letter = chr(ord('A') + row)
            col_number = col + 1
            
            # 构建列表项文本
            text_parts = [f"{row_letter}{col_number}"]
            
            if annotation.get('growth_level'):
                text_parts.append(f"生长:{annotation['growth_level']}")
            
            if annotation.get('microbe_type'):
                text_parts.append(f"类型:{annotation['microbe_type']}")
            
            list_text = " | ".join(text_parts)
            self.annotation_listbox.insert(tk.END, list_text)
    
    def _on_annotation_selected(self, event):
        """标注选择事件"""
        selection = self.annotation_listbox.curselection()
        if selection:
            index = selection[0]
            hole_id = list(self.annotations.keys())[index]
            
            # 发布孔位选择事件
            self.event_bus.publish(EventType.HOLE_SELECTED, {
                'hole_id': hole_id,
                'source': 'annotation_list'
            })
    
    def _delete_annotation(self):
        """删除标注"""
        selection = self.annotation_listbox.curselection()
        if selection:
            index = selection[0]
            hole_id = list(self.annotations.keys())[index]
            
            # 删除标注
            del self.annotations[hole_id]
            
            # 发布删除事件
            self.event_bus.publish(EventType.ANNOTATION_DELETED, {
                'hole_id': hole_id
            })
            
            # 更新界面
            if self.current_hole == hole_id:
                self._load_annotation()
                self._update_annotation_status()
            self._update_annotation_list()
            
            logger.info(f"Annotation deleted for hole {hole_id}")
    
    def _export_annotations(self):
        """导出标注"""
        # 发布导出事件
        self.event_bus.publish(EventType.FILE_EXPORTED, {
            'action': 'export_annotations',
            'annotations': self.annotations
        })
        
        logger.info("Annotation export requested")
    
    def _import_annotations(self):
        """导入标注"""
        # 发布导入事件
        self.event_bus.publish(EventType.FILE_OPENED, {
            'action': 'import_annotations'
        })
        
        logger.info("Annotation import requested")
    
    def get_annotation(self, hole_id: str) -> Optional[Dict[str, Any]]:
        """获取标注数据"""
        return self.annotations.get(hole_id)
    
    def set_annotation(self, hole_id: str, annotation: Dict[str, Any]):
        """设置标注数据"""
        self.annotations[hole_id] = annotation
        
        # 发布更新事件
        self.event_bus.publish(EventType.ANNOTATION_UPDATED, {
            'hole_id': hole_id,
            'annotation': annotation
        })
        
        # 更新界面
        if self.current_hole == hole_id:
            self._load_annotation()
            self._update_annotation_status()
        self._update_annotation_list()
    
    def get_all_annotations(self) -> Dict[str, Dict[str, Any]]:
        """获取所有标注数据"""
        return self.annotations.copy()
    
    def clear_all_annotations(self):
        """清除所有标注"""
        self.annotations.clear()
        
        # 更新界面
        self._load_annotation()
        self._update_annotation_status()
        self._update_annotation_list()
        
        # 发布清除事件
        self.event_bus.publish(EventType.ANNOTATION_UPDATED, {
            'action': 'clear_all'
        })
        
        logger.info("All annotations cleared")
    
    def set_current_hole(self, hole_id: str):
        """设置当前孔位"""
        self.current_hole = hole_id
        self._update_hole_info()
        self._load_annotation()
    
    def get_current_hole(self) -> Optional[str]:
        """获取当前孔位"""
        return self.current_hole