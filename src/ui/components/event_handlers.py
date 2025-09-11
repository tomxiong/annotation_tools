"""
事件处理模块
负责处理所有用户交互事件和系统事件
从原panoramic_annotation_gui.py中拆分出来
"""

import tkinter as tk
from typing import Optional, Any


class EventHandlers:
    """事件处理管理类"""
    
    def __init__(self, parent_gui):
        """
        初始化事件处理管理器
        
        Args:
            parent_gui: 主GUI实例，用于访问必要的属性和方法
        """
        self.gui = parent_gui
        self.root = parent_gui.root
        
    # === 事件处理方法 ===

        def toggle_annotation_mode(self):
            """切换标注模式"""
            # 清除当前显示的面板
            for widget in self.annotation_content_frame.winfo_children():
                widget.pack_forget()

            if self.use_enhanced_annotation.get():
                # 显示增强标注面板
                self.enhanced_annotation_frame.pack(fill=tk.BOTH, expand=True)
            else:
                # 显示基础标注面板
                self.basic_annotation_frame.pack(fill=tk.BOTH, expand=True)


        def on_enhanced_annotation_change(self, annotation_data=None):
            """增强标注变化回调"""
            # 标记当前标注已修改
            self.current_annotation_modified = True

            # 更新详细标注信息显示
            detailed_info = self.get_detailed_annotation_info()
            self.detailed_annotation_label.config(text=detailed_info)

            # 可以在这里添加实时预览或验证逻辑
            pass


        def _on_view_mode_changed(self):
            """视图模式变更事件处理"""
            try:
                # 获取当前选择的视图模式
                mode_value = self.view_mode_var.get()
                old_mode = self.current_view_mode
                self.current_view_mode = ViewMode(mode_value)

                log_debug(f"[VIEW_MODE] 视图模式从 {old_mode.value} 切换到 {self.current_view_mode.value}")
                log_debug(f"[VIEW_MODE] 当前全景ID: {getattr(self, 'current_panoramic_id', 'None')}")
                log_debug(f"[VIEW_MODE] 当前孔号: {getattr(self, 'current_hole_number', 'None')}")

                # 检查hole_manager是否存在模型建议数据
                if hasattr(self, 'hole_manager') and self.hole_manager:
                    # 获取建议摘要信息
                    suggestions_summary = self.hole_manager.get_suggestions_summary()
                    suggestions_count = suggestions_summary['total']
                    log_debug(f"[VIEW_MODE] 模型建议数据总数: {suggestions_count}")

                    # 检查当前切片是否有模型建议
                    if hasattr(self, 'current_panoramic_id') and hasattr(self, 'current_hole_number'):
                        if self.current_panoramic_id and self.current_hole_number:
                            slice_key = f"{self.current_panoramic_id}_{self.current_hole_number}"
                            has_suggestion = self.hole_manager.has_hole_suggestion(self.current_hole_number)
                            log_debug(f"[VIEW_MODE] 当前切片键: {slice_key}, 是否有模型建议: {has_suggestion}")

                            if has_suggestion:
                                suggestion = self.hole_manager.get_hole_suggestion(self.current_hole_number)
                                if suggestion:
                                    # 显示完整的模型建议信息
                                    growth_pattern_str = ", ".join(suggestion.growth_pattern) if suggestion.growth_pattern else "无"
                                    interference_factors_str = ", ".join(suggestion.interference_factors) if suggestion.interference_factors else "无"
                                    log_debug(f"[VIEW_MODE] 模型建议详情: growth_level={suggestion.growth_level}, confidence={suggestion.model_confidence}, growth_pattern=[{growth_pattern_str}], interference_factors=[{interference_factors_str}]")
                                else:
                                    log_debug(f"[VIEW_MODE] 获取模型建议详情失败")
                            else:
                                log_debug(f"[VIEW_MODE] 当前切片无模型建议数据")

                # 视图模式切换后，数据会通过load_current_slice重新加载，无需额外处理

                # 调用所有注册的回调函数
                callback_count = len(self.view_change_callbacks)
                log_debug(f"[VIEW_MODE] 注册的回调函数数量: {callback_count}")

                for i, callback in enumerate(self.view_change_callbacks):
                    try:
                        log_debug(f"[VIEW_MODE] 执行回调函数 {i+1}/{callback_count}")
                        # 传递完整的参数：view_mode, hole_manager, slice_index
                        callback(self.current_view_mode, self.hole_manager, self.current_hole_number)
                        log_debug(f"[VIEW_MODE] 回调函数 {i+1} 执行成功")
                    except Exception as e:
                        log_error(f"[VIEW_MODE] 回调函数 {i+1} 执行失败: {e}")

                # 更新状态显示
                mode_names = {
                    ViewMode.MANUAL: "人工视图",
                    ViewMode.MODEL: "模型视图"
                }
                mode_name = mode_names.get(self.current_view_mode, "未知视图")
                self.update_status(f"已切换到{mode_name}")

                # 重新加载当前切片以应用新的视图模式
                if hasattr(self, 'current_panoramic_id') and hasattr(self, 'current_hole_number'):
                    if self.current_panoramic_id and self.current_hole_number:
                        log_debug(f"[VIEW_MODE] 开始重新加载切片")
                        self.load_current_slice()
                        log_debug(f"[VIEW_MODE] 切片重新加载完成")
                    else:
                        log_debug(f"[VIEW_MODE] 当前无有效的全景ID或孔号，跳过切片重新加载")
                else:
                    log_debug(f"[VIEW_MODE] 缺少current_panoramic_id或current_hole_number属性")

            except Exception as e:
                log_error(f"[VIEW_MODE] 视图模式变更失败: {e}")
                messagebox.showerror("错误", f"视图模式变更失败: {str(e)}")

    def setup_bindings(self):
        """设置键盘快捷键和窗口事件"""
        # 窗口尺寸变化事件
        self.root.bind('<Configure>', self.on_window_resize)

        # 只在非输入控件获得焦点时响应快捷键
        # 方向导航快捷键
        self.root.bind('<Key-1>', self.on_key_1)
        self.root.bind('<Key-2>', self.on_key_2)
        self.root.bind('<Key-3>', self.on_key_3)
        self.root.bind('<Left>', self.on_key_left)
        self.root.bind('<Right>', self.on_key_right)
        self.root.bind('<Up>', self.on_key_up)
        self.root.bind('<Down>', self.on_key_down)

        # 序列导航快捷键（Home/End 对应 首个/最后）
        self.root.bind('<Home>', self.on_key_home)
        self.root.bind('<End>', self.on_key_end)

        # 全景图导航快捷键（PageUp/Down 对应 上一全景/下一全景）
        self.root.bind('<Prior>', self.on_key_page_up)  # PageUp
        self.root.bind('<Next>', self.on_key_page_down)  # PageDown

        # 窗口分析快捷键
        self.root.bind('<Control-l>', lambda e: self.analyze_window_resize_log())  # Ctrl+L 分析日志

        # 版本信息快捷键
        self.root.bind('<F1>', lambda e: self.show_about_dialog())  # F1 显示操作指南

        # 其他快捷键
        self.root.bind('<space>', self.on_key_space)
        self.root.bind('<Return>', self.on_key_return)

        # 设置焦点以接收键盘事件
        self.root.focus_set()

    def on_growth_level_change(self):
        """生长级别改变时的处理"""
        # 可以在这里添加自动保存逻辑或其他处理
        pass


    def on_panoramic_click(self, event):
        """全景图点击事件处理 - 优化的孔位定位算法"""
        if not self.panoramic_image:
            return

        try:
            # 获取画布尺寸
            canvas_width = self.panoramic_canvas.winfo_width()
            canvas_height = self.panoramic_canvas.winfo_height()

            # 计算显示图像的实际尺寸（保持宽高比）
            original_width = self.panoramic_image.width
            original_height = self.panoramic_image.height

            # 计算缩放比例（保持宽高比，适应画布）
            scale_w = (canvas_width - 20) / original_width
            scale_h = (canvas_height - 20) / original_height
            scale_factor = min(scale_w, scale_h)

            # 计算显示尺寸
            display_width = int(original_width * scale_factor)
            display_height = int(original_height * scale_factor)

            # 计算图像在画布中的偏移（居中显示）
            offset_x = (canvas_width - display_width) // 2
            offset_y = (canvas_height - display_height) // 2

            # 使用优化后的孔位查找方法
            hole_number = self.hole_manager.find_hole_by_coordinates(
                event.x, event.y, scale_factor, offset_x, offset_y
            )

            if hole_number:
                # 检查孔位是否可用于标注
                if self.hole_manager.is_hole_available_for_annotation(hole_number):
                    self.navigate_to_hole(hole_number)
                    self.update_status(f"点击定位到孔位 {hole_number}")
                else:
                    self.update_status(f"孔位 {hole_number} 在起始孔位({self.hole_manager.start_hole_number})之前，已忽略")
            else:
                self.update_status("点击位置未找到有效孔位")

        except Exception as e:
            log_error(f"孔位点击处理失败: {e}", "PANORAMIC_CLICK")
            self.update_status("孔位定位失败")

    # 暂时移除批量标注功能
    # def batch_annotate_row_negative(self):
    #     """批量标注整行为阴性"""
    #     if not self.current_panoramic_id:
    #         return
    #     
    #     row, col = self.hole_manager.number_to_position(self.current_hole_number)
    #     
    #     # 获取同行的所有孔位
    #     row_holes = []
    #     for c in range(12):
    #         hole_num = self.hole_manager.position_to_number(row, c)
    #         row_holes.append(hole_num)
    #     
    #     # 批量标注
    #     self.batch_annotate_holes(row_holes, 'negative')
    #     
    #     self.update_status(f"已批量标注第 {row + 1} 行为阴性")
    # 
    # def batch_annotate_col_negative(self):
    #     """批量标注整列为阴性"""
    #     if not self.current_panoramic_id:
    #         return
    #     
    #     row, col = self.hole_manager.number_to_position(self.current_hole_number)
    #     
    #     # 获取同列的所有孔位
    #     col_holes = []
    #     for r in range(10):
    #         hole_num = self.hole_manager.position_to_number(r, col)
    #         col_holes.append(hole_num)
    #     
    #     # 批量标注
    #     self.batch_annotate_holes(col_holes, 'negative')
    #     
    #     self.update_status(f"已批量标注第 {col + 1} 列为阴性")

    # 暂时移除批量标注功能
    # def batch_annotate_holes(self, hole_numbers: List[int], growth_level: str):
    #     """批量标注指定孔位"""
    #     count = 0
    #     for hole_number in hole_numbers:
    #         # 查找对应的切片文件
    #         for file_info in self.slice_files:
    #             if (file_info['panoramic_id'] == self.current_panoramic_id and 
    #                 file_info['hole_number'] == hole_number):
    #                 
    #                 # 创建标注 - 批量操作，已确认状态
    #                 annotation = PanoramicAnnotation.from_filename(
    #                     file_info['filename'],
    #                     label=growth_level,
    #                     bbox=[0, 0, 70, 70],
    #                     confidence=1.0,
    #                     microbe_type=self.current_microbe_type.get(),
    #                     growth_level=growth_level,
    #                     interference_factors=[],
    #                     annotation_source="batch_operation",
    #                     is_confirmed=True,
    #                     panoramic_id=file_info.get('panoramic_id')
    #                 )
    #                 
    #                 # 设置完整文件路径
    #                 annotation.image_path = file_info['filepath']
    #                 
    #                 # 移除已有标注
    #                 existing_ann = self.current_dataset.get_annotation_by_hole(
    #                     self.current_panoramic_id, hole_number
    #                 )
    #                 if existing_ann:
    #                     self.current_dataset.annotations.remove(existing_ann)
    #                 
    #                 # 添加新标注
    #                 self.current_dataset.add_annotation(annotation)
    #                 count += 1
    #                 break
    #     
    #     # 更新显示
    #     self.load_panoramic_image()
    #     self.update_statistics()
    #     
    #     return count


    def toggle_debug_logging(self):
        """切换调试日志开关"""
        try:
            from src.utils.logger import toggle_debug_logging, is_debug_logging_enabled

            # 切换调试日志状态
            toggle_debug_logging()

            # 更新复选框状态以反映实际状态
            current_state = is_debug_logging_enabled()
            self.debug_logging_enabled.set(current_state)

            # 更新状态栏显示
            status_text = "调试日志已开启" if current_state else "调试日志已关闭"
            self.update_status(status_text)

            # 记录操作日志
            log_info(f"调试日志开关已切换: {'开启' if current_state else '关闭'}", "DEBUG_TOGGLE")

        except Exception as e:
            log_error(f"切换调试日志失败: {str(e)}", "DEBUG_TOGGLE")
            self.update_status(f"切换调试日志失败: {str(e)}")


    def on_panoramic_selected(self, event=None):
        """处理全景图选择事件"""
        selected_panoramic_id = self.panoramic_id_var.get()
        if selected_panoramic_id and selected_panoramic_id != self.current_panoramic_id:
            self.go_to_panoramic(selected_panoramic_id)


    def on_view_mode_changed(self, view_mode):
        """处理视图模式变更事件"""
        try:
            # 保留关键的用户提示信息
            log_info(f"视图模式切换到: {view_mode}", "VIEW_MODE")

            # 更新建议显示
            self.update_hole_suggestion_display()

        except Exception as e:
            log_error(f"处理视图模式变更失败: {str(e)}", "VIEW_MODE")

    def on_window_resize(self, event):
        """窗口大小变化事件处理"""
        try:
            if event.widget == self.root:
                # 记录窗口大小变化
                geometry = self.root.geometry()
                self.gui.log_debug(f"窗口大小变化: {geometry}", "EVENT")
        except Exception as e:
            self.gui.log_error(f"窗口大小变化处理失败: {e}", "EVENT")

    def on_key_1(self, event):
        """按键1事件处理"""
        try:
            self.gui.log_info("按键1被按下", "EVENT")
            # TODO: 实现按键1的具体功能
        except Exception as e:
            self.gui.log_error(f"按键1处理失败: {e}", "EVENT")

    def on_key_2(self, event):
        """按键2事件处理"""
        try:
            self.gui.log_info("按键2被按下", "EVENT")
            # TODO: 实现按键2的具体功能
        except Exception as e:
            self.gui.log_error(f"按键2处理失败: {e}", "EVENT")

    def on_key_3(self, event):
        """按键3事件处理"""
        try:
            self.gui.log_info("按键3被按下", "EVENT")
            # TODO: 实现按键3的具体功能
        except Exception as e:
            self.gui.log_error(f"按键3处理失败: {e}", "EVENT")

    def on_key_left(self, event):
        """左箭头键事件处理"""
        try:
            self.gui.log_info("左箭头键被按下", "EVENT")
            # TODO: 实现向左导航功能
        except Exception as e:
            self.gui.log_error(f"左箭头键处理失败: {e}", "EVENT")

    def on_key_right(self, event):
        """右箭头键事件处理"""
        try:
            self.gui.log_info("右箭头键被按下", "EVENT")
            # TODO: 实现向右导航功能
        except Exception as e:
            self.gui.log_error(f"右箭头键处理失败: {e}", "EVENT")

    def on_key_up(self, event):
        """上箭头键事件处理"""
        try:
            self.gui.log_info("上箭头键被按下", "EVENT")
            # TODO: 实现向上导航功能
        except Exception as e:
            self.gui.log_error(f"上箭头键处理失败: {e}", "EVENT")

    def on_key_down(self, event):
        """下箭头键事件处理"""
        try:
            self.gui.log_info("下箭头键被按下", "EVENT")
            # TODO: 实现向下导航功能
        except Exception as e:
            self.gui.log_error(f"下箭头键处理失败: {e}", "EVENT")

