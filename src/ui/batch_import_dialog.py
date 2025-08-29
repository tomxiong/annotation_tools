"""
批量导入标注对话框
支持导入标注字符串格式
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import re
from pathlib import Path


class BatchImportDialog:
    """批量导入标注对话框"""
    
    def __init__(self, parent, callback=None):
        self.parent = parent
        self.callback = callback
        self.result = None
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("批量导入标注")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 居中显示
        self.center_window()
        
        # 创建界面
        self.create_widgets()
        
        # 绑定事件
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
    
    def center_window(self):
        """窗口居中显示"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_widgets(self):
        """创建界面组件"""
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = ttk.Label(main_frame, text="批量导入标注数据", font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 说明文本
        info_text = """
支持的格式：
1. 文件名 + 标注字符串：EB10000026.bmp,-++--+----+-+-++++-++--++++++...
2. 每行一个全景图的标注数据
3. 标注字符串长度必须为120个字符（对应12×10网格）
4. 字符含义：+ = 阳性，- = 阴性，w = 弱生长，? = 未知
        """
        
        info_label = ttk.Label(main_frame, text=info_text, justify=tk.LEFT)
        info_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 输入方式选择
        input_frame = ttk.LabelFrame(main_frame, text="输入方式")
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.input_method = tk.StringVar(value="text")
        
        ttk.Radiobutton(input_frame, text="直接输入文本", variable=self.input_method, 
                       value="text", command=self.on_input_method_change).pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(input_frame, text="从文件导入", variable=self.input_method, 
                       value="file", command=self.on_input_method_change).pack(anchor=tk.W, padx=5, pady=2)
        
        # 文件选择框
        self.file_frame = ttk.Frame(main_frame)
        self.file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.file_frame, text="选择文件:").pack(side=tk.LEFT)
        self.file_path_var = tk.StringVar()
        file_entry = ttk.Entry(self.file_frame, textvariable=self.file_path_var, width=50)
        file_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        ttk.Button(self.file_frame, text="浏览", command=self.select_file).pack(side=tk.LEFT)
        
        # 文本输入框
        text_frame = ttk.LabelFrame(main_frame, text="标注数据")
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建文本框和滚动条
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_widget = tk.Text(text_container, wrap=tk.WORD, height=15)
        scrollbar = ttk.Scrollbar(text_container, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 示例数据
        example_text = "EB10000026.bmp,-++--+----+-+-++++-++--++++++++++++++++++++++++++++++---+++++++++++++++--++++++++++--++------++++-++++-++++++"
        self.text_widget.insert(tk.END, example_text)
        
        # 微生物类型选择
        microbe_frame = ttk.LabelFrame(main_frame, text="微生物类型")
        microbe_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.microbe_type = tk.StringVar(value="bacteria")
        ttk.Radiobutton(microbe_frame, text="细菌", variable=self.microbe_type, 
                       value="bacteria").pack(side=tk.LEFT, padx=10, pady=5)
        ttk.Radiobutton(microbe_frame, text="真菌", variable=self.microbe_type, 
                       value="fungi").pack(side=tk.LEFT, padx=10, pady=5)
        
        # 按钮框
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="预览", command=self.preview_data).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="导入", command=self.import_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=self.on_cancel).pack(side=tk.RIGHT)
        
        # 初始状态
        self.on_input_method_change()
    
    def on_input_method_change(self):
        """输入方式改变时的处理"""
        if self.input_method.get() == "file":
            # 显示文件选择，隐藏文本输入
            for widget in self.file_frame.winfo_children():
                widget.configure(state="normal")
        else:
            # 隐藏文件选择，显示文本输入
            for widget in self.file_frame.winfo_children():
                if isinstance(widget, ttk.Entry):
                    widget.configure(state="disabled")
                elif isinstance(widget, ttk.Button):
                    widget.configure(state="disabled")
    
    def select_file(self):
        """选择导入文件"""
        filename = filedialog.askopenfilename(
            title="选择标注数据文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("CSV文件", "*.csv"),
                ("所有文件", "*.*")
            ]
        )
        if filename:
            self.file_path_var.set(filename)
            # 读取文件内容
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_widget.delete(1.0, tk.END)
                self.text_widget.insert(1.0, content)
            except Exception as e:
                messagebox.showerror("错误", f"读取文件失败: {str(e)}")
    
    def parse_annotation_data(self, text: str) -> List[Dict]:
        """解析标注数据"""
        results = []
        lines = text.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                # 解析格式：filename,annotation_string
                if ',' in line:
                    parts = line.split(',', 1)
                    if len(parts) == 2:
                        filename = parts[0].strip()
                        annotation_string = parts[1].strip()
                    else:
                        raise ValueError("格式错误：缺少逗号分隔符")
                else:
                    # 如果没有逗号，假设整行都是标注字符串，需要用户提供文件名
                    filename = f"unknown_{line_num}.bmp"
                    annotation_string = line
                
                # 验证标注字符串长度
                if len(annotation_string) != 120:
                    raise ValueError(f"标注字符串长度错误：期望120个字符，实际{len(annotation_string)}个字符")
                
                # 验证字符有效性
                valid_chars = {'+', '-', 'w', '?'}
                invalid_chars = set(annotation_string) - valid_chars
                if invalid_chars:
                    raise ValueError(f"包含无效字符: {invalid_chars}")
                
                # 提取全景图ID
                panoramic_id = self.extract_panoramic_id(filename)
                
                results.append({
                    'filename': filename,
                    'panoramic_id': panoramic_id,
                    'annotation_string': annotation_string,
                    'line_number': line_num
                })
                
            except Exception as e:
                raise ValueError(f"第{line_num}行解析错误: {str(e)}")
        
        return results
    
    def extract_panoramic_id(self, filename: str) -> str:
        """从文件名提取全景图ID"""
        # 移除扩展名
        stem = Path(filename).stem
        
        # 尝试匹配常见格式
        patterns = [
            r'^([A-Z]+\d+)',  # EB10000026
            r'^(\w+)',        # 通用模式
        ]
        
        for pattern in patterns:
            match = re.match(pattern, stem)
            if match:
                return match.group(1)
        
        return stem
    
    def convert_annotation_string_to_annotations(self, data: Dict) -> List[Dict]:
        """将标注字符串转换为标注对象列表"""
        annotations = []
        annotation_string = data['annotation_string']
        panoramic_id = data['panoramic_id']
        
        for i, char in enumerate(annotation_string):
            hole_number = i + 1  # 孔位编号从1开始
            
            # 转换字符到生长级别
            if char == '+':
                growth_level = 'positive'
            elif char == '-':
                growth_level = 'negative'
            elif char == 'w':
                growth_level = 'weak_growth'
            else:  # '?' 或其他
                growth_level = 'negative'  # 默认为阴性
            
            # 计算行列号
            hole_row = (hole_number - 1) // 12
            hole_col = (hole_number - 1) % 12
            
            # 生成切片文件名
            slice_filename = f"{panoramic_id}_hole_{hole_number}.png"
            
            annotations.append({
                'slice_filename': slice_filename,
                'panoramic_id': panoramic_id,
                'hole_number': hole_number,
                'hole_row': hole_row,
                'hole_col': hole_col,
                'growth_level': growth_level,
                'microbe_type': self.microbe_type.get(),
                'confidence': 1.0,
                'bbox': [0, 0, 70, 70]  # 默认边界框
            })
        
        return annotations
    
    def preview_data(self):
        """预览数据"""
        try:
            text = self.text_widget.get(1.0, tk.END).strip()
            if not text:
                messagebox.showwarning("警告", "请输入标注数据")
                return
            
            # 解析数据
            parsed_data = self.parse_annotation_data(text)
            
            # 创建预览窗口
            preview_window = tk.Toplevel(self.dialog)
            preview_window.title("数据预览")
            preview_window.geometry("800x600")
            preview_window.transient(self.dialog)
            
            # 创建树形视图
            tree_frame = ttk.Frame(preview_window)
            tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            columns = ('panoramic_id', 'total_holes', 'positive', 'negative', 'weak_growth')
            tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
            
            # 设置列标题
            tree.heading('panoramic_id', text='全景图ID')
            tree.heading('total_holes', text='总孔位数')
            tree.heading('positive', text='阳性')
            tree.heading('negative', text='阴性')
            tree.heading('weak_growth', text='弱生长')
            
            # 设置列宽
            tree.column('panoramic_id', width=150)
            tree.column('total_holes', width=100)
            tree.column('positive', width=80)
            tree.column('negative', width=80)
            tree.column('weak_growth', width=80)
            
            # 统计数据
            for data in parsed_data:
                annotations = self.convert_annotation_string_to_annotations(data)
                
                stats = {'positive': 0, 'negative': 0, 'weak_growth': 0}
                for ann in annotations:
                    stats[ann['growth_level']] += 1
                
                tree.insert('', tk.END, values=(
                    data['panoramic_id'],
                    len(annotations),
                    stats['positive'],
                    stats['negative'],
                    stats['weak_growth']
                ))
            
            # 添加滚动条
            scrollbar_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar_y.set)
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            
            # 关闭按钮
            ttk.Button(preview_window, text="关闭", 
                      command=preview_window.destroy).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("错误", f"预览失败: {str(e)}")
    
    def import_data(self):
        """导入数据"""
        try:
            text = self.text_widget.get(1.0, tk.END).strip()
            if not text:
                messagebox.showwarning("警告", "请输入标注数据")
                return
            
            # 解析数据
            parsed_data = self.parse_annotation_data(text)
            
            # 转换为标注对象
            all_annotations = []
            for data in parsed_data:
                annotations = self.convert_annotation_string_to_annotations(data)
                all_annotations.extend(annotations)
            
            # 确认导入
            total_annotations = len(all_annotations)
            total_panoramic = len(parsed_data)
            
            confirm_msg = f"将导入 {total_panoramic} 个全景图的 {total_annotations} 个标注。\n\n确定要导入吗？"
            
            if messagebox.askyesno("确认导入", confirm_msg):
                self.result = all_annotations
                
                if self.callback:
                    self.callback(all_annotations)
                
                messagebox.showinfo("成功", f"成功导入 {total_annotations} 个标注")
                self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("错误", f"导入失败: {str(e)}")
    
    def on_cancel(self):
        """取消操作"""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """显示对话框并等待结果"""
        self.dialog.wait_window()
        return self.result


def show_batch_import_dialog(parent, callback=None):
    """显示批量导入对话框的便捷函数"""
    dialog = BatchImportDialog(parent, callback)
    return dialog.show()