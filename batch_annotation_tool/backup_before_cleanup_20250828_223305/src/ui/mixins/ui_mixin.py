"""
UI创建功能Mixin
包含所有UI创建相关的方法
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class UIMixin:
    """UI创建功能混入类"""
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="打开切片目录", command=self.load_slice_directory)
        file_menu.add_separator()
        file_menu.add_command(label="导出标注", command=self.export_annotations)
        file_menu.add_command(label="导入标注", command=self.import_annotations)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_window_close)
        
        # 导航菜单
        nav_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="导航", menu=nav_menu)
        nav_menu.add_command(label="第一个孔位", command=self.go_first_hole)
        nav_menu.add_command(label="最后一个孔位", command=self.go_last_hole)
        nav_menu.add_separator()
        nav_menu.add_command(label="上一个全景图", command=self.go_prev_panoramic)
        nav_menu.add_command(label="下一个全景图", command=self.go_next_panoramic)
        
        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图", menu=view_menu)
        view_menu.add_command(label="适应窗口", command=self.fit_to_window)
        view_menu.add_command(label="重置缩放", command=self.reset_zoom)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="工具", menu=tools_menu)
        tools_menu.add_command(label="标注统计", command=self.show_annotation_statistics)
        tools_menu.add_separator()
        tools_menu.add_checkbutton(label="子目录模式", variable=self.use_subdirectory_mode)
        tools_menu.add_checkbutton(label="居中导航", variable=self.use_centered_navigation)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="快捷键说明", command=self.show_shortcuts_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def show_shortcuts_help(self):
        """显示快捷键帮助"""
        help_text = """快捷键说明：

方向导航：
  ↑↓←→ - 方向导航
  Page Up/Down - 上一个/下一个孔位
  Home/End - 第一个/最后一个孔位
  Ctrl+←/→ - 上一个/下一个全景图

功能快捷键：
  Ctrl+S - 保存标注
  Ctrl+O - 打开目录
  Delete - 清空标注
  F5 - 刷新当前切片
  
数字键 - 输入孔位编号
Enter - 跳转到输入的孔位
Esc - 清空孔位输入框
鼠标滚轮 - 切换孔位"""
        
        messagebox.showinfo("快捷键说明", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """全景图标注工具

版本: 2.0
作者: AI Assistant
描述: 用于全景图切片的批量标注工具

功能特性：
- 支持多全景图导航
- 方向导航和居中导航
- 子目录模式
- 标注数据导入导出
- 快捷键操作"""
        
        messagebox.showinfo("关于", about_text)