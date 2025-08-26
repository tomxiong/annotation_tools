"""
标注功能Mixin
包含所有标注相关的方法
"""
import json
import os
import sys
from tkinter import messagebox

class AnnotationMixin:
    """标注功能混入类"""
    
    def save_current_annotation_internal(self):
        """内部保存当前标注的方法"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            panoramic_id = current_file['panoramic_id']
            hole_number = current_file['hole_number']
            
            # 获取标注数据
            annotation_data = self.annotation_panel.get_annotation_data()
            
            # 创建标注对象
            try:
                from ...models.panoramic_annotation import PanoramicAnnotation
            except ImportError:
                # 如果相对导入失败，尝试绝对导入
                sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
                from models.panoramic_annotation import PanoramicAnnotation
            
            annotation = PanoramicAnnotation(
                panoramic_image_id=panoramic_id,
                hole_number=hole_number,
                row=self.hole_manager.get_row_from_hole_number(hole_number),
                col=self.hole_manager.get_col_from_hole_number(hole_number),
                **annotation_data
            )
            
            # 保存到配置文件
            self.config_service.save_annotation(annotation)
            
        except Exception as e:
            print(f"保存标注失败: {e}")
    
    def save_current_annotation(self):
        """保存当前标注"""
        try:
            self.save_current_annotation_internal()
            self.update_status("标注已保存")
        except Exception as e:
            messagebox.showerror("错误", f"保存标注失败: {e}")
    
    def load_annotation_for_current_slice(self):
        """为当前切片加载标注"""
        if not self.slice_files or self.current_slice_index >= len(self.slice_files):
            return
        
        try:
            current_file = self.slice_files[self.current_slice_index]
            panoramic_id = current_file['panoramic_id']
            hole_number = current_file['hole_number']
            
            # 从配置文件加载标注
            annotation = self.config_service.get_annotation(panoramic_id, hole_number)
            
            if annotation:
                # 设置标注数据到面板
                self.annotation_panel.set_annotation_data({
                    'has_bacteria': annotation.has_bacteria,
                    'bacteria_count': annotation.bacteria_count,
                    'bacteria_type': annotation.bacteria_type,
                    'has_impurities': annotation.has_impurities,
                    'impurities_type': annotation.impurities_type,
                    'image_quality': annotation.image_quality,
                    'notes': annotation.notes
                })
            else:
                # 清空标注面板
                self.annotation_panel.clear_annotation()
                
        except Exception as e:
            print(f"加载标注失败: {e}")
            self.annotation_panel.clear_annotation()
    
    def clear_current_annotation(self):
        """清空当前标注"""
        try:
            self.annotation_panel.clear_annotation()
            self.update_status("标注已清空")
        except Exception as e:
            messagebox.showerror("错误", f"清空标注失败: {e}")
    
    def export_annotations(self):
        """导出标注数据"""
        try:
            from tkinter import filedialog
            
            # 选择导出文件
            filename = filedialog.asksaveasfilename(
                title="导出标注数据",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                # 获取所有标注数据
                annotations = self.config_service.get_all_annotations()
                
                # 转换为可序列化的格式
                export_data = []
                for annotation in annotations:
                    export_data.append({
                        'panoramic_image_id': annotation.panoramic_image_id,
                        'hole_number': annotation.hole_number,
                        'row': annotation.row,
                        'col': annotation.col,
                        'has_bacteria': annotation.has_bacteria,
                        'bacteria_count': annotation.bacteria_count,
                        'bacteria_type': annotation.bacteria_type,
                        'has_impurities': annotation.has_impurities,
                        'impurities_type': annotation.impurities_type,
                        'image_quality': annotation.image_quality,
                        'notes': annotation.notes
                    })
                
                # 写入文件
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("成功", f"标注数据已导出到: {filename}")
                
        except Exception as e:
            messagebox.showerror("错误", f"导出标注数据失败: {e}")
    
    def import_annotations(self):
        """导入标注数据"""
        try:
            from tkinter import filedialog
            
            # 选择导入文件
            filename = filedialog.askopenfilename(
                title="导入标注数据",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                # 读取文件
                with open(filename, 'r', encoding='utf-8') as f:
                    import_data = json.load(f)
                
                # 导入标注数据
                try:
                    from ...models.panoramic_annotation import PanoramicAnnotation
                except ImportError:
                    sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
                    from models.panoramic_annotation import PanoramicAnnotation
                
                imported_count = 0
                
                for data in import_data:
                    annotation = PanoramicAnnotation(
                        panoramic_image_id=data['panoramic_image_id'],
                        hole_number=data['hole_number'],
                        row=data['row'],
                        col=data['col'],
                        has_bacteria=data.get('has_bacteria', False),
                        bacteria_count=data.get('bacteria_count', 0),
                        bacteria_type=data.get('bacteria_type', ''),
                        has_impurities=data.get('has_impurities', False),
                        impurities_type=data.get('impurities_type', ''),
                        image_quality=data.get('image_quality', '良好'),
                        notes=data.get('notes', '')
                    )
                    
                    self.config_service.save_annotation(annotation)
                    imported_count += 1
                
                messagebox.showinfo("成功", f"已导入 {imported_count} 条标注数据")
                
                # 重新加载当前切片的标注
                self.load_annotation_for_current_slice()
                
        except Exception as e:
            messagebox.showerror("错误", f"导入标注数据失败: {e}")
    
    def get_annotation_statistics(self):
        """获取标注统计信息"""
        try:
            annotations = self.config_service.get_all_annotations()
            
            total_count = len(annotations)
            bacteria_count = sum(1 for a in annotations if a.has_bacteria)
            impurities_count = sum(1 for a in annotations if a.has_impurities)
            
            # 按图像质量统计
            quality_stats = {}
            for annotation in annotations:
                quality = annotation.image_quality
                quality_stats[quality] = quality_stats.get(quality, 0) + 1
            
            # 按细菌类型统计
            bacteria_type_stats = {}
            for annotation in annotations:
                if annotation.has_bacteria and annotation.bacteria_type:
                    bacteria_type = annotation.bacteria_type
                    bacteria_type_stats[bacteria_type] = bacteria_type_stats.get(bacteria_type, 0) + 1
            
            return {
                'total_count': total_count,
                'bacteria_count': bacteria_count,
                'impurities_count': impurities_count,
                'quality_stats': quality_stats,
                'bacteria_type_stats': bacteria_type_stats
            }
            
        except Exception as e:
            print(f"获取统计信息失败: {e}")
            return None
    
    def show_annotation_statistics(self):
        """显示标注统计信息"""
        try:
            stats = self.get_annotation_statistics()
            if not stats:
                messagebox.showwarning("警告", "无法获取统计信息")
                return
            
            # 构建统计信息文本
            message = f"""标注统计信息：

总标注数量: {stats['total_count']}
有细菌的样本: {stats['bacteria_count']}
有杂质的样本: {stats['impurities_count']}

图像质量分布:"""
            
            for quality, count in stats['quality_stats'].items():
                message += f"\n  {quality}: {count}"
            
            if stats['bacteria_type_stats']:
                message += "\n\n细菌类型分布:"
                for bacteria_type, count in stats['bacteria_type_stats'].items():
                    message += f"\n  {bacteria_type}: {count}"
            
            messagebox.showinfo("标注统计", message)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示统计信息失败: {e}")