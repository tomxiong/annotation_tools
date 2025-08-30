#!/usr/bin/env python3
"""
目录清理脚本
整理annotation_tools目录下的文件
"""

import os
import shutil
from pathlib import Path
import datetime

def create_directory_structure():
    """创建目录结构"""
    
    # 需要创建的目录
    directories = [
        "archive/test_scripts",      # 归档测试脚本
        "archive/analysis",         # 归档分析脚本
        "archive/temp_docs",        # 归档临时文档
        "archive/optimization",     # 归档优化脚本
        "archive/verification",     # 归档验证脚本
        "archive/json_files",        # 归档JSON文件
        "archive/batch_files",       # 归档批处理文件
        "working_docs",             # 工作文档
        "config"                   # 配置文件
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"创建目录: {directory}")

def categorize_files():
    """分类文件"""
    
    # 文件分类映射
    file_categories = {
        # 测试脚本 -> archive/test_scripts
        "test_*.py": "archive/test_scripts",
        "*_test.py": "archive/test_scripts",
        "debug_*.py": "archive/test_scripts",
        "verify_*.py": "archive/test_scripts",
        "final_verification.py": "archive/test_scripts",
        "force_reload_test.py": "archive/test_scripts",
        "interface_correction_confirmation.py": "archive/test_scripts",
        
        # 分析脚本 -> archive/analysis
        "analyze_*.py": "archive/analysis",
        "*_analysis.py": "archive/analysis",
        "interference_factors_comparison*.py": "archive/analysis",
        "demo_window_analysis.py": "archive/analysis",
        
        # 优化脚本 -> archive/optimization
        "optimize_*.py": "archive/optimization",
        "*_optimize.py": "archive/optimization",
        "optimization_*.py": "archive/optimization",
        "manual_optimize.py": "archive/optimization",
        "quick_optimize.py": "archive/optimization",
        "simple_optimize.py": "archive/optimization",
        
        # JSON文件 -> archive/json_files
        "*.json": "archive/json_files",
        
        # 批处理文件 -> archive/batch_files
        "run_*.bat": "archive/batch_files",
        "run_*.sh": "archive/batch_files",
        "start_*.bat": "archive/batch_files",
        "start_*.sh": "archive/batch_files",
        
        # 启动脚本 -> 根目录保留
        "run_gui.py": ".",  # 保留
        "run_gui_fixed.py": ".",  # 保留
        "run_cli.py": ".",  # 保留
        
        # 重要文档 -> working_docs
        "DEVELOPMENT_ENVIRONMENT.md": "working_docs",
        "INSTALL.md": "working_docs",
        "README.md": "working_docs",
        
        # 临时文档 -> archive/temp_docs
        "json_optimization_analysis.md": "archive/temp_docs",
        "optimization_*.md": "archive/temp_docs",
        "optimization_execution_report.md": "archive/temp_docs",
        "optimization_implementation_guide.md": "archive/temp_docs",
        
        # 其他脚本 -> archive
        "*.py": "archive"
    }
    
    return file_categories

def move_files():
    """移动文件到相应目录"""
    
    # 获取当前目录下的所有文件
    current_dir = Path(".")
    files_to_move = []
    
    # 排除的目录和文件
    exclude_dirs = {"src", "docs", "tests", "tools", "archive", "working_docs", "config"}
    exclude_files = {"cleanup_directory.py", ".gitignore"}
    
    for item in current_dir.iterdir():
        if item.is_file() and item.name not in exclude_files:
            files_to_move.append(item)
    
    # 文件分类
    file_categories = categorize_files()
    
    moved_count = 0
    for file_path in files_to_move:
        moved = False
        
        # 查找匹配的分类
        for pattern, target_dir in file_categories.items():
            if file_path.match(pattern):
                target_path = Path(target_dir) / file_path.name
                
                # 如果目标目录不存在，创建它
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                try:
                    shutil.move(str(file_path), str(target_path))
                    print(f"移动: {file_path.name} -> {target_dir}")
                    moved_count += 1
                    moved = True
                    break
                except Exception as e:
                    print(f"移动失败 {file_path.name}: {e}")
        
        if not moved:
            print(f"未分类: {file_path.name}")
    
    return moved_count

def create_cleanup_report():
    """创建清理报告"""
    
    report = f"""
# 目录清理报告

清理时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 清理后的目录结构

### 根目录 (仅保留核心文件)
- run_gui.py - 标准GUI启动脚本
- run_gui_fixed.py - 修复版GUI启动脚本
- run_cli.py - 命令行启动脚本
- working_docs/ - 工作文档目录
- src/ - 源代码目录
- docs/ - 官方文档目录
- tests/ - 单元测试目录
- tools/ - 工具目录
- config/ - 配置文件目录

### 归档目录
- archive/test_scripts/ - 测试脚本归档
- archive/analysis/ - 分析脚本归档
- archive/optimization/ - 优化脚本归档
- archive/temp_docs/ - 临时文档归档
- archive/json_files/ - JSON文件归档
- archive/batch_files/ - 批处理文件归档

## 使用说明

1. 启动应用:
   - 标准启动: python run_gui.py
   - 修复版启动: python run_gui_fixed.py
   - 命令行: python run_cli.py

2. 查看文档:
   - 工作文档: working_docs/ 目录
   - 官方文档: docs/ 目录

3. 查看归档文件:
   - 测试脚本: archive/test_scripts/
   - 分析脚本: archive/analysis/
   - 优化脚本: archive/optimization/

## 注意事项

- 所有重要文件都已安全归档
- 核心功能文件保留在根目录
- 如需访问归档文件，请到相应目录查找
"""
    
    with open("working_docs/CLEANUP_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("清理报告已生成: working_docs/CLEANUP_REPORT.md")

def main():
    """主函数"""
    
    print("=== 开始目录清理 ===\n")
    
    try:
        # 1. 创建目录结构
        print("1. 创建目录结构...")
        create_directory_structure()
        print("✓ 目录结构创建完成\n")
        
        # 2. 移动文件
        print("2. 移动文件到相应目录...")
        moved_count = move_files()
        print(f"✓ 移动了 {moved_count} 个文件\n")
        
        # 3. 创建清理报告
        print("3. 创建清理报告...")
        create_cleanup_report()
        print("✓ 清理报告创建完成\n")
        
        print("=== 目录清理完成 ===")
        print("📁 清理后的目录结构:")
        print("   ├── run_gui.py")
        print("   ├── run_gui_fixed.py")
        print("   ├── run_cli.py")
        print("   ├── working_docs/")
        print("   ├── src/")
        print("   ├── docs/")
        print("   ├── tests/")
        print("   ├── tools/")
        print("   ├── config/")
        print("   └── archive/")
        
    except Exception as e:
        print(f"清理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()