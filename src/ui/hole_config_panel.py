"""
孔位配置面板
提供动态调整孔位定位参数的界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class HoleConfigPanel:
    """孔位配置面板类"""
    
    def __init__(self, parent: tk.Widget, apply_callback: Callable):
        self.parent = parent
        self.apply_callback = apply_callback
        
        # 配置变量
        self.hole_x_var = tk.StringVar(value="750")
        self.hole_y_var = tk.StringVar(value="392")
        self.hole_spacing_x_var = tk.StringVar(value="145")
        self.hole_spacing_y_var = tk.StringVar(value="145")
        self.hole_size_var = tk.StringVar(value="90")
        self.start_hole_var = tk.StringVar(value="25")  # 起始孔位，默认25
        
        # 创建界面
        self.create_panel()
    
    def create_panel(self):
        """创建配置面板"""
        self.config_frame = ttk.LabelFrame(self.parent, text="孔位定位配置")
        self.config_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # 第一个孔位坐标
        self.create_coordinate_section()
        
        # 孔位间距
        self.create_spacing_section()
        
        # 孔位尺寸
        # 孔位尺寸
        self.create_size_section()
        
        # 起始孔位设置
        self.create_start_hole_section()
        
        # 控制按钮
        self.create_buttons()
        
        # 说明信息
        self.create_info_section()
    
    def create_coordinate_section(self):
        """创建坐标配置区域"""
        coord_frame = ttk.LabelFrame(self.config_frame, text="第一个孔位坐标")
        coord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # X坐标
        x_frame = ttk.Frame(coord_frame)
        x_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(x_frame, text="X坐标:").pack(side=tk.LEFT)
        x_entry = ttk.Entry(x_frame, textvariable=self.hole_x_var, width=8)
        x_entry.pack(side=tk.RIGHT)
        
        # Y坐标
        y_frame = ttk.Frame(coord_frame)
        y_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(y_frame, text="Y坐标:").pack(side=tk.LEFT)
        y_entry = ttk.Entry(y_frame, textvariable=self.hole_y_var, width=8)
        y_entry.pack(side=tk.RIGHT)
    
    def create_spacing_section(self):
        """创建间距配置区域"""
        spacing_frame = ttk.LabelFrame(self.config_frame, text="孔位间距")
        spacing_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 水平间距
        h_spacing_frame = ttk.Frame(spacing_frame)
        h_spacing_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(h_spacing_frame, text="水平间距:").pack(side=tk.LEFT)
        h_entry = ttk.Entry(h_spacing_frame, textvariable=self.hole_spacing_x_var, width=8)
        h_entry.pack(side=tk.RIGHT)
        
        # 垂直间距
        v_spacing_frame = ttk.Frame(spacing_frame)
        v_spacing_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(v_spacing_frame, text="垂直间距:").pack(side=tk.LEFT)
        v_entry = ttk.Entry(v_spacing_frame, textvariable=self.hole_spacing_y_var, width=8)
        v_entry.pack(side=tk.RIGHT)
        
    def create_size_section(self):
        """创建尺寸配置区域"""
        size_frame = ttk.LabelFrame(self.config_frame, text="孔位外框尺寸")
        size_frame.pack(fill=tk.X, padx=5, pady=5)
        
        size_input_frame = ttk.Frame(size_frame)
        size_input_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(size_input_frame, text="直径:").pack(side=tk.LEFT)
        size_entry = ttk.Entry(size_input_frame, textvariable=self.hole_size_var, width=8)
        size_entry.pack(side=tk.RIGHT)
    
    def create_start_hole_section(self):
        """创建起始孔位配置区域"""
        start_frame = ttk.LabelFrame(self.config_frame, text="标注范围")
        start_frame.pack(fill=tk.X, padx=5, pady=5)
        
        start_input_frame = ttk.Frame(start_frame)
        start_input_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(start_input_frame, text="起始孔位:").pack(side=tk.LEFT)
        start_entry = ttk.Entry(start_input_frame, textvariable=self.start_hole_var, width=8)
        start_entry.pack(side=tk.RIGHT)
        
        # 说明文字
        info_label = ttk.Label(start_frame, text="(前面的孔位将被忽略)", 
                              font=('TkDefaultFont', 8), foreground='gray')
        info_label.pack(pady=2)
    
    def create_buttons(self):
        """创建控制按钮"""
        button_frame = ttk.Frame(self.config_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="应用配置", 
                  command=self.apply_config).pack(fill=tk.X, pady=2)
        ttk.Button(button_frame, text="重置默认", 
                  command=self.reset_config).pack(fill=tk.X, pady=2)
    
    def create_info_section(self):
        """创建说明信息区域"""
        info_frame = ttk.Frame(self.config_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        info_text = tk.Text(info_frame, height=4, width=25, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True)
        info_text.insert(tk.END, "说明：\n调整第一个孔位(A1)的坐标和孔位间距，然后点击'应用配置'更新显示。")
        info_text.config(state=tk.DISABLED)
        
    def apply_config(self):
        """应用配置"""
        try:
            # 获取用户输入的参数
            start_hole = int(self.start_hole_var.get())
            
            # 验证起始孔位范围
            if start_hole < 1 or start_hole > 120:
                messagebox.showerror("错误", "起始孔位必须在1-120之间")
                return
            
            config = {
                'first_x': int(self.hole_x_var.get()),
                'first_y': int(self.hole_y_var.get()),
                'spacing_x': int(self.hole_spacing_x_var.get()),
                'spacing_y': int(self.hole_spacing_y_var.get()),
                'hole_size': int(self.hole_size_var.get()),
                'start_hole': start_hole
            }
            
            # 调用回调函数
            self.apply_callback(config)
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
        except Exception as e:
            messagebox.showerror("错误", f"应用配置失败: {str(e)}")
    
    def reset_config(self):
        """重置为默认配置"""
        self.hole_x_var.set("520")
        self.hole_y_var.set("180")
        self.hole_spacing_x_var.set("195")
        self.hole_spacing_y_var.set("155")
        self.hole_size_var.set("80")
        
    def get_config(self) -> dict:
        """获取当前配置"""
        try:
            return {
                'first_x': int(self.hole_x_var.get()),
                'first_y': int(self.hole_y_var.get()),
                'spacing_x': int(self.hole_spacing_x_var.get()),
                'spacing_y': int(self.hole_spacing_y_var.get()),
                'hole_size': int(self.hole_size_var.get()),
                'start_hole': int(self.start_hole_var.get())
            }
        except ValueError:
            return None
        
    def set_config(self, config: dict):
        """设置配置值"""
        if 'first_x' in config:
            self.hole_x_var.set(str(config['first_x']))
        if 'first_y' in config:
            self.hole_y_var.set(str(config['first_y']))
        if 'spacing_x' in config:
            self.hole_spacing_x_var.set(str(config['spacing_x']))
        if 'spacing_y' in config:
            self.hole_spacing_y_var.set(str(config['spacing_y']))
        if 'hole_size' in config:
            self.hole_size_var.set(str(config['hole_size']))
        if 'start_hole' in config:
            self.start_hole_var.set(str(config['start_hole']))
