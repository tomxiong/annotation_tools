"""
标注管理模块
处理标注的保存、加载、清除和批量操作
"""

import tkinter as tk
from tkinter import messagebox
from typing import List, Dict, Any, Optional
import datetime


class AnnotationManager:
    """标注管理器"""
    
    def __init__(self, gui_instance):
        """初始化标注管理器"""
        self.gui = gui_instance
        self._config_cache = {}  # 缓存已解析的配置文件
    
    def save_current_annotation(self):
        """保存当前标注并跳转到下一个"""
        try:
            if self.save_current_annotation_internal():
                # 自动跳转到下一个
                if hasattr(self.gui, 'navigation_controller'):
                    self.gui.navigation_controller.go_next_hole()
                
                current_file = self.gui.slice_files[self.gui.current_slice_index - 1] if self.gui.current_slice_index > 0 else self.gui.slice_files[self.gui.current_slice_index]
                self.gui.update_status(f"已保存标注: {current_file['filename']}")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存标注失败: {str(e)}")
    
    def save_current_annotation_internal(self):
        """内部保存方法，不自动跳转"""
        print(f"[SAVE] annotation_manager.save_current_annotation_internal 被调用")
        if not self.gui.slice_files or self.gui.current_slice_index >= len(self.gui.slice_files):
            print(f"[SAVE] 早期退出: 没有切片文件或索引超出范围")
            return False
        
        try:
            current_file = self.gui.slice_files[self.gui.current_slice_index]
            
            # 使用增强标注模式 - 唯一的标注方式
            if hasattr(self.gui, 'enhanced_annotation_panel') and self.gui.enhanced_annotation_panel:
                try:
                    feature_combination = self.gui.enhanced_annotation_panel.get_current_feature_combination()
                    print(f"[SAVE] 准备保存增强标注: {feature_combination.growth_level} [{feature_combination.confidence:.2f}]")
                except Exception as e:
                    print(f"[ERROR] 获取特征组合失败: {e}")
                    raise
                
                # 创建增强标注对象
                from models.enhanced_annotation import EnhancedPanoramicAnnotation
                
                enhanced_annotation = EnhancedPanoramicAnnotation(
                    image_path=current_file['filepath'],
                    bbox=[0, 0, 70, 70],
                    panoramic_image_id=current_file.get('panoramic_id'),
                    hole_number=self.gui.current_hole_number,
                    microbe_type=self.gui.current_microbe_type.get(),
                    feature_combination=feature_combination,
                    annotation_source="enhanced_manual",
                    is_confirmed=True
                )
                
                # 转换为训练标签
                try:
                    training_label = enhanced_annotation.get_training_label()
                    print(f"[SAVE] 训练标签: {training_label}")
                except Exception as e:
                    print(f"[ERROR] 获取训练标签失败: {e}")
                    import traceback
                    traceback.print_exc()
                    raise
                
                # 创建兼容的PanoramicAnnotation对象用于显示
                from models.panoramic_annotation import PanoramicAnnotation
                annotation = PanoramicAnnotation.from_filename(
                    current_file['filename'],
                    label=training_label,
                    bbox=[0, 0, 70, 70],
                    confidence=feature_combination.confidence,
                    microbe_type=self.gui.current_microbe_type.get(),
                    growth_level=feature_combination.growth_level.value if hasattr(feature_combination.growth_level, 'value') else feature_combination.growth_level,
                    interference_factors=[f.value if hasattr(f, 'value') else f for f in feature_combination.interference_factors],
                    annotation_source="enhanced_manual",
                    is_confirmed=True,
                    panoramic_id=current_file.get('panoramic_id')
                )
                
                # 验证annotation_source是否正确设置
                print(f"[SAVE] 创建后的annotation.annotation_source: {annotation.annotation_source}")
                if annotation.annotation_source != "enhanced_manual":
                    print(f"[SAVE] ⚠️ annotation_source设置失败，强制修正")
                    annotation.annotation_source = "enhanced_manual"
                
                print(f"[SAVE] 创建增强标注 - 源: enhanced_manual, 生长级别: {feature_combination.growth_level}")
                print(f"[SAVE] 特征组合详情: 级别={feature_combination.growth_level}, 模式={feature_combination.growth_pattern}")
                
                # 存储增强标注数据
                enhanced_data_dict = enhanced_annotation.to_dict()
                annotation.enhanced_data = enhanced_data_dict
                print(f"[SAVE] 保存增强数据: {len(str(enhanced_data_dict))} 字符")
                print(f"[SAVE] enhanced_data包含: {list(enhanced_data_dict.keys())}")
                
                # 验证enhanced_data是否正确设置
                if hasattr(annotation, 'enhanced_data') and annotation.enhanced_data:
                    print(f"[SAVE] ✓ enhanced_data设置成功")
                    if 'feature_combination' in annotation.enhanced_data:
                        fc_data = annotation.enhanced_data['feature_combination']
                        print(f"[VERIFY] 保存的特征: 级别={fc_data.get('growth_level')}, 模式={fc_data.get('growth_pattern')}")
                    else:
                        print(f"[SAVE] ⚠️ enhanced_data缺少feature_combination字段")
                else:
                    print(f"[SAVE] ❌ enhanced_data设置失败或为空")
                    
            else:
                # 基础标注模式（向后兼容）
                print(f"[SAVE] 使用基础标注模式（无增强面板）")
                from models.panoramic_annotation import PanoramicAnnotation
                annotation = PanoramicAnnotation.from_filename(
                    current_file['filename'],
                    label=self.gui.current_growth_level.get(),
                    bbox=[0, 0, 70, 70],
                    confidence=1.0,
                    microbe_type=self.gui.current_microbe_type.get(),
                    growth_level=self.gui.current_growth_level.get(),
                    interference_factors=[],
                    annotation_source="enhanced_manual",  # 使用enhanced_manual保持一致性
                    is_confirmed=True,
                    panoramic_id=current_file.get('panoramic_id')
                )
            
            # 添加时间戳
            annotation.timestamp = datetime.datetime.now().isoformat()
            
            # 更新image_path为完整路径
            annotation.image_path = current_file['filepath']
            
            # 移除已有标注（如果存在）
            existing_ann = self.gui.current_dataset.get_annotation_by_hole(
                self.gui.current_panoramic_id, 
                self.gui.current_hole_number
            )
            if existing_ann:
                self.gui.current_dataset.annotations.remove(existing_ann)
            
            # 添加新标注
            self.gui.current_dataset.add_annotation(annotation)
            
            # 立即验证保存的标注源
            print(f"[SAVE] 添加标注后验证 - annotation.annotation_source: {annotation.annotation_source}")
            
            # 再次验证保存到数据集的标注
            verification_ann = self.gui.current_dataset.get_annotation_by_hole(
                self.gui.current_panoramic_id, 
                self.gui.current_hole_number
            )
            if verification_ann:
                print(f"[VERIFY] 从数据集验证 - annotation_source: {verification_ann.annotation_source}")
                print(f"[VERIFY] 验证enhanced_data: {bool(hasattr(verification_ann, 'enhanced_data') and verification_ann.enhanced_data)}")
            
            # 记录标注时间
            annotation_key = f"{self.gui.current_panoramic_id}_{self.gui.current_hole_number}"
            current_time = datetime.datetime.now()
            self.gui.last_annotation_time[annotation_key] = current_time
            print(f"[SAVE] 记录标注时间: {annotation_key} -> {current_time.strftime('%m-%d %H:%M:%S')}")
            
            # 更新显示 - 多重强制刷新确保统计和状态更新
            print(f"[SAVE] 开始保存后更新 - 孔位{self.gui.current_hole_number}, 标注源: {annotation.annotation_source}")
            
            # 首先更新全景图
            if hasattr(self.gui, 'load_panoramic_image'):
                self.gui.load_panoramic_image()
            
            # 第1次统计更新（立即）
            if hasattr(self.gui, 'update_statistics'):
                self.gui.update_statistics()
                self.gui.root.update_idletasks()
                self.gui.root.update()
                print("[SAVE] 第1次统计更新完成")
            
            # 第1次状态更新（立即）
            if hasattr(self.gui, 'update_slice_info_display'):
                self.gui.update_slice_info_display()
                self.gui.root.update_idletasks() 
                self.gui.root.update()
                print("[SAVE] 第1次状态更新完成")
            
            # 第2次统计更新（确保）
            if hasattr(self.gui, 'update_statistics'):
                self.gui.update_statistics()
                self.gui.root.update_idletasks()
                print("[SAVE] 第2次统计更新完成")
            
            # 第2次状态更新（确保）
            if hasattr(self.gui, 'update_slice_info_display'):
                self.gui.update_slice_info_display()
                self.gui.root.update_idletasks()
                print("[SAVE] 第2次状态更新完成")
            
            # 最终强制刷新
            self.gui.root.update()
            
            # 验证标注是否正确保存
            saved_ann = self.gui.current_dataset.get_annotation_by_hole(self.gui.current_panoramic_id, self.gui.current_hole_number)
            if saved_ann:
                print(f"[VERIFY] 标注已保存 - 源: {saved_ann.annotation_source}, 级别: {saved_ann.growth_level}")
                print(f"[VERIFY] 是否有enhanced_data: {hasattr(saved_ann, 'enhanced_data')}")
                if hasattr(saved_ann, 'enhanced_data'):
                    print(f"[VERIFY] enhanced_data内容: {bool(saved_ann.enhanced_data)}")
                    if saved_ann.enhanced_data and isinstance(saved_ann.enhanced_data, dict):
                        print(f"[VERIFY] enhanced_data键: {list(saved_ann.enhanced_data.keys())}")
                        if 'feature_combination' in saved_ann.enhanced_data:
                            fc = saved_ann.enhanced_data['feature_combination']
                            print(f"[VERIFY] 保存的特征: 级别={fc.get('growth_level')}, 模式={fc.get('growth_pattern')}")
                    else:
                        print(f"[VERIFY] enhanced_data为空或格式错误: {type(saved_ann.enhanced_data)}")
            else:
                print(f"[VERIFY] 警告 - 标注保存失败")
            
            print("[SAVE] 保存后更新全部完成")
            
            # 重置修改标记
            self.gui.current_annotation_modified = False
            
            return True
            
        except Exception as e:
            raise Exception(f"保存标注失败: {str(e)}")
    
    def auto_save_current_annotation(self):
        """自动保存当前标注（如果已修改且启用自动保存）"""
        if (hasattr(self.gui, 'auto_save_enabled') and 
            self.gui.auto_save_enabled.get() and 
            self.gui.current_annotation_modified):
            try:
                self.save_current_annotation_internal()
                self.gui.update_status("自动保存完成")
            except Exception as e:
                print(f"自动保存失败: {e}")
    
    def clear_current_annotation(self):
        """清除当前标注"""
        existing_ann = self.gui.current_dataset.get_annotation_by_hole(
            self.gui.current_panoramic_id, 
            self.gui.current_hole_number
        )
        if existing_ann:
            self.gui.current_dataset.annotations.remove(existing_ann)
            if hasattr(self.gui, 'load_panoramic_image'):
                self.gui.load_panoramic_image()
            if hasattr(self.gui, 'update_statistics'):
                self.gui.update_statistics()
            self.gui.update_status("已清除当前标注")
        
        # 重置界面状态
        self.gui.current_growth_level.set("negative")
        if hasattr(self.gui, 'interference_factors'):
            for var in self.gui.interference_factors.values():
                var.set(False)
    
    def skip_current(self):
        """跳过当前切片"""
        if hasattr(self.gui, 'navigation_controller'):
            self.gui.navigation_controller.go_next_hole()
        self.gui.update_status("已跳过当前切片")
    
    def batch_annotate_row_negative(self):
        """批量标注整行为阴性"""
        if not self.gui.current_panoramic_id:
            return
        
        row, col = self.gui.hole_manager.number_to_position(self.gui.current_hole_number)
        
        # 获取同行的所有孔位
        row_holes = []
        for c in range(12):
            hole_num = self.gui.hole_manager.position_to_number(row, c)
            row_holes.append(hole_num)
        
        # 批量标注
        self.batch_annotate_holes(row_holes, 'negative')
        
        self.gui.update_status(f"已批量标注第 {row + 1} 行为阴性")
    
    def batch_annotate_col_negative(self):
        """批量标注整列为阴性"""
        if not self.gui.current_panoramic_id:
            return
        
        row, col = self.gui.hole_manager.number_to_position(self.gui.current_hole_number)
        
        # 获取同列的所有孔位
        col_holes = []
        for r in range(10):
            hole_num = self.gui.hole_manager.position_to_number(r, col)
            col_holes.append(hole_num)
        
        # 批量标注
        self.batch_annotate_holes(col_holes, 'negative')
        
        self.gui.update_status(f"已批量标注第 {col + 1} 列为阴性")
    
    def batch_annotate_holes(self, hole_numbers: List[int], growth_level: str):
        """批量标注指定孔位"""
        count = 0
        for hole_number in hole_numbers:
            # 查找对应的切片文件
            for file_info in self.gui.slice_files:
                if (file_info['panoramic_id'] == self.gui.current_panoramic_id and 
                    file_info['hole_number'] == hole_number):
                    
                    # 检查是否已存在标注
                    existing_ann = self.gui.current_dataset.get_annotation_by_hole(
                        self.gui.current_panoramic_id, hole_number
                    )
                    
                    if not existing_ann:  # 只标注未标注的孔位
                        # 创建标注对象
                        from models.panoramic_annotation import PanoramicAnnotation
                        annotation = PanoramicAnnotation.from_filename(
                            file_info['filename'],
                            label=growth_level,
                            bbox=[0, 0, 70, 70],
                            confidence=1.0,
                            microbe_type=self.gui.current_microbe_type.get(),
                            growth_level=growth_level,
                            interference_factors=[],
                            annotation_source="batch_operation",  # 批量操作标记
                            is_confirmed=True,
                            panoramic_id=self.gui.current_panoramic_id
                        )
                        
                        annotation.image_path = file_info['filepath']
                        annotation.timestamp = datetime.datetime.now().isoformat()
                        
                        self.gui.current_dataset.add_annotation(annotation)
                        count += 1
                    break
        
        if count > 0:
            # 更新显示
            if hasattr(self.gui, 'load_panoramic_image'):
                self.gui.load_panoramic_image()
            if hasattr(self.gui, 'update_statistics'):
                self.gui.update_statistics()
            self.gui.update_status(f"批量标注完成，共标注 {count} 个孔位")
    
    def load_config_annotations(self):
        """加载配置文件中的标注数据"""
        if not self.gui.current_panoramic_id or not hasattr(self.gui, 'panoramic_directory'):
            return
        
        try:
            # 检查缓存
            cache_key = self.gui.current_panoramic_id
            if cache_key in self._config_cache:
                config_annotations = self._config_cache[cache_key]
                print(f"使用缓存的配置文件数据: {cache_key}")
            else:
                # 查找全景图文件
                panoramic_file = self.gui.image_service.find_panoramic_image(
                    f"{self.gui.current_panoramic_id}_hole_1.png", 
                    self.gui.panoramic_directory
                )
                
                if not panoramic_file:
                    return
                
                # 查找对应的配置文件
                config_file = self.gui.config_service.find_config_file(panoramic_file)
                if not config_file:
                    return
                
                # 解析配置文件并缓存
                config_annotations = self.gui.config_service.parse_config_file(config_file)
                if not config_annotations:
                    return
                
                # 缓存解析结果
                self._config_cache[cache_key] = config_annotations
                print(f"成功解析并缓存配置文件: {config_file}, 共 {len(config_annotations)} 个标注")
            
            # 导入标注数据
            imported_count = 0
            for hole_number, growth_level in config_annotations.items():
                # 检查是否已存在标注
                existing_ann = self.gui.current_dataset.get_annotation_by_hole(
                    self.gui.current_panoramic_id, hole_number
                )
                
                if not existing_ann:  # 只导入未标注的孔位
                    # 查找对应的切片文件
                    slice_filename = f"{self.gui.current_panoramic_id}_hole_{hole_number}.png"
                    
                    # 创建标注对象 - 配置文件导入，未确认状态
                    from models.panoramic_annotation import PanoramicAnnotation                    
                    annotation = PanoramicAnnotation.from_filename(
                        slice_filename,
                        label=growth_level,
                        bbox=[0, 0, 70, 70],
                        confidence=0.8,  # 配置文件导入的置信度
                        microbe_type=self.gui.current_microbe_type.get(),
                        growth_level=growth_level,
                        interference_factors=[],
                        annotation_source="config_import",
                        is_confirmed=False,
                        panoramic_id=self.gui.current_panoramic_id
                    )
                    
                    # 确保 panoramic_image_id 属性正确设置
                    annotation.panoramic_image_id = self.gui.current_panoramic_id
                    
                    # 查找对应的切片文件完整路径
                    for file_info in self.gui.slice_files:
                        if (file_info['panoramic_id'] == self.gui.current_panoramic_id and 
                            file_info['hole_number'] == hole_number):
                            annotation.image_path = file_info['filepath']
                            break
                    
                    self.gui.current_dataset.add_annotation(annotation)
                    imported_count += 1
            
            if imported_count > 0:
                self.gui.update_status(f"从配置文件导入了 {imported_count} 个标注")
                if hasattr(self.gui, 'update_statistics'):
                    self.gui.update_statistics()
            
        except Exception as e:
            print(f"加载配置文件标注失败: {e}")
    
    def get_annotation_status_text(self):
        """获取标注状态文本，包含日期时间 - 只有增强标注才算已标注"""
        existing_ann = self.gui.current_dataset.get_annotation_by_hole(
            self.gui.current_panoramic_id, 
            self.gui.current_hole_number
        )
        
        if existing_ann:
            # 检查是否为增强标注
            has_enhanced = (hasattr(existing_ann, 'enhanced_data') and 
                          existing_ann.enhanced_data and 
                          existing_ann.annotation_source == 'enhanced_manual')
            
            if has_enhanced:
                # 增强标注 - 显示已标注状态
                annotation_key = f"{self.gui.current_panoramic_id}_{self.gui.current_hole_number}"
                if annotation_key in self.gui.last_annotation_time:
                    datetime_str = self.gui.last_annotation_time[annotation_key].strftime("%m-%d %H:%M:%S")
                    return f"状态: 已标注 ({datetime_str}) - {existing_ann.growth_level}"
                else:
                    # 尝试从标注对象获取时间戳
                    if hasattr(existing_ann, 'timestamp') and existing_ann.timestamp:
                        try:
                            if isinstance(existing_ann.timestamp, str):
                                dt = datetime.datetime.fromisoformat(existing_ann.timestamp.replace('Z', '+00:00'))
                            else:
                                dt = existing_ann.timestamp
                            datetime_str = dt.strftime("%m-%d %H:%M:%S")
                            return f"状态: 已标注 ({datetime_str}) - {existing_ann.growth_level}"
                        except:
                            pass
                    return f"状态: 已标注 - {existing_ann.growth_level}"
            else:
                # 配置导入或其他类型 - 显示为配置导入状态
                return f"状态: 配置导入 - {existing_ann.growth_level}"
        else:
            return "状态: 未标注"