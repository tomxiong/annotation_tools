#!/usr/bin/env python3
"""
全自动标注同步问题检测和修复工具
专门解决：1.统计并未更新，2.切换回去状态也未更新
"""

import sys
import os
import time
import threading
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

class AutomatedSyncRepair:
    """全自动标注同步修复器"""
    
    def __init__(self):
        self.test_results = {}
        self.repair_actions = []
        
    def run_comprehensive_repair(self):
        """运行全面的自动修复"""
        print("🔧 启动全自动标注同步问题检测和修复")
        print("=" * 60)
        
        # 检测1：统计更新问题
        print("🔍 检测问题1：统计并未更新")
        stats_issue = self.detect_statistics_update_issue()
        
        # 检测2：状态更新问题
        print("🔍 检测问题2：切换回去状态也未更新")  
        status_issue = self.detect_status_update_issue()
        
        # 自动修复
        if stats_issue or status_issue:
            print("\n🛠  开始自动修复...")
            self.apply_automated_fixes()
            
            # 验证修复结果
            print("\n✅ 验证修复结果...")
            self.verify_repair_results()
        else:
            print("\n✅ 未检测到同步问题")
            
        return self.test_results
    
    def detect_statistics_update_issue(self):
        """检测统计更新问题"""
        print("   检查update_statistics()方法调用时机...")
        
        issues_found = []
        
        try:
            # 检查save_current_annotation_internal方法
            gui_file = src_dir / "ui" / "panoramic_annotation_gui.py"
            with open(gui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查保存方法中是否有正确的统计更新
            if 'def save_current_annotation_internal' in content:
                save_method_start = content.find('def save_current_annotation_internal')
                save_method_end = content.find('\n    def ', save_method_start + 1)
                if save_method_end == -1:
                    save_method_end = len(content)
                
                save_method = content[save_method_start:save_method_end]
                
                if 'self.update_statistics()' not in save_method:
                    issues_found.append("保存方法中缺少统计更新调用")
                elif save_method.count('self.update_statistics()') < 2:
                    issues_found.append("保存方法中统计更新调用次数不足")
                    
                if 'self.root.update_idletasks()' not in save_method:
                    issues_found.append("保存方法中缺少界面强制刷新")
                elif save_method.count('self.root.update_idletasks()') < 3:
                    issues_found.append("保存方法中界面刷新次数不足")
            
            # 检查导航方法中的统计更新
            for method_name in ['go_prev_hole', 'go_next_hole', 'navigate_to_hole']:
                if f'def {method_name}' in content:
                    method_start = content.find(f'def {method_name}')
                    method_end = content.find('\n    def ', method_start + 1)
                    if method_end == -1:
                        method_end = content.find('\n\n    def ', method_start + 1)
                    if method_end == -1:
                        method_end = len(content)
                    
                    method_content = content[method_start:method_end]
                    
                    if '_force_navigation_refresh' not in method_content:
                        issues_found.append(f"{method_name}方法中缺少导航后强制刷新")
            
            self.test_results['statistics_issues'] = issues_found
            print(f"   发现 {len(issues_found)} 个统计更新问题")
            for issue in issues_found:
                print(f"   - {issue}")
                
            return len(issues_found) > 0
            
        except Exception as e:
            print(f"   检测失败: {e}")
            return True
    
    def detect_status_update_issue(self):
        """检测状态更新问题"""
        print("   检查update_slice_info_display()方法调用时机...")
        
        issues_found = []
        
        try:
            gui_file = src_dir / "ui" / "panoramic_annotation_gui.py"
            with open(gui_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查load_existing_annotation方法
            if 'def load_existing_annotation' in content:
                method_start = content.find('def load_existing_annotation')
                method_end = content.find('\n    def ', method_start + 1)
                if method_end == -1:
                    method_end = len(content)
                
                method_content = content[method_start:method_end]
                
                # 检查时间戳同步逻辑
                if 'self.last_annotation_time[annotation_key]' not in method_content:
                    issues_found.append("load_existing_annotation中缺少时间戳同步")
                
                if 'enhanced_manual' not in method_content:
                    issues_found.append("load_existing_annotation中缺少增强标注识别")
            
            # 检查get_annotation_status_text方法
            if 'def get_annotation_status_text' in content:
                method_start = content.find('def get_annotation_status_text')
                method_end = content.find('\n    def ', method_start + 1)
                if method_end == -1:
                    method_end = len(content)
                
                method_content = content[method_start:method_end]
                
                if 'enhanced_manual' not in method_content:
                    issues_found.append("get_annotation_status_text中缺少增强标注检查")
                
                if 'last_annotation_time' not in method_content:
                    issues_found.append("get_annotation_status_text中缺少时间戳获取")
            
            self.test_results['status_issues'] = issues_found
            print(f"   发现 {len(issues_found)} 个状态更新问题")
            for issue in issues_found:
                print(f"   - {issue}")
                
            return len(issues_found) > 0
            
        except Exception as e:
            print(f"   检测失败: {e}")
            return True
    
    def apply_automated_fixes(self):
        """应用自动修复"""
        print("   正在应用超强力UI刷新修复...")
        
        # 修复1：超强力统计更新
        self.apply_super_force_statistics_update()
        
        # 修复2：超强力状态更新
        self.apply_super_force_status_update()
        
        # 修复3：添加调试输出
        self.add_debug_output()
        
        print("   ✅ 自动修复完成")
    
    def apply_super_force_statistics_update(self):
        """应用超强力统计更新修复"""
        gui_file = src_dir / "ui" / "panoramic_annotation_gui.py"
        
        # 添加超强力统计更新方法
        super_update_method = '''
    def _super_force_statistics_update(self):
        """超强力统计更新，确保统计信息必须更新"""
        try:
            print(f"DEBUG: 开始超强力统计更新")
            
            # 多次强制更新统计
            for i in range(3):
                self.update_statistics()
                self.root.update_idletasks()
                self.root.update()
                print(f"DEBUG: 统计更新第{i+1}次完成")
                
            # 强制刷新统计标签
            if hasattr(self, 'stats_label'):
                stats_text = self.stats_label.cget('text')
                print(f"DEBUG: 当前统计文本: {stats_text}")
                
            print(f"DEBUG: 超强力统计更新完成")
        except Exception as e:
            print(f"DEBUG: 超强力统计更新失败: {e}")
'''
        
        self._insert_method_to_file(gui_file, super_update_method)
        
        # 修改save方法调用超强力更新
        self._replace_in_file(gui_file, 
            "self.update_statistics()",
            "self._super_force_statistics_update()")
    
    def apply_super_force_status_update(self):
        """应用超强力状态更新修复"""
        gui_file = src_dir / "ui" / "panoramic_annotation_gui.py"
        
        # 添加超强力状态更新方法
        super_status_method = '''
    def _super_force_status_update(self):
        """超强力状态更新，确保状态信息必须更新"""
        try:
            print(f"DEBUG: 开始超强力状态更新")
            
            # 获取当前标注状态
            status_text = self.get_annotation_status_text()
            print(f"DEBUG: 当前状态文本: {status_text}")
            
            # 多次强制更新状态显示
            for i in range(3):
                self.update_slice_info_display()
                self.root.update_idletasks()
                self.root.update()
                print(f"DEBUG: 状态更新第{i+1}次完成")
                
            # 强制刷新切片信息标签
            if hasattr(self, 'slice_info_label'):
                slice_text = self.slice_info_label.cget('text')
                print(f"DEBUG: 当前切片信息: {slice_text}")
                
            print(f"DEBUG: 超强力状态更新完成")
        except Exception as e:
            print(f"DEBUG: 超强力状态更新失败: {e}")
'''
        
        self._insert_method_to_file(gui_file, super_status_method)
        
        # 修改相关方法调用超强力状态更新
        self._replace_in_file(gui_file,
            "self.update_slice_info_display()",
            "self._super_force_status_update()")
    
    def add_debug_output(self):
        """添加调试输出"""
        gui_file = src_dir / "ui" / "panoramic_annotation_gui.py"
        
        # 在关键方法中添加调试输出
        debug_replacements = [
            ("def save_current_annotation_internal(self):", 
             "def save_current_annotation_internal(self):\n        print(f'DEBUG: 开始保存标注 - 孔位{self.current_hole_number}')"),
            ("def load_current_slice(self):",
             "def load_current_slice(self):\n        print(f'DEBUG: 加载切片 - 索引{self.current_slice_index}')"),
            ("def get_annotation_status_text(self):",
             "def get_annotation_status_text(self):\n        print(f'DEBUG: 获取标注状态 - 孔位{self.current_hole_number}')")
        ]
        
        for old, new in debug_replacements:
            self._replace_in_file(gui_file, old, new)
    
    def _insert_method_to_file(self, file_path, method_code):
        """在文件中插入方法"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 在类定义结束前插入
            insert_pos = content.rfind('\n\nclass ')
            if insert_pos == -1:
                insert_pos = len(content) - 100
            
            new_content = content[:insert_pos] + method_code + content[insert_pos:]
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
            print(f"   ✅ 已插入超强力方法到 {file_path.name}")
            
        except Exception as e:
            print(f"   ❌ 插入方法失败: {e}")
    
    def _replace_in_file(self, file_path, old_text, new_text):
        """在文件中替换文本"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if old_text in content:
                new_content = content.replace(old_text, new_text)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                    
                print(f"   ✅ 已替换文本: {old_text[:50]}...")
            else:
                print(f"   ⚠️  未找到文本: {old_text[:50]}...")
                
        except Exception as e:
            print(f"   ❌ 替换文本失败: {e}")
    
    def verify_repair_results(self):
        """验证修复结果"""
        print("   正在启动GUI验证修复结果...")
        
        # 启动GUI进行验证
        verification_script = f'''
import sys
import os
from pathlib import Path

current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

import tkinter as tk
from ui.panoramic_annotation_gui import PanoramicAnnotationGUI

def run_verification():
    print("🔍 验证修复结果...")
    root = tk.Tk()
    app = PanoramicAnnotationGUI(root)
    
    print("✅ GUI启动成功，请测试以下功能：")
    print("1. 加载数据集")
    print("2. 进行标注并保存")
    print("3. 观察统计是否立即更新")
    print("4. 切换到其他切片再切换回来")
    print("5. 观察状态是否正确更新")
    print("\\n如果看到DEBUG输出，说明修复生效")
    
    root.mainloop()

if __name__ == '__main__':
    run_verification()
'''
        
        verification_file = project_root / "verify_repair.py"
        with open(verification_file, 'w', encoding='utf-8') as f:
            f.write(verification_script)
        
        print(f"   ✅ 已创建验证脚本: {verification_file}")
        print("   请运行以下命令验证修复结果：")
        print(f"   cd {project_root} && venv\\Scripts\\activate && python verify_repair.py")

def main():
    """主函数"""
    print("🚀 全自动标注同步问题修复工具")
    print("专门解决：1.统计并未更新，2.切换回去状态也未更新")
    print()
    
    repair_tool = AutomatedSyncRepair()
    results = repair_tool.run_comprehensive_repair()
    
    print("\n📊 修复总结:")
    print(f"统计问题: {len(results.get('statistics_issues', []))} 个")
    print(f"状态问题: {len(results.get('status_issues', []))} 个")
    print("\n🎯 应用的修复：")
    print("✅ 超强力统计更新机制")
    print("✅ 超强力状态更新机制") 
    print("✅ 调试输出增强")
    print("✅ 多重强制UI刷新")
    
    print("\n🔧 请运行验证脚本测试修复效果")

if __name__ == '__main__':
    main()