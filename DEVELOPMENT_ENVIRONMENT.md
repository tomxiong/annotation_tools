# 本地Python环境配置记录

## 当前环境信息
- 工作目录: C:\ws\annotation_tools
- 平台: win32
- Python版本: 需要确认
- 当前日期: 2025-08-30

## 项目结构
```
annotation_tools/
├── src/                          # 源代码目录
│   ├── models/                   # 数据模型
│   │   ├── enhanced_annotation.py      # 增强标注模型
│   │   ├── panoramic_annotation.py     # 全景标注模型
│   │   └── annotation.py              # 基础标注模型
│   ├── ui/                        # 用户界面
│   │   ├── enhanced_annotation_panel.py  # 增强标注面板
│   │   └── panoramic_annotation_gui.py   # 全景标注GUI
│   └── utils/                     # 工具函数
├── run_gui.py                     # 原始启动脚本
├── run_gui_fixed.py               # 修复后的启动脚本
└── 各种测试和分析脚本
```

## 依赖包要求
基于代码分析，需要的Python包：
- tkinter (GUI框架)
- pathlib (路径处理)
- json (JSON处理)
- datetime (时间处理)
- dataclasses (数据类)
- typing (类型提示)
- traceback (异常追踪)

## 启动命令
```bash
# 标准启动
python run_gui_fixed.py

# 或者使用原始启动脚本
python run_gui.py
```

## 已实现的功能
1. **干扰因素系统**：
   - PORES (气孔)
   - ARTIFACTS (气孔重叠)
   - DEBRIS (杂质)
   - CONTAMINATION (污染)

2. **继续标注功能**：
   - 自动切换到对应全景图像
   - 自动定位到最后一个标注的孔位
   - 恢复未完成的标注工作

3. **数据格式支持**：
   - 优化格式的JSON存储
   - 历史数据兼容性
   - 时间戳保留

## 常见问题及解决方案

### 1. 模块缓存问题
如果遇到InterferenceType相关错误，使用以下命令清除缓存：
```bash
python run_gui_fixed.py  # 该脚本已包含缓存清除逻辑
```

### 2. 文件路径问题
确保工作目录正确，所有相对路径都基于项目根目录。

### 3. 中文编码问题
JSON文件使用UTF-8编码，确保文件保存时编码正确。

## 测试方法
1. **功能验证**：
   ```bash
   python final_verification.py
   ```

2. **继续标注测试**：
   ```bash
   python test_continue_annotation.py
   ```

3. **强制重载测试**：
   ```bash
   python force_reload_test.py
   ```

## 核心文件说明

### src/models/enhanced_annotation.py
- 定义InterferenceType枚举
- 实现干扰因素映射关系
- 处理特征组合逻辑

### src/ui/panoramic_annotation_gui.py
- 主GUI应用程序
- 实现自动切换功能
- 处理标注加载和保存

### src/ui/enhanced_annotation_panel.py
- 增强标注控制面板
- 干扰因素选择界面
- 标注数据同步

## 开发注意事项
1. 修改InterferenceType定义时需要同步更新model和ui两个文件
2. 添加新干扰因素时需要更新VALID_COMBINATIONS
3. 修改GUI逻辑时注意保持向后兼容性
4. 测试新功能时使用独立的测试脚本

## 数据文件格式
标注数据存储为JSON格式，支持：
- 优化格式（推荐）
- 旧格式（兼容）
- 基础格式（兼容）

示例文件：
- m8.json
- m7.json
- m5.json