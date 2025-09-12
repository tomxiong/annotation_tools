# 测试与日志系统说明

## 📋 概述

本文档说明了标注工具的测试框架和日志系统的使用方法。经过整理，现在提供了统一的测试套件和灵活的日志管理功能。

## 🧪 测试系统

### 统一测试套件 (`test_suite.py`)

新的测试套件整合了所有功能测试，支持选择性运行：

```bash
# 查看可用测试
python test_suite.py --list

# 运行所有测试
python test_suite.py

# 运行指定测试
python test_suite.py --tests performance logger

# 详细输出模式
python test_suite.py --tests inheritance --verbose
```

### 可用测试项目

1. **performance** - 性能监控功能测试
   - 验证性能监控开关
   - 测试详细计时记录
   - 检查报告生成功能

2. **logger** - 日志系统功能测试
   - 测试不同日志级别
   - 验证调试模式切换
   - 检查便捷日志函数

3. **inheritance** - 智能继承策略测试
   - 验证策略方法存在
   - 检查模型视图逻辑
   - 测试状态显示功能

### 已清理的文件

以下旧测试文件已移至 `archive/temp_tests/`：
- `test_performance_monitoring_old.py`
- `quick_perf_test_old.py`

## 📊 日志系统

### 日志管理工具 (`log_manager.py`)

新的日志管理工具提供动态配置功能：

```bash
# 查看当前状态
python tools/log_manager.py status

# 设置日志级别
python tools/log_manager.py set off     # 关闭调试日志
python tools/log_manager.py set info    # 启用信息级别
python tools/log_manager.py set verbose # 启用详细调试

# 测试日志输出
python tools/log_manager.py test

# 查看日志分类
python tools/log_manager.py categories

# 清理日志文件
python tools/log_manager.py clear
```

### 日志级别说明

#### 基础级别
- **DEBUG**: 详细的调试信息，包括变量值、执行流程等
- **INFO**: 关键操作信息，如策略选择、状态变化等  
- **WARNING**: 警告信息，如性能问题、配置缺失等
- **ERROR**: 错误信息，程序可以继续运行
- **CRITICAL**: 严重错误，程序可能无法继续运行

#### 日志分类

| 分类组 | 分类名称 | 缩写 | 用途 |
|--------|----------|------|------|
| **系统级别** | SYSTEM | SYS | 系统启动、关闭等 |
| | CONFIG | CFG | 配置加载、解析等 |
| | STARTUP | START | 初始化过程 |
| **功能级别** | NAVIGATION | NAV | 导航跳转、页面切换 |
| | ANNOTATION | ANN | 标注保存、加载等 |
| | PERFORMANCE | PERF | 性能监控数据 |
| | STRATEGY | STRAT | 智能策略选择 |
| **调试级别** | DEBUG_DETAIL | DEBUG | 详细调试信息 |
| | UI_DETAIL | UI | UI组件状态变化 |
| | DATA_DETAIL | DATA | 数据结构操作 |
| | TIMING_DETAIL | TIME | 时序和计时信息 |

### 便捷日志函数

```python
# 导入便捷函数
from src.utils.logger import (
    log_strategy, log_perf, log_nav, log_ann,
    log_debug_detail, log_ui_detail, log_timing
)

# 使用示例
log_strategy("智能继承策略已选择策略2")
log_perf("性能监控: 保存并下一个操作耗时 125ms")
log_nav("导航: 从孔位1跳转到孔位2")
log_ann("标注: 已保存增强标注数据")

log_debug_detail("变量值: current_hole=1, next_hole=2")
log_ui_detail("UI组件更新: 按钮状态=禁用")
log_timing("时序: 按钮禁用->5ms, 设置收集->12ms")
```

### 动态日志控制

```python
from src.utils.logger import set_debug_mode

# 程序运行时动态调整
set_debug_mode("off")      # 关闭调试
set_debug_mode("info")     # 显示信息级别
set_debug_mode("verbose")  # 显示详细调试
```

## 🔧 使用建议

### 开发阶段
```bash
# 启用详细调试模式查看所有信息
python log_manager.py set verbose

# 运行测试验证功能
python test_suite.py --verbose
```

### 生产环境
```bash
# 关闭调试日志减少输出
python log_manager.py set off

# 定期清理日志文件
python log_manager.py clear
```

### 问题排查
```bash
# 启用信息级别查看关键操作
python log_manager.py set info

# 运行特定测试定位问题
python test_suite.py --tests performance --verbose
```

## 📁 文件结构

```
annotation_tools/
├── test_suite.py           # 统一测试套件
├── log_manager.py          # 日志管理工具
├── src/utils/logger.py     # 改进的日志系统
├── logs/                   # 日志文件目录
│   ├── annotation.log      # 主日志文件
│   └── annotation_backup.log # 备份日志
└── archive/temp_tests/     # 旧测试文件存档
    ├── test_performance_monitoring_old.py
    └── quick_perf_test_old.py
```

## 🎯 主要改进

1. **统一测试框架** - 单一入口点，支持选择性测试
2. **分层日志级别** - 明确的DEBUG/INFO区分
3. **便捷日志函数** - 针对不同功能的专用日志函数
4. **动态配置** - 运行时调整日志级别
5. **分类管理** - 清晰的日志分类和缩写
6. **工具化管理** - 专用的日志管理命令行工具

这套系统使得调试更加高效，日志信息更加清晰易读。
