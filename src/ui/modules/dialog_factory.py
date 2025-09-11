"""
对话框工厂模块
负责各种对话框的创建和管理
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from typing import Optional, Dict, Any, Callable, List
import json


class DialogFactory:
    """对话框工厂 - 负责创建和管理各种对话框"""
    
    def __init__(self, parent_gui):
        """
        初始化对话框工厂
        
        Args:
            parent_gui: 主GUI实例
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        self.open_dialogs = {}
        
    def show_directory_dialog(self) -> Optional[str]:
        """显示目录选择对话框"""
        try:
            directory = filedialog.askdirectory(
                title="选择标注数据目录",
                parent=self.root
            )
            
            if directory:
                self.gui.log_info(f"用户选择目录: {directory}", "DIALOG")
                
            return directory if directory else None
            
        except Exception as e:
            self.gui.log_error(f"目录选择对话框失败: {e}", "DIALOG")
            return None
            
    def show_export_dialog(self) -> Optional[Dict[str, str]]:
        """显示导出对话框"""
        try:
            # 创建自定义导出对话框
            dialog = self._create_export_dialog()
            if dialog:
                result = dialog.show()
                return result
                
        except Exception as e:
            self.gui.log_error(f"导出对话框失败: {e}", "DIALOG")
            
        return None
        
    def _create_export_dialog(self):
        """创建导出对话框"""
        return ExportDialog(self.root, self.gui)
        
    def show_about_dialog(self):
        """显示关于对话框"""
        try:
            # 获取版本信息
            try:
                from src.utils.version import get_version_display
                version = get_version_display()
            except ImportError:
                version = "v1.0.0"
                
            # 获取统计信息
            stats = self.gui.data_manager.get_statistics()
            
            about_text = f"""全景图像标注工具
            
版本: {version}

统计信息:
• 总切片数: {stats.get('total_slices', 0)}
• 已标注: {stats.get('total_annotations', 0)}
• 标注进度: {stats.get('progress_percent', 0):.1f}%
• 全景图数: {stats.get('panoramic_count', 0)}

快捷键:
• 1, 2, 3: 设置生长级别
• 方向键: 导航孔位
• Home/End: 首个/最后孔位
• PageUp/Down: 上一个/下一个全景图
• Space: 保存标注
• Enter: 下一个孔位
• Ctrl+S: 保存
• Ctrl+O: 打开目录
• F1: 显示帮助

开发团队: AI辅助开发
"""
            
            messagebox.showinfo(
                "关于全景图像标注工具",
                about_text,
                parent=self.root
            )
            
        except Exception as e:
            self.gui.log_error(f"关于对话框失败: {e}", "DIALOG")
            
    def show_help_dialog(self):
        """显示帮助对话框"""
        try:
            dialog = self._create_help_dialog()
            if dialog:
                dialog.show()
                
        except Exception as e:
            self.gui.log_error(f"帮助对话框失败: {e}", "DIALOG")
            
    def _create_help_dialog(self):
        """创建帮助对话框"""
        return HelpDialog(self.root, self.gui)
        
    def show_settings_dialog(self) -> Optional[Dict[str, Any]]:
        """显示设置对话框"""
        try:
            dialog = self._create_settings_dialog()
            if dialog:
                return dialog.show()
                
        except Exception as e:
            self.gui.log_error(f"设置对话框失败: {e}", "DIALOG")
            
        return None
        
    def _create_settings_dialog(self):
        """创建设置对话框"""
        return SettingsDialog(self.root, self.gui)
        
    def show_annotation_details_dialog(self, panoramic_id: str, hole_number: int) -> Optional[Dict[str, Any]]:
        """显示标注详情对话框"""
        try:
            annotation = self.gui.data_manager.get_annotation(panoramic_id, hole_number)
            dialog = self._create_annotation_details_dialog(annotation)
            if dialog:
                return dialog.show()
                
        except Exception as e:
            self.gui.log_error(f"标注详情对话框失败: {e}", "DIALOG")
            
        return None
        
    def _create_annotation_details_dialog(self, annotation):
        """创建标注详情对话框"""
        return AnnotationDetailsDialog(self.root, self.gui, annotation)
        
    def show_progress_dialog(self, title: str, max_value: int) -> 'ProgressDialog':
        """显示进度对话框"""
        try:
            dialog = ProgressDialog(self.root, title, max_value)
            return dialog
            
        except Exception as e:
            self.gui.log_error(f"进度对话框失败: {e}", "DIALOG")
            return None
            
    def show_confirmation_dialog(self, message: str, title: str = "确认") -> bool:
        """显示确认对话框"""
        try:
            result = messagebox.askyesno(
                title,
                message,
                parent=self.root
            )
            return result
            
        except Exception as e:
            self.gui.log_error(f"确认对话框失败: {e}", "DIALOG")
            return False
            
    def show_error_dialog(self, message: str, title: str = "错误"):
        """显示错误对话框"""
        try:
            messagebox.showerror(
                title,
                message,
                parent=self.root
            )
            
        except Exception as e:
            self.gui.log_error(f"错误对话框失败: {e}", "DIALOG")
            
    def show_warning_dialog(self, message: str, title: str = "警告"):
        """显示警告对话框"""
        try:
            messagebox.showwarning(
                title,
                message,
                parent=self.root
            )
            
        except Exception as e:
            self.gui.log_error(f"警告对话框失败: {e}", "DIALOG")
            
    def show_info_dialog(self, message: str, title: str = "信息"):
        """显示信息对话框"""
        try:
            messagebox.showinfo(
                title,
                message,
                parent=self.root
            )
            
        except Exception as e:
            self.gui.log_error(f"信息对话框失败: {e}", "DIALOG")


