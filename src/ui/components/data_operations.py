"""
数据操作模块
负责处理所有数据的加载、保存、导入导出操作
从原panoramic_annotation_gui.py中拆分出来
"""

import tkinter as tk
from tkinter import filedialog, messagebox
import os
import json
from pathlib import Path
from typing import Optional, Dict, List, Any


class DataOperations:
    """数据操作管理类"""
    
    def __init__(self, parent_gui):
        """
        初始化数据操作管理器
        
        Args:
            parent_gui: 主GUI实例，用于访问必要的属性和方法
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        
    # === 数据操作方法 ===
    
    def select_panoramic_directory(self):
        """选择全景图目录"""
        try:
            directory = filedialog.askdirectory(title="选择全景图目录")
            if directory:
                self.gui.panoramic_directory = directory
                if hasattr(self.gui, 'panoramic_dir_var'):
                    self.gui.panoramic_dir_var.set(directory)
                self.gui.log_info(f"已选择全景图目录: {directory}", "DATA")
                return True
        except Exception as e:
            self.gui.log_error(f"选择目录失败: {e}", "DATA")
            messagebox.showerror("错误", f"选择目录失败: {str(e)}")
        return False
    
    def load_annotations(self):
        """加载标注数据"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择标注文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            if file_path:
                self.gui.log_info(f"加载标注文件: {file_path}", "DATA")
                # TODO: 实现标注加载逻辑
                return True
        except Exception as e:
            self.gui.log_error(f"加载标注失败: {e}", "DATA")
            messagebox.showerror("错误", f"加载标注失败: {str(e)}")
        return False
    
    def save_annotations(self):
        """保存标注数据"""
        try:
            file_path = filedialog.asksaveasfilename(
                title="保存标注文件",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            if file_path:
                self.gui.log_info(f"保存标注文件: {file_path}", "DATA")
                # TODO: 实现标注保存逻辑
                return True
        except Exception as e:
            self.gui.log_error(f"保存标注失败: {e}", "DATA")
            messagebox.showerror("错误", f"保存标注失败: {str(e)}")
        return False
    
    def export_training_data(self):
        """导出训练数据"""
        try:
            directory = filedialog.askdirectory(title="选择导出目录")
            if directory:
                self.gui.log_info(f"导出训练数据到: {directory}", "DATA")
                # TODO: 实现训练数据导出逻辑
                return True
        except Exception as e:
            self.gui.log_error(f"导出训练数据失败: {e}", "DATA")
            messagebox.showerror("错误", f"导出训练数据失败: {str(e)}")
        return False
    
    def import_model_suggestions(self):
        """导入模型建议"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择模型建议文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )
            if file_path:
                self.gui.log_info(f"导入模型建议: {file_path}", "DATA")
                # TODO: 实现模型建议导入逻辑
                return True
        except Exception as e:
            self.gui.log_error(f"导入模型建议失败: {e}", "DATA")
            messagebox.showerror("错误", f"导入模型建议失败: {str(e)}")
        return False