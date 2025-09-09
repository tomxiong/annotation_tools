"""
文件管理器模块

负责文件操作、导入导出功能
"""

from typing import Optional, Dict, Any, List, TYPE_CHECKING
import logging
import json
from tkinter import filedialog, messagebox

if TYPE_CHECKING:
    from .main_controller import MainController

logger = logging.getLogger(__name__)


class FileManager:
    """文件管理器 - 负责文件操作"""

    def __init__(self, controller: 'MainController'):
        self.controller = controller

    def initialize(self):
        """初始化文件管理器"""
        logger.info("FileManager initialized")

    def select_panoramic_directory(self):
        """选择全景图目录"""
        directory = filedialog.askdirectory(title="选择全景图目录")
        if directory:
            self.controller.panoramic_dir_var.set(directory)
            self.controller.panoramic_directory = directory
            self.controller._load_data()
            self.controller.update_status(f"已选择全景图目录: {directory}")

    def load_annotations(self):
        """加载标注文件"""
        logger.info("开始加载标注文件...")

        # 记录加载标注文件的关键操作
        import time
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        current_geometry = self.controller.root.geometry()
        logger.debug(f"{timestamp} - 开始加载标注, 当前窗口: {current_geometry}")

        # 记录到日志
        log_entry = {
            'timestamp': timestamp,
            'geometry': current_geometry,
            'event': 'load_annotations_start'
        }
        self.controller.window_resize_log.append(log_entry)

        # 选择标注文件
        file_path = filedialog.askopenfilename(
            title="选择标注文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if not file_path:
            return

        try:
            # 加载标注数据
            loaded_dataset = self.controller.current_dataset.__class__.load_from_json(file_path)

            # 合并到当前数据集
            merge_count = 0
            for annotation in loaded_dataset.annotations:
                # 检查是否已存在相同标注
                existing_ann = self.controller.current_dataset.get_annotation_by_hole(
                    annotation.panoramic_image_id,
                    annotation.hole_number
                )
                if existing_ann:
                    self.controller.current_dataset.annotations.remove(existing_ann)

                # 添加加载的标注
                self.controller.current_dataset.add_annotation(annotation)
                merge_count += 1

            # 获取最后标注的信息，用于自动切换
            latest_annotation = loaded_dataset.get_latest_annotation()
            auto_switch_info = ""

            if latest_annotation:
                # 记录自动切换信息
                auto_switch_info = f" - 自动切换到 {latest_annotation.panoramic_image_id}_{latest_annotation.hole_number}"
                logger.debug(f"检测到最后标注: {latest_annotation.panoramic_image_id}_{latest_annotation.hole_number}")

                # 切换到对应的全景图
                if latest_annotation.panoramic_image_id in self.controller.panoramic_ids:
                    logger.debug(f"切换到全景图: {latest_annotation.panoramic_image_id}")
                    success = self.controller.navigation_manager._switch_to_panoramic(latest_annotation.panoramic_image_id)

                    if success:
                        # 延迟切换到对应的孔位，确保全景图加载完成
                        self.controller.root.after(100, lambda: self.controller.navigation_manager._switch_to_hole(latest_annotation.hole_number))
                    else:
                        auto_switch_info = f" - 切换全景图失败"
                else:
                    logger.debug(f"警告: 全景图 {latest_annotation.panoramic_image_id} 不在可用列表中")
                    auto_switch_info = f" - 全景图 {latest_annotation.panoramic_image_id} 不可用"
            else:
                logger.debug(f"没有找到标注信息，保持当前视图")

            # 更新显示
            self.controller._load_panoramic_image()
            self.controller._update_statistics()

            # 重新加载当前切片的标注并完整刷新当前孔状态
            self.controller._load_existing_annotation()

            # 强制刷新切片信息显示和增强标注面板
            self.controller._update_slice_info_display()

            # 确保时间戳正确同步到内存 - 修复加载时时间戳显示问题
            self.controller._force_timestamp_sync_after_load()

            # 延迟验证刷新 - 确保时间戳同步后再进行最终验证
            self.controller.root.after(50, self.controller._verify_timestamp_sync_after_load)

            # 确保增强标注面板状态同步 - 强制完整刷新
            if self.controller.annotation_panel:
                current_ann = self.controller.current_dataset.get_annotation_by_hole(
                    self.controller.current_panoramic_id,
                    self.controller.current_hole_number
                )
                if current_ann:
                    logger.debug(f"加载标注后强制刷新增强面板 - 孔位{self.controller.current_hole_number}")

                    # 先重置面板再重新设置，确保完全刷新
                    self.controller.annotation_panel.reset_annotation()
                    self.controller.root.update_idletasks()

                    # 重新触发完整的标注加载流程
                    self.controller._load_existing_annotation()
                    self.controller.root.update_idletasks()

                    # 最后一次强制UI刷新确保增强面板完全同步
                    self.controller.root.update()

                    logger.debug(f"增强面板强制刷新完成 - 孔位{self.controller.current_hole_number}")
                else:
                    logger.debug(f"当前孔位{self.controller.current_hole_number}无标注，重置增强面板")
                    self.controller.annotation_panel.reset_annotation()

            # 多重UI刷新确保状态完全更新
            self.controller.root.update_idletasks()
            self.controller.root.update()

            # 延迟验证刷新 - 确保所有异步更新完成
            self.controller.root.after(100, self.controller._verify_load_refresh)

            logger.debug(f"加载标注完成，当前孔位状态已刷新")

            messagebox.showinfo("成功", f"已加载 {merge_count} 个标注进行review")
            self.controller.update_status(f"已加载标注文件: {file_path} ({merge_count} 个标注)")

            # 记录标注加载完成的关键操作
            logger.info(f"标注文件加载完成: {file_path}，共 {merge_count} 个标注")

            # 记录加载标注后的窗口状态
            import time
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            final_geometry = self.controller.root.geometry()
            logger.debug(f"{timestamp} - 完成加载标注, 当前窗口: {final_geometry}")

            # 记录到日志
            log_entry = {
                'timestamp': timestamp,
                'geometry': final_geometry,
                'event': 'load_annotations_complete',
                'annotation_count': merge_count
            }
            self.controller.window_resize_log.append(log_entry)

        except Exception as e:
            messagebox.showerror("错误", f"加载标注文件失败: {str(e)}")

    def save_annotations(self):
        """保存标注"""
        if not self.controller.current_dataset or not self.controller.current_dataset.annotations:
            messagebox.showwarning("警告", "没有标注数据需要保存")
            return

        file_path = filedialog.asksaveasfilename(
            title="保存标注",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )

        if file_path:
            try:
                # 保存数据集
                self.controller.current_dataset.save_to_json(file_path)

                # 重置修改标记
                self.controller.is_modified = False

                # 更新最后保存时间
                import datetime
                current_time = datetime.datetime.now()
                annotation_key = f"{self.controller.current_panoramic_id}_{self.controller.current_hole_number}"
                self.controller.last_annotation_time[annotation_key] = current_time

                # 刷新显示
                self.controller._update_slice_info_display()

                messagebox.showinfo("成功", f"标注文件已保存: {file_path}")
                self.controller.update_status(f"已保存标注文件: {file_path}")

            except Exception as e:
                messagebox.showerror("错误", f"保存标注文件失败: {str(e)}")

    def import_model_suggestions(self):
        """导入模型预测结果"""
        try:
            file_path = filedialog.askopenfilename(
                title="选择模型预测结果文件",
                filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
            )

            if not file_path:
                return

            # 使用模型建议服务加载文件
            suggestions_map, warnings = self.controller.model_suggestion_service.load_from_json(file_path)

            if suggestions_map:
                self.controller.current_suggestions_map = suggestions_map
                self.controller.model_suggestion_loaded = True

                # 设置到hole_manager
                self.controller.hole_manager.set_suggestions_map(suggestions_map, self.controller.current_panoramic_id)

                # 更新当前显示
                self.controller._update_hole_suggestion_display()

                # 计算有建议的孔位数量
                suggestion_count = 0
                for hole_num in range(1, 121):
                    if suggestions_map.get_suggestion(self.controller.current_panoramic_id, hole_num):
                        suggestion_count += 1

                # 构建成功消息，包含警告信息（如果有的话）
                success_message = f"已成功导入模型建议，共 {suggestion_count} 条记录"
                if warnings:
                    warning_msg = "\n".join(warnings)
                    success_message += f"\n\n警告信息：\n{warning_msg}"

                messagebox.showinfo("成功", success_message)
                # 保留关键的用户提示信息
                logger.info(f"导入模型建议成功: {file_path}")
            else:
                messagebox.showerror("错误", "导入模型建议失败，请检查文件格式")

        except Exception as e:
            messagebox.showerror("错误", f"导入模型建议时发生错误: {str(e)}")
            logger.error(f"导入模型建议失败: {str(e)}")

    def export_training_data(self):
        """导出训练数据"""
        output_dir = filedialog.askdirectory(title="选择导出目录")
        if output_dir:
            try:
                # 分别导出细菌和真菌数据
                bacteria_summary = self.controller.current_dataset.export_for_training(output_dir, 'bacteria')
                fungi_summary = self.controller.current_dataset.export_for_training(output_dir, 'fungi')

                # 显示导出摘要
                summary_text = f"导出完成!\n\n细菌数据: {bacteria_summary['total_exported']} 个样本\n"
                summary_text += f"真菌数据: {fungi_summary['total_exported']} 个样本\n\n"
                summary_text += f"导出目录: {output_dir}"

                messagebox.showinfo("导出完成", summary_text)
                self.controller.update_status(f"已导出训练数据到: {output_dir}")

            except Exception as e:
                messagebox.showerror("错误", f"导出训练数据失败: {str(e)}")

    def export_annotations(self):
        """导出标注"""
        if not self.controller.annotation_panel:
            return

        try:
            annotations = self.controller.annotation_panel.get_all_annotations()

            if not annotations:
                messagebox.showinfo("提示", "没有标注数据可导出")
                return

            # 选择导出位置
            file_path = filedialog.asksaveasfilename(
                title="导出标注",
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv"), ("所有文件", "*.*")],
                initialdir=self._get_last_directory()
            )

            if file_path:
                if file_path.endswith('.csv'):
                    self._export_annotations_csv(annotations, file_path)
                else:
                    self._export_annotations_json(annotations, file_path)

                self._update_last_directory(file_path)
                messagebox.showinfo("成功", "标注已导出")

        except Exception as e:
            messagebox.showerror("错误", f"导出标注时出错: {str(e)}")

    def _export_annotations_json(self, annotations: Dict[str, Any], file_path: str):
        """导出为JSON格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(annotations, f, indent=2, ensure_ascii=False)

    def _export_annotations_csv(self, annotations: Dict[str, Any], file_path: str):
        """导出为CSV格式"""
        import csv

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 写入标题
            writer.writerow(['孔位', '行', '列', '生长级别', '微生物类型', '备注'])

            # 写入数据
            for hole_id, annotation in annotations.items():
                row = int(hole_id[:2])
                col = int(hole_id[2:4])
                row_letter = chr(ord('A') + row)
                col_number = col + 1

                writer.writerow([
                    f"{row_letter}{col_number}",
                    row_letter,
                    col_number,
                    annotation.get('growth_level', ''),
                    annotation.get('microbe_type', ''),
                    annotation.get('notes', '')
                ])

    def _get_last_directory(self) -> str:
        """获取最后使用的目录"""
        if self.controller.ui_state_manager:
            state = self.controller.ui_state_manager.get_state()
            return state.last_open_directory or ""
        return ""

    def _update_last_directory(self, file_path: str):
        """更新最后使用的目录"""
        import os
        directory = os.path.dirname(file_path)
        if self.controller.ui_state_manager:
            self.controller.ui_state_manager.update_state(last_open_directory=directory)