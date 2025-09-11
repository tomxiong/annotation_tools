"""
导航控制模块
负责切片导航、孔位跳转、序列控制等导航相关的核心业务逻辑
"""

import tkinter as tk
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

# 日志导入
try:
    from src.utils.logger import log_debug, log_info, log_warning, log_error
except ImportError:
    def log_debug(msg, category=""): print(f"[DEBUG] {msg}")
    def log_info(msg, category=""): print(f"[INFO] {msg}")
    def log_warning(msg, category=""): print(f"[WARNING] {msg}")
    def log_error(msg, category=""): print(f"[ERROR] {msg}")

class NavigationDirection(Enum):
    """导航方向枚举"""
    NEXT = "next"
    PREVIOUS = "previous"
    FIRST = "first"
    LAST = "last"
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

class NavigationController:
    """导航控制器 - 负责所有导航相关的操作"""
    
    def __init__(self, gui_instance):
        """
        初始化导航控制器
        
        Args:
            gui_instance: 主GUI实例，用于访问其他组件
        """
        self.gui = gui_instance
        
        # 导航状态
        self.current_slice_index = 0
        self.current_panoramic_id = None
        self.current_hole_number = None
        
        # 导航历史
        self.navigation_history = []
        self.history_index = -1
        self.max_history_size = 100
        
        # 导航设置
        self.auto_save_on_navigate = True
        self.skip_annotated = False
        self.navigation_mode = "sequential"  # sequential, grid, smart
        
        log_debug("导航控制器初始化完成", "NAVIGATION_CONTROLLER")
    
    def navigate_to_hole(self, hole_number: int) -> bool:
        """
        导航到指定孔位
        
        Args:
            hole_number: 目标孔位编号
            
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                log_warning("没有可用的切片文件", "NAVIGATION_CONTROLLER")
                return False
            
            # 查找目标孔位的切片索引
            target_index = self._find_slice_index_by_hole(hole_number)
            if target_index is None:
                log_warning(f"未找到孔位 {hole_number} 的切片", "NAVIGATION_CONTROLLER")
                return False
            
            # 保存当前状态到历史
            self._add_to_history()
            
            # 执行导航
            success = self._navigate_to_index(target_index)
            
            if success:
                log_debug(f"成功导航到孔位 {hole_number} (索引: {target_index})", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"导航到孔位 {hole_number} 失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def navigate_next(self, skip_annotated: bool = None) -> bool:
        """
        导航到下一个切片
        
        Args:
            skip_annotated: 是否跳过已标注的切片，None表示使用默认设置
            
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                return False
            
            skip = skip_annotated if skip_annotated is not None else self.skip_annotated
            target_index = self._find_next_valid_index(skip)
            
            if target_index is None:
                log_debug("已经是最后一个切片", "NAVIGATION_CONTROLLER")
                return False
            
            # 保存当前状态到历史
            self._add_to_history()
            
            # 执行导航
            success = self._navigate_to_index(target_index)
            
            if success:
                log_debug(f"导航到下一个切片 (索引: {target_index})", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"导航到下一个切片失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def navigate_previous(self, skip_annotated: bool = None) -> bool:
        """
        导航到上一个切片
        
        Args:
            skip_annotated: 是否跳过已标注的切片，None表示使用默认设置
            
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                return False
            
            skip = skip_annotated if skip_annotated is not None else self.skip_annotated
            target_index = self._find_previous_valid_index(skip)
            
            if target_index is None:
                log_debug("已经是第一个切片", "NAVIGATION_CONTROLLER")
                return False
            
            # 保存当前状态到历史
            self._add_to_history()
            
            # 执行导航
            success = self._navigate_to_index(target_index)
            
            if success:
                log_debug(f"导航到上一个切片 (索引: {target_index})", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"导航到上一个切片失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def navigate_first(self) -> bool:
        """
        导航到第一个切片
        
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                return False
            
            # 找到第一个有效切片
            target_index = self._find_first_valid_index()
            
            if target_index is None:
                log_warning("没有找到有效的第一个切片", "NAVIGATION_CONTROLLER")
                return False
            
            # 保存当前状态到历史
            self._add_to_history()
            
            # 执行导航
            success = self._navigate_to_index(target_index)
            
            if success:
                log_debug(f"导航到第一个切片 (索引: {target_index})", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"导航到第一个切片失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def navigate_last(self) -> bool:
        """
        导航到最后一个切片
        
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                return False
            
            # 找到最后一个有效切片
            target_index = self._find_last_valid_index()
            
            if target_index is None:
                log_warning("没有找到有效的最后一个切片", "NAVIGATION_CONTROLLER")
                return False
            
            # 保存当前状态到历史
            self._add_to_history()
            
            # 执行导航
            success = self._navigate_to_index(target_index)
            
            if success:
                log_debug(f"导航到最后一个切片 (索引: {target_index})", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"导航到最后一个切片失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def navigate_by_direction(self, direction: NavigationDirection) -> bool:
        """
        按方向导航（网格模式）
        
        Args:
            direction: 导航方向
            
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'hole_manager') or not self.gui.hole_manager:
                log_warning("孔位管理器不可用", "NAVIGATION_CONTROLLER")
                return False
            
            current_hole = getattr(self.gui, 'current_hole_number', None)
            if current_hole is None:
                log_warning("当前孔位编号不可用", "NAVIGATION_CONTROLLER")
                return False
            
            # 获取目标孔位
            target_hole = self._get_target_hole_by_direction(current_hole, direction)
            
            if target_hole is None:
                log_debug(f"无法在方向 {direction.value} 找到有效孔位", "NAVIGATION_CONTROLLER")
                return False
            
            # 导航到目标孔位
            return self.navigate_to_hole(target_hole)
            
        except Exception as e:
            log_error(f"按方向 {direction.value} 导航失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def navigate_to_panoramic(self, panoramic_id: str, hole_number: int = None) -> bool:
        """
        导航到指定全景图
        
        Args:
            panoramic_id: 全景图ID
            hole_number: 可选的孔位编号，如果未指定则导航到第一个孔位
            
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                return False
            
            # 查找全景图的第一个切片
            target_index = None
            target_hole = hole_number
            
            for i, slice_file in enumerate(self.gui.slice_files):
                if slice_file.get('panoramic_id') == panoramic_id:
                    if target_hole is None or slice_file.get('hole_number') == target_hole:
                        target_index = i
                        break
                    elif target_hole is None:
                        target_index = i  # 使用找到的第一个
            
            if target_index is None:
                log_warning(f"未找到全景图 {panoramic_id} 的切片", "NAVIGATION_CONTROLLER")
                return False
            
            # 保存当前状态到历史
            self._add_to_history()
            
            # 执行导航
            success = self._navigate_to_index(target_index)
            
            if success:
                log_debug(f"成功导航到全景图 {panoramic_id} 的孔位 {target_hole}", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"导航到全景图 {panoramic_id} 失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def go_back(self) -> bool:
        """
        返回上一个导航位置
        
        Returns:
            如果成功返回返回True，否则返回False
        """
        try:
            if self.history_index <= 0:
                log_debug("没有更多的导航历史", "NAVIGATION_CONTROLLER")
                return False
            
            self.history_index -= 1
            history_item = self.navigation_history[self.history_index]
            
            # 恢复到历史位置
            success = self._navigate_to_index(history_item['slice_index'], add_to_history=False)
            
            if success:
                log_debug(f"返回到历史位置: 索引 {history_item['slice_index']}", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"返回导航历史失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def go_forward(self) -> bool:
        """
        前进到下一个导航位置
        
        Returns:
            如果成功前进返回True，否则返回False
        """
        try:
            if self.history_index >= len(self.navigation_history) - 1:
                log_debug("没有更多的前进历史", "NAVIGATION_CONTROLLER")
                return False
            
            self.history_index += 1
            history_item = self.navigation_history[self.history_index]
            
            # 前进到历史位置
            success = self._navigate_to_index(history_item['slice_index'], add_to_history=False)
            
            if success:
                log_debug(f"前进到历史位置: 索引 {history_item['slice_index']}", "NAVIGATION_CONTROLLER")
            
            return success
            
        except Exception as e:
            log_error(f"前进导航历史失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def get_navigation_info(self) -> Dict[str, Any]:
        """
        获取当前导航信息
        
        Returns:
            导航信息字典
        """
        try:
            total_slices = len(self.gui.slice_files) if hasattr(self.gui, 'slice_files') and self.gui.slice_files else 0
            
            info = {
                'current_slice_index': self.current_slice_index,
                'total_slices': total_slices,
                'current_panoramic_id': self.current_panoramic_id,
                'current_hole_number': self.current_hole_number,
                'can_go_previous': self.current_slice_index > 0,
                'can_go_next': self.current_slice_index < total_slices - 1,
                'can_go_back': self.history_index > 0,
                'can_go_forward': self.history_index < len(self.navigation_history) - 1,
                'history_size': len(self.navigation_history),
                'navigation_mode': self.navigation_mode,
                'auto_save_on_navigate': self.auto_save_on_navigate,
                'skip_annotated': self.skip_annotated
            }
            
            return info
            
        except Exception as e:
            log_error(f"获取导航信息失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return {}
    
    def _navigate_to_index(self, index: int, add_to_history: bool = True) -> bool:
        """
        导航到指定索引的切片
        
        Args:
            index: 目标切片索引
            add_to_history: 是否添加到历史记录
            
        Returns:
            如果导航成功返回True，否则返回False
        """
        try:
            if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
                return False
            
            if index < 0 or index >= len(self.gui.slice_files):
                log_warning(f"切片索引超出范围: {index}", "NAVIGATION_CONTROLLER")
                return False
            
            # 如果需要自动保存当前标注
            if self.auto_save_on_navigate and hasattr(self.gui, 'current_annotation_modified'):
                if getattr(self.gui, 'current_annotation_modified', False):
                    if hasattr(self.gui, 'save_current_annotation'):
                        try:
                            self.gui.save_current_annotation()
                        except Exception as e:
                            log_warning(f"自动保存标注失败: {e}", "NAVIGATION_CONTROLLER")
            
            # 更新当前索引
            old_index = self.current_slice_index
            self.current_slice_index = index
            
            # 更新GUI的当前切片索引
            if hasattr(self.gui, 'current_slice_index'):
                self.gui.current_slice_index = index
            
            # 加载新的切片
            if hasattr(self.gui, 'load_current_slice'):
                self.gui.load_current_slice()
            
            # 更新导航状态
            current_file = self.gui.slice_files[index]
            self.current_panoramic_id = current_file.get('panoramic_id')
            self.current_hole_number = current_file.get('hole_number')
            
            log_debug(f"导航完成: 从索引 {old_index} 到 {index} (孔位: {self.current_hole_number})", "NAVIGATION_CONTROLLER")
            return True
            
        except Exception as e:
            log_error(f"导航到索引 {index} 失败: {str(e)}", "NAVIGATION_CONTROLLER")
            return False
    
    def _find_slice_index_by_hole(self, hole_number: int) -> Optional[int]:
        """查找指定孔位的切片索引"""
        if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
            return None
        
        for i, slice_file in enumerate(self.gui.slice_files):
            if slice_file.get('hole_number') == hole_number:
                return i
        
        return None
    
    def _find_next_valid_index(self, skip_annotated: bool = False) -> Optional[int]:
        """查找下一个有效的切片索引"""
        if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
            return None
        
        start_index = self.current_slice_index + 1
        
        for i in range(start_index, len(self.gui.slice_files)):
            if self._is_valid_slice_index(i, skip_annotated):
                return i
        
        return None
    
    def _find_previous_valid_index(self, skip_annotated: bool = False) -> Optional[int]:
        """查找上一个有效的切片索引"""
        if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
            return None
        
        start_index = self.current_slice_index - 1
        
        for i in range(start_index, -1, -1):
            if self._is_valid_slice_index(i, skip_annotated):
                return i
        
        return None
    
    def _find_first_valid_index(self) -> Optional[int]:
        """查找第一个有效的切片索引"""
        if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
            return None
        
        # 如果有起始孔位设置，使用起始孔位
        if hasattr(self.gui, 'hole_manager') and self.gui.hole_manager:
            start_hole = getattr(self.gui.hole_manager, 'start_hole_number', 1)
            for i, slice_file in enumerate(self.gui.slice_files):
                if slice_file.get('hole_number', 1) >= start_hole:
                    return i
        
        return 0
    
    def _find_last_valid_index(self) -> Optional[int]:
        """查找最后一个有效的切片索引"""
        if not hasattr(self.gui, 'slice_files') or not self.gui.slice_files:
            return None
        
        return len(self.gui.slice_files) - 1
    
    def _is_valid_slice_index(self, index: int, skip_annotated: bool = False) -> bool:
        """检查切片索引是否有效"""
        if index < 0 or index >= len(self.gui.slice_files):
            return False
        
        if skip_annotated:
            # 检查是否已标注
            slice_file = self.gui.slice_files[index]
            panoramic_id = slice_file.get('panoramic_id')
            hole_number = slice_file.get('hole_number')
            
            if hasattr(self.gui, 'current_dataset') and self.gui.current_dataset:
                annotation = self.gui.current_dataset.get_annotation_by_hole(panoramic_id, hole_number)
                if annotation and getattr(annotation, 'is_confirmed', False):
                    return False
        
        return True
    
    def _get_target_hole_by_direction(self, current_hole: int, direction: NavigationDirection) -> Optional[int]:
        """根据方向获取目标孔位"""
        if not hasattr(self.gui, 'hole_manager') or not self.gui.hole_manager:
            return None
        
        try:
            # 获取当前孔位的行列位置
            row, col = self.gui.hole_manager.get_hole_position(current_hole)
            
            # 根据方向计算目标位置
            if direction == NavigationDirection.UP:
                target_row, target_col = row - 1, col
            elif direction == NavigationDirection.DOWN:
                target_row, target_col = row + 1, col
            elif direction == NavigationDirection.LEFT:
                target_row, target_col = row, col - 1
            elif direction == NavigationDirection.RIGHT:
                target_row, target_col = row, col + 1
            else:
                return None
            
            # 获取目标孔位编号
            target_hole = self.gui.hole_manager.get_hole_number(target_row, target_col)
            
            # 验证目标孔位是否存在切片
            if self._find_slice_index_by_hole(target_hole) is not None:
                return target_hole
            
            return None
            
        except Exception as e:
            log_debug(f"计算方向导航目标失败: {e}", "NAVIGATION_CONTROLLER")
            return None
    
    def _add_to_history(self):
        """添加当前状态到导航历史"""
        try:
            # 移除当前位置之后的历史记录
            if self.history_index >= 0:
                self.navigation_history = self.navigation_history[:self.history_index + 1]
            
            # 添加新的历史记录
            history_item = {
                'slice_index': self.current_slice_index,
                'panoramic_id': self.current_panoramic_id,
                'hole_number': self.current_hole_number,
                'timestamp': tk.time.time()
            }
            
            self.navigation_history.append(history_item)
            self.history_index = len(self.navigation_history) - 1
            
            # 限制历史记录大小
            if len(self.navigation_history) > self.max_history_size:
                self.navigation_history = self.navigation_history[-self.max_history_size:]
                self.history_index = len(self.navigation_history) - 1
            
        except Exception as e:
            log_error(f"添加导航历史失败: {str(e)}", "NAVIGATION_CONTROLLER")
    
    def clear_history(self):
        """清空导航历史"""
        self.navigation_history.clear()
        self.history_index = -1
        log_debug("导航历史已清空", "NAVIGATION_CONTROLLER")
    
    def set_navigation_settings(self, **kwargs):
        """
        设置导航参数
        
        Args:
            **kwargs: 导航设置参数
        """
        try:
            if 'auto_save_on_navigate' in kwargs:
                self.auto_save_on_navigate = kwargs['auto_save_on_navigate']
            
            if 'skip_annotated' in kwargs:
                self.skip_annotated = kwargs['skip_annotated']
            
            if 'navigation_mode' in kwargs:
                self.navigation_mode = kwargs['navigation_mode']
            
            log_debug(f"导航设置已更新: {kwargs}", "NAVIGATION_CONTROLLER")
            
        except Exception as e:
            log_error(f"设置导航参数失败: {str(e)}", "NAVIGATION_CONTROLLER")
