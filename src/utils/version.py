#!/usr/bin/env python3
"""
版本管理模块
负责读取和管理应用程序版本信息
"""

import os
from pathlib import Path
from typing import Optional

class VersionManager:
    """版本管理器"""
    
    def __init__(self, version_file: str = "version.txt"):
        """
        初始化版本管理器
        
        Args:
            version_file: 版本文件路径，相对于项目根目录
        """
        self.version_file = version_file
        self._version = None
        self._build_info = None
    
    def get_project_root(self) -> Path:
        """获取项目根目录"""
        current_file = Path(__file__).resolve()
        # 从src/utils向上查找到项目根目录
        return current_file.parent.parent.parent
    
    def read_version(self) -> str:
        """
        读取版本号
        
        Returns:
            版本号字符串，如果读取失败返回"Unknown"
        """
        if self._version is not None:
            return self._version
        
        try:
            project_root = self.get_project_root()
            version_path = project_root / self.version_file
            
            if version_path.exists():
                version_content = version_path.read_text(encoding='utf-8').strip()
                self._version = version_content
                return self._version
            else:
                self._version = "Unknown"
                return self._version
        except Exception as e:
            print(f"读取版本文件时出错: {e}")
            self._version = "Unknown"
            return self._version
    
    def get_version_display(self) -> str:
        """
        获取用于显示的版本信息
        
        Returns:
            格式化的版本显示字符串
        """
        version = self.read_version()
        return f"v{version}"
    
    def get_full_version_info(self) -> dict:
        """
        获取完整的版本信息
        
        Returns:
            包含版本号、构建信息等的字典
        """
        version = self.read_version()
        
        # 解析版本号（假设格式为 major.minor.patch.build）
        version_parts = version.split('.')
        
        info = {
            "version": version,
            "display": self.get_version_display(),
            "major": version_parts[0] if len(version_parts) > 0 else "0",
            "minor": version_parts[1] if len(version_parts) > 1 else "0",
            "patch": version_parts[2] if len(version_parts) > 2 else "0",
            "build": version_parts[3] if len(version_parts) > 3 else "0"
        }
        
        return info
    
    def update_version(self, new_version: str) -> bool:
        """
        更新版本号
        
        Args:
            new_version: 新的版本号
            
        Returns:
            是否更新成功
        """
        try:
            project_root = self.get_project_root()
            version_path = project_root / self.version_file
            
            version_path.write_text(new_version.strip(), encoding='utf-8')
            self._version = new_version.strip()
            return True
        except Exception as e:
            print(f"更新版本文件时出错: {e}")
            return False

# 全局版本管理器实例
_version_manager = VersionManager()

def get_version() -> str:
    """获取当前版本号"""
    return _version_manager.read_version()

def get_version_display() -> str:
    """获取用于显示的版本信息"""
    return _version_manager.get_version_display()

def get_version_info() -> dict:
    """获取完整版本信息"""
    return _version_manager.get_full_version_info()

def update_version(new_version: str) -> bool:
    """更新版本号"""
    return _version_manager.update_version(new_version)