class BaseDialog:
    """对话框基类"""
    
    def __init__(self, parent, gui, title: str = "对话框"):
        self.parent = parent
        self.gui = gui
        self.title = title
        self.window = None
        self.result = None
        
    def show(self):
        """显示对话框"""
        self._create_window()
        self._create_widgets()
        self._setup_bindings()
        self._center_window()
        
        # 模态显示
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.wait_window()
        
        return self.result
        
    def _create_window(self):
        """创建窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.resizable(False, False)
        
    def _create_widgets(self):
        """创建控件 - 子类重写"""
        pass
        
    def _setup_bindings(self):
        """设置事件绑定"""
        self.window.bind('<Escape>', lambda e: self.cancel())
        
    def _center_window(self):
        """居中显示窗口"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
    def ok(self):
        """确定按钮处理"""
        self.result = True
        self.window.destroy()
        
    def cancel(self):
        """取消按钮处理"""
        self.result = None
        self.window.destroy()


class ExportDialog(BaseDialog):
    """导出对话框"""
    
    def __init__(self, parent, gui):
        super().__init__(parent, gui, "导出标注数据")
        self.format_var = tk.StringVar(value="json")
        self.path_var = tk.StringVar()
        
    def _create_widgets(self):
        """创建控件"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 导出格式选择
        format_frame = ttk.LabelFrame(main_frame, text="导出格式", padding="5")
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        formats = [("JSON格式", "json"), ("CSV格式", "csv"), ("XML格式", "xml")]
        for text, value in formats:
            rb = ttk.Radiobutton(format_frame, text=text, variable=self.format_var, value=value)
            rb.pack(anchor=tk.W)
            
        # 导出路径选择
        path_frame = ttk.LabelFrame(main_frame, text="导出路径", padding="5")
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        path_entry_frame = ttk.Frame(path_frame)
        path_entry_frame.pack(fill=tk.X)
        
        self.path_entry = ttk.Entry(path_entry_frame, textvariable=self.path_var, width=50)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = ttk.Button(path_entry_frame, text="浏览", command=self._browse_path)
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="导出", command=self._export).pack(side=tk.RIGHT)
        
    def _browse_path(self):
        """浏览保存路径"""
        format_type = self.format_var.get()
        extensions = {
            "json": [("JSON文件", "*.json")],
            "csv": [("CSV文件", "*.csv")],
            "xml": [("XML文件", "*.xml")]
        }
        
        file_path = filedialog.asksaveasfilename(
            title="保存导出文件",
            filetypes=extensions.get(format_type, [("所有文件", "*.*")]),
            parent=self.window
        )
        
        if file_path:
            self.path_var.set(file_path)
            
    def _export(self):
        """执行导出"""
        if not self.path_var.get():
            messagebox.showerror("错误", "请选择导出路径", parent=self.window)
            return
            
        success = self.gui.data_manager.export_training_data(
            self.path_var.get(),
            self.format_var.get()
        )
        
        if success:
            self.result = {
                'format': self.format_var.get(),
                'path': self.path_var.get()
            }
            messagebox.showinfo("成功", "数据导出完成", parent=self.window)
            self.window.destroy()
        else:
            messagebox.showerror("错误", "导出失败", parent=self.window)


class HelpDialog(BaseDialog):
    """帮助对话框"""
    
    def __init__(self, parent, gui):
        super().__init__(parent, gui, "操作帮助")
        
    def _create_widgets(self):
        """创建控件"""
        self.window.geometry("600x400")
        
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建notebook用于分类显示帮助内容
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 快捷键帮助
        shortcuts_frame = ttk.Frame(notebook)
        notebook.add(shortcuts_frame, text="快捷键")
        self._create_shortcuts_help(shortcuts_frame)
        
        # 操作指南
        operations_frame = ttk.Frame(notebook)
        notebook.add(operations_frame, text="操作指南")
        self._create_operations_help(operations_frame)
        
        # 关闭按钮
        close_btn = ttk.Button(main_frame, text="关闭", command=self.ok)
        close_btn.pack(anchor=tk.E)
        
    def _create_shortcuts_help(self, parent):
        """创建快捷键帮助"""
        text_frame = ttk.Frame(parent, padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        shortcuts_text = """快捷键列表:

