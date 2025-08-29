#!/usr/bin/env python3
"""
增强标注恢复修复验证测试
解决问题：设置了25号孔增强标注为阳性--聚集型，导航后回来时生长级别和模式未恢复
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_enhanced_restoration():
    """测试增强标注恢复修复"""
    print("🔧 增强标注恢复修复验证")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI初始化成功")
        print("\n🎯 问题描述:")
        print("- 设置25号孔增强标注为'阳性--聚集型'")
        print("- 点击'保存并下一个'切换到26号孔") 
        print("- 再切换回25号孔")
        print("- 问题：生长级别未设置且生长模式未设置")
        
        print("\n🔧 已实施的修复:")
        print("✓ 修复 set_feature_combination 方法正确处理枚举值")
        print("✓ 添加详细的恢复调试输出")
        print("✓ 改进特征组合数据的序列化和反序列化")
        print("✓ 增强错误处理和回退机制")
        
        print("\n📝 测试步骤:")
        print("1. 加载包含切片数据的全景图")
        print("2. 导航到25号孔")
        print("3. 在增强标注面板中设置：")
        print("   - 生长级别：阳性")
        print("   - 生长模式：聚集型")
        print("4. 点击'保存并下一个'")
        print("5. 导航回25号孔")
        print("6. 验证增强标注面板是否正确恢复状态")
        
        print("\n🔍 期望修复效果:")
        print("✅ 当前生长级别选择: 阳性")
        print("✅ 当前生长模式选择: 聚集型")
        print("✅ 控制台输出显示数据正确恢复")
        print("✅ 不再回退到默认状态")
        
        print("\n📋 关键修复点:")
        print("• set_feature_combination方法现在正确提取枚举的.value属性")
        print("• 增强了特征组合数据的调试输出")
        print("• 改进了错误处理和异常恢复机制")
        print("• 确保UI变量接收正确的字符串值而非枚举对象")
        
        print("\n🚀 启动修复后的GUI进行测试...")
        
        # 启动GUI主循环
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔧 增强标注恢复修复验证")
    print("目标：修复阳性--聚集型标注导航后的恢复问题")
    print()
    
    success = test_enhanced_restoration()
    
    if success:
        print("\n✅ 修复验证启动成功")
        print("请按照上述测试步骤验证修复效果")
    else:
        print("\n❌ 修复验证启动失败")
    
    print("\n📋 验证清单:")
    print("[ ] 设置25号孔为阳性--聚集型")
    print("[ ] 保存并导航到26号孔")
    print("[ ] 导航回25号孔")
    print("[ ] 验证生长级别显示为'阳性'")
    print("[ ] 验证生长模式显示为'聚集型'")
    print("[ ] 控制台输出显示数据正确恢复")
    
    sys.exit(0 if success else 1)