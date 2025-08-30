# 目录清理报告

清理时间: 2025-08-31

## 清理后的目录结构

### 根目录 (核心文件)
- **run_gui.py** - 标准GUI启动脚本
- **run_gui_fixed.py** - 修复版GUI启动脚本（推荐使用）
- **run_cli.py** - 命令行启动脚本
- **DEVELOPMENT_ENVIRONMENT.md** - 开发环境配置文档
- **INSTALL.md** - 安装指南
- **README.md** - 项目说明文档

### 主要目录
- **src/** - 源代码目录
  - models/ - 数据模型
  - ui/ - 用户界面
  - services/ - 业务逻辑
  - cli/ - 命令行接口
  - core/ - 核心功能

- **docs/** - 官方文档目录
  - 包含详细的技术文档和修复记录

- **tests/** - 单元测试目录
  - unit/ - 单元测试文件

- **tools/** - 工具目录
  - automation/ - 自动化工具
  - debug/ - 调试工具
  - demo/ - 演示工具
  - testing/ - 测试工具
  - utils/ - 实用工具

- **config/** - 配置文件目录

### 归档目录 (archive/)

#### archive/test_scripts/ - 测试脚本归档
- debug_*.py - 调试脚本
- test_*.py - 测试脚本
- verify_*.py - 验证脚本
- final_verification.py - 最终验证脚本
- force_reload_test.py - 强制重载测试
- interface_correction_confirmation.py - 界面修正确认
- 以及其他测试相关脚本

#### archive/analysis/ - 分析脚本归档
- analyze_*.py - 分析脚本
- interference_factors_comparison*.py - 干扰因素比较
- demo_window_analysis.py - 演示窗口分析
- complete_interference_analysis.py - 完整干扰因素分析

#### archive/optimization/ - 优化脚本归档
- optimize_*.py - 优化脚本
- manual_optimize.py - 手动优化
- quick_optimize.py - 快速优化
- simple_optimize.py - 简单优化

#### archive/json_files/ - JSON文件归档
- m5.json, m7.json, m8.json - 测试数据文件
- m5_optimized_*.json - 优化后的数据文件

#### archive/batch_files/ - 批处理文件归档
- run_*.bat, run_*.sh - 运行脚本
- start_*.bat, start_*.sh - 启动脚本

#### archive/temp_docs/ - 临时文档归档
- json_optimization_analysis.md - JSON优化分析
- optimization_*.md - 优化相关文档
- optimization_execution_report.md - 优化执行报告
- optimization_implementation_guide.md - 优化实现指南

## 使用说明

### 启动应用
1. **标准启动**: `python run_gui.py`
2. **修复版启动**: `python run_gui_fixed.py` (推荐)
3. **命令行启动**: `python run_cli.py`

### 查看文档
- **项目文档**: README.md, INSTALL.md
- **开发环境**: DEVELOPMENT_ENVIRONMENT.md
- **详细文档**: docs/ 目录

### 访问归档文件
- **测试脚本**: archive/test_scripts/
- **分析脚本**: archive/analysis/
- **优化脚本**: archive/optimization/
- **测试数据**: archive/json_files/
- **批处理脚本**: archive/batch_files/

## 清理统计
- 移动测试脚本: 20+ 个
- 移动分析脚本: 6 个
- 移动优化脚本: 4 个
- 移动JSON文件: 5 个
- 移动批处理文件: 6 个
- 移动临时文档: 4 个

## 注意事项
1. 所有重要文件都已安全归档
2. 核心功能文件保留在根目录
3. 启动脚本保持不变，确保正常使用
4. 如需访问归档文件，请到相应目录查找
5. docs/ 目录下的官方文档保持不变