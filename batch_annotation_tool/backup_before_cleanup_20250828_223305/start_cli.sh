#!/bin/bash
echo "启动批量标注工具命令行界面..."
echo

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "虚拟环境创建完成"
fi

# 激活虚拟环境
source venv/bin/activate

# 检查是否已安装依赖
if ! pip list | grep -q "batch-annotation-tool"; then
    echo "正在安装依赖..."
    pip install -e .
fi

# 运行CLI，传递所有参数
python run_cli.py "$@"

# 如果出错，显示错误信息
if [ $? -ne 0 ]; then
    echo
    echo "运行出错，请查看上面的错误信息"
    read -p "按回车键继续..."
fi