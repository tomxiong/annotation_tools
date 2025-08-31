# 全景图像标注工具打包指南

## 概述

本指南介绍如何将全景图像标注工具打包成可执行文件，使其可以在没有Python环境的计算机上运行。

## 系统要求

- Python 3.8+
- Windows 10/11 (推荐)
- 至少4GB内存
- 2GB可用磁盘空间

## 打包方法

### 方法一：使用自动构建脚本（推荐）

1. **Windows系统**：
   ```batch
   build.bat
   ```

2. **Linux/Mac系统**：
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

### 方法二：手动构建

1. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **使用PyInstaller构建**：
   ```bash
   # GUI版本
   pyinstaller --name="全景图像标注工具" --windowed --onefile --clean run_gui.py
   
   # CLI版本
   pyinstaller --name="annotation-cli" --console --onefile --clean run_cli.py
   ```

3. **使用spec文件构建**（更详细控制）：
   ```bash
   pyinstaller panoramic_annotation.spec
   ```

## 打包选项说明

### GUI版本（推荐给最终用户）
- **文件名**：`全景图像标注工具.exe`
- **类型**：窗口化应用，无控制台
- **大小**：约50-100MB
- **特点**：用户友好，双击即可运行

### CLI版本
- **文件名**：`annotation-cli.exe`
- **类型**：控制台应用
- **大小**：约40-80MB
- **特点**：适合批处理和自动化任务

## 构建输出

构建完成后，可执行文件位于：
- `dist/全景图像标注工具.exe` (GUI版本)
- `dist/annotation-cli.exe` (CLI版本)
- `release/` (包含说明文件的发布版本)

## 常见问题解决

### 1. 打包后程序无法启动

**原因**：缺少依赖库或导入路径问题

**解决方案**：
- 检查`hidden_imports`是否包含所有必要的模块
- 使用`--debug`选项重新构建查看错误信息
- 确保所有数据文件正确包含

### 2. 打包文件过大

**原因**：包含了不必要的库

**解决方案**：
- 使用`--exclude-module`排除不需要的库
- 使用UPX压缩减小文件大小
- 考虑使用目录模式而非单文件模式

### 3. 图像处理功能异常

**原因**：OpenCV或PIL库打包问题

**解决方案**：
- 添加`--collect-all=cv2`和`--collect-all=PIL`
- 确保图像处理相关的隐藏导入正确

### 4. 杀毒软件误报

**原因**：PyInstaller生成的可执行文件可能被误报

**解决方案**：
- 使用代码签名证书签名
- 添加杀毒软件白名单
- 使用知名打包工具如Inno Setup重新打包

## 高级配置

### 自定义图标
```bash
pyinstaller --icon=assets/icon.ico --windowed --onefile run_gui.py
```

### 添加版本信息
创建`version.txt`文件：
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'开发团队'),
         StringStruct(u'FileDescription', u'全景图像标注工具'),
         StringStruct(u'FileVersion', u'1.0.0'),
         StringStruct(u'InternalName', u'panoramic_annotation'),
         StringStruct(u'LegalCopyright', u'Copyright © 2024'),
         StringStruct(u'OriginalFilename', u'全景图像标注工具.exe'),
         StringStruct(u'ProductName', u'全景图像标注工具'),
         StringStruct(u'ProductVersion', u'1.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

### 创建安装程序

使用Inno Setup创建专业安装程序：

1. 下载并安装Inno Setup
2. 创建`setup.iss`脚本文件
3. 编译生成安装程序

## 分发建议

1. **测试**：在多台计算机上测试可执行文件
2. **文档**：提供详细的使用说明
3. **支持**：包含技术支持联系方式
4. **更新**：建立版本更新机制

## 性能优化

1. **减小文件大小**：
   - 使用UPX压缩
   - 排除不必要的模块
   - 考虑使用目录模式

2. **启动速度**：
   - 优化导入顺序
   - 延迟加载非必要模块
   - 使用启动画面

3. **内存使用**：
   - 及时释放不再使用的资源
   - 优化图像处理算法
   - 使用缓存机制

## 故障排除

如果遇到打包问题，请：

1. 检查控制台输出错误信息
2. 查看生成的日志文件
3. 尝试在开发环境中重现问题
4. 参考PyInstaller官方文档
5. 搜索相关问题的解决方案

---

通过以上步骤，您应该能够成功将全景图像标注工具打包成可执行文件并分发给最终用户。