导航操作:
• 方向键 (←→↑↓): 在孔位间导航
• Home: 跳转到第一个孔位
• End: 跳转到最后一个孔位
• PageUp: 上一个全景图
• PageDown: 下一个全景图

标注操作:
• 1: 设置为阴性 (negative)
• 2: 设置为弱生长 (weak_growth)
• 3: 设置为阳性 (positive)
• Space: 保存当前标注
• Enter: 保存并跳转到下一个孔位

文件操作:
• Ctrl+O: 打开目录
• Ctrl+S: 保存标注
• F1: 显示此帮助

其他:
• Escape: 关闭对话框
• Ctrl+L: 显示窗口调整日志
"""
        
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, shortcuts_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def _create_operations_help(self, parent):
        """创建操作指南"""
        text_frame = ttk.Frame(parent, padding="5")
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        operations_text = """操作指南:

1. 打开数据目录:
   - 点击"打开目录"按钮或按Ctrl+O
   - 选择包含全景图和切片图像的目录
   - 系统会自动扫描和加载图像文件

2. 图像导航:
   - 使用全景图下拉菜单选择不同的全景图
   - 点击全景图上的孔位直接跳转
   - 使用方向键在孔位间移动
   - 使用PageUp/PageDown在不同全景图间切换

3. 标注操作:
   - 观察右侧的切片图像
   - 使用数字键1、2、3快速设置生长级别
   - 或使用工具栏中的单选按钮
   - 按Space键保存当前标注

4. 数据管理:
   - 标注会自动保存到annotations.json文件
   - 使用"导出"功能导出不同格式的数据
   - 查看底部状态栏了解标注进度

5. 界面调整:
   - 拖动中间的分割条调整面板大小
   - 使用缩放滑块调整切片图像大小

