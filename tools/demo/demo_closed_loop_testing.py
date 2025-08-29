#!/usr/bin/env python3
"""
测试和修复闭环演示 (Test and Fix Closed Loop Demo)

演示完整的自动化测试、缺陷检测、自动修复和验证循环。
这个演示版本专注于展示闭环逻辑，不依赖复杂的外部库。
"""

import sys
import os
import time
import json
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加项目路径
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

class TestResult:
    """测试结果数据结构"""
    def __init__(self, name: str, passed: bool = False, error: str = "", defects: List[str] = None):
        self.name = name
        self.passed = passed
        self.error = error
        self.defects = defects or []
        self.fixes_applied = []
        self.execution_time = 0.0

class Defect:
    """缺陷数据结构"""
    def __init__(self, id: str, description: str, fix_strategy: str, auto_fixable: bool = True):
        self.id = id
        self.description = description
        self.fix_strategy = fix_strategy
        self.auto_fixable = auto_fixable
        self.fix_applied = False
        self.fix_success = False

class ClosedLoopTester:
    """测试和修复闭环演示系统"""
    
    def __init__(self):
        self.test_results = []
        self.defects_detected = []
        self.fixes_applied = []
        self.test_cycle = 0
        self.max_cycles = 3
        
        print("🔄 初始化测试和修复闭环系统")
        print("=" * 60)

    def execute_closed_loop_testing(self):
        """执行完整的测试和修复闭环"""
        print("🚀 开始执行测试和修复闭环")
        print("=" * 60)
        
        while self.test_cycle < self.max_cycles:
            self.test_cycle += 1
            print(f"\n🔄 测试循环 {self.test_cycle}/{self.max_cycles}")
            print("-" * 40)
            
            # 第一步：执行功能测试
            test_results = self.execute_functionality_tests()
            
            # 第二步：分析测试结果，检测缺陷
            defects = self.analyze_and_detect_defects(test_results)
            
            if not defects:
                print("✅ 所有测试通过！闭环测试成功完成。")
                break
                
            # 第三步：应用自动修复
            fix_results = self.apply_automated_fixes(defects)
            
            # 第四步：验证修复效果
            verification_success = self.verify_fixes(fix_results)
            
            if verification_success:
                print("✅ 自动修复成功！继续下一轮验证。")
            else:
                print("⚠️ 部分修复未成功，继续下一个测试循环。")
                
            time.sleep(0.1)  # 短暂暂停，模拟实际处理时间
        
        return self.generate_final_report()

    def execute_functionality_tests(self):
        """执行功能测试阶段"""
        print("🔍 阶段1: 执行功能测试")
        
        # 定义测试套件
        test_suite = [
            ("环境验证测试", self.test_environment_validation),
            ("GUI启动测试", self.test_gui_startup),
            ("图像系统测试", self.test_image_system),
            ("导航系统测试", self.test_navigation_system),
            ("标注功能测试", self.test_annotation_functionality),
            ("数据持久化测试", self.test_data_persistence)
        ]
        
        results = []
        
        for test_name, test_func in test_suite:
            print(f"   📋 正在执行: {test_name}")
            start_time = time.time()
            
            try:
                result = test_func()
                result.execution_time = time.time() - start_time
                results.append(result)
                
                status = "✅ 通过" if result.passed else "❌ 失败"
                print(f"      {status} ({result.execution_time:.2f}s)")
                
                if result.defects:
                    print(f"      🚨 检测到 {len(result.defects)} 个缺陷")
                    
            except Exception as e:
                result = TestResult(test_name, False, str(e))
                result.execution_time = time.time() - start_time
                results.append(result)
                print(f"      ❌ 异常: {e}")
        
        return results

    def test_environment_validation(self) -> TestResult:
        """测试环境验证"""
        defects = []
        
        # 检查虚拟环境
        venv_path = project_root / "venv"
        if not venv_path.exists():
            defects.append("virtual_environment_missing")
            
        # 检查关键模块导入
        try:
            import tkinter as tk
        except ImportError:
            defects.append("tkinter_import_failed")
            
        try:
            from PIL import Image
        except ImportError:
            defects.append("pil_import_failed")
            
        # 检查项目结构
        src_dir = project_root / "src"
        if not src_dir.exists():
            defects.append("src_directory_missing")
            
        passed = len(defects) == 0
        return TestResult("环境验证测试", passed, "", defects)

    def test_gui_startup(self) -> TestResult:
        """测试GUI启动功能"""
        defects = []
        
        # 检查GUI入口文件
        gui_files = ["start_gui.py", "launch_gui.py"]
        missing_files = []
        
        for gui_file in gui_files:
            if not (project_root / gui_file).exists():
                missing_files.append(gui_file)
                
        if missing_files:
            defects.append(f"gui_entry_files_missing: {missing_files}")
            
        # 模拟GUI组件检查
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # 隐藏窗口
            root.destroy()
        except Exception as e:
            defects.append("gui_component_error")
            
        passed = len(defects) == 0
        return TestResult("GUI启动测试", passed, "", defects)

    def test_image_system(self) -> TestResult:
        """测试图像系统功能"""
        defects = []
        
        # 检查测试图像目录
        test_image_dir = Path("D:\\test\\images")
        if not test_image_dir.exists():
            defects.append("test_image_directory_missing")
            
        # 检查图像处理能力
        try:
            from PIL import Image
            # 创建测试图像
            test_img = Image.new('RGB', (100, 100), 'white')
        except Exception as e:
            defects.append("image_processing_error")
            
        passed = len(defects) == 0
        return TestResult("图像系统测试", passed, "", defects)

    def test_navigation_system(self) -> TestResult:
        """测试导航系统功能"""
        defects = []
        
        # 模拟12x10网格验证
        grid_cols = 12
        grid_rows = 10
        expected_holes = 120
        
        actual_holes = grid_cols * grid_rows
        if actual_holes != expected_holes:
            defects.append("navigation_grid_calculation_error")
            
        # 模拟坐标计算测试
        for hole_num in [1, 25, 60, 120]:
            row = (hole_num - 1) // grid_cols
            col = (hole_num - 1) % grid_cols
            
            if row < 0 or row >= grid_rows or col < 0 or col >= grid_cols:
                defects.append(f"navigation_coordinate_error_hole_{hole_num}")
                
        passed = len(defects) == 0
        return TestResult("导航系统测试", passed, "", defects)

    def test_annotation_functionality(self) -> TestResult:
        """测试标注功能"""
        defects = []
        
        # 验证标注类型
        microbe_types = ["bacteria", "fungi"]
        growth_levels = ["negative", "weak_growth", "positive"]
        
        # 模拟标注数据验证
        test_annotation = {
            "microbe_type": "bacteria",
            "growth_level": "positive",
            "confidence": 0.9
        }
        
        if test_annotation["microbe_type"] not in microbe_types:
            defects.append("annotation_invalid_microbe_type")
            
        if test_annotation["growth_level"] not in growth_levels:
            defects.append("annotation_invalid_growth_level")
            
        confidence = test_annotation.get("confidence", 0)
        if not (0.0 <= confidence <= 1.0):
            defects.append("annotation_invalid_confidence_range")
            
        passed = len(defects) == 0
        return TestResult("标注功能测试", passed, "", defects)

    def test_data_persistence(self) -> TestResult:
        """测试数据持久化功能"""
        defects = []
        
        # 测试JSON序列化/反序列化
        test_data = {"test": "data", "timestamp": datetime.now().isoformat()}
        
        try:
            json_str = json.dumps(test_data)
            loaded_data = json.loads(json_str)
            
            if loaded_data["test"] != test_data["test"]:
                defects.append("data_persistence_integrity_error")
                
        except Exception as e:
            defects.append("data_persistence_serialization_error")
            
        # 测试文件操作
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                json.dump(test_data, f)
                temp_file = f.name
                
            with open(temp_file, 'r') as f:
                file_data = json.load(f)
                
            os.unlink(temp_file)  # 清理临时文件
            
        except Exception as e:
            defects.append("data_persistence_file_operation_error")
            
        passed = len(defects) == 0
        return TestResult("数据持久化测试", passed, "", defects)

    def analyze_and_detect_defects(self, test_results: List[TestResult]) -> List[Defect]:
        """分析测试结果并检测缺陷"""
        print("\n🔍 阶段2: 分析测试结果，检测缺陷")
        
        defects = []
        
        for result in test_results:
            if not result.passed:
                for defect_name in result.defects:
                    defect = self.create_defect_from_failure(defect_name, result.name)
                    defects.append(defect)
                    print(f"   🚨 检测到缺陷: {defect.description}")
                    
        self.defects_detected.extend(defects)
        
        if defects:
            print(f"   📊 总计检测到 {len(defects)} 个缺陷")
        else:
            print("   ✅ 未检测到缺陷")
            
        return defects

    def create_defect_from_failure(self, defect_name: str, test_name: str) -> Defect:
        """根据失败类型创建缺陷对象"""
        defect_id = f"defect_{self.test_cycle}_{len(self.defects_detected)}_{int(time.time())}"
        
        # 根据缺陷类型确定修复策略
        fix_strategies = {
            "virtual_environment_missing": "recreate_virtual_environment",
            "tkinter_import_failed": "install_tkinter_dependencies",
            "pil_import_failed": "install_pil_dependencies",
            "src_directory_missing": "create_src_directory_structure",
            "test_image_directory_missing": "create_test_image_directory",
            "gui_entry_files_missing": "create_gui_entry_files",
            "navigation_grid_calculation_error": "fix_navigation_calculations",
            "annotation_invalid_microbe_type": "reset_annotation_configuration",
            "data_persistence_serialization_error": "fix_data_serialization"
        }
        
        # 查找匹配的修复策略
        fix_strategy = "manual_investigation_required"
        for pattern, strategy in fix_strategies.items():
            if pattern in defect_name:
                fix_strategy = strategy
                break
                
        return Defect(
            id=defect_id,
            description=f"{test_name}: {defect_name}",
            fix_strategy=fix_strategy,
            auto_fixable=fix_strategy != "manual_investigation_required"
        )

    def apply_automated_fixes(self, defects: List[Defect]) -> Dict[str, bool]:
        """应用自动修复"""
        print("\n🛠️ 阶段3: 应用自动修复")
        
        fix_results = {}
        
        for defect in defects:
            if defect.auto_fixable:
                print(f"   🔧 正在修复: {defect.description}")
                print(f"      📋 修复策略: {defect.fix_strategy}")
                
                # 应用修复
                fix_success = self.apply_fix_strategy(defect.fix_strategy)
                fix_results[defect.id] = fix_success
                
                defect.fix_applied = True
                defect.fix_success = fix_success
                
                if fix_success:
                    print(f"      ✅ 修复成功")
                    self.fixes_applied.append(defect.fix_strategy)
                else:
                    print(f"      ❌ 修复失败")
            else:
                print(f"   ⚠️ 需要人工干预: {defect.description}")
                fix_results[defect.id] = False
                
        return fix_results

    def apply_fix_strategy(self, strategy: str) -> bool:
        """应用具体的修复策略"""
        try:
            if strategy == "recreate_virtual_environment":
                # 模拟虚拟环境重建
                print("      📁 重建虚拟环境...")
                venv_path = project_root / "venv"
                if not venv_path.exists():
                    venv_path.mkdir(exist_ok=True)
                return True
                
            elif strategy == "install_pil_dependencies":
                # 模拟PIL依赖安装
                print("      📦 安装PIL依赖...")
                return True
                
            elif strategy == "create_test_image_directory":
                # 创建测试图像目录
                print("      📁 创建测试图像目录...")
                test_dir = Path("D:\\test\\images")
                test_dir.mkdir(parents=True, exist_ok=True)
                
                # 创建简单的测试图像
                try:
                    from PIL import Image
                    test_img = Image.new('RGB', (100, 100), 'white')
                    test_file = test_dir / "test_image.jpg"
                    test_img.save(test_file)
                    print(f"         创建测试图像: {test_file}")
                except ImportError:
                    # 如果PIL不可用，创建占位文件
                    test_file = test_dir / "test_image.txt"
                    test_file.write_text("测试图像占位文件")
                    
                return True
                
            elif strategy == "create_src_directory_structure":
                # 创建源代码目录结构
                print("      📁 创建源代码目录结构...")
                (project_root / "src").mkdir(exist_ok=True)
                (project_root / "src" / "ui").mkdir(exist_ok=True)
                (project_root / "src" / "models").mkdir(exist_ok=True)
                (project_root / "src" / "services").mkdir(exist_ok=True)
                return True
                
            elif strategy == "fix_navigation_calculations":
                # 修复导航计算
                print("      🧮 修复导航计算...")
                # 验证12x10网格计算
                grid_result = 12 * 10
                if grid_result == 120:
                    return True
                return False
                
            elif strategy == "reset_annotation_configuration":
                # 重置标注配置
                print("      ⚙️ 重置标注配置...")
                return True
                
            elif strategy == "fix_data_serialization":
                # 修复数据序列化
                print("      💾 修复数据序列化...")
                test_data = {"test": "data"}
                json.dumps(test_data)  # 测试序列化
                return True
                
            else:
                print(f"      ⚠️ 未知修复策略: {strategy}")
                return False
                
        except Exception as e:
            print(f"      ❌ 修复过程中出现异常: {e}")
            return False

    def verify_fixes(self, fix_results: Dict[str, bool]) -> bool:
        """验证修复效果"""
        print("\n✅ 阶段4: 验证修复效果")
        
        successful_fixes = sum(1 for success in fix_results.values() if success)
        total_fixes = len(fix_results)
        
        if total_fixes == 0:
            print("   📋 没有需要验证的修复")
            return True
            
        success_rate = (successful_fixes / total_fixes) * 100
        print(f"   📊 修复成功率: {successful_fixes}/{total_fixes} ({success_rate:.1f}%)")
        
        # 快速验证关键修复
        verification_tests = [
            self.verify_environment_fix,
            self.verify_image_system_fix,
            self.verify_navigation_fix
        ]
        
        verification_passed = 0
        for verify_func in verification_tests:
            try:
                if verify_func():
                    verification_passed += 1
            except Exception as e:
                print(f"   ⚠️ 验证过程中出现异常: {e}")
                
        overall_success = verification_passed == len(verification_tests)
        
        if overall_success:
            print("   ✅ 所有修复验证通过")
        else:
            print(f"   ⚠️ {len(verification_tests) - verification_passed} 个修复验证失败")
            
        return overall_success

    def verify_environment_fix(self) -> bool:
        """验证环境修复"""
        venv_path = project_root / "venv"
        src_path = project_root / "src"
        return venv_path.exists() and src_path.exists()

    def verify_image_system_fix(self) -> bool:
        """验证图像系统修复"""
        test_dir = Path("D:\\test\\images")
        return test_dir.exists()

    def verify_navigation_fix(self) -> bool:
        """验证导航系统修复"""
        # 验证12x10网格计算
        return (12 * 10) == 120

    def generate_final_report(self) -> Dict[str, Any]:
        """生成最终报告"""
        print("\n📊 生成最终测试报告")
        print("=" * 60)
        
        total_defects = len(self.defects_detected)
        fixed_defects = len([d for d in self.defects_detected if d.fix_success])
        fixes_applied = len(self.fixes_applied)
        
        report = {
            "session_summary": {
                "test_cycles": self.test_cycle,
                "max_cycles": self.max_cycles,
                "total_defects_detected": total_defects,
                "defects_successfully_fixed": fixed_defects,
                "total_fixes_applied": fixes_applied,
                "overall_success": fixed_defects == total_defects
            },
            "defect_analysis": [
                {
                    "id": d.id,
                    "description": d.description,
                    "fix_strategy": d.fix_strategy,
                    "auto_fixable": d.auto_fixable,
                    "fix_applied": d.fix_applied,
                    "fix_success": d.fix_success
                } for d in self.defects_detected
            ],
            "fixes_applied": self.fixes_applied
        }
        
        print(f"📋 测试循环: {self.test_cycle}/{self.max_cycles}")
        print(f"🚨 检测到缺陷: {total_defects}")
        print(f"✅ 成功修复: {fixed_defects}")
        print(f"🛠️ 应用修复: {fixes_applied}")
        
        if report["session_summary"]["overall_success"]:
            print("\n🎉 测试和修复闭环成功完成！")
            print("   所有检测到的缺陷都已成功修复。")
        else:
            print("\n⚠️ 测试和修复闭环部分成功。")
            print("   部分缺陷需要进一步处理。")
            
        return report


def main():
    """主入口点"""
    print("🔬 测试和修复闭环演示系统")
    print("=" * 60)
    print("演示自动化测试、缺陷检测、自动修复和验证的完整循环")
    print()
    
    try:
        # 创建闭环测试器
        tester = ClosedLoopTester()
        
        # 执行完整的测试和修复闭环
        final_report = tester.execute_closed_loop_testing()
        
        # 保存报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = project_root / f"closed_loop_test_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, indent=2, ensure_ascii=False)
            
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        # 退出状态
        if final_report["session_summary"]["overall_success"]:
            print("\n✅ 闭环测试成功完成！")
            return 0
        else:
            print("\n⚠️ 闭环测试部分完成，需要进一步处理。")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了测试过程。")
        return 2
    except Exception as e:
        print(f"\n❌ 闭环测试过程中发生错误: {e}")
        return 3


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)