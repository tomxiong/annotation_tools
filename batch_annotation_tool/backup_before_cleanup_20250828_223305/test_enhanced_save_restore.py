#!/usr/bin/env python3
"""
Test script to validate enhanced annotation save/restore functionality
This verifies that our fixes to save_current_annotation_internal are working
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_enhanced_save_restore():
    """Test enhanced save/restore functionality"""
    print("🔧 Enhanced Annotation Save/Restore Test")
    print("=" * 60)
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # Create GUI instance
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✅ GUI initialization successful")
        
        print("\n🎯 Test Instructions:")
        print("1. Load a panoramic image with slices")
        print("2. Navigate to any hole (e.g., hole 25)")
        print("3. In the enhanced annotation panel, set:")
        print("   - Growth Level: 阳性 (positive)")
        print("   - Growth Pattern: 聚集型 (clustered)")
        print("4. Click '保存并下一个' (Save and Next)")
        print("5. Watch for NEW debug output:")
        print("   ✓ [SAVE] 检查增强标注面板: hasattr=True, not None=True")
        print("   ✓ [SAVE] 准备保存增强标注: positive [1.00]")
        print("   ✓ [SAVE] 训练标签: positive_clustered")
        print("   ✓ [SAVE] enhanced_annotation.to_dict() 成功: XXX 字符")
        print("   ✓ [SAVE] enhanced_data 赋值成功")
        print("   ✓ [SAVE] ✓ enhanced_data设置成功")
        print("   ✓ [VERIFY] 保存的特征: 级别=positive, 模式=clustered")
        print("6. Navigate to another hole (e.g., hole 26)")
        print("7. Navigate back to the original hole (e.g., hole 25)")
        print("8. Watch for enhanced restore output:")
        print("   ✓ [DEBUG] enhanced_data内容: True") 
        print("   ✓ [DEBUG] 条件满足，进入增强数据恢复流程")
        print("   ✓ [RESTORE] 设置特征组合: 级别=positive, 模式=clustered")
        print("9. Verify the UI shows:")
        print("   ✓ Growth Level: 阳性 (positive)")
        print("   ✓ Growth Pattern: 聚集型 (clustered)")
        print("   ✓ Status timestamp shows current time")
        
        print("\n🚨 Important Notes:")
        print("• If you see the OLD message '[DEBUG] 是否有enhanced_data属性: False',")
        print("  that means you're loading an OLD annotation saved BEFORE our fixes")
        print("• You must SAVE a NEW annotation to test the enhanced save logic")
        print("• Only annotations saved AFTER our fixes will have enhanced_data")
        
        print("\n📋 Expected vs. Problematic Behavior:")
        print("Expected (after our fixes):")
        print("  [SAVE] ✓ enhanced_data设置成功")
        print("  [DEBUG] enhanced_data内容: True")
        print("  [RESTORE] 设置特征组合: 级别=positive, 模式=clustered")
        print("  UI: Growth Level='阳性', Growth Pattern='聚集型'")
        print()
        print("Problematic (old behavior):")
        print("  [DEBUG] 是否有enhanced_data属性: False")
        print("  [SYNC] 创建特征组合: positive_heavy_growth")
        print("  [RESTORE] 设置特征组合: 级别=positive, 模式=heavy_growth")
        print("  UI: Growth Level='阳性', Growth Pattern='重生长' (wrong!)")
        
        print("\n🚀 Starting enhanced test GUI...")
        
        # Start GUI main loop
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔧 Enhanced Annotation Save/Restore Test")
    print("Goal: Verify that positive_clustered annotations are properly saved and restored")
    print()
    
    success = test_enhanced_save_restore()
    
    if success:
        print("\n✅ Test GUI started successfully")
        print("Please follow the test instructions above")
    else:
        print("\n❌ Test GUI startup failed")
    
    print("\n📋 Verification Checklist:")
    print("[ ] See [SAVE] 检查增强标注面板: hasattr=True, not None=True")
    print("[ ] See [SAVE] ✓ enhanced_data设置成功")
    print("[ ] See [VERIFY] 保存的特征: 级别=positive, 模式=clustered")
    print("[ ] See [DEBUG] enhanced_data内容: True (when loading)")
    print("[ ] See [RESTORE] 设置特征组合: 级别=positive, 模式=clustered")
    print("[ ] UI correctly shows '阳性' and '聚集型' after restore")
    
    sys.exit(0 if success else 1)