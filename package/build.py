#!/usr/bin/env python3
"""
全景图像标注工具打包脚本
使用PyInstaller将项目打包成可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_dependencies():
    """安装项目依赖"""
    print("正在安装项目依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False

def build_executable():
    """构建可执行文件"""
    print("正在构建可执行文件...")
    
    # 确保在正确的目录
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # PyInstaller命令
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=全景图像标注工具",
        "--windowed",  # GUI应用，不显示控制台
        "--onefile",   # 打包成单个文件
        "--clean",     # 清理临时文件
        "--add-data=src;src",  # 包含源代码目录
        "--icon=NONE",  # 可以添加图标文件路径
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=yaml",
        "--collect-all=PIL",
        "--collect-all=cv2",
        "--collect-all=numpy",
        "--collect-all=yaml",
        "run_gui.py"   # 主入口文件
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 可执行文件构建完成")
        print(f"输出位置: {project_root / 'dist' / '全景图像标注工具.exe'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def build_cli_executable():
    """构建CLI版本的可执行文件"""
    print("正在构建CLI版本可执行文件...")
    
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    # CLI版本命令
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=annotation-cli",
        "--console",   # 控制台应用
        "--onefile",   # 打包成单个文件
        "--clean",     # 清理临时文件
        "--add-data=src;src",  # 包含源代码目录
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=yaml",
        "--collect-all=cv2",
        "--collect-all=numpy",
        "--collect-all=yaml",
        "run_cli.py"   # CLI入口文件
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ CLI可执行文件构建完成")
        print(f"输出位置: {project_root / 'dist' / 'annotation-cli.exe'}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ CLI构建失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False

def create_installer():
    """创建安装程序（可选）"""
    print("正在创建安装程序...")
    
    # 这里可以集成Inno Setup或NSIS来创建安装程序
    # 目前只是复制文件到指定目录
    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"
    output_dir = project_root / "release"
    
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()
    
    # 复制可执行文件
    for exe_file in dist_dir.glob("*.exe"):
        shutil.copy2(exe_file, output_dir)
    
    # 创建说明文件
    readme_content = """# 全景图像标注工具

## 使用方法

1. GUI版本: 双击运行 `全景图像标注工具.exe`
2. CLI版本: 在命令行运行 `annotation-cli.exe`

## 系统要求

- Windows 10/11
- 至少4GB内存
- 支持的图像格式: PNG, JPG, JPEG, BMP

## 注意事项

- 首次运行可能需要一些时间来初始化
- 建议将可执行文件放在没有中文路径的目录中
- 如果遇到杀毒软件误报，请添加到白名单

## 技术支持

如有问题，请联系技术支持。
"""
    
    (output_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    
    print(f"✅ 安装包创建完成: {output_dir}")

def main():
    """主函数"""
    print("=== 全景图像标注工具打包脚本 ===")
    
    # 1. 安装依赖
    if not install_dependencies():
        sys.exit(1)
    
    # 2. 构建GUI版本
    if not build_executable():
        sys.exit(1)
    
    # 3. 构建CLI版本
    if not build_cli_executable():
        sys.exit(1)
    
    # 4. 创建安装包
    create_installer()
    
    print("\n🎉 打包完成!")
    print("📁 可执行文件位置: ./dist/")
    print("📦 安装包位置: ./release/")

if __name__ == "__main__":
    main()