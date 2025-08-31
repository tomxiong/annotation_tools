#!/bin/bash

echo "=== 全景图像标注工具打包脚本 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3环境，请先安装Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 安装依赖
echo "正在安装依赖..."
pip install -r requirements.txt

# 构建可执行文件
echo "正在构建可执行文件..."
python build.py

echo
echo "打包完成!"
echo "可执行文件位置: ./dist/"
echo