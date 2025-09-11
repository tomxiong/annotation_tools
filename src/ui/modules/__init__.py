"""
模块化GUI组件包
包含各种功能模块，实现GUI功能的模块化管理
"""

from .data_manager import DataManager
from .ui_builder import UIBuilder
from .event_dispatcher import EventDispatcher
from .slice_controller import SliceController
from .annotation_assistant import AnnotationAssistant
from .annotation_processor import AnnotationProcessor
from .dialog_factory import DialogFactory
from .view_manager import ViewManager
from .image_processor import ImageProcessor
from .navigation_controller import NavigationController
from .state_manager import StateManager

__all__ = [
    'DataManager',
    'UIBuilder', 
    'EventDispatcher',
    'SliceController',
    'AnnotationAssistant',
    'AnnotationProcessor',
    'DialogFactory',
    'ViewManager',
    'ImageProcessor',
    'NavigationController',
    'StateManager'
]
