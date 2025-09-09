"""
导航管理器模块

负责图像和孔位间的导航逻辑
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    from .main_controller import MainController

logger = logging.getLogger(__name__)


class NavigationManager:
    """导航管理器 - 负责导航逻辑"""

    def __init__(self, controller: 'MainController'):
        self.controller = controller

        # 导航状态
        self.panoramic_ids: List[str] = []
        self.current_panoramic_id = ""
        self.current_hole_number = 1
        self.current_slice_index = 0

    def initialize(self):
        """初始化导航管理器"""
        logger.info("NavigationManager initialized")

    def set_panoramic_ids(self, panoramic_ids: List[str]):
        """设置全景图ID列表"""
        self.panoramic_ids = panoramic_ids
        logger.debug(f"Set panoramic IDs: {panoramic_ids}")

    def set_current_panoramic(self, panoramic_id: str):
        """设置当前全景图"""
        if panoramic_id in self.panoramic_ids:
            self.current_panoramic_id = panoramic_id
            logger.debug(f"Set current panoramic: {panoramic_id}")
            return True
        else:
            logger.warning(f"Panoramic ID {panoramic_id} not found in available IDs")
            return False

    def set_current_hole(self, hole_number: int):
        """设置当前孔位"""
        if 1 <= hole_number <= 120:
            self.current_hole_number = hole_number
            logger.debug(f"Set current hole: {hole_number}")
            return True
        else:
            logger.warning(f"Invalid hole number: {hole_number}")
            return False

    def set_current_slice_index(self, index: int):
        """设置当前切片索引"""
        self.current_slice_index = index
        logger.debug(f"Set current slice index: {index}")

    def go_to_next_panoramic(self) -> bool:
        """跳转到下一个全景图"""
        if not self.panoramic_ids:
            return False

        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)

        next_index = (current_index + 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[next_index]

        return self._switch_to_panoramic(target_panoramic_id)

    def go_to_prev_panoramic(self) -> bool:
        """跳转到上一个全景图"""
        if not self.panoramic_ids:
            return False

        current_index = 0
        if self.current_panoramic_id in self.panoramic_ids:
            current_index = self.panoramic_ids.index(self.current_panoramic_id)

        prev_index = (current_index - 1) % len(self.panoramic_ids)
        target_panoramic_id = self.panoramic_ids[prev_index]

        return self._switch_to_panoramic(target_panoramic_id)

    def go_to_next_hole(self) -> bool:
        """跳转到下一个孔位"""
        next_hole = self.current_hole_number + 1
        if next_hole > 120:
            next_hole = 1

        return self._switch_to_hole(next_hole)

    def go_to_prev_hole(self) -> bool:
        """跳转到上一个孔位"""
        prev_hole = self.current_hole_number - 1
        if prev_hole < 1:
            prev_hole = 120

        return self._switch_to_hole(prev_hole)

    def go_to_first_hole(self) -> bool:
        """跳转到第一个孔位"""
        start_hole = self.controller.hole_manager.start_hole_number if self.controller.hole_manager else 25
        return self._switch_to_hole(start_hole)

    def go_to_last_hole(self) -> bool:
        """跳转到最后一个孔位"""
        return self._switch_to_hole(120)

    def go_to_hole(self, hole_number: int) -> bool:
        """跳转到指定孔位"""
        try:
            hole_num = int(hole_number)
            if 1 <= hole_num <= 120:
                return self._switch_to_hole(hole_num)
            else:
                logger.warning(f"孔位编号必须在1-120之间: {hole_number}")
                return False
        except ValueError:
            logger.warning(f"无效的孔位编号: {hole_number}")
            return False

    def find_hole_at_position(self, x: float, y: float) -> Optional[int]:
        """根据位置查找孔位"""
        if not self.controller.panoramic_image or not self.controller.hole_manager:
            return None

        try:
            # 获取画布尺寸
            canvas_width = self.controller.ui_manager.get_panoramic_canvas().winfo_width()
            canvas_height = self.controller.ui_manager.get_panoramic_canvas().winfo_height()

            # 计算缩放比例
            img_width, img_height = self.controller.panoramic_image.size
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y)

            # 计算图像在画布上的偏移
            offset_x = (canvas_width - img_width * scale) / 2
            offset_y = (canvas_height - img_height * scale) / 2

            # 转换为图像坐标
            img_x = (x - offset_x) / scale
            img_y = (y - offset_y) / scale

            # 查找点击位置对应的孔位
            for row in range(10):  # 10行
                for col in range(12):  # 12列
                    hole_number = row * 12 + col + 1

                    # 获取孔位位置
                    hole_pos = self.controller.hole_manager.get_hole_position(hole_number)
                    if hole_pos:
                        hole_x, hole_y = hole_pos

                        # 检查点击是否在孔位范围内
                        distance = ((img_x - hole_x) ** 2 + (img_y - hole_y) ** 2) ** 0.5
                        if distance <= 15:  # 15像素半径
                            return hole_number

            return None

        except Exception as e:
            logger.error(f"查找孔位位置失败: {str(e)}")
            return None

    def _switch_to_panoramic(self, panoramic_id: str) -> bool:
        """切换到指定全景图"""
        if panoramic_id not in self.panoramic_ids:
            logger.debug(f"全景图 {panoramic_id} 不在可用列表中")
            return False

        # 保存当前标注
        self.controller._save_current_annotation_internal("navigation")

        # 查找目标全景图的第一个孔位
        target_slice_index = None
        start_hole = self.controller.hole_manager.start_hole_number if self.controller.hole_manager else 25

        for i, slice_file in enumerate(self.controller.slice_files):
            if (slice_file['panoramic_id'] == panoramic_id and
                slice_file.get('hole_number', 1) >= start_hole):
                target_slice_index = i
                break

        if target_slice_index is not None:
            # 更新当前索引和全景图ID
            self.current_slice_index = target_slice_index
            self.current_panoramic_id = panoramic_id

            # 更新hole_manager的panoramic_id，确保模型建议正确显示
            if hasattr(self.controller, 'hole_manager') and self.controller.hole_manager:
                self.controller.hole_manager._current_panoramic_id = panoramic_id

            # 更新下拉列表选中项
            panoramic_combobox = self.controller.ui_manager.get_panoramic_combobox()
            if panoramic_combobox:
                panoramic_combobox.set(panoramic_id)

            # 加载新的切片
            self.controller._load_current_slice()
            self.controller._update_progress()
            self.controller._update_statistics()

            # 保留关键的用户提示信息
            logger.info(f"已切换到全景图: {panoramic_id}")
            return True
        else:
            logger.debug(f"未找到全景图 {panoramic_id} 的切片文件")
            return False

    def _switch_to_hole(self, hole_number: int) -> bool:
        """切换到指定孔位"""
        if not self.controller.slice_files:
            return False

        # 查找指定孔位的切片
        target_index = None
        for i, slice_file in enumerate(self.controller.slice_files):
            if (slice_file['panoramic_id'] == self.current_panoramic_id and
                slice_file['hole_number'] == hole_number):
                target_index = i
                break

        if target_index is not None:
            self.current_slice_index = target_index
            self.current_hole_number = hole_number
            self.controller.hole_number_var.set(str(hole_number))

            # 加载切片
            self.controller._load_current_slice()
            self.controller._update_progress()

            logger.debug(f"已切换到孔位: {hole_number}")
            return True
        else:
            logger.debug(f"未找到孔位 {hole_number} 的切片文件")
            return False

    def get_current_panoramic_id(self) -> str:
        """获取当前全景图ID"""
        return self.current_panoramic_id

    def get_current_hole_number(self) -> int:
        """获取当前孔位编号"""
        return self.current_hole_number

    def get_current_slice_index(self) -> int:
        """获取当前切片索引"""
        return self.current_slice_index

    def get_panoramic_ids(self) -> List[str]:
        """获取全景图ID列表"""
        return self.panoramic_ids.copy()

    def update_panoramic_list(self):
        """更新全景图列表"""
        try:
            # 从切片文件中提取唯一的全景图ID
            panoramic_ids = set()
            for slice_file in self.controller.slice_files:
                panoramic_ids.add(slice_file['panoramic_id'])

            self.panoramic_ids = sorted(list(panoramic_ids))

            # 更新下拉列表
            panoramic_combobox = self.controller.ui_manager.get_panoramic_combobox()
            if panoramic_combobox:
                panoramic_combobox['values'] = self.panoramic_ids

                # 设置当前选中项
                if self.current_panoramic_id in self.panoramic_ids:
                    panoramic_combobox.set(self.current_panoramic_id)
                elif self.panoramic_ids:
                    panoramic_combobox.set(self.panoramic_ids[0])

        except Exception as e:
            logger.error(f"更新全景图列表失败: {e}")

    def find_first_valid_slice_index(self) -> int:
        """找到第一个有效孔位的切片索引"""
        if not self.controller.slice_files:
            return 0

        start_hole = self.controller.hole_manager.start_hole_number if self.controller.hole_manager else 25

        # 查找第一个孔位号大于等于起始孔位的切片
        for i, slice_file in enumerate(self.controller.slice_files):
            hole_number = slice_file.get('hole_number', 1)
            if hole_number >= start_hole:
                return i

        # 如果没找到有效孔位，返回0
        return 0