注意事项:
- 确保图像文件命名规范（全景图ID_孔位号）
- 定期保存工作进度
- 标注质量影响最终的模型训练效果
"""
        
        text_widget.config(state=tk.NORMAL)
        text_widget.insert(tk.END, operations_text)
        text_widget.config(state=tk.DISABLED)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)


class SettingsDialog(BaseDialog):
    """设置对话框"""
    
    def __init__(self, parent, gui):
        super().__init__(parent, gui, "设置")
        self.settings = self._load_settings()
        
    def _load_settings(self) -> Dict[str, Any]:
        """加载设置"""
        # 默认设置
        default_settings = {
            'auto_save_interval': 60,  # 秒
            'zoom_sensitivity': 0.1,
            'grid_color': '#808080',
            'highlight_color': '#FF0000',
            'default_microbe_type': 'unknown',
            'confirm_before_exit': True
        }
        
        try:
            # 尝试从文件加载设置
            settings_file = "config/settings.json"
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
        except Exception:
            pass
            
        return default_settings
        
    def _create_widgets(self):
        """创建控件"""
        self.window.geometry("400x300")
        
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 设置项
        settings_frame = ttk.LabelFrame(main_frame, text="设置项", padding="5")
        settings_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 自动保存间隔
        auto_save_frame = ttk.Frame(settings_frame)
        auto_save_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(auto_save_frame, text="自动保存间隔(秒):").pack(side=tk.LEFT)
        self.auto_save_var = tk.IntVar(value=self.settings['auto_save_interval'])
        auto_save_spinbox = ttk.Spinbox(auto_save_frame, from_=10, to=600, textvariable=self.auto_save_var, width=10)
        auto_save_spinbox.pack(side=tk.RIGHT)
        
        # 缩放敏感度
        zoom_frame = ttk.Frame(settings_frame)
        zoom_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(zoom_frame, text="缩放敏感度:").pack(side=tk.LEFT)
        self.zoom_var = tk.DoubleVar(value=self.settings['zoom_sensitivity'])
        zoom_scale = ttk.Scale(zoom_frame, from_=0.01, to=0.5, variable=self.zoom_var, orient=tk.HORIZONTAL)
        zoom_scale.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
        
        # 默认微生物类型
        microbe_frame = ttk.Frame(settings_frame)
        microbe_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(microbe_frame, text="默认微生物类型:").pack(side=tk.LEFT)
        self.microbe_var = tk.StringVar(value=self.settings['default_microbe_type'])
        microbe_entry = ttk.Entry(microbe_frame, textvariable=self.microbe_var, width=15)
        microbe_entry.pack(side=tk.RIGHT)
        
        # 确认退出
        self.confirm_exit_var = tk.BooleanVar(value=self.settings['confirm_before_exit'])
        confirm_cb = ttk.Checkbutton(settings_frame, text="退出前确认", variable=self.confirm_exit_var)
        confirm_cb.pack(anchor=tk.W, pady=2)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="取消", command=self.cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="应用", command=self._apply_settings).pack(side=tk.RIGHT)
        
    def _apply_settings(self):
        """应用设置"""
        try:
            # 收集设置值
            new_settings = {
                'auto_save_interval': self.auto_save_var.get(),
                'zoom_sensitivity': self.zoom_var.get(),
                'default_microbe_type': self.microbe_var.get(),
                'confirm_before_exit': self.confirm_exit_var.get()
            }
            
            # 保存设置
            self._save_settings(new_settings)
            
            self.result = new_settings
            messagebox.showinfo("成功", "设置已保存", parent=self.window)
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}", parent=self.window)
            
    def _save_settings(self, settings: Dict[str, Any]):
        """保存设置到文件"""
        try:
            import os
            os.makedirs("config", exist_ok=True)
            
            with open("config/settings.json", 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"保存设置文件失败: {e}")


class AnnotationDetailsDialog(BaseDialog):
    """标注详情对话框"""
    
    def __init__(self, parent, gui, annotation):
        super().__init__(parent, gui, "标注详情")
        self.annotation = annotation
        
    def _create_widgets(self):
        """创建控件"""
        self.window.geometry("400x350")
        
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        if self.annotation:
            # 显示标注信息
            info_frame = ttk.LabelFrame(main_frame, text="标注信息", padding="5")
            info_frame.pack(fill=tk.X, pady=(0, 10))
            
            fields = [
                ("全景图ID", self.annotation.panoramic_id),
                ("孔位号", str(self.annotation.hole_number)),
                ("生长级别", self.annotation.growth_level),
                ("置信度", f"{self.annotation.confidence:.2f}"),
                ("微生物类型", self.annotation.microbe_type),
                ("标注来源", self.annotation.annotation_source),
                ("是否确认", "是" if self.annotation.is_confirmed else "否"),
                ("创建时间", self.annotation.timestamp)
            ]
            
            for i, (label, value) in enumerate(fields):
                frame = ttk.Frame(info_frame)
                frame.pack(fill=tk.X, pady=2)
                
                ttk.Label(frame, text=f"{label}:").pack(side=tk.LEFT, anchor=tk.W, padx=(0, 10))
                ttk.Label(frame, text=str(value)).pack(side=tk.RIGHT, anchor=tk.E)
                
            # 干扰因素
            if self.annotation.interference_factors:
                factors_frame = ttk.LabelFrame(main_frame, text="干扰因素", padding="5")
                factors_frame.pack(fill=tk.X, pady=(0, 10))
                
                factors_text = ", ".join(self.annotation.interference_factors)
                ttk.Label(factors_frame, text=factors_text, wraplength=350).pack(anchor=tk.W)
        else:
            # 无标注信息
            ttk.Label(main_frame, text="当前孔位未标注").pack(expand=True)
            
        # 关闭按钮
        close_btn = ttk.Button(main_frame, text="关闭", command=self.ok)
        close_btn.pack(anchor=tk.E)


class ProgressDialog:
    """进度对话框"""
    
    def __init__(self, parent, title: str, max_value: int):
        self.parent = parent
        self.title = title
        self.max_value = max_value
        self.current_value = 0
        
        self._create_window()
        
    def _create_window(self):
        """创建窗口"""
        self.window = tk.Toplevel(self.parent)
        self.window.title(self.title)
        self.window.geometry("300x100")
        self.window.resizable(False, False)
        
        # 居中显示
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (300 // 2)
        y = (self.window.winfo_screenheight() // 2) - (100 // 2)
        self.window.geometry(f"300x100+{x}+{y}")
        
        # 创建控件
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = ttk.Label(main_frame, text="准备中...")
        self.status_label.pack(pady=(0, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=self.max_value
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        self.percent_label = ttk.Label(main_frame, text="0%")
        self.percent_label.pack()
        
        # 模态显示
        self.window.transient(self.parent)
        self.window.grab_set()
        
    def update(self, value: int, status: str = ""):
        """更新进度"""
        self.current_value = min(value, self.max_value)
        self.progress_var.set(self.current_value)
        
        percent = int((self.current_value / self.max_value) * 100) if self.max_value > 0 else 0
        self.percent_label.config(text=f"{percent}%")
        
        if status:
            self.status_label.config(text=status)
            
        self.window.update()
        
    def close(self):
        """关闭对话框"""
        self.window.destroy()
