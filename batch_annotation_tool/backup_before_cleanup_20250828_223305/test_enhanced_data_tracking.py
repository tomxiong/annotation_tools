#!/usr/bin/env python3
"""
Enhanced Data Tracking Test
This script helps track the enhanced annotation save/load process to identify why enhanced_data is missing
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

def test_enhanced_data_flow():
    """Test enhanced data save/load flow"""
    print("🔍 Enhanced Data Tracking Test")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # 创建GUI实例
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI初始化成功")
        
        print("\n🎯 问题分析:")
        print("从您的控制台输出中发现:")
        print("1. ✓ positive_clustered 特征组合创建成功")
        print("2. ✓ 枚举值处理修复生效")
        print("3. ✓ 统计更新正常工作")
        print("4. ✓ 时间戳生成正常")
        print("5. ❌ enhanced_data属性缺失或为False")
        
        print("\n🔍 关键发现:")
        print("控制台显示: [DEBUG] 是否有enhanced_data属性: False")
        print("这意味着saved annotation没有enhanced_data，所以回退到sync方法")
        print("sync方法默认使用positive_heavy_growth而不是positive_clustered")
        
        print("\n📋 调试步骤:")
        print("现在请按照以下步骤操作，并观察新的调试输出:")
        print()
        print("1. 加载包含切片的全景图")
        print("2. 导航到任意孔位（比如25号孔）")
        print("3. 在增强标注面板设置:")
        print("   - 生长级别: 阳性")
        print("   - 生长模式: 聚集型")
        print("4. 点击'保存并下一个'")
        print("5. 观察控制台输出，特别关注:")
        print("   [SAVE] 保存增强数据: XXX 字符")
        print("   [SAVE] ✓ enhanced_data设置成功")
        print("   [VERIFY] 保存的特征: 级别=positive, 模式=clustered")
        print("6. 导航回该孔位")
        print("7. 观察是否显示:")
        print("   [DEBUG] enhanced_data内容: True")
        print("   [DEBUG] 条件满足，进入增强数据恢复流程")
        
        print("\n🔧 新增的调试功能:")
        print("✓ [SAVE] 详细的enhanced_data保存过程追踪")
        print("✓ [VERIFY] 验证保存到数据集的实际数据")
        print("✓ 减少了config_import的噪音输出")
        print("✓ 增强了特征组合数据的验证")
        
        print("\n🎯 预期结果:")
        print("如果修复完全成功，您应该看到:")
        print("1. 保存时: [SAVE] ✓ enhanced_data设置成功")
        print("2. 保存时: [VERIFY] 保存的特征: 级别=positive, 模式=clustered")
        print("3. 加载时: [DEBUG] enhanced_data内容: True")
        print("4. 加载时: [RESTORE] 设置特征组合: 级别=positive, 模式=clustered")
        print("5. UI显示: 生长级别='阳性', 生长模式='聚集型'")
        
        print("\n🚀 启动调试版GUI...")
        
        # 启动GUI主循环
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔍 Enhanced Data Tracking Test")
    print("目标：追踪enhanced_data的保存和加载过程")
    print()
    
    success = test_enhanced_data_flow()
    
    if success:
        print("\n✅ 调试测试启动成功")
        print("请按照上述步骤进行测试并观察调试输出")
    else:
        print("\n❌ 调试测试启动失败")
    
    print("\n📋 调试验证清单:")
    print("[ ] 看到 [SAVE] ✓ enhanced_data设置成功")
    print("[ ] 看到 [VERIFY] 保存的特征包含正确的模式")
    print("[ ] 看到 [DEBUG] enhanced_data内容: True")
    print("[ ] 看到 [RESTORE] 设置正确的特征组合")
    print("[ ] UI正确显示保存的生长模式")
    
    sys.exit(0 if success else 1)